import uuid
from typing import Union

import openai
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum, QuerySet
from django.utils import timezone
from openai import OpenAI
from simple_history.models import HistoricalRecords
from taggit.managers import TaggableManager

from communication.models import Conversation
from honeycomb.selectors import get_hive_related_documents
from honeycomb.tasks import sync_hive_vector_store

client = OpenAI(api_key=settings.OPEN_AI_API_KEY)
HIVE_TYPE_CHOICES = [
    ('queen', 'With Queen (Paid)'),
    ('no_queen', 'No Queen (Collective Collaboration)'),
]

BEE_TYPE_CHOICES = [
    ('worker', 'Worker'),
    ('scout', 'Scout'),
    ('guardian', 'Guardian'),
    ('queen', 'Queen'),
]

NECTAR_IS_FULL_ERROR = "This nectar already has the required number of freelancers."
COMMON_DOCUMENT_MODEL = 'common.Document'


class Hive(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    hive_type = models.CharField(max_length=10, choices=HIVE_TYPE_CHOICES)
    admins = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='admin_hives', blank=True)
    hive_requirements = models.TextField()
    hive_bees = models.ManyToManyField('Bee', through='Membership')
    is_public = models.BooleanField(default=False)
    documents = models.ManyToManyField(COMMON_DOCUMENT_MODEL, related_name='hive_documents', blank=True)
    status = models.CharField(max_length=255, blank=True, default="open")
    vector_store_id = models.CharField(max_length=255, blank=True)
    tags = TaggableManager()
    change_history = HistoricalRecords()

    def submit_membership_application(self, bee: 'Bee') -> Union['Membership', 'HiveRequest']:

        if HiveRequest.objects.filter(hive=self, bee=bee, is_accepted=False).exists():
            raise ValidationError("A pending application already exists.")
        if HiveRequest.objects.filter(hive=self, bee=bee).exists():
            raise ValidationError("You already are a member")

        application = HiveRequest.objects.create(hive=self, bee=bee)
        if self.is_public:
            return self.accept_application(bee)
        return application

    def accept_application(self, bee: 'Bee') -> 'Membership':
        current_membership = Membership.objects.filter(hive=self, bee=bee).first()
        if current_membership:
            current_membership.is_accepted = True
            current_membership.save()
            return current_membership

        return Membership.objects.create(is_accepted=True, hive=self, bee=bee)

    def get_bees_ordered_by_honey_points(self) -> QuerySet['Bee']:
        return Bee.objects.filter(
            membership__hive=self
        ).annotate(
            total_honey_points=Sum('membership__honey_points')
        ).order_by('-total_honey_points')

    def is_admin_by_user(self, user: settings.AUTH_USER_MODEL) -> bool:
        return user in self.admins.all()

    def is_admin_by_user_id(self, user_id: int) -> bool:
        return self.admins.filter(id=user_id).exists()

    def is_admin_by_bee(self, bee: 'Bee') -> bool:
        return bee.user in self.admins.all()

    def is_admin_by_bee_id(self, bee_id: int) -> bool:
        bee = Bee.objects.get(id=bee_id)
        return self.admins.filter(id=bee.user.id).exists()

    def get_hive_bees(self) -> QuerySet['Bee']:
        return Bee.objects.filter(membership__hive=self, membership__is_accepted=True)


    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def convert_to_ai_readable(self):
        return f"""
        Name: {self.name}
        Description: {self.description}
        Hive type: {self.hive_type}
        Hive requirements: {self.hive_requirements}
        hive documents: {[document.convert_to_ai_readable() for document in self.documents.all()]}
        """


class Bee(models.Model):
    DEFAULT_BEE_TYPE = 'worker'
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='bee',
                                on_delete=models.CASCADE)  # User associated with this bee
    bee_bio = models.TextField(blank=True, null=True)
    bee_type = models.CharField(max_length=10, choices=BEE_TYPE_CHOICES, default=DEFAULT_BEE_TYPE)
    documents = models.ManyToManyField(COMMON_DOCUMENT_MODEL, related_name='bee_documents', blank=True)
    change_history = HistoricalRecords()

    def submit_hive_application(self, hive: 'Hive') -> Union['Membership', 'HiveRequest']:
        return hive.submit_membership_application(self)

    def __str__(self):
        return self.user.email

    def convert_to_ai_readable(self):
        return f"""user information : {self.user.convert_to_ai_readable()}
         bee id: {self.id}
         """






