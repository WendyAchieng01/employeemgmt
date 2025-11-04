from django import forms
from .models import ContractDeduction, Deduction, Payroll
from core.models import Contract
from django.forms import inlineformset_factory, ModelForm
import re

class PayrollForm(ModelForm):
    class Meta:
        model = Payroll
        fields = [
            'gross_salary', 'bank_name', 'bank_branch', 'pay_month',
            'bank_branch_code', 'account_no', 'kra_pin'
        ]
        widgets = {
            'pay_month': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control bg-white border-gray-300 focus:border-purple-500 rounded-lg'
            }),
            'gross_salary': forms.NumberInput(attrs={
                'class': 'form-control bg-white border-gray-300 focus:border-purple-500 rounded-lg',
                'step': '0.01',
                'min': '0',
                'placeholder': '50000.00'
            }),
            'bank_name': forms.Select(attrs={
                'class': 'form-control bg-white border-gray-300 focus:border-purple-500 rounded-lg'
            }, choices=[
                ('', 'Select Bank'),
                ('KCB', 'KCB Bank'),
                ('EQUITY', 'Equity Bank'),
                ('COOP', 'Co-operative Bank'),
                ('NCBA', 'NCBA Bank'),
                ('STANBIC', 'Stanbic Bank'),
                ('ABSA', 'Absa Bank'),
            ]),
            'bank_branch': forms.TextInput(attrs={
                'class': 'form-control bg-white border-gray-300 focus:border-purple-500 rounded-lg',
                'placeholder': 'Nairobi Main'
            }),
            'bank_branch_code': forms.TextInput(attrs={
                'class': 'form-control bg-white border-gray-300 focus:border-purple-500 rounded-lg',
                'placeholder': '011'
            }),
            'account_no': forms.TextInput(attrs={
                'class': 'form-control bg-white border-gray-300 focus:border-purple-500 rounded-lg',
                'placeholder': '1234567890'
            }),
            'kra_pin': forms.TextInput(attrs={'placeholder': 'e.g., A123456789Z'}),
        }

    def __init__(self, *args, **kwargs):
        self.staff = kwargs.pop('staff', None)
        self.contract = kwargs.pop('contract', None)
        super().__init__(*args, **kwargs)
        
        # Auto-populate from contract
        if self.contract:
            self.fields['gross_salary'].initial = self.contract.salary
            
        # Customize labels
        self.fields['gross_salary'].label = "Gross Salary (KSh)"
        self.fields['account_no'].label = "Account Number"

    def clean_kra_pin(self):
        """Validate KRA PIN format if provided"""
        kra_pin = self.cleaned_data.get('kra_pin')
        if kra_pin:
            if not re.match(r'^[A-Za-z][0-9]{9}[A-Za-z]$', kra_pin):
                raise forms.ValidationError("KRA PIN must be 11 characters: 1 letter, 9 digits, 1 letter")
        return kra_pin


class ContractDeductionOverrideForm(forms.ModelForm):
    """Form for contract-specific deduction overrides"""
    
    class Meta:
        model = ContractDeduction
        fields = ['deduction', 'custom_percentage', 'fixed_amount', 'is_active']
        widgets = {
            'deduction': forms.Select(attrs={
                'class': 'form-control bg-white border-gray-300 focus:border-purple-500'
            }),
            'custom_percentage': forms.NumberInput(attrs={
                'class': 'form-control bg-white border-gray-300 focus:border-purple-500',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '0.00'
            }),
            'fixed_amount': forms.NumberInput(attrs={
                'class': 'form-control bg-white border-gray-300 focus:border-purple-500',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.contract = kwargs.pop('contract', None)
        super().__init__(*args, **kwargs)
        
        # Only show VOLUNTARY and LOAN deductions
        self.fields['deduction'].queryset = Deduction.objects.filter(
            deduction_type__in=['VOLUNTARY', 'LOAN'],
            is_active=True
        ).order_by('name')
        
        # Add CSS classes
        for field in self.fields.values():
            if isinstance(field.widget, forms.TextInput) or isinstance(field.widget, forms.NumberInput):
                field.widget.attrs['class'] += ' rounded-lg'
    
    def clean(self):
        cleaned_data = super().clean()
        custom_pct = cleaned_data.get('custom_percentage')
        fixed_amt = cleaned_data.get('fixed_amount')
        
        if custom_pct and fixed_amt:
            raise forms.ValidationError(
                "Specify EITHER percentage OR fixed amount, not both."
            )
        
        if not custom_pct and not fixed_amt:
            raise forms.ValidationError(
                "Must specify EITHER percentage OR fixed amount."
            )
        
        return cleaned_data

# Inline formset for multiple overrides
ContractDeductionFormSet = inlineformset_factory(
    Contract,
    ContractDeduction,
    form=ContractDeductionOverrideForm,
    extra=1,  # Show 3 empty rows
    can_delete=True,
    fields=['deduction', 'custom_percentage', 'fixed_amount', 'is_active']
)