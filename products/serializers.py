from rest_framework import serializers
from .models import Product, ProductImage, ProductSpec, Tag

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']

class ProductSpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpec
        fields = ['id', 'key', 'value']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'key', 'value']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    specs = ProductSpecSerializer(many=True, required=False)
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'shortdescription', 'brand', 'stock',
            'price', 'discount_price', 'category', 'stars', 'created_at',
            'images', 'specs', 'tags'
        ]

    def create(self, validated_data):
        specs_data = validated_data.pop('specs', [])
        tags_data = validated_data.pop('tags', [])
        product = Product.objects.create(**validated_data)

        # Create specs
        for spec in specs_data:
            ProductSpec.objects.create(product=product, **spec)

        # Create tags
        for tag in tags_data:
            Tag.objects.create(product=product, **tag)

        return product

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr not in ['images', 'specs', 'tags']:
                setattr(instance, attr, value)
        instance.save()

        # Update specs
        specs_data = validated_data.get('specs')
        if specs_data:
            instance.specs.all().delete()
            for spec in specs_data:
                ProductSpec.objects.create(product=instance, **spec)

        # Update tags
        tags_data = validated_data.get('tags')
        if tags_data:
            instance.tags.all().delete()
            for tag in tags_data:
                Tag.objects.create(product=instance, **tag)

        return instance