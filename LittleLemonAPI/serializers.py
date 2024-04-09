from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator
from .models import MenuItem, Category, Cart, Order, OrderItem
from django.contrib.auth.models import User, Group
import bleach

class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ['id','slug', 'title']

class MenuItemsSerializer(serializers.ModelSerializer):
    
    category = CategorySerializer(Category, read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    title =  serializers.CharField(
        validators = [
            UniqueValidator(
                queryset=MenuItem.objects.all()
                )
                ]
        )

    def validate_title(self, attrs):
        return bleach.clean(attrs)

    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category', 'category_id']
      
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

        def validate_status(self, attrs):
            return bleach.clean(attrs)
        
        def validate_delivery_crew(self, attrs):
            return bleach.clean(attrs)

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


class OrderMenuItemSerializer(serializers.ModelSerializer):
    
    menuitem = SingleMenuItemSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'quantity', 'unit_price', 'price', 'menuitem']



class GroupsSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'groups']
