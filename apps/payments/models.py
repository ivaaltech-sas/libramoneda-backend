"""
Payment models for Libramoneda platform
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from apps.core.models import AuditableModel


class PaymentStatus(models.TextChoices):
    """Payment status choices"""
    PENDING = 'PENDING', _('Pending')
    PAID = 'PAID', _('Paid')
    LATE = 'LATE', _('Late')
    PARTIAL = 'PARTIAL', _('Partially Paid')
    CANCELLED = 'CANCELLED', _('Cancelled')


class Payment(AuditableModel):
    """
    Payment model - represents each installment of a credit
    Includes complete breakdown: capital, interest, aval, IVA
    """
    # Relationship
    credit = models.ForeignKey(
        'credits.Credit',
        on_delete=models.PROTECT,
        related_name='payments',
        verbose_name=_('credit')
    )
    
    # Payment identification
    payment_number = models.PositiveIntegerField(
        _('payment number'),
        help_text=_('Sequential payment number (1, 2, 3...)')
    )
    
    # Payment dates
    due_date = models.DateField(
        _('due date'),
        db_index=True,
        help_text=_('Date when payment is due')
    )
    payment_date = models.DateField(
        _('payment date'),
        null=True,
        blank=True,
        help_text=_('Actual date when payment was made')
    )
    
    # Payment breakdown (scheduled amounts)
    scheduled_capital = models.DecimalField(
        _('scheduled capital'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Scheduled capital portion for this payment')
    )
    scheduled_interest = models.DecimalField(
        _('scheduled interest'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Scheduled interest portion for this payment')
    )
    scheduled_aval = models.DecimalField(
        _('scheduled aval'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Scheduled aval portion for this payment')
    )
    scheduled_iva_aval = models.DecimalField(
        _('scheduled IVA on aval'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Scheduled IVA on aval for this payment')
    )
    scheduled_total = models.DecimalField(
        _('scheduled total'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Total scheduled payment amount')
    )
    
    # Actual amounts paid
    paid_capital = models.DecimalField(
        _('paid capital'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Actual capital paid')
    )
    paid_interest = models.DecimalField(
        _('paid interest'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Actual interest paid')
    )
    paid_aval = models.DecimalField(
        _('paid aval'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Actual aval paid')
    )
    paid_iva_aval = models.DecimalField(
        _('paid IVA on aval'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Actual IVA on aval paid')
    )
    paid_total = models.DecimalField(
        _('paid total'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Total amount actually paid')
    )
    
    # Late payment fees
    late_fee = models.DecimalField(
        _('late fee'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Late payment fee charged')
    )
    
    # Balance tracking
    balance_before = models.DecimalField(
        _('balance before payment'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Outstanding balance before this payment')
    )
    balance_after = models.DecimalField(
        _('balance after payment'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Outstanding balance after this payment')
    )
    
    # Status
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True
    )
    
    # Payment dates
    due_date = models.DateField(
        _('due date'),
        db_index=True,
        help_text=_('Date when payment is due (end of month)')
    )
    
    payment_deadline = models.DateField(
        _('payment deadline'),
        null=True,
        blank=True,
        help_text=_('Final deadline for payment. For Libranza: company payment day. For others: same as due_date.')
    )
    
    payment_date = models.DateField(
        _('payment date'),
        null=True,
        blank=True,
        help_text=_('Actual date when payment was made')
    )
    
    # Period information
    period_days = models.PositiveIntegerField(
        _('period days'),
        null=True,
        blank=True,
        help_text=_('Number of days in this payment period')
    )
    
    # Payment details
    payment_method = models.CharField(
        _('payment method'),
        max_length=50,
        blank=True,
        help_text=_('e.g., Bank transfer, Cash, Card, Payroll deduction')
    )
    transaction_reference = models.CharField(
        _('transaction reference'),
        max_length=100,
        blank=True,
        help_text=_('Bank reference or transaction ID')
    )
    
    # Additional information
    notes = models.TextField(_('notes'), blank=True)

    class Meta:
        db_table = 'payments'
        verbose_name = _('payment')
        verbose_name_plural = _('payments')
        ordering = ['credit', 'payment_number']
        unique_together = [['credit', 'payment_number']]
        indexes = [
            models.Index(fields=['credit', 'payment_number']),
            models.Index(fields=['due_date']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_date']),
        ]

    def __str__(self):
        return f"{self.credit.credit_number} - Payment #{self.payment_number} - {self.due_date}"

    def save(self, *args, **kwargs):
        # Update status based on payment
        if self.paid_total >= self.scheduled_total:
            self.status = PaymentStatus.PAID
            # Calculate balance after
            self.balance_after = self.balance_before - self.paid_capital
        elif self.paid_total > 0:
            self.status = PaymentStatus.PARTIAL
        elif self.due_date < date.today() and self.status == PaymentStatus.PENDING:
            self.status = PaymentStatus.LATE
        
        super().save(*args, **kwargs)
        
        # Update credit balance
        if self.status == PaymentStatus.PAID:
            self.credit.balance = self.balance_after
            self.credit.save(update_fields=['balance'])

    @property
    def is_overdue(self):
        """Check if payment is overdue"""
        return self.due_date < date.today() and self.status in [PaymentStatus.PENDING, PaymentStatus.PARTIAL]

    @property
    def days_overdue(self):
        """Calculate days overdue"""
        if self.is_overdue:
            return (date.today() - self.due_date).days
        return 0

    @property
    def remaining_amount(self):
        """Calculate remaining amount to pay"""
        return self.scheduled_total - self.paid_total
