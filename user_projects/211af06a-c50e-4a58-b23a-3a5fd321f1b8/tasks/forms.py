from django import forms
from .models import Task, TaskList
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'priority', 'status']
        widgets = {
            'due_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'description': forms.Textarea(
                attrs={'rows': 4, 'class': 'form-control'}
            ),
        }
        help_texts = {
            'title': 'Enter a clear and concise title for your task',
            'due_date': 'Select the deadline for this task',
            'priority': 'Set the importance level of this task',
        }
        labels = {
            'title': 'Task Title',
            'description': 'Task Description',
            'due_date': 'Due Date',
            'priority': 'Priority Level',
            'status': 'Current Status',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Task'))
        
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now():
            raise forms.ValidationError("Due date cannot be in the past")
        return due_date

class TaskListForm(forms.ModelForm):
    class Meta:
        model = TaskList
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'name': 'Enter a name for your task list',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Task List'))