from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

class UserRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(max_length=150, required=True, min_length=6, write_only=True)

    def validate_username(self, data):
        # Проверка что username не пустой
        if not data.strip():
            raise serializers.ValidationError("Username cannot be empty")
        # Проверка на уникальность (без учета регистра)
        if User.objects.filter(username__iexact=data).exists():
            raise serializers.ValidationError("Username already taken")
        return data

    def create(self, validated_data):
        # Создаем пользователя с паролем
        user = User.objects.create_user(
            username=validated_data['username'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password']
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, data):  # <- метод должен называться validate, а не validate_login
        username = data.get("username")
        password = data.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                data["user"] = user
            else:
                raise serializers.ValidationError("Invalid username or password")
        else:
            raise serializers.ValidationError("Both username and password are required")
        return data
