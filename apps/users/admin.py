from django.contrib import admin
from django.utils.html import format_html
from apps.users.models import UserProfile, FarmData


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user_email', 'phone_number', 'location_address', 'farm_size',
        'soil_type', 'is_premium', 'premium_expiry', 'location_link'
    ]
    list_filter = ['soil_type', 'is_premium', 'created_at']
    search_fields = ['user__username', 'user__email', 'location_address']
    readonly_fields = ['firebase_uid', 'created_at', 'updated_at', 'location_map']
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'firebase_uid', 'phone_number')
        }),
        ('Location Data', {
            'fields': ('latitude', 'longitude', 'location_address', 'location_map')
        }),
        ('Farm Information', {
            'fields': ('farm_size', 'primary_crops', 'soil_type', 'years_of_experience')
        }),
        ('Premium Status', {
            'fields': ('is_premium', 'premium_plan', 'premium_expiry', 'posts_created_this_month')
        }),
        ('Profile', {
            'fields': ('bio', 'profile_picture')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    
    def location_link(self, obj):
        if obj.latitude and obj.longitude:
            url = f"https://maps.google.com/?q={obj.latitude},{obj.longitude}"
            return format_html('<a href="{}" target="_blank">View on Maps</a>', url)
        return "No location"
    location_link.short_description = 'Map'
    
    def location_map(self, obj):
        if not obj.latitude or not obj.longitude:
            return "No coordinates set"
        
        # Simple map HTML using OpenStreetMap (free)
        html = f"""
        <div style="width: 100%; height: 400px; border: 1px solid #ccc;">
            <iframe width="100%" height="400" frameborder="0" style="border:0"
                src="https://www.openstreetmap.org/export/embed.html?bbox={float(obj.longitude)-0.01},{float(obj.latitude)-0.01},{float(obj.longitude)+0.01},{float(obj.latitude)+0.01}&layer=mapnik&marker={obj.latitude},{obj.longitude}"
                allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade">
            </iframe>
        </div>
        """
        return format_html(html)
    location_map.short_description = 'Location Map'


@admin.register(FarmData)
class FarmDataAdmin(admin.ModelAdmin):
    list_display = [
        'farmer_email', 'crop_name', 'planting_date', 'expected_harvest_date',
        'area_planted', 'yield_obtained', 'created_at'
    ]
    list_filter = ['crop_name', 'planting_date', 'created_at']
    search_fields = ['user_profile__user__email', 'crop_name']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Farmer Information', {
            'fields': ('user_profile',)
        }),
        ('Crop Details', {
            'fields': ('crop_name', 'area_planted')
        }),
        ('Timeline', {
            'fields': ('planting_date', 'expected_harvest_date', 'actual_harvest_date')
        }),
        ('Results', {
            'fields': ('yield_obtained', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def farmer_email(self, obj):
        return obj.user_profile.user.email
    farmer_email.short_description = 'Farmer Email'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user_profile__user')
