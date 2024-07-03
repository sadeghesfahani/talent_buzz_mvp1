import django_filters
from .models import Feedback

class FeedbackFilter(django_filters.FilterSet):

    class Meta:
        model = Feedback
        fields = {
            'recipient': ['exact'],
            'contract': ['exact']
        }