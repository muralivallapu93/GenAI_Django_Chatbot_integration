from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth.models import User
from .models import UserProfile, Conversation, Message

@receiver(post_save, sender= User)
def created_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance, username=instance.username)
@receiver(post_save, sender= Message)
def update_conversation_update_time(sender, instance, **kwargs):
    instance.conversation.modified_at = timezone.now()
    instance.conversation.save()