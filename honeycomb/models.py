import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords

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


class Hive(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    hive_type = models.CharField(max_length=10, choices=HIVE_TYPE_CHOICES)
    admins = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='admin_hives')
    hive_requirements = models.TextField()
    hive_bees = models.ManyToManyField('Bee', through='Membership')
    is_public = models.BooleanField(default=False)
    change_history = HistoricalRecords()

    def submit_membership_application(self, bee):
        if HiveRequest.objects.filter(hive=self, bee=bee, is_accepted=False).exists():
            raise ValidationError("A pending application already exists.")
        application = HiveRequest.objects.create(hive=self, bee=bee)
        return application

    def accept_application(self, bee):
        current_membership = Membership.objects.filter(hive=self, bee=bee).first()
        if current_membership:
            current_membership.first().is_accepted = True
            current_membership.save()
            return current_membership

        return Membership.objects.create(is_accepted=True, membership_hive=self, membership_bee=bee)

    def __str__(self):
        return self.name


class Bee(models.Model):
    DEFAULT_BEE_TYPE = 'worker'
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # User associated with this bee
    bee_bio = models.TextField(blank=True)
    bee_type = models.CharField(max_length=10, choices=BEE_TYPE_CHOICES, default=DEFAULT_BEE_TYPE)
    change_history = HistoricalRecords()

    def submit_hive_application(self, hive):
        return hive.submit_membership_application(self)

    def __str__(self):
        return self.user.email


class Membership(models.Model):
    membership_hive = models.ForeignKey(Hive, on_delete=models.CASCADE)
    membership_bee = models.ForeignKey(Bee, on_delete=models.CASCADE)
    is_accepted = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    honey_points = models.IntegerField(default=0)  # Track contributions (HoneyPoints)
    change_history = HistoricalRecords()

    class Meta:
        unique_together = ('membership_hive', 'membership_bee')

    def save(self, *args, **kwargs):
        # Check if leaving the hive
        if self.pk is not None and self.left_at is None and not self.is_accepted:
            self.left_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.membership_bee} in {self.membership_hive}"


class Nectar(models.Model):
    nectar_title = models.CharField(max_length=255)
    nectar_description = models.TextField()
    nectar_hive = models.ForeignKey(Hive, on_delete=models.CASCADE, related_name='nectars', blank=True, null=True)
    is_public = models.BooleanField(default=True)
    change_history = HistoricalRecords()

    def submit_contract(self, bee):
        return Contract.objects.create(nectar=self, bee=bee, is_accepted=False)

    def get_hive_admins(self):
        return self.nectar_hive.admins.all()

    def __str__(self):
        return self.nectar_title


class HiveRequest(models.Model):
    hive = models.ForeignKey('Hive', on_delete=models.CASCADE, related_name='applications')
    bee = models.ForeignKey('Bee', on_delete=models.CASCADE, related_name='applications')
    is_accepted = models.BooleanField(default=False)
    applied_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    change_history = HistoricalRecords()

    def accept_application(self, user):
        self._validate_application()
        self._check_permissions(user)
        self._deactivate_existing_membership()
        self._accept_application()

    def _validate_application(self):
        if self.is_accepted:
            raise ValidationError("Application is already accepted.")

    def _check_permissions(self, user):
        if user not in self.hive.admins.all():
            raise ValidationError("Only hive admins can accept membership applications.")

    def _deactivate_existing_membership(self):
        existing_membership = Membership.objects.filter(
            membership_hive=self.hive,
            membership_bee=self.bee,
            is_accepted=True,
            left_at=None
        ).first()
        if existing_membership:
            existing_membership.is_accepted = False
            existing_membership.left_at = timezone.now()
            existing_membership.save()

    def _accept_application(self):
        self.is_accepted = True
        self.accepted_at = timezone.now()
        self.save()
        self._create_active_membership()

    def _create_active_membership(self):
        Membership.objects.create(
            membership_hive=self.hive,
            membership_bee=self.bee,
            is_accepted=True
        )

    def __str__(self):
        return f"Application of {self.bee} to {self.hive}"


class Contract(models.Model):
    contract_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    nectar = models.ForeignKey('Nectar', on_delete=models.CASCADE, related_name='applications')
    bee = models.ForeignKey(Bee, on_delete=models.CASCADE)
    is_accepted = models.BooleanField(default=False)
    applied_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    change_history = HistoricalRecords()

    def accept_application(self, user):
        if self.is_accepted:
            raise ValidationError("Application is already accepted.")
        if user not in self.nectar.nectar_hive.admins.all():
            raise ValidationError("Only hive admins can accept nectar applications.")
        self.is_accepted = True
        self.accepted_at = timezone.now()
        self.save()

    def __str__(self):
        return f"Application for {self.nectar} by {self.bee}"
