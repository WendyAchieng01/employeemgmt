from django.contrib import admin
from .models import Department, Staff, Contract, ContractRenewal


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
        'unique_id', 'full_name', 'department', 'position', 'employment_status',
        'employment_date', 'is_admin'
    ]
    list_filter = [
        'department', 'gender', 
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
                'salary', 'is_admin'
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


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ['staff', 'job_title', 'contract_type', 'start_date', 'end_date', 'status', 'is_expiring_soon']
    list_filter = ['status', 'contract_type', 'department', 'start_date']
    search_fields = ['staff__full_name', 'job_title', 'department__name']
    readonly_fields = ['created_at', 'updated_at', 'days_until_expiry', 'is_expired']
    actions = ['send_renewal_reminders', 'mark_as_renewed']
    
    fieldsets = (
        (None, {
            'fields': ('staff', 'contract_type', 'start_date', 'end_date')
        }),
        ('Employment Details', {
            'fields': ('job_title', 'department', 'salary', 'benefits')
        }),
        ('Status', {
            'fields': ('status', 'document', 'notes')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at', 'renewal_reminder_sent'),
            'classes': ('collapse',)
        }),
    )
    
    def is_expiring_soon(self, obj):
        return obj.is_expiring_soon
    is_expiring_soon.boolean = True
    is_expiring_soon.short_description = 'Expiring Soon'
    
    def send_renewal_reminders(self, request, queryset):
        from django.contrib import messages
        from .tasks import send_contract_renewal_reminder
        
        count = 0
        for contract in queryset.filter(status='ACTIVE', end_date__isnull=False):
            if contract.is_expiring_soon and not contract.renewal_reminder_sent:
                send_contract_renewal_reminder(contract.id)
                contract.renewal_reminder_sent = True
                contract.save()
                count += 1
                
        self.message_user(request, f"Renewal reminders sent for {count} contracts")
    send_renewal_reminders.short_description = "Send renewal reminders"
    
    def mark_as_renewed(self, request, queryset):
        updated = queryset.update(status='RENEWED')
        self.message_user(request, f"{updated} contracts marked as renewed")
    mark_as_renewed.short_description = "Mark selected as renewed"


@admin.register(ContractRenewal)
class ContractRenewalAdmin(admin.ModelAdmin):
    list_display = ['contract', 'renewal_date', 'renewed_by']
    list_filter = ['renewal_date']
    readonly_fields = ['renewal_date']
    
    def save_model(self, request, obj, form, change):
        if not obj.renewed_by:
            obj.renewed_by = request.user
        super().save_model(request, obj, form, change)