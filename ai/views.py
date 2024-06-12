# views.py
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .services import run_message_through_hive_aware_assistant  # Import the function
from .serializers import HiveAssistantRequestSerializer

User = get_user_model()


class TestHiveAssistantView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=HiveAssistantRequestSerializer,

    )
    def post(self, request):
        serializer = HiveAssistantRequestSerializer(data=request.data)
        if serializer.is_valid():
            hive_id = serializer.validated_data['hive_id']
            message = serializer.validated_data['message']
            user_id = request.user.id
            thread_id = serializer.validated_data.get('thread_id', None)

            try:
                messages = run_message_through_hive_aware_assistant(hive_id, message, user_id, thread_id)
                return Response({'messages': messages})
            except ValidationError as e:
                return Response({'error': str(e)}, status=400)
            except Exception as e:
                return Response({'error': 'An error occurred while processing your request'}, status=500)
        else:
            return Response(serializer.errors, status=400)
