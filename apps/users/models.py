"""
User models for Libramoneda platform
"""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel
from .managers import UserManager


class Role(models.TextChoices):
    """User role choices"""
    SALES_ADVISOR = 'SALES_ADVISOR', _('Sales Advisor')
    CREDIT_APPROVER = 'CREDIT_APPROVER', _('Credit Approver')
    SUPERVISOR = 'SUPERVISOR', _('Supervisor')
    ACCOUNTING = 'ACCOUNTING', _('Accounting')
    ADMIN = 'ADMIN', _('Administrator')


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """
    Custom User model with Google SSO integration
    and enterprise domain validation
    """
    email = models.EmailField(
        _('email address'),
        unique=True,
        db_index=True,
        help_text=_('Must be from @libramoneda.com domain')
    )
    first_name = models.CharField(_('first name'), max_length=150)
    last_name = models.CharField(_('last name'), max_length=150)
    role = models.CharField(
        _('role'),
        max_length=20,
        choices=Role.choices,
        default=Role.SALES_ADVISOR
    )
    is_active = models.BooleanField(_('active'), default=True)
    is_staff = models.BooleanField(_('staff status'), default=False)
    google_id = models.CharField(
        _('Google ID'),
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )
    
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between"""
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        """Return the short name for the user"""
        return self.first_name

    @property
    def is_admin(self):
        """Check if user is admin"""
        return self.role == Role.ADMIN

    def has_role(self, role):
        """Check if user has specific role"""
        return self.role == role