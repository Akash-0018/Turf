from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.views.generic import ListView, CreateView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from .models import Booking
from .serializers import BookingSerializer
from reviews.models import Review
from facilities.models import FacilitySport, TimeSlot, Offer, Facility, SportType
from django.db.models import Avg, Count

from django.http import JsonResponse
from django.shortcuts import render
from datetime import datetime, timedelta
import pytz

from django.db.models import Q
from accounts.decorators import admin_required
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from .utils import send_booking_notification_to_admin, send_booking_confirmation_to_user
from django.utils.timesince import timesince
import json

class BookingPageView(LoginRequiredMixin, CreateView):
    model = Booking
    template_name = 'bookings/booking_form.html'
    fields = ['facility_sport', 'date', 'time_slot']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all active facilities with their active sports, reviews, and images
        facilities = Facility.objects.filter(is_active=True).prefetch_related(
            'sports',
            'sports__sport',
            'facility_reviews',
            'images'
        ).annotate(
            avg_rating=Avg('facility_reviews__rating'),
            review_count=Count('facility_reviews', distinct=True)
        )

        # Get all active sports types that have at least one active facility
        active_sports = SportType.objects.filter(
            facilitysport__facility__is_active=True,
            facilitysport__is_available=True
        ).distinct()
        
        context.update({
            'facilities': facilities,
            'sports': active_sports,
            'today': timezone.now().date(),
        })
        
        return context

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_admin:
            return Booking.objects.all().select_related(
                'user', 'facility_sport__facility', 'facility_sport__sport'
            )
        return Booking.objects.filter(user=self.request.user).select_related(
            'facility_sport__facility', 'facility_sport__sport'
        )
    
    def perform_create(self, serializer):
        facility_sport = serializer.validated_data['facility_sport']
        date = serializer.validated_data['date']
        time_slot = serializer.validated_data['time_slot']
        
        # Check for existing bookings in the same slot
        existing_booking = Booking.objects.filter(
            facility_sport=facility_sport,
            date=date,
            time_slot=time_slot,
            status__in=['confirmed', 'pending']
        ).exists()
        
        if existing_booking:
            raise serializers.ValidationError(
                {"detail": "Booking with this Facility sport, Date and Time slot already exists."}
            )
        
        # Get any applicable offers
        active_offer = Offer.objects.filter(
            facility=facility_sport.facility,
            start_date__lte=date,
            end_date__gte=date,
            is_active=True
        ).first()

        # Calculate total price
        total_price = facility_sport.price_per_slot

        # Only apply early bird discount to eligible slots (6-10am)
        if active_offer:
            slot_start = facility_sport.time_slot.start_time if hasattr(facility_sport, 'time_slot') else None
            # Early bird offer logic: only for slots starting between 6:00 and 10:00
            if slot_start and (slot_start.hour >= 6 and slot_start.hour < 10):
                discount = total_price * (active_offer.discount_percentage / 100)
                total_price -= discount
        
        # Auto-confirm if user is admin
        initial_status = 'confirmed' if self.request.user.is_admin else 'pending'
        
        booking = serializer.save(
            user=self.request.user,
            total_price=total_price,
            status=initial_status
        )
        
        # Send notifications
        if initial_status == 'pending':
            send_booking_notification_to_admin(booking)
        else:
            send_booking_confirmation_to_user(booking)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        
        # Allow admins to cancel any booking, users can only cancel their confirmed bookings
        if not request.user.is_admin:
            if booking.status != 'confirmed' or booking.user != request.user:
                return Response(
                    {"detail": "You can only cancel your own confirmed bookings"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        booking.status = 'cancelled'
        booking.save()
        
        return Response({"status": "booking cancelled"})
    
    @action(detail=True, methods=['post'])
    @method_decorator(admin_required)
    def approve(self, request, pk=None):
        booking = self.get_object()
        if booking.status != 'pending':
            return Response(
                {"detail": "Only pending bookings can be approved"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'confirmed'
        booking.save()
        
        # Send confirmation email to user
        send_booking_confirmation_to_user(booking)
        
        return Response({"status": "booking approved"})
    
    @action(detail=True, methods=['post'])
    @method_decorator(admin_required)
    def reject(self, request, pk=None):
        booking = self.get_object()
        if booking.status != 'pending':
            return Response(
                {"detail": "Only pending bookings can be rejected"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', '')
        booking.status = 'rejected'
        booking.notes = f"Rejected reason: {reason}"
        booking.save()
        
        return Response({"status": "booking rejected"})
    
    @action(detail=False, methods=['get'])
    @method_decorator(admin_required)
    def pending(self, request):
        pending_bookings = self.get_queryset().filter(status='pending')
        page = self.paginate_queryset(pending_bookings)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(pending_bookings, many=True)
        return Response(serializer.data)

class UserBookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'bookings/booking_list_new.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).select_related(
            'facility_sport__facility',
            'facility_sport__sport',
            'time_slot'
        ).order_by('-date')

from django.db import transaction
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)

class BookingCreateView(LoginRequiredMixin, CreateView):
    model = Booking
    template_name = 'bookings/booking_form.html'
    fields = ['facility_sport', 'date', 'time_slot']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context['form']
        
        # Update facility_sport field's queryset
        form.fields['facility_sport'].queryset = FacilitySport.objects.filter(
            facility__is_active=True,
            is_available=True
        ).select_related(
            'facility',
            'sport'
        ).prefetch_related(
            'facility__images',
            'facility__facility_reviews'
        )
        
        context.update({
            'today': timezone.now().date()
        })
        return context

        context.update({
            'facilities': facilities,
            'today': timezone.now().date()
        })
        return context

    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Get selected date and validate
                selected_date = form.cleaned_data['date']
                logger.info(f"Booking attempt started: user={self.request.user}, date={selected_date}")

                if selected_date < timezone.now().date():
                    logger.warning(f"Booking failed: past date selected - {selected_date}")
                    form.add_error('date', 'Cannot book for past dates')
                    return self.form_invalid(form)

                # Check for existing bookings
                facility_sport = form.instance.facility_sport
                time_slot = form.instance.time_slot

                logger.info(f"Form data: facility_sport={form.data.get('facility_sport')}, time_slot={form.data.get('time_slot')}, date={form.data.get('date')}")

                # Validate that facility_sport and time_slot exist
                if not facility_sport:
                    logger.error(f"Invalid facility_sport ID: {form.data.get('facility_sport')}")
                    if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Invalid facility or sport selected'
                        }, status=400)
                    form.add_error('facility_sport', 'Invalid facility or sport selected')
                    return self.form_invalid(form)

                if not time_slot:
                    logger.error(f"Invalid time_slot ID: {form.data.get('time_slot')}")
                    if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Invalid time slot selected'
                        }, status=400)
                    form.add_error('time_slot', 'Invalid time slot selected')
                    return self.form_invalid(form)

                # Log the booking attempt details for debugging
                logger.info(f"Booking attempt: user={self.request.user}, facility_sport={facility_sport}, date={selected_date}, time_slot={time_slot}")

                # Lock the time slot for concurrent booking prevention
                existing_booking = Booking.objects.select_for_update().filter(
                    facility_sport=facility_sport,
                    date=selected_date,
                    time_slot=time_slot,
                    status__in=['initiated', 'payment_pending', 'confirmed']
                ).exists()

                if existing_booking:
                    logger.warning(f"Booking failed: time slot already booked for facility_sport={facility_sport}, date={selected_date}, time_slot={time_slot}")
                    if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Booking with this Facility sport, Date and Time slot already exists.'
                        }, status=400)
                    form.add_error(None, 'Booking with this Facility sport, Date and Time slot already exists.')
                    return self.form_invalid(form)

                # Set basic booking info
                form.instance.user = self.request.user
                form.instance.date = selected_date
                form.instance.status = 'initiated'

                logger.info(f"Saving booking: user={self.request.user}, facility_sport={facility_sport}, date={selected_date}, time_slot={time_slot}")

                # Save booking - price calculation happens in model's save method
                response = super().form_valid(form)

                logger.info(f"Booking saved successfully: id={self.object.id}, total_price={self.object.total_price}")

                if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Booking initiated successfully',
                        'booking_id': self.object.id,
                        'total_price': str(self.object.total_price),
                        'payment_deadline': self.object.payment_deadline.isoformat(),
                        'redirect_url': reverse('payment-process', kwargs={'booking_id': self.object.id})
                    })

                return response

        except Exception as e:
            logger.error(f"Booking creation error: {str(e)}", exc_info=True)
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)
            raise

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Convert form errors to a readable message
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            message = '; '.join(error_messages) if error_messages else 'Invalid form data'
            return JsonResponse({
                'status': 'error',
                'message': message
            }, status=400)
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse('user-bookings')

