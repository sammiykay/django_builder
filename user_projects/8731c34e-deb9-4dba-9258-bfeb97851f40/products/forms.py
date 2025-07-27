from django import forms
from .models import Category, Product
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'
        help_texts = {
            'name': 'Enter the category name',
            'description': 'Provide a brief description of the category',
        }
        labels = {
            'name': 'Category Name',
            'description': 'Description',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Category'))
        
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 2:
            raise forms.ValidationError("Category name must be at least 2 characters long")
        return name

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'price': forms.NumberInput(attrs={'step': '0.01'}),
        }
        help_texts = {
            'name': 'Enter the product name',
            'description': 'Provide a detailed description of the product',
            'price': 'Enter the price in decimal format (e.g., 99.99)',
            'category': 'Select the product category',
        }
        labels = {
            'name': 'Product Name',
            'description': 'Description',
            'price': 'Price',
            'category': 'Category',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6'),
                Column('category', css_class='form-group col-md-6'),
            ),
            'description',
            'price',
            Submit('submit', 'Save Product', css_class='btn btn-primary')
        )

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise forms.ValidationError("Price must be greater than zero")
        return price

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 3:
            raise forms.ValidationError("Product name must be at least 3 characters long")
        return name