from django.urls import path
from .views import download_document, download_avatar

urlpatterns = [
    path('download/<int:document_id>', download_document, name='download_document'),
    path('avatars/<str:file_name>', download_avatar, name='download_avatar'),
]