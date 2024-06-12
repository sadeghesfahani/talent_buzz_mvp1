from django.urls import path
from .views import TestHiveAssistantView

urlpatterns = [
    path('test-hive-assistant/', TestHiveAssistantView.as_view(), name='test_hive_assistant'),
    # other paths...
]