class Membership(models.Model):
    hive = models.ForeignKey(Hive, on_delete=models.CASCADE)
    bee = models.ForeignKey(Bee, on_delete=models.CASCADE)
    is_accepted = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    honey_points = models.IntegerField(default=0)  # Track contributions (HoneyPoints)
    change_history = HistoricalRecords()

    class Meta:
        unique_together = ('hive', 'bee')

    def save(self, *args, **kwargs):
        # Check if leaving the hive
        if self.pk is not None and self.left_at is None and not self.is_accepted:
            self.left_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.bee} in {self.hive}"


class Nectar(models.Model):
    nectar_title = models.CharField(max_length=255)
    nectar_description = models.TextField()
    nectar_hive = models.ForeignKey(Hive, on_delete=models.CASCADE, related_name='nectars', blank=True, null=True)
    is_public = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # Price for the gig
    duration = models.DurationField(blank=True, null=True)  # Expected duration to complete the gig
    required_skills = models.TextField(blank=True)  # Skills required for the gig
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when the gig was created
    updated_at = models.DateTimeField(auto_now=True)  # Timestamp when the gig was last updated
    deadline = models.DateTimeField(null=True, blank=True)  # Deadline for the gig
    required_bees = models.PositiveIntegerField(blank=True, null=True, default=1)  # Number of freelancers required
    status = models.CharField(max_length=255, blank=True, default="open")  # Status of the gig
    documents = models.ManyToManyField(COMMON_DOCUMENT_MODEL, related_name='nectar_documents', blank=True)
    tags = TaggableManager()
    change_history = HistoricalRecords()

    def submit_contract(self, bee: 'Bee') -> 'Contract':
        if self.is_full():
            raise ValidationError(NECTAR_IS_FULL_ERROR)
        if Contract.objects.filter(nectar=self, bee=bee, is_accepted=False).exists():
            raise ValidationError("A pending application already exists.")
        if Contract.objects.filter(nectar=self, bee=bee, is_accepted=True).exists():
            raise ValidationError("You are already working on this gig.")
        return Contract.objects.create(nectar=self, bee=bee, is_accepted=False)

    def accept_application(self, contract: 'Contract', user: settings.AUTH_USER_MODEL) -> 'Contract':
        if self.is_full():
            raise ValidationError(NECTAR_IS_FULL_ERROR)
        if contract.nectar != self:
            raise ValidationError("This contract does not belong to this nectar.")
        contract.accept_application(user)
        return contract

    def is_full(self) -> bool:
        return Contract.objects.filter(is_accepted=True, completed_at__isnull=True).count() >= self.required_bees

    def get_hive_admins(self) -> QuerySet[settings.AUTH_USER_MODEL]:
        return self.nectar_hive.admins.all()

    def get_active_contracts(self) -> QuerySet['Contract']:
        return Contract.objects.filter(nectar=self, is_accepted=True, completed_at__isnull=True)

    def get_completed_contracts(self) -> QuerySet['Contract']:
        return Contract.objects.filter(nectar=self, is_accepted=True, completed_at__isnull=False)

    def get_pending_applications(self) -> QuerySet['Contract']:
        return Contract.objects.filter(nectar=self, is_accepted=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        Conversation.objects.get_or_create(nectar=self, tag="general")

    def __str__(self):
        return self.nectar_title

    def convert_to_ai_readable(self):
        return f"""
        Title: {self.nectar_title}
        Description: {self.nectar_description}
        required skills for this nectar: {self.required_skills}
        Price: {self.price}
        Duration: {self.duration}
        Deadline: {self.deadline}
        documents: {[document.convert_to_ai_readable() for document in self.documents.all()]}
        tags: {self.tags.all()}
        """


class HiveRequest(models.Model):
    hive = models.ForeignKey('Hive', on_delete=models.CASCADE, related_name='applications')
    bee = models.ForeignKey('Bee', on_delete=models.CASCADE, related_name='applications')
    is_accepted = models.BooleanField(default=False)
    applied_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    motivation = models.TextField(blank=True)
    documents = models.ManyToManyField(COMMON_DOCUMENT_MODEL, related_name='hive_request_documents', blank=True)
    change_history = HistoricalRecords()


    def accept_application(self, user: settings.AUTH_USER_MODEL) -> 'Membership':
        self._validate_application()
        self._check_permissions(user)
        self._deactivate_existing_membership()
        return self._accept_application()

    def _validate_application(self) -> None:
        if self.is_accepted:
            raise ValidationError("Application is already accepted.")

    def _check_permissions(self, user) -> None:
        if self.hive.is_public:
            return None  # No need to check permissions for public hives
        if user not in self.hive.admins.all():
            raise ValidationError("Only hive admins can accept membership applications.")

    def _deactivate_existing_membership(self) -> None:
        existing_membership = Membership.objects.filter(
            hive=self.hive,
            bee=self.bee,
            is_accepted=True,
            left_at=None
        ).first()
        if existing_membership:
            existing_membership.is_accepted = False
            existing_membership.left_at = timezone.now()
            existing_membership.save()

    def _accept_application(self) -> 'Membership':
        self.is_accepted = True
        self.accepted_at = timezone.now()
        self.save()
        return self._create_active_membership()

    def _create_active_membership(self) -> 'Membership':
        membership = Membership.objects.get_or_create(
            hive=self.hive,
            bee=self.bee,
        )[0]
        membership.is_accepted = True
        membership.save()
        return membership

    def __str__(self):
        return f"Application of {self.bee} to {self.hive}"

    def convert_to_ai_readable(self):
        return f"""
        Application for {self.hive.convert_to_ai_readable()} by {self.bee.convert_to_ai_readable()}.
        motivation : {self.motivation}
        documents: {[document.convert_to_ai_readable() for document in self.documents.all()]}
        """

class Contract(models.Model):
    contract_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    nectar = models.ForeignKey('Nectar', on_delete=models.CASCADE, related_name='applications')
    bee = models.ForeignKey(Bee, on_delete=models.CASCADE)
    accepted_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_accepted = models.BooleanField(default=False)
    applied_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)  # When the contract work started
    completed_at = models.DateTimeField(null=True, blank=True)  # When the contract work was completed
    documents = models.ManyToManyField(COMMON_DOCUMENT_MODEL, related_name='contract_documents', blank=True)
    change_history = HistoricalRecords()

    def save(self, *args, **kwargs):
        # Prevent changes to accepted_rate if the contract is already accepted
        if self.pk is not None:  # Check if the object is being updated
            original = Contract.objects.get(pk=self.pk)
            if original.is_accepted and original.accepted_rate != self.accepted_rate:
                raise ValidationError("Cannot change the accepted rate of an accepted contract.")
        super().save(*args, **kwargs)

    def accept_application(self, user: Bee) -> None:
        is_admin = self.nectar.nectar_hive.admins.filter(id=user.id).exists()
        if not is_admin:
            raise ValidationError("Only hive admins can accept nectar applications.")
        if self.nectar.is_full():
            raise ValidationError("This nectar already has the required number of freelancers.")

        self.is_accepted = True
        self.accepted_at = timezone.now()
        self.save()

    def __str__(self):
        return f"Application for {self.nectar} by {self.bee}"

    def convert_to_ai_readable(self):
        return f"""
        Contract for {self.nectar.convert_to_ai_readable()} by {self.bee.convert_to_ai_readable()}.
        accepted rate : {self.accepted_rate}
        documents: {[document.convert_to_ai_readable() for document in self.documents.all()]}
        is accepted : {self.is_accepted}
        """

