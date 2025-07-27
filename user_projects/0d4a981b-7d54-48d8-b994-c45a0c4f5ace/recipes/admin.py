from django.contrib import admin
from .models import Recipe, Ingredient, Instruction

class IngredientInline(admin.TabularInline):
    model = Ingredient
    extra = 1

class InstructionInline(admin.TabularInline):
    model = Instruction
    extra = 1

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at', 'cooking_time', 'difficulty_level')
    list_filter = ('difficulty_level', 'created_at', 'cooking_time')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [IngredientInline, InstructionInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'image')
        }),
        ('Cooking Details', {
            'fields': ('cooking_time', 'difficulty_level', 'servings')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_featured']
    
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)
    mark_as_featured.short_description = "Mark selected recipes as featured"

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'unit', 'recipe')
    list_filter = ('unit', 'recipe')
    search_fields = ('name', 'recipe__title')

@admin.register(Instruction)
class InstructionAdmin(admin.ModelAdmin):
    list_display = ('step_number', 'description', 'recipe')
    list_filter = ('recipe',)
    search_fields = ('description', 'recipe__title')
    ordering = ('step_number',)