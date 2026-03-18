from django.urls import path
from .views import signup, login, protected_route

urlpatterns = [
    path('signup/', signup),
    path('login/', login),
    path('protected/', protected_route),
]