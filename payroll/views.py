from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import Http404
from .models import Payroll, Staff, ContractDeduction, Deduction
from .forms import PayrollForm, ContractDeductionFormSet


def payroll_create_view(request, unique_id):
    staff = get_object_or_404(Staff, unique_id=unique_id)
    active_contract = staff.contracts.filter(status='ACTIVE').first()

    if not active_contract:
        messages.error(
            request,
            f"No active contract found for {staff.full_name}. "
            f"Please activate a contract before generating payroll."
        )
        return redirect('core:staff_list')

    # Instantiate form and formset
    if request.method == 'POST':
        form = PayrollForm(request.POST, staff=staff, contract=active_contract)
        deduction_formset = ContractDeductionFormSet(request.POST, instance=active_contract)

        if form.is_valid() and deduction_formset.is_valid():
            # Save deductions
            deduction_formset.save()

            # Save payroll
            payroll = form.save(commit=False)
            payroll.staff = staff
            payroll.contract = active_contract
            payroll.save()

            messages.success(
                request,
                f'Payroll generated successfully for {staff.full_name}! '
                f'Net Salary: KSh {payroll.net_salary:,.2f}'
            )
            return redirect('payroll:payroll_detail', unique_id=staff.unique_id)
    else:
        form = PayrollForm(staff=staff, contract=active_contract)
        deduction_formset = ContractDeductionFormSet(instance=active_contract)

    context = {
        'staff': staff,
        'contract': active_contract,
        'form': form,
        'deduction_formset': deduction_formset,
    }
    return render(request, 'payroll_form.html', context)



def payroll_update_view(request, unique_id):
    staff = get_object_or_404(Staff, unique_id=unique_id)
    payroll = Payroll.objects.filter(staff=staff).order_by('-pay_period_end').first()

    if not payroll:
        raise Http404("No payroll record found for this staff member.")

    active_contract = payroll.contract

    if request.method == 'POST':
        form = PayrollForm(request.POST, instance=payroll, staff=staff, contract=active_contract)
        deduction_formset = ContractDeductionFormSet(request.POST, instance=active_contract)

        if form.is_valid() and deduction_formset.is_valid():
            deduction_formset.save()
            form.save()

            messages.success(
                request,
                f'Payroll updated successfully for {staff.full_name}!'
            )
            return redirect('payroll:payroll_detail', unique_id=staff.unique_id)
    else:
        form = PayrollForm(instance=payroll, staff=staff, contract=active_contract)
        deduction_formset = ContractDeductionFormSet(instance=active_contract)

    context = {
        'staff': staff,
        'contract': active_contract,
        'form': form,
        'deduction_formset': deduction_formset,
    }
    return render(request, 'payroll_form.html', context)


def payroll_detail_view(request, unique_id):
    staff = get_object_or_404(Staff, unique_id=unique_id)
    payroll = get_object_or_404(Payroll, staff=staff)

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

    context = {
        'payroll': payroll,
        'mandatory_deductions': mandatory,
        'contract_deductions': optional,
        'staff': payroll.staff,
    }
    return render(request, 'payroll_detail.html', context)

