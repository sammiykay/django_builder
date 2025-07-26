from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from .models import Dashboard, Widget

class DashboardForm(forms.ModelForm):
    class Meta:
        model = Dashboard
        fields = '__all__'
        help_texts = {
            'title': 'Enter a descriptive title for your dashboard',
            'description': 'Provide a brief description of the dashboard purpose',
        }
        labels = {
            'title': 'Dashboard Title',
            'description': 'Dashboard Description',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Dashboard'))
        
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 3:
            raise ValidationError('Title must be at least 3 characters long')
        return title

class WidgetForm(forms.ModelForm):
    class Meta:
        model = Widget
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        help_texts = {
            'title': 'Enter a name for this widget',
            'widget_type': 'Select the type of widget',
            'position': 'Widget position on the dashboard',
        }
        labels = {
            'title': 'Widget Title',
            'widget_type': 'Widget Type',
            'position': 'Position',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('title', css_class='form-group col-md-6'),
                Column('widget_type', css_class='form-group col-md-6'),
            ),
            'description',
            'position',
            'dashboard',
            Submit('submit', 'Save Widget', css_class='btn btn-primary')
        )

    def clean(self):
        cleaned_data = super().clean()
        widget_type = cleaned_data.get('widget_type')
        position = cleaned_data.get('position')
        
        if widget_type and position:
            # Add any custom validation logic here
            pass
        
        return cleaned_data