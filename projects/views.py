from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from .models import Project, ProjectCategory, ProjectMilestone, ProjectSubmission, WeeklyProjectReview
from .serializers import ProjectSerializer, ProjectMilestoneSerializer, ProjectSubmissionSerializer

# Web Views
class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 10

    def get_queryset(self):
        queryset = Project.objects.all().order_by('-created_at')
        # Filter by user's projects if not admin/team_lead
        if not self.request.user.can_manage_users():
            queryset = queryset.filter(team_members=self.request.user)
        return queryset

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        context['milestones'] = project.milestones.all()
        context['submissions'] = project.submissions.all()[:5]  # Recent submissions
        context['weekly_reviews'] = project.weekly_reviews.all()[:3]  # Recent reviews
        return context

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    template_name = 'projects/project_create.html'
    fields = ['title', 'description', 'category', 'difficulty_level', 'estimated_duration_weeks', 'required_skills', 'technologies']
    success_url = reverse_lazy('projects:project-list')

    def form_valid(self, form):
        form.instance.project_manager = self.request.user
        messages.success(self.request, 'Project created successfully!')
        return super().form_valid(form)

class ProjectEditView(LoginRequiredMixin, UpdateView):
    model = Project
    template_name = 'projects/project_edit.html'
    fields = ['title', 'description', 'category', 'status', 'difficulty_level', 'estimated_duration_weeks', 'progress_percentage']
    
    def get_success_url(self):
        return reverse_lazy('projects:project-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Project updated successfully!')
        return super().form_valid(form)

class ProjectSubmissionView(LoginRequiredMixin, CreateView):
    model = ProjectSubmission
    template_name = 'projects/project_submission.html'
    fields = ['submission_type', 'title', 'description', 'file_path', 'external_url', 'notes']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = get_object_or_404(Project, pk=self.kwargs['pk'])
        return context
    
    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        form.instance.project = project
        form.instance.submitted_by = self.request.user
        messages.success(self.request, 'Submission created successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('projects:project-detail', kwargs={'pk': self.kwargs['pk']})

class WeeklyReviewView(LoginRequiredMixin, CreateView):
    model = WeeklyProjectReview
    template_name = 'projects/weekly_review.html'
    fields = ['week_ending', 'accomplishments', 'challenges', 'progress_rating']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = get_object_or_404(Project, pk=self.kwargs['pk'])
        return context
    
    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        form.instance.project = project
        form.instance.reviewer = self.request.user
        messages.success(self.request, 'Weekly review submitted successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('projects:project-detail', kwargs={'pk': self.kwargs['pk']})

class MyProjectsView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/my_projects.html'
    context_object_name = 'projects'
    
    def get_queryset(self):
        return Project.objects.filter(team_members=self.request.user).order_by('-created_at')

# API ViewSets
class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Project.objects.all()
        # Filter by user's projects if not admin/team_lead
        if not self.request.user.can_manage_users():
            queryset = queryset.filter(team_members=self.request.user)
        return queryset
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update project progress"""
        project = self.get_object()
        progress = request.data.get('progress', 0)
        
        try:
            project.progress_percentage = min(100, max(0, int(progress)))
            project.save()
            return Response({'status': 'Progress updated successfully'})
        except (ValueError, TypeError):
            return Response({'error': 'Invalid progress value'}, status=status.HTTP_400_BAD_REQUEST)

class ProjectMilestoneViewSet(viewsets.ModelViewSet):
    queryset = ProjectMilestone.objects.all()
    serializer_class = ProjectMilestoneSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if 'project_pk' in self.kwargs:
            return ProjectMilestone.objects.filter(project_id=self.kwargs['project_pk'])
        return ProjectMilestone.objects.all()

class ProjectSubmissionViewSet(viewsets.ModelViewSet):
    queryset = ProjectSubmission.objects.all()
    serializer_class = ProjectSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if 'project_pk' in self.kwargs:
            return ProjectSubmission.objects.filter(project_id=self.kwargs['project_pk'])
        return ProjectSubmission.objects.all()

# API Views
class ProjectProgressAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        projects = Project.objects.filter(team_members=user)
        
        progress_data = []
        for project in projects:
            progress_data.append({
                'id': project.id,
                'title': project.title,
                'progress_percentage': project.progress_percentage,
                'status': project.status,
                'estimated_duration_weeks': project.estimated_duration_weeks,
            })
        
        return Response(progress_data)

class WeeklyReviewAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        reviews = WeeklyProjectReview.objects.filter(reviewer=user).order_by('-week_ending')[:10]
        
        review_data = []
        for review in reviews:
            review_data.append({
                'id': review.id,
                'project_title': review.project.title,
                'week_ending': review.week_ending,
                'progress_rating': review.progress_rating,
                'accomplishments': review.accomplishments,
                'challenges': review.challenges,
            })
        
        return Response(review_data)
    
    def get_serializer_class(self):
        from rest_framework import serializers
        class ProjectSerializer(serializers.ModelSerializer):
            class Meta:
                model = Project
                fields = '__all__'
        return ProjectSerializer

# Temporarily commented out until ProjectTask model is enabled
# class ProjectTaskViewSet(viewsets.ModelViewSet):
#     queryset = ProjectTask.objects.all()
#     permission_classes = [permissions.IsAuthenticated]
#     
#     def get_serializer_class(self):
#         from rest_framework import serializers
#         class ProjectTaskSerializer(serializers.ModelSerializer):
#             class Meta:
#                 model = ProjectTask
#                 fields = '__all__'
#         return ProjectTaskSerializer

class ProjectProgressAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        return Response({'message': 'Project progress endpoint'})

class WeeklyReviewAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        return Response({'message': 'Weekly review endpoint'})
