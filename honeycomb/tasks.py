import asyncio

from celery import shared_task
from django.conf import settings
from openai import OpenAI

from honeycomb.selectors import get_hive_related_documents

client = OpenAI(api_key=settings.OPEN_AI_API_KEY)


@shared_task
def sync_hive_vector_store(vector_store_id, hive_id):
    # Get the vector store, check the file_ids, add new files if any
    related_documents = get_hive_related_documents(hive_id)

    supported_extensions = ['pdf', 'txt', 'docx']  # Add all supported extensions here

    file_ids = []
    for document in related_documents:
        file_extension = document.document.file.name.split('.')[-1].lower()
        if file_extension not in supported_extensions:
            print(
                f"Unsupported file extension: {file_extension} for document {document.document.file.name} - {document.file_id}")

            continue

        file_ids.append(document.file_id)

    # Distinct file_ids
    file_ids = list(set(file_ids))
    # here I want to check if the file_ids are already in the vector store
    # if not, I want to add them to the vector store

    # Retrieve existing file IDs from the vector store
    try:
        existing_files = client.beta.vector_stores.files.list(vector_store_id=vector_store_id)
        existing_file_ids = {file.id for file in existing_files.data}
    except Exception as e:
        print(f"Failed to retrieve existing files from vector store: {e}")
        return

    # Filter out the file IDs that are already in the vector store
    new_file_ids = [file_id for file_id in file_ids if file_id not in existing_file_ids]

    if new_file_ids:
        asyncio.run(add_files_async(vector_store_id, new_file_ids))


async def add_files_async(vector_store_id, file_ids):
    tasks = []
    for file_id in file_ids:
        task = asyncio.create_task(create_file(vector_store_id, file_id))
        tasks.append(task)

    await asyncio.gather(*tasks)


async def create_file(vector_store_id, file_id):
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, client.beta.vector_stores.files.create_and_poll, vector_store_id, file_id)
        print(f"Successfully added file {file_id} to vector store")
    except Exception as e:
        print(f"Failed to add file {file_id} to vector store: {e}")
