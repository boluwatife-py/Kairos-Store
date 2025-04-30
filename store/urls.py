from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('beats/', views.beats, name='beats'),
    path('beat/<int:beat_id>/', views.beat_detail, name='beat_detail'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('cart/', views.cart, name='cart'),
    path('checkout/<int:order_id>/', views.checkout, name='checkout'),
    path('api/bundle/<int:bundle_id>/beats/', views.get_bundle_beats, name='bundle_beats'),
    path('create-order/', views.create_order, name='create_order'),
    path('add-to-cart/<int:beat_id>/', views.add_to_cart, name='add_to_cart'),
    path('add-to-cart/bundle/<int:bundle_id>/', views.add_bundle_to_cart, name='add_bundle_to_cart'),
    path('remove-from-cart/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('download/<int:beat_id>/', views.download_beat, name='download_beat'),
    path('toggle-favorite/<int:beat_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # Authentication URLs
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('api/settings/update/', views.update_settings, name='update_settings'),
] 