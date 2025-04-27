from django.contrib import admin
from .models import Beat, Bundle, Testimonial, Cart, CartItem, Order, OrderItem

@admin.register(Beat)
class BeatAdmin(admin.ModelAdmin):
    list_display = ('title', 'genre', 'bpm', 'price', 'is_featured', 'is_new_release')
    list_filter = ('genre', 'is_featured', 'is_new_release')
    search_fields = ('title', 'description')

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
