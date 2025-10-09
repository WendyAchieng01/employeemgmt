from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from .models import Staff, Department, Contract, ContractRenewal
from .forms import StaffForm, ContractForm
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
import logging
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_http_methods

def is_admin(user):
    return user.groups.filter(name='Admin').exists()

def lcdash(request):
    # Get query parameters
    search_query = request.GET.get('search', '')
    department_id = request.GET.get('department', '')
    status = request.GET.get('status', '')

    # Base queryset
    staff = Staff.objects.filter(employment_category='LOCUM')
    total = staff
    present = staff.filter(employment_status='ACTIVE')
    on_leave = staff.filter(employment_status='INACTIVE')

    # Apply search filter (Name, ID, Email, KRA PIN)
    if search_query:
        staff = staff.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(middle_name__icontains=search_query) |
            Q(unique_id__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(kra_pin__icontains=search_query)
        )

    # Apply department filter
    if department_id:
        staff = staff.filter(department__id=department_id)

    # Apply status filter
    if status:
        staff = staff.filter(employment_status=status)

    # Get departments with staff count for filter dropdown
    departments = Department.objects.annotate(staff_count=Count('staff_members'))

    context = {
        'staff_list': staff,
        'total': total,
        'departments': departments,
        'search_query': search_query,
        'current_dept': department_id,
        'current_status': status,
        'leave': on_leave,
        'present': present,
    }
    return render(request, 'dashboard.html', context)

def cdash(request):
    # Get query parameters
    search_query = request.GET.get('search', '')
    department_id = request.GET.get('department', '')
    status = request.GET.get('status', '')

    # Base queryset
    staff = Staff.objects.filter(employment_category='CASUAL')
    total = staff
    present = staff.filter(employment_status='ACTIVE')
    on_leave = staff.filter(employment_status='INACTIVE')

    # Apply search filter (Name, ID, Email, KRA PIN)
    if search_query:
        staff = staff.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(middle_name__icontains=search_query) |
            Q(unique_id__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(kra_pin__icontains=search_query)
        )

    # Apply department filter
    if department_id:
        staff = staff.filter(department__id=department_id)

    # Apply status filter
    if status:
        staff = staff.filter(employment_status=status)

    # Get departments with staff count for filter dropdown
    departments = Department.objects.annotate(staff_count=Count('staff_members'))

    context = {
        'staff_list': staff,
        'total': total,
        'departments': departments,
        'search_query': search_query,
        'current_dept': department_id,
        'current_status': status,
        'leave': on_leave,
        'present': present,
    }
    return render(request, 'casualdash.html', context)

def contracts(request):
    # Get filter parameters
    search_query = request.GET.get('search', '')
    department_id = request.GET.get('department', '')
    status = request.GET.get('status', '')

    # Start with all contracts
    contracts = Contract.objects.all()

    # Apply search filter
    if search_query:
        contracts = contracts.filter(
            Q(staff__first_name__icontains=search_query) |
            Q(staff__middle_name__icontains=search_query) |
            Q(staff__last_name__icontains=search_query) |
            Q(staff__unique_id__icontains=search_query) |
            Q(staff__email__icontains=search_query) |
            Q(staff__kra_pin__icontains=search_query)
        )

    # Apply department filter
    if department_id:
        contracts = contracts.filter(department__id=department_id)

    # Apply status filter
    if status:
        contracts = contracts.filter(status=status)

    # Dashboard card querysets (unfiltered)
    active = Contract.objects.filter(status='ACTIVE')
    inactive = Contract.objects.filter(status__in=['INACTIVE', 'EXPIRED'])
    pending_renewal = Contract.objects.filter(status='PENDING')

    # Get all departments for dropdown
    departments = Department.objects.all()

    context = {
        'contracts': contracts,
        'departments': departments,
        'search_query': search_query,
        'current_dept': department_id,
        'current_status': status,
        'active': active,
        'inactive': inactive,
        'pending_renewal': pending_renewal,
    }
    return render(request, 'contracts.html', context)

@login_required
def staff_list(request):
    search_query = request.GET.get('search', '')
    department_id = request.GET.get('department', '')
    status = request.GET.get('status', '')

    staff = Staff.objects.all()
    active = staff.filter(employment_status='ACTIVE')
    inactive = staff.filter(employment_status='INACTIVE')

    if search_query:
        staff = staff.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(middle_name__icontains=search_query) |
            Q(unique_id__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(kra_pin__icontains=search_query)
        )

    if department_id:
        staff = staff.filter(department__id=department_id)

    if status:
        staff = staff.filter(employment_status=status)

    departments = Department.objects.annotate(staff_count=Count('staff_members'))

    context = {
        'staff_list': staff,
        'active': active,
        'inactive': inactive,
        'departments': departments,
        'search_query': search_query,
        'current_dept': department_id,
        'current_status': status,
    }
    return render(request, 'locumdash.html', context)

def staff_create(request):
    if request.method == 'POST':
        form = StaffForm(request.POST)
        if form.is_valid():
            staff = form.save()
            messages.success(request, f'Staff member {staff.full_name} created successfully with ID: {staff.unique_id}')
            return redirect('core:staff_detail', unique_id=staff.unique_id)
        else:
            messages.error(request, 'Please correct the errors below.')
            print(form.errors)
    else:
        form = StaffForm()
    
    return render(request, 'staff_form.html', {
        'form': form,
        'title': 'Add New Staff Member'
    })


def staff_detail(request, unique_id):
    staff = get_object_or_404(Staff, unique_id=unique_id)
    return render(request, 'staffdash.html', {'staff': staff})

