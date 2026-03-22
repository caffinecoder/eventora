"""
payments/views.py — Mock payment (no real gateway)
Swap this out for the Razorpay version when ready to go live.
"""

from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Payment
from .serializers import InitiatePaymentSerializer, ConfirmPaymentSerializer, PaymentSerializer
from apps.accounts.permissions import IsStudent, IsAdminUser
from apps.registrations.models import Registration


# ── Student Views ─────────────────────────────────────────────────────────────

class InitiatePaymentView(APIView):
    """
    POST /api/v1/payments/initiate/
    Creates a pending Payment and immediately confirms it (mock).
    Body: { "registration_id": 5, "method": "upi" }
    """
    permission_classes = [IsStudent]

    @transaction.atomic
    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        reg_id = serializer.validated_data['registration_id']
        method = serializer.validated_data['method']
        reg    = Registration.objects.select_for_update().get(pk=reg_id)

        # Create or retrieve existing payment
        payment, created = Payment.objects.get_or_create(
            registration=reg,
            defaults={
                'student': request.user,
                'amount':  reg.amount_paid,
                'method':  method,
                'status':  Payment.Status.PENDING,
            }
        )
        if not created:
            payment.method = method
            payment.save(update_fields=['method', 'updated_at'])

        return Response({
            'transaction_id':   payment.transaction_id,
            'amount':           str(payment.amount),
            'method':           payment.method,
            'registration_ref': reg.registration_id,
            'event':            reg.event.title,
            # mock flag so frontend knows to skip real gateway
            'mock':             True,
        }, status=status.HTTP_201_CREATED)


class ConfirmPaymentView(APIView):
    """
    POST /api/v1/payments/confirm/
    Mock confirmation — always succeeds, marks registration as confirmed.
    Body: { "transaction_id": "TXN-...", "success": true }
    """
    permission_classes = [IsStudent]

    @transaction.atomic
    def post(self, request):
        serializer = ConfirmPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        txn_id  = serializer.validated_data['transaction_id']
        success = serializer.validated_data['success']

        payment = get_object_or_404(Payment, transaction_id=txn_id, student=request.user)

        if payment.status == Payment.Status.SUCCESS:
            return Response({'detail': 'Payment already confirmed.'})

        if success:
            payment.status            = Payment.Status.SUCCESS
            payment.gateway_reference = 'MOCK-' + payment.transaction_id
            payment.save()

            payment.registration.status = Registration.Status.CONFIRMED
            payment.registration.save(update_fields=['status', 'updated_at'])

            return Response({
                'detail':           'Payment successful. Registration confirmed.',
                'transaction_id':   payment.transaction_id,
                'registration_ref': payment.registration.registration_id,
            })
        else:
            payment.status = Payment.Status.FAILED
            payment.save()
            return Response({'detail': 'Payment failed.'}, status=400)


class MyPaymentsView(generics.ListAPIView):
    permission_classes = [IsStudent]
    serializer_class   = PaymentSerializer

    def get_queryset(self):
        return Payment.objects.filter(student=self.request.user).select_related('registration__event')


class PaymentDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class   = PaymentSerializer
    lookup_field       = 'transaction_id'

    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user:
            return Payment.objects.select_related('registration__event', 'student')
        return Payment.objects.filter(student=user).select_related('registration__event')


# ── Admin Views ───────────────────────────────────────────────────────────────

class AdminPaymentListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class   = PaymentSerializer
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['transaction_id', 'student__full_name', 'student__email']
    ordering_fields    = ['created_at', 'amount', 'status']
    ordering           = ['-created_at']

    def get_queryset(self):
        qs  = Payment.objects.select_related('registration__event', 'student')
        sts = self.request.query_params.get('status')
        if sts:
            qs = qs.filter(status=sts)
        return qs


class AdminRefundView(APIView):
    """
    POST /api/v1/payments/admin/<transaction_id>/refund/
    Mock refund — just marks payment as refunded and cancels registration.
    """
    permission_classes = [IsAdminUser]

    @transaction.atomic
    def post(self, request, transaction_id):
        payment = get_object_or_404(Payment, transaction_id=transaction_id)

        if payment.status != Payment.Status.SUCCESS:
            return Response({'detail': 'Only successful payments can be refunded.'}, status=400)

        payment.status = Payment.Status.REFUNDED
        payment.save(update_fields=['status', 'updated_at'])

        payment.registration.status = Registration.Status.CANCELLED
        payment.registration.save(update_fields=['status', 'updated_at'])

        return Response({'detail': f'Payment {transaction_id} refunded and registration cancelled.'})