from django import forms
from django.forms import ModelForm
from .models import Task, TeamMember
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field
from django.utils import timezone


class TeamCreationForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        fields = ['user', 'role', 'projects']
        widgets = {
            'projects': forms.CheckboxSelectMultiple(),  # To allow multiple project selection
        }

    # Custom validation for user (optional, depending on use case)
    def clean_user(self):
        user = self.cleaned_data.get('user')
        if user is None:
            raise forms.ValidationError("User is required.")
        return user
class TaskForm(ModelForm):
    class Meta:
        model = Task
        fields = '__all__'
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        help_texts = {
            'title': 'Enter a clear and concise task title',
            'description': 'Provide detailed information about the task',
            'due_date': 'When does this task need to be completed?',
        }
        labels = {
            'title': 'Task Title',
            'description': 'Task Description',
            'due_date': 'Due Date',
            'completed': 'Task Status',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Task'))
        
        self.helper.layout = Layout(
            Field('title', css_class='form-control'),
            Field('description', css_class='form-control'),
            Field('due_date', css_class='form-control'),
            Field('completed', css_class='form-check-input'),
        )

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 3:
            raise forms.ValidationError("Title must be at least 3 characters long")
        return title

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now():
            raise forms.ValidationError("Due date cannot be in the past")
        return due_date