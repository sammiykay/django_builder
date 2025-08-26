from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field
from .models import Project, Requirement

class RequirementsUploadForm(forms.Form):
    requirements_file = forms.FileField(
        widget=forms.FileInput(attrs={'accept': '.txt,.pip,.req'}),
        label='Requirements File',
        help_text='Upload a requirements.txt file'
    )
    project_name = forms.CharField(
        max_length=100,
        label='Project Name',
        help_text='Enter a name for your project'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Upload Requirements'))
        self.helper.layout = Layout(
            Field('project_name'),
            Field('requirements_file'),
        )

    def clean_requirements_file(self):
        file = self.cleaned_data.get('requirements_file')
        if file:
            if not file.name.endswith(('.txt', '.pip', '.req')):
                raise ValidationError('Invalid file type. Please upload a requirements text file.')
        return file

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Project'))

class RequirementForm(forms.ModelForm):
    class Meta:
        model = Requirement
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Requirement'))