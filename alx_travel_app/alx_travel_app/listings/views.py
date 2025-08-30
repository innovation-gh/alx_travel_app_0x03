from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Listing, Review, Booking
from .serializers import ListingSerializer, ReviewSerializer, BookingSerializer
from .filters import ListingFilter


class ListingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing listings.
    
    Provides CRUD operations for travel listings with filtering and search capabilities.
    """
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ListingFilter
    search_fields = ['title', 'description', 'location', 'amenities']
    ordering_fields = ['price_per_night', 'created_at', 'title']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Optionally filter the queryset based on query parameters.
        """
        queryset = Listing.objects.all()
        
        # Filter by availability
        is_available = self.request.query_params.get('is_available', None)
        if is_available is not None:
            queryset = queryset.filter(is_available=is_available.lower() == 'true')
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        if min_price is not None:
            queryset = queryset.filter(price_per_night__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price_per_night__lte=max_price)
        
        # Filter by guest capacity
        guests = self.request.query_params.get('guests', None)
        if guests is not None:
            queryset = queryset.filter(max_guests__gte=guests)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set the host as the current user when creating a listing."""
        serializer.save(host=self.request.user)
    
    @swagger_auto_schema(
        method='get',
        responses={200: ListingSerializer(many=True)},
        operation_description="Get listings by the current user"
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_listings(self, request):
        """Get all listings owned by the current user."""
        listings = self.queryset.filter(host=request.user)
        serializer = self.get_serializer(listings, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='get',
        responses={200: openapi.Response('Average rating', openapi.Schema(type=openapi.TYPE_OBJECT))},
        operation_description="Get average rating for a listing"
    )
    @action(detail=True, methods=['get'])
    def rating(self, request, pk=None):
        """Get average rating for a specific listing."""
        listing = self.get_object()
        avg_rating = listing.reviews.aggregate(Avg('rating'))['rating__avg']
        review_count = listing.reviews.count()
        
        return Response({
            'average_rating': round(avg_rating, 2) if avg_rating else 0,
            'review_count': review_count
        })


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing reviews.
    
    Provides CRUD operations for listing reviews.
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter reviews by listing if specified."""
        queryset = Review.objects.all()
        listing_id = self.request.query_params.get('listing', None)
        if listing_id is not None:
            queryset = queryset.filter(listing_id=listing_id)
        return queryset
    
    def perform_create(self, serializer):
        """Set the reviewer as the current user when creating a review."""
        serializer.save(reviewer=self.request.user)


class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing bookings.
    
    Provides CRUD operations for listing bookings.
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'check_in_date', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter bookings based on user role."""
        user = self.request.user
        queryset = Booking.objects.all()
        
        # Users can only see their own bookings or bookings for their listings
        if not user.is_staff:
            queryset = queryset.filter(
                Q(guest=user) | Q(listing__host=user)
            )
        
        return queryset
    
    def perform_create(self, serializer):
        """Set the guest as the current user when creating a booking."""
        serializer.save(guest=self.request.user)
    
    @swagger_auto_schema(
        method='post',
        responses={200: BookingSerializer},
        operation_description="Confirm a booking"
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def confirm(self, request, pk=None):
        """Confirm a booking (only by the host)."""
        booking = self.get_object()
        
        # Check if the current user is the host of the listing
        if booking.listing.host != request.user:
            return Response(
                {'error': 'Only the host can confirm bookings'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        booking.status = 'confirmed'
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='post',
        responses={200: BookingSerializer},
        operation_description="Cancel a booking"
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def cancel(self, request, pk=None):
        """Cancel a booking."""
        booking = self.get_object()
        
        # Check if the current user is the guest or host
        if booking.guest != request.user and booking.listing.host != request.user:
            return Response(
                {'error': 'Only the guest or host can cancel bookings'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        booking.status = 'cancelled'
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)


class ListingReviewsView(APIView):
    """
    API view to get all reviews for a specific listing.
    """
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        responses={200: ReviewSerializer(many=True)},
        operation_description="Get all reviews for a specific listing"
    )
    def get(self, request, listing_id):
        """Get all reviews for a specific listing."""
        try:
            listing = Listing.objects.get(id=listing_id)
            reviews = listing.reviews.all()
            serializer = ReviewSerializer(reviews, many=True)
            return Response(serializer.data)
        except Listing.DoesNotExist:
            return Response(
                {'error': 'Listing not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class ListingBookingsView(APIView):
    """
    API view to get all bookings for a specific listing (host only).
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        responses={200: BookingSerializer(many=True)},
        operation_description="Get all bookings for a specific listing (host only)"
    )
    def get(self, request, listing_id):
        """Get all bookings for a specific listing."""
        try:
            listing = Listing.objects.get(id=listing_id)
            
            # Check if the current user is the host
            if listing.host != request.user:
                return Response(
                    {'error': 'Only the host can view bookings for this listing'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            bookings = listing.bookings.all()
            serializer = BookingSerializer(bookings, many=True)
            return Response(serializer.data)
        except Listing.DoesNotExist:
            return Response(
                {'error': 'Listing not found'},
                status=status.HTTP_404_NOT_FOUND
            )
