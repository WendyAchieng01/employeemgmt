from django.shortcuts import render, get_object_or_404
from django.views.generic import CreateView
from core.models import Contract, Staff
from .models import ContractDeduction, Payroll, Deduction
from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404
from .models import Payroll, ContractDeduction
from .forms import PayrollForm, ContractDeductionFormSet
    

class PayrollCreateView(CreateView):
    model = Payroll
    form_class = PayrollForm
    template_name = 'payroll_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get staff and contract
        unique_id = self.kwargs.get('unique_id')
        staff = get_object_or_404(Staff, unique_id=unique_id)
        active_contract = staff.contracts.filter(status='ACTIVE').first()

        # Add formset
        if self.request.POST:
            context['deduction_formset'] = ContractDeductionFormSet(
                self.request.POST, instance=active_contract
            )
        else:
            context['deduction_formset'] = ContractDeductionFormSet(instance=active_contract)
        
        context.update({
            'staff': staff,
            'contract': active_contract,
            'form': self.get_form()
        })
        
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        
        unique_id = self.kwargs.get('unique_id')
        staff = get_object_or_404(Staff, unique_id=unique_id)
        active_contract = staff.contracts.filter(status='ACTIVE').first()
        
        
        kwargs.update({
            'staff': staff,
            'contract': active_contract
        })
        
        return kwargs
    
    def form_valid(self, form):
        # Set staff and contract
        unique_id = self.kwargs.get('unique_id')
        staff = get_object_or_404(Staff, unique_id=unique_id)
        active_contract = staff.contracts.filter(status='ACTIVE').first()

        # Save formset first (deductions linked to contract)
        formset = self.get_context_data()['deduction_formset']
        if formset.is_valid():
            formset.instance = active_contract
            formset.save()
        
        form.instance.staff = staff
        form.instance.contract = active_contract
        
        # Save payroll
        self.object = form.save()
        response = super().form_valid(form)
        
        # Generate payslip message
        messages.success(
            self.request,
            f'Payroll generated successfully for {staff.full_name}! '
            f'Net Salary: KSh {form.instance.net_salary:,.2f}'
        )
        
        return response
    
    def get_success_url(self):
        unique_id = self.kwargs.get('unique_id')
        return reverse_lazy('payroll:payroll_detail', kwargs={'unique_id': self.object.staff.unique_id})


# -----------------------------------------------------------------
# Update view – almost identical, just inherit from UpdateView
# -----------------------------------------------------------------
class PayrollUpdateView(PayrollCreateView, UpdateView):
    """Reuse the same logic for editing."""
    def get_object(self, queryset=None):
        # pk is the Payroll primary key
        return super().get_object(queryset)
    

class PayrollDetailView(DetailView):
    model = Payroll
    template_name = 'payroll_detail.html'
    context_object_name = 'payroll'

    def get_object(self, queryset=None):
        """
        Find the Payroll by staff.unique_id + pay_period_start.
        You can change the lookup logic (latest, specific period, etc.)
        """
        unique_id = self.kwargs.get('unique_id')
        staff = get_object_or_404(Staff, unique_id=unique_id)

        # If you want the *most recent* payroll:
        payroll = Payroll.objects.filter(staff=staff).order_by('-pay_period_end').first()
        # if not payroll: raise Http404

        return payroll

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payroll = self.object
        salary = payroll.gross_salary

        # Mandatory deductions
        mandatory = []
        for d in Deduction.objects.filter(deduction_type='MANDATORY', is_active=True):
            amt = d.calculate_amount(salary)
            if amt > 0:
                mandatory.append({'name': d.name, 'amount': amt})

        # Optional (contract) deductions
        optional = []
        for cd in ContractDeduction.objects.filter(contract=payroll.contract, is_active=True):
            amt = cd.calculate_amount(salary)
            if amt > 0:
                optional.append({
                    'deduction': cd.deduction,
                    'custom_percentage': cd.custom_percentage,
                    'fixed_amount': cd.fixed_amount,
                    'amount': amt
                })

        context.update({
            'mandatory_deductions': mandatory,
            'contract_deductions': optional,
            'staff': payroll.staff,
        })
        return context
