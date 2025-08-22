from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.models import Group

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
    EMPLOYMENT_STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('TERMINATED', 'Terminated'),
        ('RETIRED', 'Retired'),
    ]
    EMPLOYMENT_CATEGORY_CHOICES = [
        ('LOCUM', 'Locum'),
        ('CASUAL', 'Casual'),
    ]

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
    position = models.CharField(max_length=100, verbose_name=_("Position"))
    employment_date = models.DateField(verbose_name=_("Employment Date"))
    employment_status = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_STATUS_CHOICES,
        default='ACTIVE',
        verbose_name=_("Employment Status")
    )
    employment_category = models.CharField(max_length=20, choices=EMPLOYMENT_CATEGORY_CHOICES)
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name=_("Salary"))
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Emergency Contact Name"))
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True, verbose_name=_("Emergency Contact Phone"))
    emergency_contact_relationship = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Emergency Contact Relationship"))
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