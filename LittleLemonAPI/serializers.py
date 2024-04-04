from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator
from .models import MenuItem, Category
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
        fields = '__all__'