from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate, logout
from django.http import JsonResponse, FileResponse
from django.db.models import Q, Sum
from functools import wraps
from .models import Beat, Bundle, OrderItem, Testimonial, Cart, CartItem, Order, Favorite
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy, reverse
from django.http import Http404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import check_password
from .validators import validate_password_strength
from django.core.exceptions import ValidationError
import json

def require_auth(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Please login to continue',
                    'requires_auth': True
                }, status=401)
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Please login to continue',
                    'requires_auth': True,
                    'redirect': '/'
                }, status=401)
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def home(request):
    # Get featured beats that are active and have all required fields
    featured_beats = Beat.objects.filter(
        is_featured=True,
        is_active=True,
        image__isnull=False,
        sample_audio__isnull=False,
        full_audio__isnull=False
    ).order_by('-created_at')[:3]

    # Get new releases that are active and have all required fields
    new_releases = Beat.objects.filter(
        is_new_release=True,
        is_active=True,
        image__isnull=False,
        sample_audio__isnull=False,
        full_audio__isnull=False
    ).order_by('-created_at')[:3]

    # Get active bundles
    bundles = Bundle.objects.filter(
        is_active=True,
        image__isnull=False
    ).order_by('-created_at')[:2]

    # Get active testimonials
    testimonials = Testimonial.objects.filter(
        is_active=True
    ).order_by('-created_at')[:3]

    # Set user on beats for purchased check
    for beat in list(featured_beats) + list(new_releases):
        beat.set_user(request.user)

    context = {
        'featured_beats': featured_beats,
        'new_releases': new_releases,
        'bundles': bundles,
        'testimonials': testimonials,
    }
    return render(request, 'home.html', context)

