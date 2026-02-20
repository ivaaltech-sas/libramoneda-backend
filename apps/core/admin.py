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
        'base_interest_rate',
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
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    
    fieldsets = (
        (_('Period'), {
            'fields': (
                'year',
                'month',
                'effective_date'
            )
        }),
        (_('Usury Rate'), {
            'fields': (
                'usury_rate',
                'base_interest_rate'
            ),
            'description': 'Base interest rate will be auto-calculated if left empty'
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
        # ⭐ Formatear el número PRIMERO
        rate_text = f"{float(obj.usury_rate):.2f}%"
        
        # Luego pasar el texto ya formateado a format_html
        return format_html(
            '<span style="background-color: #FF9800; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            rate_text
        )
    usury_rate_display.short_description = _('Usury Rate')
    
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
