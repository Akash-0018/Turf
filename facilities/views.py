from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from django.utils.decorators import method_decorator
from django.db import transaction
from django.core.exceptions import ValidationError
from accounts.decorators import admin_required
from .models import (
    Facility, FacilitySport, SportType, Offer, 
    TimeSlot, SiteSettings, FacilityImage
)
from reviews.models import Review
from .serializers import FacilitySerializer, FacilitySportSerializer

class FacilityListView(ListView):
    model = Facility
    template_name = 'facilities/facility_list.html'
    context_object_name = 'facilities'
    
    def get_queryset(self):
        return Facility.objects.all()

class FacilityDetailView(DetailView):
    model = Facility
    template_name = 'facilities/facility_detail.html'
    context_object_name = 'facility'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get facility sports with prefetched relationships
        context['facility_sports'] = self.object.sports.select_related('sport').all()
        
        # Get reviews with user info
        context['reviews'] = Review.objects.filter(facility=self.object)\
            .select_related('user')\
            .order_by('-is_approved', '-created_at')
        
        # Calculate average rating
        reviews = context['reviews']
        if reviews:
            total_rating = sum(review.rating for review in reviews)
            context['average_rating'] = total_rating / len(reviews)
            context['rating_count'] = len(reviews)
        else:
            context['average_rating'] = 0
            context['rating_count'] = 0
        
        # Add today's date for the date picker min value
        context['today'] = timezone.now().date()
        
        # Get available time slots for today
        context['time_slots'] = TimeSlot.objects.all()
        
        return context

