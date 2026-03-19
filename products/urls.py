from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.add_product),
    path('list/', views.list_products),
    path('edit/<int:pk>/', views.edit_product),
    path('delete/<int:pk>/', views.delete_product),
]