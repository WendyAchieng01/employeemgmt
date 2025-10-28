# payroll/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Payroll

@receiver(post_save, sender=Payroll)
def generate_payroll_pdf(sender, instance, created, **kwargs):
    if not instance.pdf_file:
        instance.generate_pdf()
        instance.save(update_fields=['pdf_file'])