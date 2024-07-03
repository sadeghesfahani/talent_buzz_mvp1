from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from .models import Feedback
from .serializers import FeedbackSerializer
from .filters import FeedbackFilter


class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = FeedbackFilter
