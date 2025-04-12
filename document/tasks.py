from celery import shared_task
from django.utils import timezone
from notifications.models import Notification

@shared_task
def check_relances():
    """
    Vérifie les relances à effectuer aujourd'hui
    """
    today = timezone.now().date()
    notifications_due = Notification.objects.filter(
        scheduled_date=today,
        unread=True
    )
    
    for notification in notifications_due:
        # Envoi d'un email par exemple
        send_relance_email(notification)

def send_relance_email(notification):
    """
    Envoie un email de relance
    """
    subject = f"Relance à effectuer - {notification.target}"
    message = f"""
    Une relance est à effectuer aujourd'hui pour :
    Client: {notification.action_object}
    Offre: {notification.target}
    """
    # Logique d'envoi d'email