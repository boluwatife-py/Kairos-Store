from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import Beat, Bundle, OrderItem, Testimonial, Cart, CartItem, Order

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

@login_required
def add_to_cart(request, beat_id):
    beat = get_object_or_404(Beat, id=beat_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, beat=beat)
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f'{beat.title} added to cart!')
    return redirect('store:beats')

@login_required
def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, 'Item removed from cart!')
    return redirect('store:cart')

@login_required
def cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    context = {
        'cart': cart,
    }
    return render(request, 'cart.html', context)

@login_required
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
        messages.success(request, 'Order placed successfully!')
        return redirect('store:dashboard')
    
    context = {
        'cart': cart,
    }
    return render(request, 'checkout.html', context)

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('store:home')
    else:
        form = UserCreationForm()
    return render(request, 'store/register.html', {'form': form})

def terms(request):
    return render(request, 'store/terms.html')

def privacy(request):
    return render(request, 'store/privacy.html')
