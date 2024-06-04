# views.py
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from .models import User
from .serializers import UserSerializer
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
