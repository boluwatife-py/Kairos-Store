from django.db import models
from django.contrib.auth.models import User, AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.urls import reverse

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = CustomUserManager()
    
    def __str__(self):
        return self.email

class Beat(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    genre = models.CharField(max_length=100)
    bpm = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='beats/images/', null=True, blank=True)
    sample_audio = models.FileField(upload_to='beats/samples/', help_text='30-second sample preview')
    full_audio = models.FileField(upload_to='beats/full/', help_text='Full track for purchase')
    is_featured = models.BooleanField(default=False)
    is_new_release = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    _user = None

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

    def get_image_url(self):
        if self.image:
            return self.image.url
        return '/static/images/default-beat.jpg'

    def get_sample_url(self):
        if self.sample_audio:
            return self.sample_audio.url
        return None

    def get_full_audio_url(self):
        if self.full_audio:
            return self.full_audio.url
        return None

    @property
    def is_purchased(self):
        if not self._user or not self._user.is_authenticated:
            return False
        return OrderItem.objects.filter(
            order__user=self._user,
            beat=self,
            order__status='completed'
        ).exists()

    @property
    def is_favorite(self):
        if not self._user or not self._user.is_authenticated:
            return False
        return Favorite.objects.filter(
            user=self._user,
            beat=self
        ).exists()

    def set_user(self, user):
        self._user = user

class Bundle(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='bundles/')
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.IntegerField()
    beats = models.ManyToManyField(Beat)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    @property
    def beat_count(self):
        return self.beats.count()

    class Meta:
        ordering = ['-created_at']

class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    content = models.TextField()
    rating = models.DecimalField(max_digits=3, decimal_places=1)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.role}"

    class Meta:
        ordering = ['-created_at']

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    beats = models.ManyToManyField(Beat, through='CartItem')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.email}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.cartitem_set.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    beat = models.ForeignKey(Beat, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity}x {self.beat.title} in {self.cart}"

    @property
    def total_price(self):
        return self.beat.price * self.quantity

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    beats = models.ManyToManyField(Beat, through='OrderItem')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.email}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    beat = models.ForeignKey(Beat, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}x {self.beat.title} in Order #{self.order.id}"

class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    beat = models.ForeignKey(Beat, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'beat')

    def __str__(self):
        return f"{self.user.email} - {self.beat.title}"
