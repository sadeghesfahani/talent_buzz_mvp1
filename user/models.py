from datetime import date, datetime
from typing import Optional, List, Tuple, Iterator

from dateutil.rrule import rrulestr
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models import Avg

from feedback.models import Feedback
from library.constants import REGULAR_CHAR_LENGTH, URL_LENGTH, PHONE_LENGTH
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



class Experience(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='experiences')
    position = models.CharField(max_length=50)
    company = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    related_skills = models.ManyToManyField('Skill', related_name='experiences', blank=True)
    documents = models.ManyToManyField('common.Document', related_name='experiences', blank=True)
    description = models.TextField(blank=True)

    def experience_period(self):
        if self.end_date:
            delta = self.end_date - self.start_date
        else:
            delta = date.today() - self.start_date
        return delta.days


class Education(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='educations')
    degree = models.CharField(max_length=50)
    description = models.TextField()
    university = models.CharField(max_length=50)
    documents = models.ManyToManyField('common.Document', related_name='educations', blank=True)


class Certificate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certifications')
    documents = models.ManyToManyField('common.Document', related_name='certifications')
    title = models.CharField(max_length=50)
    institution = models.CharField(max_length=50)
    date_earned = models.DateField()
    description = models.TextField()


class Portfolio(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='portfolio')
    title = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    link = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to='portfolio/', blank=True, null=True)
    documents = models.ManyToManyField('common.Document', related_name='portfolios', blank=True)


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

    # Personal information
    first_name = models.CharField(max_length=REGULAR_CHAR_LENGTH, blank=True)
    last_name = models.CharField(max_length=REGULAR_CHAR_LENGTH, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    passport_number = models.CharField(max_length=REGULAR_CHAR_LENGTH, blank=True)
    language = models.CharField(max_length=REGULAR_CHAR_LENGTH, blank=True)

    # Company details
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

    # settings
    settings = models.JSONField(blank=True, default=dict)

    # psychological and biological information
    personality_type = models.JSONField(blank=True, default=dict)
    iq = models.IntegerField(blank=True, null=True)

    # Gamification
    points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)

    skills = models.ManyToManyField('Skill', related_name='users', blank=True)
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

    def get_rank(self):
        # I want to get the rank of the user based on the points in comparison to other users
        users = User.objects.all().order_by('-points')
        rank = 1
        for user in users:
            if user == self:
                return rank
            rank += 1
        return rank

    def convert_to_ai_readable(self):
        return f"""
        
        """


class Skill(models.Model):
    TECHNICAL = 'Technical'
    SOFT = 'Soft'
    SKILL_TYPE_CHOICES = [
        (TECHNICAL, 'Technical'),
        (SOFT, 'Soft'),
    ]
    name = models.CharField(max_length=50)
    type = models.CharField(max_length=50, choices=SKILL_TYPE_CHOICES, blank=True)
    equivalents = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    parents = models.ManyToManyField('self', related_name='sub_skills', symmetrical=False, blank=True)
    def __str__(self):
        return self.name



class AvailableTimeSlotException(models.Model):
    slot = models.ForeignKey('AvailableTimeSlot', related_name='exceptions', on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    reason = models.CharField(max_length=255, blank=True)  # Optional reason for the exception

    def __str__(self) -> str:
        return f"Exception from {self.start_time} to {self.end_time} for {self.slot}: {self.reason if self.reason else 'No specified reason'}"


class AvailableTimeSlot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='available_time_slots')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    recurrence_rule = models.CharField(max_length=255, blank=True)
    recurrence_end = models.DateField(blank=True, null=True)
    type = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.type} for {self.user.username} from {self.start_time} to {self.end_time}"

    def occurrences(self, end_date: Optional[datetime] = None) -> List[Tuple[datetime, datetime]]:
        """Generate occurrences of the available time slot, considering exceptions."""
        final_occurrences = []
        if self.recurrence_rule:
            # Calculate the end date using the smallest of the provided end_date or the recurrence_end
            effective_end_date = min(self.recurrence_end if self.recurrence_end else end_date,
                                     end_date) if end_date else self.recurrence_end
            rule = rrulestr(self.recurrence_rule, dtstart=self.start_time)
            for start in rule.between(self.start_time, effective_end_date, inc=True):
                period = (start, start + (self.end_time - self.start_time))
                final_occurrences.extend(self.adjust_period_based_on_exceptions(period))
        else:
            # No recurrence rule means a single occurrence
            final_occurrences.append((self.start_time, self.end_time))
        return final_occurrences

    def adjust_period_based_on_exceptions(self, period: Tuple[datetime, datetime]) -> Iterator[
        Tuple[datetime, datetime]]:
        """Yield periods adjusted based on any exceptions."""
        start, end = period
        exceptions = self.exceptions.filter(start_time__lt=end, end_time__gt=start).order_by('start_time')

        last_end = start
        for exception in exceptions:
            if exception.start_time > last_end:
                # Yield the time before the exception starts
                yield (last_end, exception.start_time)
            # Update last_end to skip over the exception
            last_end = max(last_end, exception.end_time)

        if last_end < end:
            # Yield the remaining time after the last exception
            yield (last_end, end)
