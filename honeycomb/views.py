from django.core.exceptions import ValidationError, PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import HiveFilter, BeeFilter, NectarFilter, MembershipFilter, ContractFilter
from .honeycomb_service import NectarService, HiveService
from .models import Hive, Bee, Membership, Nectar, HiveRequest, Contract
from .permissions import IsHiveAdmin
from .serializers import HiveSerializer, BeeSerializer, MembershipSerializer, NectarSerializer, HiveRequestSerializer, \
    ContractSerializer


class HiveViewSet(viewsets.ModelViewSet):
    queryset = Hive.objects.all()
    serializer_class = HiveSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = HiveFilter

    def perform_create(self, serializer):
        hive = serializer.save()
        hive.admins.add(self.request.user)
        return hive

    def perform_update(self, serializer):
        hive = self.get_object()
        if not hive.is_admin_by_user(self.request.user):
            raise PermissionDenied("You do not have permission to edit this hive.")
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        hive = self.get_object()
        if not hive.is_admin_by_user(request.user):
            raise PermissionDenied("You do not have permission to delete this hive.")
        # Custom logic for deleting a hive can go here
        return super().destroy(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        hive = self.get_object()
        if not hive.is_admin_by_user(request.user):
            raise PermissionDenied("You do not have permission to partially update this hive.")
        # Custom logic for partial updates can go here
        return super().partial_update(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        bees_ordered = instance.get_bees_ordered_by_honey_points()
        data = {
            "hive": HiveSerializer(instance).data,
            "bees": [
                {
                    "bee_id": bee.id,
                    "email": bee.user.email,
                    "total_honey_points": bee.total_honey_points
                } for bee in bees_ordered
            ]
        }
        return Response(data)


class BeeViewSet(viewsets.ModelViewSet):
    queryset = Bee.objects.all()
    serializer_class = BeeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = BeeFilter


class MembershipViewSet(viewsets.ModelViewSet):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = MembershipFilter


class NectarViewSet(viewsets.ModelViewSet):
    queryset = Nectar.objects.all()
    serializer_class = NectarSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = NectarFilter


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
    filter_backends = [DjangoFilterBackend]
    filterset_class = ContractFilter

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


class Membership(APIView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hive_service = HiveService()
        self.nectar_service = NectarService()

    def post(self, request):
        hive_id = request.data.get('hive')
        if not hive_id:
            return Response({"message": "Hive ID is required"}, status=400)

        try:
            hive = self._get_hive(hive_id)
            bee = self._get_bee(request.user)
            application = self._submit_application(hive, bee)
            return self._handle_application_response(application, request.user)
        except NotFound as e:
            return Response({"message": str(e)}, status=404)
        except ValidationError as e:
            return Response({"message": str(e)}, status=400)

    def _get_hive(self, hive_id):
        try:
            return self.hive_service.get_hive(hive_id)
        except Hive.DoesNotExist:
            raise NotFound("Hive not found")

    def _get_bee(self, user):
        try:
            return Bee.objects.get(user=user)
        except Bee.DoesNotExist:
            raise NotFound("There is no associated bee to you")

    def _submit_application(self, hive, bee):
        try:
            return self.hive_service.submit_membership_application(hive, bee)
        except ValidationError:
            raise ValidationError("You already have a pending application.")

    def _handle_application_response(self, application, user):
        try:
            membership = application.accept_application(user)
            serialized_membership = MembershipSerializer(membership)
            return Response(
                {"message": "Application accepted successfully.", "membership": serialized_membership.data},
                status=201)
        except ValidationError:
            serialized_hive_request = HiveRequestSerializer(application)
            return Response(
                {"message": "Application submitted", "application": serialized_hive_request.data},
                status=400
            )
