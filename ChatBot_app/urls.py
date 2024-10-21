from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from .views import UserProfileViewSet, ConversationViewSet, MessageViewSet, login_view, LogoutView, register_view, get_profile_and_conversation_id
from django.contrib.auth import views as auth_views

router = DefaultRouter()
router.register(r'user-profiles', UserProfileViewSet, basename='userprofile')

conversation_router = NestedDefaultRouter(router, r'user-profiles', lookup='user_profile')
conversation_router.register(r'conversations', ConversationViewSet, basename='conversation')

message_router = NestedDefaultRouter(conversation_router, r'conversations', lookup='conversation')
message_router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile-id/', get_profile_and_conversation_id, name='get_profile_conversation_id'),
    path('', include(router.urls)),
    path('', include(conversation_router.urls)),
    path('', include(message_router.urls)),
    # path('api/auth/login/', login_view, name='azure_ad_login'),
    # path('api/auth/callback/', login_view, name='azure_ad_callback'),
]
