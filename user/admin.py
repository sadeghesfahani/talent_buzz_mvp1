# from django.contrib import admin
#
# # Register your models here.
#
# from .models import User, PersonalDetails, CompanyDetails, FreelancerDetails, Skill, Measures
#
# admin.site.register(User)
# admin.site.register(PersonalDetails)
# admin.site.register(CompanyDetails)
# admin.site.register(FreelancerDetails)
# admin.site.register(Skill)
# admin.site.register(Measures)

# admin_inlines.py (or include in the same file as admin.py)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Avg
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from feedback.models import Feedback
from .models import User, Address, Certificate, Education,Portfolio,Experience


class AddressInline(admin.StackedInline):
    model = Address
    can_delete = True
    extra = 1
    verbose_name_plural = 'Addresses'


class FeedbackInline(admin.TabularInline):
    model = Feedback
    extra = 0
    fk_name = 'recipient'
    readonly_fields = (
        'feedback_link', 'communication', 'quality_of_work', 'punctuality', 'overall_satisfaction', 'experience',
        'created_at'
    )
    fields = ('feedback_link', 'communication', 'quality_of_work', 'punctuality', 'overall_satisfaction', 'experience',
              'created_at')

    def feedback_link(self, obj):
        url = reverse('admin:feedback_feedback_change', args=[obj.id])
        return format_html('<a href="{}">Feedback {}</a>', url, obj.id)

    feedback_link.short_description = 'Feedback'


class UserAdmin(BaseUserAdmin):
    inlines = (AddressInline, FeedbackInline)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('phone_number', 'avatar', 'first_name', 'last_name',)}),
        ('Flags', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_freelancer', 'is_company')}),
        ('Freelancer details', {'fields': ('headline','bio','tags','skills','cv_notes')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Rate', {'fields': (
        'average_communication', 'average_quality_of_work', 'average_punctuality', 'average_overall_satisfaction')}),
    )
    readonly_fields = ('date_joined', 'average_communication', 'average_quality_of_work', 'average_punctuality',
                       'average_overall_satisfaction')
    list_display = (
        'email', 'is_staff', 'is_active', 'is_superuser',
        'average_communication', 'average_quality_of_work', 'average_punctuality', 'average_overall_satisfaction'
    )
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'date_joined')
    search_fields = ('email', 'phone_number', 'passport_number')
    ordering = ('email',)
    date_hierarchy = 'date_joined'
    # list_select_related = ('company_details', 'freelancer_details')
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )

    def average_communication(self, obj):
        return Feedback.objects.filter(recipient=obj).aggregate(Avg('communication'))['communication__avg']

    average_communication.short_description = 'Avg Communication'

    def average_quality_of_work(self, obj):
        return Feedback.objects.filter(recipient=obj).aggregate(Avg('quality_of_work'))['quality_of_work__avg']

    average_quality_of_work.short_description = 'Avg Quality of Work'

    def average_punctuality(self, obj):
        return Feedback.objects.filter(recipient=obj).aggregate(Avg('punctuality'))['punctuality__avg']

    average_punctuality.short_description = 'Avg Punctuality'

    def average_overall_satisfaction(self, obj):
        return Feedback.objects.filter(recipient=obj).aggregate(Avg('overall_satisfaction'))[
            'overall_satisfaction__avg']

    average_overall_satisfaction.short_description = 'Avg Overall Satisfaction'

    def feedback_links(self, obj):
        feedbacks = Feedback.objects.filter(recipient=obj)
        links = []
        for feedback in feedbacks:
            url = reverse('admin:feedback_feedback_change', args=[feedback.id])
            links.append(format_html('<a href="{}">{}</a>', url, feedback.id))
        return mark_safe(', '.join(links))


admin.site.register(User, UserAdmin)
admin.site.register(Certificate)
admin.site.register(Education)
admin.site.register(Portfolio)
admin.site.register(Experience)
