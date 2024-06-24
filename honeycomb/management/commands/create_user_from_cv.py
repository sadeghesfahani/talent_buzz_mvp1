import os
import time
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files import File
from common.models import Document  # Assuming this is your Document model
from django.conf import settings

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
        for filename in os.listdir(directory_path):
            if self.validate_file_format(filename):
                file_path = os.path.join(directory_path, filename)
                document = self.create_document(file_path, admin_user)
                if document:
                    document_ids.append(document.id)
            else:
                self.stdout.write(self.style.WARNING(f'Skipped invalid file format: {filename}'))

        # Waiting for all files to obtain their file_ids or timeout
        self.wait_for_file_ids(document_ids)

        # Process each document with AI after file_id is obtained
        for document_id in document_ids:
            document = Document.objects.get(id=document_id)
            if document.file_id:
                self.process_with_ai(document)
            else:
                self.stdout.write(self.style.ERROR(f'Document {document_id} did not receive a file_id'))

    def wait_for_file_ids(self, document_ids, timeout=300):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if all(Document.objects.filter(id__in=document_ids, file_id__isnull=False).count() == len(document_ids)):
                return
            time.sleep(10)  # Check every 10 seconds
        self.stdout.write(self.style.ERROR('Timeout reached while waiting for file_ids'))

    def process_with_ai(self, document):

        # AI implementation comes here
        # Example placeholder:
        self.stdout.write(self.style.SUCCESS(f'Processing document {document.id} with AI'))
        # Add actual AI processing logic here

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
