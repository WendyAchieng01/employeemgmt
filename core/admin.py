from django.contrib import admin
from .models import Department, Staff


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'staff_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at', 'updated_at']
    
    def staff_count(self, obj):
        return obj.staff_members.count()
    staff_count.short_description = 'Staff Count'

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = [
        'unique_id', 'full_name', 'department', 'position', 
        'employment_date', 'employment_status', 'is_admin'
    ]
    list_filter = [
        'department', 'employment_status', 'gender', 
        'employment_date', 'created_at', 'is_admin'
    ]
    search_fields = [
        'unique_id', 'first_name', 'last_name', 'email', 
        'national_id', 'position'
    ]
    readonly_fields = ['unique_id', 'created_at', 'updated_at', 'years_of_service']
    
    fieldsets = (
        ('Staff ID', {
            'fields': ('unique_id',)
        }),
        ('Personal Information', {
            'fields': (
                ('first_name', 'middle_name', 'last_name'),
                'email', 'phone', 'gender', 'date_of_birth',
                'national_id', 'address'
            )
        }),
        ('Employment Information', {
            'fields': (
                'department', 'position', 'employment_date',
                'employment_status', 'salary', 'is_admin'
            )
        }),
        ('Emergency Contact', {
            'fields': (
                'emergency_contact_name', 'emergency_contact_phone',
                'emergency_contact_relationship'
            )
        }),
        ('System Information', {
            'fields': ('years_of_service', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )