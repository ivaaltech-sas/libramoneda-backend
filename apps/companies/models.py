"""
Company models for Libramoneda platform
Companies with payroll deduction agreements (convenio de libranza)
"""
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.utils.translation import gettext_lazy as _
from apps.core.models import AuditableModel


class CompanyStatus(models.TextChoices):
    """Company agreement status"""
    ACTIVE = 'ACTIVE', _('Activo')
    INACTIVE = 'INACTIVE', _('Inactivo')
    SUSPENDED = 'SUSPENDED', _('Suspendido')


class Company(AuditableModel):
    """
    Companies with payroll deduction agreements (convenio de libranza)
    """
    # Company Information
    nit = models.CharField(
        _('NIT'),
        max_length=20,
        unique=True,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r'^[0-9\-]+$',
                message=_('NIT must contain only digits and hyphens')
            )
        ]
    )
    business_name = models.CharField(
        _('business name'),
        max_length=200,
        help_text=_('Legal business name (Razón Social)')
    )
    trade_name = models.CharField(
        _('trade name'),
        max_length=200,
        blank=True,
        help_text=_('Commercial name (Nombre Comercial)')
    )
    
    # Contact Information
    phone_number = models.CharField(
        _('phone number'),
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message=_('Phone number must be valid')
            )
        ]
    )
    email = models.EmailField(_('email address'))
    website = models.URLField(_('website'), blank=True)
    
    # Address
    address = models.CharField(_('address'), max_length=255)
    city = models.CharField(_('city'), max_length=100)
    department = models.CharField(_('department/state'), max_length=100)
    
    # Agreement Details (Convenio)
    agreement_number = models.CharField(
        _('agreement number'),
        max_length=50,
        unique=True,
        help_text=_('Unique agreement/contract number')
    )
    agreement_date = models.DateField(_('agreement start date'))
    agreement_end_date = models.DateField(
        _('agreement end date'),
        null=True,
        blank=True,
        help_text=_('Leave empty for indefinite agreements')
    )
    
    payment_day = models.PositiveIntegerField(
        _('payment day'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text=_('Day of the month when the company pays salaries (1-31). Used for Libranza credits.')
    )
    
    # Status
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=CompanyStatus.choices,
        default=CompanyStatus.ACTIVE
    )
    
    # Contact Person
    contact_person_name = models.CharField(_('contact person name'), max_length=200)
    contact_person_position = models.CharField(
        _('contact person position'),
        max_length=100,
        blank=True
    )
    contact_person_phone = models.CharField(_('contact person phone'), max_length=15)
    contact_person_email = models.EmailField(_('contact person email'))
    
    # Additional
    notes = models.TextField(_('notes'), blank=True)

    class Meta:
        db_table = 'companies'
        verbose_name = _('company')
        verbose_name_plural = _('companies')
        ordering = ['business_name']
        indexes = [
            models.Index(fields=['nit']),
            models.Index(fields=['business_name']),
            models.Index(fields=['status']),
            models.Index(fields=['agreement_number']),
        ]

    def __str__(self):
        return f"{self.business_name} ({self.nit})"

    @property
    def is_active(self):
        """Check if company agreement is active"""
        return self.status == CompanyStatus.ACTIVE

    @property
    def display_name(self):
        """Return trade name if available, otherwise business name"""
        return self.trade_name or self.business_name
