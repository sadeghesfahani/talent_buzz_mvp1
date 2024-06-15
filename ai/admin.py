from django.contrib import admin

# Register your models here.
from .models import AssistantInfo, Thread, Message

admin.site.register(AssistantInfo)
admin.site.register(Thread)
admin.site.register(Message)

