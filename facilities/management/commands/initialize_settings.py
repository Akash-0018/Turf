from django.core.management.base import BaseCommand
from facilities.models import SiteSettings

class Command(BaseCommand):
    help = 'Initialize site settings'

    def handle(self, *args, **kwargs):
        if not SiteSettings.objects.exists():
            SiteSettings.objects.create(
                site_name='TurfZone',
                contact_email='admin@turfzone.com',
                contact_phone='+91 1234567890',
                about_us='Welcome to TurfZone',
                booking_time_limit=15,  # minutes
                cancellation_time_limit=24,  # hours
                max_advance_booking_days=30,
                maintenance_mode=False
            )
            self.stdout.write(self.style.SUCCESS('Successfully initialized site settings'))