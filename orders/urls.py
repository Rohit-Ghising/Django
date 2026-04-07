from django.urls import path

from . import views

urlpatterns = [
    path('', views.list_orders, name='order-list'),
    path('payments/<str:transaction_uuid>/confirm/', views.confirm_payment, name='payment-confirm'),
    path('<int:pk>/', views.order_detail, name='order-detail'),
]
