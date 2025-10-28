from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from decimal import Decimal
from core.models import Contract, Staff
from django.utils.translation import gettext_lazy as _
from django_weasyprint import WeasyTemplateResponseMixin
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
import uuid

# Create your models here.

def payslip_upload_path(instance, filename):
    """
    Generate path: payslips/<unique_id>/<year>/<filename>
    """
    unique_id = instance.staff.unique_id
    year = instance.pay_period_start.strftime('%Y')
    # Optional: add month
    # month = instance.pay_period_start.strftime('%m')
    # return f'payslips/{unique_id}/{year}/{month}/{filename}'
    
    return f'payslips/{year}/{unique_id}/{filename}'
class Payroll(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    staff = models.ForeignKey(
        'core.Staff',
        on_delete=models.CASCADE,
        related_name='payroll_identity',
        verbose_name=_("Staff")
    )
    contract = models.ForeignKey(
        'core.Contract',
        on_delete=models.CASCADE,
        related_name='payroll_contract',
        verbose_name=_("Contract")
    )
    pay_period_start = models.DateField(verbose_name=_("Pay Period Start"))
    pay_period_end = models.DateField(verbose_name=_("Pay Period End"))
    gross_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Gross Salary")
    )
    total_deductions = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
        verbose_name=_("Total Deductions")
    )
    net_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
        verbose_name=_("Net Salary")
    )
    kra_pin = models.CharField(
        max_length=11,
        unique=True,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^[A-Za-z][0-9]{9}[A-Za-z]$', 'KRA PIN must be 11 characters: 1 letter, 9 digits, 1 letter')],
        verbose_name=_("KRA PIN")
    )
    bank_name = models.CharField(max_length=100, verbose_name=_("Bank Name"))
    bank_branch = models.CharField(max_length=100, verbose_name=_("Bank Branch"))
    bank_branch_code = models.CharField(max_length=20, verbose_name=_("Bank Branch Code"))
    account_no = models.CharField(max_length=20, verbose_name=_("Account Number"))
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Generated At"))
    pdf_file = models.FileField(
        upload_to=payslip_upload_path,
        blank=True,
        null=True,
        verbose_name=_("Payslip PDF")
    )

    class Meta:
        ordering = ['-pay_period_end']
        verbose_name = _('Payroll')
        verbose_name_plural = _('Payrolls')
        unique_together = ['staff', 'pay_period_start', 'pay_period_end']

    def __str__(self):
        return f"{self.staff_name} {self.staff_unique_id} - {self.pay_period_start} to {self.pay_period_end}"

    @property
    def staff_name(self):
        """Fetch full name from Staff model"""
        return getattr(self.staff, 'full_name', 'Unknown')

    @property
    def staff_national_id(self):
        """Fetch national ID from Staff model"""
        return getattr(self.staff, 'national_id', 'N/A')
    
    @property
    def staff_unique_id(self):
        """Fetch unique ID from Staff model"""
        return getattr(self.staff, 'unique_id', 'N/A')

    @property
    def engagement_date(self):
        """Fetch engagement date from Contract"""
        return self.contract.start_date if self.contract else None

    @property
    def expiry_date(self):
        """Fetch expiry date from Contract"""
        return self.contract.end_date if self.contract else None

    def calculate_deductions(self):
        """Calculate total deductions based on global and contract-specific deductions"""
        total = Decimal('0.00')
        
        # Mandatory deductions (global)
        mandatory_deductions = Deduction.objects.filter(
            deduction_type='MANDATORY',
            is_active=True
        )
        for deduction in mandatory_deductions:
            total += deduction.calculate_amount(self.gross_salary)

        # Optional deductions (contract-specific overrides)
        contract_deductions = ContractDeduction.objects.filter(
            contract=self.contract,
            is_active=True
        )
        for cd in contract_deductions:
            total += cd.calculate_amount(self.gross_salary)

        return total
    
    def get_mandatory_deductions(self):
        salary = self.gross_salary
        deductions = []
        for d in Deduction.objects.filter(deduction_type='MANDATORY', is_active=True):
            amt = d.calculate_amount(salary)
            if amt > 0:
                deductions.append({'name': d.name, 'amount': amt})
        return deductions

    def get_contract_deductions(self):
        salary = self.gross_salary
        deductions = []
        for cd in ContractDeduction.objects.filter(contract=self.contract, is_active=True):
            amt = cd.calculate_amount(salary)
            if amt > 0:
                deductions.append({
                    'deduction': cd.deduction,
                    'custom_percentage': cd.custom_percentage,
                    'fixed_amount': cd.fixed_amount,
                    'amount': amt
                })
        return deductions
    
    def generate_pdf(self):
        """Generate PDF payslip and save to pdf_file"""
        from django.conf import settings

        # Render the same detail template as HTML string
        html_string = render_to_string('payroll_pdf.html', {
            'payroll': self,
            'mandatory_deductions': self.get_mandatory_deductions(),
            'contract_deductions': self.get_contract_deductions(),
            'staff': self.staff,
        })

        # Convert HTML to PDF
        from weasyprint import HTML
        pdf_file = HTML(string=html_string, base_url=settings.MEDIA_ROOT).write_pdf()

        # Save to model
        filename = f"payslip_{self.staff.unique_id}_{self.pay_period_start.strftime('%m')}.pdf"
        self.pdf_file.save(filename, ContentFile(pdf_file), save=False)

    def save(self, *args, **kwargs):
        # Auto-calculate totals (existing logic)
        self.total_deductions = self.calculate_deductions()
        self.net_salary = self.gross_salary - self.total_deductions
        super().save(*args, **kwargs)


