from rest_framework import serializers
from .models import User
from datetime import datetime


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model - read operations and updates"""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'date_of_birth', 'is_active', 'date_joined'
        ]
        read_only_fields = ['id', 'is_active', 'date_joined']

    def validate_email(self, value):
        """Validate email uniqueness for new users"""
        if self.instance is None and User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value
    
    def validate_username(self, value):
        """Validate username uniqueness for new users"""
        if self.instance is None and User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Username already exists')
        return value
    
    def validate_date_of_birth(self, value):
        """Validate date of birth is not in the future"""
        if value and value > datetime.now().date():
            raise serializers.ValidationError('Date of birth cannot be in the future')
        return value


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration with password confirmation"""
    
    password = serializers.CharField(
        write_only=True, 
        min_length=8,
        style={'input_type': 'password'}
    )
    password_confirmation = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 
            'date_of_birth', 'password', 'password_confirmation'
        ]
        extra_kwargs = {
            'username': {'help_text': 'Required. 150 characters or fewer.'},
            'email': {'help_text': 'Required. Enter a valid email address.'},
        }
    
    def validate(self, attrs):
        """Validate password confirmation"""
        if attrs['password'] != attrs['password_confirmation']:
            raise serializers.ValidationError({
                'password_confirmation': "Passwords don't match"
            })
        return attrs
        
    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop('password_confirmation')
        return User.objects.create_user(**validated_data)
    
    def validate_email(self, value):
        """Validate email uniqueness"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value

    def validate_username(self, value):
        """Validate username uniqueness"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Username already exists')
        return value

    def validate_date_of_birth(self, value):
        """Validate date of birth"""
        if value and value > datetime.now().date():
            raise serializers.ValidationError('Date of birth cannot be in the future')
        return value


class UpdateUserProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile - excludes sensitive fields"""
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'date_of_birth'
        ]
        extra_kwargs = {
            'username': {'help_text': 'Required. 150 characters or fewer.'},
            'email': {'help_text': 'Required. Enter a valid email address.'},
        }
    
    def validate_username(self, value):
        """Validate username uniqueness for updates"""
        if self.instance and self.instance.username != value:
            if User.objects.filter(username=value).exists():
                raise serializers.ValidationError('Username already exists')
        return value

    def validate_email(self, value):
        """Validate email uniqueness for updates"""
        if self.instance and self.instance.email != value:
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError('Email already exists')
        return value
    
    def validate_date_of_birth(self, value):
        """Validate date of birth"""
        if value and value > datetime.now().date():
            raise serializers.ValidationError('Date of birth cannot be in the future')
        return value