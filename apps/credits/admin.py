"""
Admin configuration for Credit models
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from .models import Credit, CreditStatus, CreditType


@admin.register(Credit)
class CreditAdmin(admin.ModelAdmin):
    """Credit admin configuration"""
    
    list_display = [
        'credit_number',
        'customer_name',
        'credit_type',
        'approved_amount_display',
        'approved_term',
        'status_badge',
        'created_at',
    ]
    
    list_filter = [
        'status',
        'credit_type',
        'payment_frequency',
        'created_at',
        'approval_date',
    ]
    
    search_fields = [
        'credit_number',
        'customer__first_name',
        'customer__last_name',
        'customer__identification_number',
    ]
    
    readonly_fields = [
        'credit_number',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
        'payment_breakdown_display',
        'payments_summary',  # ← ESTE ESTÁ BIEN
    ]
    
    fieldsets = (
        (_('Credit Information'), {
            'fields': (
                'credit_number',
                'customer',
                'credit_type',
                'company',
                'purpose',
            )
        }),
        (_('Requested Terms'), {
            'fields': (
                'requested_amount',
                'requested_term',
            )
        }),
        (_('Interest Rate Configuration'), {
            'fields': (
                'interest_rate_config',
                'base_interest_rate',
                'aval_rate',
                'iva_rate',
            )
        }),
        (_('Approved Terms'), {
            'fields': (
                'approved_amount',
                'approved_term',
                'payment_frequency',
            )
        }),
        (_('Payment Breakdown'), {
            'fields': ('payment_breakdown_display',)
        }),
        (_('Totals'), {
            'fields': (
                'total_interest',
                'total_aval',
                'total_iva_aval',
                'total_amount',
            )
        }),
        (_('Disbursement'), {
            'fields': (
                'disbursement_date',
                'disbursement_method',
            )
        }),
        (_('Status'), {
            'fields': (
                'status',
                'balance',
            )
        }),
        (_('Approval Workflow'), {
            'fields': (
                'sales_advisor',
                'approved_by',
                'approval_date',
                'approval_notes',
            )
        }),
        (_('Rejection'), {
            'fields': (
                'rejected_by',
                'rejection_date',
                'rejection_reason',
            ),
            'classes': ('collapse',)
        }),
        (_('Payment Schedule'), {  # ← NUEVO
            'fields': ('payments_summary',)
        }),
        (_('Additional'), {
            'fields': ('notes',)
        }),
        (_('Audit'), {
            'fields': (
                'created_at',
                'updated_at',
                'created_by',
                'updated_by',
            ),
            'classes': ('collapse',)
        }),
    )
    
    # ========================================
    # MÉTODOS (DENTRO DE LA CLASE)
    # ========================================
    
    def customer_name(self, obj):
        """Display customer name"""
        return f"{obj.customer.first_name} {obj.customer.last_name}"
    customer_name.short_description = _('Customer')
    
    def approved_amount_display(self, obj):
        """Display approved amount formatted"""
        if obj.approved_amount:
            return f"${obj.approved_amount:,.0f}"
        return '-'
    approved_amount_display.short_description = _('Approved Amount')
    
    def status_badge(self, obj):
        """Display status with color badge"""
        colors = {
            CreditStatus.PENDING: '#FF9800',
            CreditStatus.APPROVED: '#4CAF50',
            CreditStatus.REJECTED: '#F44336',
            CreditStatus.DISBURSED: '#2196F3',
            CreditStatus.ACTIVE: '#00BCD4',
            CreditStatus.PAID: '#8BC34A',
            CreditStatus.DEFAULTED: '#F44336',
            CreditStatus.CANCELLED: '#9E9E9E',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')
    
    def payment_breakdown_display(self, obj):
        """Display payment breakdown"""
        if not obj.monthly_payment:
            return format_html('<em>Not calculated yet</em>')
        
        total_aval = obj.total_aval or 0
        total_iva_aval = obj.total_iva_aval or 0
        total_amount = obj.total_amount or 0
        
        html = f"""
        <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
            <thead>
                <tr style="background-color: #e3f2fd;">
                    <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Concepto</th>
                    <th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Mensual</th>
                    <th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Total</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Cuota Base (Capital + Interés)</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">${obj.monthly_payment_base:,.0f}</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">${obj.monthly_payment_base * obj.approved_term:,.0f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Aval</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">${obj.monthly_aval:,.0f}</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">${total_aval:,.0f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">IVA sobre Aval</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">${obj.monthly_iva_aval:,.0f}</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">${total_iva_aval:,.0f}</td>
                </tr>
                <tr style="background-color: #c8e6c9; font-weight: bold;">
                    <td style="padding: 8px; border: 1px solid #ddd;">CUOTA TOTAL</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">${obj.monthly_payment:,.0f}</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">${total_amount:,.0f}</td>
                </tr>
            </tbody>
        </table>
        """
        return format_html(html)
    payment_breakdown_display.short_description = _('Payment Breakdown')
    
    def payments_summary(self, obj):
        """Display payments summary with link"""
        if not obj.pk:
            return '-'
        
        total_payments = obj.payments.count()
        
        if total_payments == 0:
            return format_html('<em>No payments generated yet. Change status to DISBURSED to generate.</em>')
        
        paid_count = obj.payments.filter(status='PAID').count()
        pending_count = obj.payments.filter(status='PENDING').count()
        late_count = obj.payments.filter(status='LATE').count()
        
        url = reverse('admin:payments_payment_changelist') + f'?credit__id__exact={obj.id}'
        
        return format_html(
            """
            <div style="padding: 10px; background: #f5f5f5; border-radius: 5px;">
                <p><strong>Total Payments:</strong> {}</p>
                <p><strong>Paid:</strong> <span style="color: green;">{}</span></p>
                <p><strong>Pending:</strong> <span style="color: orange;">{}</span></p>
                <p><strong>Late:</strong> <span style="color: red;">{}</span></p>
                <p><a href="{}" target="_blank" style="color: #0066cc;">→ View all payments</a></p>
            </div>
            """,
            total_payments,
            paid_count,
            pending_count,
            late_count,
            url
        )
    payments_summary.short_description = _('Payments Summary')
