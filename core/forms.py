from django import forms
from django.utils import timezone
from .models import Staff, Department, Contract

class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        exclude = ['unique_id', 'created_at', 'updated_at']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'employment_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'gender': forms.Select(),
            'employment_status': forms.Select(attrs={'required': 'false'}),
            'kra_pin': forms.TextInput(attrs={'placeholder': ''}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.all()
        # Set initial employment_date to current date
        self.fields['employment_date'].initial = timezone.now().date()
        
        # Make certain fields required
        required_fields = [
            'first_name', 'last_name', 'email', 'phone', 'gender',
            'date_of_birth', 'national_id', 'department', 'position',
            'employment_date', 'employment_category'
        ]
        
        for field in required_fields:
            self.fields[field].required = True

    def clean_national_id(self):
        """Validate national ID format and uniqueness"""
        national_id = self.cleaned_data.get('national_id')
        if national_id:
            # Remove any non-alphanumeric characters for validation
            clean_id = ''.join(c for c in national_id if c.isalnum())
            if len(clean_id) < 6:  # Minimum length check
                raise forms.ValidationError("National ID must be at least 6 characters long")
        return national_id

    def clean_kra_pin(self):
        """Validate KRA PIN format if provided"""
        kra_pin = self.cleaned_data.get('kra_pin')
        if kra_pin:
            import re
            if not re.match(r'^[A-Za-z][0-9]{9}[A-Za-z]$', kra_pin):
                raise forms.ValidationError("KRA PIN must be 11 characters: 1 letter, 9 digits, 1 letter")
        return kra_pin

    def clean(self):
        """Custom validation to check for potential duplicate staff IDs"""
        cleaned_data = super().clean()
        national_id = cleaned_data.get('national_id')
        department = cleaned_data.get('department')
        employment_date = cleaned_data.get('employment_date')
        
        if national_id and department and employment_date:
            # Generate the potential staff ID with hyphen (per model)
            clean_national_id = ''.join(c for c in national_id if c.isalnum())
            potential_unique_id = f"{department.code}{clean_national_id}-{employment_date.year}"
            
            # Check if this staff ID already exists (exclude current instance if updating)
            existing_staff = Staff.objects.filter(unique_id=potential_unique_id)
            if self.instance and self.instance.pk:
                existing_staff = existing_staff.exclude(pk=self.instance.pk)
            
            if existing_staff.exists():
                raise forms.ValidationError(
                    f"A staff member with this National ID already exists in {department.name} "
                    f"for the year {employment_date.year}. Staff ID would be: {potential_unique_id}"
                )
        
        return cleaned_data
    
class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = [
            'contract_type', 'start_date', 'end_date', 'salary', 
            'benefits', 'job_title', 'department', 'document', 'notes'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'benefits': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        contract_type = cleaned_data.get('contract_type')
        
        if contract_type != 'PERMANENT' and not end_date:
            raise forms.ValidationError("End date is required for non-permanent contracts.")
        
        if end_date and start_date and end_date <= start_date:
            raise forms.ValidationError("End date must be after start date.")
        
        return cleaned_data