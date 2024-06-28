import django_filters

from .models import Skill


class SkillFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Skill
        fields = ['name', 'type']  # You can add more fields to filter on if needed
