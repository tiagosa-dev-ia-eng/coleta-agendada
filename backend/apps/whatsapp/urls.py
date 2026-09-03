from django.urls import path

from apps.whatsapp import views

urlpatterns = [
    path(
        "webhooks/whatsapp",
        views.InboundWhatsAppView.as_view(),
        name="whatsapp-webhook",
    ),
    path(
        "whatsapp/conversations",
        views.ConversationListView.as_view(),
        name="whatsapp-conversation-list",
    ),
    path(
        "whatsapp/conversations/by-phone/<str:phone>",
        views.ConversationByPhoneView.as_view(),
        name="whatsapp-conversation-by-phone",
    ),
]
