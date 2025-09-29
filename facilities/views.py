from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
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
from .forms import FacilityForm, SportTypeForm, FacilitySportForm, SportManagementForm

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
    template_name = 'facilities/admin_settings_new.html'
    
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
        form = FacilityForm(request.POST, request.FILES)
        if form.is_valid():
            facility = form.save()
            
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
        else:
            errors = {}
            for field, error_list in form.errors.items():
                if field == '__all__':
                    errors['general'] = [str(e) for e in error_list]
                else:
                    errors[field] = [str(e) for e in error_list]
            
            return JsonResponse({
                'success': False,
                'message': 'Invalid form data',
                'errors': errors
            }, status=400)
            
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@admin_required
def edit_facility(request, facility_id):
    facility = get_object_or_404(Facility, id=facility_id)
    
    if request.method == 'GET':
        form = FacilityForm(instance=facility)
        return JsonResponse({
            'name': facility.name,
            'description': facility.description,
            'location': facility.location,
            'google_maps_link': facility.google_maps_link or '',
            'rules': facility.rules,
            'opening_time': facility.opening_time.strftime('%H:%M'),
            'closing_time': facility.closing_time.strftime('%H:%M'),
            'is_active': facility.is_active,
            'amenities': facility.amenities
        })
    
    if request.method == 'POST':
        try:
            form = FacilityForm(request.POST, request.FILES, instance=facility)
            if form.is_valid():
                facility = form.save()
                
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
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid form data',
                    'errors': form.errors
                }, status=400)
                
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
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
def toggle_facility_sport_availability(request, facility_id, sport_id):
    try:
        facility_sport = get_object_or_404(
            FacilitySport,
            facility_id=facility_id,
            sport_id=sport_id
        )
        facility_sport.is_available = not facility_sport.is_available
        facility_sport.save()
        
        return JsonResponse({
            'success': True,
            'is_available': facility_sport.is_available
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@require_POST
@admin_required
def remove_facility_sport(request, facility_id, sport_id):
    try:
        facility_sport = get_object_or_404(
            FacilitySport,
            facility_id=facility_id,
            sport_id=sport_id
        )
        facility_sport.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Sport removed from facility'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

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

@login_required
def get_slots(request):
    try:
        date_str = request.GET.get('date')
        facility_id = request.GET.get('facility_id')

        if not date_str:
            return JsonResponse({'error': 'Missing date parameter'}, status=400)

        # Parse the date
        try:
            date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format'}, status=400)

        # Get all time slots
        slots = TimeSlot.objects.all()
        
        # Format slots for response
        slots_data = []
        current_time = timezone.localtime().time()
        is_today = date == timezone.localtime().date()

        for slot in slots:
            slot_time = slot.start_time
            is_past = is_today and slot_time < current_time
            
            slot_data = {
                'id': slot.id,
                'display_time': f'{slot.start_time.strftime("%I:%M %p")} - {slot.end_time.strftime("%I:%M %p")}',
                'is_available': not is_past,
                'is_past': is_past
            }
            slots_data.append(slot_data)

        return JsonResponse({
            'slots': slots_data
        })

    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

@admin_required
def manage_facility_sports(request, facility_id):
    facility = get_object_or_404(Facility, id=facility_id)
    
    if request.method == 'GET':
        form = SportManagementForm(instance=facility)
        facility_sports = FacilitySport.objects.filter(facility=facility).select_related('sport')
        
        return JsonResponse({
            'facility_name': facility.name,
            'sports': [
                {
                    'id': fs.sport.id,
                    'name': fs.sport.name,
                    'price_per_slot': str(fs.price_per_slot),
                    'is_available': fs.is_available,
                    'max_players': fs.max_players,
                    'icon_url': fs.sport.icon.url if fs.sport.icon else None
                }
                for fs in facility_sports
            ],
            'available_sports': [
                {
                    'id': sport.id,
                    'name': sport.name
                }
                for sport in SportType.objects.exclude(
                    id__in=facility_sports.values_list('sport_id', flat=True)
                )
            ]
        })
    
    if request.method == 'POST':
        try:
            form = SportManagementForm(request.POST, instance=facility)
            if form.is_valid():
                with transaction.atomic():
                    # Save the new sport to facility
                    form.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Facility sports updated successfully'
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid form data',
                    'errors': form.errors
                }, status=400)
                
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

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
