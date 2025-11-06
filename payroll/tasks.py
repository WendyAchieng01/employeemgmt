from celery import shared_task
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import Payroll, Contract
from decimal import Decimal

@shared_task
def create_monthly_payslips():
    """
    Run on the 1st of every month (or on the 28th for safety).
    Creates a PENDING payslip for every ACTIVE contract.
    """
    today = timezone.localdate()
    target_month = today.replace(day=1)          # first day of current month

    # Find every contract that is active in this month
    active_contracts = Contract.objects.filter(
        start_date__lte=target_month + relativedelta(months=1) - relativedelta(days=1),
        end_date__gte=target_month,
        status='ACTIVE'
    ).select_related('staff')

    created = 0
    for contract in active_contracts:
        staff = contract.staff

        # Skip if already exists
        if Payroll.objects.filter(staff=staff, pay_month=target_month).exists():
            continue

        # You probably have a way to know the monthly gross for this staff
        gross = contract.salary   # ← implement in Contract or elsewhere
        payroll = Payroll.objects.filter(staff=staff, pay_month=target_month)

        payslip = Payroll(
            staff=staff,
            contract=contract,
            pay_month=target_month,
            gross_salary=gross,
            bank_name=payroll.bank_name or "",
            bank_branch=payroll.bank_branch or "",
            bank_branch_code=payroll.bank_branch_code or "",
            account_no=payroll.account_no or "",
            kra_pin=payroll.kra_pin or "",
        )
        payslip.save()               # triggers deduction calc + PDF generation
        payslip.generate_pdf()       # optional – generate PDF now
        payslip.save()
        created += 1

    return f"Created {created} payslips for {target_month:%B %Y}"