from django.contrib.auth.models import Group, User
from rest_framework import serializers
from .models import UserProfile, Conversation, Message

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'
class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only = True)
    class Meta:
        model = Conversation
        fields = ["id", "user_profile", "conversation_name", 'datetime', 'modified_at', 'filename', 'messages']
class UserProfileSerializer(serializers.ModelSerializer):
    conversation = ConversationSerializer(many=True, read_only=True)
    class Meta:
        model = UserProfile
        fields = '__all__'


