from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ListingViewSet, BookingViewSet

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'listings', ListingViewSet, basename='listing')
router.register(r'bookings', BookingViewSet, basename='booking')

app_name = 'listings'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
]

# The router automatically creates the following URL patterns:
# 
# Listing endpoints:
# GET    /api/listings/                    - List all listings
# POST   /api/listings/                    - Create a new listing
# GET    /api/listings/{id}/               - Retrieve a specific listing
# PUT    /api/listings/{id}/               - Update a specific listing (full)
# PATCH  /api/listings/{id}/               - Update a specific listing (partial)
# DELETE /api/listings/{id}/               - Delete a specific listing
# GET    /api/listings/available/          - Get available listings
# GET    /api/listings/my_listings/        - Get current user's listings
#
# Booking endpoints:
# GET    /api/bookings/                    - List all bookings (filtered by user)
# POST   /api/bookings/                    - Create a new booking
# GET    /api/bookings/{id}/               - Retrieve a specific booking
# PUT    /api/bookings/{id}/               - Update a specific booking (full)
# PATCH  /api/bookings/{id}/               - Update a specific booking (partial)
# DELETE /api/bookings/{id}/               - Delete a specific booking
# GET    /api/bookings/my_bookings/        - Get current user's bookings as guest
# GET    /api/bookings/host_bookings/      - Get bookings for current user's listings
# PATCH  /api/bookings/{id}/update_status/ - Update booking status