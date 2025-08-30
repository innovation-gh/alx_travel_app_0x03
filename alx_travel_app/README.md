# alx_travel_app_0x01

# ALX Travel App 0x01 - API Development

A Django REST API for managing travel listings and bookings with comprehensive CRUD operations, filtering, search, and Swagger documentation.

## Features

### 🏠 Listing Management
- **CRUD Operations**: Create, Read, Update, Delete listings
- **Search & Filter**: Search by title/description, filter by location, price, availability
- **Custom Endpoints**: 
  - `/api/listings/available/` - Get available listings with date filtering
  - `/api/listings/my_listings/` - Get current user's listings

### 📅 Booking Management
- **CRUD Operations**: Complete booking lifecycle management
- **Status Management**: Pending → Confirmed/Canceled workflow
- **Custom Endpoints**:
  - `/api/bookings/my_bookings/` - User's bookings as guest
  - `/api/bookings/host_bookings/` - Bookings for user's listings
  - `/api/bookings/{id}/update_status/` - Update booking status

### 📚 API Documentation
- **Swagger UI**: Interactive API documentation at `/swagger/`
- **ReDoc**: Alternative documentation at `/redoc/`
- **Schema Export**: JSON schema available at `/swagger.json`

## Project Structure

```
alx_travel_app_0x01/
├── alx_travel_app/
│   ├── __init__.py
│   ├── settings.py          # Django settings with DRF configuration
│   ├── urls.py              # Main URL configuration with Swagger
│   └── wsgi.py
├── listings/
│   ├── __init__.py
│   ├── admin.py             # Django admin configuration
│   ├── models.py            # Listing and Booking models
│   ├── serializers.py       # DRF serializers with validation
│   ├── views.py             # API ViewSets with custom actions
│   └── urls.py              # API URL routing with router
├── requirements.txt         # Project dependencies
├── test_api_endpoints.py    # Automated API testing script
└── README.md               # This file
```

## Installation & Setup

### 1. Duplicate Project
```bash
# Clone or copy from alx_travel_app_0x00
cp -r alx_travel_app_0x00 alx_travel_app_0x01
cd alx_travel_app_0x01
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 4. Run Development Server
```bash
python manage.py runserver
```

## API Endpoints

### Base URL: `http://localhost:8000/api/`

### 🏠 Listings Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/listings/` | List all listings | No |
| POST | `/listings/` | Create new listing | Yes |
| GET | `/listings/{id}/` | Get listing details | No |
| PUT | `/listings/{id}/` | Update listing (full) | Yes (owner) |
| PATCH | `/listings/{id}/` | Update listing (partial) | Yes (owner) |
| DELETE | `/listings/{id}/` | Delete listing | Yes (owner) |
| GET | `/listings/available/` | Get available listings | No |
| GET | `/listings/my_listings/` | Get user's listings | Yes |

#### Listing Query Parameters
- `search`: Search in title, description, location
- `location`: Filter by location
- `price_per_night`: Filter by price
- `availability`: Filter by availability (true/false)
- `ordering`: Sort by `created_at`, `price_per_night`, `title`

### 📅 Booking Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/bookings/` | List user's bookings | Yes |
| POST | `/bookings/` | Create new booking | Yes |
| GET | `/bookings/{id}/` | Get booking details | Yes (guest/host) |
| PUT | `/bookings/{id}/` | Update booking (full) | Yes (guest) |
| PATCH | `/bookings/{id}/` | Update booking (partial) | Yes (guest) |
| DELETE | `/bookings/{id}/` | Delete booking | Yes (guest) |
| GET | `/bookings/my_bookings/` | Get bookings as guest | Yes |
| GET | `/bookings/host_bookings/` | Get bookings for user's listings | Yes |
| PATCH | `/bookings/{id}/update_status/` | Update booking status | Yes (guest/host) |

#### Booking Query Parameters
- `status`: Filter by status (`pending`, `confirmed`, `canceled`)
- `listing`: Filter by listing ID
- `ordering`: Sort by `created_at`, `start_date`, `end_date`

## Request/Response Examples

