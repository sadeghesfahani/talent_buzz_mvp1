import asyncio

from celery import shared_task
from django.conf import settings
from openai import OpenAI

from ai.helpers import AIBaseClass
from honeycomb.selectors import get_hive_related_documents

client = OpenAI(api_key=settings.OPEN_AI_API_KEY)


@shared_task
def sync_hive_vector_store(vector_store_id, hive_id):
    # Get the vector store, check the file_ids, add new files if any
    related_documents = get_hive_related_documents(hive_id)
    AIBaseClass().add_documents_to_vector_store(vector_store_id, related_documents)

