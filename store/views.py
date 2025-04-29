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
from django.urls import reverse_lazy
from django.http import Http404

def login_required_json(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 'error',
                'message': 'Please login to continue',
                'requires_auth': True
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

    context = {
        'beats': beats,
        'genres': genres,
        'search_query': search_query,
        'selected_genre': genre,
        'bpm_min': bpm_min,
        'bpm_max': bpm_max,
        'sort_by': sort_by,
    }
    return render(request, 'beats.html', context)

@login_required
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

@login_required_json
def add_to_cart(request, beat_id):
    beat = get_object_or_404(Beat, id=beat_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, beat=beat)
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    return JsonResponse({
        'status': 'success',
        'message': f'{beat.title} added to cart!'
    })

@login_required_json
def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)
    cart_item.delete()
    return JsonResponse({
        'status': 'success',
        'message': 'Item removed from cart!'
    })

@login_required
def cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.cartitem_set.all().select_related('beat')
    
    items_data = [{
        'id': item.id,
        'beat': {
            'title': item.beat.title,
            'genre': item.beat.genre,
            'bpm': item.beat.bpm,
            'price': float(item.beat.price),
            'image_url': item.beat.get_image_url()
        },
        'quantity': item.quantity,
        'total_price': float(item.total_price)
    } for item in cart_items]
    
    return JsonResponse({
        'items': items_data,
        'total_price': float(cart.total_price)
    })

@login_required
def checkout(request, order_id):
    # Get the order and verify it belongs to the user and is not completed
    order = get_object_or_404(Order, id=order_id, user=request.user, status='pending')
    
    # Get order items
    order_items = order.orderitem_set.all().select_related('beat')
    context = {
        'order': order,
        'order_items': order_items,
        'total_price': order.total_price
    }
    return render(request, 'checkout.html', context)

@login_required_json
def create_order(request):
    if request.method == 'POST':
        cart = get_object_or_404(Cart, user=request.user)
        order = Order.objects.create(
            user=request.user,
            total_price=cart.total_price
        )
        for item in cart.cartitem_set.all():
            OrderItem.objects.create(
                order=order,
                beat=item.beat,
                price=item.beat.price,
                quantity=item.quantity
            )
        cart.delete()
        return JsonResponse({
            'status': 'success',
            'message': 'Order placed successfully!',
            'redirect': f'/checkout/{order.id}/'
        })
    
    # Raise 404 for GET requests
    raise Http404("Page not found")

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

@login_required
def download_beat(request, beat_id):
    beat = get_object_or_404(Beat, id=beat_id)
    
    # Check if user has purchased the beat
    has_purchased = OrderItem.objects.filter(
        order__user=request.user,
        beat=beat,
        order__status='completed'
    ).exists()
    
    if not has_purchased:
        return JsonResponse({
            'status': 'error',
            'message': 'You need to purchase this beat before downloading it'
        }, status=403)
    
    if not beat.full_audio:
        return JsonResponse({
            'status': 'error',
            'message': 'Audio file not found'
        }, status=404)
    
    # Serve the file
    response = FileResponse(beat.full_audio, as_attachment=True)
    response['Content-Disposition'] = f'attachment; filename="{beat.title}.mp3"'
    return response

@login_required_json
def toggle_favorite(request, beat_id):
    beat = get_object_or_404(Beat, id=beat_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, beat=beat)
    
    if not created:
        favorite.delete()
        is_favorite = False
        message = 'Beat removed from favorites'
    else:
        is_favorite = True
        message = 'Beat added to favorites'
    
    return JsonResponse({
        'status': 'success',
        'message': message,
        'is_favorite': is_favorite
    })