def beats(request):
    # Get search query
    search_query = request.GET.get('search', '')
    genre = request.GET.get('genre', '')
    bpm_min = request.GET.get('bpm_min', '')
    bpm_max = request.GET.get('bpm_max', '')
    sort_by = request.GET.get('sort', '-created_at')

    # Start with all active beats
    beats = Beat.objects.filter(is_active=True)

    # Apply search filter
    if search_query:
        beats = beats.filter(
            Q(title__icontains=search_query) |
            Q(genre__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Apply genre filter
    if genre:
        beats = beats.filter(genre=genre)

    # Apply BPM range filter
    if bpm_min:
        beats = beats.filter(bpm__gte=bpm_min)
    if bpm_max:
        beats = beats.filter(bpm__lte=bpm_max)

    # Apply sorting
    if sort_by == 'price_asc':
        beats = beats.order_by('price')
    elif sort_by == 'price_desc':
        beats = beats.order_by('-price')
    elif sort_by == 'bpm_asc':
        beats = beats.order_by('bpm')
    elif sort_by == 'bpm_desc':
        beats = beats.order_by('-bpm')
    else:  # Default to newest first
        beats = beats.order_by('-created_at')

    # Get unique genres for filter
    genres = Beat.objects.filter(is_active=True).values_list('genre', flat=True).distinct()

    # Get active bundles for carousel
    bundles = Bundle.objects.filter(
        is_active=True,
        image__isnull=False
    ).order_by('-created_at')

    context = {
        'beats': beats,
        'genres': genres,
        'search_query': search_query,
        'selected_genre': genre,
        'bpm_min': bpm_min,
        'bpm_max': bpm_max,
        'sort_by': sort_by,
        'bundles': bundles,
    }
    return render(request, 'beats.html', context)

def beat_detail(request, beat_id):
    beat = get_object_or_404(Beat, id=beat_id, is_active=True)
    
    # Get similar beats (same genre)
    similar_beats = Beat.objects.filter(
        genre=beat.genre,
        is_active=True
    ).exclude(id=beat.id).order_by('-created_at')[:3]
    
    # Get bundles containing this beat
    bundles = Bundle.objects.filter(
        beats=beat,
        is_active=True
    ).order_by('-created_at')[:2]
    
    # Set user for purchased check
    beat.set_user(request.user)
    
    context = {
        'beat': beat,
        'similar_beats': similar_beats,
        'bundles': bundles,
    }
    return render(request, 'beat_detail.html', context)

@require_auth
def dashboard(request):
    # Get user's purchased beats
    purchased_beats = Beat.objects.filter(
        orderitem__order__user=request.user,
        orderitem__order__status='completed'
    ).distinct()

    # Set user on beats for purchased check
    for beat in purchased_beats:
        beat.set_user(request.user)

    # Get user's orders
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    # Calculate total spent
    total_spent = Order.objects.filter(
        user=request.user,
        status='completed'
    ).aggregate(total=Sum('total_price'))['total'] or 0

    # Get download count (for future implementation)
    download_count = 0  # This will be implemented when we add download tracking

    # Get favorite beats
    favorite_beats = Beat.objects.filter(
        favorite__user=request.user
    ).distinct()

    # Set user on favorite beats for purchased check
    for beat in favorite_beats:
        beat.set_user(request.user)

    context = {
        'purchased_beats': purchased_beats,
        'orders': orders,
        'total_spent': total_spent,
        'download_count': download_count,
        'purchased_count': purchased_beats.count(),
        'favorite_beats': favorite_beats,
    }
    return render(request, 'dashboard.html', context)

@require_auth
def add_to_cart(request, beat_id):
    beat = get_object_or_404(Beat, id=beat_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
        
    # Check if beat is already in cart as an individual item
    if CartItem.objects.filter(cart=cart, beat=beat).exists():
        return JsonResponse({
            'status': 'error',
            'message': 'Beat is already in your cart'
        })
    
    # Check if beat is part of any bundle in cart
    bundle_cart_items = CartItem.objects.filter(cart=cart, bundle__isnull=False)
    for cart_item in bundle_cart_items:
        if beat in cart_item.bundle.beats.all():
            return JsonResponse({
                'status': 'error',
                'message': f'This beat is already in your cart as part of the bundle: {cart_item.bundle.title}'
            })
    
    # Add beat to cart
    CartItem.objects.create(cart=cart, beat=beat)
    
    return JsonResponse({
        'status': 'success',
        'message': f'{beat.title} added to cart!'
    })

@require_auth
def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)
    cart_item.delete()
    return JsonResponse({
        'status': 'success',
        'message': 'Item removed from cart!'
    })

@require_auth
def cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.cartitem_set.all().select_related('beat', 'bundle')
    
    items_data = []
    for item in cart_items:
        if item.beat:
            items_data.append({
                'id': item.id,
                'type': 'beat',
                'title': item.beat.title,
                'genre': item.beat.genre,
                'bpm': item.beat.bpm,
                'price': float(item.beat.price),
                'image_url': item.beat.get_image_url(),
                'quantity': item.quantity,
                'total_price': float(item.total_price)
            })
        elif item.bundle:
            items_data.append({
                'id': item.id,
                'type': 'bundle',
                'title': item.bundle.title,
                'genre': None,
                'bpm': None,
                'price': float(item.bundle.discounted_price),
                'image_url': item.bundle.image.url,
                'quantity': item.quantity,
                'total_price': float(item.total_price)
            })
    
    return JsonResponse({
        'items': items_data,
        'total_price': float(cart.total_price)
    })

@require_auth
def checkout(request, order_id):
    # Get the order and verify it belongs to the user and is not completed
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # If order is already completed, redirect to dashboard
    if order.status == 'completed':
        messages.warning(request, 'This order has already been completed.')
        return redirect('store:dashboard')
    
    # Get order items
    order_items = order.orderitem_set.all().select_related('beat')
    context = {
        'order': order,
        'order_items': order_items,
        'total_price': order.total_price
    }
    return render(request, 'checkout.html', context)

@login_required
def create_order(request):
    """Create a new order from cart items and process payment"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    try:
        # Get cart items through the cart relationship
        cart_items = CartItem.objects.filter(cart__user=request.user).select_related('beat', 'bundle')
        
        # Validate cart is not empty
        if not cart_items.exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Your cart is empty. Please add items before creating an order.'
            }, status=400)
        
        # Validate all items are still available and prices are current
        for item in cart_items:
            if item.beat:
                if not item.beat.is_active:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Beat "{item.beat.title}" is no longer available.'
                    }, status=400)
                if item.beat.price != item.price:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Price for "{item.beat.title}" has changed. Please refresh your cart.'
                    }, status=400)
            elif item.bundle:
                if not item.bundle.is_active:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Bundle "{item.bundle.title}" is no longer available.'
                    }, status=400)
                if item.bundle.discounted_price != item.price:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Price for bundle "{item.bundle.title}" has changed. Please refresh your cart.'
                    }, status=400)
        
        # Calculate total price
        total_price = sum(item.total_price for item in cart_items)
        
        # Get payment data from request
        try:
            payment_data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid payment data format.'
            }, status=400)
        
        # Validate payment data
        required_fields = ['payment_method', 'payment_details']
        for field in required_fields:
            if field not in payment_data:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Missing required payment field: {field}'
                }, status=400)
        
        # Create the order with initial status
        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
            status='pending',
            payment_method=payment_data['payment_method'],
            payment_details=payment_data['payment_details']
        )
        
        # Track beats that have been added to the order
        added_beats = set()
        
        # First, add all bundles to ensure we don't block beats that are part of bundles
        for item in cart_items:
            if item.bundle:
                # Create a single order item for the bundle
                OrderItem.objects.create(
                    order=order,
                    bundle=item.bundle,
                    price=item.bundle.discounted_price,
                    quantity=item.quantity
                )
                # Track all beats in this bundle
                added_beats.update(item.bundle.beats.all())
        
        # Then add individual beats that aren't part of any bundle
        for item in cart_items:
            if item.beat and item.beat.id not in added_beats:
                OrderItem.objects.create(
                    order=order,
                    beat=item.beat,
                    price=item.beat.price,
                    quantity=item.quantity
                )
                added_beats.add(item.beat.id)
        
        # Process payment (implement your payment gateway integration here)
        try:
            # This is where you would integrate with your payment processor
            # For example: Stripe, PayPal, etc.
            payment_success = process_payment(order, payment_data)
            
            if not payment_success:
                # If payment fails, delete the order and return error
                order.delete()
                return JsonResponse({
                    'status': 'error',
                    'message': 'Payment processing failed. Please try again or use a different payment method.'
                }, status=400)
            
            # Update order status to completed
            order.status = 'completed'
            order.save()
            
            # Clear the cart
            cart_items.delete()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Order created and payment processed successfully!',
                'order_id': order.id,
                'order_details': {
                    'total_price': float(order.total_price),
                    'items_count': order.orderitem_set.count(),
                    'status': order.status
                }
            })
            
        except Exception as e:
            # If payment processing fails, delete the order and return error
            order.delete()
            return JsonResponse({
                'status': 'error',
                'message': f'Payment processing error: {str(e)}'
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }, status=500)

def process_payment(order, payment_data):
    """
    Process payment for an order using the specified payment method.
    This is a placeholder function - implement your actual payment processing logic here.
    """
    # TODO: Implement actual payment processing logic
    # This could involve:
    # 1. Stripe integration
    # 2. PayPal integration
    # 3. Other payment gateways
    
    # For now, return True to simulate successful payment
    return True

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return JsonResponse({
                'status': 'success',
                'message': 'Account created successfully!'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'errors': form.errors
            }, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

def custom_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        
        if not email or not password:
            return JsonResponse({
                'status': 'error',
                'message': 'Please provide both email and password'
            }, status=400)
        
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            login(request, user)
            if not remember:
                request.session.set_expiry(0)
            return JsonResponse({
                'status': 'success',
                'message': 'Login successful!'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid email or password'
            }, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

def terms(request):
    return render(request, 'store/terms.html')

def privacy(request):
    return render(request, 'store/privacy.html')

def custom_logout(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({
            'status': 'success',
            'message': 'Logged out successfully'
        })
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)

class CustomPasswordResetView(PasswordResetView):
    template_name = 'store/password_reset.html'
    email_template_name = 'store/password_reset_email.html'
    subject_template_name = 'store/password_reset_subject.txt'
    html_email_template_name = 'store/password_reset_email.html'
    success_url = reverse_lazy('store:password_reset_done')

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'store/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'store/password_reset_confirm.html'
    success_url = reverse_lazy('store:password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'store/password_reset_complete.html'

@require_auth
def download_beat(request, beat_id):
    beat = get_object_or_404(Beat, id=beat_id)
    
    # Check if user has purchased the beat
    has_purchased = OrderItem.objects.filter(
        order__user=request.user,
        order__status='completed',
        beat=beat
    ).exists()
    
    if not has_purchased:
        return JsonResponse({
            'status': 'error',
            'message': 'You need to purchase this beat before downloading'
        })
    
    # Return the file
    response = FileResponse(beat.full_audio, as_attachment=True)
    response['Content-Disposition'] = f'attachment; filename="{beat.title}.mp3"'
    return response

@require_auth
def toggle_favorite(request, beat_id):
    beat = get_object_or_404(Beat, id=beat_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, beat=beat)
    
    if not created:
        favorite.delete()
        return JsonResponse({
            'status': 'success',
            'message': 'Beat removed from favorites',
            'is_favorite': False
        })
    
    return JsonResponse({
        'status': 'success',
        'message': 'Beat added to favorites',
        'is_favorite': True
    })

def get_bundle_beats(request, bundle_id):
    bundle = get_object_or_404(Bundle, id=bundle_id, is_active=True)
    beats = bundle.beats.filter(is_active=True)
    
    beats_data = [{
        'id': beat.id,
        'title': beat.title,
        'genre': beat.genre,
        'bpm': beat.bpm,
        'price': float(beat.price),
        'image_url': beat.get_image_url(),
        'sample_url': beat.get_sample_url(),
        'is_purchased': beat.is_purchased if hasattr(beat, 'is_purchased') else False,
        'is_favorite': beat.is_favorite if hasattr(beat, 'is_favorite') else False
    } for beat in beats]
    
    return JsonResponse({
        'status': 'success',
        'bundle': {
            'id': bundle.id,
            'title': bundle.title,
            'description': bundle.description,
            'original_price': float(bundle.original_price),
            'discounted_price': float(bundle.discounted_price),
            'discount': bundle.discount,
            'beat_count': bundle.beat_count,
            'image_url': bundle.image.url if bundle.image else None,
        },
        'beats': beats_data
    })

@require_auth
def add_bundle_to_cart(request, bundle_id):
    bundle = get_object_or_404(Bundle, id=bundle_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Check if bundle is already in cart
    if CartItem.objects.filter(cart=cart, bundle=bundle).exists():
        return JsonResponse({
            'status': 'error',
            'message': 'This bundle is already in your cart. Please check your cart before adding it again.'
        })
    
    # Get all beats in the bundle
    bundle_beats = set(bundle.beats.all())
    
    # Get all beats currently in cart (both individual and from other bundles)
    cart_items = CartItem.objects.filter(cart=cart).select_related('beat', 'bundle')
    existing_beats = {}  # Dictionary to track where each beat is from
    
    for item in cart_items:
        if item.beat:
            existing_beats[item.beat] = 'individual item'
        elif item.bundle:
            for beat in item.bundle.beats.all():
                existing_beats[beat] = f'bundle "{item.bundle.title}"'
    
    # Check for overlapping beats
    overlapping_beats = bundle_beats.intersection(existing_beats.keys())
    if overlapping_beats:
        # Group beats by their source
        beats_by_source = {}
        for beat in overlapping_beats:
            source = existing_beats[beat]
            if source not in beats_by_source:
                beats_by_source[source] = []
            beats_by_source[source].append(beat.title)
        
        # Build detailed message
        message_parts = ['Unable to add this bundle because some beats are already in your cart:']
        for source, beats in beats_by_source.items():
            message_parts.append(f"\n• {', '.join(beats)} (from {source})")
        message_parts.append("\nTo avoid double payment, please either:")
        message_parts.append("1. Remove these beats from your cart first")
        message_parts.append("2. Purchase them as part of this bundle instead")
        
        return JsonResponse({
            'status': 'error',
            'message': ''.join(message_parts)
        })
    
    # Add bundle to cart
    CartItem.objects.create(cart=cart, bundle=bundle)
    
    return JsonResponse({
        'status': 'success',
        'message': f'{bundle.title} has been added to your cart! You can now proceed to checkout.'
    })

@require_http_methods(["POST"])
@require_auth
def update_settings(request):
    try:
        data = json.loads(request.body)
        user = request.user
        
        # Update profile
        if 'profile' in data:
            profile = data['profile']
            
            if 'first_name' in profile:
                user.first_name = profile['first_name']
            if 'last_name' in profile:
                user.last_name = profile['last_name']
            if 'bio' in profile:
                user.userprofile.bio = profile['bio']
            
            user.save()
            user.userprofile.save()
        
        # Update password
        if 'password' in data:
            password = data['password']
            
            # First check if current password is correct
            if not check_password(password['current_password'], user.password):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Current password is incorrect'
                }, status=400)
            
            # Then check if new passwords match
            if password['new_password'] != password['confirm_password']:
                return JsonResponse({
                    'status': 'error',
                    'message': 'New passwords do not match'
                }, status=400)
            
            # Finally validate password strength
            try:
                validate_password_strength(password['new_password'])
            except ValidationError as e:
                return JsonResponse({
                    'status': 'error',
                    'message': '\n'.join(e.messages)
                }, status=400)
            
            # If all validations pass, update the password
            user.set_password(password['new_password'])
            user.save()
        
        # Update notification preferences
        if 'notifications' in data:
            notifications = data['notifications']
            profile = user.userprofile
            
            if 'email_notifications' in notifications:
                profile.email_notifications = notifications['email_notifications'] == 'true'
            if 'order_updates' in notifications:
                profile.order_updates = notifications['order_updates'] == 'true'
            if 'new_releases' in notifications:
                profile.new_releases = notifications['new_releases'] == 'true'
            
            profile.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Settings updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
