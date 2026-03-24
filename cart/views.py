from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Cart, CartItem
from .serializers import CartSerializer, AddCartItemSerializer, UpdateCartItemSerializer
from products.models import Product
from orders.models import Order, OrderItem
from orders.serializers import OrderSerializer

# Get or create active cart for user
def get_user_cart(user):
    cart, created = Cart.objects.get_or_create(user=user, is_ordered=False)
    return cart

# List user's cart
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cart_detail(request):
    cart = get_user_cart(request.user)
    serializer = CartSerializer(cart)
    return Response(serializer.data)

# Add product to cart
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    serializer = AddCartItemSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    product_id = serializer.validated_data['product_id']
    quantity = serializer.validated_data['quantity']
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
    cart = get_user_cart(request.user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity},
    )
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    cart_serializer = CartSerializer(cart)
    return Response(cart_serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_cart(request):
    cart = get_user_cart(request.user)
    cart.items.all().delete()
    serializer = CartSerializer(cart)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout_cart(request):
    cart = get_user_cart(request.user)
    if not cart.items.exists():
        return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
    cart_items = list(cart.items.select_related('product'))
    order_total = sum(item.total_price for item in cart_items)
    order = Order.objects.create(
        user=request.user,
        cart_id=cart.id,
        total_price=order_total,
        status=Order.STATUS_COMPLETED,
    )

    order_items = []
    for item in cart_items:
        unit_price = item.product.discount_price if item.product.discount_price else item.product.price
        order_items.append(OrderItem(
            order=order,
            product=item.product,
            quantity=item.quantity,
            unit_price=unit_price,
        ))
    OrderItem.objects.bulk_create(order_items)

    cart.items.all().delete()
    cart.is_ordered = True
    cart.save()
    new_cart = get_user_cart(request.user)
    cart_serializer = CartSerializer(new_cart)
    order_serializer = OrderSerializer(order)
    return Response({
        'message': 'Checkout complete',
        'order': order_serializer.data,
        'cart': cart_serializer.data,
    })

# Update quantity
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user, cart__is_ordered=False)
    except CartItem.DoesNotExist:
        return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = UpdateCartItemSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    cart_item.quantity = serializer.validated_data['quantity']
    cart_item.save()
    cart = get_user_cart(request.user)
    cart_serializer = CartSerializer(cart)
    return Response(cart_serializer.data)

# Remove item from cart
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_cart_item(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user, cart__is_ordered=False)
    except CartItem.DoesNotExist:
        return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)
    
    cart_item.delete()
    cart = get_user_cart(request.user)
    serializer = CartSerializer(cart)
    return Response(serializer.data)
