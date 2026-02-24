"""
Credit models for Libramoneda platform
"""
from datetime import timedelta

from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal, getcontext, ROUND_HALF_UP
from apps.core.models import AuditableModel

# Configuración de precisión decimal
getcontext().prec = 28
getcontext().rounding = ROUND_HALF_UP


class CreditType(models.TextChoices):
    """Credit type choices"""
    LIBRANZA = 'LIBRANZA', _('Libranza (Payroll Deduction)')
    NATURAL = 'NATURAL', _('Natural Person')


class CreditStatus(models.TextChoices):
    """Credit status workflow"""
    PENDING = 'PENDING', _('Pending Approval')
    APPROVED = 'APPROVED', _('Approved')
    REJECTED = 'REJECTED', _('Rejected')
    DISBURSED = 'DISBURSED', _('Disbursed')
    ACTIVE = 'ACTIVE', _('Active')
    PAID = 'PAID', _('Paid Off')
    DEFAULTED = 'DEFAULTED', _('Defaulted')
    PAID_OFF = 'PAID_OFF', _('Paid Off')
    CANCELLED = 'CANCELLED', _('Cancelled')


class PaymentFrequency(models.TextChoices):
    """Payment frequency options"""
    MONTHLY = 'MONTHLY', _('Monthly')
    BIWEEKLY = 'BIWEEKLY', _('Biweekly')
    WEEKLY = 'WEEKLY', _('Weekly')


