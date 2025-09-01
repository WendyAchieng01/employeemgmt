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
from django.views.generic import CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.utils import timezone

def is_admin(user):
    return user.groups.filter(name='Admin').exists()

def lcdash(request):
    # Get query parameters
    search_query = request.GET.get('search', '')
    department_id = request.GET.get('department', '')
    status = request.GET.get('status', '')

    # Base queryset
    staff = Staff.objects.filter(employment_category='LOCUM')
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
        'departments': departments,
        'search_query': search_query,
        'current_dept': department_id,
        'current_status': status,
        'leave': on_leave,
        'present': present,
    }
    return render(request, 'casualdash.html', context)


@login_required
def staff_list(request):
    search_query = request.GET.get('search', '')
    department_id = request.GET.get('department', '')
    status = request.GET.get('status', '')

    staff = Staff.objects.all()

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
        'departments': departments,
        'search_query': search_query,
        'current_dept': department_id,
        'current_status': status,
    }
    return render(request, 'staff_list.html', context)

@login_required
@user_passes_test(is_admin)
def staff_create(request):
    if request.method == 'POST':
        form = StaffForm(request.POST)
        if form.is_valid():
            staff = form.save()
            messages.success(request, f'Staff member {staff.full_name} created successfully with ID: {staff.unique_id}')
            return redirect('core:staff_detail', unique_id=staff.unique_id)
        else:
            messages.error(request, 'Please correct the errors below.')
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
                'position': staff.position,
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
    

class ContractCreateView(CreateView):
    model = Contract
    form_class = ContractForm
    template_name = 'contract_form.html'
    
    def get_staff_object(self):
        """Get staff by unique_id"""
        unique_id = self.kwargs.get('unique_id')
        staff = get_object_or_404(Staff, unique_id=unique_id)
        return staff
    
    def get_initial(self):
        initial = super().get_initial()
        staff = self.get_staff_object()
        initial['staff'] = staff
        initial['department'] = staff.department
        initial['job_title'] = staff.position
        return initial
    
    def form_valid(self, form):
        form.instance.staff = self.get_staff_object()
        response = super().form_valid(form)
        messages.success(self.request, f'Contract created successfully for {form.instance.staff.full_name}')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['staff'] = self.get_staff_object()
        return context
    
    def get_success_url(self):
        return reverse_lazy('core:staff_detail', kwargs={'unique_id': self.object.staff.unique_id})

class ContractRenewView(UpdateView):
    model = Contract
    form_class = ContractForm
    template_name = 'contract_renew.html'
    
    def get_initial(self):
        initial = super().get_initial()
        # Set the start date to today for renewal
        initial['start_date'] = timezone.now().date()
        return initial
    
    def form_valid(self, form):
        # Create a renewal record
        ContractRenewal.objects.create(
            contract=self.object,
            renewed_by=self.request.user,
            previous_end_date=self.object.end_date,
            new_end_date=form.cleaned_data['end_date'],
            notes=f"Renewed by {self.request.user.get_full_name() or self.request.user.username}"
        )
        
        response = super().form_valid(form)
        messages.success(self.request, f'Contract renewed successfully for {form.instance.staff.full_name}')
        return response
    
    def get_success_url(self):
        return reverse_lazy('core:staff_detail', kwargs={'unique_id': self.object.staff.unique_id})

class ContractDetailView(DetailView):
    model = Contract
    template_name = 'core/contract_detail.html'
    context_object_name = 'contract'

class ContractUpdateView(UpdateView):
    model = Contract
    form_class = ContractForm
    template_name = 'core/contract_form.html'
    
    def get_success_url(self):
        return reverse_lazy('core:staff_detail', kwargs={'unique_id': self.object.staff.unique_id})

class ContractDeleteView(DeleteView):
    model = Contract
    template_name = 'core/contract_confirm_delete.html'
    
    def get_success_url(self):
        staff_unique_id = self.object.staff.unique_id
        messages.success(self.request, 'Contract deleted successfully')
        return reverse_lazy('core:staff_detail', kwargs={'unique_id': staff_unique_id})