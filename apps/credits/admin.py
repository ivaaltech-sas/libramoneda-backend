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
        'payments_summary',
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
        (_('Payment Schedule'), {
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
    # ACCIONES
    # ========================================
    
    actions = [
        'approve_credits',
        'reject_credits',
        'disburse_credits',
        'regenerate_schedules',
        'update_statuses',  # ← NUEVO
    ]
    
    # ========================================
    # MÉTODOS DE VISUALIZACIÓN
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
            CreditStatus.PENDING: '#9E9E9E',       # Gris
            CreditStatus.APPROVED: '#2196F3',      # Azul
            CreditStatus.REJECTED: '#E91E63',      # Rosa/Rojo
            CreditStatus.DISBURSED: '#00BCD4',     # Cyan
            CreditStatus.ACTIVE: '#4CAF50',        # Verde
            CreditStatus.PAST_DUE: '#FF9800',      # Naranja ⭐ NUEVO
            CreditStatus.DEFAULTED: '#F44336',     # Rojo
            CreditStatus.PAID_OFF: '#8BC34A',      # Verde claro
            CreditStatus.CANCELLED: '#607D8B',     # Gris azulado
        }
        color = colors.get(obj.status, 'gray')
        
        # Mostrar días de mora si aplica
        extra_info = ''
        if obj.status in [CreditStatus.PAST_DUE, CreditStatus.DEFAULTED]:
            days = obj.max_days_overdue
            if days > 0:
                extra_info = f' ({days}d)'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}{}</span>',
            color,
            obj.get_status_display(),
            extra_info
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
        overdue_count = obj.payments.filter(status='OVERDUE').count()
        
        url = reverse('admin:payments_payment_changelist') + f'?credit__id__exact={obj.id}'
        
        return format_html(
            """
            <div style="padding: 10px; background: #f5f5f5; border-radius: 5px;">
                <p><strong>Total Payments:</strong> {}</p>
                <p><strong>Paid:</strong> <span style="color: green;">{}</span></p>
                <p><strong>Pending:</strong> <span style="color: orange;">{}</span></p>
                <p><strong>Overdue:</strong> <span style="color: red;">{}</span></p>
                <p><a href="{}" target="_blank" style="color: #0066cc;">→ View all payments</a></p>
            </div>
            """,
            total_payments,
            paid_count,
            pending_count,
            overdue_count,
            url
        )
    payments_summary.short_description = _('Payments Summary')
    
    # ========================================
    # MÉTODOS DE ACCIONES
    # ========================================
    
    def approve_credits(self, request, queryset):
        """Approve selected credits"""
        from django.utils import timezone
        
        pending = queryset.filter(status=CreditStatus.PENDING)
        
        if not pending.exists():
            self.message_user(
                request,
                "No pending credits selected",
                level='WARNING'
            )
            return
        
        count = pending.update(
            status=CreditStatus.APPROVED,
            approved_by=request.user,
            approval_date=timezone.now()
        )
        
        self.message_user(
            request,
            f"Approved {count} credit(s)"
        )
    
    approve_credits.short_description = "Approve selected credits"
    
    def reject_credits(self, request, queryset):
        """Reject selected credits"""
        from django.utils import timezone
        
        pending = queryset.filter(status=CreditStatus.PENDING)
        
        if not pending.exists():
            self.message_user(
                request,
                "No pending credits selected",
                level='WARNING'
            )
            return
        
        count = pending.update(
            status=CreditStatus.REJECTED,
            rejected_by=request.user,
            rejection_date=timezone.now()
        )
        
        self.message_user(
            request,
            f"Rejected {count} credit(s)"
        )
    
    reject_credits.short_description = "Reject selected credits"
    
    def disburse_credits(self, request, queryset):
        """Disburse selected credits"""
        from datetime import date
        
        approved = queryset.filter(status=CreditStatus.APPROVED)
        
        if not approved.exists():
            self.message_user(
                request,
                "No approved credits selected",
                level='WARNING'
            )
            return
        
        count = 0
        for credit in approved:
            if not credit.disbursement_date:
                credit.disbursement_date = date.today()
            credit.status = CreditStatus.DISBURSED
            credit.save()
            count += 1
        
        self.message_user(
            request,
            f"Disbursed {count} credit(s)"
        )
    
    disburse_credits.short_description = "Disburse selected credits"
    
    def regenerate_schedules(self, request, queryset):
        """Regenerate payment schedules for selected credits"""
        count = 0
        for credit in queryset:
            if credit.status in [CreditStatus.DISBURSED, CreditStatus.ACTIVE]:
                credit.regenerate_payment_schedule()
                count += 1
        
        self.message_user(
            request,
            f"Regenerated schedules for {count} credit(s)"
        )
    
    regenerate_schedules.short_description = "Regenerate payment schedules"
    
    def update_statuses(self, request, queryset):
        """Actualizar estados de los créditos seleccionados"""
        count = 0
        changes = []
        
        for credit in queryset:
            # Solo actualizar si tiene pagos
            if not credit.payments.exists():
                continue
                
            old_status = credit.status
            credit.update_status_from_payments()
            credit.refresh_from_db()
            
            if old_status != credit.status:
                count += 1
                changes.append(f"{credit.credit_number}: {old_status} → {credit.status}")
        
        if count > 0:
            message = f"Updated status for {count} credit(s)"
            if count <= 5:  # Mostrar detalles si son pocos
                message += ":\n" + "\n".join(changes)
            self.message_user(request, message)
        else:
            self.message_user(
                request,
                "No status changes needed",
                level='WARNING'
            )
    
    update_statuses.short_description = "Update credit statuses based on payments"
