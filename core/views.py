from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from .models import Staff, Department
from .forms import StaffForm
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect



def staff_list(request):
    """Display all staff members with filtering and search"""
    staff_list = Staff.objects.select_related('department').all()
    departments = Department.objects.annotate(staff_count=Count('staff_members'))
    
    # Filter by department
    dept_filter = request.GET.get('department')
    if dept_filter:
        staff_list = staff_list.filter(department__id=dept_filter)
    
    # Filter by employment status
    status_filter = request.GET.get('status')
    if status_filter:
        staff_list = staff_list.filter(employment_status=status_filter)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        staff_list = staff_list.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(unique_id__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(position__icontains=search_query)
        )
    
    context = {
        'staff_list': staff_list,
        'departments': departments,
        'current_dept': dept_filter,
        'current_status': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'staff_list.html', context)

def staff_create(request):
    """Create a new staff member"""
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
    staff = Staff.objects.get(unique_id=unique_id)
    return render(request, 'staff_detail.html', {'staff': staff})

def staff_update(request, unique_id):
    """Update an existing staff member"""
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

def department_staff(request, dept_id):
    """List all staff members in a specific department"""
    department = get_object_or_404(Department, id=dept_id)
    staff_list = Staff.objects.filter(department=department)
    
    return render(request, 'department_staff.html', {
        'department': department,
        'staff_list': staff_list
    })

def staff_api(request):
    """API endpoint for staff data (for AJAX requests)"""
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

@require_POST
@csrf_protect
@login_required
def delete_staff(request, staff_id):
    staff = get_object_or_404(Staff, unique_id=staff_id)
    try:
        staff.delete()
        return HttpResponse(status=200)
    except Exception as e:
        return HttpResponse(status=500)