### Create Listing
```bash
POST /api/listings/
Content-Type: application/json
Authorization: Basic <credentials>

{
    "title": "Beachfront Villa",
    "description": "Beautiful villa with stunning ocean views and private beach access",
    "location": "Malibu, CA",
    "price_per_night": "450.00",
    "availability": true
}
```

### Create Booking
```bash
POST /api/bookings/
Content-Type: application/json
Authorization: Basic <credentials>

{
    "listing_id": 1,
    "start_date": "2024-12-01",
    "end_date": "2024-12-05"
}
```

### Update Booking Status (Host)
```bash
PATCH /api/bookings/1/update_status/
Content-Type: application/json
Authorization: Basic <credentials>

{
    "status": "confirmed"
}
```

## Testing

### Automated Testing
Run the included test script:
```bash
python test_api_endpoints.py
```

### Manual Testing with cURL

#### Get All Listings
```bash
curl -X GET http://localhost:8000/api/listings/
```

#### Create Listing (requires authentication)
```bash
curl -X POST http://localhost:8000/api/listings/ \
  -H "Content-Type: application/json" \
  -u username:password \
  -d '{
    "title": "Test Listing",
    "description": "A test listing for API demonstration",
    "location": "Test City",
    "price_per_night": "100.00",
    "availability": true
  }'
```

#### Search Listings
```bash
curl -X GET "http://localhost:8000/api/listings/?search=beach&location=Miami"
```

### Testing with Postman

1. **Import Collection**: Create a new Postman collection
2. **Set Base URL**: `http://localhost:8000/api`
3. **Authentication**: Use Basic Auth with your Django superuser credentials
4. **Test Endpoints**: Follow the endpoint documentation above

## Authentication

The API uses Django's built-in authentication:
- **Session Authentication**: For web browsers
- **Basic Authentication**: For API clients
- **Permissions**: 
  - Listings: Read-only for anonymous, full CRUD for authenticated users
  - Bookings: Requires authentication, users can only access their own bookings

## Validation & Business Logic

### Listing Validation
- Title: Minimum 5 characters
- Description: Minimum 20 characters
- Price: Must be positive
- Auto-assign authenticated user as host

### Booking Validation
- Dates: Start/end dates cannot be in the past
- Date Range: End date must be after start date
- Availability: Check listing availability and conflicts
- Auto-calculate total price based on nights × price_per_night
- Status transitions: pending → confirmed/canceled, confirmed → canceled

## API Documentation

### Swagger UI
Visit `http://localhost:8000/swagger/` for interactive API documentation where you can:
- View all endpoints and their parameters
- Test endpoints directly in the browser
- See request/response schemas
- Authenticate and try protected endpoints

### ReDoc
Visit `http://localhost:8000/redoc/` for clean, readable API documentation.

## Error Handling

The API returns appropriate HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request (validation errors)
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error

Error responses include detailed messages:
```json
{
    "error": "This listing is already booked for the selected dates.",
    "field_errors": {
        "start_date": ["Start date cannot be in the past."]
    }
}
```

## Development Notes

### Key Technologies
- **Django 4.2+**: Web framework
- **Django REST Framework**: API framework
- **drf-yasg**: Swagger/OpenAPI documentation
- **django-filter**: Advanced filtering
- **django-cors-headers**: CORS support

### Performance Optimizations
- Database indexes on commonly queried fields
- `select_related()` for foreign key queries
- Pagination for list endpoints
- Efficient queryset filtering

### Security Features
- Authentication required for sensitive operations
- Permission-based access control
- CSRF protection
- Input validation and sanitization

## Next Steps

1. **Authentication Enhancement**: Add JWT token authentication
2. **File Uploads**: Add image upload for listings
3. **Email Notifications**: Send booking confirmations
4. **Payment Integration**: Add payment processing
5. **Advanced Search**: Geographic search, amenity filtering
6. **Rate Limiting**: Implement API rate limiting
7. **Caching**: Add Redis for better performance

## Repository Information

- **GitHub Repository**: `alx_travel_app_0x01`
- **Directory**: `alx_travel_app`
- **Key Files**: 
  - `listings/views.py` - API ViewSets
  - `listings/urls.py` - URL configuration
  - `README.md` - This documentation