import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Booking, Payment
import uuid
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from celery import shared_task

class InitiatePaymentView(APIView):
    def post(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id, user=request.user)
            
            # Check if payment already exists
            if hasattr(booking, 'payment'):
                return Response(
                    {"error": "Payment already initiated for this booking"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Prepare Chapa payment request
            amount = booking.total_price
            email = request.user.email
            first_name = request.user.first_name
            last_name = request.user.last_name
            tx_ref = f"travel-{uuid.uuid4().hex}"
            
            headers = {
                "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "amount": str(amount),
                "currency": "ETB",
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "tx_ref": tx_ref,
                "callback_url": f"{settings.BASE_URL}/api/payments/verify/{tx_ref}/",
                "return_url": f"{settings.FRONTEND_URL}/booking/{booking_id}/status",
                "customization": {
                    "title": "ALX Travel App",
                    "description": "Payment for your booking"
                }
            }
            
            # Make request to Chapa API
            response = requests.post(
                f"{settings.CHAPA_BASE_URL}/transaction/initialize",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Create payment record
                payment = Payment.objects.create(
                    booking=booking,
                    amount=amount,
                    transaction_id=tx_ref,
                    status='pending'
                )
                
                return Response({
                    "checkout_url": data['data']['checkout_url'],
                    "message": "Payment initiated successfully"
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "Failed to initiate payment"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Booking.DoesNotExist:
            return Response(
                {"error": "Booking not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class VerifyPaymentView(APIView):
    def get(self, request, tx_ref):
        try:
            payment = Payment.objects.get(transaction_id=tx_ref)
            
            headers = {
                "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"
            }
            
            # Verify payment with Chapa
            response = requests.get(
                f"{settings.CHAPA_BASE_URL}/transaction/verify/{tx_ref}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data['status'] == 'success':
                    payment.status = 'completed'
                    payment.save()
                    
                    # Send confirmation email asynchronously
                    send_booking_confirmation.delay(payment.booking.id)
                    
                    return Response(
                        {"status": "completed", "message": "Payment verified successfully"},
                        status=status.HTTP_200_OK
                    )
                else:
                    payment.status = 'failed'
                    payment.save()
                    return Response(
                        {"status": "failed", "message": "Payment verification failed"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {"error": "Failed to verify payment"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Payment.DoesNotExist:
            return Response(
                {"error": "Payment not found"},
                status=status.HTTP_404_NOT_FOUND
            )

@shared_task
def send_booking_confirmation(booking_id):
    booking = Booking.objects.get(id=booking_id)
    user = booking.user
    subject = "Your Booking Confirmation"
    html_message = render_to_string('emails/booking_confirmation.html', {
        'user': user,
        'booking': booking
    })
    plain_message = strip_tags(html_message)
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message
    )