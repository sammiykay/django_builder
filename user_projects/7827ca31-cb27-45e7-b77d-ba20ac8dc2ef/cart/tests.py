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
    def product(self):
        return Product.objects.create(
            name='Test Product',
            price=10.00,
            description='Test Description'
        )

    @pytest.fixture
    def cart(self, user):
        return Cart.objects.create(user=user)

    def test_cart_creation(self, user):
        cart = Cart.objects.create(user=user)
        assert cart.user == user
        assert str(cart) == f"Cart for {user.username}"

    def test_cart_item_creation(self, cart, product):
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=2
        )
        assert cart_item.cart == cart
        assert cart_item.product == product
        assert cart_item.quantity == 2

    def test_cart_total(self, cart, product):
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=2
        )
        assert cart.get_total() == 20.00

    def test_cart_item_update_quantity(self, cart, product):
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=1
        )
        cart_item.quantity = 3
        cart_item.save()
        assert cart_item.quantity == 3

    def test_cart_item_negative_quantity(self, cart, product):
        with pytest.raises(ValueError):
            CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=-1
            )

    def test_cart_empty(self, cart):
        assert cart.is_empty()

    def test_cart_item_count(self, cart, product):
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=2
        )
        assert cart.get_item_count() == 1

    def test_cart_total_quantity(self, cart, product):
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=2
        )
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=3
        )
        assert cart.get_total_quantity() == 5

    def test_cart_clear(self, cart, product):
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=2
        )
        cart.clear()
        assert cart.is_empty()

    def test_cart_item_str(self, cart, product):
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=2
        )
        assert str(cart_item) == f"{product.name} (2)"

@pytest.mark.django_db
class TestCartEdgeCases:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def product(self):
        return Product.objects.create(
            name='Test Product',
            price=10.00,
            description='Test Description'
        )

    def test_multiple_carts_per_user(self, user):
        cart1 = Cart.objects.create(user=user)
        cart2 = Cart.objects.create(user=user)
        assert Cart.objects.filter(user=user).count() == 2

    def test_cart_with_zero_quantity_items(self, user, product):
        cart = Cart.objects.create(user=user)
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=0
        )
        assert cart.get_total() == 0
        assert cart.get_total_quantity() == 0

    def test_cart_with_max_quantity(self, user, product):
        cart = Cart.objects.create(user=user)
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=999999
        )
        assert cart.get_total() == product.price * 999999

    def test_delete_product_cascade(self, user, product):
        cart = Cart.objects.create(user=user)
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=1
        )
        product.delete()
        assert CartItem.objects.filter(id=cart_item.id).count() == 0

    def test_delete_cart_cascade(self, user, product):
        cart = Cart.objects.create(user=user)
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=1
        )
        cart.delete()
        assert CartItem.objects.filter(id=cart_item.id).count() == 0