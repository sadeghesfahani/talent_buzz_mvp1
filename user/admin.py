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

from .models import PersonalDetails, CompanyDetails, FreelancerDetails, User, Address


class AddressInline(admin.StackedInline):
    model = Address
    can_delete = True
    extra = 1
    verbose_name_plural = 'Addresses'


class PersonalDetailsInline(admin.StackedInline):
    model = PersonalDetails
    can_delete = False
    verbose_name_plural = 'Personal Details'


class CompanyDetailsInline(admin.StackedInline):
    model = CompanyDetails
    can_delete = False
    verbose_name_plural = 'Company Details'


class FreelancerDetailsInline(admin.StackedInline):
    model = FreelancerDetails
    can_delete = False
    verbose_name_plural = 'Freelancer Details'


class UserAdmin(BaseUserAdmin):
    inlines = (PersonalDetailsInline, CompanyDetailsInline, FreelancerDetailsInline, AddressInline)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('phone_number', 'avatar')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ('date_joined',)
    list_display = ('email', 'is_staff', 'is_active', 'is_superuser', 'date_joined', 'last_login')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'date_joined')
    search_fields = ('email', 'phone_number', 'personal_details__passport_number', 'company_details__company_name',
                     'freelancer_details__skills__name')
    ordering = ('email',)
    date_hierarchy = 'date_joined'
    list_select_related = ('personal_details', 'company_details', 'freelancer_details')


admin.site.register(User, UserAdmin)
