from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Feedback(models.Model):
    RATINGS = [
        (1, 'Very Poor'),
        (2, 'Poor'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Excellent'),
    ]

    contract = models.ForeignKey('honeycomb.Contract', on_delete=models.CASCADE, related_name='feedbacks')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='given_feedbacks')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_feedbacks')
    communication = models.PositiveIntegerField(choices=RATINGS,
                                                validators=[MinValueValidator(1), MaxValueValidator(5)])
    quality_of_work = models.PositiveIntegerField(choices=RATINGS,
                                                  validators=[MinValueValidator(1), MaxValueValidator(5)])
    punctuality = models.PositiveIntegerField(choices=RATINGS, validators=[MinValueValidator(1), MaxValueValidator(5)])
    overall_satisfaction = models.PositiveIntegerField(choices=RATINGS,
                                                       validators=[MinValueValidator(1), MaxValueValidator(5)])
    experience = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Feedback by {self.author} for {self.contract}"

    class Meta:
        unique_together = ('contract', 'author', 'recipient')
