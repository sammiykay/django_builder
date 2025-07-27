from django.contrib import admin
from .models import Post, Comment

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1
    readonly_fields = ('created_at',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'author')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [CommentInline]
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'content', 'author')
        }),
        ('Status', {
            'fields': ('status', 'created_at', 'updated_at')
        }),
    )
    
    actions = ['make_published', 'make_draft']
    
    def make_published(self, request, queryset):
        queryset.update(status='published')
    make_published.short_description = "Mark selected posts as published"
    
    def make_draft(self, request, queryset):
        queryset.update(status='draft')
    make_draft.short_description = "Mark selected posts as draft"

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('author', 'content')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Comment Information', {
            'fields': ('post', 'author', 'content')
        }),
        ('Moderation', {
            'fields': ('is_active', 'created_at')
        }),
    )
    
    actions = ['approve_comments', 'disapprove_comments']
    
    def approve_comments(self, request, queryset):
        queryset.update(is_active=True)
    approve_comments.short_description = "Approve selected comments"
    
    def disapprove_comments(self, request, queryset):
        queryset.update(is_active=False)
    disapprove_comments.short_description = "Disapprove selected comments"