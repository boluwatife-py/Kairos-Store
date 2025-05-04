// Add getCookie function
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

async function handleAddToCart(beatId, beatTitle) {
  try {
    const response = await fetch(`/add-to-cart/${beatId}/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      }
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      if (response.status === 401 && data.requires_auth) {
        showLoginModal();
        throw new Error('Unauthorized');
      }
      throw new Error(data.message || 'Error adding to cart');
    }
    
    if (data.status === 'success') {
      showToast(data.message);
      // Fetch actual cart count from server
      const cartResponse = await fetch('/api/cart/', {
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });
      const cartData = await cartResponse.json();
      const cartCount = document.querySelector('#cartButton span');
      if (cartCount) {
        cartCount.textContent = cartData.cart_count;
        cartCount.classList.remove('hidden');
      }
      // Update mobile cart count
      const mobileCartCount = document.querySelector('.mobile-cart-count');
      if (mobileCartCount) {
        mobileCartCount.textContent = cartData.cart_count;
        mobileCartCount.classList.remove('hidden');
      }
    } else {
      throw new Error(data.message || 'Error adding to cart');
    }
  } catch (error) {
    if (!error.message?.includes('Unauthorized')) {
      console.error('Error adding to cart:', error);
      showToast(error.message || 'An error occurred. Please try again.', 'error');
    }
  }
}

async function handleDownload(beatId, beatTitle) {
  try {
    const response = await fetch(`/download/${beatId}/`, {
      method: 'GET',
      headers: {
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
      }
    });
    
    if (response.ok) {
      // Create a temporary link to download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${beatTitle}.mp3`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      showToast('Download started!');
    } else {
      const data = await response.json();
      showToast(data.message || 'Error downloading beat', 'error');
    }
  } catch (error) {
    showToast('An error occurred while downloading', 'error');
  }
}

// Handle favorite button click
async function handleFavoriteClick(button) {
  const beatId = button.dataset.beatId;
  try {
    const response = await fetch(`/toggle-favorite/${beatId}/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      }
    });

    // Check if user is not authenticated
    if (response.status === 401 || response.status === 403) {
      showToast('Please login to add favorites', 'error');
      // Show login modal if it exists
      const loginModal = document.getElementById('loginModal');
      if (loginModal) {
        loginModal.classList.remove('hidden');
      } else {
        // Redirect to login page if modal doesn't exist
        window.location.href = '/login/';
      }
      return;
    }

    // Try to parse JSON response
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      throw new Error('Received non-JSON response from server');
    }

    const data = await response.json();
    if (data.status === 'success') {
      const icon = button.querySelector('i');
      if (data.is_favorite) {
        icon.classList.remove('ri-heart-line');
        icon.classList.add('ri-heart-fill', 'text-primary');
      } else {
        icon.classList.remove('ri-heart-fill', 'text-primary');
        icon.classList.add('ri-heart-line');
      }
      showToast(data.message);
    }
  } catch (error) {
    console.error('Error:', error);
    showToast('Error updating favorite status', 'error');
  }
}

// Use event delegation for favorite buttons
document.addEventListener('click', function(e) {
  const favoriteButton = e.target.closest('.favorite-button');
  if (favoriteButton) {
    handleFavoriteClick(favoriteButton);
  }
}); 