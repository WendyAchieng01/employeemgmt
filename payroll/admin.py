from django.contrib import admin
from .models import Deduction, ContractDeduction, Payroll

# Register your models here.
@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = [
        'staff_name', 'pay_period_start', 'pay_period_end',
        'gross_salary', 'total_deductions', 'net_salary', 'generated_at',
        'staff_national_id', 'staff_unique_id'
    ]
    list_filter = ['pay_period_start', 'pay_period_end']
    search_fields = ['staff__full_name', 'contract__job_title']
    readonly_fields = ['total_deductions', 'net_salary', 'generated_at']



@admin.register(Deduction)
class DeductionAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'percentage', 'deduction_type', 'is_active', 
        'min_salary_threshold', 'max_amount', 'created_at'
    ]
    list_filter = ['deduction_type', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'percentage', 'deduction_type')
        }),
        ('Rules', {
            'fields': ('min_salary_threshold', 'max_amount', 'is_active')
        }),
        ('Description', {
            'fields': ('description',)
        }),
    )
    
    # Show warning for mandatory deductions
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if object_id:
            deduction = Deduction.objects.get(pk=object_id)
            if deduction.deduction_type == 'MANDATORY':
                extra_context['mandatory_warning'] = (
                    "⚠️ MANDATORY deductions apply to ALL staff automatically. "
                    "No contract selection needed."
                )
        return super().changeform_view(request, object_id, form_url, extra_context)

@admin.register(ContractDeduction)
class ContractDeductionAdmin(admin.ModelAdmin):
    list_display = ['contract', 'deduction', 'override_type', 'amount_display', 'is_active']
    list_filter = ['is_active']
    search_fields = ['contract__staff__first_name', 'deduction__name']
    
    def override_type(self, obj):
        if obj.custom_percentage:
            return f"{obj.custom_percentage}%"
        elif obj.fixed_amount:
            return f"KSh {obj.fixed_amount}"
        return "None"
    override_type.short_description = 'Override'
    
    def amount_display(self, obj):
        return f"KSh {obj.calculate_amount(obj.contract.salary):,.2f}"
    amount_display.short_description = 'Calculated Amount'


class ContractDeductionInline(admin.TabularInline):
    model = ContractDeduction
    extra = 0
    fields = ['deduction', 'custom_percentage', 'fixed_amount', 'is_active']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('deduction')