from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from apps.core.models import AuditableModel


class PaymentStatus(models.TextChoices):
    """Payment status choices"""
    PENDING = 'PENDING', _('Pending')
    PARTIAL = 'PARTIAL', _('Partially Paid')
    PAID = 'PAID', _('Paid')
    OVERDUE = 'OVERDUE', _('Overdue')
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
        default=Decimal('0'),
        help_text=_('Actual capital paid')
    )
    paid_interest = models.DecimalField(
        _('paid interest'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        help_text=_('Actual interest paid')
    )
    paid_aval = models.DecimalField(
        _('paid aval'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        help_text=_('Actual aval paid')
    )
    paid_iva_aval = models.DecimalField(
        _('paid IVA on aval'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        help_text=_('Actual IVA on aval paid')
    )
    paid_late_interest = models.DecimalField(
        _('paid late interest'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        help_text=_('Actual late interest paid')
    )
    paid_total = models.DecimalField(
        _('paid total'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        help_text=_('Total amount actually paid')
    )
    
    # Late payment fields (MORA)
    late_interest_rate = models.DecimalField(
        _('late interest rate'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0'),
        help_text=_('Monthly late interest rate (e.g., 3.00 for 3%)')
    )
    
    calculated_late_interest = models.DecimalField(
        _('calculated late interest'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        help_text=_('Calculated but not yet applied late interest')
    )
    
    applied_late_interest = models.DecimalField(
        _('applied late interest'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0'),
        help_text=_('Late interest that has been applied to this payment')
    )
    
    late_interest_calculated_date = models.DateField(
        _('late interest calculation date'),
        null=True,
        blank=True,
        help_text=_('Last date when late interest was calculated')
    )
    
    late_interest_applied_date = models.DateField(
        _('late interest applied date'),
        null=True,
        blank=True,
        help_text=_('Date when late interest was applied')
    )
    
    # Balance tracking
    balance_before = models.DecimalField(
        _('balance before payment'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Outstanding balance before this payment')
    )
    
    # Status
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True
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
            models.Index(fields=['payment_deadline']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_date']),
        ]

    def __str__(self):
        return f"Payment #{self.payment_number} - {self.credit.credit_number}"
    
    # Properties
    @property
    def remaining_capital(self):
        return self.scheduled_capital - self.paid_capital
    
    @property
    def remaining_interest(self):
        return self.scheduled_interest - self.paid_interest
    
    @property
    def remaining_aval(self):
        return self.scheduled_aval - self.paid_aval
    
    @property
    def remaining_iva(self):
        return self.scheduled_iva_aval - self.paid_iva_aval
    
    @property
    def remaining_late_interest(self):
        return self.applied_late_interest - self.paid_late_interest
    
    @property
    def remaining_total(self):
        """Total remaining including applied late interest"""
        return (
            self.remaining_capital +
            self.remaining_interest +
            self.remaining_aval +
            self.remaining_iva +
            self.remaining_late_interest
        )
    
    @property
    def days_overdue(self):
        """Calculate days overdue from payment_deadline"""
        if self.status == PaymentStatus.PAID:
            return 0
        
        deadline = self.payment_deadline or self.due_date
        today = date.today()
        
        if today > deadline:
            return (today - deadline).days
        return 0
    
    @property
    def is_overdue(self):
        """Check if payment is overdue"""
        return self.days_overdue > 0
    
    def calculate_late_interest(self, as_of_date=None, rate=None):
        """
        Calculate late interest but DON'T apply it yet
        Returns the calculated amount
        """
        as_of_date = as_of_date or date.today()
        deadline = self.payment_deadline or self.due_date
        
        # No late interest if not overdue
        if as_of_date <= deadline:
            return Decimal('0')
        
        # Use provided rate or get from credit's rate config
        if rate is None:
            if self.credit.interest_rate_config and hasattr(self.credit.interest_rate_config, 'late_interest_rate'):
                rate = self.credit.interest_rate_config.late_interest_rate
            else:
                rate = self.late_interest_rate or Decimal('0')
        
        if rate == 0:
            return Decimal('0')
        
        # Calculate days overdue
        days_late = (as_of_date - deadline).days
        
        # Late interest on remaining balance
        overdue_amount = self.remaining_total
        
        # Monthly rate to daily
        daily_rate = rate / Decimal('100') / Decimal('30')
        
        # Calculate late interest
        late_interest = (overdue_amount * daily_rate * Decimal(days_late)).quantize(
            Decimal('1'), 
            rounding=ROUND_HALF_UP
        )
        
        return late_interest
    
    def apply_late_interest(self, as_of_date=None, rate=None):
        """
        Calculate AND apply late interest to this payment
        This is MANUAL - only called when user triggers it
        """
        calculated = self.calculate_late_interest(as_of_date, rate)
        
        if calculated > 0:
            self.calculated_late_interest = calculated
            self.applied_late_interest = calculated
            self.late_interest_calculated_date = as_of_date or date.today()
            self.late_interest_applied_date = date.today()
            self.save(update_fields=[
                'calculated_late_interest',
                'applied_late_interest',
                'late_interest_calculated_date',
                'late_interest_applied_date'
            ])
            
            print(f"✓ Applied late interest of ${calculated:,.0f} to Payment #{self.payment_number}")
        
        return calculated
    
    def apply_payment(self, amount, transaction_date, payment_method='CASH', reference='', notes=''):
        """
        Apply a payment to this Payment installment
        Follows waterfall: Late Interest → Interest → Aval → IVA → Capital
        """
        remaining = Decimal(str(amount))
        breakdown = {
            'late_interest': Decimal('0'),
            'interest': Decimal('0'),
            'aval': Decimal('0'),
            'iva': Decimal('0'),
            'capital': Decimal('0'),
        }
        
        # 1. Apply to late interest first
        late_interest_due = self.remaining_late_interest
        if late_interest_due > 0 and remaining > 0:
            applied = min(remaining, late_interest_due)
            breakdown['late_interest'] = applied
            self.paid_late_interest += applied
            remaining -= applied
        
        # 2. Apply to interest
        interest_due = self.remaining_interest
        if interest_due > 0 and remaining > 0:
            applied = min(remaining, interest_due)
            breakdown['interest'] = applied
            self.paid_interest += applied
            remaining -= applied
        
        # 3. Apply to aval
        aval_due = self.remaining_aval
        if aval_due > 0 and remaining > 0:
            applied = min(remaining, aval_due)
            breakdown['aval'] = applied
            self.paid_aval += applied
            remaining -= applied
        
        # 4. Apply to IVA
        iva_due = self.remaining_iva
        if iva_due > 0 and remaining > 0:
            applied = min(remaining, iva_due)
            breakdown['iva'] = applied
            self.paid_iva_aval += applied
            remaining -= applied
        
        # 5. Apply to capital
        capital_due = self.remaining_capital
        if capital_due > 0 and remaining > 0:
            applied = min(remaining, capital_due)
            breakdown['capital'] = applied
            self.paid_capital += applied
            remaining -= applied
        
        # Update total paid
        self.paid_total += amount
        
        # Update payment date if first payment
        if not self.payment_date:
            self.payment_date = transaction_date
        
        # Update status
        self._update_status()
        
        # Save payment
        self.save()
        
        # Create transaction record
        transaction = PaymentTransaction.objects.create(
            payment=self,
            transaction_date=transaction_date,
            amount=amount,
            payment_method=payment_method,
            reference_number=reference,
            applied_to_late_interest=breakdown['late_interest'],
            applied_to_interest=breakdown['interest'],
            applied_to_aval=breakdown['aval'],
            applied_to_iva=breakdown['iva'],
            applied_to_capital=breakdown['capital'],
            notes=notes
        )
        
        # Update credit balance
        if breakdown['capital'] > 0:
            self.credit.balance -= breakdown['capital']
            self.credit.save(update_fields=['balance'])
            
        self.credit.update_status_from_payments()
        
        print(f"✓ Payment of ${amount:,.0f} applied to Payment #{self.payment_number}")
        print(f"  Breakdown: Late Interest=${breakdown['late_interest']:,.0f}, "
              f"Interest=${breakdown['interest']:,.0f}, Aval=${breakdown['aval']:,.0f}, "
              f"IVA=${breakdown['iva']:,.0f}, Capital=${breakdown['capital']:,.0f}")
        
        return transaction
    
    def _update_status(self):
        """Update payment status based on amounts paid"""
        tolerance = Decimal('10')  # $10 tolerance for rounding
        
        total_due = self.scheduled_total + self.applied_late_interest
        
        if self.paid_total >= (total_due - tolerance):
            self.status = PaymentStatus.PAID
        elif self.paid_total > 0:
            self.status = PaymentStatus.PARTIAL
        elif self.days_overdue > 0:
            self.status = PaymentStatus.OVERDUE
        else:
            self.status = PaymentStatus.PENDING


class PaymentTransaction(AuditableModel):
    """
    Individual payment transactions
    Multiple transactions can be applied to a single Payment
    Records each payment received from the customer
    """
    payment = models.ForeignKey(
        'Payment',
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name=_('payment')
    )
    
    # Transaction details
    transaction_date = models.DateField(
        _('transaction date'),
        db_index=True,
        help_text=_('Date when payment was received')
    )
    
    amount = models.DecimalField(
        _('amount'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Amount received in this transaction')
    )
    
    # Payment method
    PAYMENT_METHOD_CHOICES = [
        ('CASH', _('Cash')),
        ('BANK_TRANSFER', _('Bank Transfer')),
        ('CARD', _('Card')),
        ('PSE', _('PSE')),
        ('CHECK', _('Check')),
        ('PAYROLL_DEDUCTION', _('Payroll Deduction')),
        ('OTHER', _('Other')),
    ]
    
    payment_method = models.CharField(
        _('payment method'),
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES,
        default='CASH'
    )
    
    reference_number = models.CharField(
        _('reference number'),
        max_length=100,
        blank=True,
        help_text=_('Transaction reference (e.g., transfer number, check number)')
    )
    
    # Application breakdown (how the payment was distributed)
    applied_to_late_interest = models.DecimalField(
        _('applied to late interest'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0')
    )
    
    applied_to_interest = models.DecimalField(
        _('applied to interest'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0')
    )
    
    applied_to_aval = models.DecimalField(
        _('applied to aval'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0')
    )
    
    applied_to_iva = models.DecimalField(
        _('applied to IVA'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0')
    )
    
    applied_to_capital = models.DecimalField(
        _('applied to capital'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0')
    )
    
    notes = models.TextField(
        _('notes'),
        blank=True
    )
    
    class Meta:
        db_table = 'payment_transactions'
        verbose_name = _('payment transaction')
        verbose_name_plural = _('payment transactions')
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['payment', '-transaction_date']),
            models.Index(fields=['transaction_date']),
            models.Index(fields=['payment_method']),
        ]
    
    def __str__(self):
        return f"${self.amount:,.0f} - {self.payment} - {self.transaction_date}"
    
    @property
    def total_applied(self):
        """Total amount applied (should equal amount)"""
        return (
            self.applied_to_late_interest +
            self.applied_to_interest +
            self.applied_to_aval +
            self.applied_to_iva +
            self.applied_to_capital
        )