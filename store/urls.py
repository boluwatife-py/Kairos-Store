from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('beats/', views.beats, name='beats'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:beat_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    
    # Authentication URLs
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # Legal URLs
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
] 