from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import models

# Try to import REST framework components
try:
    from rest_framework import viewsets, permissions, status
    from rest_framework.response import Response
    from rest_framework.views import APIView
    from rest_framework.decorators import action
    HAS_REST_FRAMEWORK = True
except ImportError:
    HAS_REST_FRAMEWORK = False
    # Create dummy classes
    class ViewSets:
        class ModelViewSet:
            pass
    viewsets = ViewSets()
    
    class APIView:
        pass
    
    class Permissions:
        class IsAuthenticated:
            pass
    permissions = Permissions()
    
    class Status:
        HTTP_200_OK = 200
        HTTP_400_BAD_REQUEST = 400
        HTTP_404_NOT_FOUND = 404
    status = Status()
    
    def action(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    class Response:
        def __init__(self, data=None, status=None):
            self.data = data
            self.status = status

from .models import Resource, ResourceCategory, ResourceFile, StudyMaterial, ResourceLike, ResourceDownload
from .forms import ResourceUploadForm, ResourceSearchForm, ResourceCategoryForm

# Web Views
class ResourceListView(LoginRequiredMixin, ListView):
    model = Resource
    template_name = 'resources/resource_list.html'
    context_object_name = 'resources'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Resource.objects.filter(is_public=True).order_by('-created_at')
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ResourceCategory.objects.all()
        return context

class ResourceDetailView(LoginRequiredMixin, DetailView):
    model = Resource
    template_name = 'resources/resource_detail.html'
    context_object_name = 'resource'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resource = self.get_object()
        context['files'] = resource.files.all()
        context['comments'] = resource.comments.all()[:10]  # Recent comments
        context['user_liked'] = ResourceLike.objects.filter(resource=resource, user=self.request.user).exists()
        context['study_material'] = getattr(resource, 'study_material', None)
        return context

class ResourceUploadView(LoginRequiredMixin, CreateView):
    model = Resource
    form_class = ResourceUploadForm
    template_name = 'resources/resource_upload.html'
    success_url = reverse_lazy('resources:resource-list')
    
    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, 'Resource uploaded successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ResourceCategory.objects.all().order_by('name')
        return context

class ResourceEditView(LoginRequiredMixin, UpdateView):
    model = Resource
    form_class = ResourceUploadForm
    template_name = 'resources/resource_edit.html'
    
    def get_success_url(self):
        return reverse_lazy('resources:resource-detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Resource updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ResourceCategory.objects.all().order_by('name')
        return context

class ResourceDownloadView(LoginRequiredMixin, DetailView):
    model = Resource
    template_name = 'resources/resource_download.html'
    context_object_name = 'resource'
    
    def get(self, request, *args, **kwargs):
        resource = self.get_object()
        # Track download
        ResourceDownload.objects.get_or_create(resource=resource, user=request.user)
        return super().get(request, *args, **kwargs)

class ResourceCategoryListView(LoginRequiredMixin, ListView):
    model = ResourceCategory
    template_name = 'resources/category_list.html'
    context_object_name = 'categories'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add resource count for each category
        for category in context['categories']:
            category.resource_count = category.resources.count()
        return context
    model = ResourceCategory
    template_name = 'resources/category_list.html'
    context_object_name = 'categories'

class StudyMaterialListView(LoginRequiredMixin, ListView):
    model = StudyMaterial
    template_name = 'resources/study_materials.html'
    context_object_name = 'study_materials'
    
    def get_queryset(self):
        return StudyMaterial.objects.filter(resource__is_public=True).order_by('-created_at')

class MyResourcesView(LoginRequiredMixin, ListView):
    model = Resource
    template_name = 'resources/my_resources.html'
    context_object_name = 'resources'
    
    def get_queryset(self):
        return Resource.objects.filter(uploaded_by=self.request.user).order_by('-created_at')

# API ViewSets - Only available if REST framework is installed
if HAS_REST_FRAMEWORK:
    class ResourceViewSet(viewsets.ModelViewSet):
        queryset = Resource.objects.all()
        permission_classes = [permissions.IsAuthenticated]
        
        def get_queryset(self):
            queryset = Resource.objects.filter(is_public=True)
            # Allow users to see their own private resources
            if self.request.user.is_authenticated:
                queryset = queryset.filter(
                    models.Q(is_public=True) | models.Q(uploaded_by=self.request.user)
                )
            return queryset.order_by('-created_at')
        
        def get_serializer_class(self):
            from rest_framework import serializers
            from django.db import models
            class ResourceSerializer(serializers.ModelSerializer):
                class Meta:
                    model = Resource
                    fields = '__all__'
            return ResourceSerializer
        
        @action(detail=True, methods=['post'])
        def like(self, request, pk=None):
            """Like/unlike a resource"""
            resource = self.get_object()
            like, created = ResourceLike.objects.get_or_create(resource=resource, user=request.user)
            
            if not created:
                like.delete()
                return Response({'status': 'unliked'})
            return Response({'status': 'liked'})

    class ResourceCategoryViewSet(viewsets.ModelViewSet):
        queryset = ResourceCategory.objects.all()
        permission_classes = [permissions.IsAuthenticated]
        
        def get_serializer_class(self):
            from rest_framework import serializers
            class ResourceCategorySerializer(serializers.ModelSerializer):
                class Meta:
                    model = ResourceCategory
                    fields = '__all__'
            return ResourceCategorySerializer

    class StudyMaterialViewSet(viewsets.ModelViewSet):
        queryset = StudyMaterial.objects.all()
        permission_classes = [permissions.IsAuthenticated]
        
        def get_queryset(self):
            return StudyMaterial.objects.filter(resource__is_public=True)
        
        def get_serializer_class(self):
            from rest_framework import serializers
            class StudyMaterialSerializer(serializers.ModelSerializer):
                class Meta:
                    model = StudyMaterial
                    fields = '__all__'
            return StudyMaterialSerializer

    class GoogleDriveUploadAPIView(APIView):
        permission_classes = [permissions.IsAuthenticated]
        
        def post(self, request):
            # Placeholder for Google Drive upload functionality
            return Response({'message': 'Google Drive upload endpoint - implementation pending'})

    class ResourceSearchAPIView(APIView):
        permission_classes = [permissions.IsAuthenticated]
        
        def get(self, request):
            query = request.GET.get('q', '')
            category = request.GET.get('category', '')
            
            resources = Resource.objects.filter(is_public=True)
            
            if query:
                resources = resources.filter(
                    models.Q(title__icontains=query) | 
                    models.Q(description__icontains=query) |
                    models.Q(tags__icontains=query)
                )
            
            if category:
                resources = resources.filter(category_id=category)
            
            resource_data = []
            for resource in resources[:20]:  # Limit results
                resource_data.append({
                    'id': resource.id,
                    'title': resource.title,
                    'description': resource.description,
                    'category': resource.category.name if resource.category else None,
                    'uploaded_by': resource.uploaded_by.get_full_name(),
                    'created_at': resource.created_at,
                })
            
            return Response({
                'results': resource_data,
                'total': len(resource_data)
            })

else:
    # Dummy classes when REST framework is not available
    class ResourceViewSet:
        pass
    
    class ResourceCategoryViewSet:
        pass
    
    class StudyMaterialViewSet:
        pass
    
    class GoogleDriveUploadAPIView:
        pass
    
    class ResourceSearchAPIView:
        pass
