import django_filters

from .models import Hive, Bee, Nectar, Membership, Contract


class HiveFilter(django_filters.FilterSet):
    class Meta:
        model = Hive
        fields = {
            'name': ['exact', 'icontains'],
            'hive_type': ['exact'],
            'is_public': ['exact'],
        }


class BeeFilter(django_filters.FilterSet):
    class Meta:
        model = Bee
        fields = {
            'bee_type': ['exact'],
            'user__email': ['exact', 'icontains'],
        }


class NectarFilter(django_filters.FilterSet):
    class Meta:
        model = Nectar
        fields = {
            'nectar_title': ['exact', 'icontains'],
            'nectar_hive': ['exact'],
            'is_public': ['exact'],
            'price': ['lt', 'gt'],
            'deadline': ['lt', 'gt'],
        }


class MembershipFilter(django_filters.FilterSet):
    class Meta:
        model = Membership
        fields = {
            'hive': ['exact'],
            'bee': ['exact'],
            'is_accepted': ['exact'],
        }


class ContractFilter(django_filters.FilterSet):
    class Meta:
        model = Contract
        fields = {
            'nectar': ['exact'],
            'bee': ['exact'],
            'is_accepted': ['exact'],
            'applied_at': ['lt', 'gt'],
            'accepted_at': ['lt', 'gt'],
        }
