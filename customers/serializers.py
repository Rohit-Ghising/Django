from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

# Signup serializer
class RegisterSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'name', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['name']
        )

# Login serializer
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid email or password")
        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='first_name')
    role = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='date_joined')

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'createdAt']

    def get_role(self, obj):
        return 'admin' if obj.is_staff or obj.is_superuser else 'user'
