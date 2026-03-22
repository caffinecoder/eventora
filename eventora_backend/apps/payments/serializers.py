"""
payments/serializers.py  — updated to accept Razorpay fields
"""

from rest_framework import serializers
from .models import Payment
from apps.registrations.models import Registration


class InitiatePaymentSerializer(serializers.Serializer):
    registration_id = serializers.IntegerField()
    method          = serializers.ChoiceField(choices=Payment.Method.choices)

    def validate_registration_id(self, value):
        user = self.context['request'].user
        try:
            reg = Registration.objects.get(pk=value, student=user)
        except Registration.DoesNotExist:
            raise serializers.ValidationError('Registration not found.')
        if reg.status == Registration.Status.CONFIRMED:
            raise serializers.ValidationError('This registration is already paid.')
        if reg.status == Registration.Status.CANCELLED:
            raise serializers.ValidationError('Cannot pay for a cancelled registration.')
        return value


class ConfirmPaymentSerializer(serializers.Serializer):
    transaction_id      = serializers.CharField()
    # Razorpay fields — all three required for signature verification
    razorpay_order_id   = serializers.CharField(required=False, allow_blank=True)
    razorpay_payment_id = serializers.CharField(required=False, allow_blank=True)
    razorpay_signature  = serializers.CharField(required=False, allow_blank=True)
    gateway_reference   = serializers.CharField(required=False, allow_blank=True)
    success             = serializers.BooleanField()


class PaymentSerializer(serializers.ModelSerializer):
    event_title      = serializers.CharField(source='registration.event.title', read_only=True)
    student_name     = serializers.CharField(source='student.full_name', read_only=True)
    registration_ref = serializers.CharField(source='registration.registration_id', read_only=True)

    class Meta:
        model  = Payment
        fields = [
            'id', 'transaction_id', 'registration_ref', 'event_title',
            'student_name', 'amount', 'method', 'status',
            'gateway_reference', 'created_at',
        ]