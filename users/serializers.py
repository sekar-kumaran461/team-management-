from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'phone', 'bio', 'date_joined',
            'total_tasks_completed', 'total_resources_shared', 'total_points',
            'is_active'
        ]
        read_only_fields = [
            'id', 'date_joined', 'total_tasks_completed', 
            'total_resources_shared', 'total_points'
        ]

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'github_username', 'linkedin_url',
            'preferred_learning_topics', 'learning_goals', 'timezone',
            'notification_preferences'
        ]

class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password', 'password_confirm', 'role'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        return user

class UserStatsSerializer(serializers.Serializer):
    """Serializer for user statistics"""
    tasks_completed = serializers.IntegerField()
    tasks_pending = serializers.IntegerField()
    resources_shared = serializers.IntegerField()
    projects_active = serializers.IntegerField()
    total_points = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    learning_streak = serializers.IntegerField()
