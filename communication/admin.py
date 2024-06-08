from django.contrib import admin
from .models import Conversation, Message, Notification

admin.site.register(Conversation)
admin.site.register(Message)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'notification_type', 'timestamp', 'read']
    list_filter = ['notification_type', 'timestamp', 'read']
    search_fields = ['user__username', 'message']
    list_editable = ['read']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    list_per_page = 20

