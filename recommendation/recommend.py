from __future__ import annotations

import math
import re
from collections import Counter
from decimal import Decimal
from difflib import get_close_matches

from products.models import Product

DEFAULT_RECOMMENDATION_COUNT = 4
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _stringify(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def _build_text_features(product: Product) -> Counter[str]:
    tag_text = " ".join(
        filter(None, (_stringify(tag.value or tag.key) for tag in product.tags.all()))
    )
    spec_text = " ".join(
        filter(
            None,
            (
                f"{_stringify(spec.key)} {_stringify(spec.value)}".strip()
                for spec in product.specs.all()
            ),
        )
    )
    base_text = " ".join(
        filter(
            None,
            [
                _stringify(product.name),
                _stringify(product.brand),
                _stringify(product.category),
                _stringify(product.shortdescription),
                _stringify(product.description),
                tag_text,
                spec_text,
            ],
        )
    )
    return Counter(_tokenize(base_text))


def _build_numeric_features(product: Product) -> dict[str, float]:
    price = float(product.discount_price or product.price or Decimal("0"))
    return {
        "rating": float(product.rating or 0),
        "review_count": float(product.review_count or 0),
        "stock": float(product.stock or 0),
        "price": price,
        "featured": 1.0 if product.featured else 0.0,
        "trending": 1.0 if product.trending else 0.0,
        "is_new": 1.0 if product.is_new else 0.0,
    }


def _load_products() -> list[Product]:
    return list(
        Product.objects.order_by("id").prefetch_related("images", "specs", "tags")
    )


def _resolve_product_index(
    products: list[Product],
    product_id: int | None = None,
    product_name: str | None = None,
) -> int | None:
    if product_id is not None:
        for index, product in enumerate(products):
            if product.id == product_id:
                return index
        return None

    if not product_name:
        return None

    normalized_name = product_name.casefold().strip()
    names = {product.name.casefold(): index for index, product in enumerate(products)}
    if normalized_name in names:
        return names[normalized_name]

    matches = get_close_matches(normalized_name, list(names.keys()), n=1, cutoff=0.4)
    if not matches:
        return None

    return names[matches[0]]


def _normalize_numeric_features(
    numeric_rows: list[dict[str, float]],
) -> list[dict[str, float]]:
    keys = list(numeric_rows[0].keys())
    minima = {key: min(row[key] for row in numeric_rows) for key in keys}
    maxima = {key: max(row[key] for row in numeric_rows) for key in keys}

    normalized_rows: list[dict[str, float]] = []
    for row in numeric_rows:
        normalized_row: dict[str, float] = {}
        for key in keys:
            low = minima[key]
            high = maxima[key]
            if math.isclose(high, low):
                normalized_row[key] = 0.0
            else:
                normalized_row[key] = (row[key] - low) / (high - low)
        normalized_rows.append(normalized_row)
    return normalized_rows


def _merge_feature_maps(
    text_features: Counter[str],
    numeric_features: dict[str, float],
) -> dict[str, float]:
    merged = {f"text:{token}": float(weight) for token, weight in text_features.items()}
    for key, value in numeric_features.items():
        merged[f"num:{key}"] = float(value)
    return merged


def _cosine_similarity(
    left: dict[str, float],
    right: dict[str, float],
) -> float:
    if not left or not right:
        return 0.0

    shared_keys = set(left.keys()) & set(right.keys())
    numerator = sum(left[key] * right[key] for key in shared_keys)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))

    if math.isclose(left_norm, 0.0) or math.isclose(right_norm, 0.0):
        return 0.0

    return numerator / (left_norm * right_norm)


def _build_feature_vectors(products: list[Product]) -> list[dict[str, float]]:
    text_rows = [_build_text_features(product) for product in products]
    numeric_rows = [_build_numeric_features(product) for product in products]
    normalized_numeric_rows = _normalize_numeric_features(numeric_rows)

    return [
        _merge_feature_maps(text_features, numeric_features)
        for text_features, numeric_features in zip(text_rows, normalized_numeric_rows)
    ]


def get_recommendations(
    product_id: int | None = None,
    product_name: str | None = None,
    n: int = DEFAULT_RECOMMENDATION_COUNT,
) -> list[int]:
    products = _load_products()
    if len(products) < 2:
        return []

    target_index = _resolve_product_index(
        products,
        product_id=product_id,
        product_name=product_name,
    )
    if target_index is None:
        return []

    recommendation_count = max(int(n), 1)
    feature_vectors = _build_feature_vectors(products)
    target_vector = feature_vectors[target_index]

    scored_candidates = []
    for index, product in enumerate(products):
        if index == target_index:
            continue

        similarity = _cosine_similarity(target_vector, feature_vectors[index])
        scored_candidates.append((similarity, product.id))

    scored_candidates.sort(key=lambda item: (-item[0], item[1]))
    return [product_id for _, product_id in scored_candidates[:recommendation_count]]
