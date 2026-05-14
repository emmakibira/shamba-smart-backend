from django.contrib import admin
from apps.users.models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'location', 'farm_size']
    search_fields = ['user__username', 'user__email']
