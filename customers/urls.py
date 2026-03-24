from django.urls import path
from .views import signup, login, protected_route, profile, list_users

urlpatterns = [
    path('signup/', signup),
    path('login/', login),
    path('protected/', protected_route),
    path('me/', profile),
    path('users/', list_users),
]
