"""
payments/urls.py
"""

from django.urls import path
from .views import (
    InitiatePaymentView,
    ConfirmPaymentView,
    MyPaymentsView,
    PaymentDetailView,
    AdminPaymentListView,
    AdminRefundView,
)

urlpatterns = [
    # Student
    path('initiate/',                          InitiatePaymentView.as_view(),  name='initiate_payment'),
    path('confirm/',                           ConfirmPaymentView.as_view(),   name='confirm_payment'),
    path('my/',                                MyPaymentsView.as_view(),       name='my_payments'),
    path('<str:transaction_id>/',              PaymentDetailView.as_view(),    name='payment_detail'),

    # Admin
    path('admin/',                             AdminPaymentListView.as_view(),  name='admin_payments'),
    path('admin/<str:transaction_id>/refund/', AdminRefundView.as_view(),       name='admin_refund'),
]