class AdminSettingsView(TemplateView):
    template_name = 'facilities/admin_settings.html'
    
    @method_decorator(admin_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get or create site settings
        settings, _ = SiteSettings.objects.get_or_create(pk=1)
        
        context.update({
            'settings': settings,
            'facilities': Facility.objects.all(),
            'sports': SportType.objects.all(),
            'offers': Offer.objects.all(),
            'reviews': Review.objects.all().select_related('user', 'facility')
        })
        
        return context

@require_POST
@admin_required
def save_settings(request):
    try:
        settings = SiteSettings.objects.get(pk=1)
        
        # Update text fields
        settings.site_name = request.POST.get('site_name', settings.site_name)
        settings.contact_email = request.POST.get('contact_email', settings.contact_email)
        settings.contact_phone = request.POST.get('contact_phone', settings.contact_phone)
        settings.about_us = request.POST.get('about_us', settings.about_us)
        settings.booking_time_limit = request.POST.get('booking_time_limit', settings.booking_time_limit)
        settings.cancellation_time_limit = request.POST.get('cancellation_time_limit', settings.cancellation_time_limit)
        settings.max_advance_booking_days = request.POST.get('max_advance_booking_days', settings.max_advance_booking_days)
        settings.maintenance_mode = request.POST.get('maintenance_mode') == 'true'
        
        # Handle file uploads
        if 'logo' in request.FILES:
            old_logo = settings.logo.path if settings.logo else None
            settings.logo = request.FILES['logo']
            if old_logo:
                default_storage.delete(old_logo)
                
        if 'favicon' in request.FILES:
            old_favicon = settings.favicon.path if settings.favicon else None
            settings.favicon = request.FILES['favicon']
            if old_favicon:
                default_storage.delete(old_favicon)
        
        settings.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Settings saved successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@require_POST
@admin_required
def toggle_review_featured(request, review_id):
    try:
        review = get_object_or_404(Review, id=review_id)
        review.is_featured = not review.is_featured
        # Also approve the review when featuring it
        if review.is_featured and not review.is_approved:
            review.is_approved = True
        review.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Review has been ' + ('featured' if review.is_featured else 'unfeatured'),
            'is_featured': review.is_featured,
            'is_approved': review.is_approved
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
@admin_required
def toggle_offer_active(request, offer_id):
    try:
        offer = get_object_or_404(Offer, id=offer_id)
        offer.is_active = not offer.is_active
        offer.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Offer has been ' + ('activated' if offer.is_active else 'deactivated'),
            'is_active': offer.is_active
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
@admin_required
def add_facility(request):
    try:
        data = request.POST
        facility = Facility.objects.create(
            name=data.get('name'),
            description=data.get('description'),
            location=data.get('location'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            rules=data.get('rules'),
            opening_time=data.get('opening_time'),
            closing_time=data.get('closing_time'),
            is_active=data.get('is_active') == 'true',
            amenities=data.getlist('amenities[]')
        )
        
        if 'images' in request.FILES:
            for i, image in enumerate(request.FILES.getlist('images')):
                FacilityImage.objects.create(
                    facility=facility,
                    image=image,
                    is_primary=(i == 0),
                    order=i
                )
        
        return JsonResponse({
            'success': True,
            'message': 'Facility added successfully',
            'id': facility.id
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@admin_required
def edit_facility(request, facility_id):
    facility = get_object_or_404(Facility, id=facility_id)
    
    if request.method == 'GET':
        return JsonResponse({
            'name': facility.name,
            'description': facility.description,
            'location': facility.location,
            'latitude': str(facility.latitude) if facility.latitude else '',
            'longitude': str(facility.longitude) if facility.longitude else '',
            'rules': facility.rules,
            'opening_time': facility.opening_time.strftime('%H:%M'),
            'closing_time': facility.closing_time.strftime('%H:%M'),
            'is_active': facility.is_active,
            'amenities': facility.amenities
        })
    
    if request.method == 'POST':
        try:
            data = request.POST
            
            # Update all fields from the form
            facility.name = data.get('name')
            facility.description = data.get('description')
            facility.location = data.get('location')
            facility.latitude = data.get('latitude') if data.get('latitude') else None
            facility.longitude = data.get('longitude') if data.get('longitude') else None
            facility.rules = data.get('rules')
            facility.opening_time = data.get('opening_time')
            facility.closing_time = data.get('closing_time')
            # Handle is_active field properly for checkboxes
            facility.is_active = data.get('is_active', 'off') == 'on'
            
            if 'amenities[]' in data:
                facility.amenities = data.getlist('amenities[]')
            
            facility.save()
            
            # Handle image uploads
            if 'images' in request.FILES:
                for i, image in enumerate(request.FILES.getlist('images')):
                    FacilityImage.objects.create(
                        facility=facility,
                        image=image,
                        is_primary=(i == 0 and not facility.images.filter(is_primary=True).exists()),
                        order=facility.images.count() + i
                    )
            
            return JsonResponse({
                'success': True,
                'message': 'Facility updated successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

@require_POST
@admin_required
def delete_facility(request, facility_id):
    try:
        facility = get_object_or_404(Facility, id=facility_id)
        facility.delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
@admin_required
def add_facility_images(request, facility_id):
    try:
        facility = get_object_or_404(Facility, id=facility_id)
        images = []
        
        for i, image in enumerate(request.FILES.getlist('images')):
            img = FacilityImage.objects.create(
                facility=facility,
                image=image,
                is_primary=False,
                order=facility.images.count() + i
            )
            images.append({
                'id': img.id,
                'url': img.image.url
            })
        
        return JsonResponse({
            'success': True,
            'message': 'Images added successfully',
            'images': images
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@require_POST
@admin_required
def delete_facility_image(request, facility_id, image_id):
    try:
        image = get_object_or_404(FacilityImage, id=image_id, facility_id=facility_id)
        image.delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
@admin_required
def set_primary_image(request, facility_id, image_id):
    try:
        facility = get_object_or_404(Facility, id=facility_id)
        facility.images.update(is_primary=False)
        image = get_object_or_404(FacilityImage, id=image_id, facility_id=facility_id)
        image.is_primary = True
        image.save()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
@admin_required
def add_sport(request):
    try:
        sport = SportType.objects.create(
            name=request.POST.get('name')
        )
        if 'icon' in request.FILES:
            sport.icon = request.FILES['icon']
            sport.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Sport added successfully',
            'id': sport.id
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@admin_required
def edit_sport(request, sport_id):
    sport = get_object_or_404(SportType, id=sport_id)
    
    if request.method == 'GET':
        return JsonResponse({
            'name': sport.name,
            'icon_url': sport.icon.url if sport.icon else None
        })
    
    if request.method == 'POST':
        try:
            # Update name
            sport.name = request.POST.get('name')
            
            # Handle icon upload
            if 'icon' in request.FILES:
                if sport.icon:
                    sport.icon.delete()  # Delete old icon
                sport.icon = request.FILES['icon']
            
            sport.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Sport updated successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

@require_POST
@admin_required
def delete_sport(request, sport_id):
    try:
        sport = get_object_or_404(SportType, id=sport_id)
        sport.delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
@admin_required
def add_offer(request):
    try:
        offer = Offer.objects.create(
            facility_id=request.POST.get('facility'),
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            discount_percentage=request.POST.get('discount_percentage'),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            is_active=request.POST.get('is_active') == 'true'
        )
        return JsonResponse({'status': 'success', 'id': offer.id})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@admin_required
def edit_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    
    if request.method == 'GET':
        return JsonResponse({
            'facility': offer.facility_id,
            'title': offer.title,
            'description': offer.description,
            'discount_percentage': str(offer.discount_percentage),
            'start_date': offer.start_date.strftime('%Y-%m-%d'),
            'end_date': offer.end_date.strftime('%Y-%m-%d'),
            'is_active': offer.is_active
        })
    
    if request.method == 'POST':
        try:
            data = request.POST
            
            # Update all fields
            offer.facility_id = data.get('facility')
            offer.title = data.get('title')
            offer.description = data.get('description')
            offer.discount_percentage = data.get('discount_percentage')
            offer.start_date = data.get('start_date')
            offer.end_date = data.get('end_date')
            offer.is_active = data.get('is_active') == 'true'
            
            offer.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Offer updated successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

@require_POST
@admin_required
def delete_offer(request, offer_id):
    try:
        offer = get_object_or_404(Offer, id=offer_id)
        offer.delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
@admin_required
def toggle_review_approved(request, review_id):
    try:
        review = get_object_or_404(Review, id=review_id)
        review.is_approved = not review.is_approved
        # If un-approving, also un-feature the review
        if not review.is_approved:
            review.is_featured = False
        review.save()
        
        return JsonResponse({
            'status': 'success',
            'is_approved': review.is_approved,
            'is_featured': review.is_featured
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class FacilityViewSet(viewsets.ModelViewSet):
    queryset = Facility.objects.all()
    serializer_class = FacilitySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'sports_type']
    ordering_fields = ['name', 'created_at']
    
    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        facility = self.get_object()
        date = request.query_params.get('date', timezone.now().date())
        
        # Get all confirmed bookings for the date
        bookings = facility.bookings.filter(
            date=date,
            status='confirmed'
        ).values('date', 'time_slot__start_time', 'time_slot__end_time')
        
        # Get sports available at the facility
        facility_sports = facility.sports.filter(is_available=True)
        sports_serializer = FacilitySportSerializer(facility_sports, many=True)
        
        return Response({
            'bookings': bookings,
            'facility_sports': sports_serializer.data
        })
