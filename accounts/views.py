from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from .forms import CustomUserCreationForm, CustomUserChangeForm
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from .decorators import admin_required
from .models import User
from bookings.models import Booking
from facilities.models import Facility

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        if self.request.user.is_admin:
            return reverse_lazy('admin-dashboard')
        return reverse_lazy('user-dashboard')

@require_http_methods(['GET', 'POST'])
def register(request):
    if request.user.is_authenticated:
        return redirect('user-dashboard' if not request.user.is_admin else 'admin-dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('user-dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def user_dashboard(request):
    if request.user.is_admin:
        return redirect('admin-dashboard')
    
    recent_bookings = request.user.bookings.all().order_by('-created_at')[:5]
    upcoming_bookings = request.user.bookings.filter(
        date__gte=timezone.now().date(),
        status='confirmed'
    ).order_by('date', 'time_slot__start_time')[:3]
    
    context = {
        'recent_bookings': recent_bookings,
        'upcoming_bookings': upcoming_bookings,
    }
    return render(request, 'accounts/dashboard.html', context)

@login_required
def user_bookings(request):
    if request.user.is_admin:
        return redirect('admin-bookings')
    
    bookings = request.user.bookings.all().order_by('-created_at')
    return render(request, 'accounts/bookings.html', {'bookings': bookings})

@admin_required
def admin_dashboard(request):
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    # Calculate statistics
    today_bookings = Booking.objects.filter(created_at__date=today)
    monthly_bookings = Booking.objects.filter(created_at__date__gte=thirty_days_ago)
    
    stats = {
        'today_revenue': today_bookings.aggregate(Sum('total_price'))['total_price__sum'] or 0,
        'monthly_revenue': monthly_bookings.aggregate(Sum('total_price'))['total_price__sum'] or 0,
        'pending_bookings': Booking.objects.filter(status='pending').count(),
        'active_users': User.objects.filter(is_active=True, is_admin=False).count(),
        'total_bookings': today_bookings.count(),
        'monthly_bookings': monthly_bookings.count(),
        'total_facilities': Facility.objects.count(),
    }
    
    # Get pending bookings
    pending_bookings = (Booking.objects.filter(status='pending')
                       .select_related('user', 'facility_sport__facility', 'time_slot')
                       .order_by('-created_at')[:5])
    
    # Get facility revenue with percentages
    total_revenue = Booking.objects.filter(status='confirmed').aggregate(
        total=Sum('total_price'))['total'] or 1  # Avoid division by zero
    
    facility_revenue = []
    facilities = Facility.objects.annotate(
        revenue=Sum('sports__bookings__total_price', 
                   filter=Q(sports__bookings__status='confirmed'))
    )
    
    for facility in facilities:
        revenue = facility.revenue or 0
        facility_revenue.append({
            'name': facility.name,
            'revenue': revenue,
            'percentage': int((revenue / total_revenue) * 100)
        })
    
    # Get recent activities
    recent_activities = []
    
    # Add recent bookings
    recent_bookings = Booking.objects.select_related(
        'user', 'facility_sport__facility'
    ).order_by('-created_at')[:5]
    
    for booking in recent_bookings:
        activity_type = booking.status.title()
        if booking.status == 'confirmed':
            color = '#28a745'  # Success green
        elif booking.status == 'pending':
            color = '#ffc107'  # Warning yellow
        else:
            color = '#dc3545'  # Danger red
            
        recent_activities.append({
            'type': activity_type,
            'color': color,
            'timestamp': booking.created_at,
            'description': f"{booking.user.get_full_name() or booking.user.username} booked {booking.facility_sport.facility.name}"
        })
    
    context = {
        'stats': stats,
        'pending_bookings': pending_bookings,
        'facility_revenue': facility_revenue,
        'recent_activities': sorted(recent_activities, key=lambda x: x['timestamp'], reverse=True)
    }
    
    return render(request, 'accounts/admin/dashboard.html', context)

@admin_required
def admin_bookings(request):
    bookings = Booking.objects.select_related('user', 'facility_sport__facility', 'time_slot').order_by('-created_at')
    return render(request, 'accounts/admin/bookings.html', {'bookings': bookings})

@admin_required
def admin_users(request):
    users = User.objects.filter(is_admin=False).annotate(
        booking_count=Count('bookings')
    ).order_by('-date_joined')
    return render(request, 'accounts/admin/users.html', {'users': users})

@admin_required
def admin_facilities(request):
    facilities = Facility.objects.annotate(
        booking_count=Count('bookings'),
        revenue=Sum('bookings__amount')
    ).order_by('name')
    return render(request, 'accounts/admin/facilities.html', {'facilities': facilities})

@login_required
def profile(request):
    bookings = request.user.bookings.all().order_by('-created_at')[:5]
    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'recent_bookings': bookings
    })

@login_required
@require_http_methods(['GET', 'POST'])
def edit_profile(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserChangeForm(instance=request.user)
    
    return render(request, 'accounts/edit_profile.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')
