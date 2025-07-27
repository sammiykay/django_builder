from django import forms
from .models import Recipe, Ingredient, Instruction
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = '__all__'
        help_texts = {
            'title': 'Enter the name of your recipe',
            'description': 'Provide a brief description of your recipe',
            'cooking_time': 'Enter cooking time in minutes',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Recipe'))

    def clean_cooking_time(self):
        cooking_time = self.cleaned_data.get('cooking_time')
        if cooking_time and cooking_time < 0:
            raise forms.ValidationError("Cooking time cannot be negative")
        return cooking_time

class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = '__all__'
        help_texts = {
            'name': 'Enter ingredient name',
            'quantity': 'Enter the amount needed',
            'unit': 'Specify the unit of measurement',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Add Ingredient'))

class InstructionForm(forms.ModelForm):
    class Meta:
        model = Instruction
        fields = '__all__'
        help_texts = {
            'step_number': 'Enter the step number',
            'description': 'Describe this step of the recipe',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Add Instruction'))

    def clean_step_number(self):
        step_number = self.cleaned_data.get('step_number')
        if step_number and step_number < 1:
            raise forms.ValidationError("Step number must be positive")
        return step_number