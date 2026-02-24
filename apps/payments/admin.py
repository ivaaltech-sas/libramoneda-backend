"""
Admin configuration for Payment models
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Sum, Q
from decimal import Decimal
from datetime import date
from .models import Payment, PaymentStatus, PaymentTransaction


class PaymentTransactionInline(admin.TabularInline):
    """Inline for payment transactions"""
    model = PaymentTransaction
    extra = 0
    readonly_fields = [
        'transaction_date',
        'amount',
        'payment_method',
        'reference_number',
        'applied_to_late_interest',
        'applied_to_interest',
        'applied_to_aval',
        'applied_to_iva',
        'applied_to_capital',
        'created_at'
    ]
    can_delete = False
    
    fields = [
        'transaction_date',
        'amount',
        'payment_method',
        'reference_number',
        'applied_to_late_interest',
        'applied_to_interest',
        'applied_to_aval',
        'applied_to_iva',
        'applied_to_capital',
    ]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Payment admin configuration"""
    
    list_display = [
        'payment_number',
        'credit_link',
        'due_date',
        'payment_deadline',
        'scheduled_total_display',
        'paid_total_display',
        'remaining_display',
        'status_badge',
        'days_overdue_display',
    ]
    
    list_filter = [
        'status',
        'due_date',
        'payment_deadline',
        'credit__credit_type',
    ]
    
    search_fields = [
        'credit__credit_number',
        'credit__customer__first_name',
        'credit__customer__last_name',
        'credit__customer__document_number',
    ]
    
    readonly_fields = [
        'payment_number',
        'due_date',
        'payment_deadline',
        'period_days',
        'scheduled_capital',
        'scheduled_interest',
        'scheduled_aval',
        'scheduled_iva_aval',
        'scheduled_total',
        'balance_before',
        'remaining_capital',
        'remaining_interest',
        'remaining_aval',
        'remaining_iva',
        'remaining_total',
        'days_overdue',
        'calculated_late_interest_display',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        (_('Payment Information'), {
            'fields': (
                'credit',
                'payment_number',
                'status',
            )
        }),
        (_('Dates'), {
            'fields': (
                'due_date',
                'payment_deadline',
                'payment_date',
                'period_days',
                'days_overdue',
            )
        }),
        (_('Scheduled Amounts'), {
            'fields': (
                'scheduled_capital',
                'scheduled_interest',
                'scheduled_aval',
                'scheduled_iva_aval',
                'scheduled_total',
            )
        }),
        (_('Paid Amounts'), {
            'fields': (
                'paid_capital',
                'paid_interest',
                'paid_aval',
                'paid_iva_aval',
                'paid_late_interest',
                'paid_total',
            )
        }),
        (_('Remaining Amounts'), {
            'fields': (
                'remaining_capital',
                'remaining_interest',
                'remaining_aval',
                'remaining_iva',
                'remaining_total',
            ),
            'classes': ('collapse',)
        }),
        (_('Late Interest (Mora)'), {
            'fields': (
                'late_interest_rate',
                'calculated_late_interest_display',
                'applied_late_interest',
                'late_interest_calculated_date',
                'late_interest_applied_date',
            )
        }),
        (_('Balance'), {
            'fields': (
                'balance_before',
            )
        }),
        (_('Additional Information'), {
            'fields': (
                'notes',
            )
        }),
    )
    
    inlines = [PaymentTransactionInline]
    
    actions = [
        'calculate_late_interest_preview',
        'apply_late_interest_action',
        'mark_as_overdue',
    ]
    
    def credit_link(self, obj):
        """Link to credit"""
        from django.urls import reverse
        url = reverse('admin:credits_credit_change', args=[obj.credit.pk])
        return format_html('<a href="{}">{}</a>', url, obj.credit.credit_number)
    credit_link.short_description = _('Credit')
    
    def scheduled_total_display(self, obj):
        """Display scheduled total"""
        formatted = f"${obj.scheduled_total:,.0f}"
        return format_html('<span style="font-weight: bold;">{}</span>', formatted)
    scheduled_total_display.short_description = _('Scheduled')
    
    def paid_total_display(self, obj):
        """Display paid total"""
        if obj.paid_total > 0:
            formatted = f"${obj.paid_total:,.0f}"
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                formatted
            )
        return '$0'
    paid_total_display.short_description = _('Paid')
    
    def remaining_display(self, obj):
        """Display remaining amount"""
        remaining = (
            obj.scheduled_capital - obj.paid_capital +
            obj.scheduled_interest - obj.paid_interest +
            obj.scheduled_aval - obj.paid_aval +
            obj.scheduled_iva_aval - obj.paid_iva_aval +
            obj.applied_late_interest - obj.paid_late_interest
        )
        
        if remaining > 0:
            formatted = f"${remaining:,.0f}"
            return format_html(
                '<span style="color: red; font-weight: bold;">{}</span>',
                formatted
            )
        return format_html('<span style="color: green;">$0</span>')
    remaining_display.short_description = _('Remaining')
    
    def status_badge(self, obj):
        """Display status with color badge"""
        colors = {
            PaymentStatus.PENDING: '#FFA500',
            PaymentStatus.PARTIAL: '#FFD700',
            PaymentStatus.PAID: '#4CAF50',
            PaymentStatus.OVERDUE: '#F44336',
            PaymentStatus.CANCELLED: '#9E9E9E',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')
    
    def days_overdue_display(self, obj):
        """Display days overdue"""
        days = obj.days_overdue
        if days > 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">{} days</span>',
                days
            )
        return '-'
    days_overdue_display.short_description = _('Days Overdue')
    
    def calculated_late_interest_display(self, obj):
        """Display calculated late interest"""
        calculated = obj.calculate_late_interest()
        if calculated > 0:
            formatted = f"${calculated:,.0f}"
            return format_html(
                '<span style="color: red; font-weight: bold;">{}</span>',
                formatted
            )
        return '$0'
    calculated_late_interest_display.short_description = _('Current Late Interest')
    
    # Actions
    
    def calculate_late_interest_preview(self, request, queryset):
        """Calculate and preview late interest without applying"""
        total_late_interest = Decimal('0')
        results = []
        
        for payment in queryset:
            if payment.status in [PaymentStatus.OVERDUE, PaymentStatus.PARTIAL]:
                calculated = payment.calculate_late_interest()
                if calculated > 0:
                    total_late_interest += calculated
                    results.append(
                        f"Payment #{payment.payment_number} ({payment.credit.credit_number}): "
                        f"${calculated:,.0f} ({payment.days_overdue} days overdue)"
                    )
        
        if results:
            message = "Late interest preview:\n" + "\n".join(results)
            message += f"\n\nTotal late interest: ${total_late_interest:,.0f}"
            self.message_user(request, message)
        else:
            self.message_user(request, "No overdue payments found", level='WARNING')
    
    calculate_late_interest_preview.short_description = "Preview late interest (no changes)"
    
    def apply_late_interest_action(self, request, queryset):
        """Apply late interest to selected payments"""
        count = 0
        total_applied = Decimal('0')
        
        for payment in queryset:
            if payment.status in [PaymentStatus.OVERDUE, PaymentStatus.PARTIAL, PaymentStatus.PENDING]:
                if payment.days_overdue > 0:
                    calculated = payment.apply_late_interest()
                    if calculated > 0:
                        total_applied += calculated
                        count += 1
        
        if count > 0:
            self.message_user(
                request,
                f"Applied late interest to {count} payment(s). Total: ${total_applied:,.0f}"
            )
        else:
            self.message_user(request, "No overdue payments to apply late interest", level='WARNING')
    
    apply_late_interest_action.short_description = "Apply late interest to selected payments"
    
    def mark_as_overdue(self, request, queryset):
        """Mark pending payments past deadline as overdue"""
        today = date.today()
        updated = queryset.filter(
            Q(payment_deadline__lt=today) | Q(due_date__lt=today),
            status=PaymentStatus.PENDING
        ).update(status=PaymentStatus.OVERDUE)
        
        self.message_user(request, f"Marked {updated} payment(s) as overdue")
    
    mark_as_overdue.short_description = "Mark as overdue"


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    """Payment transaction admin configuration"""
    
    list_display = [
        'transaction_date',
        'payment_link',
        'amount_display',
        'payment_method',
        'reference_number',
        'breakdown_display',
    ]
    
    list_filter = [
        'payment_method',
        'transaction_date',
    ]
    
    search_fields = [
        'payment__credit__credit_number',
        'reference_number',
        'payment__credit__customer__document_number',
    ]
    
    readonly_fields = [
        'payment',
        'transaction_date',
        'amount',
        'payment_method',
        'reference_number',
        'applied_to_late_interest',
        'applied_to_interest',
        'applied_to_aval',
        'applied_to_iva',
        'applied_to_capital',
        'total_applied',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        (_('Transaction Details'), {
            'fields': (
                'payment',
                'transaction_date',
                'amount',
                'payment_method',
                'reference_number',
            )
        }),
        (_('Application Breakdown'), {
            'fields': (
                'applied_to_late_interest',
                'applied_to_interest',
                'applied_to_aval',
                'applied_to_iva',
                'applied_to_capital',
                'total_applied',
            )
        }),
        (_('Notes'), {
            'fields': ('notes',)
        }),
    )
    
    def payment_link(self, obj):
        """Link to payment"""
        from django.urls import reverse
        url = reverse('admin:payments_payment_change', args=[obj.payment.pk])
        return format_html(
            '<a href="{}">{} - Payment #{}</a>',
            url,
            obj.payment.credit.credit_number,
            obj.payment.payment_number
        )
    payment_link.short_description = _('Payment')
    
    def amount_display(self, obj):
        """Display amount"""
        formatted = f"${obj.amount:,.0f}"
        return format_html(
            '<span style="color: green; font-weight: bold;">{}</span>',
            formatted
        )
    amount_display.short_description = _('Amount')
    
    def breakdown_display(self, obj):
        """Display payment breakdown"""
        parts = []
        if obj.applied_to_late_interest > 0:
            parts.append(f"Mora: ${obj.applied_to_late_interest:,.0f}")
        if obj.applied_to_interest > 0:
            parts.append(f"Int: ${obj.applied_to_interest:,.0f}")
        if obj.applied_to_capital > 0:
            parts.append(f"Cap: ${obj.applied_to_capital:,.0f}")
        
        return " | ".join(parts) if parts else "-"
    breakdown_display.short_description = _('Breakdown')
