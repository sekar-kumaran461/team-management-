from django import forms
from django.contrib.auth import get_user_model
from .models import Task, TaskFile, TaskCategory, TaskSubmission, BulkTaskUpload
from users.models import Tag, Skill, Technology

User = get_user_model()

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class TaskCreateForm(forms.ModelForm):
    """Enhanced task creation form with file upload support"""
    
    # Multiple file upload field
    files = MultipleFileField(
        required=False,
        help_text='Select multiple files to attach to this task'
    )
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'category', 'task_type', 'priority', 'difficulty',
            'due_date', 'start_date', 'assigned_to', 'reviewer', 'estimated_hours',
            'acceptance_criteria', 'points_value', 'tags', 'required_skills', 'technologies'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Enter task title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 4,
                'placeholder': 'Describe the task in detail'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'task_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'difficulty': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'type': 'datetime-local'
            }),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'type': 'datetime-local'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'reviewer': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'step': '0.5',
                'min': '0.5'
            }),
            'acceptance_criteria': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Define what constitutes task completion'
            }),
            'points_value': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'min': '1'
            }),
            'tags': forms.CheckboxSelectMultiple(attrs={
                'class': 'grid grid-cols-2 gap-2'
            }),
            'required_skills': forms.CheckboxSelectMultiple(attrs={
                'class': 'grid grid-cols-2 gap-2'
            }),
            'technologies': forms.CheckboxSelectMultiple(attrs={
                'class': 'grid grid-cols-2 gap-2'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter active users for assignment
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)
        self.fields['reviewer'].queryset = User.objects.filter(is_active=True, groups__name__in=['Teacher', 'Admin'])

class TaskFileUploadForm(forms.ModelForm):
    """Form for uploading files to tasks"""
    
    class Meta:
        model = TaskFile
        fields = ['file_type', 'description']
        widgets = {
            'file_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 2,
                'placeholder': 'Optional description for this file'
            }),
        }

class TaskSubmissionForm(forms.ModelForm):
    """Enhanced task submission form with file upload"""
    
    submission_files = MultipleFileField(
        required=False,
        help_text='Upload your solution files'
    )
    
    class Meta:
        model = TaskSubmission
        fields = ['title', 'description', 'submission_type', 'external_url', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Enter submission title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 4,
                'placeholder': 'Describe your approach and solution'
            }),
            'submission_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'external_url': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Enter external URL (GitHub, Drive, etc.)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono',
                'rows': 6,
                'placeholder': 'Additional notes, code snippets, or explanations'
            }),
        }
