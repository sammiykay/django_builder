import pytest
from django.test import TestCase, Client
from django.urls import reverse
from products.models import Category, Product
from django.contrib.auth.models import User
from decimal import Decimal

@pytest.fixture
def category():
    return Category.objects.create(
        name='Test Category',
        slug='test-category',
        description='Test category description'
    )

@pytest.fixture
def product(category):
    return Product.objects.create(
        name='Test Product',
        slug='test-product',
        category=category,
        description='Test product description',
        price=Decimal('99.99'),
        stock=10,
        available=True
    )

@pytest.fixture
def client():
    return Client()

class TestCategoryModel:
    def test_category_creation(self, category):
        assert category.name == 'Test Category'
        assert category.slug == 'test-category'
        assert str(category) == 'Test Category'

    def test_category_slug_unique(self, db):
        Category.objects.create(name='Category 1', slug='category-1')
        with pytest.raises(Exception):
            Category.objects.create(name='Category 1', slug='category-1')

class TestProductModel:
    def test_product_creation(self, product, category):
        assert product.name == 'Test Product'
        assert product.category == category
        assert product.price == Decimal('99.99')
        assert str(product) == 'Test Product'

    def test_product_price_validation(self, category):
        with pytest.raises(Exception):
            Product.objects.create(
                name='Invalid Price Product',
                category=category,
                price=Decimal('-10.00')
            )

    def test_product_stock_validation(self, category):
        with pytest.raises(Exception):
            Product.objects.create(
                name='Invalid Stock Product',
                category=category,
                price=Decimal('10.00'),
                stock=-1
            )

class TestProductListView:
    def test_product_list_view(self, client, product):
        url = reverse('product-list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'Test Product' in str(response.content)

    def test_product_list_view_empty(self, client):
        url = reverse('product-list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'No products available' in str(response.content)

    def test_product_list_view_filtering(self, client, product, category):
        url = reverse('product-list') + f'?category={category.slug}'
        response = client.get(url)
        assert response.status_code == 200
        assert 'Test Product' in str(response.content)

class TestProductDetailView:
    def test_product_detail_view(self, client, product):
        url = reverse('product-detail', kwargs={'slug': product.slug})
        response = client.get(url)
        assert response.status_code == 200
        assert product.name in str(response.content)
        assert str(product.price) in str(response.content)

    def test_product_detail_view_404(self, client):
        url = reverse('product-detail', kwargs={'slug': 'nonexistent-product'})
        response = client.get(url)
        assert response.status_code == 404

    def test_product_detail_view_unavailable(self, client, product):
        product.available = False
        product.save()
        url = reverse('product-detail', kwargs={'slug': product.slug})
        response = client.get(url)
        assert response.status_code == 404

@pytest.mark.parametrize(
    'name,slug,price,stock,expected_valid',
    [
        ('Valid Product', 'valid-product', Decimal('10.00'), 5, True),
        ('', 'valid-product', Decimal('10.00'), 5, False),
        ('Valid Product', '', Decimal('10.00'), 5, False),
        ('Valid Product', 'valid-product', Decimal('-10.00'), 5, False),
        ('Valid Product', 'valid-product', Decimal('10.00'), -1, False),
    ]
)
def test_product_validation(name, slug, price, stock, expected_valid, category):
    try:
        product = Product.objects.create(
            name=name,
            slug=slug,
            category=category,
            price=price,
            stock=stock
        )
        assert expected_valid
    except:
        assert not expected_valid

def test_category_absolute_url(category):
    expected_url = reverse('product-list') + f'?category={category.slug}'
    assert category.get_absolute_url() == expected_url

def test_product_absolute_url(product):
    expected_url = reverse('product-detail', kwargs={'slug': product.slug})
    assert product.get_absolute_url() == expected_url