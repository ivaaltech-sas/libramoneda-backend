from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Company, CompanyStatus


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Company admin configuration"""
    
    list_display = [
        'business_name',
        'nit',
        'city',
        'payment_day',
        'agreement_number',
        'status_badge',
        'is_active',
    ]
    
    list_filter = [
        'status',
        'city',
        'department',
        'agreement_date',
    ]
    
    search_fields = [
        'business_name',
        'trade_name',
        'nit',
        'agreement_number',
        'email',
        'contact_person_name',
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
        'is_active',
        'display_name',
    ]
    
    fieldsets = (
        (_('Company Information'), {
            'fields': (
                'nit',
                'business_name',
                'trade_name',
                'display_name',
            )
        }),
        (_('Contact Information'), {
            'fields': (
                'phone_number',
                'email',
                'website',
                'address',
                'city',
                'department',
            )
        }),
        (_('Agreement Details'), {
            'fields': (
                'agreement_number',
                'agreement_date',
                'agreement_end_date',
                'status',
            )
        }),
        (_('Payroll Settings'), {
            'fields': (
                'payment_day',
            ),
            'description': _('Day of month when company pays salaries (for Libranza credits)')
        }),
        (_('Contact Person'), {
            'fields': (
                'contact_person_name',
                'contact_person_position',
                'contact_person_phone',
                'contact_person_email',
            )
        }),
        (_('Additional Information'), {
            'fields': (
                'notes',
            )
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
    
    def status_badge(self, obj):
        """Display status with color badge"""
        colors = {
            CompanyStatus.ACTIVE: '#4CAF50',
            CompanyStatus.INACTIVE: '#9E9E9E',
            CompanyStatus.SUSPENDED: '#F44336',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')