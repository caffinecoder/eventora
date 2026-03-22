"""
events/models.py
Event and Category models.
"""

from django.db import models
from django.conf import settings
class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    class Meta:
        db_table    = 'categories'
        verbose_name_plural = 'categories'
        ordering    = ['name']

    def __str__(self):
        return self.name
class Event(models.Model):
    class Status(models.TextChoices):
        DRAFT     = 'draft',     'Draft'
        OPEN      = 'open',      'Open'
        CLOSED    = 'closed',    'Closed'
        CANCELLED = 'cancelled', 'Cancelled'
        COMPLETED = 'completed', 'Completed'
    # Core details
    title       = models.CharField(max_length=200)
    slug        = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    category    = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='events')
    emoji       = models.CharField(max_length=10, default='🎉', help_text='Emoji icon for the event card')
    # Scheduling
    event_date  = models.DateField()
    start_time  = models.TimeField()
    end_time    = models.TimeField(blank=True, null=True)
    venue       = models.CharField(max_length=200)
    department  = models.CharField(max_length=100, default='All Departments')
    # Registration
    capacity             = models.PositiveIntegerField(default=100)
    registration_fee     = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    registration_deadline = models.DateTimeField()
    # Status
    status      = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    # Metadata
    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_events'
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'events'
        ordering = ['event_date', 'start_time']
    def __str__(self):
        return self.title

    @property
    def is_free(self):
        return self.registration_fee == 0

    @property
    def spots_remaining(self):
        confirmed = self.registrations.filter(status='confirmed').count()
        return self.capacity - confirmed

    @property
    def is_full(self):
        return self.spots_remaining <= 0
