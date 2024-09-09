
from django.urls import path
from .views import get_user_information_based_on_their_cv, get_user_cv_note


urlpatterns = [
    path('cv-generator/', get_user_information_based_on_their_cv, name='get_user_information_based_on_their_cv'),
    path('cv-note/', get_user_cv_note, name='get_user_cv_note'),

]
