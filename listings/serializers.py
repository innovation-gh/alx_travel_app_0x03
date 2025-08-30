from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Listing, Booking
from django.utils import timezone


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']


class ListingSerializer(serializers.ModelSerializer):
    """Serializer for Listing model."""
    host = UserSerializer(read_only=True)
    host_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'description', 'location', 'price_per_night',
            'availability', 'host', 'host_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'host']

    def validate_price_per_night(self, value):
        """Validate that price per night is positive."""
        if value <= 0:
            raise serializers.ValidationError("Price per night must be greater than 0.")
        return value

    def validate_title(self, value):
        """Validate title length."""
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters long.")
        return value.strip()

    def validate_description(self, value):
        """Validate description length."""
        if len(value.strip()) < 20:
            raise serializers.ValidationError("Description must be at least 20 characters long.")
        return value.strip()


class BookingSerializer(serializers.ModelSerializer):
    """Serializer for Booking model."""
    guest = UserSerializer(read_only=True)
    guest_id = serializers.IntegerField(write_only=True, required=False)
    listing = ListingSerializer(read_only=True)
    listing_id = serializers.IntegerField(write_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    nights = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'listing', 'listing_id', 'guest', 'guest_id',
            'start_date', 'end_date', 'total_price', 'nights',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'guest', 'total_price', 'nights']

    def validate_start_date(self, value):
        """Validate that start date is not in the past."""
        if value < timezone.now().date():
            raise serializers.ValidationError("Start date cannot be in the past.")
        return value

    def validate_end_date(self, value):
        """Validate that end date is not in the past."""
        if value < timezone.now().date():
            raise serializers.ValidationError("End date cannot be in the past.")
        return value

    def validate(self, data):
        """Validate booking data."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        listing_id = data.get('listing_id')

        # Validate date range
        if start_date and end_date:
            if start_date >= end_date:
                raise serializers.ValidationError("End date must be after start date.")
            
            # Check if booking is for more than 365 days
            if (end_date - start_date).days > 365:
                raise serializers.ValidationError("Booking cannot exceed 365 days.")

        # Validate listing availability
        if listing_id:
            try:
                listing = Listing.objects.get(id=listing_id)
                if not listing.availability:
                    raise serializers.ValidationError("This listing is not available for booking.")
                
                # Check for conflicting bookings
                if start_date and end_date:
                    conflicting_bookings = Booking.objects.filter(
                        listing=listing,
                        status__in=['confirmed', 'pending'],
                        start_date__lt=end_date,
                        end_date__gt=start_date
                    )
                    
                    # Exclude current booking if updating
                    if self.instance:
                        conflicting_bookings = conflicting_bookings.exclude(id=self.instance.id)
                    
                    if conflicting_bookings.exists():
                        raise serializers.ValidationError(
                            "This listing is already booked for the selected dates."
                        )
                        
            except Listing.DoesNotExist:
                raise serializers.ValidationError("Invalid listing ID.")

        return data

    def create(self, validated_data):
        """Create a new booking and calculate total price."""
        booking = super().create(validated_data)
        booking.calculate_total_price()
        return booking

    def update(self, instance, validated_data):
        """Update booking and recalculate total price if dates changed."""
        old_start = instance.start_date
        old_end = instance.end_date
        
        booking = super().update(instance, validated_data)
        
        # Recalculate total price if dates changed
        if booking.start_date != old_start or booking.end_date != old_end:
            booking.calculate_total_price()
            
        return booking


class BookingCreateSerializer(BookingSerializer):
    """Simplified serializer for creating bookings."""
    class Meta(BookingSerializer.Meta):
        fields = ['listing_id', 'start_date', 'end_date']


class BookingStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating booking status."""
    status = serializers.ChoiceField(
        choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('canceled', 'Canceled')],
        required=True
    )

    def validate_status(self, value):
        """Validate status transition."""
        if self.instance:
            current_status = self.instance.status
            
            # Define valid status transitions
            valid_transitions = {
                'pending': ['confirmed', 'canceled'],
                'confirmed': ['canceled'],
                'canceled': []  # Cannot change from canceled
            }
            
            if value not in valid_transitions.get(current_status, []):
                raise serializers.ValidationError(
                    f"Cannot change status from {current_status} to {value}."
                )
        
        return value