document.addEventListener('DOMContentLoaded', function() {
    const cartModal = document.getElementById('cartModal');
    const cartButton = document.getElementById('cartButton');
    const mobileCartButton = document.querySelector('.mobile-cart-button');
    const mobileCartCount = document.querySelector('.mobile-cart-count');
    const closeCartButton = document.getElementById('closeCartButton');
    const cartOverlay = document.getElementById('cartOverlay');
    const cartSidebar = document.getElementById('cartSidebar');
    const cartItemsContainer = document.querySelector('#cartModal .overflow-y-auto');
    const cartCount = document.querySelector('#cartButton span');
    const cartTitle = document.querySelector('#cartModal h2');
    const subtotalElement = document.querySelector('#cartModal .text-white.font-medium');
    const totalElement = document.querySelector('#cartModal .text-primary.font-bold');
    const checkoutButton = document.getElementById('checkoutButton');
    const continueShoppingButton = document.getElementById('continueShoppingButton');
    const mobileMenu = document.getElementById('mobileMenu');

    // Cart state management
    let cartState = {
        items: [],
        total_price: 0,
        isLoading: false
    };

    // Load cart count on page load
    loadCartCount();

    // Open cart
    async function openCart() {
        try {
            const response = await fetch('/api/cart/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            const data = await response.json();
            
            if (response.status === 401 && data.requires_auth) {
                // Update URL and show login modal with /cart/ as next parameter
                const url = new URL(window.location);
                url.searchParams.delete('show_modal');
                url.pathname = '/login/';
                url.searchParams.set('next', '/cart/');
                window.history.pushState({}, '', url);
                showLoginModal();
                return;
            }
            
            if (cartModal && cartSidebar) {
                // If mobile menu is open, close it first
                if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
                    mobileMenu.classList.add('hidden');
                    const mobileMenuButton = document.getElementById('mobileMenuButton');
                    if (mobileMenuButton) {
                        const icon = mobileMenuButton.querySelector('i');
                        icon.classList.remove('ri-close-line');
                        icon.classList.add('ri-menu-line');
                    }
                }
                
                cartModal.classList.remove('hidden');
                setTimeout(() => {
                    cartSidebar.classList.remove('translate-x-full');
                }, 10);
                loadCart();
            }
        } catch (error) {
            if (!error.message?.includes('Unauthorized')) {
                showToast('An error occurred while opening the cart', 'error');
            }
        }
    }

    if (cartButton) {
        cartButton.addEventListener('click', openCart);
    }
    if (mobileCartButton) {
        mobileCartButton.addEventListener('click', (e) => {
            e.preventDefault();
            openCart();
        });
    }

    // Close cart
    function closeCart() {
        if (cartSidebar && cartModal) {
            cartSidebar.classList.add('translate-x-full');
            setTimeout(() => {
                cartModal.classList.add('hidden');
            }, 300);
        }
    }

    if (closeCartButton) {
        closeCartButton.addEventListener('click', closeCart);
    }
    if (cartOverlay) {
        cartOverlay.addEventListener('click', closeCart);
    }
    if (continueShoppingButton) {
        continueShoppingButton.addEventListener('click', closeCart);
    }

    // Handle escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && cartModal && !cartModal.classList.contains('hidden')) {
            closeCart();
        }
    });

    // Show loading state
    function showLoading() {
        cartState.isLoading = true;
        if (cartItemsContainer) {
            cartItemsContainer.innerHTML = `
                <div class="flex flex-col items-center justify-center py-8 sm:py-12">
                    <div class="animate-spin rounded-full h-8 w-8 sm:h-12 sm:w-12 border-b-2 border-primary"></div>
                    <p class="text-gray-400 text-sm sm:text-base mt-3 sm:mt-4">Loading your cart...</p>
                </div>
            `;
        }
        if (checkoutButton) {
            checkoutButton.disabled = true;
            checkoutButton.classList.add('opacity-50', 'cursor-not-allowed');
        }
    }

    // Hide loading state
    function hideLoading() {
        cartState.isLoading = false;
        if (checkoutButton && cartState.items.length > 0) {
            checkoutButton.disabled = false;
            checkoutButton.classList.remove('opacity-50', 'cursor-not-allowed');
        }
    }

    // Get CSRF token
    function getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!token) {
            throw new Error('CSRF token not found');
        }
        return token;
    }

    // Load cart count
    async function loadCartCount() {
        try {
            // Try to get count from local storage first
            const cachedCount = localStorage.getItem('cartCount');
            if (cachedCount && cartCount) {
                updateCartCount(parseInt(cachedCount));
            }

            const response = await fetch('/api/cart/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            const data = await response.json();
            
            if (response.status === 401 && data.requires_auth) {
                return;
            }
            
            if (response.ok) {
                updateCartCount(data.cart_count);
                localStorage.setItem('cartCount', data.cart_count);
            }
        } catch (error) {
            // Silently fail for cart count errors
            return;
        }
    }

    // Update cart count
    function updateCartCount(count) {
        // Update desktop cart count
        if (cartCount) {
        if (count > 0) {
            cartCount.textContent = count;
            cartCount.classList.remove('hidden');
        } else {
            cartCount.classList.add('hidden');
            }
        }

        // Update mobile cart count
        if (mobileCartCount) {
            if (count > 0) {
                mobileCartCount.textContent = count;
                mobileCartCount.classList.remove('hidden');
            } else {
                mobileCartCount.classList.add('hidden');
            }
        }
    }

    // Load cart data
    async function loadCart() {
        try {
            showLoading();
            const response = await fetch('/api/cart/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            const data = await response.json();
            
            if (response.status === 401 && data.requires_auth) {
                // Store current path for next parameter
                const currentPath = window.location.pathname + window.location.search;
                // Show login modal
                const loginModal = document.getElementById('loginModal');
                if (loginModal) {
                    // Set the next URL in the form
                    const nextInput = loginModal.querySelector('input[name="next"]');
                    if (nextInput) {
                        nextInput.value = currentPath;
                    }
                    loginModal.classList.remove('hidden');
                    // Close cart modal
                    closeCart();
                }
                return;
            }
            
            if (response.ok) {
                cartState.items = data.cart_items;
                cartState.total_price = data.total_price;
                updateCartUI({
                    items: data.cart_items,
                    total_price: data.total_price
                });
                localStorage.setItem('cartCount', data.cart_count);
            } else {
                showToast(data.message || 'Error loading cart', 'error');
                showEmptyCart();
            }
        } catch (error) {
            if (!error.message?.includes('Unauthorized')) {
                showToast('An error occurred while loading the cart', 'error');
                showEmptyCart();
            }
        } finally {
            hideLoading();
        }
    }

    // Show empty cart
    function showEmptyCart() {
        if (cartItemsContainer) {
            cartItemsContainer.innerHTML = `
                <div class="flex flex-col items-center justify-center py-8 sm:py-12 text-center">
                    <i class="ri-shopping-cart-line text-3xl sm:text-4xl text-gray-400 mb-3 sm:mb-4"></i>
                    <p class="text-gray-400 text-sm sm:text-base">Your cart is empty</p>
                    <p class="text-gray-500 text-xs sm:text-sm mt-1 sm:mt-2">Add some beats to your cart to get started</p>
                </div>
            `;
        }
        if (checkoutButton) {
            checkoutButton.disabled = true;
            checkoutButton.classList.add('opacity-50', 'cursor-not-allowed');
        }
        if (subtotalElement) {
            subtotalElement.textContent = '$0.00';
        }
        if (totalElement) {
            totalElement.textContent = '$0.00';
        }
    }

    // Update cart UI
    function updateCartUI(cartData) {
        // Update cart count
        updateCartCount(cartData.items.length);
        if (cartTitle) {
            cartTitle.textContent = `Your Cart (${cartData.items.length})`;
        }

        // Clear existing items
        if (cartItemsContainer) {
            cartItemsContainer.innerHTML = '';

            if (cartData.items.length === 0) {
                showEmptyCart();
                return;
            }

            // Add cart items
            cartData.items.forEach(item => {
                const itemElement = createCartItemElement(item);
                if (itemElement) {
                    cartItemsContainer.appendChild(itemElement);
                }
            });
        }

        // Enable/disable checkout button based on cart items
        if (checkoutButton) {
            if (cartData.items.length === 0) {
                console.log('Setting button to disabled in updateCartUI');
                checkoutButton.disabled = true;
                checkoutButton.classList.add('opacity-50', 'cursor-not-allowed');
            } else {
                checkoutButton.disabled = false;
                checkoutButton.classList.remove('opacity-50', 'cursor-not-allowed');
            }
        }

        // Update totals
        if (subtotalElement) {
            subtotalElement.textContent = `$${cartData.total_price.toFixed(2)}`;
        }
        if (totalElement) {
            totalElement.textContent = `$${cartData.total_price.toFixed(2)}`;
        }
    }

    // Create cart item element
    function createCartItemElement(item) {
        if (!item) return null;

        const div = document.createElement('div');
        div.className = 'flex items-center mb-3 sm:mb-6 pb-3 sm:pb-6 border-b border-gray-800 gap-3 sm:gap-4';
        
        if (item.type === 'beat') {
            div.innerHTML = `
                <div class="w-12 h-12 sm:w-16 sm:h-16 bg-gray-800 rounded flex-shrink-0">
                    <img src="${item.image_url}" alt="${item.title}" class="w-full h-full object-cover rounded" />
                </div>
                <div class="flex-grow min-w-0">
                    <h4 class="text-white font-medium text-sm sm:text-base truncate">${item.title}</h4>
                    <p class="text-gray-400 text-xs sm:text-sm">${item.genre} • ${item.bpm} BPM</p>
                </div>
                <div class="flex items-center gap-2 sm:gap-4 flex-shrink-0">
                    <span class="text-primary font-bold text-sm sm:text-base">$${item.price.toFixed(2)}</span>
                    <button 
                        onclick="removeFromCart(${item.id})"
                        class="w-7 h-7 sm:w-8 sm:h-8 flex items-center justify-center text-gray-400 hover:text-white transition-colors"
                    >
                        <i class="ri-delete-bin-line text-lg sm:ri-lg"></i>
                    </button>
                </div>
            `;
        } else if (item.type === 'bundle') {
            div.innerHTML = `
                <div class="w-12 h-12 sm:w-16 sm:h-16 bg-gray-800 rounded flex-shrink-0">
                    <img src="${item.image_url}" alt="${item.title}" class="w-full h-full object-cover rounded" />
                </div>
                <div class="flex-grow min-w-0">
                    <h4 class="text-white font-medium text-sm sm:text-base truncate">${item.title}</h4>
                    <p class="text-gray-400 text-xs sm:text-sm">Bundle</p>
                </div>
                <div class="flex items-center gap-2 sm:gap-4 flex-shrink-0">
                    <span class="text-primary font-bold text-sm sm:text-base">$${item.price.toFixed(2)}</span>
                    <button 
                        onclick="removeFromCart(${item.id})"
                        class="w-7 h-7 sm:w-8 sm:h-8 flex items-center justify-center text-gray-400 hover:text-white transition-colors"
                    >
                        <i class="ri-delete-bin-line text-lg sm:ri-lg"></i>
                    </button>
                </div>
            `;
        }
        return div;
    }

    // Debounce function
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Remove item from cart
    window.removeFromCart = debounce(async function(cartItemId) {
        try {
            showLoading();
            const response = await fetch(`/remove-from-cart/${cartItemId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const data = await response.json();
            
            if (response.status === 401 && data.requires_auth) {
                // Store current path for next parameter
                const currentPath = window.location.pathname + window.location.search;
                // Update URL and show login modal
                const url = new URL(window.location);
                url.searchParams.delete('show_modal');
                url.pathname = '/login/';
                url.searchParams.set('next', currentPath);
                window.history.pushState({}, '', url);
                showLoginModal();
                return;
            }
            
            if (response.ok) {
                showToast(data.message);
                loadCart(); // Reload cart after removal
            } else {
                showToast(data.message || 'Error removing item', 'error');
            }
        } catch (error) {
            if (!error.message?.includes('Unauthorized')) {
                showToast('An error occurred while removing the item', 'error');
            }
        } finally {
            hideLoading();
        }
    }, 300);

    // Handle checkout
    if (checkoutButton) {
        checkoutButton.addEventListener('click', debounce(async function(e) {
            // Browser should prevent clicks on disabled button, but double-check
            if (checkoutButton.disabled || cartState.items.length === 0) {
                console.log('Preventing checkout - button disabled or cart empty');
                e.preventDefault();
                return;
            }

            try {
                showLoading();
                const response = await fetch('/create-order/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCSRFToken(),
                        'Content-Type': 'application/json'
                    }
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showToast(data.message);
                    closeCart();
                    // Clear cart state
                    cartState = { items: [], total_price: 0 };
                    localStorage.removeItem('cartCount');
                    loadCartCount();
                    // Navigate to checkout page
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    }
                } else {
                    showToast(data.message || 'Error during checkout', 'error');
                }
            } catch (error) {
                console.error('Checkout error:', error);
                showToast('An error occurred during checkout', 'error');
            } finally {
                hideLoading();
            }
        }, 300));
    }
});