from rest_framework.decorators import api_view
from rest_framework.response import Response

from products.models import Product
from products.serializers import ProductSerializer

from .recommend import get_recommendations

DEFAULT_RECOMMENDATION_LIMIT = 4
MAX_RECOMMENDATION_LIMIT = 12


def _parse_limit(raw_value) -> int:
    try:
        return max(1, min(int(raw_value), MAX_RECOMMENDATION_LIMIT))
    except (TypeError, ValueError):
        return DEFAULT_RECOMMENDATION_LIMIT


def _serialize_recommendations(product_ids: list[int]):
    if not product_ids:
        return []

    products = Product.objects.filter(id__in=product_ids).prefetch_related(
        "images",
        "specs",
        "tags",
    )
    products_by_id = {product.id: product for product in products}
    ordered_products = [
        products_by_id[product_id]
        for product_id in product_ids
        if product_id in products_by_id
    ]
    return ProductSerializer(ordered_products, many=True).data


@api_view(["GET"])
def recommend_api(request):
    limit = _parse_limit(request.GET.get("limit"))
    raw_product_id = request.GET.get("product_id")
    product_name = request.GET.get("name")

    product_id = None
    if raw_product_id is not None:
        try:
            product_id = int(raw_product_id)
        except (TypeError, ValueError):
            return Response({"error": "product_id must be an integer"}, status=400)

        if not Product.objects.filter(id=product_id).exists():
            return Response({"error": "Product not found"}, status=404)

    if product_id is None and not product_name:
        return Response(
            {"error": "product_id or name is required"},
            status=400,
        )

    recommended_ids = get_recommendations(
        product_id=product_id,
        product_name=product_name,
        n=limit,
    )
    return Response(_serialize_recommendations(recommended_ids))


@api_view(["GET"])
def recommend_for_product(request, product_id: int):
    if not Product.objects.filter(id=product_id).exists():
        return Response({"error": "Product not found"}, status=404)

    limit = _parse_limit(request.GET.get("limit"))
    recommended_ids = get_recommendations(product_id=product_id, n=limit)
    return Response(_serialize_recommendations(recommended_ids))
