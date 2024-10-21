from django.apps import AppConfig


class ChatbotAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ChatBot_app'
    
    def ready(self):
        import ChatBot_app.singals
