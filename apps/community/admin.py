from django.contrib import admin
from .models import Post, PostLike, Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'user_profile', 'likes_count', 'comments_count', 'created_at']
    list_filter = ['created_at', 'likes_count']
    search_fields = ['title', 'content', 'user_profile__user__email']
    readonly_fields = ['likes_count', 'comments_count', 'created_at', 'updated_at']


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ['post', 'user_profile', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user_profile__user__email']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['post', 'user_profile', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'user_profile__user__email']
