from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


# Create your views here.
class UserIDView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"user_id": request.user.id})
