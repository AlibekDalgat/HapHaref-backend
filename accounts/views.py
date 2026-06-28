from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .serializers import UserSerializer


class LoginRateThrottle(AnonRateThrottle):
    """Limit login attempts per IP to slow down password brute-forcing."""

    scope = "login"


class LoginView(APIView):
    """Exchange username/password for an auth token (for the React admin)."""

    authentication_classes = []
    permission_classes = []
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {"detail": "Неверный логин или пароль."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.can_edit_dictionary:
            return Response(
                {"detail": "Доступ только для редакторов словаря."},
                status=status.HTTP_403_FORBIDDEN,
            )
        token, _ = Token.objects.get_or_create(user=user)
        django_login(request, user)
        return Response({"token": token.key, "user": UserSerializer(user).data})


class MeView(APIView):
    """Return the currently authenticated user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class LogoutView(APIView):
    """Invalidate the current token."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        django_logout(request)  # also clear the Django session
        return Response(status=status.HTTP_204_NO_CONTENT)
