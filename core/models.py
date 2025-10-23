from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from datetime import timedelta
import uuid
from decimal import Decimal

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Department Name"))
    code = models.CharField(
        max_length=3,
        unique=True,
        validators=[RegexValidator(r'^[A-Z]{3}$', 'Code must be 3 uppercase letters')],
        verbose_name=_("Department Code")
    )
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ['name']

class Staff(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    EMPLOYMENT_CATEGORY_CHOICES = [
        ('LOCUM', 'Locum'),
        ('CASUAL', 'Casual'),
        ('PERMANENT', 'Permanent and Pentionable'),
    ]

    EMPLOYMENT_STATUS_CHOICES = (
        ('AWAITING CONTRACT', 'Awaiting Contract'),
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('TERMINATED', 'Terminated'),
        ('RENEWED', 'Renewed'),
        ('PENDING', 'Pending Renewal'),
        ('INACTIVE', 'Inactive'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("User Account"))
    first_name = models.CharField(max_length=50, verbose_name=_("First Name"))
    middle_name = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Middle Name"))
    last_name = models.CharField(max_length=50, verbose_name=_("Last Name"))
    email = models.EmailField(unique=True, verbose_name=_("Email"))
    phone = models.CharField(max_length=15, verbose_name=_("Phone Number"))
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name=_("Gender"))
    date_of_birth = models.DateField(verbose_name=_("Date of Birth"))
    national_id = models.CharField(max_length=20, unique=True, verbose_name=_("National ID"))
    address = models.TextField(verbose_name=_("Address"))
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='staff_members', verbose_name=_("Department"))
    designation = models.CharField(max_length=100, verbose_name=_("Position"))
    employment_date = models.DateField(verbose_name=_("Employment Date"))
    employment_category = models.CharField(max_length=20, choices=EMPLOYMENT_CATEGORY_CHOICES)
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name=_("Salary"))
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Emergency Contact Name"))
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True, verbose_name=_("Emergency Contact Phone"))
    emergency_contact_relationship = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Emergency Contact Relationship"))
    employment_status = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_STATUS_CHOICES,
        verbose_name=_("Employment Status"),
        default='AWAITING CONTRACT'
    )
    kra_pin = models.CharField(
        max_length=11,
        unique=True,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^[A-Za-z][0-9]{9}[A-Za-z]$', 'KRA PIN must be 11 characters: 1 letter, 9 digits, 1 letter')],
        verbose_name=_("KRA PIN")
    )
    unique_id = models.CharField(max_length=30, unique=True, editable=False, verbose_name=_("Unique ID"))
    is_admin = models.BooleanField(default=False, verbose_name=_("Is Admin"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.unique_id:
            if not self.national_id:
                raise ValueError("National ID is required to generate unique ID")
            if not self.employment_date:
                raise ValueError("Employment date is required to generate unique ID")
            clean_national_id = ''.join(c for c in self.national_id if c.isalnum())
            self.unique_id = f"MLKH{clean_national_id}{self.employment_date.year}"

        # Create or update associated User account
        if not self.user:
            try:
                if User.objects.filter(username=self.unique_id).exists():
                    # If username already exists, assign the user instead of creating a new one
                    self.user = User.objects.get(username=self.unique_id)
                else:
                    user = User.objects.create_user(
                        username=self.unique_id,
                        email=self.email,
                        password=self.national_id,
                        first_name=self.first_name,
                        last_name=self.last_name
                    )
                    self.user = user
            except Exception as e:
                raise ValueError(f"Failed to create or assign user account: {str(e)}")
        else:
            # Update existing user info
            user = self.user
            user.first_name = self.first_name
            user.last_name = self.last_name
            user.email = self.email
            user.username = self.unique_id  # Keep username in sync with unique_id
            try:
                user.full_clean()
                user.save()
            except Exception as e:
                raise ValueError(f"Failed to update user account: {str(e)}")

        # Manage Admin group membership
        admin_group, _ = Group.objects.get_or_create(name='Admin')
        if self.is_admin:
            if not self.user.groups.filter(name='Admin').exists():
                self.user.groups.add(admin_group)
        else:
            if self.user.groups.filter(name='Admin').exists():
                self.user.groups.remove(admin_group)

        super().save(*args, **kwargs)

    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    @property
    def years_of_service(self):
        current_date = timezone.now().date()
        years = current_date.year - self.employment_date.year
        if (current_date.month, current_date.day) < (self.employment_date.month, self.employment_date.day):
            years -= 1
        return max(0, years)

    def __str__(self):
        return f"{self.full_name} ({self.unique_id})"

    class Meta:
        ordering = ['unique_id']
        verbose_name_plural = "Staff"

    @property
    def current_contract(self):
        """Get the most recent active contract"""
        return self.contracts.filter(status='ACTIVE').order_by('-start_date').first()
    
    @property
    def contract_history(self):
        """Get all contracts ordered by start date"""
        return self.contracts.all().order_by('-start_date')
    
    def get_expiring_contracts(self):
        """Get contracts expiring within 30 days"""
        return self.contracts.filter(
            status='ACTIVE',
            end_date__gte=timezone.now().date(),
            end_date__lte=timezone.now().date() + timedelta(days=30)
        )

def contract_upload_path(instance, filename):
    """
    Generate a file upload path using the staff ID.
    """
    # Assuming instance has a staff_id field or is linked to a Staff model
    staff_id = getattr(instance, 'unique_id', None) or instance.staff.unique_id
    return f'contracts/staff_{staff_id}/{filename}'

class Benefits(models.Model):
    name = models.CharField(max_length = 100, verbose_name = ("Benefit Name"))
class Deduction(models.Model):
    DEDUCTION_TYPES = (
        ('MANDATORY', 'Mandatory'),
        ('VOLUNTARY', 'Voluntary'),
        ('LOAN', 'Loan'),
    )
    
    name = models.CharField(max_length=100, verbose_name=_("Deduction Name"))
    percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_("Percentage Cut (%)")
    )
    description = models.TextField(verbose_name=_("Description"))
    deduction_type = models.CharField(
        max_length=20, 
        choices=DEDUCTION_TYPES, 
        default='MANDATORY',
        verbose_name=_("Deduction Type")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    applies_to_contract_types = models.ManyToManyField(
        'Contract', 
        related_name='applicable_deductions',
        blank=True,
        verbose_name=_("Applies to Contract Types")
    )
    min_salary_threshold = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Minimum Salary Threshold"),
        help_text=_("Deduction only applies if salary is above this amount")
    )
    max_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_("Maximum Deduction Amount"),
        help_text=_("Maximum amount to deduct (overrides percentage if set)")
    )
    
    # Auto fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = _('Deduction')
        verbose_name_plural = _('Deductions')
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


