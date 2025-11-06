from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from datetime import timedelta
import uuid

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

class Designation(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name=_("Designation Name"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"

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
    designation = models.ForeignKey(Designation, on_delete=models.CASCADE, verbose_name=_("Position"), related_name="staff_designation")
    employment_date = models.DateField(verbose_name=_("Employment Date"))
    employment_category = models.CharField(max_length=20, choices=EMPLOYMENT_CATEGORY_CHOICES)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Emergency Contact Name"))
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True, verbose_name=_("Emergency Contact Phone"))
    emergency_contact_relationship = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Emergency Contact Relationship"))
    employment_status = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_STATUS_CHOICES,
        verbose_name=_("Employment Status"),
        default='AWAITING CONTRACT'
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

    
    def renew_contract(self, new_end_date, new_salary=None, new_job_title=None):
        """Create a new contract based on the current one"""
        new_contract = Contract(
            staff=self.staff,
            contract_type=self.contract_type,
            start_date=timezone.now().date(),
            end_date=new_end_date,
            salary=new_salary or self.salary,
            job_title=new_job_title or self.job_title,
            department=self.department or self.staff.department,
            status='ACTIVE'
        )
        new_contract.save()
        
        # Mark old contract as renewed
        self.status = 'RENEWED'
        self.save()
        
        return new_contract
    
    
    
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