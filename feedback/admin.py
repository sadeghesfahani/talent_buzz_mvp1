from django.contrib import admin
from .models import Feedback

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('author','recipient', 'contract', 'communication', 'quality_of_work', 'punctuality', 'overall_satisfaction', 'created_at')
    list_filter = ('communication', 'quality_of_work', 'punctuality', 'overall_satisfaction', 'created_at')
    search_fields = ('user__username', 'contract__nectar__nectar_title', 'experience')
    date_hierarchy = 'created_at'
