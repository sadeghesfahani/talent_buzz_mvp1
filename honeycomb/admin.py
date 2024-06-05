from django.contrib import admin
from .models import Hive, Bee, Membership, Nectar, HiveRequest, Contract
from simple_history.admin import SimpleHistoryAdmin

@admin.register(Hive)
class HiveAdmin(SimpleHistoryAdmin):
    list_display = ('name', 'hive_type', 'description', 'hive_requirements')
    search_fields = ('name', 'hive_type', 'description')
    list_filter = ('hive_type',)
    filter_horizontal = ('admins',)  # Removed 'hive_bees' from filter_horizontal
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'hive_type', 'hive_requirements', 'admins')
        }),
    )

@admin.register(Bee)
class BeeAdmin(SimpleHistoryAdmin):
    list_display = ('user', 'bee_type', 'bee_bio')
    search_fields = ('user__email', 'bee_type', 'bee_bio')
    list_filter = ('bee_type',)

@admin.register(Membership)
class MembershipAdmin(SimpleHistoryAdmin):
    list_display = ('hive', 'bee', 'is_accepted', 'joined_at', 'left_at', 'honey_points')
    search_fields = ('hive__name', 'bee__user__email')
    list_filter = ('is_accepted', 'joined_at', 'left_at')

@admin.register(Nectar)
class NectarAdmin(SimpleHistoryAdmin):
    list_display = ('nectar_title', 'nectar_hive', 'is_public')
    search_fields = ('nectar_title', 'nectar_hive__name')
    list_filter = ('is_public',)

@admin.register(HiveRequest)
class HiveRequestAdmin(SimpleHistoryAdmin):
    list_display = ('hive', 'bee', 'is_accepted', 'applied_at', 'accepted_at')
    search_fields = ('hive__name', 'bee__user__email')
    list_filter = ('is_accepted', 'applied_at', 'accepted_at')

    def accept_application(self, request, queryset):
        for application in queryset:
            application.accept_application()
    accept_application.short_description = 'Accept selected applications'

    actions = [accept_application]

@admin.register(Contract)
class ContractAdmin(SimpleHistoryAdmin):
    list_display = ('nectar', 'bee', 'is_accepted', 'applied_at', 'accepted_at')
    search_fields = ('nectar__nectar_title', 'applicant__email')
    list_filter = ('is_accepted', 'applied_at', 'accepted_at')

    def accept_application(self, request, queryset):
        for application in queryset:
            application.accept_application()
    accept_application.short_description = 'Accept selected contracts'

    actions = [accept_application]
