from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from products.models import Category, Product
import pytest
from decimal import Decimal

@pytest.mark.django_db
class TestCategory:
    def test_category_creation(self):
        category = Category.objects.create(
            name="Test Category",
            slug="test-category",
            description="Test Description"
        )
        assert category.name == "Test Category"
        assert category.slug == "test-category"
        assert str(category) == "Test Category"

    def test_category_unique_slug(self):
        Category.objects.create(name="Test Category", slug="test-category")
        with pytest.raises(Exception):
            Category.objects.create(name="Test Category", slug="test-category")

@pytest.mark.django_db
class TestProduct:
    @pytest.fixture
    def category(self):
        return Category.objects.create(name="Test Category", slug="test-category")

    @pytest.fixture
    def product(self, category):
        return Product.objects.create(
            category=category,
            name="Test Product",
            slug="test-product",
            price=Decimal("99.99"),
            description="Test Description",
            stock=10
        )

    def test_product_creation(self, product):
        assert product.name == "Test Product"
        assert product.price == Decimal("99.99")
        assert str(product) == "Test Product"

    def test_product_price_validation(self, category):
        with pytest.raises(Exception):
            Product.objects.create(
                category=category,
                name="Invalid Price Product",
                price=Decimal("-10.00"),
                stock=5
            )

@pytest.mark.django_db
class TestViews:
    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def category(self):
        return Category.objects.create(name="Test Category", slug="test-category")

    @pytest.fixture
    def product(self, category):
        return Product.objects.create(
            category=category,
            name="Test Product",
            slug="test-product",
            price=Decimal("99.99"),
            stock=10
        )

    def test_product_list_view(self, client, product):
        url = reverse('product-list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'Test Product' in str(response.content)

    def test_product_detail_view(self, client, product):
        url = reverse('product-detail', kwargs={'slug': product.slug})
        response = client.get(url)
        assert response.status_code == 200
        assert 'Test Product' in str(response.content)

    def test_product_detail_view_404(self, client):
        url = reverse('product-detail', kwargs={'slug': 'nonexistent-product'})
        response = client.get(url)
        assert response.status_code == 404

    def test_product_list_view_empty(self, client):
        url = reverse('product-list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'No products found' in str(response.content)

    def test_product_list_view_filtering(self, client, category, product):
        url = reverse('product-list') + f'?category={category.slug}'
        response = client.get(url)
        assert response.status_code == 200
        assert 'Test Product' in str(response.content)

@pytest.mark.django_db
class TestEdgeCases:
    @pytest.fixture
    def category(self):
        return Category.objects.create(name="Test Category", slug="test-category")

    def test_very_long_product_name(self, category):
        long_name = "x" * 255
        product = Product.objects.create(
            category=category,
            name=long_name,
            slug="test-product",
            price=Decimal("99.99"),
            stock=10
        )
        assert len(product.name) == 255

    def test_max_price(self, category):
        max_price = Decimal("999999.99")
        product = Product.objects.create(
            category=category,
            name="Expensive Product",
            slug="expensive-product",
            price=max_price,
            stock=10
        )
        assert product.price == max_price

    def test_zero_stock(self, category):
        product = Product.objects.create(
            category=category,
            name="Out of Stock Product",
            slug="out-of-stock",
            price=Decimal("99.99"),
            stock=0
        )
        assert product.stock == 0

    def test_special_characters_in_name(self, category):
        product = Product.objects.create(
            category=category,
            name="Product !@#$%^&*()",
            slug="special-chars",
            price=Decimal("99.99"),
            stock=10
        )
        assert "!@#$%^&*()" in product.name