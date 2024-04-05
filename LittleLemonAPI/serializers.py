from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator
from .models import MenuItem, Category, Cart, Order, OrderItem
from django.contrib.auth.models import User, Group


class MenuItemsSerializer(serializers.ModelSerializer):
    
    category = serializers.StringRelatedField()

    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category']

        validators = [
            UniqueValidator('title')
        ]

        extra_kwargs = {
            'price': {'min_value': 0}
        }

class CartItemsSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = Cart
        fields = ['id', 'user', 'menuitem', 'quantity', 'unit_price', 'price']

        validators = [
            UniqueTogetherValidator(
                queryset=Cart.objects.all(),
                fields=['user', 'menuitem']
            )
        ]

        extra_kwargs = {
            'quantity': {'min_value': 1}
        }


class OrderItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'menuitem', 'quantity', 'unit_price', 'price']

        validators = [
            UniqueTogetherValidator(
                queryset=OrderItem.objects.all(),
                fields=['order', 'menuitem']
            )
        ]

        extra_kwargs = {
            'quantity': {'min_value': 1}
        }


class OrdersSerializer(serializers.ModelSerializer):
  
    order_items = OrderItemsSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew', 'status', 'total', 'date', 'order_items']

        validators = [
            UniqueTogetherValidator(
                queryset=Order.objects.all(),
                fields=['user', 'date']
            )
        ]


class SingleMenuItemSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category']


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ['id','slug', 'title']


class GroupsSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'groups']
