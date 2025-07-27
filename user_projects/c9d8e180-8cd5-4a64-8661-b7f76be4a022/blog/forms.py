from django import forms
from .models import Post, Comment
from ckeditor.widgets import CKEditorWidget
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field

class PostForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorWidget())
    
    class Meta:
        model = Post
        fields = ['title', 'content', 'featured_image', 'status', 'tags']
        labels = {
            'title': 'Post Title',
            'content': 'Post Content',
            'featured_image': 'Featured Image',
            'status': 'Publication Status',
            'tags': 'Post Tags'
        }
        help_texts = {
            'title': 'Enter a descriptive title for your post',
            'content': 'Write your post content here',
            'featured_image': 'Upload an image to be displayed with your post',
            'status': 'Select whether to publish or save as draft',
            'tags': 'Add relevant tags (comma separated)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Post'))
        
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 5:
            raise forms.ValidationError("Title must be at least 5 characters long")
        return title

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = '__all__'
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit Comment'))