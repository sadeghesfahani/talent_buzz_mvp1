from django.contrib.auth import get_user_model

from assistant.tools import Assistant
from user.services import UserService
from .functions import update_user_basic_data, update_user_skills, create_user_education, create_certificate, \
    create_experience, create_portfolio

User = get_user_model()


class AIUserService:
    user_service = UserService

    @staticmethod
    def generate_user_data_based_on_cv(user: User):
        document_queryset = user.user_documents.filter(is_ai_sync=True, purpose="cv")
        if document_queryset:
            assistant_object = Assistant(user=user, document_query=document_queryset,
                                         instruction="you need to read the cv file and generate user data",
                                         functions=[
                                             update_user_basic_data,
                                             update_user_skills,
                                             create_user_education,
                                             create_certificate,
                                             create_experience,
                                             create_portfolio
                                         ])

            try:
                assistant_object.send_message("start")
            except ValueError as e:
                print(e)
