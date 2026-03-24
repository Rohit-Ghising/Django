from django.db import models

class Product(models.Model):
    # Categories as Enum choices
    PHONES = 'phones'
    LAPTOPS = 'laptops'
    HEADPHONES = 'headphones'
    SMARTWATCHES = 'smartwatches'
    ACCESSORIES = 'accessories'
    ELECTRONICS = 'electronics'
    FASHION = 'fashion'
    BOOKS = 'books'
    HOME = 'home'
    TOYS = 'toys'
    
    CATEGORY_CHOICES = [
        (PHONES, 'Phones'),
        (LAPTOPS, 'Laptops'),
        (HEADPHONES, 'Headphones'),
        (SMARTWATCHES, 'Smartwatches'),
        (ACCESSORIES, 'Accessories'),
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
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=4.5)
    review_count = models.PositiveIntegerField(default=0)
    featured = models.BooleanField(default=False)
    trending = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# Product images: multiple and required
class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.URLField(max_length=1024)

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
