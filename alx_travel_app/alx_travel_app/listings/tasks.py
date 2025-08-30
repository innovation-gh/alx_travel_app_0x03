# listings/tasks.py

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_booking_confirmation_email(self, booking_id, user_email, listing_title, check_in_date, check_out_date):
    """
    Send booking confirmation email asynchronously
    """
    try:
        # Email subject
        subject = f'Booking Confirmation - {listing_title}'
        
        # Create email context
        context = {
            'booking_id': booking_id,
            'listing_title': listing_title,
            'check_in_date': check_in_date,
            'check_out_date': check_out_date,
            'user_email': user_email,
        }
        
        # Render HTML email template
        html_message = render_to_string('emails/booking_confirmation.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f'Booking confirmation email sent successfully to {user_email}')
        return f'Email sent successfully to {user_email}'
        
    except Exception as exc:
        logger.error(f'Failed to send booking confirmation email: {str(exc)}')
        # Retry the task
        raise self.retry(exc=exc, countdown=60, max_retries=3)

@shared_task
def send_booking_reminder_email(booking_id, user_email, listing_title, check_in_date):
    """
    Send booking reminder email (can be scheduled for later)
    """
    try:
        subject = f'Booking Reminder - {listing_title}'
        
        context = {
            'booking_id': booking_id,
            'listing_title': listing_title,
            'check_in_date': check_in_date,
            'user_email': user_email,
        }
        
        html_message = render_to_string('emails/booking_reminder.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f'Booking reminder email sent successfully to {user_email}')
        return f'Reminder email sent successfully to {user_email}'
        
    except Exception as exc:
        logger.error(f'Failed to send booking reminder email: {str(exc)}')
        raise exc