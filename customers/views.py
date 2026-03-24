from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from products.permissions import IsSuperUser
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer

# Signup API
@api_view(['POST'])
def signup(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        token_data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        return Response({'user': UserSerializer(user).data, **token_data})
    return Response(serializer.errors, status=400)

# Login API
@api_view(['POST'])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        token_data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        return Response({'user': UserSerializer(user).data, **token_data})
    return Response(serializer.errors, status=400)

# Example protected route
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_route(request):
    return Response({'message': f'Hello {request.user.first_name}, you are authenticated!'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSuperUser])
def list_users(request):
    users = User.objects.order_by('-date_joined')
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)
