from django.contrib import admin
from .models import Profile, Post, Comment

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'location', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email', 'bio']
    raw_id_fields = ['user']

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['author', 'content', 'created_at', 'likes_count']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['content', 'author__username']
    raw_id_fields = ['author']
    date_hierarchy = 'created_at'
    
    def likes_count(self, obj):
        return obj.likes.count()
    likes_count.short_description = 'Likes'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'content', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'author__username']
    raw_id_fields = ['author', 'post']