from django import forms
from .models import Post, Comment
from tinymce.widgets import TinyMCE
from django.utils import timezone

class PostForm(forms.ModelForm):
    title = forms.CharField(
        max_length=200,
        help_text='Enter the title of your post',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    content = forms.CharField(
        widget=TinyMCE(attrs={'cols': 80, 'rows': 30}),
        help_text='Write your post content here'
    )
    featured_image = forms.ImageField(
        required=False,
        help_text='Upload a featured image for your post',
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    excerpt = forms.CharField(
        max_length=200,
        help_text='Write a brief summary of your post',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    status = forms.ChoiceField(
        choices=[('draft', 'Draft'), ('published', 'Published')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    publish_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        initial=timezone.now
    )

    class Meta:
        model = Post
        fields = ['title', 'content', 'featured_image', 'excerpt', 'status', 'publish_date']

    def clean_publish_date(self):
        date = self.cleaned_data['publish_date']
        if date < timezone.now():
            raise forms.ValidationError("Publication date cannot be in the past")
        return date

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = '__all__'
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'author': forms.TextInput(attrs={'class': 'form-control'})
        }
        help_texts = {
            'content': 'Write your comment here',
            'author': 'Enter your name'
        }