from django.urls import path

from . import views

urlpatterns = [
    path('', views.list_orders, name='order-list'),
    path('<int:pk>/', views.order_detail, name='order-detail'),
]
