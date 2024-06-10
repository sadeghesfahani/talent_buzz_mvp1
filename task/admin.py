from django.contrib import admin
from .models import Task, TaskAssignment, BeeSelection
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'contract', 'is_completed', 'due_date')
    search_fields = ('title', 'description', 'contract__nectar__nectar_title')
    list_filter = ('is_completed', 'due_date', 'created_at', 'updated_at')


@admin.register(TaskAssignment)
class TaskAssignmentAdmin(admin.ModelAdmin):
    list_display = ('task', 'bee', 'assigned_at', 'is_accepted', 'is_active')
    search_fields = ('task__title', 'bee__user__email')
    list_filter = ('is_accepted', 'is_active', 'assigned_at')


@admin.register(BeeSelection)
class BeeSelectionAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'updated_at')
    search_fields = ('created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')