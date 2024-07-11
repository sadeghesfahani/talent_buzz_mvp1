
from django.urls import path
from .views import get_user_information_based_on_their_cv


urlpatterns = [
    path('cv-generator/', get_user_information_based_on_their_cv, name='get_user_information_based_on_their_cv'),

]
