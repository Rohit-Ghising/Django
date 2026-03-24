from django.db import models
from django.conf import settings
from products.models import Product  # your existing Product model

User = settings.AUTH_USER_MODEL  # works with custom user models

class Cart(models.Model):
    user = models.ForeignKey(User, related_name='carts', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_ordered = models.BooleanField(default=False)  # True after checkout

    def __str__(self):
        return f"Cart of {self.user.username} ({'Ordered' if self.is_ordered else 'Active'})"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='cart_items', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def total_price(self):
        # Use discount_price if available
        if self.product.discount_price:
            return self.quantity * self.product.discount_price
        return self.quantity * self.product.price