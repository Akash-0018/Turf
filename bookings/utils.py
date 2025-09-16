from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

def send_booking_notification_to_admin(booking):
    """Send a notification email to admin when a new booking is made"""
    subject = f'New Booking Alert - {booking.facility_sport.facility.name}'
    message = render_to_string('emails/admin_booking_notification.html', {
        'booking': booking,
    })
    send_mail(
        subject=subject,
        message=message,
        html_message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ADMIN_EMAIL],
        fail_silently=False,
    )

def send_booking_confirmation_to_user(booking):
    """Send a confirmation email to user when their booking is confirmed"""
    subject = f'Booking Confirmed - {booking.facility_sport.facility.name}'
    message = render_to_string('emails/user_booking_confirmation.html', {
        'booking': booking,
    })
    send_mail(
        subject=subject,
        message=message,
        html_message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[booking.user.email],
        fail_silently=False,
    )