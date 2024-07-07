# views.py
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated

from .filters import SkillFilter
from .models import User, Skill, Experience, Education, Certificate, Portfolio
from .serializers import UserWithRelatedFieldsSerializer, SkillSerializer, UserBaseCreateSerializer, UserSerializer, \
    UserListSerializer, \
    EducationReadSerializer, EducationWriteSerializer, ExperienceReadSerializer, ExperienceWriteSerializer, \
    CertificateReadSerializer, CertificateWriteSerializer, PortfolioReadSerializer, PortfolioWriteSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserBaseCreateSerializer
        if self.action == 'update':
            return UserSerializer
        if self.action == 'partial_update':
            return UserSerializer
        if self.action == 'retrieve':
            return UserWithRelatedFieldsSerializer
        return UserListSerializer

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class ExperienceViewSet(viewsets.ModelViewSet):
    queryset = Experience.objects.all()
    # parser_classes = (MultiPartParser, FormParser,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ExperienceReadSerializer
        return ExperienceWriteSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class EducationViewSet(viewsets.ModelViewSet):
    queryset = Education.objects.all()
    # parser_classes = (MultiPartParser, FormParser,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return EducationReadSerializer
        return EducationWriteSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class CertificateViewSet(viewsets.ModelViewSet):
    queryset = Certificate.objects.all()
    # parser_classes = (MultiPartParser, FormParser,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return CertificateReadSerializer
        return CertificateWriteSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class PortfolioViewSet(viewsets.ModelViewSet):
    queryset = Portfolio.objects.all()
    # parser_classes = (MultiPartParser, FormParser,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PortfolioReadSerializer
        return PortfolioWriteSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = SkillFilter
