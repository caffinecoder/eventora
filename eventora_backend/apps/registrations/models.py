"""
registrations/models.py
"""

import uuid
from django.db import models
from django.conf import settings


class Registration(models.Model):

    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending Payment'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'
        ATTENDED  = 'attended',  'Attended'

    registration_id = models.CharField(
        max_length=20, unique=True, editable=False,
        help_text='Public-facing ID, e.g. EVT-001-CS2021001'
    )
    student   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='registrations'
    )
    event     = models.ForeignKey(
        'events.Event', on_delete=models.CASCADE,
        related_name='registrations'
    )
    status    = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'registrations'
        unique_together = ('student', 'event')   # one registration per student per event
        ordering = ['-registered_at']

    def __str__(self):
        return f"{self.registration_id} — {self.student.full_name} @ {self.event.title}"

    def save(self, *args, **kwargs):
        if not self.registration_id:
            self.registration_id = self._generate_id()
        super().save(*args, **kwargs)

    def _generate_id(self):
        sid = self.student.student_id or str(self.student.id)
        eid = str(self.event_id).zfill(3)
        return f"EVT-{eid}-{sid}"
