from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    username = models.CharField(max_length=255, unique=True)
    def __str__(self):
        return f"{self.user.username}'s profile"
class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="conversations")
    conversation_name = models.CharField(max_length=255, default="New Conversation")
    datatime = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=255, default="pdf")
    def __str__(self):
        return f"conversation name : {self.conversation_name}"
class Message(models.Model):
    class RoleChoices(models.TextChoices):
        ASSISTANT= 'Assistant'
        USER = 'user'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.TextField()
    reference_links = models.TextField(null=True)
    role = models.CharField(max_length=20, choices=RoleChoices.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    status =models.CharField(max_length=20, choices=[('sent','Sent'), ('delivered', 'Delivered'), ('read', 'Read')], default='sent')
    Conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    def __str__(self):
        return f'Message id: {self.id}'


