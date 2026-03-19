from django.db import models

from myproject.storage_backends import MediaStorage

class Product(models.Model):
    # Categories as Enum choices
    ELECTRONICS = 'electronics'
    FASHION = 'fashion'
    BOOKS = 'books'
    HOME = 'home'
    TOYS = 'toys'
    
    CATEGORY_CHOICES = [
        (ELECTRONICS, 'Electronics'),
        (FASHION, 'Fashion'),
        (BOOKS, 'Books'),
        (HOME, 'Home'),
        (TOYS, 'Toys'),
    ]

    name = models.CharField(max_length=255)  # required
    description = models.TextField()   
    shortdescription = models.TextField()      # required
    brand = models.CharField(max_length=255) # required
    stock = models.PositiveIntegerField()    # required
    price = models.DecimalField(max_digits=10, decimal_places=2)  # required
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # optional
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)  # required
    stars = models.CharField(max_length=5, null=True, blank=True)  # optional
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# Product images: multiple and required
class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/images/', storage=MediaStorage())

    def __str__(self):
        return f"Image for {self.product.name}"


# Optional specs
class ProductSpec(models.Model):
    product = models.ForeignKey(Product, related_name='specs', on_delete=models.CASCADE, null=True, blank=True)
    key = models.CharField(max_length=255, null=True, blank=True)
    value = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.key}: {self.value}"


# Optional tags
class Tag(models.Model):
    product = models.ForeignKey(Product, related_name='tags', on_delete=models.CASCADE, null=True, blank=True)
    key = models.CharField(max_length=255, null=True, blank=True)
    value = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.key}: {self.value}"
