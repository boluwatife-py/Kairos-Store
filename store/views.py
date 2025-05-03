from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate, logout
from django.http import JsonResponse, FileResponse, Http404, HttpResponseRedirect, HttpResponse
from django.db.models import Q, Sum
from functools import wraps
from .models import Beat, Bundle, OrderItem, Testimonial, Cart, CartItem, Order, Favorite
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import check_password
from .validators import validate_password_strength
from django.core.exceptions import ValidationError
import json
import stripe
from django.conf import settings
import requests
from django.core.files.base import ContentFile
from urllib.parse import unquote, quote
import zipfile
import io
from django.contrib.auth.models import User
from .models import UserProfile

# Initialize Stripe with your secret key
stripe.api_key = settings.STRIPE_SECRET_KEY

@require_http_methods(["POST"])
@login_required
def create_beat(request):
    """Create a new beat"""
    try:
        data = json.loads(request.body)
        
        # Create the beat
        beat = Beat.objects.create(
            title=data['title'],
            description=data.get('description', ''),
            genre=data['genre'],
            bpm=data['bpm'],
            price=float(data['price']),
            is_active=True,
            is_featured=data.get('is_featured', False),
            is_new_release=data.get('is_new_release', False),
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Beat created successfully',
            'beat_id': beat.id
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to create beat: {str(e)}'
        }, status=400)

@require_http_methods(["POST"])
@login_required
def create_bundle(request):
    """Create a new bundle"""
    try:
        data = json.loads(request.body)
        
        # Create the bundle
        bundle = Bundle.objects.create(
            title=data['title'],
            description=data.get('description', ''),
            original_price=float(data['original_price']),
            discounted_price=float(data['discounted_price']),
            is_active=True,
        )
        
        # Add beats to bundle if provided
        if 'beat_ids' in data:
            bundle.beats.set(data['beat_ids'])
        
        return JsonResponse({
            'status': 'success',
            'message': 'Bundle created successfully',
            'bundle_id': bundle.id
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to create bundle: {str(e)}'
        }, status=400)

