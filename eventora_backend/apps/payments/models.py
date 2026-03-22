"""
payments/models.py
"""

import uuid
from django.db import models
from django.conf import settings


class Payment(models.Model):

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUCCESS = 'success', 'Success'
        FAILED  = 'failed',  'Failed'
        REFUNDED = 'refunded', 'Refunded'

    class Method(models.TextChoices):
        CARD        = 'card',        'Card'
        UPI         = 'upi',         'UPI'
        NET_BANKING = 'net_banking',  'Net Banking'

    # Links
    registration = models.OneToOneField(
        'registrations.Registration', on_delete=models.CASCADE, related_name='payment'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments'
    )

    # Payment details
    transaction_id = models.CharField(max_length=100, unique=True, editable=False)
    amount         = models.DecimalField(max_digits=8, decimal_places=2)
    method         = models.CharField(max_length=15, choices=Method.choices)
    status         = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    # Gateway response (store raw for debugging)
    gateway_reference = models.CharField(max_length=200, blank=True, null=True)
    gateway_response  = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_id} — ₹{self.amount} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)
