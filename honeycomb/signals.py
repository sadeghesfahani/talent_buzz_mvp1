# myapp/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from communication.models import Notification
from .models import Hive, Membership, Nectar, HiveRequest, Contract, Report


@receiver(post_save, sender=Hive)
def hive_created(sender, instance, created, **kwargs):
    if created:
        # Notify admins of the new hive
        for admin in instance.admins.all():
            Notification.objects.create(
                user=admin,
                message=f"Your hive '{instance.name}' has been created.",
                notification_type='info'
            )


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
