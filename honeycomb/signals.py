# myapp/signals.py
from django.conf import settings
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from openai import OpenAI

from ai.helpers import AIBaseClass
from ai.models import AssistantInfo
from communication.models import Notification, Conversation
from honeycomb.tasks import sync_hive_vector_store
from .models import Hive, Membership, Nectar, HiveRequest, Contract, Report, Bee

client = OpenAI(api_key=settings.OPEN_AI_API_KEY)




@receiver(post_save, sender=Membership)
def membership_created(sender, instance, created, **kwargs):
    if created:
        # Notify user of the membership
        Notification.objects.create(
            user=instance.bee.user,
            message=f"You have been added to the hive '{instance.hive.name}'.",
            notification_type='info'
        )


@receiver(post_save, sender=Nectar)
def nectar_created(sender, instance, created, **kwargs):
    if created:
        # Notify hive admins of the new nectar
        for admin in instance.nectar_hive.admins.all():
            Notification.objects.create(
                user=admin,
                message=f"A new nectar '{instance.nectar_title}' has been created in hive '{instance.nectar_hive.name}'.",
                notification_type='info'
            )
        for bee in instance.nectar_hive.get_hive_bees():
            Notification.objects.create(
                user=bee.user,
                message=f"Nectar '{instance.nectar_title}' in hive '{instance.nectar_hive.name} posted'.",
                notification_type='info'
            )


@receiver(post_save, sender=HiveRequest)
def hive_request_created(sender, instance, created, **kwargs):
    if created:
        # Notify hive admins of the new hive request
        for admin in instance.hive.admins.all():
            Notification.objects.create(
                user=admin,
                message=f"A new membership request for hive '{instance.hive.name}' has been submitted by '{instance.bee.user.email}'.",
                notification_type='info'
            )


@receiver(post_save, sender=Membership)
def membership_status_changed(sender, instance, created, **kwargs):
    if created and instance.is_accepted:
        Notification.objects.create(
            user=instance.bee.user,
            message=f"Your membership to the hive '{instance.hive.name}' has been accepted.",
            notification_type='info'
        )
    elif not created:
        if instance.is_accepted:
            Notification.objects.create(
                user=instance.bee.user,
                message=f"Your membership to the hive '{instance.hive.name}' has been accepted.",
                notification_type='info'
            )
        else:
            Notification.objects.create(
                user=instance.bee.user,
                message=f"You have left the hive '{instance.hive.name}'.",
                notification_type='warning'
            )


@receiver(post_save, sender=Contract)
def contract_created(sender, instance, created, **kwargs):
    if created:
        # Notify nectar hive admins of the new contract
        for admin in instance.nectar.nectar_hive.admins.all():
            Notification.objects.create(
                user=admin,
                message=f"A new contract for nectar '{instance.nectar.nectar_title}' has been submitted by '{instance.bee.user.email}'.",
                notification_type='info'
            )


@receiver(post_save, sender=Report)
def report_created(sender, instance, created, **kwargs):
    if created:
        # Notify hive admins of the new report
        for admin in instance.hive.admins.all():
            Notification.objects.create(
                user=admin,
                message=f"A new report '{instance.title}' has been created in hive '{instance.hive.name}'.",
                notification_type='info'
            )


@receiver(post_delete, sender=Membership)
def membership_deleted(sender, instance, **kwargs):
    # Notify user of the membership removal
    Notification.objects.create(
        user=instance.bee.user,
        message=f"You have been removed from the hive '{instance.hive.name}'.",
        notification_type='warning'
    )


@receiver(post_delete, sender=Nectar)
def nectar_deleted(sender, instance, **kwargs):
    # Notify hive admins of the nectar deletion
    for admin in instance.nectar_hive.admins.all():
        Notification.objects.create(
            user=admin,
            message=f"The nectar '{instance.nectar_title}' has been deleted from hive '{instance.nectar_hive.name}'.",
            notification_type='warning'
        )


@receiver(post_delete, sender=Contract)
def contract_deleted(sender, instance, **kwargs):
    # Notify nectar hive admins of the contract deletion
    for admin in instance.nectar.nectar_hive.admins.all():
        Notification.objects.create(
            user=admin,
            message=f"The contract for nectar '{instance.nectar.nectar_title}' by '{instance.bee.user.email}' has been deleted.",
            notification_type='warning'
        )


@receiver(post_save, sender=Hive)
def sync_vector_store(sender, instance, created, **kwargs):
    if settings.IS_TEST:
        return  # Skip signal handling during tests
    if created:
        # Create vector store if it does not exist
        vector_store = client.beta.vector_stores.create(name=f"{instance.name} Vector Store")
        instance.vector_store_id = vector_store.id
        instance.save()
    else:
        # Sync vector store if it already exists
        sync_hive_vector_store.delay(vector_store_id=instance.vector_store_id, hive_id=instance.id)


@receiver(m2m_changed, sender=Bee.documents.through)
def sync_bee_files(sender, instance, action, reverse, model, pk_set, **kwargs):
    if settings.IS_TEST:
        return

    if action == "post_add" or action == "post_remove":
        base_vector_store = AssistantInfo.objects.first().base_vector_store_id
        AIBaseClass().add_documents_to_vector_store(base_vector_store, instance.documents.all())
