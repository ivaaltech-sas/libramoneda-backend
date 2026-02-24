"""
Admin configuration for Core models
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import InterestRateConfig


@admin.register(InterestRateConfig)
class InterestRateConfigAdmin(admin.ModelAdmin):
    """Interest Rate Configuration admin"""
    
    list_display = [
        'period',
        'usury_rate_display',
        'base_interest_rate_display',
        'late_interest_rate_display',  # ← AGREGADO
        'effective_date',
        'is_active_badge',
        'created_at'
    ]
    
    list_filter = [
        'is_active',
        'year',
        'effective_date',
        'created_at'
    ]
    
    search_fields = [
        'year',
        'month',
        'notes'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'base_interest_rate']  # ← base_interest_rate es readonly
    
    fieldsets = (
        (_('Period'), {
            'fields': (
                'year',
                'month',
                'effective_date'
            )
        }),
        (_('Interest Rates'), {
            'fields': (
                'usury_rate',
                'base_interest_rate',  # ← Auto-calculado (readonly)
                'late_interest_rate',  # ← AGREGADO (editable)
            ),
            'description': 'Base interest rate will be auto-calculated from usury rate'
        }),
        (_('Aval Rates'), {
            'fields': (
                'aval_rate_libranza',
                'aval_rate_high',
                'aval_rate_low'
            )
        }),
        (_('IVA'), {
            'fields': ('iva_rate',)
        }),
        (_('Status'), {
            'fields': (
                'is_active',
                'notes'
            )
        }),
        (_('Metadata'), {
            'fields': (
                'created_at',
                'updated_at',
                'created_by'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def period(self, obj):
        """Display period as YYYY-MM"""
        return f"{obj.year}-{obj.month:02d}"
    period.short_description = _('Period')
    period.admin_order_field = 'year'
    
    def usury_rate_display(self, obj):
        """Display usury rate with color"""
        rate_text = f"{float(obj.usury_rate):.2f}%"
        return format_html(
            '<span style="background-color: #FF9800; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            rate_text
        )
    usury_rate_display.short_description = _('Usury Rate')
    
    def base_interest_rate_display(self, obj):
        """Display base interest rate"""
        if obj.base_interest_rate:
            rate_text = f"{float(obj.base_interest_rate):.4f}%"
            return format_html(
                '<span style="background-color: #2196F3; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
                rate_text
            )
        return '-'
    base_interest_rate_display.short_description = _('Base Rate')
    
    def late_interest_rate_display(self, obj):
        """Display late interest rate (mora)"""
        rate_text = f"{float(obj.late_interest_rate):.2f}%"
        return format_html(
            '<span style="background-color: #F44336; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            rate_text
        )
    late_interest_rate_display.short_description = _('Late Rate')
    
    def is_active_badge(self, obj):
        """Display active status with badge"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #4CAF50; color: white; padding: 3px 10px; border-radius: 3px;">Activo</span>'
            )
        return format_html(
            '<span style="background-color: #9E9E9E; color: white; padding: 3px 10px; border-radius: 3px;">Inactivo</span>'
        )
    is_active_badge.short_description = _('Status')
    
    def save_model(self, request, obj, form, change):
        """Set created_by on creation"""
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
