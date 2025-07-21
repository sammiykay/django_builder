from django.db import models
from django.contrib.auth.models import User
from products.models import Product
from decimal import Decimal

class Cart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='User',
        help_text='User who owns this cart'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At',
        help_text='Date and time when cart was created'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At',
        help_text='Date and time when cart was last updated'
    )

    class Meta:
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'
        ordering = ['-created_at']

    def __str__(self):
        return f"Cart {self.id} - {'Guest' if not self.user else self.user.username}"

    def get_total(self):
        return sum(item.get_subtotal() for item in self.cartitem_set.all())

    def get_items_count(self):
        return self.cartitem_set.count()

class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        verbose_name='Cart',
        help_text='Cart this item belongs to'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name='Product',
        help_text='Product in cart'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name='Quantity',
        help_text='Quantity of product'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Price',
        help_text='Price of product at time of adding to cart'
    )

    class Meta:
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity}x {self.product.name} in Cart {self.cart.id}"

    def get_subtotal(self):
        return Decimal(self.quantity) * self.price