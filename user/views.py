# views.py
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import SkillFilter
from .models import User, Skill, UserPreferences
from .serializers import UserSerializer, SkillSerializer, UserPreferencesSerializer
from .swagger import CREATE_NEW_USER, UPDATE_AN_EXISTING_USER, PARTIAL_UPDATE_USER


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @swagger_auto_schema(
        request_body=UserSerializer,
        responses={200: UserSerializer()},
        operation_description=CREATE_NEW_USER
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=UserSerializer,
        responses={200: UserSerializer()},
        operation_description=UPDATE_AN_EXISTING_USER
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=UserSerializer,
        responses={200: UserSerializer()},
        operation_description=PARTIAL_UPDATE_USER
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def set_preferences(self, request, pk=None):
        user = self.get_object()
        serializer = UserPreferencesSerializer(data=request.data)

        if serializer.is_valid():
            UserPreferences.objects.update_or_create(
                user=user,
                defaults=serializer.validated_data
            )
            return Response({'status': 'preferences set'})
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = SkillFilter