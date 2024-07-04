
from django.core.exceptions import ValidationError



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
        return hive.admins.all()

    @staticmethod
    def get_hive(hive_id) -> 'Hive':
        from .models import Hive
        return Hive.objects.get(id=hive_id)

    @staticmethod
    def get_user_hives(user: 'User') -> ['Hive']:
        from .models import Hive
        return Hive.objects.filter(admins=user)

    @staticmethod
    def get_hive_queryset(hive_ids: [str]):
        from .models import Hive
        return Hive.objects.filter(id__in=hive_ids)

    @staticmethod
    def create_hive(user, name, description, hive_type, is_public) -> 'Hive':
        from .models import Hive
        hive = Hive.objects.create(admins=[user], name=name, description=description, hive_type=hive_type, is_public=is_public)
        return hive


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

    @staticmethod
    def get_nectar_queryset(nectar_ids: [str]):
        from .models import Nectar
        return Nectar.objects.filter(id__in=nectar_ids)


    @staticmethod
    def create_nectar(user, name, description, nectar_type, is_public) -> 'Nectar':
        from .models import Nectar
        nectar = Nectar.objects.create(user=user, name=name, description=description, nectar_type=nectar_type, is_public=is_public)
        return nectar


class BeeService:
    @staticmethod
    def get_bee(bee_id) -> 'Bee':
        from .models import Bee
        return Bee.objects.get(id=bee_id)

    def get_bee_queryset(self, list_of_bee_ids: [str]):
        from .models import Bee
        return Bee.objects.filter(id__in=list_of_bee_ids)

    @staticmethod
    def get_user_bees(user: 'User') -> ['Bee']:
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

    @staticmethod
    def create_bee(user, bio, document_id= None) -> 'Bee':
        from common.models import Document
        from .models import Bee
        bee = Bee.objects.create(user=user, bee_bio=bio, bee_type=Bee.DEFAULT_BEE_TYPE)
        if document_id:
            document = Document.objects.get(id=document_id)
            document.user = user
            document.save()
            bee.documents.add(document)

    @staticmethod
    def get_user_bees_AI_readable(**kwargs):
        from .models import Bee
        return " ,".join([bee.convert_to_ai_readable() for bee in Bee.objects.all()])

    @staticmethod

    def get_bee_queryset_by_email(email_list: [str]):
        from .models import Bee
        return Bee.objects.filter(user__email__in=email_list)


class ContractService:

    @staticmethod
    def get_nectar_requests(user):
        from .models import Contract
        return [" ,".join(contract.convert_to_ai_readable()) for contract in Contract.objects.filter(is_accepted=False, accepted_at=None)]