class BookingDetailView(LoginRequiredMixin, DetailView):
    model = Booking
    template_name = 'bookings/booking_detail.html'
    context_object_name = 'booking'

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

@login_required
def review_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    # Check if booking is completed and hasn't been reviewed yet
    if booking.status != 'completed':
        messages.error(request, 'You can only review completed bookings')
        return redirect('bookings')

    if hasattr(booking, 'review'):
        messages.error(request, 'You have already reviewed this booking')
        return redirect('bookings')

    if request.method == 'POST':
        rating = request.POST.get('rating')
        review_text = request.POST.get('review_text')

        if not rating or not review_text:
            return JsonResponse({
                'status': 'error',
                'message': 'Both rating and review text are required'
            }, status=400)

        try:
            # Create the review
            Review.objects.create(
                user=request.user,
                facility=booking.facility_sport.facility,
                booking=booking,
                rating=rating,
                review_text=review_text,
                is_approved=False  # Reviews need admin approval
            )

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Review submitted successfully',
                    'redirect_url': reverse('bookings')
                })

            messages.success(request, 'Thank you for your review!')
            return redirect('bookings')

        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)
            messages.error(request, f'Error submitting review: {str(e)}')
            return redirect('bookings')

    context = {
        'booking': booking,
    }
    return render(request, 'bookings/review_form_new.html', context)

