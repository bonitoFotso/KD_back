from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _

from .models import Opportunite


class StatutFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour le statut des opportunités"""
    title = _('Statut')
    parameter_name = 'statut'

    def lookups(self, request, model_admin):
        return Opportunite.STATUS_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(statut=self.value())
        return queryset


class NecessiteRelanceFilter(admin.SimpleListFilter):
    """Filtre pour les opportunités nécessitant une relance"""
    title = _('Nécessite une relance')
    parameter_name = 'relance_necessaire'

    def lookups(self, request, model_admin):
        return (
            ('oui', _('Oui')),
            ('non', _('Non')),
        )

    def queryset(self, request, queryset):
        from django.utils.timezone import now
        if self.value() == 'oui':
            return queryset.filter(
                relance__lte=now(),
                statut__in=['PROSPECT', 'QUALIFICATION', 'PROPOSITION', 'NEGOCIATION']
            )
        elif self.value() == 'non':
            return queryset.exclude(
                relance__lte=now(),
                statut__in=['PROSPECT', 'QUALIFICATION', 'PROPOSITION', 'NEGOCIATION']
            )
        return queryset


@admin.register(Opportunite)
class OpportuniteAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 
        'client_link', 
        'statut_badge', 
        'montant_estime_display', 
        'probabilite_display',
        'valeur_ponderee_display',
        'date_creation', 
        'relance_status',
        'responsable'
        #'has_offre'
    ]
    list_filter = [
        StatutFilter, 
        NecessiteRelanceFilter,
        'entity', 
        'date_creation', 
        #'produit_principal__categorie',
        'created_by'
    ]
    search_fields = [
        'reference', 
        'client__nom', 
        'client__c_num', 
        'description', 
        'besoins_client'
    ]
    readonly_fields = [
        'reference', 
        'sequence_number', 
        'date_creation', 
        'date_modification', 
        'valeur_ponderee_display',
        'offres_associees'
    ]
    fieldsets = (
        (_('Informations Générales'), {
            'fields': (
                'reference', 
                ('client', 'contact'), 
                ('entity', 'created_by'),
                'statut',
                'description'
            )
        }),
        (_('Produits'), {
            'fields': (
                'produit_principal', 
                'produits'
            )
        }),
        (_('Montants et Prévisions'), {
            'fields': (
                ('montant', 'montant_estime'),
                ('probabilite', 'valeur_ponderee_display')
            )
        }),
        (_('Besoins Client'), {
            'fields': ('besoins_client','commentaire'),
            'classes': ('collapse',)
        }),
        (_('Dates et Suivi'), {
            'fields': (
                ('date_creation', 'date_modification'),
                ('date_cloture'),
                'relance'
            )
        }),
        (_('Offres Associées'), {
            'fields': ('offres_associees',),
            'classes': ('collapse',)
        }),
    )
    autocomplete_fields = ['client', 'contact', 'produit_principal', 'produits']
    actions = ['convert_to_offre', 'mark_as_won', 'mark_as_lost', 'update_relance']
    date_hierarchy = 'date_creation'
    save_on_top = True
    list_per_page = 25

    class Media:
        css = {
            'all': ('css/admin/opportunite.css',)
        }
        js = ('js/admin/opportunite.js',)

    def get_queryset(self, request):
        """Optimise les requêtes avec des prefetch et select_related"""
        queryset = super().get_queryset(request)
        # Vérifiez le nom correct de la relation inverse - selon le modèle Offre
        # Si votre modèle Offre a: opportunite = models.ForeignKey('opportunites.Opportunite', ...)
        # alors Django créera automatiquement un nom de relation inverse comme 'offres'
        return queryset.select_related(
            'client', 
            'contact', 
            'entity', 
            'produit_principal',
            'created_by'
        ).prefetch_related('produits')

    def client_link(self, obj):
        """Affiche un lien vers le client"""
        url = reverse("admin:client_client_change", args=[obj.client.id])
        return format_html('<a href="{}">{}</a>', url, obj.client.nom)
    client_link.short_description = _('Client')
    client_link.admin_order_field = 'client__nom'

    def statut_badge(self, obj):
        """Affiche le statut avec une couleur distinctive"""
        colors = {
            'PROSPECT': '#6c757d',       # Gris
            'QUALIFICATION': '#17a2b8',  # Bleu clair
            'PROPOSITION': '#007bff',    # Bleu
            'NEGOCIATION': '#6f42c1',    # Violet
            'GAGNEE': '#28a745',         # Vert
            'PERDUE': '#dc3545',         # Rouge
        }
        color = colors.get(obj.statut, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; '
            'border-radius: 4px;">{}</span>',
            color, dict(Opportunite.STATUS_CHOICES).get(obj.statut, obj.statut)
        )
    statut_badge.short_description = _('Statut')
    statut_badge.admin_order_field = 'statut'

    def montant_estime_display(self, obj):
        """Affiche le montant estimé formaté"""
        return format_html('{0} €'.format(
            '{:,.2f}'.format(obj.montant_estime).replace(',', ' ').replace('.', ',')
        ))
    montant_estime_display.short_description = _('Montant estimé')
    montant_estime_display.admin_order_field = 'montant_estime'

    def probabilite_display(self, obj):
        """Affiche la probabilité avec un pourcentage"""
        return format_html('{}%', obj.probabilite)
    probabilite_display.short_description = _('Probabilité')
    probabilite_display.admin_order_field = 'probabilite'

    def valeur_ponderee_display(self, obj):
        """Affiche la valeur pondérée (montant × probabilité)"""
        if obj.valeur_ponderee is None:
            return format_html('- €')
        
        try:
            formatted_value = '{:,.2f}'.format(obj.valeur_ponderee).replace(',', ' ').replace('.', ',')
            return format_html('{0} €'.format(formatted_value))
        except (TypeError, ValueError):
            return format_html('- €')

    def relance_status(self, obj):
        """Affiche un indicateur visuel pour les relances"""
        if obj.statut in ['GAGNEE', 'PERDUE']:
            return format_html('<span>-</span>')

        if obj.necessite_relance:
            return format_html(
                '<span style="color: #dc3545;"><strong>⚠️ Relance requise</strong></span>'
            )
        elif obj.relance:
            # Formatage de la date en utilisant strftime puis format_html
            formatted_date = obj.relance.strftime('%d/%m/%Y')
            return format_html('{}', formatted_date)
        return format_html('<span>Non planifiée</span>')
    relance_status.short_description = _('Relance')
    relance_status.admin_order_field = 'relance'

    #def has_offre(self, obj):
    #    """Indique si l'opportunité a des offres associées"""
    #    # Il faut vérifier le nom de relation inverse correct
    #    # Cela dépend de comment la relation est définie dans le modèle Offre
    #    try:
    #        # Essayons différentes possibilités de nom de relation
    #        for attr in ['offres', 'offre_set', 'offres_commerciales']:
    #            if hasattr(obj, attr) and callable(getattr(obj, attr).exists):
    #                has_offres = getattr(obj, attr).exists()
    #                if has_offres:
    #                    return format_html('<span style="color: #28a745;">Oui</span>')
    #        
    #        # Si aucune relation n'est trouvée ou si elles sont vides
    #        return format_html('<span style="color: #dc3545;">Non</span>')
    #    except Exception:
    #        # En cas d'erreur, afficher simplement un tiret
    #        return format_html('<span>-</span>')
    #has_offre.short_description = _('Offre')
    #has_offre.boolean = True

    def offres_associees(self, obj):
        """Affiche les offres associées à cette opportunité"""
        # Chercher la bonne relation inverse pour les offres
        offres = []
        
        # Essayer différentes possibilités de nom de relation
        for attr in ['offres', 'offre_set', 'offres_commerciales']:
            if hasattr(obj, attr):
                try:
                    offres = getattr(obj, attr).all()
                    if offres.exists():
                        break
                except Exception:
                    continue
        
        if not offres:
            return _("Aucune offre associée")
        
        result = ['<ul>']
        for offre in offres:
            try:
                url = reverse("admin:offres_app_offre_change", args=[offre.id])
                status_display = getattr(offre, 'get_statut_display', lambda: offre.statut)()
                result.append('<li><a href="{}">{}</a> - {}</li>'.format(
                    url, offre.reference, status_display
                ))
            except Exception as e:
                result.append('<li>{} (Erreur: {})</li>'.format(
                    offre.reference, str(e)
                ))
        result.append('</ul>')
        return format_html(''.join(result))
    offres_associees.short_description = _('Offres associées')

    def convert_to_offre(self, request, queryset):
        """Action pour convertir les opportunités sélectionnées en offres"""
        success_count = 0
        error_count = 0
        for opportunite in queryset:
            try:
                opportunite.creer_offre(request.user)
                success_count += 1
            except ValueError:
                error_count += 1
                self.message_user(
                    request, 
                    f"Impossible de convertir l'opportunité {opportunite.reference} en offre", 
                    level='ERROR'
                )
        
        if success_count:
            self.message_user(
                request, 
                f"{success_count} opportunité(s) convertie(s) en offre avec succès."
            )
    convert_to_offre.short_description = _("Convertir en offre commerciale")

    def mark_as_won(self, request, queryset):
        """Action pour marquer les opportunités comme gagnées"""
        for opportunite in queryset:
            try:
                opportunite.gagner(request.user)
                opportunite.save()
            except Exception as e:
                self.message_user(
                    request, 
                    f"Erreur pour {opportunite.reference}: {str(e)}", 
                    level='ERROR'
                )
        self.message_user(request, _("Les opportunités ont été marquées comme gagnées."))
    mark_as_won.short_description = _("Marquer comme gagnées")

    def mark_as_lost(self, request, queryset):
        """Action pour marquer les opportunités comme perdues"""
        for opportunite in queryset:
            try:
                opportunite.perdre(request.user)
                opportunite.save()
            except Exception as e:
                self.message_user(
                    request, 
                    f"Erreur pour {opportunite.reference}: {str(e)}", 
                    level='ERROR'
                )
        self.message_user(request, _("Les opportunités ont été marquées comme perdues."))
    mark_as_lost.short_description = _("Marquer comme perdues")

    def update_relance(self, request, queryset):
        """Action pour mettre à jour les dates de relance"""
        for opportunite in queryset:
            if opportunite.statut not in ['GAGNEE', 'PERDUE']:
                opportunite.set_relance()
                opportunite.save(update_fields=['relance'])
        self.message_user(request, _("Les dates de relance ont été mises à jour."))
    update_relance.short_description = _("Mettre à jour les dates de relance")

    #def changelist_view(self, request, extra_context=None):
    #    """Ajoute des statistiques au-dessus de la liste des opportunités"""
    #    response = super().changelist_view(request, extra_context)
    #    
    #    if hasattr(response, 'context_data'):
    #        queryset = self.get_queryset(request)
    #        
    #        # Appliquer les filtres de la requête
    #        cl = response.context_data['cl']
    #        queryset = cl.get_queryset(request)
    #        
    #        # Calculer les sommes
    #        stats = queryset.aggregate(
    #            total_montant=Coalesce(Sum('montant'), 0, output_field=DecimalField()),
    #            total_estime=Coalesce(Sum('montant_estime'), 0, output_field=DecimalField()),
    #            total_pondere=Coalesce(Sum(F('montant_estime') * F('probabilite') / 100, 
    #                                      output_field=DecimalField()), 0)
    #        )
    #        
    #        # Ajouter les statistiques au contexte
    #        response.context_data['summary_stats'] = stats
    #        
    #        # Compter par statut
    #        status_counts = {}
    #        for status, label in Opportunite.STATUS_CHOICES:
    #            status_counts[status] = {
    #                'count': queryset.filter(statut=status).count(),
    #                'label': label
    #            }
    #        response.context_data['status_counts'] = status_counts
    #        
    #    return response