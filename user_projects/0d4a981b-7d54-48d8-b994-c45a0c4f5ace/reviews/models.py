from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

RATING_CHOICES = [
    (1, '1 Star'),
    (2, '2 Stars'),
    (3, '3 Stars'),
    (4, '4 Stars'),
    (5, '5 Stars'),
]

class Rating(models.Model):
    recipe = models.ForeignKey(
        'recipes.Recipe',
        on_delete=models.CASCADE,
        related_name='ratings',
        verbose_name='Recipe'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipe_ratings',
        verbose_name='User'
    )
    value = models.IntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Rating Value'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )

    class Meta:
        unique_together = ['recipe', 'user']
        verbose_name = 'Rating'
        verbose_name_plural = 'Ratings'

    def __str__(self):
        return f'{self.user.username} rated {self.recipe.title} {self.value} stars'

class Review(models.Model):
    recipe = models.ForeignKey(
        'recipes.Recipe',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Recipe'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipe_reviews',
        verbose_name='User'
    )
    text = models.TextField(
        verbose_name='Review Text',
        help_text='Write your review here'
    )
    images = models.ManyToManyField(
        'ReviewImage',
        related_name='reviews',
        blank=True,
        verbose_name='Review Images'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'

    def __str__(self):
        return f'Review by {self.user.username} for {self.recipe.title}'

class ReviewImage(models.Model):
    image = models.ImageField(
        upload_to='review_images/',
        verbose_name='Image'
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Uploaded At'
    )

    class Meta:
        verbose_name = 'Review Image'
        verbose_name_plural = 'Review Images'

    def __str__(self):
        return f'Review image uploaded at {self.uploaded_at}'