@login_required
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    # Allow admins to cancel any booking, users can only cancel their confirmed bookings
    if not request.user.is_admin:
        if booking.status != 'confirmed' or booking.user != request.user:
            messages.error(request, 'You can only cancel your own confirmed bookings')
            return redirect('dashboard')

    booking.status = 'cancelled'
    booking.save()

    messages.success(request, 'Booking cancelled successfully')
    return redirect('dashboard')

@login_required
def get_slots(request):
    """
    Returns available slots for a given date.
    Query param: date (YYYY-MM-DD)
    facility_id: ID of the facility to check slots for
    """
    try:
        date_str = request.GET.get('date')
        facility_id = request.GET.get('facility_id')

        if not date_str:
            return JsonResponse({'error': 'Missing date parameter'}, status=400)

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format'}, status=400)

        # Get all time slots
        all_slots = TimeSlot.objects.all()

        # Get booked slots for the date
        booked_slots = Booking.objects.filter(
            date=date_obj,
            status__in=['confirmed', 'pending'],
        )
        if facility_id:
            booked_slots = booked_slots.filter(facility_sport__facility_id=facility_id)

        booked_slot_ids = set(booked_slots.values_list('time_slot_id', flat=True))

        # Get active offers for the facility
        offers = []
        active_offer = None
        if facility_id:
            active_offer = Offer.objects.filter(
                facility_id=facility_id,
                start_date__lte=date_obj,
                end_date__gte=date_obj,
                is_active=True
            ).first()
            if active_offer:
                offers = [{
                    'title': active_offer.title,
                    'discount_percentage': active_offer.discount_percentage
                }]

        # Filter available slots
        slots = []
        now = timezone.now()
        is_today = date_obj == now.date()

        for slot in all_slots:
            is_lunch = slot.slot_time == '12:00-13:00'  # Check for lunch slot

            # Check if slot is in the past (for today only)
            is_past = False
            if is_today:
                # Convert both times to IST for comparison
                current_local = timezone.localtime(now)
                slot_local = timezone.localtime(timezone.make_aware(datetime.combine(date_obj, slot.start_time)))
                is_past = slot_local <= current_local

            # A slot is available if it's:
            # - Not in the past
            # - Not a lunch break
            # - Not already booked
            is_booked = slot.id in booked_slot_ids
            is_available = not (is_past or is_lunch or is_booked)

            # Format display time
            display_time = f"{slot.start_time.strftime('%I:%M %p')} - {slot.end_time.strftime('%I:%M %p')}"

            slot_data = {
                'id': slot.id,
                'slot_time': slot.slot_time,
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M'),
                'display_time': display_time,
                'is_past': is_past,
                'is_lunch': is_lunch,
                'is_booked': is_booked,
                'is_available': is_available
            }

            # Add sport-specific information if facility is specified
            if facility_id:
                sports = FacilitySport.objects.filter(
                    facility_id=facility_id,
                    is_available=True
                ).select_related('sport')

                for sport in sports:
                    sport_slot = slot_data.copy()
                    sport_slot['id'] = f"{date_str}_{slot.id}_{sport.id}"
                    sport_slot['sport_name'] = sport.sport.name
                    base_price = float(sport.price_per_slot)
                    sport_slot['base_price'] = base_price
                    sport_slot['price'] = base_price  # Keep for backward compatibility

                    # Apply discount only for early bird slots (6-10am)
                    slot_hour = slot.start_time.hour
                    if active_offer and (slot_hour >= 6 and slot_hour < 10):
                        discount = base_price * (active_offer.discount_percentage / 100)
                        discounted_price = base_price - discount
                        sport_slot['discounted_price'] = float(discounted_price)
                        sport_slot['discount_percentage'] = active_offer.discount_percentage
                    else:
                        sport_slot['discounted_price'] = base_price
                        sport_slot['discount_percentage'] = 0

                    sport_slot['facility_sport_id'] = sport.id

                    slots.append(sport_slot)
            else:
                slots.append(slot_data)

        return JsonResponse({
            'available_slots': slots,  # Changed to match template expectations
            'offers': offers
        })

    except Exception as e:
        logger.error(f"Error in get_slots: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': 'Internal server error occurred while loading slots'
        }, status=500)


