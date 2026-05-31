from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Post, PostLike, Comment
from .serializers import PostSerializer, PostCreateSerializer, CommentSerializer


class PostListCreateView(generics.ListCreateAPIView):
    """List all posts or create a new post"""
    permission_classes = [IsAuthenticated]
    queryset = Post.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PostCreateSerializer
        return PostSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a post"""
    permission_classes = [IsAuthenticated]
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    
    def perform_update(self, serializer):
        """Ensure user can only update their own posts"""
        if serializer.instance.user_profile.user != self.request.user:
            raise PermissionError("You can only update your own posts")
        serializer.save()
    
    def perform_destroy(self, instance):
        """Ensure user can only delete their own posts"""
        if instance.user_profile.user != self.request.user:
            raise PermissionError("You can only delete your own posts")
        instance.delete()


class PostLikeToggleView(generics.GenericAPIView):
    """Toggle like on a post"""
    permission_classes = [IsAuthenticated]
    queryset = Post.objects.all()
    
    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        user_profile = request.user.profile
        
        like, created = PostLike.objects.get_or_create(
            post=post,
            user_profile=user_profile
        )
        
        if not created:
            # Remove like
            like.delete()
            post.likes_count -= 1
            post.save()
            return Response({'liked': False, 'likes_count': post.likes_count})
        else:
            # Add like
            post.likes_count += 1
            post.save()
            return Response({'liked': True, 'likes_count': post.likes_count})


class CommentListCreateView(generics.ListCreateAPIView):
    """List comments for a post or create a new comment"""
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializer
    
    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        return Comment.objects.filter(post_id=post_id)
    
    def perform_create(self, serializer):
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, pk=post_id)
        user_profile = self.request.user.profile
        
        comment = serializer.save(post=post, user_profile=user_profile)
        post.comments_count += 1
        post.save()


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a comment"""
    permission_classes = [IsAuthenticated]
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    
    def perform_update(self, serializer):
        """Ensure user can only update their own comments"""
        if serializer.instance.user_profile.user != self.request.user:
            raise PermissionError("You can only update your own comments")
        serializer.save()
    
    def perform_destroy(self, instance):
        """Ensure user can only delete their own comments"""
        if instance.user_profile.user != self.request.user:
            raise PermissionError("You can only delete your own comments")
        
        post = instance.post
        post.comments_count -= 1
        post.save()
        instance.delete()
