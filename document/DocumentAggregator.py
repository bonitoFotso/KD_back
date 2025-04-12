from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Prefetch
from collections import OrderedDict
from document.mod import AttestationFormationSerializer, FormationDetailSerializer
from document.models import Affaire, AttestationFormation, Client, Entity, Facture, Formation, Offre, Participant, Product, Proforma, Rapport, Site
from document.serializers import AffaireSerializer, FactureSerializer, OffreSerializer, ProformaSerializer, RapportSerializer

from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from collections import OrderedDict
from datetime import datetime
from django.utils.dateparse import parse_datetime as django_parse_datetime
from django.utils.timezone import make_aware, get_current_timezone
def parse_datetime(date_str):
    """
    Parse une chaîne de date dans plusieurs formats possibles.
    Retourne un objet datetime aware (avec timezone) ou None si le parsing échoue.
    """
    if not date_str:
        return None

    # Si c'est déjà un datetime
    if isinstance(date_str, datetime):
        return make_aware(date_str) if date_str.tzinfo is None else date_str

    # Liste des formats de date possibles
    date_formats = [
        '%Y-%m-%d',  # 2025-01-09
        '%d/%m/%Y',  # 09/01/2025
        '%Y-%m-%d %H:%M:%S',  # 2025-01-09 15:30:00
        '%Y-%m-%dT%H:%M:%S',  # 2025-01-09T15:30:00
        '%Y-%m-%dT%H:%M:%S.%f',  # 2025-01-09T15:30:00.000
        '%Y-%m-%dT%H:%M:%S.%fZ',  # 2025-01-09T15:30:00.000Z
        '%d-%m-%Y',  # 09-01-2025
        '%d-%m-%Y %H:%M:%S',  # 09-01-2025 15:30:00
    ]

    # Essayer d'abord le parser de Django
    parsed_date = django_parse_datetime(date_str)
    if parsed_date:
        return make_aware(parsed_date) if parsed_date.tzinfo is None else parsed_date

    # Essayer tous les formats
    for date_format in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, date_format)
            return make_aware(parsed_date, timezone=get_current_timezone())
        except ValueError:
            continue

    # Si la chaîne contient seulement une date (sans heure)
    try:
        parsed_date = datetime.strptime(date_str.split()[0], '%Y-%m-%d')
        return make_aware(parsed_date, timezone=get_current_timezone())
    except (ValueError, IndexError):
        return None
    
class DocumentAggregatorView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Récupérer tous les documents avec leurs relations
            offres = Offre.objects.select_related(
                'client',
                'proforma',
                'entity'
            ).prefetch_related(
                'produit',
                'sites'
            )

            affaires = Affaire.objects.select_related(
                'offre__client',
                'offre__entity',
                'facture'
            ).prefetch_related(
                'rapports__site',
                'rapports__produit',
                'formations__participants',
                'attestations__participant'
            )

            # Initialiser le dictionnaire de réponse
            response_data = OrderedDict({
                'documents': {
                    'offres': [],
                    'affaires': [],
                    'proformas': [],
                    'factures': [],
                    'rapports': [],
                    'formations': [],
                    'attestations': []
                },
                'metadata': {
                    'total_documents': 0,
                    'documents_par_type': {}
                }
            })

            # Sérialiser les offres
            for offre in offres:
                offre_data = OffreSerializer(offre).data
                response_data['documents']['offres'].append(offre_data)

            # Sérialiser les affaires et leurs documents associés
            for affaire in affaires:
                affaire_data = AffaireSerializer(affaire).data
                response_data['documents']['affaires'].append(affaire_data)
                
                # Ajouter les proformas
                if hasattr(affaire.offre, 'proforma'):
                    proforma_data = ProformaSerializer(affaire.offre.proforma).data
                    response_data['documents']['proformas'].append(proforma_data)
                
                # Ajouter la facture
                if hasattr(affaire, 'facture'):
                    facture_data = FactureSerializer(affaire.facture).data
                    response_data['documents']['factures'].append(facture_data)
                
                # Ajouter les rapports
                rapports_data = RapportSerializer(affaire.rapports.all(), many=True).data
                response_data['documents']['rapports'].extend(rapports_data)
                
                # Ajouter les formations
                formations_data = FormationDetailSerializer(affaire.formations.all(), many=True).data
                response_data['documents']['formations'].extend(formations_data)
                
                # Ajouter les attestations
                attestations_data = AttestationFormationSerializer(affaire.attestations.all(), many=True).data
                response_data['documents']['attestations'].extend(attestations_data)

            # Calculer les métadonnées
            for doc_type, docs in response_data['documents'].items():
                response_data['metadata']['documents_par_type'][doc_type] = len(docs)
                response_data['metadata']['total_documents'] += len(docs)

            # Ajouter des filtres si spécifiés dans la requête
            filters = request.query_params.dict()
            if filters:
                filtered_data = self.apply_filters(response_data['documents'], filters)
                response_data['documents'] = filtered_data
                # Recalculer les métadonnées pour les données filtrées
                response_data['metadata'] = {
                    'total_documents': sum(len(docs) for docs in filtered_data.values()),
                    'documents_par_type': {
                        doc_type: len(docs) for doc_type, docs in filtered_data.items()
                    }
                }

            return Response(response_data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def apply_filters(self, documents, filters):
        """
        Applique les filtres spécifiés aux documents.
        """
        filtered_docs = OrderedDict()
        
        for doc_type, docs in documents.items():
            filtered_docs[doc_type] = []
            
            for doc in docs:
                match = True
                for key, value in filters.items():
                    # Gestion des filtres de date
                    if 'date' in key.lower():
                        try:
                            doc_date = parse_datetime(doc.get(key, ''))
                            filter_date = parse_datetime(value)
                            if doc_date and filter_date:
                                if doc_date.date() != filter_date.date():
                                    match = False
                                    break
                        except:
                            continue
                    # Filtres de texte standard
                    elif key in doc and str(doc[key]).lower() != str(value).lower():
                        match = False
                        break
                
                if match:
                    filtered_docs[doc_type].append(doc)
                    
        return filtered_docs

# Ajoutez cette configuration des URLs
from django.urls import path

urlpatterns = [
    path('documents/', DocumentAggregatorView.as_view(), name='document-aggregator'),
    # ... vos autres URLs ...
]