from django.core.exceptions import ValidationError

from .models import HiveRequest, Contract, Hive


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

    @staticmethod
    def get_hive_admins(hive):
        return hive.admins.all()

    @staticmethod
    def get_hive(hive_id):
        return Hive.objects.get(id=hive_id)


class NectarService:
    @staticmethod
    def submit_nectar_application(nectar, bee):
        if Contract.objects.filter(nectar=nectar, bee=bee, is_accepted=False).exists():
            raise ValidationError("A pending application already exists.")
        application = Contract.objects.create(nectar=nectar, bee=bee)
        return application

    @staticmethod
    def accept_nectar_application(application, user):
        application.accept_application(user)
