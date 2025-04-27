from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.http import JsonResponse
from functools import wraps
from .models import Beat, Bundle, OrderItem, Testimonial, Cart, CartItem, Order
from .forms import CustomUserCreationForm

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
    featured_beats = Beat.objects.filter(is_featured=True)[:3]
    new_releases = Beat.objects.filter(is_new_release=True)[:3]
    bundles = Bundle.objects.all()[:2]
    testimonials = Testimonial.objects.all()[:3]

    context = {
        'featured_beats': featured_beats,
        'new_releases': new_releases,
        'bundles': bundles,
        'testimonials': testimonials,
    }
    return render(request, 'home.html', context)

def beats(request):
    beats = Beat.objects.all()
    context = {
        'beats': beats,
    }
    return render(request, 'beats.html', context)

@login_required
def dashboard(request):
    user_orders = Order.objects.filter(user=request.user)
    context = {
        'orders': user_orders,
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
    context = {
        'cart': cart,
    }
    return render(request, 'cart.html', context)

@login_required_json
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    if request.method == 'POST':
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
            'message': 'Order placed successfully!'
        })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)

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