@login_required
@user_passes_test(is_admin)
def staff_update(request, unique_id):
    staff = get_object_or_404(Staff, unique_id=unique_id)
    
    if request.method == 'POST':
        form = StaffForm(request.POST, instance=staff)
        if form.is_valid():
            form.save()
            messages.success(request, f'Staff member {staff.full_name} updated successfully')
            return redirect('core:staff_detail', unique_id=staff.unique_id)
    else:
        form = StaffForm(instance=staff)
    
    return render(request, 'staff_form.html', {
        'form': form,
        'staff': staff,
        'title': f'Update {staff.full_name}'
    })

@login_required
def department_staff(request, dept_id):
    department = get_object_or_404(Department, id=dept_id)
    staff_list = Staff.objects.filter(department=department)
    
    return render(request, 'department_staff.html', {
        'department': department,
        'staff_list': staff_list
    })

@login_required
def staff_api(request):
    if request.method == 'GET':
        staff_data = []
        for staff in Staff.objects.select_related('department'):
            staff_data.append({
                'id': staff.unique_id,
                'name': staff.full_name,
                'department': staff.department.name,
                'designation': staff.designation,
                'status': staff.employment_status,
                'employment_date': staff.employment_date.strftime('%Y-%m-%d')
            })
        return JsonResponse({'staff': staff_data})

@login_required
@user_passes_test(is_admin)
@require_POST
@csrf_protect
def delete_staff(request, staff_id):
    staff = get_object_or_404(Staff, unique_id=staff_id)
    try:
        user = staff.user
        staff.delete()
        if user:
            user.delete()
        return HttpResponse(status=200)
    except Exception as e:
        return HttpResponse(status=500)
    
logger = logging.getLogger(__name__)

def contract_create(request, unique_id):
    staff = get_object_or_404(Staff, unique_id=unique_id)
    
    if request.method == 'POST':
        form = ContractForm(request.POST)
        if form.is_valid():
            contract = form.save(commit=False)
            contract.staff = staff
            contract.save()
            messages.success(request, f'Contract created successfully for {contract.staff.full_name}')
            return redirect('core:staff_detail', unique_id=staff.unique_id)
    else:
        initial = {
            'staff': staff,
            'department': staff.department,
            'job_title': staff.designation
        }
        form = ContractForm(initial=initial)
    
    context = {'form': form, 'staff': staff}
    return render(request, 'contract_form.html', context)

@login_required
def contract_renew(request, unique_id):
    contract = get_object_or_404(Contract, id=unique_id, status='ACTIVE')
    
    if request.method == 'POST':
        form = ContractForm(request.POST)
        if form.is_valid():
            try:
                new_contract = contract.renew_contract(
                    new_end_date=form.cleaned_data['end_date'],
                    new_salary=form.cleaned_data.get('salary', contract.salary),
                    new_benefits=form.cleaned_data.get('benefits', contract.benefits),
                    new_job_title=form.cleaned_data.get('job_title', contract.job_title)
                )
                
                ContractRenewal.objects.create(
                    contract=contract,
                    renewed_by=request.user,
                    previous_end_date=contract.end_date,
                    new_end_date=new_contract.end_date,
                    notes=form.cleaned_data.get('notes', f"Renewed by {request.user.get_full_name() or request.user.username}")
                )
                
                messages.success(request, f'Contract renewed successfully for {contract.staff.full_name}')
                return redirect('core:staff_detail', unique_id=contract.staff.unique_id)
            except Exception as e:
                logger.error(f"Error renewing contract: {str(e)}", exc_info=True)
                messages.error(request, f'Failed to renew contract: {str(e)}')
                return render(request, 'contract_renew.html', {'form': form})
    else:
        initial = {
            'start_date': timezone.now().date(),
            'contract_type': contract.contract_type,
            'job_title': contract.job_title,
            'department': contract.department,
            'salary': contract.salary,
            'benefits': contract.benefits,
        }
        form = ContractForm(initial=initial)
    
    context = {'form': form, 'contract': contract}
    return render(request, 'contract_renew.html', context)

def contract_detail(request, unique_id):
    contract = get_object_or_404(Contract, id=unique_id)
    context = {'contract': contract}
    return render(request, 'contract_detail.html', context)

def contract_update(request, unique_id):
    contract = get_object_or_404(Contract, id=unique_id)
    staff = contract.staff  # Get the associated staff object
    
    if request.method == 'POST':
        form = ContractForm(request.POST, instance=contract)
        if form.is_valid():
            form.save()
            messages.success(request, f'Contract updated successfully for {contract.staff.full_name}')
            if staff and hasattr(staff, 'unique_id') and staff.unique_id:
                return redirect('core:staff_detail', unique_id=staff.unique_id)
            else:
                messages.warning(request, 'Staff details not found. Redirecting to contract list.')
                return redirect('core:contracts')
    else:
        form = ContractForm(instance=contract)
    
    context = {'form': form, 'contract': contract, 'staff': staff}
    return render(request, 'contract_form.html', context)

@require_http_methods(["POST"])
def contract_delete(request, unique_id):
    contract = get_object_or_404(Contract, id=unique_id)
    staff_unique_id = contract.staff.unique_id
    contract_info = f"{contract.staff.full_name} - {contract.job_title}"
    
    try:
        contract.delete()
        
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Contract for {contract_info} deleted successfully',
                'redirect_url': f'/staff/{staff_unique_id}/'  # Adjust this based on your URL structure
            })
        else:
            messages.success(request, f'Contract for {contract_info} deleted successfully')
            return redirect('core:staff_detail', unique_id=staff_unique_id)
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Error deleting contract: {str(e)}'
            }, status=400)
        else:
            messages.error(request, f'Error deleting contract: {str(e)}')
            return redirect('core:contract_detail', unique_id=unique_id)
def billing(request):
    return render(request, "billing.html")

def about(request):
    return render(request, "tables.html")