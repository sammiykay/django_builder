from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from reviews.models import Rating, Review
import pytest

User = get_user_model()

@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

@pytest.fixture
def rating(user):
    return Rating.objects.create(
        user=user,
        score=5,
        target_type='product',
        target_id=1
    )

@pytest.fixture
def review(user):
    return Review.objects.create(
        user=user,
        title='Test Review',
        content='This is a test review content',
        target_type='product',
        target_id=1
    )

@pytest.mark.django_db
class TestRatingModel:
    def test_rating_creation(self, rating):
        assert rating.score == 5
        assert rating.target_type == 'product'
        assert rating.target_id == 1

    def test_rating_str_representation(self, rating):
        expected_str = f"Rating {rating.score} by {rating.user.username}"
        assert str(rating) == expected_str

    def test_invalid_score(self, user):
        with pytest.raises(ValidationError):
            rating = Rating.objects.create(
                user=user,
                score=6,  # Invalid score > 5
                target_type='product',
                target_id=1
            )
            rating.full_clean()

    def test_negative_score(self, user):
        with pytest.raises(ValidationError):
            rating = Rating.objects.create(
                user=user,
                score=-1,  # Invalid negative score
                target_type='product',
                target_id=1
            )
            rating.full_clean()

@pytest.mark.django_db
class TestReviewModel:
    def test_review_creation(self, review):
        assert review.title == 'Test Review'
        assert review.content == 'This is a test review content'
        assert review.target_type == 'product'
        assert review.target_id == 1

    def test_review_str_representation(self, review):
        expected_str = f"Review: {review.title} by {review.user.username}"
        assert str(review) == expected_str

    def test_review_title_max_length(self, user):
        with pytest.raises(ValidationError):
            review = Review.objects.create(
                user=user,
                title='A' * 201,  # Exceeds max length
                content='Test content',
                target_type='product',
                target_id=1
            )
            review.full_clean()

    def test_review_content_required(self, user):
        with pytest.raises(ValidationError):
            review = Review.objects.create(
                user=user,
                title='Test Title',
                content='',  # Empty content
                target_type='product',
                target_id=1
            )
            review.full_clean()

    def test_review_update(self, review):
        review.title = 'Updated Title'
        review.save()
        updated_review = Review.objects.get(id=review.id)
        assert updated_review.title == 'Updated Title'

    def test_review_deletion(self, review):
        review_id = review.id
        review.delete()
        with pytest.raises(Review.DoesNotExist):
            Review.objects.get(id=review_id)

@pytest.mark.django_db
class TestModelRelationships:
    def test_user_reviews(self, user, review):
        assert user.reviews.first() == review

    def test_user_ratings(self, user, rating):
        assert user.ratings.first() == rating

    def test_multiple_reviews_per_user(self, user):
        Review.objects.create(
            user=user,
            title='First Review',
            content='Content 1',
            target_type='product',
            target_id=1
        )
        Review.objects.create(
            user=user,
            title='Second Review',
            content='Content 2',
            target_type='product',
            target_id=2
        )
        assert user.reviews.count() == 2

    def test_multiple_ratings_per_user(self, user):
        Rating.objects.create(
            user=user,
            score=4,
            target_type='product',
            target_id=1
        )
        Rating.objects.create(
            user=user,
            score=5,
            target_type='product',
            target_id=2
        )
        assert user.ratings.count() == 2

@pytest.mark.django_db
class TestModelValidation:
    def test_invalid_target_type(self, user):
        with pytest.raises(ValidationError):
            review = Review.objects.create(
                user=user,
                title='Test Review',
                content='Content',
                target_type='invalid_type',
                target_id=1
            )
            review.full_clean()

    def test_negative_target_id(self, user):
        with pytest.raises(ValidationError):
            rating = Rating.objects.create(
                user=user,
                score=5,
                target_type='product',
                target_id=-1
            )
            rating.full_clean()