def require_auth(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Please login to continue',
                    'requires_auth': True
                }, status=401)
            else:
                # Get the current path for the next parameter
                next_url = request.get_full_path()
                # Render home template with login modal
                return render(request, 'home.html', {
                    'show_modal': 'login',
                    'next_url': next_url
                })
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

    # Get modal parameter and next URL
    modal = request.GET.get('modal')
    next_url = request.GET.get('next', '')
    
    # Get cart data if modal is cart
    cart_data = None
    if modal == 'cart' and request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart_items = cart.cartitem_set.all()
            cart_data = {
                'items': cart_items,
                'total_price': cart.get_total_price()
            }

    context = {
        'featured_beats': featured_beats,
        'new_releases': new_releases,
        'bundles': bundles,
        'testimonials': testimonials,
        'show_modal': modal,  # Will be 'login', 'signup', 'cart', or None
        'cart_data': cart_data,
        'next_url': next_url,  # Pass the next URL to the template
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

    # Set user on beats for purchased check
    for beat in beats:
        beat.set_user(request.user)

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

    # Get user's orders with additional context for overruled orders
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Check each order for purchased items and update status if needed
    for order in orders:
        if order.status != 'completed':  # Only check non-completed orders
            purchased_items = order.check_for_purchased_items()
            if purchased_items:
                if order.status != 'overruled':
                    order.status = 'overruled'
                    order.save()
                order.purchased_items = purchased_items

    # Calculate total spent
    total_spent = Order.objects.filter(
        user=request.user,
        status='completed'
    ).aggregate(total=Sum('total_price'))['total'] or 0

    # Get favorite beats
    favorite_beats = Beat.objects.filter(
        favorite__user=request.user
    ).distinct()

    # Set user on favorite beats for purchased check
    for beat in favorite_beats:
        beat.set_user(request.user)

    # Get purchased beats count
    purchased_count = purchased_beats.count()

    # Get download count (this will be the same as purchased count for now)
    # In the future, you might want to track actual downloads separately
    download_count = purchased_count

    context = {
        'purchased_beats': purchased_beats,
        'orders': orders,
        'total_spent': total_spent,
        'favorite_beats': favorite_beats,
        'purchased_count': purchased_count,
        'download_count': download_count,
    }
    return render(request, 'dashboard.html', context)

@require_auth
def add_to_cart(request, beat_id):
    beat = get_object_or_404(Beat, id=beat_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Check if beat is already purchased
    if OrderItem.objects.filter(
        order__user=request.user,
        order__status='completed',
        beat=beat
    ).exists():
        return JsonResponse({
            'status': 'error',
            'message': 'You have already purchased this beat'
        })
        
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

@login_required
def cart(request):
    """Handle regular cart view with HTML response"""
    # Get user's cart
    cart = Cart.objects.filter(user=request.user).first()
    cart_items = []
    total_price = 0
    
    if cart:
        cart_items = cart.cartitem_set.all()
        total_price = cart.get_total_price()

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'cart.html', context)

def api_cart(request):
    """Handle JSON cart requests"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'error',
            'message': 'Please login to view your cart',
            'requires_auth': True
        }, status=401)
    
    # Get user's cart
    cart = Cart.objects.filter(user=request.user).first()
    cart_items = []
    total_price = 0
    
    if cart:
        cart_items = cart.cartitem_set.all()
        total_price = cart.get_total_price()

        # Prepare cart items data for JSON response
        cart_items_data = []
        for item in cart_items:
            item_data = {
                'id': item.id,
                'type': 'beat' if item.beat else 'bundle',
            }
            if item.beat:
                item_data.update({
                    'title': item.beat.title,
                    'price': float(item.beat.price),
                    'image_url': item.beat.get_image_url(),
                    'genre': item.beat.genre,
                    'bpm': item.beat.bpm,
                })
            else:
                item_data.update({
                    'title': item.bundle.title,
                    'price': float(item.bundle.discounted_price),
                    'image_url': item.bundle.image.url if item.bundle.image else None,
                })
            cart_items_data.append(item_data)

        return JsonResponse({
            'cart_count': len(cart_items),
            'cart_items': cart_items_data,
            'total_price': float(total_price)
        })
    
    return JsonResponse({
        'cart_count': 0,
        'cart_items': [],
        'total_price': 0.00
    })

@login_required
def create_order(request):
    if request.method == 'POST':
        cart = get_object_or_404(Cart, user=request.user)
        
        # Check for already purchased items in cart
        purchased_items = []
        for item in cart.cartitem_set.all():
            if item.beat:
                if OrderItem.objects.filter(
                    order__user=request.user,
                    order__status='completed',
                    beat=item.beat
                ).exists():
                    purchased_items.append(item.beat.title)
            elif item.bundle:
                bundle_purchased_beats = []
                for beat in item.bundle.beats.all():
                    if OrderItem.objects.filter(
                        order__user=request.user,
                        order__status='completed',
                        beat=beat
                    ).exists():
                        bundle_purchased_beats.append(beat.title)
                if bundle_purchased_beats:
                    purchased_items.append(f"Bundle '{item.bundle.title}' contains already purchased beats: {', '.join(bundle_purchased_beats)}")

        if purchased_items:
            # Create order but mark it as overruled
            order = Order.objects.create(
                user=request.user,
                total_price=cart.total_price,
                status='overruled'
            )
            
            # Still create order items for tracking
            for item in cart.cartitem_set.all():
                if item.beat:
                    OrderItem.objects.create(
                        order=order,
                        beat=item.beat,
                        price=item.beat.price,
                        quantity=item.quantity
                    )
                elif item.bundle:
                    for beat in item.bundle.beats.all():
                        OrderItem.objects.create(
                            order=order,
                            beat=beat,
                            price=beat.price,
                            quantity=item.quantity
                        )
            
            cart.delete()
            
            return JsonResponse({
                'status': 'error',
                'message': 'Some items in your cart have already been purchased:\n• ' + '\n• '.join(purchased_items),
                'redirect': reverse('store:dashboard')
            })

        # Create normal order if no purchased items
        order = Order.objects.create(
            user=request.user,
            total_price=cart.total_price
        )
        
        for item in cart.cartitem_set.all():
            if item.beat:
                OrderItem.objects.create(
                    order=order,
                    beat=item.beat,
                    price=item.beat.price,
                    quantity=item.quantity
                )
            elif item.bundle:
                for beat in item.bundle.beats.all():
                    OrderItem.objects.create(
                        order=order,
                        beat=beat,
                        price=beat.price,
                        quantity=item.quantity
                    )
        
        cart.delete()
        return JsonResponse({
            'status': 'success',
            'message': 'Order created successfully',
            'redirect': reverse('store:checkout', args=[order.id])
        })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=400)

@require_http_methods(["GET", "POST"])
def custom_login(request, next_url=None):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        next_url = request.POST.get('next', '')
        
        if not email or not password:
            return JsonResponse({
                'status': 'error',
                'message': 'Please provide both email and password'
            }, status=400)
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            if not remember:
                request.session.set_expiry(0)
            
            # If it's an AJAX request, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Login successful!',
                    'redirect': next_url if next_url else reverse('store:home')
                })
            # For regular form submissions, redirect
            else:
                return HttpResponseRedirect(next_url if next_url else reverse('store:home'))
        else:
            # If it's an AJAX request, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid email or password'
                }, status=400)
            # For regular form submissions, show error message
            else:
                messages.error(request, 'Invalid email or password')
                return HttpResponseRedirect(reverse('store:login'))

    # If GET request, render home template with login modal
    featured_beats = Beat.objects.filter(
        is_featured=True,
        is_active=True,
        image__isnull=False,
        sample_audio__isnull=False,
        full_audio__isnull=False
    ).order_by('-created_at')[:3]

    new_releases = Beat.objects.filter(
        is_new_release=True,
        is_active=True,
        image__isnull=False,
        sample_audio__isnull=False,
        full_audio__isnull=False
    ).order_by('-created_at')[:3]

    bundles = Bundle.objects.filter(
        is_active=True,
        image__isnull=False
    ).order_by('-created_at')[:2]

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
        'show_modal': 'login',
        'next_url': next_url,
    }
    return render(request, 'home.html', context)


@require_http_methods(["GET", "POST"])
def register(request, next_url=None):
    if request.method == "POST":
        try:
            # Get form data
            email = request.POST.get('email')
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            next_url = request.POST.get('next', '')

            # Validate passwords match
            if password1 != password2:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Passwords do not match'
                }, status=400)

            # Validate password length
            if len(password1) < 8:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Password must be at least 8 characters long'
                }, status=400)

            # Check if user already exists
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'A user with this email already exists'
                }, status=400)

            # Create user
            user = User.objects.create_user(
                username=email,  # Using email as username
                email=email,
                password=password1
            )

            # Create user profile
            UserProfile.objects.create(user=user)

            # Log the user in
            login(request, user)

            return JsonResponse({
                'status': 'success',
                'message': 'Registration successful! Welcome to Kairos.',
                'redirect': next_url if next_url else reverse('store:home')
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

    # If GET request, render home template with signup modal
    featured_beats = Beat.objects.filter(
        is_featured=True,
        is_active=True,
        image__isnull=False,
        sample_audio__isnull=False,
        full_audio__isnull=False
    ).order_by('-created_at')[:3]

    new_releases = Beat.objects.filter(
        is_new_release=True,
        is_active=True,
        image__isnull=False,
        sample_audio__isnull=False,
        full_audio__isnull=False
    ).order_by('-created_at')[:3]

    bundles = Bundle.objects.filter(
        is_active=True,
        image__isnull=False
    ).order_by('-created_at')[:2]

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
        'show_modal': 'signup',
        'next_url': next_url,
    }
    return render(request, 'home.html', context)


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
        }, status=403)
    
    try:
        # Get the secure URL from Cloudinary
        download_url = beat.full_audio.url
        
        # Download the file from Cloudinary
        response = requests.get(download_url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Create the HTTP response with the file content
        file_response = HttpResponse(
            response.iter_content(chunk_size=8192),
            content_type='audio/mpeg'
        )
        
        # Set headers for file download
        filename = f"{beat.title}.mp3"
        file_response['Content-Disposition'] = f'attachment; filename="{filename}"'
        file_response['Access-Control-Allow-Origin'] = '*'
        file_response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        file_response['Access-Control-Allow-Headers'] = 'Content-Type'
        
        return file_response
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error downloading file: {str(e)}'
        }, status=500)

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
    
    # Set user on each beat before checking is_purchased
    for beat in beats:
        beat._user = request.user
    
    beats_data = [{
        'id': beat.id,
        'title': beat.title,
        'genre': beat.genre,
        'bpm': beat.bpm,
        'price': float(beat.price),
        'image_url': beat.get_image_url(),
        'sample_url': beat.get_sample_url(),
        'is_purchased': beat.is_purchased,  # Now this will work correctly
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
    
    # Check if any beats in the bundle are already purchased
    purchased_beats = []
    for beat in bundle.beats.all():
        if OrderItem.objects.filter(
            order__user=request.user,
            order__status='completed',
            beat=beat
        ).exists():
            purchased_beats.append(beat.title)
    
    if purchased_beats:
        if len(purchased_beats) == 1:
            message = f"Cannot add bundle because you have already purchased the beat: {purchased_beats[0]}"
        else:
            message = f"Cannot add bundle because you have already purchased these beats: {', '.join(purchased_beats)}"
        return JsonResponse({
            'status': 'error',
            'message': message
        })
    
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
    overlapping_beats = []
    for beat in bundle.beats.all():
        if beat in existing_beats:
            overlapping_beats.append((beat.title, existing_beats[beat]))
    
    if overlapping_beats:
        message_parts = ['Cannot add bundle because some beats are already in your cart:']
        for beat_title, source in overlapping_beats:
            message_parts.append(f"\n• {beat_title} (as {source})")
        
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

@require_auth
def checkout(request, order_id):
    # Get the order and verify it belongs to the user
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Check order status
    if order.status == 'completed':
        messages.warning(request, 'This order has already been completed.')
        return redirect('store:dashboard')
    elif order.status == 'overruled':
        purchased_items = order.check_for_purchased_items()
        messages.error(request, 'Order cannot be completed because these items have already been purchased:\n• ' + '\n• '.join(purchased_items))
        return redirect('store:dashboard')
    
    # Recheck for purchased items before proceeding
    purchased_items = order.check_for_purchased_items()
    if purchased_items:
        order.status = 'overruled'
        order.save()
        messages.error(request, 'Order cannot be completed because these items have already been purchased:\n• ' + '\n• '.join(purchased_items))
        return redirect('store:dashboard')
    
    # Get order items
    order_items = order.orderitem_set.all().select_related('beat')
    context = {
        'order': order,
        'order_items': order_items,
        'total_price': order.total_price,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, 'checkout.html', context)

@require_http_methods(["POST"])
@require_auth
def create_payment_intent(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=int(order.total_price * 100),  # Convert to cents
            currency='usd',
            metadata={
                'order_id': str(order.id),
                'user_id': str(request.user.id),
            }
        )
        
        return JsonResponse({
            'clientSecret': intent.client_secret
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)

@require_auth
def payment_success(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        payment_intent_id = request.GET.get('payment_intent')
        
        if payment_intent_id:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if payment_intent.status == 'succeeded':
                # Update order status
                order.status = 'completed'
                order.payment_id = payment_intent_id
                order.save()
                
                # Clear the cart if it exists
                Cart.objects.filter(user=request.user).delete()
                
                messages.success(request, 'Payment successful! You can now download your beats.')
                return redirect('store:dashboard')
            
        messages.error(request, 'Payment verification failed. Please contact support if you believe this is an error.')
        return redirect('store:checkout', order_id=order_id)
        
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('store:checkout', order_id=order_id)

@require_auth
def download_all_purchases(request):
    # Get all purchased beats
    purchased_beats = Beat.objects.filter(
        orderitem__order__user=request.user,
        orderitem__order__status='completed'
    ).distinct()

    if not purchased_beats.exists():
        messages.warning(request, 'You have no purchased beats to download.')
        return redirect('store:dashboard')

    # Create a zip file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for beat in purchased_beats:
            try:
                # Get the audio file from Cloudinary
                response = requests.get(beat.full_audio.url, stream=True)
                response.raise_for_status()
                
                # Create a safe filename
                filename = f"{beat.title}.mp3".replace(" ", "_")
                
                # Add the file to the zip
                zip_file.writestr(filename, response.content)
                
            except Exception as e:
                messages.error(request, f'Error downloading {beat.title}: {str(e)}')
                continue

    # Reset buffer position
    zip_buffer.seek(0)
    
    # Create the response
    response = FileResponse(
        zip_buffer,
        as_attachment=True,
        filename='purchased_beats.zip'
    )
    
    # Add CORS headers
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    
    return response
