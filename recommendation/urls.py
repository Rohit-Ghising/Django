from django.urls import path

from .views import recommend_api, recommend_for_product

urlpatterns = [
    path("recommend/", recommend_api, name="recommend-by-query"),
    path("recommend/<int:product_id>/", recommend_for_product, name="recommend-by-product"),
]
