import django_filters
from taggit.models import Tag

from .models import Hive, Bee, Nectar, Membership, Contract, HiveRequest, Report


class HiveFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__name',
        to_field_name='name',
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Hive
        fields = {
            'name': ['exact', 'icontains'],
            'hive_type': ['exact'],
            'is_public': ['exact'],
            'tags': ['exact'],
        }


class BeeFilter(django_filters.FilterSet):
    class Meta:
        model = Bee
        fields = {
            'bee_type': ['exact'],
            'user__email': ['exact', 'icontains'],
        }


class NectarFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__name',
        to_field_name='name',
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Nectar
        fields = {
            'nectar_title': ['exact', 'icontains'],
            'nectar_hive': ['exact'],
            'is_public': ['exact'],
            'price': ['lt', 'gt'],
            'deadline': ['lt', 'gt'],
            'tags': ['exact'],
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


class HiveRequestFilter(django_filters.FilterSet):
    hive = django_filters.NumberFilter(field_name='hive__id', lookup_expr='exact')
    bee = django_filters.NumberFilter(field_name='bee__id', lookup_expr='exact')
    is_accepted = django_filters.BooleanFilter(field_name='is_accepted')
    applied_at = django_filters.DateTimeFilter(field_name='applied_at', lookup_expr='exact')
    applied_at__gte = django_filters.DateTimeFilter(field_name='applied_at', lookup_expr='gte')
    applied_at__lte = django_filters.DateTimeFilter(field_name='applied_at', lookup_expr='lte')
    accepted_at = django_filters.DateTimeFilter(field_name='accepted_at', lookup_expr='exact')
    accepted_at__gte = django_filters.DateTimeFilter(field_name='accepted_at', lookup_expr='gte')
    accepted_at__lte = django_filters.DateTimeFilter(field_name='accepted_at', lookup_expr='lte')

    class Meta:
        model = HiveRequest
        fields = ['hive', 'bee', 'is_accepted', 'applied_at', 'accepted_at']


class ReportsFilter(django_filters.FilterSet):
    class Meta:
        model = Report
        fields = {
            'hive': ['exact'],
            'bee': ['exact'],
            'nectar': ['exact'],
        }
