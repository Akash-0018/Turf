from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
import uuid
from .models import Payment
from .serializers import PaymentSerializer
from bookings.models import Booking

@login_required
def process_payment(request, booking_id):
    """Process payment for a booking"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status not in ['initiated', 'payment_pending']:
        return render(request, 'payments/failure.html', {
            'error_message': 'This booking is not available for payment',
            'booking': booking
        })
    
    # Check if payment already exists
    existing_payment = Payment.objects.filter(booking=booking).exists()
    if existing_payment:
        return render(request, 'payments/failure.html', {
            'error_message': 'A payment already exists for this booking',
            'booking': booking
        })
    
    if request.method == 'POST':
        try:
            # Create payment record
            payment = Payment.objects.create(
                user=request.user,
                booking=booking,
                amount=booking.total_price,
                transaction_id=str(uuid.uuid4()),
                status='processing'
            )
            
            # Here you would integrate with a payment gateway
            # For now, we'll simulate success/failure
            import random
            success = random.random() < 0.9  # 90% success rate
            
            if success:
                payment.status = 'completed'
                payment.save()
                
                booking.status = 'confirmed'
                booking.save()
                
                return render(request, 'payments/success.html', {
                    'booking': booking,
                    'payment': payment
                })
            else:
                payment.status = 'failed'
                payment.save()
                return render(request, 'payments/failure.html', {
                    'error_message': 'Payment could not be processed. Please try again.',
                    'booking': booking
                })
                
        except Exception as e:
            return render(request, 'payments/failure.html', {
                'error_message': f'An error occurred: {str(e)}',
                'booking': booking
            })
    
    return render(request, 'payments/process.html', {
        'booking': booking
    })

@login_required
def payment_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    payment = get_object_or_404(Payment, booking=booking)
    
    if payment.status != 'completed':
        return render(request, 'payments/failure.html', {
            'error_message': 'Invalid payment status',
            'booking': booking
        })
    
    return render(request, 'payments/success.html', {
        'booking': booking,
        'payment': payment
    })

@login_required
def payment_failure(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    payment = Payment.objects.filter(booking=booking).last()
    
    error_message = request.GET.get('error', 'Payment processing failed')
    
    return render(request, 'payments/failure.html', {
        'error_message': error_message,
        'booking': booking,
        'payment': payment
    })

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_admin:
            return Payment.objects.all()
        return Payment.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Check if the booking is still valid for payment
        booking = serializer.validated_data['booking']
        if booking.status not in ['initiated', 'payment_pending']:
            raise serializers.ValidationError(
                {"booking": "This booking is no longer valid for payment"}
            )
        
        if booking.payment_deadline and booking.payment_deadline < timezone.now():
            booking.status = 'expired'
            booking.save()
            raise serializers.ValidationError(
                {"booking": "The payment window for this booking has expired"}
            )
        
        # Generate unique transaction ID
        transaction_id = str(uuid.uuid4())
        
        # Save payment with initiated status
        payment = serializer.save(
            user=self.request.user,
            transaction_id=transaction_id,
            status='initiated'
        )
        
        # Update booking status to payment_pending
        booking.status = 'payment_pending'
        booking.save()
        
        return payment
    
    @action(detail=True, methods=['post'])
    def process_payment(self, request, pk=None):
        payment = self.get_object()
        
        if payment.status != 'initiated':
            return Response(
                {"detail": "Payment cannot be processed in its current state"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Update payment status to processing
            payment.status = 'processing'
            payment.save()
            
            # Simulate payment gateway processing
            # In a real application, this would interact with a payment gateway
            success = self.process_payment_with_gateway(payment)
            
            if success:
                payment.status = 'completed'
                payment.completion_date = timezone.now()
                payment.save()
                
                return Response({
                    "status": "success",
                    "message": "Payment processed successfully",
                    "booking_status": payment.booking.status
                })
            else:
                payment.status = 'failed'
                payment.failure_reason = "Payment gateway error"
                payment.save()
                
                return Response({
                    "status": "failed",
                    "message": "Payment processing failed",
                    "booking_status": payment.booking.status
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            payment.status = 'failed'
            payment.failure_reason = str(e)
            payment.save()
            
            return Response({
                "status": "error",
                "message": "An error occurred during payment processing",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def process_payment_with_gateway(self, payment):
        """
        Simulate payment gateway processing
        In a real application, this would integrate with an actual payment gateway
        """
        # Simulate 90% success rate for demo purposes
        import random
        return random.random() < 0.9
    
    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        payment = self.get_object()
        
        if payment.status != 'completed':
            return Response(
                {"detail": "Only completed payments can be refunded"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Simulate refund process
            # In a real application, this would interact with the payment gateway
            success = self.process_refund_with_gateway(payment)
            
            if success:
                payment.status = 'refunded'
                payment.save()
                
                return Response({
                    "status": "success",
                    "message": "Payment refunded successfully"
                })
            else:
                return Response({
                    "status": "failed",
                    "message": "Refund processing failed"
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                "status": "error",
                "message": "An error occurred during refund processing",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def process_refund_with_gateway(self, payment):
        """
        Simulate refund gateway processing
        In a real application, this would integrate with an actual payment gateway
        """
        # Simulate 95% success rate for demo purposes
        import random
        return random.random() < 0.95    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        payment = self.get_object()
        
        if payment.status != 'completed':
            return Response(
                {"detail": "Only completed payments can be refunded"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # In a real application, you would process the refund with the payment gateway
        payment.status = 'refunded'
        payment.save()
        
        # Update booking status
        booking = payment.booking
        booking.status = 'cancelled'
        booking.save()
        
        return Response({"status": "payment refunded"})
