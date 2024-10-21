from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from .models import Message, Conversation, UserProfile
from .serializers import MessageSerializer, ConversationSerializer, UserProfileSerializer
from .Generative_AI_code.AzureAISearch import *
from .llama_index.core.llms import ChatMessage, MessageRole

@api_view(['POST'])
def register_view(request):
    username = request.data.get("username")
    password = request.data.get("password")
    email = request.data.get("email")

    if not User.objects.filter(username=username).exists():
        User.objects.create_user(username=username, password=password, email=email)
        return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)
    return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(username=username, password=password)

    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)
    return Response({"error": "Invalid Credentials"}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if UserProfile.objects.filter(user=self.request.user).exists():
            raise ValidationError("User profile already exists.")
        serializer.save(user=self.request.user, username=self.request.user.username)

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(user_profile__user=self.request.user).order_by("-datetime")

    def perform_create(self, serializer):
        user_profile = UserProfile.objects.get(user=self.request.user)
        serializer.save(user_profile=user_profile)

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs['conversation_pk']
        return Message.objects.filter(conversation=conversation_id, conversation__user_profile__user=self.request.user).order_by('timestamp')

    def perform_create(self, serializer):
        conversation_id = self.kwargs.get('conversation_pk')
        user_profile = get_object_or_404(UserProfile, user=self.request.user)

        if conversation_id:
            conversation = get_object_or_404(Conversation, id=conversation_id, user_profile=user_profile)
        else:
            conversation = Conversation.objects.create(user_profile=user_profile)
        
        serializer.save(conversation=conversation)

        # If the message is from the user, generate a response from the chatbot
        if serializer.validated_data['role'] == 'user':
            messages = Message.objects.filter(conversation=conversation).order_by('created_at')
            chat_history = [
                ChatMessage(role=message.role, content=message.content)
                for message in messages
            ]
            user_query = serializer.validated_data['content']
            excel_name = conversation.filename
            obj1 = azureAI_response(user_query)
            response_content, reference_links = obj1.llamachatengine(chat_history)

            

            Message.objects.create(
                content=response_content,
                role='assistant',
                conversation=conversation,
                reference_links=reference_links
            )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile_and_conversation_id(request):
    profile_id = request.user.id
    conversation_id = request.query_params.get('conversation_id', None)
    return Response({"profile_id": profile_id, "conversation_id": conversation_id})



