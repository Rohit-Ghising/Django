import uuid
from pathlib import Path

from rest_framework.decorators import (
    api_view,
    permission_classes,
    parser_classes,
    authentication_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Product, ProductImage, Tag
from .permissions import IsSuperUser
from .serializers import ProductSerializer
from myproject.storage_backends import MediaStorage

DEFAULT_PRODUCT_IMAGE = "https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?w=800&q=80"
storage = MediaStorage()


def _save_file_to_s3(uploaded_file):
    extension = Path(uploaded_file.name).suffix or ".jpg"
    filename = f"products/{uuid.uuid4().hex}{extension}"
    stored_path = storage.save(filename, uploaded_file)
    return storage.url(stored_path)


def _extract_uploaded_files(request):
    files = []
    for key in ("images", "image_files", "image"):
        files.extend(request.FILES.getlist(key))
    return files


def _attach_uploaded_images(product, uploads):
    for upload in uploads:
        ProductImage.objects.create(product=product, image=_save_file_to_s3(upload))


def _attach_tags(product, raw_tags):
    normalized = []
    if isinstance(raw_tags, str):
        normalized = [tag.strip() for tag in raw_tags.split(',') if tag.strip()]
    elif isinstance(raw_tags, list):
        for entry in raw_tags:
            if isinstance(entry, str) and entry.strip():
                normalized.append(entry.strip())
            elif isinstance(entry, dict):
                value = entry.get("value") or entry.get("key")
                if isinstance(value, str) and value.strip():
                    normalized.append(value.strip())
    for tag in normalized:
        Tag.objects.create(product=product, key=tag, value=tag)


def _extract_image_urls(request):
    urls = []
    image_urls = request.data.get('image_urls')
    if isinstance(image_urls, list):
        urls.extend(image_urls)
    elif isinstance(image_urls, str) and image_urls.strip():
        urls.extend([u.strip() for u in image_urls.split(',') if u.strip()])

    single = request.data.get('image_url') or request.data.get('image')
    if isinstance(single, str) and single.strip():
        urls.append(single.strip())
    return [u for u in urls if u]


def _attach_image_urls(product, urls):
    for url in urls:
        ProductImage.objects.create(product=product, image=url)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsSuperUser])
@parser_classes([MultiPartParser, FormParser])
def add_product(request):
    serializer = ProductSerializer(data=request.data)
    if serializer.is_valid():
        product = serializer.save()

        image_urls = _extract_image_urls(request)
        uploaded_files = _extract_uploaded_files(request)

        if not image_urls and not uploaded_files:
            image_urls = [DEFAULT_PRODUCT_IMAGE]

        if image_urls:
            _attach_image_urls(product, image_urls)
        if uploaded_files:
            _attach_uploaded_images(product, uploaded_files)

        tags_input = request.data.get("tags")
        if tags_input is not None:
            _attach_tags(product, tags_input)

        # Re-serialize to include images
        refreshed_serializer = ProductSerializer(product)
        return Response(refreshed_serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def list_products(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)

@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsSuperUser])
@parser_classes([MultiPartParser, FormParser])
def edit_product(request, pk):
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = ProductSerializer(product, data=request.data)
    if serializer.is_valid():
        product = serializer.save()

        image_urls = _extract_image_urls(request)
        uploaded_files = _extract_uploaded_files(request)
        if image_urls or uploaded_files:
            product.images.all().delete()
            if image_urls:
                _attach_image_urls(product, image_urls)
            if uploaded_files:
                _attach_uploaded_images(product, uploaded_files)

        tags_input = request.data.get("tags")
        if tags_input is not None:
            product.tags.all().delete()
            _attach_tags(product, tags_input)

        # Re-serialize
        refreshed_serializer = ProductSerializer(product)
        return Response(refreshed_serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsSuperUser])
def delete_product(request, pk):
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
    product.delete()
    return Response({"message": "Product deleted successfully"})
