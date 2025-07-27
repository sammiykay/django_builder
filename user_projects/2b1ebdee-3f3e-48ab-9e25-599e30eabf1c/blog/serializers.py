from rest_framework import serializers
from .models import Post, Comment

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'content', 'author', 'created_at']
        read_only_fields = ['created_at']

    def validate_content(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Comment must be at least 10 characters long")
        return value

class PostSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    comment_count = serializers.IntegerField(source='comments.count', read_only=True)
    
    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'created_at', 'updated_at', 'comments', 'comment_count']
        read_only_fields = ['created_at', 'updated_at']

    def validate_title(self, value):
        if len(value) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters long")
        return value

    def validate_content(self, value):
        if len(value) < 20:
            raise serializers.ValidationError("Content must be at least 20 characters long")
        return value

    def create(self, validated_data):
        return Post.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.content = validated_data.get('content', instance.content)
        instance.save()
        return instance