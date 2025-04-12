from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum, Q
from django.utils.timezone import now
from django.shortcuts import get_object_or_404

from api import user
from api.user.models import User
from api.user.serializers import UserSerializer
from document.utils import log_user_action
from offres_app.models import Offre
from offres_app.serializers import OffreSerializer

from .models import Affaire
from document.models import Rapport, Formation
from .serializers import (
    AffaireSerializer, 
    AffaireDetailSerializer, 
    AffaireCreateSerializer,
    RapportSerializer,
    FactureSerializer,
    ChangeStatutSerializer,
    DashboardSerializer
)
from .filters import AffaireFilter
from .permissions import AffairePermission


class AffaireViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des affaires.
    Fournit les opérations CRUD standard ainsi que des actions personnalisées.
    """
    queryset = Affaire.objects.all()
    permission_classes = [IsAuthenticated, AffairePermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AffaireFilter
    search_fields = ['reference', 'offre__client__nom']
    ordering_fields = ['date_creation', 'date_debut', 'date_fin_prevue', 'montant_total', 'statut']
    ordering = ['-date_creation']

    def get_serializer_class(self):
        """Sélectionne le sérialiseur approprié selon l'action."""
        if self.action == ['create', 'update']:
            return AffaireCreateSerializer
        elif self.action in ['rapports', 'factures']:
            return AffaireDetailSerializer
        elif self.action == 'change_statut':
            return ChangeStatutSerializer
        return AffaireDetailSerializer

    def perform_create(self, serializer):
        """Enregistre l'utilisateur courant comme créateur lors de la création."""
        serializer.save(created_by=self.request.user)
        aff = serializer.instance
        log_user_action(
            user=self.request.user,
            action_type='CREATE',
            instance=aff,
            description=f"creations de l'offre {aff.reference}",
            request=self.request
        )
        
    
    
    @action(detail=True, methods=['post'])
    def change_statut(self, request, pk=None):
        """
        Change le statut d'une affaire.
        """
        affaire = self.get_object()
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            nouveau_statut = serializer.validated_data['statut']
            commentaire = serializer.validated_data.get('commentaire', '')
            
            # Appel de la méthode du modèle pour changer le statut
            affaire.mettre_a_jour_statut(
                nouveau_statut=nouveau_statut,
                utilisateur=request.user,
                commentaire=commentaire
            )
            
            return Response({
                'success': True,
                'statut': nouveau_statut,
                'message': f"Statut de l'affaire mis à jour vers '{nouveau_statut}'"
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def rapports(self, request, pk=None):
        """
        Liste les rapports associés à une affaire.
        """
        affaire = self.get_object()
        rapports = Rapport.objects.filter(affaire=affaire)
        serializer = RapportSerializer(rapports, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def initData(self, request, pk=None):
        """
        Liste des element necesaire a la creation d'une affaire
        """
        offres = Offre.objects.filter(statut='GAGNE')
        offres_serializer = OffreSerializer(offres, many=True)
        
        users = User.objects.all()
        user_serializer = UserSerializer(users, many=True)
        
        return Response({
            'offres': offres_serializer.data,
            'users': user_serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def factures(self, request, pk=None):
        """
        Liste les factures associées à une affaire.
        """
        affaire = self.get_object()
        factures = Facture.objects.filter(affaire=affaire)
        serializer = FactureSerializer(factures, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def generer_facture(self, request, pk=None):
        """
        Génère une nouvelle facture pour l'affaire.
        """
        affaire = self.get_object()
        
        # Vérification du montant restant à facturer
        montant_restant = affaire.get_montant_restant_a_facturer()
        if montant_restant <= 0:
            return Response({
                'success': False,
                'message': "Le montant total a déjà été entièrement facturé"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Création de la facture
        facture = affaire.cree_facture_initiale()
        if not facture:
            return Response({
                'success': False,
                'message': "Impossible de créer la facture"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = FactureSerializer(facture)
        return Response({
            'success': True,
            'message': "Facture générée avec succès",
            'facture': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def marquer_rapport_termine(self, request, pk=None):
        """
        Marque un rapport spécifique comme terminé.
        """
        affaire = self.get_object()
        rapport_id = request.data.get('rapport_id')
        
        if not rapport_id:
            return Response({
                'success': False,
                'message': "L'ID du rapport est requis"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            rapport = Rapport.objects.get(id=rapport_id, affaire=affaire)
            rapport.statut = 'VALIDE'
            rapport.save()
            
            # Journalisation de l'action
            affaire.log_event(
                titre="Rapport terminé",
                description=f"Le rapport pour {rapport.produit.name} a été marqué comme terminé"
            )
            
            return Response({
                'success': True,
                'message': "Rapport marqué comme terminé avec succès"
            })
        except Rapport.DoesNotExist:
            return Response({
                'success': False,
                'message': "Rapport non trouvé pour cette affaire"
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """
        Fournit les données pour le mini tableau de bord.
        """
        # Compteurs par statut
        compteurs_statut = Affaire.objects.values('statut').annotate(
            count=Count('id')
        ).order_by('statut')

        # Dernières affaires créées
        dernieres_affaires = Affaire.objects.order_by('-date_creation')[:5]
        dernieres_affaires_serialized = AffaireSerializer(dernieres_affaires, many=True).data

        # Affaires en retard
        affaires_en_retard = Affaire.objects.filter(
            statut='EN_COURS',
            date_fin_prevue__lt=now()
        ).order_by('date_fin_prevue')[:5]
        affaires_en_retard_serialized = AffaireSerializer(affaires_en_retard, many=True).data

        # Résumé financier
        resume_financier = {
            'montant_total': Affaire.objects.aggregate(Sum('montant_total'))['montant_total__sum'] or 0,
            'montant_facture': Affaire.objects.aggregate(Sum('montant_facture'))['montant_facture__sum'] or 0,
            'montant_paye': Affaire.objects.aggregate(Sum('montant_paye'))['montant_paye__sum'] or 0,
        }

        # Construire la réponse directement sans utiliser DashboardSerializer
        data = {
            'compteurs_statut': compteurs_statut,
            'dernieres_affaires': dernieres_affaires_serialized,
            'affaires_en_retard': affaires_en_retard_serialized,
            'resume_financier': resume_financier
        }

        return Response(data)
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """
        Exporte la liste des affaires en CSV.
        """
        from django.http import HttpResponse
        import csv
        
        # Application des filtres
        queryset = self.filter_queryset(self.get_queryset())
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="affaires.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Référence', 'Client', 'Date de début', 'Date de fin prévue', 
            'Statut', 'Montant total', 'Montant facturé', 'Montant payé'
        ])
        
        for affaire in queryset:
            writer.writerow([
                affaire.reference,
                affaire.offre.client.nom,
                affaire.date_debut.strftime('%d/%m/%Y'),
                affaire.date_fin_prevue.strftime('%d/%m/%Y') if affaire.date_fin_prevue else '',
                dict(Affaire.STATUT_CHOICES).get(affaire.statut, affaire.statut),
                affaire.montant_total,
                affaire.montant_facture,
                affaire.montant_paye
            ])
        
        return response
    
    @action(detail=True, methods=['get'])
    def export_pdf(self, request, pk=None):
        """
        Exporte la fiche affaire en PDF.
        """
        from django.http import FileResponse
        #from reportlab.pdfgen import canvas
        #from reportlab.lib.pagesizes import A4
        from io import BytesIO
        
        affaire = self.get_object()
        
        # Création du PDF en mémoire
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        # En-tête
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, 800, f"Affaire : {affaire.reference}")
        
        # Informations générales
        p.setFont("Helvetica", 12)
        p.drawString(50, 760, f"Client : {affaire.offre.client.nom}")
        p.drawString(50, 740, f"Statut : {dict(Affaire.STATUT_CHOICES).get(affaire.statut, affaire.statut)}")
        p.drawString(50, 720, f"Date de début : {affaire.date_debut.strftime('%d/%m/%Y')}")
        if affaire.date_fin_prevue:
            p.drawString(50, 700, f"Date de fin prévue : {affaire.date_fin_prevue.strftime('%d/%m/%Y')}")
        
        # Informations financières
        p.drawString(50, 670, f"Montant total : {affaire.montant_total} €")
        p.drawString(50, 650, f"Montant facturé : {affaire.montant_facture} €")
        p.drawString(50, 630, f"Montant payé : {affaire.montant_paye} €")
        
        # Liste des produits
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, 590, "Liste des produits")
        
        p.setFont("Helvetica", 12)
        y_position = 570
        for i, produit in enumerate(affaire.offre.produits.all()):
            p.drawString(50, y_position, f"{i+1}. {produit.name}")
            y_position -= 20
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=f'affaire_{affaire.reference}.pdf')