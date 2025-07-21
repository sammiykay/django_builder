from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Cart, CartItem
from products.models import Product
import pytest

User = get_user_model()

@pytest.mark.django_db
class TestCartModel:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def cart(self, user):
        return Cart.objects.create(user=user)

    @pytest.fixture
    def product(self):
        return Product.objects.create(
            name='Test Product',
            price=10.00,
            description='Test Description'
        )

    def test_cart_creation(self, user):
        cart = Cart.objects.create(user=user)
        assert isinstance(cart, Cart)
        assert str(cart) == f"Cart for {user.username}"
        assert cart.user == user

    def test_cart_total(self, cart, product):
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=2
        )
        assert cart.total == 20.00

    def test_cart_item_count(self, cart, product):
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=3
        )
        assert cart.item_count == 3

@pytest.mark.django_db
class TestCartItemModel:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def cart(self, user):
        return Cart.objects.create(user=user)

    @pytest.fixture
    def product(self):
        return Product.objects.create(
            name='Test Product',
            price=10.00,
            description='Test Description'
        )

    def test_cart_item_creation(self, cart, product):
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=1
        )
        assert isinstance(cart_item, CartItem)
        assert str(cart_item) == f"{product.name} (Qty: 1)"
        assert cart_item.cart == cart
        assert cart_item.product == product

    def test_cart_item_subtotal(self, cart, product):
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=3
        )
        assert cart_item.subtotal == 30.00

    def test_negative_quantity(self, cart, product):
        with pytest.raises(ValueError):
            CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=-1
            )

    def test_zero_quantity(self, cart, product):
        with pytest.raises(ValueError):
            CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=0
            )

    def test_cart_item_update_quantity(self, cart, product):
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=1
        )
        cart_item.quantity = 5
        cart_item.save()
        assert cart_item.quantity == 5
        assert cart_item.subtotal == 50.00

    def test_cart_item_max_quantity(self, cart, product):
        with pytest.raises(ValueError):
            CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=1001
            )

@pytest.mark.django_db
class TestCartOperations:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def cart(self, user):
        return Cart.objects.create(user=user)

    @pytest.fixture
    def products(self):
        return [
            Product.objects.create(
                name=f'Product {i}',
                price=10.00 * i,
                description=f'Description {i}'
            ) for i in range(1, 4)
        ]

    def test_add_multiple_items(self, cart, products):
        for i, product in enumerate(products, 1):
            CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=i
            )
        assert cart.item_count == 6  # 1 + 2 + 3
        assert cart.total == 140.00  # (10 * 1) + (20 * 2) + (30 * 3)

    def test_clear_cart(self, cart, products):
        for product in products:
            CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=1
            )
        cart.items.all().delete()
        assert cart.item_count == 0
        assert cart.total == 0

    def test_duplicate_product(self, cart, product):
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=1
        )
        with pytest.raises(Exception):
            CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=1
            )