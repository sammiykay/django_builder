from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field
from .models import Rating, Review

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = '__all__'
        widgets = {
            'score': forms.NumberInput(attrs={'min': 1, 'max': 5}),
        }
        help_texts = {
            'score': 'Rate from 1 to 5 stars',
        }
        labels = {
            'score': 'Rating Score',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit Rating'))

    def clean_score(self):
        score = self.cleaned_data.get('score')
        if score < 1 or score > 5:
            raise forms.ValidationError('Rating must be between 1 and 5')
        return score

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = '__all__'
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Write your review here...'}),
        }
        help_texts = {
            'content': 'Please provide your detailed review',
            'title': 'Give your review a title',
        }
        labels = {
            'content': 'Review Content',
            'title': 'Review Title',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit Review'))

    def clean_content(self):
        content = self.cleaned_data.get('content')
        if len(content) < 10:
            raise forms.ValidationError('Review content must be at least 10 characters long')
        return content