from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field
from .models import MetricSnapshot

class MetricSnapshotForm(forms.ModelForm):
    class Meta:
        model = MetricSnapshot
        fields = '__all__'
        help_texts = {
            'timestamp': 'Date and time when the metric was recorded',
            'metric_name': 'Name of the metric being tracked',
            'value': 'Numerical value of the metric',
        }
        labels = {
            'metric_name': 'Metric Name',
            'value': 'Metric Value',
            'timestamp': 'Recorded At',
        }
        widgets = {
            'timestamp': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'value': forms.NumberInput(attrs={'step': 'any'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))
        self.helper.layout = Layout(
            Field('metric_name', css_class='form-control'),
            Field('value', css_class='form-control'),
            Field('timestamp', css_class='form-control'),
        )

    def clean_value(self):
        value = self.cleaned_data.get('value')
        if value is not None and value < 0:
            raise forms.ValidationError("Metric value cannot be negative")
        return value

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data