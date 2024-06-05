from django.core.exceptions import ValidationError

from .models import HiveRequest, Contract


class HiveService:
    @staticmethod
    def submit_membership_application(hive, bee):
        if HiveRequest.objects.filter(hive=hive, bee=bee, is_accepted=False).exists():
            raise ValidationError("A pending application already exists.")
        application = HiveRequest.objects.create(hive=hive, bee=bee)
        return application

    @staticmethod
    def accept_membership_application(application,user):
        application.accept_application(user)


class NectarService:
    @staticmethod
    def submit_nectar_application(nectar, applicant):
        if Contract.objects.filter(nectar=nectar, applicant=applicant, is_accepted=False).exists():
            raise ValidationError("A pending application already exists.")
        application = Contract.objects.create(nectar=nectar, applicant=applicant)
        return application

    @staticmethod
    def accept_nectar_application(application, user):
        application.accept_application(user)
