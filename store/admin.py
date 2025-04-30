from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserProfile, Beat, Bundle, Testimonial, Cart, CartItem, Order, OrderItem, Favorite

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_notifications', 'order_updates', 'new_releases', 'promotions')
    list_filter = ('email_notifications', 'order_updates', 'new_releases', 'promotions')
    search_fields = ('user__email',)

@admin.register(Beat)
class BeatAdmin(admin.ModelAdmin):
    list_display = ('title', 'genre', 'bpm', 'price', 'is_featured', 'is_new_release', 'is_active', 'created_at')
    list_filter = ('genre', 'is_featured', 'is_new_release', 'is_active')
    search_fields = ('title', 'description', 'genre')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'genre', 'bpm', 'price')
        }),
        ('Media', {
            'fields': ('image', 'sample_audio', 'full_audio'),
            'description': 'Upload a 30-second sample preview and the full track for purchase.'
        }),
        ('Status', {
            'fields': ('is_featured', 'is_new_release', 'is_active')
        }),
    )

@admin.register(Bundle)
class BundleAdmin(admin.ModelAdmin):
    list_display = ('title', 'original_price', 'discounted_price', 'discount', 'beat_count')
    filter_horizontal = ('beats',)

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'rating', 'created_at')
    list_filter = ('rating',)

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'beat', 'quantity', 'added_at')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'status', 'created_at')
    list_filter = ('status',)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'beat', 'price', 'quantity')

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'beat', 'created_at')
