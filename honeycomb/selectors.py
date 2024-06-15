from common.models import Document

from task.models import Task


def get_hive_related_documents(hive_id: int):
    from honeycomb.models import Hive
    hive = Hive.objects.get(id=hive_id)
    hive_direct_documents = hive.documents.all()

    # Collect all related tasks through nectars and contracts
    tasks = Task.objects.filter(contract__nectar__nectar_hive=hive)

    # Collect all documents related to these tasks
    task_related_documents = Document.objects.filter(tasks__in=tasks)

    # Combine the two QuerySets
    combined_documents = hive_direct_documents | task_related_documents

    # Remove duplicates, if any
    combined_documents = combined_documents.distinct()

    return combined_documents
