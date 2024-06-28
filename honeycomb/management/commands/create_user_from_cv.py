import os
import time

from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand

from ai.helpers import AIBaseClass
from ai.services import AIService
from common.models import Document  # Assuming this is your Document model

User = get_user_model()


class Command(BaseCommand):
    help = 'Read files from a specified directory, create Document objects for the admin user, and process them with AI.'

    def add_arguments(self, parser):
        # Positional mandatory argument
        parser.add_argument('directory_path', type=str, help='Path to the directory containing the CV files')

    def handle(self, *args, **options):
        directory_path = options['directory_path']
        admin_user = self.get_admin_user()
        if not admin_user:
            self.stdout.write(self.style.ERROR('Admin user not found. Please ensure an admin user exists.'))
            return

        if not os.path.isdir(directory_path):
            self.stdout.write(self.style.ERROR(f'The specified directory does not exist: {directory_path}'))
            return

        document_ids = []
        document_queryset = []
        for filename in os.listdir(directory_path):
            if self.validate_file_format(filename):
                file_path = os.path.join(directory_path, filename)
                document = self.create_document(file_path, admin_user)
                if document:
                    document_ids.append(document.id)
                    document_queryset.append(document)
            else:
                self.stdout.write(self.style.WARNING(f'Skipped invalid file format: {filename}'))

        # Waiting for all files to obtain their file_ids or timeout
        self.wait_for_file_ids(document_ids)
        ai_helper = AIBaseClass("backend_assistant")
        ai_helper.add_documents_to_vector_store(ai_helper.base_vector_store, document_queryset)

        # Process each document with AI after file_id is obtained
        for document_id in document_ids:
            document = Document.objects.get(id=document_id)
            if document.file_id:
                self.process_with_ai(document)
            else:
                self.stdout.write(self.style.ERROR(f'Document {document_id} did not receive a file_id'))

    def wait_for_file_ids(self, document_ids, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Count the documents that have a non-null file_id
            count_with_file_id = Document.objects.filter(id__in=document_ids, file_id__isnull=False).count()

            # Check if the number of documents with file_ids matches the total number of documents
            if count_with_file_id == len(document_ids):
                return  # All documents have file_ids; exit the loop
            print("put fetching file_ids into sleep for 2 seconds")
            time.sleep(2)  # Wait for 10 seconds before checking again
        else:
            # This block executes if the while loop completes without returning (i.e., timeout reached)
            self.stdout.write(self.style.ERROR('Timeout reached while waiting for file_ids'))


    def process_with_ai(self, document):
        ai_service = AIService(document.user, "backend_assistant")

        # AI implementation comes here
        # Example placeholder:
        self.stdout.write(self.style.SUCCESS(f'Processing document {document.id} with AI'))

        ai_service.review_document_with_file_id(document.file_id)

    def validate_file_format(self, filename):
        valid_extensions = {'pdf', 'doc', 'docx'}  # Define acceptable formats
        return any(filename.lower().endswith(ext) for ext in valid_extensions)

    def create_document(self, file_path, user):
        try:
            # Copy file to the Django media folder
            with open(file_path, 'rb') as file:
                django_file = File(file)
                document = Document(user=user)
                document.document.save(os.path.basename(file_path), django_file, save=True)
            self.stdout.write(self.style.SUCCESS(f'Successfully processed {file_path}'))
            return document
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating document for {file_path}: {str(e)}'))
            return None

    def get_admin_user(self):
        # Gets the first admin user; adjust accordingly if your criteria differ
        return User.objects.filter(is_superuser=True).first()
