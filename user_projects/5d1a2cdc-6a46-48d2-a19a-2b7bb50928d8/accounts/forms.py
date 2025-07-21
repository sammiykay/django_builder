from django import forms
from django.contrib.auth.forms import UserCreationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from .models import TeamMember, Team

class TeamMemberForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        fields = '__all__'
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'date_joined': forms.DateInput(attrs={'type': 'date'}),
        }
        help_texts = {
            'bio': 'Brief description about the team member',
            'role': 'Position within the team',
        }
        labels = {
            'date_joined': 'Join Date',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and TeamMember.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError('This email is already in use.')
        return email

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'created_date': forms.DateInput(attrs={'type': 'date'}),
        }
        help_texts = {
            'name': 'Name of the team',
            'description': 'Brief description of the team and its purpose',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6'),
                Column('created_date', css_class='form-group col-md-6'),
            ),
            'description',
            'members',
            Submit('submit', 'Save Team')
        )

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and Team.objects.filter(name=name).exclude(id=self.instance.id).exists():
            raise forms.ValidationError('A team with this name already exists.')
        return name