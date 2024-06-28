from django.http import FileResponse
from .models import Document


def download_document(request, document_id):
    document = Document.objects.get(id=document_id)
    file_path = document.document.path
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=document.document.name)


def download_avatar(request, file_name):
    return FileResponse(open(f'avatars/{file_name}', 'rb'), filename=file_name)