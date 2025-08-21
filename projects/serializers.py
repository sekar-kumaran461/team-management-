from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Project, ProjectMilestone, ProjectSubmission

User = get_user_model()

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'

class ProjectMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMilestone
        fields = '__all__'

class ProjectSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectSubmission
        fields = '__all__'
