from django.core.exceptions import ValidationError, PermissionDenied
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, MethodNotAllowed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.models import Document
from .filters import HiveFilter, BeeFilter, NectarFilter, MembershipFilter, ContractFilter, HiveRequestFilter
from .honeycomb_service import NectarService, HiveService
from .models import Hive, Bee, Membership, Nectar, HiveRequest, Contract, Report
from .serializers import HiveSerializer, BeeSerializer, MembershipSerializer, NectarSerializer, HiveRequestSerializer, \
    ContractSerializer, MembershipAcceptSerializer, ReportSerializer, HiveWiThDetailsSerializer


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

    @action(detail=True, methods=['get'], url_path='dashboard')
    def dashboard(self, request, pk=None):
        try:
            hive = self.get_object()

            # Aggregated Data
            active_nectars = Nectar.objects.filter(nectar_hive=hive, status='Active')
            completed_nectars = Nectar.objects.filter(nectar_hive=hive, status='Complete')
            active_nectars_count = active_nectars.count()
            total_open_contracts = Contract.objects.filter(nectar__nectar_hive=hive, is_accepted=True,
                                                           completed_at__isnull=True).count()
            total_contracts = Contract.objects.filter(nectar__nectar_hive=hive).count()
            pending_requests = HiveRequest.objects.filter(hive=hive, is_accepted=False).count()
            pending_contracts = Contract.objects.filter(nectar__nectar_hive=hive, is_accepted=False).count()
            last_reports = Report.objects.filter(hive=hive).order_by('-created_at')[:5]

            data = {
                'hive': HiveWiThDetailsSerializer(hive).data,
                'active_nectars': NectarSerializer(active_nectars, many=True).data,
                'total_active_nectars': active_nectars_count,
                'total_completed_nectars': completed_nectars.count(),
                'total_open_contracts': total_open_contracts,
                'total_contracts': total_contracts,
                'pending_requests': pending_requests,
                'pending_contracts': pending_contracts,
                'last_reports': ReportSerializer(last_reports, many=True).data
            }
            return Response(data)
        except Hive.DoesNotExist:
            return Response({"message": "Hive not found"}, status=404)


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

    def get_queryset(self):
        user = self.request.user
        return Membership.objects.filter(bee__user=user)


class NectarViewSet(viewsets.ModelViewSet):
    queryset = Nectar.objects.all()
    serializer_class = NectarSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = NectarFilter

    def perform_create(self, serializer):
        documents = self.request.FILES.getlist('documents')
        nectar = serializer.save()
        for document in documents:
            Document.objects.create(
                user=self.request.user,
                document=document,
                description=f"Document for nectar {nectar.id}"
            )
            nectar.documents.add(document)
        nectar.save()

        return nectar


class HiveRequestViewSet(viewsets.ModelViewSet):
    queryset = HiveRequest.objects.all()
    serializer_class = HiveRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = HiveRequestFilter

    def get_queryset(self):
        user = self.request.user
        hives_admin = Hive.objects.filter(admins__in=[user])
        hive_ids = hives_admin.values_list('id', flat=True)
        return HiveRequest.objects.filter(hive_id__in=hive_ids)

    def perform_create(self, serializer):
        hive = serializer.validated_data['hive']
        bee = serializer.validated_data['bee']
        try:
            application = HiveService.submit_membership_application(hive, bee)
            return self._handle_application_response(application, self.request.user)
        except NotFound as e:
            raise ValidationError({"message": str(e)})
        except ValidationError as e:
            raise ValidationError({"message": str(e)})

    def perform_update(self, serializer):
        raise MethodNotAllowed("PUT/PATCH method not allowed on this endpoint.")

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed("DELETE method not allowed on this endpoint.")

    def get_permissions(self):
        permission_classes = [IsAuthenticated]
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes.append(MethodNotAllowed)
        return [permission() for permission in permission_classes]

    def _handle_application_response(self, application, user):
        if self._is_user_admin_of_hive(application.hive, user):
            try:
                membership = application.accept_application(user)
                serialized_membership = MembershipSerializer(membership)
                return Response(
                    {"message": "Application accepted successfully.", "membership": serialized_membership.data},
                    status=status.HTTP_202_ACCEPTED)
            except ValidationError as e:
                raise ValidationError({"message": str(e)})
        else:
            serialized_hive_request = HiveRequestSerializer(application)
            return Response(
                {"message": "Application submitted", "application": serialized_hive_request.data},
                status=status.HTTP_201_CREATED)

    @staticmethod
    def _is_user_admin_of_hive(hive, user):
        return hive.is_admin_by_user(user)


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['hive', 'nectar', 'bee', 'created_at']

    def get_queryset(self):
        user = self.request.user
        member_hive_ids = Membership.objects.filter(bee__user=user).values_list('hive_id', flat=True)
        public_hive_ids = Hive.objects.filter(is_public=True).values_list('id', flat=True)
        return Report.objects.filter(
            Q(hive_id__in=member_hive_ids) |
            Q(hive_id__in=public_hive_ids)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save()


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
            NectarService.accept_nectar_application(instance, self.request.user.bee)
        return super().perform_update(serializer)


class MembershipAcceptView(APIView):
    MEMBERSHIP_ACCEPT_SUCCESS = "Membership application accepted"
    HIVE_REQUEST_NOT_FOUND = "Hive Request not found"
    NOT_HIVE_ADMIN = "You are not an admin of this hive"
    FIELD_REQUIRED = "This field is required."
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hive_service = HiveService()
        self.nectar_service = NectarService()

    @swagger_auto_schema(
        request_body=MembershipAcceptSerializer,
        responses={
            200: openapi.Response(description=MEMBERSHIP_ACCEPT_SUCCESS,
                                  examples={"application/json": {"message": MEMBERSHIP_ACCEPT_SUCCESS}}),
            400: openapi.Response(description="Bad Request",
                                  examples={"application/json": {"hive_request_id": [FIELD_REQUIRED]}}),
            403: openapi.Response(description="Forbidden",
                                  examples={"application/json": {"message": NOT_HIVE_ADMIN}}),
            404: openapi.Response(description="Not Found",
                                  examples={"application/json": {"message": HIVE_REQUEST_NOT_FOUND}})
        }
    )
    def post(self, request):
        serializer = MembershipAcceptSerializer(data=request.data)

        if serializer.is_valid():
            hive_request_id = serializer.validated_data['hive_request_id']

            hive = self.hive_service.get_hive(hive_request_id)
            if not hive:
                return Response({"message": self.HIVE_REQUEST_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            if not hive.is_admin_by_user(request.user):
                return Response({"message": self.NOT_HIVE_ADMIN}, status=status.HTTP_403_FORBIDDEN)

            hive.accept_application(request.user.bee)
            return Response({"message": self.MEMBERSHIP_ACCEPT_SUCCESS}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
