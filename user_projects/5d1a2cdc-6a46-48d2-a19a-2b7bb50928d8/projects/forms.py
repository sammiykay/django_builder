from django import forms
from django.forms import ModelForm
from django.apps import apps

class ProjectForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically get the Team model
        Team = apps.get_model('teams', 'Team')
        self.fields['team'].queryset = Team.objects.all()
    
    class Meta:
        model = apps.get_model('projects', 'Project')
        fields = ['name', 'description', 'team', 'start_date', 'end_date', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }