from .models import SiteSettings

def site_settings(request):
    """Context processor to make site settings available in all templates."""
    try:
        settings = SiteSettings.objects.get(pk=1)
        return {
            'site_settings': settings
        }
    except SiteSettings.DoesNotExist:
        return {
            'site_settings': None
        }