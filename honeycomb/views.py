from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .honeycomb_service import NectarService, HiveService
from .models import Hive, Bee, Membership, Nectar, HiveRequest, Contract
from .permissions import IsHiveAdmin
from .serializers import HiveSerializer, BeeSerializer, MembershipSerializer, NectarSerializer, HiveRequestSerializer, \
    ContractSerializer


class HiveViewSet(viewsets.ModelViewSet):
    queryset = Hive.objects.all()
    serializer_class = HiveSerializer
    permission_classes = [IsAuthenticated]


class BeeViewSet(viewsets.ModelViewSet):
    queryset = Bee.objects.all()
    serializer_class = BeeSerializer
    permission_classes = [IsAuthenticated]


class MembershipViewSet(viewsets.ModelViewSet):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticated]


class NectarViewSet(viewsets.ModelViewSet):
    queryset = Nectar.objects.all()
    serializer_class = NectarSerializer
    permission_classes = [IsAuthenticated]


class HiveRequestViewSet(viewsets.ModelViewSet):
    queryset = HiveRequest.objects.all()
    serializer_class = HiveRequestSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        hive = serializer.validated_data['hive']
        bee = serializer.validated_data['bee']
        HiveService.submit_membership_application(hive, bee)
        return super().perform_create(serializer)

    def perform_update(self, serializer):
        instance = self.get_object()
        if 'is_accepted' in serializer.validated_data and serializer.validated_data['is_accepted']:
            HiveService.accept_membership_application(instance)
        return super().perform_update(serializer)

    def get_permissions(self):
        permission_classes = [IsAuthenticated]
        if self.action in ['update', 'partial_update']:
            permission_classes.append(IsHiveAdmin)
        return [permission() for permission in permission_classes]


class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        nectar = serializer.validated_data['nectar']
        applicant = serializer.validated_data['bee']
        NectarService.submit_nectar_application(nectar, applicant)
        return super().perform_create(serializer)

    def perform_update(self, serializer):
        instance = self.get_object()
        if 'is_accepted' in serializer.validated_data and serializer.validated_data['is_accepted']:
            NectarService.accept_nectar_application(instance)
        return super().perform_update(serializer)
