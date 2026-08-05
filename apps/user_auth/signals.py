from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from apps.core.models import EmailRecipient, EmailRecipientList
from apps.user_auth.models import Profile


@receiver(post_save, sender=Profile)
def sync_newsletter_recipient(sender, instance, **kwargs):
    try:
        newsletter_list = EmailRecipientList.objects.get(name='newsletter')
    except EmailRecipientList.DoesNotExist:
        return
    email = instance.user.email
    if not email:
        return
    if instance.newsletter:
        EmailRecipient.objects.get_or_create(
            email=email,
            defaults={'recipient_list': newsletter_list},
        )
    else:
        EmailRecipient.objects.filter(email=email, recipient_list=newsletter_list).delete()


@receiver(pre_delete, sender=Profile)
def remove_newsletter_recipient(sender, instance, **kwargs):
    try:
        newsletter_list = EmailRecipientList.objects.get(name='newsletter')
    except EmailRecipientList.DoesNotExist:
        return
    email = instance.user.email
    if email:
        EmailRecipient.objects.filter(email=email, recipient_list=newsletter_list).delete()
