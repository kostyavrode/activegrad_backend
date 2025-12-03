from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import CustomUser
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    
    class Meta:
        model = CustomUser
        fields = [
            "id", "username", "first_name", "last_name", "password",
            "coins", "registration_date", "boots", "pants", "tshirt",
            "cap", "gender"
        ]
        read_only_fields = ["coins", "registration_date", "boots", "pants", "tshirt", "cap", "gender"]   

    def validate_username(self, data):
        # Проверка что username не пустой
        if not data.strip():
            raise serializers.ValidationError("Username cannot be empty")
        # Проверка на уникальность (без учета регистра)
        if CustomUser.objects.filter(username__iexact=data).exists():
            raise serializers.ValidationError("Username already taken")
        return data

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data["username"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            password=validated_data["password"],
            gender=validated_data.get("gender", None),
        )
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Можно добавить кастомные поля прямо в токен (необязательно)
        token['username'] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Добавляем данные о пользователе в ответ
        data['user'] = {
            "id": self.user.id,
            "player_id": self.user.id,  # Явно добавляем player_id для удобства
            "username": self.user.username,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "coins": self.user.coins,
            "registration_date": self.user.registration_date,
            "boots": self.user.boots,
            "pants": self.user.pants,
            "tshirt": self.user.tshirt,
            "cap": self.user.cap,
        }
        return data

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

class UserClothesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["boots", "pants", "tshirt", "cap", "gender"]