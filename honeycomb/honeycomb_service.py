from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from honeycomb.models import Bee, Contract, Nectar


class HiveService:
    @staticmethod
    def submit_membership_application(hive, bee):
        from .models import HiveRequest, Membership
        if HiveRequest.objects.filter(hive=hive, bee=bee, is_accepted=False).exists():
            raise ValidationError("A pending application already exists.")
        if Membership.objects.filter(hive=hive, bee=bee).exists():
            raise ValidationError("The bee is already a member of the hive.")
        # todo: more validation is needed, e.g. bee is not already a member of the hive
        application = HiveRequest.objects.create(hive=hive, bee=bee)
        return application

    @staticmethod
    def accept_membership_application(application, user):
        application.accept_application(user)

    @staticmethod
    def get_hive_admins(hive):
        from .models import Hive
        return hive.admins.all()

    @staticmethod
    def get_hive(hive_id) -> 'Hive':
        from .models import Hive
        return Hive.objects.get(id=hive_id)

    @staticmethod
    def get_user_hives(user: User) -> ['Hive']:
        from .models import Hive
        return Hive.objects.filter(admins=user)


class NectarService:
    @staticmethod
    def submit_nectar_application(nectar, bee):
        from .models import Contract
        if Contract.objects.filter(nectar=nectar, bee=bee, is_accepted=False).exists():
            raise ValidationError("A pending application already exists.")
        application = Contract.objects.create(nectar=nectar, bee=bee)
        return application

    @staticmethod
    def accept_nectar_application(application, user):
        application.accept_application(user)


class BeeService:
    @staticmethod
    def get_bee(bee_id) -> 'Bee':
        from .models import Bee
        return Bee.objects.get(id=bee_id)

    def get_bee_queryset(self, list_of_bee_ids:[str]):
        from .models import Bee
        return Bee.objects.filter(id__in=list_of_bee_ids)

    @staticmethod
    def get_user_bees(user: User) -> ['Bee']:
        from .models import Bee
        return Bee.objects.filter(user=user)

    @staticmethod
    def get_hive_bees(hive) -> ['Bee']:
        from .models import Bee
        return Bee.objects.filter(hive=hive)

    @staticmethod
    def get_bee_contracts(bee) -> ['Contract']:
        from .models import Contract
        return Contract.objects.filter(bee=bee)

    @staticmethod
    def get_bee_nectars(bee) -> ['Nectar']:
        from .models import Nectar
        return Nectar.objects.filter(bee=bee)