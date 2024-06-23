from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models import Avg

from feedback.models import Feedback
from library.constants import REGULAR_CHAR_LENGTH, URL_LENGTH, DECIMAL_MAX_DIGITS, DECIMAL_DECIMAL_PLACES, PHONE_LENGTH, \
    LONG_TEXT_LENGTH
from library.validators import PHONE_REGEX


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=50, choices=[
        ('home', 'Home'),
        ('work', 'Work'),
        ('other', 'Other'),
    ])
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.address_type} address for {self.user.email}"


class CustomUserManager(BaseUserManager):
    def _create_user(self, email, password=None, is_staff=False, is_superuser=False, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, is_staff=is_staff, is_superuser=is_superuser, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        return self._create_user(email, password, is_staff=True, is_superuser=True, **extra_fields)


class PersonalDetails(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='personal_details')
    first_name = models.CharField(max_length=REGULAR_CHAR_LENGTH, blank=True)
    last_name = models.CharField(max_length=REGULAR_CHAR_LENGTH, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    passport_number = models.CharField(max_length=REGULAR_CHAR_LENGTH, blank=True)
    measures = models.ManyToManyField('Measures', related_name='user_measures', blank=True)

    def __str__(self):
        return f"PersonalDetails for {self.id}"

    def convert_to_ai_readable(self):
        return f"""
        user first name is : {self.first_name}, user last name is : {self.last_name}, user date of birth is : {self.date_of_birth}
        user measures are : {[measure.convert_to_ai_readable() for measure in self.measures.all()]}
        """


class CompanyDetails(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='company_details')
    company_name = models.CharField(max_length=REGULAR_CHAR_LENGTH, blank=True)
    kvk_number = models.CharField(max_length=REGULAR_CHAR_LENGTH, blank=True)
    vat_id = models.CharField(max_length=REGULAR_CHAR_LENGTH, blank=True)
    bank_account = models.CharField(max_length=REGULAR_CHAR_LENGTH, blank=True)
    company_logo = models.ImageField(upload_to='company_logo', blank=True)
    company_description = models.TextField(blank=True)
    company_website = models.URLField(max_length=URL_LENGTH, blank=True)
    company_size = models.CharField(max_length=REGULAR_CHAR_LENGTH, blank=True)
    company_industry = models.CharField(max_length=REGULAR_CHAR_LENGTH, blank=True)
    company_type = models.CharField(max_length=REGULAR_CHAR_LENGTH, blank=True)
    company_founded = models.DateField(blank=True, null=True)
    company_location = models.CharField(max_length=REGULAR_CHAR_LENGTH, blank=True)
    company_specialities = models.JSONField(blank=True, default=list)
    company_social_media = models.JSONField(blank=True, default=dict)

    def __str__(self):
        return f"CompanyDetails for {self.company_name}"


class FreelancerDetails(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='freelancer_details')
    hourly_rate = models.DecimalField(max_digits=DECIMAL_MAX_DIGITS, decimal_places=DECIMAL_DECIMAL_PLACES, blank=True)
    skills = models.ManyToManyField('Skill', related_name='user_skills', blank=True)
    experience = models.JSONField(blank=True, default=list)
    education = models.JSONField(blank=True, default=list)
    certification = models.JSONField(blank=True, default=list)
    portfolio = models.JSONField(blank=True, default=list)

    def __str__(self):
        return f"FreelancerDetails for {self.id}"


class User(AbstractBaseUser, PermissionsMixin):
    # Account information
    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=REGULAR_CHAR_LENGTH, blank=True, null=True)
    phone_number = models.CharField(
        validators=[PHONE_REGEX], max_length=PHONE_LENGTH,
        blank=True, null=True, unique=True, db_index=True
    )
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    # User flags
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    # Dates
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        ordering = ['-date_joined']

    def get_feedback_aggregates(self):
        feedbacks = Feedback.objects.filter(author=self)
        aggregate_data = feedbacks.aggregate(
            avg_communication=Avg('communication'),
            avg_quality_of_work=Avg('quality_of_work'),
            avg_punctuality=Avg('punctuality'),
            avg_overall_satisfaction=Avg('overall_satisfaction'),
        )
        return aggregate_data

    def __str__(self):
        return self.email


class Skill(models.Model):
    name = models.CharField(max_length=REGULAR_CHAR_LENGTH)
    type = models.CharField(max_length=REGULAR_CHAR_LENGTH, blank=True)
    equivalents = models.CharField(max_length=LONG_TEXT_LENGTH, blank=True)
    parent = models.ForeignKey('Skill', on_delete=models.CASCADE, related_name='sub_skills', blank=True, null=True)

    def __str__(self):
        return self.name


class Measures(models.Model):
    name = models.CharField(max_length=REGULAR_CHAR_LENGTH)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=REGULAR_CHAR_LENGTH)
    value = models.CharField(blank=True, max_length=REGULAR_CHAR_LENGTH)

    def __str__(self):
        return self.name

    def convert_to_ai_readable(self):
        return f"""
        measure name is : {self.name}, measure description is : {self.description}, measure unit is : {self.unit}, measure value is : {self.value}
        """
