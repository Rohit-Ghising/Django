from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from .models import Product, ProductImage
from .serializers import ProductSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def add_product(request):
    serializer = ProductSerializer(data=request.data)
    if serializer.is_valid():
        product = serializer.save()

        # Handle multiple images
        images = request.FILES.getlist('images')
        for img in images:
            ProductImage.objects.create(product=product, image=img)

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
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def edit_product(request, pk):
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = ProductSerializer(product, data=request.data)
    if serializer.is_valid():
        product = serializer.save()

        # Handle new images (replace all)
        images = request.FILES.getlist('images')
        if images:
            product.images.all().delete()
            for img in images:
                ProductImage.objects.create(product=product, image=img)

        # Re-serialize
        refreshed_serializer = ProductSerializer(product)
        return Response(refreshed_serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_product(request, pk):
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
    product.delete()
    return Response({"message": "Product deleted successfully"})