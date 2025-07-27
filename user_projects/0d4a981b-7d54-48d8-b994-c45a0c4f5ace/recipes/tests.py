import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from recipes.models import Recipe, Ingredient, Instruction
from recipes.forms import RecipeForm
from django.core.exceptions import ValidationError

User = get_user_model()

@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

@pytest.fixture
def recipe(user):
    recipe = Recipe.objects.create(
        title='Test Recipe',
        description='Test Description',
        cooking_time=30,
        author=user
    )
    return recipe

@pytest.fixture
def ingredient(recipe):
    return Ingredient.objects.create(
        recipe=recipe,
        name='Test Ingredient',
        quantity='1',
        unit='cup'
    )

@pytest.fixture
def instruction(recipe):
    return Instruction.objects.create(
        recipe=recipe,
        step_number=1,
        description='Test instruction step'
    )

class TestModels:
    def test_recipe_creation(self, recipe):
        assert recipe.title == 'Test Recipe'
        assert str(recipe) == 'Test Recipe'

    def test_ingredient_creation(self, ingredient):
        assert str(ingredient) == '1 cup Test Ingredient'

    def test_instruction_creation(self, instruction):
        assert str(instruction) == '1. Test instruction step'

    def test_recipe_validation(self):
        with pytest.raises(ValidationError):
            Recipe.objects.create(
                title='',
                description='Test',
                cooking_time=-1
            )

class TestViews:
    @pytest.fixture
    def client(self):
        return Client()

    def test_recipe_list_view(self, client, recipe):
        url = reverse('recipe-list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'Test Recipe' in str(response.content)

    def test_recipe_detail_view(self, client, recipe):
        url = reverse('recipe-detail', args=[recipe.id])
        response = client.get(url)
        assert response.status_code == 200
        assert recipe.title in str(response.content)

    def test_recipe_create_view(self, client, user):
        client.force_login(user)
        url = reverse('recipe-create')
        data = {
            'title': 'New Recipe',
            'description': 'New Description',
            'cooking_time': 45,
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert Recipe.objects.filter(title='New Recipe').exists()

    def test_recipe_create_view_unauthorized(self, client):
        url = reverse('recipe-create')
        response = client.get(url)
        assert response.status_code == 302  # Redirects to login

class TestForms:
    def test_recipe_form_valid(self):
        form_data = {
            'title': 'Test Recipe',
            'description': 'Test Description',
            'cooking_time': 30,
        }
        form = RecipeForm(data=form_data)
        assert form.is_valid()

    def test_recipe_form_invalid(self):
        form_data = {
            'title': '',  # Title is required
            'description': 'Test Description',
            'cooking_time': -30,  # Negative time is invalid
        }
        form = RecipeForm(data=form_data)
        assert not form.is_valid()

class TestEdgeCases:
    def test_very_long_title(self, user):
        long_title = 'x' * 300
        recipe = Recipe.objects.create(
            title=long_title,
            description='Test',
            cooking_time=30,
            author=user
        )
        assert len(recipe.title) <= 255

    def test_zero_cooking_time(self, user):
        recipe = Recipe.objects.create(
            title='Test Recipe',
            description='Test',
            cooking_time=0,
            author=user
        )
        assert recipe.cooking_time == 0

    def test_unicode_characters(self, user):
        recipe = Recipe.objects.create(
            title='测试食谱',
            description='测试描述',
            cooking_time=30,
            author=user
        )
        assert Recipe.objects.filter(title='测试食谱').exists()

    def test_special_characters(self, user):
        recipe = Recipe.objects.create(
            title='Recipe!@#$%^&*()',
            description='Test',
            cooking_time=30,
            author=user
        )
        assert Recipe.objects.filter(title='Recipe!@#$%^&*()').exists()

    def test_duplicate_recipe_titles(self, user):
        Recipe.objects.create(
            title='Duplicate Recipe',
            description='Test 1',
            cooking_time=30,
            author=user
        )
        Recipe.objects.create(
            title='Duplicate Recipe',
            description='Test 2',
            cooking_time=45,
            author=user
        )
        assert Recipe.objects.filter(title='Duplicate Recipe').count() == 2