class ReportManager(models.Manager):
    def for_hive(self, hive: 'Hive') -> QuerySet['Report']:
        return self.filter(hive=hive)

    def for_nectar(self, nectar: 'Nectar') -> QuerySet['Report']:
        return self.filter(nectar=nectar)

    def for_bee(self, bee: 'Bee') -> QuerySet['Report']:
        return self.filter(bee=bee)


class Report(models.Model):
    hive = models.ForeignKey(Hive, on_delete=models.CASCADE, related_name='hive_reports', blank=True, null=True)
    nectar = models.ForeignKey(Nectar, on_delete=models.CASCADE, related_name='nectar_reports', blank=True, null=True)
    task = models.ForeignKey('task.Task', on_delete=models.CASCADE, related_name='task_reports', blank=True, null=True)
    bee = models.ForeignKey(Bee, on_delete=models.CASCADE, related_name='bee_reports')
    title = models.CharField(max_length=255)
    content = models.TextField()
    documents = models.ManyToManyField(COMMON_DOCUMENT_MODEL, related_name='report_documents', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=255, blank=True)

    objects = ReportManager()

    def convert_to_ai_readable(self):
        return f"""
        Report for {self.hive.convert_to_ai_readable()} by {self.bee.convert_to_ai_readable()}.
        title : {self.title}
        content : {self.content}
        documents: {[document.convert_to_ai_readable() for document in self.documents.all()]}
        status : {self.status}
        """


