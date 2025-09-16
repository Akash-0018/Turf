from django.contrib import admin
from .models import Payment, PaymentSettings

@admin.register(PaymentSettings)
class PaymentSettingsAdmin(admin.ModelAdmin):
    list_display = ('merchant_name', 'upi_id', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('merchant_name', 'upi_id')
    readonly_fields = ('created_at', 'updated_at')
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the last active payment settings
        if obj and obj.is_active and PaymentSettings.objects.count() == 1:
            return False
        return super().has_delete_permission(request, obj)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'amount', 'payment_method', 'status', 'payment_date')
    list_filter = ('status', 'payment_method', 'payment_date')
    search_fields = ('booking__user__username', 'transaction_id')
    readonly_fields = ('payment_date', 'last_updated')
