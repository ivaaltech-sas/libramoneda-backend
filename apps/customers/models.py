"""
Customer models for Libramoneda platform
"""
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from apps.core.models import AuditableModel


class IdentificationType(models.TextChoices):
    """Identification document types"""
    CEDULA = 'CEDULA', _('Cédula de Ciudadanía')
    CEDULA_EXTRANJERIA = 'CEDULA_EXTRANJERIA', _('Cédula de Extranjería')
    PASAPORTE = 'PASAPORTE', _('Pasaporte')


class MaritalStatus(models.TextChoices):
    """Marital status options"""
    SINGLE = 'SINGLE', _('Soltero/a')
    MARRIED = 'MARRIED', _('Casado/a')
    DIVORCED = 'DIVORCED', _('Divorciado/a')
    WIDOWED = 'WIDOWED', _('Viudo/a')
    UNION = 'UNION', _('Unión Libre')


class Customer(AuditableModel):
    """
    Customer model - can be either employed (for libranza) or natural person
    """
    # Personal Information
    identification_type = models.CharField(
        _('identification type'),
        max_length=20,
        choices=IdentificationType.choices,
        default=IdentificationType.CEDULA
    )
    identification_number = models.CharField(
        _('identification number'),
        max_length=20,
        unique=True,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r'^[0-9]+$',
                message=_('Identification number must contain only digits')
            )
        ]
    )
    first_name = models.CharField(_('first name'), max_length=100)
    last_name = models.CharField(_('last name'), max_length=100)
    date_of_birth = models.DateField(_('date of birth'))
    marital_status = models.CharField(
        _('marital status'),
        max_length=20,
        choices=MaritalStatus.choices,
        default=MaritalStatus.SINGLE
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
    mobile_number = models.CharField(
        _('mobile number'),
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message=_('Mobile number must be valid')
            )
        ]
    )
    email = models.EmailField(_('email address'), blank=True)
    
    # Address
    address = models.CharField(_('address'), max_length=255)
    city = models.CharField(_('city'), max_length=100)
    department = models.CharField(_('department/state'), max_length=100)
    neighborhood = models.CharField(_('neighborhood'), max_length=100, blank=True)
    
    # Employment Information (for LIBRANZA credits)
    company = models.ForeignKey(
        'companies.Company',  # ⭐ Relación con la app companies
        on_delete=models.PROTECT,
        related_name='employees',
        verbose_name=_('company'),
        null=True,
        blank=True,
        help_text=_('Company where the customer works (for libranza credits)')
    )
    employee_code = models.CharField(
        _('employee code'),
        max_length=50,
        blank=True,
        help_text=_('Employee code/number in the company')
    )
    position = models.CharField(_('position/job title'), max_length=100, blank=True)
    hire_date = models.DateField(_('hire date'), null=True, blank=True)
    monthly_salary = models.DecimalField(
        _('monthly salary'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Monthly salary in COP')
    )
    
    # For NATURAL PERSON credits
    occupation = models.CharField(
        _('occupation'),
        max_length=100,
        blank=True,
        help_text=_('For self-employed or natural persons')
    )
    monthly_income = models.DecimalField(
        _('monthly income'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Monthly income for natural persons in COP')
    )
    
    # Additional Financial Information
    has_other_credits = models.BooleanField(
        _('has other credits'),
        default=False
    )
    other_credits_total = models.DecimalField(
        _('total other credits'),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    notes = models.TextField(_('notes'), blank=True)

    class Meta:
        db_table = 'customers'
        verbose_name = _('customer')
        verbose_name_plural = _('customers')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['identification_number']),
            models.Index(fields=['first_name', 'last_name']),
            models.Index(fields=['company']),
            models.Index(fields=['-created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'employee_code'],
                name='unique_employee_per_company',
                condition=models.Q(company__isnull=False, employee_code__gt='')
            )
        ]

    def __str__(self):
        return f"{self.get_full_name()} - {self.identification_number}"

    def get_full_name(self):
        """Return the full name"""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def age(self):
        """Calculate age from date of birth"""
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def is_employee(self):
        """Check if customer is an employee (has company)"""
        return self.company is not None

    @property
    def total_income(self):
        """Get total monthly income"""
        if self.company:
            return self.monthly_salary
        return self.monthly_income or 0
