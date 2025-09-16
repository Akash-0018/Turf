from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from .models import Review, Reply
from .serializers import ReviewSerializer, ReplySerializer
from facilities.models import Facility
from bookings.models import Booking

@login_required
def create_review(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)
    
    try:
        # Get required fields
        facility_id = request.POST.get('facility')
        rating = request.POST.get('rating')
        review_text = request.POST.get('review_text')
        booking_id = request.POST.get('booking')
        
        # Validate required fields
        if not all([facility_id, rating, review_text]):
            return JsonResponse({
                'success': False, 
                'message': 'Missing required fields'
            }, status=400)
        
        # Get facility
        facility = get_object_or_404(Facility, id=facility_id)
        
        # Create review
        review = Review.objects.create(
            user=request.user,
            facility=facility,
            rating=rating,
            review_text=review_text
        )
        
        # Associate booking if provided
        if booking_id:
            booking = get_object_or_404(Booking, id=booking_id, user=request.user)
            review.booking = booking
            review.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Review submitted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

class ReviewPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action in ['list', 'retrieve']:
            return True
        return request.user.is_authenticated
        
    def has_object_permission(self, request, view, obj):
        if view.action in ['retrieve']:
            return True
        return obj.user == request.user or request.user.is_staff

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [ReviewPermission]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['review_text', 'user__first_name', 'user__last_name', 'facility__name']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Review.objects.all()
        return Review.objects.filter(is_approved=True)
    
    def perform_create(self, serializer):
        facility = get_object_or_404(Facility, pk=self.request.data.get('facility'))
        serializer.save(user=self.request.user, facility=facility)
        
    @action(detail=False, methods=['GET'])
    def my_reviews(self, request):
        reviews = Review.objects.filter(user=request.user)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['GET'])
    def facility_reviews(self, request):
        facility_id = request.query_params.get('facility_id')
        if not facility_id:
            return Response({'error': 'facility_id is required'}, status=400)
            
        reviews = Review.objects.filter(facility_id=facility_id, is_approved=True)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)

class ReplyPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action in ['list', 'retrieve']:
            return True
        return request.user.is_authenticated
        
    def has_object_permission(self, request, view, obj):
        if view.action in ['retrieve']:
            return True
        return obj.user == request.user or request.user.is_staff

@user_passes_test(lambda u: u.is_staff)
def toggle_review_featured(request, review_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)
    
    try:
        review = get_object_or_404(Review, id=review_id)
        review.is_featured = not review.is_featured
        review.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Review {"featured" if review.is_featured else "unfeatured"} successfully',
            'is_featured': review.is_featured
        })
        
    except Review.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Review not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

class ReplyViewSet(viewsets.ModelViewSet):
    serializer_class = ReplySerializer
    permission_classes = [ReplyPermission]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Reply.objects.all()
        return Reply.objects.filter(is_approved=True)
    
    def perform_create(self, serializer):
        review = get_object_or_404(Review, pk=self.request.data.get('review'))
        serializer.save(user=self.request.user, review=review)