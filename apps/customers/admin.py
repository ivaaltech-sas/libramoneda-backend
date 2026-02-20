"""
Admin configuration for Customer models
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Customer admin configuration"""
    
    list_display = [
        'identification_number',
        'get_full_name',
        'customer_type',
        'company',
        'city',
        'total_income',
        'is_active',
        'created_at'
    ]
    list_filter = [
        'is_active',
        'identification_type',
        'marital_status',
        'company',
        'has_other_credits',
        'city',
        'created_at'
    ]
    search_fields = [
        'identification_number',
        'first_name',
        'last_name',
        'email',
        'phone_number',
        'mobile_number',
        'employee_code'
    ]
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = (
        (_('Personal Information'), {
            'fields': (
                'identification_type',
                'identification_number',
                'first_name',
                'last_name',
                'date_of_birth',
                'marital_status'
            )
        }),
        (_('Contact Information'), {
            'fields': (
                'phone_number',
                'mobile_number',
                'email',
                'address',
                'neighborhood',
                'city',
                'department'
            )
        }),
        (_('Employment Information (Libranza)'), {
            'fields': (
                'company',
                'employee_code',
                'position',
                'hire_date',
                'monthly_salary'
            ),
            'classes': ('collapse',),
            'description': 'Fill this section only for employees (libranza credits)'
        }),
        (_('Natural Person Information'), {
            'fields': (
                'occupation',
                'monthly_income'
            ),
            'classes': ('collapse',),
            'description': 'Fill this section only for natural persons'
        }),
        (_('Financial Information'), {
            'fields': (
                'has_other_credits',
                'other_credits_total'
            )
        }),
        (_('Additional'), {
            'fields': (
                'is_active',
                'notes'
            )
        }),
        (_('Audit'), {
            'fields': (
                'created_at',
                'updated_at',
                'created_by',
                'updated_by'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_name(self, obj):
        """Display full name"""
        return obj.get_full_name()
    get_full_name.short_description = _('Full Name')
    
    def customer_type(self, obj):
        """Display customer type with badge"""
        if obj.is_employee:
            return format_html(
                '<span style="background-color: #4CAF50; color: white; padding: 3px 10px; border-radius: 3px;">Empleado (Libranza)</span>'
            )
        return format_html(
            '<span style="background-color: #2196F3; color: white; padding: 3px 10px; border-radius: 3px;">Persona Natural</span>'
        )
    customer_type.short_description = _('Type')
