from celery import shared_task
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import Payroll, Contract
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect

@shared_task
def create_monthly_payslips():
    from django.utils import timezone
    from dateutil.relativedelta import relativedelta
    from .models import Payroll, Contract
    from decimal import Decimal
    import logging

    logger = logging.getLogger(__name__)
    today = timezone.localdate()
    target_month = today.replace(day=1)
    month_end = target_month + relativedelta(months=1) - relativedelta(days=1)

    logger.info(f"Generating payslips for {target_month:%B %Y}")

    active_contracts = Contract.objects.filter(
        start_date__lte=month_end,
        end_date__gte=target_month,
        status='ACTIVE'
    ).select_related('staff')

    logger.info(f"Found {active_contracts.count()} active contracts")

    created = 0
    for contract in active_contracts:
        staff = contract.staff
        if Payroll.objects.filter(staff=staff, pay_month=target_month).exists():
            continue

        gross = getattr(contract, 'salary', Decimal('0.00'))
        if gross <= 0:
            logger.warning(f"Contract {contract.id} has no salary, skipping")
            continue

        payroll = get_object_or_404(Payroll, staff=staff)

        Payroll.objects.create(
            staff=staff,
            contract=contract,
            pay_month=target_month,
            gross_salary=gross,
            bank_name=payroll.bank_name,
            bank_branch=payroll.bank_branch,
            kra_pin=payroll.kra_pin,
            account_no=payroll.account_no,
            # copy bank details, etc.
        )
        created += 1

    logger.info(f"Created {created} payslips")
    return f"Created {created} payslips for {target_month:%B %Y}"