from django.db.models.signals import m2m_changed, post_save, post_delete
from django.dispatch import receiver
from honeycomb.models import Hive, Membership, Contract


@receiver(m2m_changed, sender=Hive.hive_bees.through)
def sync_conversation_participants(sender, instance, action, reverse, pk_set, **kwargs):
    if action == 'post_add':
        for bee_id in pk_set:
            bee = instance.hive_bees.get(pk=bee_id)
            user = bee.user
            for conversation in instance.conversations.all():
                conversation.participants.add(user)
    elif action == 'post_remove':
        for bee_id in pk_set:
            bee = instance.hive_bees.get(pk=bee_id)
            user = bee.user
            for conversation in instance.conversations.all():
                conversation.participants.remove(user)


@receiver(post_save, sender=Membership)
def add_member_to_conversation(sender, instance, created, **kwargs):
    if created and instance.is_accepted:
        bee = instance.bee
        user = bee.user
        hive = instance.hive
        for conversation in hive.hive_conversations.all():
            (conversation.participants.add(user)

@receiver(post_save, sender=Membership))
def add_member_to_conversation(sender, instance, created, **kwargs):
    if created and instance.is_accepted:
        bee = instance.bee
        user = bee.user
        hive = instance.hive
        for conversation in hive.hive_conversations.all():
            conversation.participants.add(user)


@receiver(post_delete, sender=Membership)
def remove_member_from_conversation(sender, instance, **kwargs):
    bee = instance.bee
    user = bee.user
    hive = instance.hive
    for conversation in hive.hive_conversations.all():
        conversation.participants.remove(user)


@receiver(post_save, sender=Contract)
def add_bee_to_conversation(sender, instance, created, **kwargs):
    if instance.is_accepted:
        conversation = instance.nectar.nectar_conversations.filter(tag='general').first()
        if conversation and instance.bee.user not in conversation.participants.all():
            conversation.participants.add(instance.bee.user)
            conversation.save()