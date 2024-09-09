# Create your views here.
from django.http import JsonResponse


def get_user_information_based_on_their_cv(request):
    from .services import AIUserService
    AIUserService.generate_user_data_based_on_cv(user=request.user)
    return JsonResponse({"message": "The process has been started."})


def get_user_cv_note(request):
    from .services import AIUserService
    resume = AIUserService.get_user_cv_note(user=request.user)

    return JsonResponse({"message": resume})
