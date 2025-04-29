// Cart functionality
document.addEventListener('DOMContentLoaded', function() {
    const cartModal = document.getElementById('cartModal');
    const cartButton = document.getElementById('cartButton');
    const closeCartButton = document.getElementById('closeCartButton');
    const cartOverlay = document.getElementById('cartOverlay');
    const cartSidebar = document.getElementById('cartSidebar');
    const cartItemsContainer = document.querySelector('#cartModal .overflow-y-auto');
    const cartCount = document.querySelector('#cartButton span');
    const cartTitle = document.querySelector('#cartModal h2');
    const subtotalElement = document.querySelector('#cartModal .text-white.font-medium');
    const totalElement = document.querySelector('#cartModal .text-primary.font-bold.text-xl');
    const checkoutButton = document.querySelector('#cartModal button.bg-primary');
    const continueShoppingButton = document.querySelector('#cartModal button.bg-transparent');

    // Load cart count on page load
    loadCartCount();

    // Open cart
    cartButton.addEventListener('click', () => {
        cartModal.classList.remove('hidden');
        cartSidebar.classList.remove('translate-x-full');
        showLoading();
        loadCart();
    });

    // Close cart
    function closeCart() {
        cartSidebar.classList.add('translate-x-full');
        setTimeout(() => {
            cartModal.classList.add('hidden');
        }, 300);
    }

    closeCartButton.addEventListener('click', closeCart);
    cartOverlay.addEventListener('click', closeCart);

    // Show loading state
    function showLoading() {
        cartItemsContainer.innerHTML = `
            <div class="flex flex-col items-center justify-center py-12">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                <p class="text-gray-400 mt-4">Loading your cart...</p>
            </div>
        `;
        checkoutButton.disabled = true;
        checkoutButton.classList.add('opacity-50', 'cursor-not-allowed');
    }

    // Load cart count
    async function loadCartCount() {
        try {
            const response = await fetch('/cart/');
            const data = await response.json();
            
            if (response.ok) {
                updateCartCount(data.items.length);
            }
        } catch (error) {
            console.error('Error loading cart count:', error);
        }
    }

    // Update cart count
    function updateCartCount(count) {
        if (count > 0) {
            cartCount.textContent = count;
            cartCount.classList.remove('hidden');
        } else {
            cartCount.classList.add('hidden');
        }
    }

    // Load cart data
    async function loadCart() {
        try {
            const response = await fetch('/cart/');
            const data = await response.json();
            
            if (response.ok) {
                updateCartUI(data);
            } else {
                showToast(data.message || 'Error loading cart', 'error');
                showEmptyCart();
            }
        } catch (error) {
            showToast('An error occurred while loading the cart', 'error');
            showEmptyCart();
        }
    }

    // Show empty cart
    function showEmptyCart() {
        cartItemsContainer.innerHTML = `
            <div class="flex flex-col items-center justify-center py-12 text-center">
                <i class="ri-shopping-cart-line text-4xl text-gray-400 mb-4"></i>
                <p class="text-gray-400">Your cart is empty</p>
                <p class="text-gray-500 text-sm mt-2">Add some beats to your cart to get started</p>
            </div>
        `;
        checkoutButton.disabled = true;
        checkoutButton.classList.add('opacity-50', 'cursor-not-allowed');
        subtotalElement.textContent = '$0.00';
        totalElement.textContent = '$0.00';
    }

    // Update cart UI
    function updateCartUI(cartData) {
        // Update cart count
        updateCartCount(cartData.items.length);
        cartTitle.textContent = `Your Cart (${cartData.items.length})`;

        // Clear existing items
        cartItemsContainer.innerHTML = '';

        if (cartData.items.length === 0) {
            showEmptyCart();
            return;
        }

        // Enable checkout button
        checkoutButton.disabled = false;
        checkoutButton.classList.remove('opacity-50', 'cursor-not-allowed');

        // Add cart items
        cartData.items.forEach(item => {
            const itemElement = createCartItemElement(item);
            cartItemsContainer.appendChild(itemElement);
        });

        // Update totals
        subtotalElement.textContent = `$${cartData.total_price.toFixed(2)}`;
        totalElement.textContent = `$${cartData.total_price.toFixed(2)}`;
    }

    // Create cart item element
    function createCartItemElement(item) {
        const div = document.createElement('div');
        div.className = 'flex items-center mb-6 pb-6 border-b border-gray-800';
        div.innerHTML = `
            <div class="w-16 h-16 bg-gray-800 rounded flex-shrink-0 mr-4">
                <img src="${item.beat.image_url}" alt="${item.beat.title}" class="w-full h-full object-cover rounded" />
            </div>
            <div class="flex-grow">
                <h4 class="text-white font-medium">${item.beat.title}</h4>
                <p class="text-gray-400 text-sm">${item.beat.genre} • ${item.beat.bpm} BPM</p>
            </div>
            <div class="flex items-center">
                <span class="text-primary font-bold mr-4">$${item.beat.price.toFixed(2)}</span>
                <button 
                    onclick="removeFromCart(${item.id})"
                    class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-white transition-colors"
                >
                    <i class="ri-delete-bin-line"></i>
                </button>
            </div>
        `;
        return div;
    }

    // Remove item from cart
    window.removeFromCart = async function(cartItemId) {
        try {
            showLoading();
            const response = await fetch(`/cart/remove/${cartItemId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showToast(data.message);
                loadCart(); // Reload cart after removal
                loadCartCount(); // Update cart count
            } else {
                showToast(data.message || 'Error removing item', 'error');
            }
        } catch (error) {
            showToast('An error occurred while removing the item', 'error');
        }
    };

    // Handle checkout
    checkoutButton.addEventListener('click', async function() {
        try {
            showLoading();
            const response = await fetch('/checkout/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showToast(data.message);
                closeCart();
                loadCartCount(); // Update cart count after checkout
                // Redirect to orders page or show success message
            } else {
                showToast(data.message || 'Error during checkout', 'error');
            }
        } catch (error) {
            showToast('An error occurred during checkout', 'error');
        }
    });

    // Handle continue shopping
    continueShoppingButton.addEventListener('click', () => {
        closeCart();
        window.location.href = '/beats/';
    });
}); 