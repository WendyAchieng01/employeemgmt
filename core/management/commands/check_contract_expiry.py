# management/commands/check_contract_expiry.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from datetime import timedelta
from core.models import Contract

class Command(BaseCommand):
    help = 'Check for expiring contracts and send notifications'
    
    def handle(self, *args, **options):
        # Contracts expiring in the next 30 days
        warning_date = timezone.now().date() + timedelta(days=30)
        expiring_contracts = Contract.objects.filter(
            end_date__lte=warning_date,
            end_date__gte=timezone.now().date(),
            status='ACTIVE',
            renewal_reminder_sent=False
        )
        
        #for contract in expiring_contracts:
          #  self.send_renewal_reminder(contract)
          #  contract.renewal_reminder_sent = True
           # contract.save()
            
        # Mark expired contracts
        expired_contracts = Contract.objects.filter(
            end_date__lt=timezone.now().date()
        )
        
        for contract in expired_contracts:
            contract.status = 'EXPIRED'
            if contract.contract_type == "CASUAL":
                contract.staff.employment_status = "INACTIVE"
            elif contract.contract_type == "LOCUM":
                contract.staff.employment_status = "EXPIRED"
            else:
                contract.staff.employment_status = "EXPIRED"
            contract.save()
            
        self.stdout.write(
            self.style.SUCCESS(
                f"Checked contracts: {len(expiring_contracts)} expiring soon, "
                f"{len(expired_contracts)} marked as expired"
            )
        )
    
    def send_renewal_reminder(self, contract):
        subject = f"Contract Renewal Reminder: {contract.staff.full_name}"
        
        context = {
            'contract': contract,
            'days_remaining': contract.days_until_expiry,
            'staff': contract.staff,
        }
        
        message = render_to_string('emails/contract_renewal_reminder.txt', context)
        html_message = render_to_string('emails/contract_renewal_reminder.html', context)
        
        # Send to HR/admin (you can modify recipients as needed)
        recipients = ['hr@yourcompany.com', 'admin@yourcompany.com']
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            html_message=html_message,
            fail_silently=False,
        )