from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Rating, Review
from .forms import ReviewForm, RatingForm

def index(request):
    latest_reviews = Review.objects.select_related('recipe', 'user').order_by('-created_at')[:5]
    top_rated = Rating.objects.select_related('recipe').values('recipe').annotate(avg_rating=Avg('value')).order_by('-avg_rating')[:5]
    
    context = {
        'latest_reviews': latest_reviews,
        'top_rated': top_rated,
    }
    return render(request, 'reviews/index.html', context)

class ReviewListView(ListView):
    model = Review
    template_name = 'reviews/review_list.html'
    context_object_name = 'reviews'
    paginate_by = 10
    ordering = ['-created_at']

@login_required
def add_review(request, recipe_id):
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.recipe_id = recipe_id
            review.save()
            messages.success(request, 'Review added successfully!')
            return redirect('recipe_detail', pk=recipe_id)
    else:
        form = ReviewForm()
    
    return render(request, 'reviews/add_review.html', {'form': form})

@login_required
def add_rating(request, recipe_id):
    if request.method == 'POST' and request.is_ajax():
        rating_value = request.POST.get('rating')
        try:
            rating, created = Rating.objects.update_or_create(
                user=request.user,
                recipe_id=recipe_id,
                defaults={'value': rating_value}
            )
            return JsonResponse({'success': True, 'rating': rating_value})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

class ReviewUpdateView(LoginRequiredMixin, UpdateView):
    model = Review
    form_class = ReviewForm
    template_name = 'reviews/edit_review.html'
    
    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('recipe_detail', kwargs={'pk': self.object.recipe.pk})

class ReviewDeleteView(LoginRequiredMixin, DeleteView):
    model = Review
    template_name = 'reviews/review_confirm_delete.html'
    
    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('recipe_detail', kwargs={'pk': self.object.recipe.pk})

@login_required
def delete_rating(request, recipe_id):
    if request.method == 'POST' and request.is_ajax():
        try:
            Rating.objects.filter(user=request.user, recipe_id=recipe_id).delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def get_recipe_ratings(request, recipe_id):
    ratings = Rating.objects.filter(recipe_id=recipe_id)
    avg_rating = ratings.aggregate(Avg('value'))['value__avg'] or 0
    rating_count = ratings.count()
    
    return JsonResponse({
        'average_rating': round(avg_rating, 1),
        'rating_count': rating_count
    })