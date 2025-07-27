from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.db.models import Q, Avg
from django.forms import inlineformset_factory
from .models import Recipe, Ingredient, Instruction
from .forms import RecipeForm, IngredientForm, InstructionForm

class RecipeListView(ListView):
    model = Recipe
    template_name = 'recipes/recipe_list.html'
    context_object_name = 'recipes'
    paginate_by = 12

    def get_queryset(self):
        queryset = Recipe.objects.all()
        category = self.request.GET.get('category')
        tag = self.request.GET.get('tag')
        search = self.request.GET.get('search')

        if category:
            queryset = queryset.filter(category=category)
        if tag:
            queryset = queryset.filter(tags__name=tag)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Recipe.objects.values_list('category', flat=True).distinct()
        context['tags'] = Recipe.objects.values_list('tags__name', flat=True).distinct()
        context['featured_recipes'] = Recipe.objects.filter(is_featured=True)[:4]
        return context

class RecipeDetailView(DetailView):
    model = Recipe
    template_name = 'recipes/recipe_detail.html'
    context_object_name = 'recipe'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipe = self.get_object()
        context['reviews'] = recipe.review_set.all().order_by('-created_at')
        context['similar_recipes'] = Recipe.objects.filter(
            category=recipe.category
        ).exclude(id=recipe.id)[:3]
        
        if self.request.user.is_authenticated:
            context['user_rating'] = recipe.review_set.filter(
                user=self.request.user
            ).first()
        
        context['average_rating'] = recipe.review_set.aggregate(
            Avg('rating')
        )['rating__avg']
        return context

class RecipeCreateView(LoginRequiredMixin, CreateView):
    model = Recipe
    form_class = RecipeForm
    template_name = 'recipes/recipe_form.html'
    success_url = reverse_lazy('recipes:recipe_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['ingredient_formset'] = IngredientFormSet(
                self.request.POST, instance=self.object
            )
            context['instruction_formset'] = InstructionFormSet(
                self.request.POST, instance=self.object
            )
        else:
            context['ingredient_formset'] = IngredientFormSet(instance=self.object)
            context['instruction_formset'] = InstructionFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        ingredient_formset = context['ingredient_formset']
        instruction_formset = context['instruction_formset']
        form.instance.author = self.request.user

        if ingredient_formset.is_valid() and instruction_formset.is_valid():
            self.object = form.save()
            ingredient_formset.instance = self.object
            instruction_formset.instance = self.object
            ingredient_formset.save()
            instruction_formset.save()
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))

# Formsets for ingredients and instructions
IngredientFormSet = inlineformset_factory(
    Recipe,
    Ingredient,
    form=IngredientForm,
    extra=3,
    can_delete=True
)

InstructionFormSet = inlineformset_factory(
    Recipe,
    Instruction,
    form=InstructionForm,
    extra=3,
    can_delete=True
)