class Contract(models.Model):
    CONTRACT_TYPES = (
        ('PERMANENT', 'Permanent'),
        ('LOCUM', 'Locum'),
        ('CASUAL', 'Casual'),
    )
    
    CONTRACT_STATUS = (
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('TERMINATED', 'Terminated'),
        ('RENEWED', 'Renewed'),
        ('PENDING', 'Pending Renewal'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='contracts')
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPES, default='FIXED')
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    salary = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    benefits = models.TextField(blank=True, null=True)
    job_title = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=CONTRACT_STATUS, default='ACTIVE')
    document = models.FileField(upload_to=contract_upload_path, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    
    # Auto fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    renewal_reminder_sent = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = _('Contract')
        verbose_name_plural = _('Contracts')
    
    def __str__(self):
        return f"{self.staff.full_name} - {self.job_title} ({self.start_date})"
    
    @property
    def is_expired(self):
        if self.end_date and timezone.now().date() > self.end_date:
            return True
        return False
    
    @property
    def is_expiring_soon(self):
        if self.end_date:
            warning_period = timedelta(days=30)
            today = timezone.now().date()
            return today <= self.end_date <= today + warning_period
        return False
    
    @property
    def days_until_expiry(self):
        if self.end_date:
            today = timezone.now().date()
            if today > self.end_date:
                return (today - self.end_date).days * -1  # Negative for expired
            return (self.end_date - today).days
        return None
    
    @property
    def duration(self):
        if self.end_date:
            return (self.end_date - self.start_date).days
        return (timezone.now().date() - self.start_date).days

    
    def renew_contract(self, new_end_date, new_salary=None, new_benefits=None, new_job_title=None):
        """Create a new contract based on the current one"""
        new_contract = Contract(
            staff=self.staff,
            contract_type=self.contract_type,
            start_date=timezone.now().date(),
            end_date=new_end_date,
            salary=new_salary or self.salary,
            benefits=new_benefits or self.benefits,
            job_title=new_job_title or self.job_title,
            department=self.department or self.staff.department,
            status='ACTIVE'
        )
        new_contract.save()
        
        # Mark old contract as renewed
        self.status = 'RENEWED'
        self.save()
        
        return new_contract
    
    @property
    def mandatory_deductions(self):
        """Get only mandatory deductions (global)"""
        return Deduction.objects.filter(
            deduction_type='MANDATORY', 
            is_active=True
        )
    
    @property
    def all_deductions(self):
        """Get ALL deductions: mandatory (global) + optional (with overrides)"""
        mandatory = self.mandatory_deductions
        optional_with_overrides = self._get_optional_deductions_with_overrides()
        return list(mandatory) + list(optional_with_overrides)
    
    def _get_optional_deductions_with_overrides(self):
        """Get optional deductions with their overrides"""
        overrides = self.deduction_overrides.filter(is_active=True)
        return [
            {
                'deduction': override.deduction,
                'override': override,
                'amount_calculator': override.calculate_amount
            }
            for override in overrides
        ]

    @property
    def total_deductions_amount(self):
        """Calculate total from ALL sources with overrides"""
        total = Decimal('0.00')
        
        # Mandatory deductions (global)
        for deduction in self.mandatory_deductions:
            if self.salary >= deduction.min_salary_threshold:
                total += deduction.calculate_amount(self.salary)
        
        # Optional deductions (with overrides)
        for item in self._get_optional_deductions_with_overrides():
            override = item['override']
            total += override.calculate_amount(self.salary)
        
        return total
    
    @property
    def net_salary(self):
        """Calculate net salary after ALL deductions"""
        return self.salary - self.total_deductions_amount
    
    @property
    def deductions_breakdown(self):
        """Get detailed breakdown of ALL deductions"""
        breakdown = []
        
        # Mandatory deductions
        for deduction in self.mandatory_deductions:
            if self.salary >= deduction.min_salary_threshold:
                amount = deduction.calculate_amount(self.salary)
                if amount > 0:
                    breakdown.append({
                        'name': deduction.name,
                        'percentage': deduction.percentage,
                        'amount': amount,
                        'description': deduction.description,
                        'type': 'MANDATORY',
                        'is_optional': False
                    })
        
        # Optional deductions
        for deduction in self.optional_deductions.filter(is_active=True):
            if self.salary >= deduction.min_salary_threshold:
                amount = deduction.calculate_amount(self.salary)
                if amount > 0:
                    breakdown.append({
                        'name': deduction.name,
                        'percentage': deduction.percentage,
                        'amount': amount,
                        'description': deduction.description,
                        'type': deduction.deduction_type,
                        'is_optional': True
                    })
        
        return breakdown

    def add_optional_deduction(self, deduction, percentage=None, fixed_amount=None):
        """Helper method to add deduction override"""
        ContractDeduction.objects.update_or_create(
            contract=self,
            deduction=deduction,
            defaults={
                'custom_percentage': percentage,
                'fixed_amount': fixed_amount,
                'is_active': True
            }
        )
    
    def save(self, *args, **kwargs):
        # Update status based on expiration
        if self.end_date and timezone.now().date() > self.end_date:
            self.status = 'EXPIRED'
        elif self.status == 'EXPIRED' and self.end_date and timezone.now().date() <= self.end_date:
            self.status = 'ACTIVE'
        
        # For permanent contracts, set end_date to None
        if self.contract_type == 'PERMANENT':
            self.end_date = None
            
        super().save(*args, **kwargs)

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
        verbose_name=_("Custom Percentage (%)")
    )
    
    fixed_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_("Fixed Amount (KSh)")
    )
    
    is_active = models.BooleanField(default=True)
    
    # Auto fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['contract', 'deduction']  # One override per deduction per contract
        verbose_name = _('Contract Deduction Override')
        verbose_name_plural = _('Contract Deduction Overrides')
    
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
class ContractRenewal(models.Model):
    """Track contract renewal history"""
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='renewals')
    renewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    renewal_date = models.DateTimeField(auto_now_add=True)
    previous_end_date = models.DateField()
    new_end_date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-renewal_date']
        verbose_name = _('Contract Renewal')
        verbose_name_plural = _('Contract Renewals')
    
    def __str__(self):
        return f"Renewal of {self.contract} on {self.renewal_date.date()}"