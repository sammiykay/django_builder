from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify

DIFFICULTY_CHOICES = [
    ('easy', 'Easy'),
    ('medium', 'Medium'),
    ('hard', 'Hard'),
]

class Recipe(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    prep_time = models.IntegerField(help_text="Preparation time in minutes")
    cook_time = models.IntegerField(help_text="Cooking time in minutes")
    servings = models.IntegerField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    image = models.ImageField(upload_to='recipes/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('recipe_detail', kwargs={'slug': self.slug})

    def calculate_average_rating(self):
        ratings = self.review_set.values_list('rating', flat=True)
        if ratings:
            self.average_rating = sum(ratings) / len(ratings)
            self.save()
        return self.average_rating

    def generate_shopping_list(self):
        return self.ingredient_set.all()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

class Ingredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=6, decimal_places=2)
    unit = models.CharField(max_length=50)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['recipe', 'name']
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'

    def __str__(self):
        return f"{self.quantity} {self.unit} {self.name}"

class Instruction(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    step_number = models.IntegerField()
    description = models.TextField()
    time_required = models.IntegerField(null=True, blank=True, help_text="Time required in minutes")

    class Meta:
        ordering = ['recipe', 'step_number']
        verbose_name = 'Instruction'
        verbose_name_plural = 'Instructions'

    def __str__(self):
        return f"Step {self.step_number} for {self.recipe.title}"