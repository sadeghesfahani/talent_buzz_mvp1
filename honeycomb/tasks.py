from celery import shared_task
from django.conf import settings
from openai import OpenAI

from honeycomb.selectors import get_hive_related_documents
client = OpenAI(api_key=settings.OPEN_AI_API_KEY)

@shared_task
def sync_hive_vector_store(vector_store_id, hive_id):
    # Get the vector store, check the file_ids, add new files if any
    related_documents = get_hive_related_documents(hive_id)
    vector_store = client.beta.vector_stores.retrieve(vector_store_id)

    supported_extensions = ['pdf', 'txt', 'docx']  # Add all supported extensions here

    file_ids = []
    for document in related_documents:
        file_extension = document.document.file.name.split('.')[-1].lower()
        print("file extension", file_extension)
        if file_extension not in supported_extensions:
            print(document.document.file_id)

            print(
                f"Unsupported file extension: {file_extension} for document {document.document.file.name} - {document.file_id}")

            continue
        # print(client.beta.vector_stores.files.retrieve(file_id=document.file_id, vector_store_id=self.vector_store_id))
        file_ids.append(document.file_id)
        try:
            print(client.beta.vector_stores.files.retrieve(file_id=document.file_id,
                                                           vector_store_id=vector_store_id))
        except Exception as e:
            print(f"Failed to retrieve file {document.file_id} from vector store {vector_store_id}: {e}")

    # Distinct file_ids
    file_ids = list(set(file_ids))
    if file_ids:
        try:
            for file_id in file_ids:
                file = client.beta.vector_stores.files.create_and_poll(vector_store_id=vector_store_id,
                                                                       file_id=file_id)
                while (file.status == 'in_progress'):
                    print(f"File {file_id} status: {file.status}")
                print(file.__dict__)
            # print(client.beta.vector_stores.file_batches.create(vector_store_id=self.vector_store_id, file_ids=file_ids))
        except Exception as e:
            print(f"Failed to add files to vector store: {e}")
            print(f"Vector Store ID: {vector_store_id}")
            print(f"File IDs: {file_ids}")