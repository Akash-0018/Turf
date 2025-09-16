from django.core.management.base import BaseCommand
from facilities.models import SportType

class Command(BaseCommand):
    help = 'Cleans up duplicate sport types'

    def handle(self, *args, **kwargs):
        # Get all sport names
        sport_names = SportType.objects.values_list('name', flat=True).distinct()
        
        for name in sport_names:
            # Keep the first one, delete the rest
            sports = SportType.objects.filter(name=name).order_by('id')
            if sports.count() > 1:
                first = sports.first()
                sports.exclude(id=first.id).delete()
                self.stdout.write(self.style.SUCCESS(f'Cleaned up duplicates for {name}'))
        
        self.stdout.write(self.style.SUCCESS('Sport types cleanup completed'))