class Deduction(models.Model):
    DEDUCTION_TYPES = (
        ('MANDATORY', 'Mandatory'),
        ('VOLUNTARY', 'Voluntary'),
        ('LOAN', 'Loan'),
    )
    
    name = models.CharField(max_length=100, verbose_name=("Deduction Name"))
    percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=("Percentage Cut (%)")
    )
    description = models.TextField(verbose_name=("Description"))
    deduction_type = models.CharField(
        max_length=20, 
        choices=DEDUCTION_TYPES, 
        default='MANDATORY',
        verbose_name=("Deduction Type")
    )
    is_active = models.BooleanField(default=True, verbose_name=("Is Active"))
    applies_to_contract_types = models.ManyToManyField(
        Contract, 
        related_name='applicable_deductions',
        blank=True,
        verbose_name=("Applies to Contract Types")
    )
    min_salary_threshold = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=("Minimum Salary Threshold"),
        help_text=("Deduction only applies if salary is above this amount")
    )
    max_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=("Maximum Deduction Amount"),
        help_text=("Maximum amount to deduct (overrides percentage if set)")
    )
    
    # Auto fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = ('Deduction')
        verbose_name_plural = ('Deductions')
        unique_together = ['name', 'percentage']  # Prevent duplicate deductions
    
    def __str__(self):
        return f"{self.name} ({self.percentage}%)"
    
    @property
    def is_mandatory(self):
        return self.deduction_type == 'MANDATORY'
    
    def calculate_amount(self, salary):
        """Calculate deduction amount based on salary"""
        if not self.is_active:
            return Decimal('0.00')
        
        # Check salary threshold
        if salary < self.min_salary_threshold:
            return Decimal('0.00')
        
        if self.max_amount:
            # Use whichever is smaller: percentage or max_amount
            percentage_amount = (salary * self.percentage / 100)
            return min(percentage_amount, self.max_amount)
        else:
            # Simple percentage calculation
            return salary * self.percentage / 100
    
    def get_display_percentage(self):
        return f"{self.percentage}%"
    
    def get_display_amount(self, salary):
        amount = self.calculate_amount(salary)
        return f"KSh {amount:,.2f}"
    
class ContractDeduction(models.Model):
    """Contract-specific deduction overrides"""
    
    contract = models.ForeignKey(
        Contract, 
        on_delete=models.CASCADE, 
        related_name='deduction_overrides'
    )
    deduction = models.ForeignKey(
        Deduction, 
        on_delete=models.CASCADE,
        limit_choices_to={'deduction_type__in': ['VOLUNTARY', 'LOAN']}
    )
    
    # Override options: EITHER percentage OR fixed amount
    custom_percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=("Custom Percentage (%)")
    )
    
    fixed_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=("Fixed Amount (KSh)")
    )
    
    is_active = models.BooleanField(default=True)
    
    # Auto fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['contract', 'deduction']  # One override per deduction per contract
        verbose_name = ('Contract Deduction Override')
        verbose_name_plural = ('Contract Deduction Overrides')
    
    def __str__(self):
        if self.custom_percentage:
            return f"{self.deduction.name}: {self.custom_percentage}%"
        elif self.fixed_amount:
            return f"{self.deduction.name}: KSh {self.fixed_amount}"
        return f"{self.deduction.name} (No Override)"
    
    def clean(self):
        """Ensure only ONE of percentage or fixed_amount is set"""
        from django.core.exceptions import ValidationError
        
        if self.custom_percentage and self.fixed_amount:
            raise ValidationError(
                "Specify EITHER custom percentage OR fixed amount, not both."
            )
        
        if not self.custom_percentage and not self.fixed_amount:
            raise ValidationError(
                "Must specify EITHER custom percentage OR fixed amount."
            )
    
    def calculate_amount(self, salary):
        """Calculate based on override"""
        if not self.is_active:
            return Decimal('0.00')
        
        if self.custom_percentage is not None:
            return salary * self.custom_percentage / 100
        elif self.fixed_amount is not None:
            return self.fixed_amount
        return Decimal('0.00')
    
    @property
    def override_type(self):
        if self.custom_percentage is not None:
            return 'PERCENTAGE'
        elif self.fixed_amount is not None:
            return 'FIXED'
        return None
    
    