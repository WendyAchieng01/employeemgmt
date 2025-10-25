from django.core.management.base import BaseCommand
from payroll.models import Payroll
import uuid

class Command(BaseCommand):
    help = 'Fix invalid UUIDs in Payroll.id field'

    def handle(self, *args, **options):
        fixed = 0
        for payroll in Payroll.objects.all():
            try:
                # Try to parse as UUID
                uuid.UUID(str(payroll.id))
            except (ValueError, TypeError, AttributeError):
                # Invalid → generate new UUID
                payroll.id = uuid.uuid4()
                payroll.save(update_fields=['id'])
                fixed += 1
                self.stdout.write(f"Fixed: {payroll.staff.full_name} → {payroll.id}")

        self.stdout.write(
            self.style.SUCCESS(f"Fixed {fixed} invalid UUIDs")
        )