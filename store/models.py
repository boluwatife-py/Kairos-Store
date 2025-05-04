from django.db import models
from django.contrib.auth.models import User, AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver
from cloudinary.models import CloudinaryField
from datetime import timedelta

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

class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='userprofile')
    bio = models.TextField(blank=True, null=True)
    email_notifications = models.BooleanField(default=True)
    order_updates = models.BooleanField(default=True)
    new_releases = models.BooleanField(default=True)
    promotions = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.email}"

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

class Beat(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    genre = models.CharField(max_length=100)
    bpm = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = CloudinaryField('image', folder='beats/images', null=True, blank=True, 
                          transformation={'quality': 'auto:good'})
    sample_audio = CloudinaryField('audio', folder='beats/samples', null=True, blank=True, 
                                 resource_type='video', help_text='30-second sample preview')
    full_audio = CloudinaryField('audio', folder='beats/full', null=True, blank=True, 
                               resource_type='video', help_text='Full track for purchase')
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
    image = CloudinaryField('image', folder='bundles', null=True, blank=True)
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
    beat = models.ForeignKey(Beat, on_delete=models.CASCADE, null=True, blank=True)
    bundle = models.ForeignKey(Bundle, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('cart', 'beat'), ('cart', 'bundle')]

    @property
    def total_price(self):
        if self.beat:
            return self.beat.price * self.quantity
        elif self.bundle:
            return self.bundle.discounted_price * self.quantity
        return 0

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('overruled', 'Overruled - Contains Purchased Items'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    beats = models.ManyToManyField(Beat, through='OrderItem')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.email}"

    def check_for_purchased_items(self):
        """Check if any items in the order have already been purchased"""
        purchased_items = []
        for item in self.orderitem_set.all():
            if item.beat:
                # Check if individual beat is already purchased
                if OrderItem.objects.filter(
                    order__user=self.user,
                    order__status='completed',
                    beat=item.beat
                ).exists():
                    purchased_items.append(item.beat.title)
            elif item.bundle:
                # Check each beat in the bundle
                bundle_purchased_beats = []
                for beat in item.bundle.beats.all():
                    if OrderItem.objects.filter(
                        order__user=self.user,
                        order__status='completed',
                        beat=beat
                    ).exists():
                        bundle_purchased_beats.append(beat.title)
                if bundle_purchased_beats:
                    purchased_items.append(f"Bundle '{item.bundle.title}' contains already purchased beats: {', '.join(bundle_purchased_beats)}")
        return purchased_items

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    beat = models.ForeignKey(Beat, on_delete=models.CASCADE, null=True, blank=True)
    bundle = models.ForeignKey(Bundle, on_delete=models.CASCADE, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        if self.beat:
            return f"{self.quantity}x {self.beat.title} in Order #{self.order.id}"
        return f"{self.quantity}x {self.bundle.title} (Bundle) in Order #{self.order.id}"

class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    beat = models.ForeignKey(Beat, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'beat')

    def __str__(self):
        return f"{self.user.email} - {self.beat.title}"

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    def is_valid(self):
        # OTP expires after 10 minutes
        expiry_time = self.created_at + timedelta(minutes=10)
        return not self.is_used and timezone.now() <= expiry_time