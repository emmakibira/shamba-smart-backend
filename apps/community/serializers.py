from rest_framework import serializers
from .models import Post, PostLike, Comment
from apps.users.models import UserProfile


class UserProfileSimpleSerializer(serializers.ModelSerializer):
    """Simple user profile serializer for nested use"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user_email', 'user_name', 'profile_picture', 'location_address']


class CommentSerializer(serializers.ModelSerializer):
    user_profile = UserProfileSimpleSerializer(read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'post', 'user_profile', 'content', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class PostSerializer(serializers.ModelSerializer):
    user_profile = UserProfileSimpleSerializer(read_only=True)
    comments = CommentSerializer(read_only=True, many=True)
    user_has_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'user_profile', 'title', 'content', 'image', 
            'likes_count', 'comments_count', 'user_has_liked',
            'comments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['likes_count', 'comments_count', 'created_at', 'updated_at']
    
    def get_user_has_liked(self, obj):
        """Check if current user has liked this post"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        try:
            user_profile = request.user.profile
            return PostLike.objects.filter(post=obj, user_profile=user_profile).exists()
        except UserProfile.DoesNotExist:
            return False


class PostCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating posts with validation"""
    class Meta:
        model = Post
        fields = ['title', 'content', 'image']
    
    def create(self, validated_data):
        request = self.context.get('request')
        user_profile = request.user.profile
        
        # Check if user can create post
        if not user_profile.can_create_post():
            raise serializers.ValidationError(
                "You have reached the maximum number of posts for this month. "
                "Upgrade to premium for unlimited posts."
            )
        
        post = Post.objects.create(user_profile=user_profile, **validated_data)
        user_profile.posts_created_this_month += 1
        user_profile.save()
        return post
