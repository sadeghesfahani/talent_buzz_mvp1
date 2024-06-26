from django.urls import path
from .views import download_document

urlpatterns = [
    path('download/<int:document_id>', download_document, name='download_document'),
]