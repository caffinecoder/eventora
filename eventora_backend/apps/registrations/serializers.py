"""
registrations/serializers.py
"""

from rest_framework import serializers
from .models import Registration
from apps.events.serializers import EventListSerializer


class RegistrationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Registration
        fields = ['event']

    def validate_event(self, event):
        from apps.events.models import Event
        from django.utils import timezone

        if event.status != Event.Status.OPEN:
            raise serializers.ValidationError('This event is not open for registration.')
        if event.registration_deadline < timezone.now():
            raise serializers.ValidationError('Registration deadline has passed.')
        if event.is_full:
            raise serializers.ValidationError('This event is fully booked.')

        # Prevent duplicate registration
        user = self.context['request'].user
        if Registration.objects.filter(student=user, event=event).exists():
            raise serializers.ValidationError('You are already registered for this event.')
        return event

    def create(self, validated_data):
        user  = self.context['request'].user
        event = validated_data['event']
        reg   = Registration.objects.create(
            student=user,
            event=event,
            amount_paid=event.registration_fee,
            status=Registration.Status.PENDING if event.registration_fee > 0
                   else Registration.Status.CONFIRMED,
        )
        return reg


class RegistrationSerializer(serializers.ModelSerializer):
    event         = EventListSerializer(read_only=True)
    student_name  = serializers.CharField(source='student.full_name', read_only=True)
    student_email = serializers.CharField(source='student.email',     read_only=True)

    class Meta:
        model  = Registration
        fields = [
            'id', 'registration_id', 'student_name', 'student_email',
            'event', 'status', 'amount_paid',
            'registered_at', 'updated_at',
        ]


class AdminRegistrationSerializer(serializers.ModelSerializer):
    """Full serializer for admin views."""
    event         = EventListSerializer(read_only=True)
    student_name  = serializers.CharField(source='student.full_name', read_only=True)
    student_email = serializers.CharField(source='student.email',     read_only=True)
    student_id    = serializers.CharField(source='student.student_id', read_only=True)

    class Meta:
        model  = Registration
        fields = [
            'id', 'registration_id',
            'student_name', 'student_email', 'student_id',
            'event', 'status', 'amount_paid',
            'registered_at', 'updated_at',
        ]
        read_only_fields = ['id', 'registration_id', 'registered_at']
