# views.py
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import HiveAssistantRequestSerializer
from .services import AIService

User = get_user_model()


class TestHiveAssistantView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=HiveAssistantRequestSerializer,

    )
    def post(self, request):
        serializer = HiveAssistantRequestSerializer(data=request.data)
        if serializer.is_valid():
            message = serializer.validated_data['message']
            additional_instructions = serializer.validated_data['additional_instructions']

            try:
                ai_service = AIService(user=request.user, assistant_type="hive_assistant")
                messages = ai_service.send_message(message=message, additional_instructions=additional_instructions,
                                                   ai_type="hive_assistant")
                return Response({'messages': messages})
            except ValidationError as e:
                return Response({'error': str(e)}, status=400)
            except Exception as e:
                print(e)
                return Response({'error': 'An error occurred while processing your request'}, status=500)
        else:
            return Response(serializer.errors, status=400)
