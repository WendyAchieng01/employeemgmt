from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Contract

@receiver(post_save, sender=Contract)
def update_staff_employment_status(sender, instance, **kwargs):
    # Check if the contract has a valid staff relationship
    if not hasattr(instance, 'staff') or not instance.staff:
        return  # Exit if staff is None to avoid errors

    # Check if this contract is the staff's current contract
    current_contract = instance.staff.current_contract
    if current_contract and instance.id == current_contract.id:
        if instance.contract_type == 'CASUAL' and instance.status == 'EXPIRED':
            instance.staff.employment_status = 'INACTIVE'
        else:
            instance.staff.employment_status = instance.status
        instance.staff.save()