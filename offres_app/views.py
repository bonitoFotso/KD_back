# views.py
from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.decorators import action

from client.models import Client, Contact
from document.models import Entity, Product
from document.utils import log_user_action

from .models import Offre
from .serializers import (
    OffreSerializer, 
    OffreCreateSerializer,
    ClientSerializer, 
    ClientLightSerializer,
    ContactSerializer,
    OffreStatusChangeSerializer, 
    ProductSerializer,
    EntitySerializer,
    OffreNoteSerializer,
    OffreRelanceSerializer
)


class OffreViewSet(viewsets.ModelViewSet):
    """
    Viewset complet pour la gestion des offres (CRUD)
    """
    permission_classes = [IsAuthenticated]
    queryset = Offre.objects.all().order_by('date_creation')



    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return OffreCreateSerializer
        return OffreSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        offre = serializer.instance
        log_user_action(
            user=self.request.user,
            action_type='CREATE',
            instance=offre,
            description=f"creations de l'offre {offre.reference}",
            request=self.request
        )
        
    def perform_update(self, serializer):
        offre = serializer.instance
        log_user_action(
            user=self.request.user,
            action_type='UPDATE',
            instance=offre,
            description=f"Modification de l'offre {offre.reference}",
            request=self.request
        )
        return super().perform_update(serializer)
        
    @action(detail=True, methods=['put'])
    def update_status(self, request, pk=None):
        """
        Met à jour le statut d'une offre.
        """
        offre = self.get_object()
        ancien_statut = offre.status
        serializer = OffreStatusChangeSerializer(offre, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            log_user_action(
            user=request.user,
            action_type='STATUS_CHANGE',
            instance=offre,
            field_name='status',
            old_value=ancien_statut,
            new_value=offre.status,
            description=f"Changement de statut de l'offre #{offre.id}",
            request=request
        )
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# view pour prolonger la relance
class OffreRelanceProlongationView(generics.UpdateAPIView):
    """
    Vue pour prolonger la date de relance d'une offre
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OffreRelanceSerializer
    queryset = Offre.objects.all()
    
    def perform_update(self, serializer):
        # Prolongation de la date de relance de l'offre
        instance = serializer.instance
        old_relance_date = instance.relance
        
        # On prolonge la date de relance de 7 jours
        instance.set_relance()
        
        serializer.save()
        log_user_action(
            user=self.request.user,
            action_type='UPDATE',
            instance=serializer.instance,
            field_name='relance',
            old_value=old_relance_date,
            new_value=instance.relance,
            description=f"Prolongation de la date de relance de l'offre #{instance.id}",
            request=self.request
        )
        return Response(serializer.data)
# views pour modifier les notes et la date de relance
class OffreNoteView(generics.UpdateAPIView):
    """
    Vue pour modifier les notes d'une offre
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OffreNoteSerializer
    queryset = Offre.objects.all()
    
    
    def perform_update(self, serializer):
        # Met à jour les notes de l'offre
        instance = serializer.instance
        old_note = instance.notes
        
        serializer.save()
        log_user_action(
            user=self.request.user,
            action_type='UPDATE',
            instance=serializer.instance,
            field_name='notes',
            old_value=old_note,
            new_value=instance.notes,
            description=f"Changement de notes de l'offre #{instance.id}",
            request=self.request
        )
        
class OffreRelanceView(generics.UpdateAPIView):
    """
    Vue pour modifier la date de relance d'une offre
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OffreRelanceSerializer
    queryset = Offre.objects.all()
    
    def perform_update(self, serializer):
        # Met à jour la date de relance de l'offre
        serializer.save()

class OffreInitDataView(APIView):
    """
    Vue pour récupérer toutes les données nécessaires à l'initialisation 
    du formulaire de création d'offre en une seule requête
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        print("OffreInitDataView")
        # Récupération des données nécessaires
        clients = Client.objects.all().order_by('nom')
        entities = Entity.objects.all().order_by('code')
        
        # Les produits les plus utilisés dans les offres récentes (top 10)
        popular_products = Product.objects.annotate(
            usage_count=Count('offres')
        ).order_by('-usage_count')[:10]
        produits = Product.objects.all().order_by('code')
        contacts = Contact.objects.all().order_by('nom')
        
        # Sérialisation des données
        data = {
            'clients': ClientLightSerializer(clients, many=True).data,
            'entities': EntitySerializer(entities, many=True).data,
            'produits': ProductSerializer(produits, many=True).data,
            'contacts': ContactSerializer(contacts, many=True).data,
            
        }
        
        return Response(data)


class ClientListView(generics.ListAPIView):
    """
    Liste des clients disponibles pour la création d'offre
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ClientLightSerializer
    
    def get_queryset(self):
        queryset = Client.objects.all().order_by('nom')
        
        # Filtrage par nom ou numéro client
        search = self.request.GET.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) | 
                Q(c_num__icontains=search)
            )
        
        return queryset


class ContactsByClientView(generics.ListAPIView):
    """
    Liste des contacts associés à un client spécifique
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ContactSerializer
    
    def get_queryset(self):
        client_id = self.kwargs.get('client_id')
        return Contact.objects.filter(client_id=client_id).order_by('nom')


class EntityListView(generics.ListAPIView):
    """
    Liste des entités disponibles
    """
    permission_classes = [IsAuthenticated]
    queryset = Entity.objects.all().order_by('code')
    serializer_class = EntitySerializer


class ProductListView(generics.ListAPIView):
    """
    Liste des produits disponibles pour la création d'offre
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer
    
    def get_queryset(self):
        queryset = Product.objects.all().order_by('designation')
        
        # Filtrage par désignation ou code
        search = self.request.GET.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(designation__icontains=search) | 
                Q(code__icontains=search)
            )
        
        # Filtrage par catégorie
        category = self.request.GET.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset


class OffreDraftView(generics.CreateAPIView):
    """
    Création d'un brouillon d'offre
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OffreCreateSerializer

    def perform_create(self, serializer):
        # Force le statut à 'BROUILLON'
        serializer.save(user=self.request.user, statut='BROUILLON')


from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class OffreStatusUpdateView(generics.UpdateAPIView):
    """
    Vue de base pour la mise à jour du statut d'une offre
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OffreStatusChangeSerializer
    queryset = Offre.objects.all()
    target_status = None
    required_status = None
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        ancien_statut = instance.statut 
        # Vérification que l'offre est dans le statut requis
        if instance.statut != self.required_status:
            return Response(
                {
                    "success": False,
                    "detail": f"Seules les offres en statut {self.required_status} peuvent être modifiées.",
                    "code": "invalid_status",
                    "current_status": instance.statut
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Sauvegarde du statut précédent pour la réponse
        previous_status = instance.statut
            
        # Mise à jour du statut
        instance.statut = self.target_status

        # Récupération des dates depuis le frontend
        if self.target_status == 'ENVOYE':
            date_envoi = request.data.get('date_envoi')
            if date_envoi:
                instance.date_envoi = date_envoi
        elif self.target_status == 'GAGNE':
            date_validation = request.data.get('date_validation')
            if date_validation:
                instance.date_validation = date_validation
        elif self.target_status == 'PERDU':
            date_cloture = request.data.get('date_cloture')
            if date_cloture:
                instance.date_cloture = date_cloture

        log_user_action(
            user=request.user,
            action_type='STATUS_CHANGE',
            instance=instance,
            field_name='status',
            old_value=ancien_statut,
            new_value=instance.statut,
            description=f"Changement de statut de l'offre #{instance.id}",
            request=request
        )
        instance.save()
        
        # Configuration de la date de relance
        instance.set_relance()
        instance.save()
        
        serializer = self.get_serializer(instance)
        
        # Construction d'une réponse enrichie pour le frontend
        response_data = {
            "success": True,
            "message": f"L'offre a été mise à jour avec succès de {previous_status} à {self.target_status}",
            "data": serializer.data,
            "previous_status": previous_status,
            "current_status": self.target_status,
        }
        
        return Response(response_data)
        
        def partial_update(self, request, *args, **kwargs):
        # Pour les mises à jour partielles, on utilise la même logique que update()
            return self.update(request, *args, **kwargs)


class OffreSubmitView(OffreStatusUpdateView):
    """
    Soumission d'une offre (changement de statut en 'ENVOYE')
    """
    target_status = 'ENVOYE'
    required_status = 'BROUILLON'
class OffreWonView(OffreStatusUpdateView):
    """
    Marquer une offre comme gagnée (changement de statut en 'GAGNE')
    """
    target_status = 'GAGNE'
    required_status = 'ENVOYE'
class OffreLostView(OffreStatusUpdateView):
    """
    Marquer une offre comme perdue (changement de statut en 'PERDU')
    """
    target_status = 'PERDU'
    required_status = 'ENVOYE'
    
    
class OffreStatusChangeView(generics.UpdateAPIView):
    """
    Changement de statut d'une offre (GAGNE ou PERDU)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OffreSerializer
    queryset = Offre.objects.all()

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        new_status = request.data.get('statut')
        
        # Vérification que le nouveau statut est valide
        if new_status not in ['GAGNE', 'PERDU']:
            return Response(
                {"detail": "Le statut doit être GAGNE ou PERDU."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mise à jour du statut
        instance.statut = new_status
        
        # Si l'offre est gagnée, définir la date de validation
        if new_status == 'GAGNE':
            instance.date_validation = timezone.now()
        
        instance.save()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    
from rest_framework import status, views, parsers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.conf import settings
import os
from .models import Offre

class OffreFileUploadView(views.APIView):
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk=None):
        """
        Upload un fichier pour une offre spécifique.
        
        Le fichier est enregistré dans le système de fichiers et le chemin est 
        mis à jour dans l'objet Offre correspondant.
        """
        # Récupérer l'objet offre ou retourner 404
        offre = get_object_or_404(Offre, pk=pk)
        old_file = offre.fichier
        # Vérifier que l'utilisateur a les permissions (exemple: propriétaire ou staff)
        if not request.user.is_staff : #and offre.created_by != request.user:
            return Response(
                {"detail": "Vous n'avez pas la permission d'uploader des fichiers pour cette offre."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Vérifier si un fichier a été envoyé
        if 'file' not in request.FILES:
            return Response(
                {"detail": "Aucun fichier n'a été fourni."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        
        # Validation du type de fichier (optionnel)
        allowed_extensions = ['.pdf', '.docx', '.xlsx', '.pptx', '.doc', '.xls']
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        if file_extension not in allowed_extensions:
            return Response(
                {"detail": f"Type de fichier non autorisé. Extensions acceptées: {', '.join(allowed_extensions)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Création du dossier de destination si nécessaire
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'offres', str(pk))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Définir le chemin du fichier
        filename = f"offre_{pk}_{uploaded_file.name}"
        file_path = os.path.join(upload_dir, filename)
        
        # Sauvegarder le fichier
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        # Mettre à jour le chemin du fichier dans l'objet Offre
        relative_path = os.path.join('offres', str(pk), filename)
        from django.core.files import File
        with open(file_path, 'rb') as f:
            log_user_action(
            user=request.user,
            action_type='UPDATE',
            instance=offre,
            field_name='fichier',
            old_value=old_file,
            new_value=file_path,
            description=f"Changement de fichier de l'offre #{offre.pk}",
            request=request
        )
            offre.fichier.save(filename, File(f), save=True)
        
        # Sérialiser et retourner l'objet offre mis à jour
        serializer = OffreSerializer(offre)
        
        return Response(serializer.data, status=status.HTTP_200_OK)