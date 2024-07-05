from django.urls import path
from . import views
from .views import webhook_view

urlpatterns = [
    path("webhooks/", webhook_view,  name="webhooks"),
    path("blogposts/", views.BlogPostListCreate.as_view() , name="blogpost-view-create"),
    path("blogposts/<int:pk>/", views.BlogPostRetrieveUpdateDestroy.as_view(), name="update"),
    path("translate/", views.TranslateListCreate.as_view() , name="Translate-view-create"),
    path("translate/<int:pk>/", views.TranslateRetrieveUpdateDestroy.as_view(), name="update"),
    path("voice_translate/", views.VoiceTranslateListCreate.as_view(), name="Voice-Translate-view-create"),
    path("voice_translate/<int:pk>/", views.VoiceTranslateRetrieveUpdateDestroy.as_view(), name="update"),
]