class Credit(AuditableModel):
    """
    Credit model with complete loan information and workflow
    Uses InterestRateConfig for rate management
    """
    # Credit Identification
    credit_number = models.CharField(
        _('credit number'),
        max_length=20,
        unique=True,
        db_index=True,
        help_text=_('Auto-generated unique credit number')
    )
    
    # Interest Rate Configuration
    interest_rate_config = models.ForeignKey(
        'core.InterestRateConfig',
        on_delete=models.PROTECT,
        related_name='credits',
        verbose_name=_('interest rate configuration'),
        null=True,
        blank=True,
        help_text=_('Interest rate configuration used for this credit')
    )
    
    # Customer and Type
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.PROTECT,
        related_name='credits',
        verbose_name=_('customer')
    )
    credit_type = models.CharField(
        _('credit type'),
        max_length=20,
        choices=CreditType.choices
    )
    
    # For LIBRANZA credits
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.PROTECT,
        related_name='credits',
        verbose_name=_('company'),
        null=True,
        blank=True,
        help_text=_('Required for libranza credits')
    )
    
    # Financial Terms - Requested
    requested_amount = models.DecimalField(
        _('requested amount'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('100000.00'))],
        help_text=_('Amount requested by customer in COP')
    )
    requested_term = models.PositiveIntegerField(
        _('requested term'),
        help_text=_('Requested term in months')
    )
    
    # Financial Terms - Approved
    approved_amount = models.DecimalField(
        _('approved amount'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Amount approved by credit approver in COP')
    )
    approved_term = models.PositiveIntegerField(
        _('approved term'),
        null=True,
        blank=True,
        help_text=_('Approved term in months')
    )
    
    # Tasas (copiadas de InterestRateConfig al aprobar)
    base_interest_rate = models.DecimalField(
        _('base monthly interest rate'),
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        help_text=_('Base monthly interest rate % (e.g., 1.88 for 1.88%)')
    )
    aval_rate = models.DecimalField(
        _('aval monthly rate'),
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        help_text=_('Aval monthly rate used for calculation (7.05% or 4.05%)')
    )
    iva_rate = models.DecimalField(
        _('IVA rate'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('IVA percentage (e.g., 19.00 for 19%)')
    )
    
    # Payment Details
    payment_frequency = models.CharField(
        _('payment frequency'),
        max_length=20,
        choices=PaymentFrequency.choices,
        default=PaymentFrequency.MONTHLY
    )
    
    # Desglose de cuota mensual
    monthly_payment = models.DecimalField(
        _('total monthly payment'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Total monthly payment (base + aval + IVA)')
    )
    monthly_payment_base = models.DecimalField(
        _('monthly payment base'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Monthly payment with base interest only (capital + interest)')
    )
    monthly_aval = models.DecimalField(
        _('monthly aval'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Monthly aval amount (difference between aval rate and base rate)')
    )
    monthly_iva_aval = models.DecimalField(
        _('monthly IVA on aval'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Monthly IVA on aval (19% of aval)')
    )
    
    # Totales del crédito
    total_amount = models.DecimalField(
        _('total amount to pay'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Total amount to pay (monthly_payment * term)')
    )
    total_interest = models.DecimalField(
        _('total interest'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Total interest to pay')
    )
    total_aval = models.DecimalField(
        _('total aval'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Total aval (monthly_aval * term)')
    )
    total_iva_aval = models.DecimalField(
        _('total IVA on aval'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Total IVA on aval (monthly_iva_aval * term)')
    )
    
    # Disbursement
    disbursement_date = models.DateField(
        _('disbursement date'),
        null=True,
        blank=True
    )
    disbursement_method = models.CharField(
        _('disbursement method'),
        max_length=50,
        blank=True,
        help_text=_('e.g., Bank transfer, Cash, Check')
    )
    
    # Current Status
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=CreditStatus.choices,
        default=CreditStatus.PENDING,
        db_index=True
    )
    balance = models.DecimalField(
        _('current balance'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Current outstanding balance (only capital)')
    )
    
    # Approval Workflow
    sales_advisor = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='credits_as_advisor',
        verbose_name=_('sales advisor'),
        help_text=_('User who created the credit application')
    )
    approved_by = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='credits_approved',
        verbose_name=_('approved by'),
        null=True,
        blank=True
    )
    approval_date = models.DateTimeField(
        _('approval date'),
        null=True,
        blank=True
    )
    approval_notes = models.TextField(
        _('approval notes'),
        blank=True
    )
    
    # Rejection
    rejection_reason = models.TextField(
        _('rejection reason'),
        blank=True
    )
    rejected_by = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='credits_rejected',
        verbose_name=_('rejected by'),
        null=True,
        blank=True
    )
    rejection_date = models.DateTimeField(
        _('rejection date'),
        null=True,
        blank=True
    )
    
    # Additional Information
    purpose = models.TextField(
        _('loan purpose'),
        help_text=_('Purpose of the loan')
    )
    notes = models.TextField(_('notes'), blank=True)

    class Meta:
        db_table = 'credits'
        verbose_name = _('credit')
        verbose_name_plural = _('credits')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['credit_number']),
            models.Index(fields=['customer']),
            models.Index(fields=['status']),
            models.Index(fields=['credit_type']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.credit_number} - {self.customer.get_full_name()} - ${self.requested_amount}"

    def save(self, *args, **kwargs):
        # Auto-generate credit number if not set
        if not self.credit_number:
            self.credit_number = self.generate_credit_number()
        
        # Track if status changed to DISBURSED
        is_being_disbursed = False
        if self.pk:
            try:
                old_instance = Credit.objects.get(pk=self.pk)
                if old_instance.status != CreditStatus.DISBURSED and self.status == CreditStatus.DISBURSED:
                    is_being_disbursed = True
            except Credit.DoesNotExist:
                pass
        
        # Assign interest rate config and rates when approved
        if self.status == CreditStatus.APPROVED:
            # If no config assigned, get the active one
            if not self.interest_rate_config:
                from apps.core.models import InterestRateConfig
                from datetime import date
                
                approval_date = self.approval_date.date() if self.approval_date else date.today()
                rate_config = InterestRateConfig.get_rate_for_date(approval_date)
                
                if rate_config:
                    self.interest_rate_config = rate_config
            
            # Copy rates from config
            if self.interest_rate_config and not self.base_interest_rate:
                self.base_interest_rate = self.interest_rate_config.base_interest_rate
                self.iva_rate = self.interest_rate_config.iva_rate
                
                # Select aval rate based on type and amount
                if self.credit_type == CreditType.LIBRANZA:
                    self.aval_rate = self.interest_rate_config.aval_rate_libranza
                elif self.approved_amount and self.approved_amount > Decimal('5000000'):
                    self.aval_rate = self.interest_rate_config.aval_rate_high
                else:
                    self.aval_rate = self.interest_rate_config.aval_rate_low
        
        # Calculate payment breakdown if approved and has all required data
        if (self.status == CreditStatus.APPROVED and 
            self.approved_amount and 
            self.approved_term and 
            self.base_interest_rate and
            self.aval_rate and
            self.iva_rate):
            self.calculate_and_save_payments()
        
        # Set balance when disbursed
        if self.status == CreditStatus.DISBURSED and self.balance == 0:
            self.balance = self.approved_amount
        
        # Save first
        super().save(*args, **kwargs)
        
        # Generate payment schedule ONLY when first disbursed
        if is_being_disbursed and not self.payments.exists():
            print("DEBUG: First disbursement - generating payment schedule...")
            self.generate_payment_schedule()

    def generate_credit_number(self):
        """Generate unique credit number"""
        from datetime import datetime
        year = datetime.now().year
        last_credit = Credit.objects.filter(
            credit_number__startswith=f'CR-{year}'
        ).order_by('-credit_number').first()
        
        if last_credit:
            last_number = int(last_credit.credit_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
        
        return f'CR-{year}-{new_number:05d}'

    def pmt(self, principal: Decimal, rate: Decimal, n: int) -> Decimal:
        """
        Cálculo PMT (sistema francés)
        rate_percent: tasa mensual en porcentaje (ej: 1.82 para 1.82%)
        """
        print(f"Calculating PMT with principal={principal}, rate_percent={rate}, n={n}")
        # rate = rate_percent / Decimal('1000')  # Convertir a decimal
        print(f"Converted rate to decimal: {rate}")
        if rate == 0:
            return (principal / Decimal(n)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        
        num = principal * rate
        den = Decimal(1) - (Decimal(1) + rate) ** Decimal(-n)
        result = num / den
        
        return result.quantize(Decimal('1'), rounding=ROUND_HALF_UP)

    def calculate_and_save_payments(self):
        """
        Calcula los pagos mensuales según la lógica de negocio
        Sigue EXACTAMENTE la lógica de build_schedule
        """
        P = self.approved_amount.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        n = self.approved_term
        
        # Tasas en decimal (NO porcentaje)
        i0 = self.base_interest_rate / Decimal('100')  # ej: 1.88% -> 0.0188
        i_aval = self.aval_rate / Decimal('100')  # ej: 7.05% -> 0.0705
        iva = self.iva_rate / Decimal('100')  # ej: 19% -> 0.19
        print(f"DEBUG: Calculating payments with P={P}, n={n}, i0={i0}, i_aval={i_aval}, iva={iva}")
        # CRITICAL: Tasa total = base + aval (como en build_schedule)
        i1 = i_aval  # ej: 0.0188 + 0.0705 = 0.0893
        
        # 1. Cuota base (solo interés base)
        pay_base = self.pmt(P, i0, n)
        self.monthly_payment_base = pay_base
        
        # 2. Cuota con aval (usando tasa TOTAL)
        pay_with_aval = self.pmt(P, i1, n)
        
        # 3. Aval mensual (diferencia entre cuota total y cuota base)
        aval_monthly = (pay_with_aval - pay_base).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        self.monthly_aval = aval_monthly
        
        # 4. IVA del aval
        iva_aval_monthly = (aval_monthly * iva).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        self.monthly_iva_aval = iva_aval_monthly
        
        # 5. Cuota total mensual
        payment_monthly = (pay_base + aval_monthly + iva_aval_monthly).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        self.monthly_payment = payment_monthly
        
        # # 6. Totales
        # self.total_aval = aval_monthly * n
        # self.total_iva_aval = iva_aval_monthly * n
        # self.total_amount = payment_monthly * n
        # self.total_interest = self.total_amount - P - self.total_aval - self.total_iva_aval

    def generate_payment_schedule(self):
        """
        Generate complete payment schedule (amortization table)
        Uses the 15-day rule for first payment
        Follows EXACT amortization logic from build_schedule
        """
        from datetime import date
        from calendar import monthrange
        from apps.payments.models import Payment, PaymentStatus
        
        # Delete existing payments if regenerating
        self.payments.all().delete()
        
        # Validate required data
        if not self.approved_amount or not self.approved_term:
            print("ERROR: Missing approved_amount or approved_term")
            return
        
        if not self.base_interest_rate or not self.aval_rate or not self.iva_rate:
            print("ERROR: Missing interest rates")
            return
        
        if not self.monthly_payment_base or not self.monthly_aval or not self.monthly_iva_aval:
            print("ERROR: Missing calculated payment amounts")
            return
        print(f"DEBUG: Monthly payment breakdown - Base: {self.monthly_payment_base}, Aval: {self.monthly_aval}, IVA Aval: {self.monthly_iva_aval}")
        # Initial values
        saldo = self.approved_amount
        start_date = self.disbursement_date or date.today()
        
        # Get company payment day for Libranza
        company_payment_day = None
        if self.credit_type == CreditType.LIBRANZA and self.company:
            company_payment_day = self.company.payment_day
        
        print(f"\n=== GENERATING PAYMENT SCHEDULE ===")
        print(f"Credit type: {self.credit_type}")
        print(f"Start date: {start_date}")
        print(f"Amount: ${saldo:,.0f}")
        print(f"Term: {self.approved_term} months")
        if company_payment_day:
            print(f"Company payment day: {company_payment_day}")
        
        # Monthly amounts
        payment_monthly = self.monthly_payment_base + self.monthly_aval + self.monthly_iva_aval
        aval_monthly = self.monthly_aval
        iva_aval = self.monthly_iva_aval
        
        # Interest rate as decimal (monthly)
        i0 = self.base_interest_rate / Decimal('100')
        
        payments = []
        
        # ========================================
        # FIRST PAYMENT - 15 DAY RULE
        # ========================================
        
        year = start_date.year
        month = start_date.month
        last_day = monthrange(year, month)[1]
        fin_mes_desembolso = date(year, month, last_day)
        
        # Apply 15-day rule
        if start_date.day <= 15:
            fecha_final_1 = fin_mes_desembolso
            dias_0 = (fin_mes_desembolso - start_date).days
        else:
            if month == 12:
                next_month = 1
                next_year = year + 1
            else:
                next_month = month + 1
                next_year = year
            last_day_next = monthrange(next_year, next_month)[1]
            fecha_final_1 = date(next_year, next_month, last_day_next)
            dias_0 = (fecha_final_1 - start_date).days
        
        dias_total_1 = dias_0
        
        # Calculate payment deadline for first payment
        first_deadline = self._calculate_payment_deadline(fecha_final_1, company_payment_day)
        
        # Interest calculation for first payment
        interes_primera = (saldo * i0 * Decimal(dias_0) / Decimal('30')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        interes_30 = (saldo * i0 * Decimal('30') / Decimal('30')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        interes_tramo_restante = (interes_30 - interes_primera).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        
        payment_first_month = payment_monthly - interes_tramo_restante
        
        # Capital for first payment
        abono_cap_1 = (payment_first_month - aval_monthly - iva_aval - interes_primera).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        if abono_cap_1 < 0:
            abono_cap_1 = Decimal('0')
        if abono_cap_1 > saldo:
            abono_cap_1 = saldo
        
        saldo_inicial_1 = saldo
        saldo = (saldo - abono_cap_1).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        valor_cuota_1 = (abono_cap_1 + aval_monthly + iva_aval + interes_primera).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        print(f"Initial capital: {abono_cap_1}, Interest: {interes_primera}, Balance before: {saldo_inicial_1}")

        payments.append(Payment(
            credit=self,
            payment_number=1,
            due_date=fecha_final_1,
            payment_deadline=first_deadline,
            period_days=dias_total_1,
            scheduled_capital=abono_cap_1,
            scheduled_interest=interes_primera,
            scheduled_aval=aval_monthly,
            scheduled_iva_aval=iva_aval,
            scheduled_total=valor_cuota_1,
            balance_before=saldo_inicial_1,
            status=PaymentStatus.PENDING
        ))
        

        # ========================================
        # REMAINING PAYMENTS (2 to N)
        # ========================================
        prev_final = fecha_final_1
        
        for k in range(2, self.approved_term + 1):
            # Next month's last day
            year = prev_final.year
            month = prev_final.month
            
            if month == 12:
                next_month = 1
                next_year = year + 1
            else:
                next_month = month + 1
                next_year = year
            
            last_day = monthrange(next_year, next_month)[1]
            fecha_inicial_k = prev_final + timedelta(days=1)
            fecha_final_k = date(next_year, next_month, last_day)
            
            # Calculate payment deadline
            deadline = self._calculate_payment_deadline(fecha_final_k, company_payment_day)
            
            # Calculate days in this period
            dias_k = (fecha_final_k - fecha_inicial_k).days
            print(f"dias_k {dias_k} for payment {k} (fecha_final_k {fecha_final_k}, fecha_inicial_k {fecha_inicial_k})")
            saldo_inicial_k = saldo
            
            # Interest for this payment
            interes_k = (saldo * i0 * Decimal(dias_k) / Decimal('30')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            
            # Capital calculation
            abono_cap_k = (payment_monthly - aval_monthly - iva_aval - interes_k).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            if abono_cap_k < 0:
                print(f"Warning: Negative capital for payment {k}, setting to 0")
                abono_cap_k = Decimal('0')
            
            # CRITICAL: Last payment adjustment BEFORE updating saldo
            if k == self.approved_term:
                abono_cap_k = saldo
                print(f"saldo before last payment: {saldo}")
            
            saldo = (saldo - abono_cap_k).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            valor_cuota_k = (abono_cap_k + interes_k + aval_monthly + iva_aval).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            
            payments.append(Payment(
                credit=self,
                payment_number=k,
                due_date=fecha_final_k,
                payment_deadline=deadline,
                period_days=dias_k,
                scheduled_capital=abono_cap_k,
                scheduled_interest=interes_k,
                scheduled_aval=aval_monthly,
                scheduled_iva_aval=iva_aval,
                scheduled_total=valor_cuota_k,
                balance_before=saldo_inicial_k,
                status=PaymentStatus.PENDING
            ))
            
            prev_final = fecha_final_k
        
        # Bulk create
        Payment.objects.bulk_create(payments)
        self.update_totals_from_schedule()

        print(f"✓ Generated {len(payments)} payments")
        print(f"First payment: {fecha_final_1} (deadline: {first_deadline}, {dias_total_1} days)")
        return payments
    
    def update_totals_from_schedule(self):
        """Recalculate totals based on generated payment schedule"""
        payments = self.payments.all()
        
        total_capital = Decimal('0')
        total_interest = Decimal('0')
        total_aval = Decimal('0')
        total_iva_aval = Decimal('0')
        total_amount = Decimal('0')

        for p in payments:
            total_capital += p.scheduled_capital
            total_interest += p.scheduled_interest
            total_aval += p.scheduled_aval
            total_iva_aval += p.scheduled_iva_aval
            total_amount += p.scheduled_total

        self.total_aval = total_aval
        self.total_iva_aval = total_iva_aval
        self.total_amount = total_amount
        self.total_interest = total_interest

        self.save(update_fields=[
            'total_aval',
            'total_iva_aval',
            'total_amount',
            'total_interest'
        ])
    
    def _calculate_payment_deadline(self, due_date, company_payment_day=None):
        """
        Calculate payment deadline based on credit type
        For LIBRANZA: company payment day of the NEXT month after due_date
        For others: same as due_date
        """
        if self.credit_type != CreditType.LIBRANZA or not company_payment_day:
            return due_date
        
        from datetime import date
        from calendar import monthrange
        
        # Get next month after due_date
        year = due_date.year
        month = due_date.month
        
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year
        
        # Get last day of next month
        last_day_of_next_month = monthrange(next_year, next_month)[1]
        
        # Use company payment day, but don't exceed last day of month
        payment_day = min(company_payment_day, last_day_of_next_month)
        
        return date(next_year, next_month, payment_day)
    
    def regenerate_payment_schedule(self):
        """
        Force regeneration of payment schedule
        Deletes existing payments and creates new ones
        Useful when rates, amounts, or dates change
        """
        print("\n" + "=" * 60)
        print("REGENERATING PAYMENT SCHEDULE")
        print("=" * 60)
        
        # Delete existing payments
        existing_count = self.payments.count()
        if existing_count > 0:
            print(f"Deleting {existing_count} existing payments...")
            self.payments.all().delete()
        
        # Recalculate payment amounts
        print("Recalculating payment amounts...")
        self.calculate_and_save_payments()
        
        # Save updated values
        super(Credit, self).save(update_fields=[
            'monthly_payment_base',
            'monthly_aval',
            'monthly_iva_aval',
            'monthly_payment',
            'total_aval',
            'total_iva_aval',
            'total_amount',
            'total_interest'
        ])
        
        # Generate new schedule
        print("Generating new payment schedule...")
        self.generate_payment_schedule()
        
        print(f"✓ Successfully regenerated {self.payments.count()} payments")
        print("=" * 60)
        
        return self.payments.all()
    
    @property
    def final_amount(self):
        """Get the final approved or requested amount"""
        return self.approved_amount or self.requested_amount

    @property
    def final_term(self):
        """Get the final approved or requested term"""
        return self.approved_term or self.requested_term

    @property
    def is_active(self):
        """Check if credit is currently active"""
        return self.status in [CreditStatus.DISBURSED, CreditStatus.ACTIVE]

    @property
    def is_paid_off(self):
        """Check if credit is fully paid"""
        return self.balance <= 0 or self.status == CreditStatus.PAID

    @property
    def has_overdue_payments(self):
        """Verificar si tiene pagos vencidos"""
        return self.payments.filter(
            status__in=['OVERDUE', 'PARTIAL']
        ).exists()
    
    @property
    def max_days_overdue(self):
        """Calcular la mora máxima de todos los pagos"""
        max_days = 0
        for payment in self.payments.filter(status__in=['PENDING', 'PARTIAL', 'OVERDUE']):
            if payment.days_overdue > max_days:
                max_days = payment.days_overdue
        return max_days
    
    @property
    def total_overdue_amount(self):
        """Total de dinero vencido (en mora)"""
        from decimal import Decimal
        total = Decimal('0')
        for payment in self.payments.filter(status__in=['OVERDUE', 'PARTIAL']):
            if payment.days_overdue > 0:
                total += payment.remaining_total
        return total
    
    def update_status_from_payments(self):
        """
        Actualizar estado del crédito basado en el estado de los pagos
        Reglas:
        - Balance = 0 → PAID_OFF
        - Mora >= 30 días → DEFAULTED
        - Mora 1-29 días → PAST_DUE
        - Mora 0 días → ACTIVE
        - DEFAULTED puede volver a ACTIVE solo si está totalmente al día
        """
        from datetime import date
        
        # Si no hay pagos, no hacer nada
        if not self.payments.exists():
            return
        
        # REGLA 1: Si balance = 0 → PAID_OFF
        if self.balance <= 0:
            if self.status != CreditStatus.PAID_OFF:
                old_status = self.status
                self.status = CreditStatus.PAID_OFF
                self.save(update_fields=['status'])
                print(f"✓ Credit {self.credit_number}: {old_status} → PAID_OFF")
            return
        
        # Calcular días de mora máximos
        max_days = self.max_days_overdue
        
        # REGLA 2: Si mora >= 30 días → DEFAULTED
        if max_days >= 30:
            if self.status != CreditStatus.DEFAULTED:
                old_status = self.status
                self.status = CreditStatus.DEFAULTED
                self.save(update_fields=['status'])
                print(f"✓ Credit {self.credit_number}: {old_status} → DEFAULTED ({max_days} days overdue)")
            return
        
        # REGLA 3: Si mora 1-29 días → PAST_DUE
        if max_days > 0:
            if self.status != CreditStatus.PAST_DUE:
                old_status = self.status
                self.status = CreditStatus.PAST_DUE
                self.save(update_fields=['status'])
                print(f"✓ Credit {self.credit_number}: {old_status} → PAST_DUE ({max_days} days overdue)")
            return
        
        # REGLA 4: Si mora = 0 días → ACTIVE (incluso si estaba DEFAULTED)
        if max_days == 0:
            if self.status not in [CreditStatus.ACTIVE, CreditStatus.PAID_OFF]:
                old_status = self.status
                self.status = CreditStatus.ACTIVE
                self.save(update_fields=['status'])
                print(f"✓ Credit {self.credit_number}: {old_status} → ACTIVE (now up to date)")