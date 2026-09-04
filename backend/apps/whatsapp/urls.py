from django.urls import path

from apps.whatsapp import views
from apps.whatsapp.views_contacts import WhatsAppContactViewSet

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
    path(
        "whatsapp/contacts",
        WhatsAppContactViewSet.as_view({"get": "list", "post": "create"}),
        name="whatsapp-contact-list",
    ),
    path(
        "whatsapp/contacts/<int:pk>",
        WhatsAppContactViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="whatsapp-contact-detail",
    ),
]
