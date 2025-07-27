from django.db import models
from django.urls import reverse
from ckeditor.fields import RichTextField

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Category Name")
    slug = models.SlugField(unique=True, help_text="Unique URL identifier")
    description = models.TextField(blank=True, verbose_name="Category Description")
    image = models.ImageField(upload_to='categories/', verbose_name="Category Image")

    class Meta:
        ordering = ['name']
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('products:category_detail', args=[self.slug])

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Product Name")
    slug = models.SlugField(unique=True, help_text="Unique URL identifier")
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name="Product Category"
    )
    description = RichTextField(verbose_name="Product Description")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Price"
    )
    stock = models.PositiveIntegerField(verbose_name="Stock Quantity")
    available = models.BooleanField(default=True, verbose_name="Available")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('products:product_detail', args=[self.category.slug, self.slug])

    def check_stock(self):
        return self.stock > 0

    def apply_discount(self, percentage):
        if not 0 <= percentage <= 100:
            raise ValueError("Discount percentage must be between 0 and 100")
        discount = (percentage / 100) * self.price
        return self.price - discount