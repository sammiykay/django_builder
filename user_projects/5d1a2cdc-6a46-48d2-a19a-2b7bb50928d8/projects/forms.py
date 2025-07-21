from django import forms
from django.forms import ModelForm
from .models import Project
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
        help_texts = {
            'title': 'Enter the project title',
            'description': 'Provide a detailed description of the project',
            'start_date': 'Select the project start date',
            'end_date': 'Select the expected completion date',
        }
        labels = {
            'title': 'Project Title',
            'description': 'Project Description',
            'start_date': 'Start Date',
            'end_date': 'End Date',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Project'))

        # Lazy import of the related Team model to avoid circular import
        from tasks.models import TeamMember
        self.fields['team'].queryset = TeamMember.objects.all()  # Ensure the field is populated with Team instances

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError("End date cannot be before start date")
        
        return cleaned_data
