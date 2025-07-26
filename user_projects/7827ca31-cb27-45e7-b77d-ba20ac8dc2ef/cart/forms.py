from django import forms
from .models import Cart, CartItem
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

class CartForm(forms.ModelForm):
    class Meta:
        model = Cart
        fields = '__all__'
        help_texts = {
            'user': 'Select the user who owns this cart',
            'created_at': 'Date and time when the cart was created',
            'updated_at': 'Date and time when the cart was last updated',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Cart'))

class CartItemForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = '__all__'
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': 1}),
        }
        help_texts = {
            'cart': 'Select the cart this item belongs to',
            'product': 'Select the product',
            'quantity': 'Enter the quantity (minimum 1)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Cart Item'))

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity < 1:
            raise forms.ValidationError("Quantity must be at least 1")
        return quantity

    def clean(self):
        cleaned_data = super().clean()
        cart = cleaned_data.get('cart')
        product = cleaned_data.get('product')
        
        if cart and product:
            # Check if the same product already exists in the cart
            existing_item = CartItem.objects.filter(cart=cart, product=product).exclude(pk=self.instance.pk if self.instance else None).first()
            if existing_item:
                raise forms.ValidationError("This product is already in the cart")
        
        return cleaned_data