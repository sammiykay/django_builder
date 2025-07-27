from django.contrib import admin
from .models import Rating, Review

class RatingInline(admin.TabularInline):
    model = Rating
    extra = 1
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'score', 'created_at')
    list_filter = ('score', 'created_at')
    search_fields = ('user__username', 'score')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Rating Information', {
            'fields': ('user', 'score')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['reset_ratings']

    def reset_ratings(self, request, queryset):
        queryset.update(score=0)
    reset_ratings.short_description = "Reset selected ratings to zero"

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'created_at', 'is_published')
    list_filter = ('is_published', 'created_at')
    search_fields = ('user__username', 'title', 'content')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [RatingInline]
    
    fieldsets = (
        ('Review Information', {
            'fields': ('user', 'title', 'content', 'is_published')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['publish_reviews', 'unpublish_reviews']

    def publish_reviews(self, request, queryset):
        queryset.update(is_published=True)
    publish_reviews.short_description = "Mark selected reviews as published"

    def unpublish_reviews(self, request, queryset):
        queryset.update(is_published=False)
    unpublish_reviews.short_description = "Mark selected reviews as unpublished"