def home_get_slots(request):
    """
    Returns preview slots for home page.
    Shows slots for next 3 days for all facilities combined.
    """
    current_datetime = timezone.localtime(timezone.now())
    today = current_datetime.date()
    current_time = current_datetime.time()
    dates = [today + timedelta(days=i) for i in range(3)]
    
    all_slots = TimeSlot.objects.all()
    date_slots = {}
    
    for date in dates:
        # Get booked slots for the date
        booked_slots = Booking.objects.filter(
            date=date,
            status__in=['confirmed', 'pending'],
        ).values_list('time_slot_id', flat=True)
        
        booked_slot_ids = set(booked_slots)
        
        # Filter available slots
        available_slots = []
        for slot in all_slots:
            # For today's slots, check if the slot's start time has passed
            is_past = False
            if date == today:
                current_hour = current_time.hour
                current_minute = current_time.minute
                slot_hour = slot.start_time.hour
                slot_minute = slot.start_time.minute
                # Convert both times to minutes for easier comparison
                current_minutes = current_hour * 60 + current_minute
                slot_minutes = slot_hour * 60 + slot_minute
                is_past = slot_minutes <= current_minutes
            is_available = slot.id not in booked_slot_ids and not is_past
            slot_data = {
                'id': slot.id,
                'slot_time': slot.slot_time,
                'display_time': slot.get_slot_time_display(),
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M'),
                'is_available': is_available,
                'is_past': is_past,
                'discounted_price': None,
                'discount_percentage': 0
            }
            # Early bird offer logic: only for slots starting between 6:00 and 10:00 IST
            slot_time = timezone.localtime(datetime.combine(date, slot.start_time))
            slot_hour = slot_time.hour
            active_offer = None
            offers = Offer.objects.filter(
                start_date__lte=date,
                end_date__gte=date,
                is_active=True
            )
            if offers.exists() and (slot_hour >= 6 and slot_hour < 10):
                active_offer = offers.first()
                base_price = None
                sports = FacilitySport.objects.filter(is_available=True).select_related('sport')
                if sports.exists():
                    base_price = float(sports.first().price_per_slot)
                if base_price:
                    discount = base_price * (active_offer.discount_percentage / 100)
                    discounted_price = base_price - discount
                    slot_data['discounted_price'] = float(discounted_price)
                    slot_data['discount_percentage'] = active_offer.discount_percentage
            available_slots.append(slot_data)
        date_slots[date] = available_slots
    
    context = {
        'date_slots': date_slots,
        'dates': dates,
        'is_preview': True
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        html = render_to_string('includes/slots_preview.html', context)
        return JsonResponse({
            'html': html,
            'dates': [str(d) for d in dates],
        })
    
    return render(request, 'includes/slots_preview.html', context)