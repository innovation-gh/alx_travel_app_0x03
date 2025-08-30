from django.urls import path
from listings.views import InitiatePaymentView, VerifyPaymentView

urlpatterns = [
    path('payments/initiate/<int:booking_id>/', InitiatePaymentView.as_view(), name='initiate-payment'),
    path('payments/verify/<str:tx_ref>/', VerifyPaymentView.as_view(), name='verify-payment'),
]