from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class Listing(models.Model):
    """
    Model representing a travel listing/accommodation.
    """
    PROPERTY_TYPES = [
        ('hotel', 'Hotel'),
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('villa', 'Villa'),
        ('resort', 'Resort'),
        ('hostel', 'Hostel'),
        ('guesthouse', 'Guesthouse'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPES)
    location = models.CharField(max_length=255)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    max_guests = models.PositiveIntegerField()
    bedrooms = models.PositiveIntegerField()
    bathrooms = models.PositiveIntegerField()
    amenities = models.TextField(help_text="Comma-separated list of amenities")
    
    # Geolocation
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Images
    main_image = models.ImageField(upload_to='listings/images/', null=True, blank=True)
    
    # Availability
    is_available = models.BooleanField(default=True)
    minimum_stay = models.PositiveIntegerField(default=1, help_text="Minimum nights required")
    
    # Metadata
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['location']),
            models.Index(fields=['property_type']),
            models.Index(fields=['price_per_night']),
            models.Index(fields=['is_available']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.location}"
    
    @property
    def amenities_list(self):
        """Return amenities as a list."""
        return [amenity.strip() for amenity in self.amenities.split(',') if amenity.strip()]


class Review(models.Model):
    """
    Model representing a review for a listing.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['listing', 'reviewer']  # One review per user per listing
    
    def __str__(self):
        return f"Review by {self.reviewer.username} for {self.listing.title}"


class Booking(models.Model):
    """
    Model representing a booking for a listing.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bookings')
    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    number_of_guests = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Payment information
    payment_method = models.CharField(max_length=50, blank=True)
    payment_status = models.CharField(max_length=20, default='pending')
    
    # Special requests
    special_requests = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['check_in_date']),
            models.Index(fields=['check_out_date']),
        ]
    
    def __str__(self):
        return f"Booking by {self.guest.username} for {self.listing.title}"
    
    @property
    def duration_nights(self):
        """Calculate the number of nights for the booking."""
        return (self.check_out_date - self.check_in_date).days
    
    def clean(self):
        """Validate booking dates."""
        from django.core.exceptions import ValidationError
        
        if self.check_in_date >= self.check_out_date:
            raise ValidationError("Check-out date must be after check-in date.")
        
        if self.number_of_guests > self.listing.max_guests:
            raise ValidationError(f"Number of guests exceeds maximum allowed ({self.listing.max_guests}).")


class ListingImage(models.Model):
    """
    Model for additional images of a listing.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='listings/images/')
    caption = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"Image for {self.listing.title}"
