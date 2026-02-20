"""
Core models for Libramoneda platform
Abstract base models for common functionality
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal, getcontext, ROUND_HALF_UP
from django.core.validators import MinValueValidator, MaxValueValidator

class TimeStampedModel(models.Model):
    """
    Abstract model that provides self-updating 'created_at' and 'updated_at' fields
    """
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        abstract = True


class AuditableModel(models.Model):
    """
    Abstract model for audit trail
    Adds created/updated timestamps and user tracking
    """
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='%(class)s_created',
        verbose_name=_('created by'),
        null=True,
        blank=True
    )
    updated_by = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='%(class)s_updated',
        verbose_name=_('updated by'),
        null=True,
        blank=True
    )

    class Meta:
        abstract = True


# ⭐ NUEVO MODELO - Interest Rate Configuration
class InterestRateConfig(models.Model):
    """
    Monthly interest rate configuration based on usury rate
    Stores historical usury rates and calculates credit interest rates
    """
    # Period
    year = models.PositiveIntegerField(
        _('year'),
        help_text=_('Year (e.g., 2026)')
    )
    month = models.PositiveIntegerField(
        _('month'),
        validators=[
            MinValueValidator(1),      # ✅ Correcto
            MaxValueValidator(12)      # ✅ Correcto
        ],
        help_text=_('Month (1-12)')
    )
    
    # Usury Rate (Tasa de Usura)
    usury_rate = models.DecimalField(
        _('usury rate'),
        max_digits=5,
        decimal_places=2,
        help_text=_('Annual usury rate percentage (e.g., 25.01 for 25.01%)')
    )
    
    # Calculated Interest Rate (for credits)
    base_interest_rate = models.DecimalField(
        _('base interest rate'),
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True, 
        help_text=_('Calculated monthly base interest rate (e.g., 1.88 for 1.88%)')
    )
    
    # Aval Rates
    aval_rate_libranza = models.DecimalField(
        _('aval rate - libranza'),
        max_digits=5,
        decimal_places=4,
        default=Decimal('7.05'),
        help_text=_('Aval monthly rate for payroll deduction credits')
    )
    aval_rate_high = models.DecimalField(
        _('aval rate - high amount'),
        max_digits=5,
        decimal_places=4,
        default=Decimal('4.05'),
        help_text=_('Aval monthly rate for credits > 5M')
    )
    aval_rate_low = models.DecimalField(
        _('aval rate - low amount'),
        max_digits=5,
        decimal_places=4,
        default=Decimal('7.05'),
        help_text=_('Aval monthly rate for credits <= 5M')
    )
    
    # IVA
    iva_rate = models.DecimalField(
        _('IVA rate'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('19.00'),
        help_text=_('IVA percentage')
    )
    
    # Status
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Whether this rate is currently active')
    )
    effective_date = models.DateField(
        _('effective date'),
        help_text=_('Date when this rate becomes effective')
    )
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='interest_rates_created',
        verbose_name=_('created by'),
        null=True,
        blank=True
    )
    notes = models.TextField(_('notes'), blank=True)

    class Meta:
        db_table = 'interest_rate_configs'
        verbose_name = _('interest rate configuration')
        verbose_name_plural = _('interest rate configurations')
        ordering = ['-year', '-month']
        indexes = [
            models.Index(fields=['year', 'month']),
            models.Index(fields=['effective_date']),
            models.Index(fields=['is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['year', 'month'],
                name='unique_rate_per_month'
            )
        ]

    def __str__(self):
        return f"{self.year}-{self.month:02d} | Usura: {self.usury_rate}% | Base: {self.base_interest_rate}%"

    @classmethod
    def get_current_rate(cls):
        """Get the current active interest rate configuration"""
        from datetime import date
        today = date.today()
        
        # Try to get exact month
        rate = cls.objects.filter(
            year=today.year,
            month=today.month,
            is_active=True
        ).first()
        
        if rate:
            return rate
        
        # Fallback: get most recent active rate
        return cls.objects.filter(is_active=True).first()

    @classmethod
    def get_rate_for_date(cls, reference_date):
        """Get interest rate configuration for a specific date"""
        rate = cls.objects.filter(
            year=reference_date.year,
            month=reference_date.month,
            is_active=True
        ).first()
        
        if rate:
            return rate
        
        # Fallback: get closest previous rate
        return cls.objects.filter(
            effective_date__lte=reference_date,
            is_active=True
        ).order_by('-effective_date').first()

    def save(self, *args, **kwargs):
        """
        Auto-calculate base_interest_rate from usury_rate if not set
        Formula: monthly_rate = (1 + annual_rate)^(1/12) - 1
        Where annual_rate is the usury rate (D14 in your Excel)
        """
        if not self.base_interest_rate and self.usury_rate:
            # Configurar precisión decimal
            getcontext().prec = 28
            getcontext().rounding = ROUND_HALF_UP
            
            # Convertir tasa de usura de porcentaje a decimal
            # Ejemplo: 25.01% -> 0.2501
            usury_decimal = self.usury_rate / Decimal('100')
            
            # Aplicar fórmula: (1 + D14)^(1/12) - 1
            base = Decimal('1') + usury_decimal
            exponent = Decimal('1') / Decimal('12')
            
            # Calcular potencia
            monthly_rate_decimal = base ** exponent - Decimal('1')
            
            # Convertir de decimal a porcentaje
            # Ejemplo: 0.0188 -> 1.88%
            monthly_rate_percent = monthly_rate_decimal * Decimal('100')
            
            # Guardar con 4 decimales
            self.base_interest_rate = monthly_rate_percent.quantize(Decimal('0.0001'))
        
        super().save(*args, **kwargs)
