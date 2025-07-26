from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Category Name")
    slug = models.SlugField(unique=True, help_text="Unique URL identifier")
    description = models.TextField(blank=True, verbose_name="Category Description")
    image = models.ImageField(upload_to="categories/", verbose_name="Category Image")

    class Meta:
        ordering = ["name"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("products:category_detail", kwargs={"slug": self.slug})

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Product Name")
    slug = models.SlugField(unique=True, help_text="Unique URL identifier")
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="Product Category"
    )
    description = models.TextField(verbose_name="Product Description")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Price"
    )
    stock = models.PositiveIntegerField(verbose_name="Stock Quantity")
    available = models.BooleanField(default=True, verbose_name="Available")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("products:product_detail", kwargs={"slug": self.slug})

    def check_stock(self):
        return self.stock > 0

    def update_stock(self, quantity):
        if quantity > self.stock:
            raise ValidationError("Requested quantity exceeds available stock")
        self.stock -= quantity
        self.save()