from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Contract

ACTIVE_STATUSES = {'ACTIVE', 'ONGOING'}  # adjust to your enum/choices

def sync_staff_employment_status(staff):
    if not staff:
        return
    # If any active contract exists -> ACTIVE
    if staff.contract_set.filter(status__in=ACTIVE_STATUSES).exists():
        staff.employment_status = 'ACTIVE'
    else:
        # none active: if the last/only contract is casual and expired -> INACTIVE
        casual_expired = staff.contract_set.filter(
            contract_type='CASUAL', status='EXPIRED'
        ).exists()
        staff.employment_status = 'INACTIVE' if casual_expired else 'INACTIVE'  # adjust if you have other states
    staff.save(update_fields=['employment_status'])


@receiver(post_save, sender=Contract)
def on_contract_saved(sender, instance, **kwargs):
    sync_staff_employment_status(instance.staff)

@receiver(post_delete, sender=Contract)
def on_contract_deleted(sender, instance, **kwargs):
    # If you ever delete/replace contracts, keep staff correct too
    sync_staff_employment_status(instance.staff)
