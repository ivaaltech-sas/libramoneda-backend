"""
Admin configuration for Payment models
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Sum
from .models import Payment, PaymentStatus


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Payment admin configuration"""
    
    list_display = [
        'payment_info',
        'credit_link',
        'due_date',
        'payment_deadline_display',
        'period_days',
        'scheduled_total_display',
        'paid_total_display',
        'remaining_display',
        'status_badge',
        'days_overdue_display'
    ]
    
    list_filter = [
        'status',
        'due_date',
        'payment_date',
        'credit__credit_type',
        'credit__customer',
    ]
    
    search_fields = [
        'credit__credit_number',
        'credit__customer__first_name',
        'credit__customer__last_name',
        'credit__customer__identification_number',
        'transaction_reference',
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
        'payment_breakdown_display',
        'balance_info_display',
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
                'payment_date',
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
                'paid_total',
            )
        }),
        (_('Payment Breakdown'), {
            'fields': ('payment_breakdown_display',)
        }),
        (_('Balance Tracking'), {
            'fields': (
                'balance_before',
                'balance_after',
                'balance_info_display',
            )
        }),
        (_('Late Payment'), {
            'fields': ('late_fee',)
        }),
        (_('Payment Details'), {
            'fields': (
                'payment_method',
                'transaction_reference',
            )
        }),
        (_('Additional Information'), {
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
    
    actions = ['mark_as_paid', 'mark_as_late']
    
    def payment_info(self, obj):
        """Display payment number and credit"""
        return f"Payment #{obj.payment_number}"
    payment_info.short_description = _('Payment')
    
    def credit_link(self, obj):
        """Display clickable credit link"""
        from django.urls import reverse
        url = reverse('admin:credits_credit_change', args=[obj.credit.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.credit.credit_number
        )
    credit_link.short_description = _('Credit')
    
    def scheduled_total_display(self, obj):
        """Display scheduled total"""
        return f"${obj.scheduled_total:,.0f}"
    scheduled_total_display.short_description = _('Scheduled')
    
    def paid_total_display(self, obj):
        """Display paid total"""
        if obj.paid_total > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">${}</span>',
                f'{obj.paid_total:,.0f}'  # ← Cambio aquí
            )
        return f"${obj.paid_total:,.0f}"
    paid_total_display.short_description = _('Paid')
    
    def remaining_display(self, obj):
        """Display remaining amount"""
        remaining = obj.remaining_amount
        if remaining > 0:
            return format_html(
                '<span style="color: red;">${}</span>',
                f'{remaining:,.0f}'  # ← Cambio aquí
            )
        return f"${remaining:,.0f}"
    remaining_display.short_description = _('Remaining')
    
    def days_overdue_display(self, obj):
        """Display days overdue"""
        if obj.is_overdue:
            return format_html(
                '<span style="color: red; font-weight: bold;">{} days</span>',
                obj.days_overdue
            )
        return '-'
    days_overdue_display.short_description = _('Days Overdue')
    
    def payment_deadline_display(self, obj):
        """Display payment deadline"""
        if obj.payment_deadline and obj.payment_deadline != obj.due_date:
            return format_html(
                '<span style="color: #FF5722; font-weight: bold;">{}</span>',
                obj.payment_deadline.strftime('%b %d, %Y')
            )
        return obj.due_date.strftime('%b %d, %Y')
    payment_deadline_display.short_description = _('Payment Deadline')
    
    def status_badge(self, obj):
        """Display status with color badge"""
        colors = {
            PaymentStatus.PENDING: '#FF9800',
            PaymentStatus.PAID: '#4CAF50',
            PaymentStatus.LATE: '#F44336',
            PaymentStatus.PARTIAL: '#FFC107',
            PaymentStatus.CANCELLED: '#9E9E9E',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')
    
    def payment_breakdown_display(self, obj):
        """Display detailed payment breakdown comparison"""
        html = """
        <table style="border-collapse: collapse; width: 100%; max-width: 700px;">
            <thead>
                <tr style="background-color: #f5f5f5;">
                    <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Concepto</th>
                    <th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Programado</th>
                    <th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Pagado</th>
                    <th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Diferencia</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Capital</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">${:,.0f}</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">${:,.0f}</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">${:,.0f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Interés</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">${:,.0f}</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">${:,.0f}</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">${:,.0f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Aval</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">${:,.0f}</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">${:,.0f}</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">${:,.0f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">IVA Aval</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">${:,.0f}</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">${:,.0f}</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">${:,.0f}</td>
                </tr>
                <tr style="background-color: #e3f2fd; font-weight: bold;">
                    <td style="padding: 8px; border: 1px solid #ddd;">TOTAL</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">${:,.0f}</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">${:,.0f}</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">${:,.0f}</td>
                </tr>
            </tbody>
        </table>
        """.format(
            obj.scheduled_capital,
            obj.paid_capital,
            obj.scheduled_capital - obj.paid_capital,
            obj.scheduled_interest,
            obj.paid_interest,
            obj.scheduled_interest - obj.paid_interest,
            obj.scheduled_aval,
            obj.paid_aval,
            obj.scheduled_aval - obj.paid_aval,
            obj.scheduled_iva_aval,
            obj.paid_iva_aval,
            obj.scheduled_iva_aval - obj.paid_iva_aval,
            obj.scheduled_total,
            obj.paid_total,
            obj.remaining_amount,
        )
        
        if obj.late_fee > 0:
            html += """
            <p style="margin-top: 10px; color: red;">
                <strong>Mora:</strong> ${:,.0f}
            </p>
            """.format(obj.late_fee)
        
        return format_html(html)
    payment_breakdown_display.short_description = _('Payment Breakdown')
    
    def balance_info_display(self, obj):
        """Display balance information"""
        balance_after_value = obj.balance_after if obj.balance_after else obj.balance_before
        
        html = """
        <table style="border-collapse: collapse;">
            <tr>
                <td style="padding: 5px;"><strong>Saldo antes:</strong></td>
                <td style="padding: 5px; text-align: right;">${:,.0f}</td>
            </tr>
            <tr>
                <td style="padding: 5px;"><strong>Capital pagado:</strong></td>
                <td style="padding: 5px; text-align: right; color: green;">-${:,.0f}</td>
            </tr>
            <tr style="border-top: 2px solid #333;">
                <td style="padding: 5px;"><strong>Saldo después:</strong></td>
                <td style="padding: 5px; text-align: right; font-weight: bold;">
                    ${:,.0f}
                </td>
            </tr>
        </table>
        """.format(
            obj.balance_before,
            obj.paid_capital,
            balance_after_value,
        )
        
        return format_html(html)
    balance_info_display.short_description = _('Balance Information')
    
    def mark_as_paid(self, request, queryset):
        """Mark selected payments as paid"""
        from datetime import date
        updated = 0
        for payment in queryset:
            if payment.status != PaymentStatus.PAID:
                payment.paid_capital = payment.scheduled_capital
                payment.paid_interest = payment.scheduled_interest
                payment.paid_aval = payment.scheduled_aval
                payment.paid_iva_aval = payment.scheduled_iva_aval
                payment.paid_total = payment.scheduled_total
                payment.payment_date = date.today()
                payment.status = PaymentStatus.PAID
                payment.save()
                updated += 1
        
        self.message_user(request, f"{updated} payments marked as paid.")
    mark_as_paid.short_description = _("Mark selected payments as paid")
    
    def mark_as_late(self, request, queryset):
        """Mark selected payments as late"""
        updated = queryset.filter(status=PaymentStatus.PENDING).update(status=PaymentStatus.LATE)
        self.message_user(request, f"{updated} payments marked as late.")
    mark_as_late.short_description = _("Mark selected payments as late")
