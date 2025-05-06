// Helper function to get CSRF token
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function handleAddBundleToCart(bundleId, bundleTitle) {
  fetch(`/add-to-cart/bundle/${bundleId}/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest'
    },
  })
  .then(async response => {
    const data = await response.json();
    
    if (!response.ok) {
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
        throw new Error('Unauthorized');
      }
      throw new Error(data.message || 'Error adding bundle to cart');
    }
    
    if (data.status === 'success') {
      showToast(data.message, 'success');
      return fetch('/api/cart/', {
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      }).then(response => response.json());
    } else {
      throw new Error(data.message || 'Error adding bundle to cart');
    }
  })
  .then(cartData => {
    // Update desktop cart count
    const cartBadge = document.querySelector('#cartButton span');
    if (cartBadge) {
      cartBadge.textContent = cartData.cart_count;
      cartBadge.classList.remove('hidden');
    }
    // Update mobile cart count
    const mobileCartCount = document.querySelector('.mobile-cart-count');
    if (mobileCartCount) {
      mobileCartCount.textContent = cartData.cart_count;
      mobileCartCount.classList.remove('hidden');
    }
  })
  .catch(error => {
    if (error.message !== 'Unauthorized') {
      showToast(error.message || 'An error occurred. Please try again.', 'error');
    }
  });
}

// Function to update cart count
function updateCartCount() {
  fetch('/api/cart/')
    .then(response => response.json())
    .then(data => {
      const cartCount = data.cart_count;
      const cartCountElements = document.querySelectorAll('[data-cart-count]');
      cartCountElements.forEach(element => {
        element.textContent = cartCount;
        if (cartCount > 0) {
          element.classList.remove('hidden');
        } else {
          element.classList.add('hidden');
        }
      });
      
      const cartCountElement = document.getElementById('cartCount');
      if (cartCountElement) {
        cartCountElement.textContent = cartCount;
        if (cartCount > 0) {
          cartCountElement.classList.remove('hidden');
        } else {
          cartCountElement.classList.add('hidden');
        }
      }
    })
    .catch(error => {});
}

// Handle equalizer animation for bundles
document.addEventListener('DOMContentLoaded', function() {
  window.addEventListener('bundlePlayerStateChange', function(e) {
    const { bundleId, isPlaying } = e.detail;
    const equalizer = document.querySelector(`.equalizer[data-bundle-id="${bundleId}"]`);
    if (equalizer) {
      if (isPlaying) {
        equalizer.classList.add('playing');
      } else {
        equalizer.classList.remove('playing');
      }
    }
    
    // Remove playing class from other equalizers
    document.querySelectorAll('.equalizer').forEach(eq => {
      if (eq.dataset.bundleId !== bundleId) {
        eq.classList.remove('playing');
      }
    });
  });
}); 