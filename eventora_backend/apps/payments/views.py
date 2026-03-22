"""
payments/views.py  — with full Razorpay integration
"""

from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from decouple import config
import razorpay
import hmac, hashlib

from .models import Payment
from .serializers import InitiatePaymentSerializer, ConfirmPaymentSerializer, PaymentSerializer
from apps.accounts.permissions import IsStudent, IsAdminUser
from apps.registrations.models import Registration

# Razorpay client (reads from .env)
rz_client = razorpay.Client(
    auth=(config('RAZORPAY_KEY_ID'), config('RAZORPAY_KEY_SECRET'))
)


# ── Student Views ─────────────────────────────────────────────────────────────

class InitiatePaymentView(APIView):
    """
    POST /api/v1/payments/initiate/
    Creates a Razorpay order + a pending Payment record.
    Returns the order_id and key needed by the Razorpay checkout popup.
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

        # Amount in paise (Razorpay expects integers, no decimals)
        amount_paise = int(reg.amount_paid * 100)

        # Create Razorpay order
        rz_order = rz_client.order.create({
            'amount':   amount_paise,
            'currency': 'INR',
            'payment_capture': 1,  # auto-capture
            'notes': {
                'registration_id': str(reg.registration_id),
                'student_email':   request.user.email,
                'event':           reg.event.title,
            }
        })

        # Create (or update) local pending payment record
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

        # Store the Razorpay order_id so we can verify later
        payment.gateway_reference = rz_order['id']
        payment.save(update_fields=['gateway_reference', 'updated_at'])

        return Response({
            'transaction_id':   payment.transaction_id,
            'razorpay_order_id': rz_order['id'],
            'razorpay_key_id':  config('RAZORPAY_KEY_ID'),
            'amount':           amount_paise,
            'currency':         'INR',
            'method':           method,
            'registration_ref': reg.registration_id,
            'event':            reg.event.title,
            'student_name':     request.user.full_name,
            'student_email':    request.user.email,
        }, status=status.HTTP_201_CREATED)


class ConfirmPaymentView(APIView):
    """
    POST /api/v1/payments/confirm/
    Verifies Razorpay signature — if valid, marks payment SUCCESS and confirms registration.
    Body: {
        "transaction_id":         "TXN-...",
        "razorpay_order_id":      "order_...",
        "razorpay_payment_id":    "pay_...",
        "razorpay_signature":     "...",
        "success":                true
    }
    """
    permission_classes = [IsStudent]

    @transaction.atomic
    def post(self, request):
        serializer = ConfirmPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        txn_id  = serializer.validated_data['transaction_id']
        success = serializer.validated_data['success']
        gw_ref  = serializer.validated_data.get('gateway_reference', '')

        payment = get_object_or_404(Payment, transaction_id=txn_id, student=request.user)

        if payment.status == Payment.Status.SUCCESS:
            return Response({'detail': 'Payment already confirmed.'})

        payment.gateway_response = request.data

        if success:
            # Verify Razorpay signature to ensure the payment is genuine
            order_id    = request.data.get('razorpay_order_id', '')
            payment_id  = request.data.get('razorpay_payment_id', '')
            signature   = request.data.get('razorpay_signature', '')

            # Signature = HMAC-SHA256(order_id + "|" + payment_id, key_secret)
            expected = hmac.new(
                config('RAZORPAY_KEY_SECRET').encode(),
                f"{order_id}|{payment_id}".encode(),
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(expected, signature):
                payment.status = Payment.Status.FAILED
                payment.save()
                return Response(
                    {'detail': 'Payment verification failed. Possible fraud attempt.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            payment.gateway_reference = payment_id  # store pay_xxx as final reference
            payment.status = Payment.Status.SUCCESS
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
            return Response({'detail': 'Payment failed. Please try again.'}, status=400)


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
    Issues a real Razorpay refund and cancels the registration.
    """
    permission_classes = [IsAdminUser]

    @transaction.atomic
    def post(self, request, transaction_id):
        payment = get_object_or_404(Payment, transaction_id=transaction_id)

        if payment.status != Payment.Status.SUCCESS:
            return Response({'detail': 'Only successful payments can be refunded.'}, status=400)

        try:
            # Issue refund via Razorpay using the stored payment_id
            rz_client.payment.refund(payment.gateway_reference, {
                'amount': int(payment.amount * 100),  # paise
                'notes':  {'reason': 'Admin initiated refund', 'transaction_id': transaction_id}
            })
        except Exception as e:
            return Response({'detail': f'Razorpay refund failed: {str(e)}'}, status=400)

        payment.status = Payment.Status.REFUNDED
        payment.save(update_fields=['status', 'updated_at'])

        payment.registration.status = Registration.Status.CANCELLED
        payment.registration.save(update_fields=['status', 'updated_at'])

        return Response({'detail': f'Payment {transaction_id} refunded and registration cancelled.'})