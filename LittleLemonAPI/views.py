from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import MenuItem, Category, Cart, Order, OrderItem
from .serializers import MenuItemsSerializer, CategorySerializer, SingleMenuItemSerializer, GroupsSerializer, CartItemsSerializer
from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404

class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemsSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
           
        return [IsAdminUser()]
    

class CartMenuItemsView(generics.ListCreateAPIView):
    
    serializer_class = CartItemsSerializer

    def get_queryset(self):

        user = self.request.user

        return Cart.objects.filter(user=user)
    

    def post(self, request): 

        menuitemId = self.request.data.get('menuitemId')

        if not menuitemId:
            return Response({"method": "Bad Request. Fields missing"}, status=status.HTTP_400_BAD_REQUEST)
        
        quantity = int(self.request.data.get('quantity', 1))

        menuItem = MenuItem.objects.get(id=menuitemId)

        if not menuItem:
            return Response({"method": "Resource not found"}, status=status.HTTP_404_NOT_FOUND)
        
        user = self.request.user

        existingCartItem = Cart.objects.filter(user=user,menuitem=menuItem).first()


        if existingCartItem:
           existingCartItem.quantity = quantity
           existingCartItem.save()
        else:
            cartItem = Cart(
            user=user,
            menuitem=menuItem,
            quantity=quantity,
            unit_price=menuItem.price,
            price=quantity*menuItem.price
        )
            cartItem.save()
        
        return Response({"message": "Added/updated successfully"}, status=status.HTTP_200_OK)
    

    def delete(self, request):

        user = self.request.user

        carts = Cart.objects.filter(user=user)
        carts.delete()

        return Response({"message": "Cart emptied"}, status=status.HTTP_200_OK)


class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = SingleMenuItemSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
           
        return [IsAdminUser()]
    
    
    
class ManagersView(generics.ListCreateAPIView):
    
    serializer_class = GroupsSerializer

    def IsManagerOrIsAdmin(self):
        return self.request.user.groups.filter(name="Manager").exists() or self.request.user.is_staff
        
    def get(self, request):

        if not self.IsManagerOrIsAdmin():
            return Response({"message": "You are not authorized to perform this action"}, status=status.HTTP_401_UNAUTHORIZED)
   
        group = Group.objects.filter(name="Manager").first()

        if not group:
            return Response({"message": "Resource not found"}, status=status.HTTP_404_NOT_FOUND)
        
        group_id = group.id
        users = User.objects.filter(groups=group_id)

        return Response(users.values('id', 'username', 'email', 'groups'), status=status.HTTP_200_OK)


    def post(self, username):

        if not self.IsManagerOrIsAdmin():
            return Response({"message": "You are not authorized to perform this action"}, status=status.HTTP_401_UNAUTHORIZED)
        
        username = self.request.data['username']
        if username:
            # return Response({"message": f"missing {username}"}, status=status.HTTP_200_OK)
            user = get_object_or_404(User, username=username)
            managers = Group.objects.get(name="Manager")
            managers.user_set.add(user)

        return Response({"message": "user added to group"}, status=status.HTTP_200_OK)

    def delete(self, request, userId):

        if not self.IsManagerOrIsAdmin():
            return Response({"message": "You are not authorized to perform this action"}, status=status.HTTP_401_UNAUTHORIZED)
        

        if userId is None:
            return Response({"message": "Missing userId"}, status=status.HTTP_400_BAD_REQUEST)


        user = get_object_or_404(User, id=userId)
        managers = Group.objects.get(name="Manager")
        managers.user_set.remove(user)
        
        return Response({"message": "user removed from group"}, status=status.HTTP_200_OK)
    

class DeliveryCrewsView(generics.ListCreateAPIView):
    
    serializer_class = GroupsSerializer

    def IsManagerOrIsAdmin(self):
        return self.request.user.groups.filter(name="Manager").exists() or self.request.user.is_staff
        
    def get(self, request):

        if not self.IsManagerOrIsAdmin():
            return Response({"message": "You are not authorized to perform this action"}, status=status.HTTP_401_UNAUTHORIZED)

        group = Group.objects.filter(name="DeliveryCrew").first()

        if not group:
            return Response({"message": "Resource not found"}, status=status.HTTP_404_NOT_FOUND)
        
        group_id = group.id
        users = User.objects.filter(groups=group_id)

        return Response(users.values('id', 'username', 'email', 'groups'), status=status.HTTP_200_OK)


    def post(self, username):

        if not self.IsManagerOrIsAdmin():
            return Response({"message": "You are not authorized to perform this action"}, status=status.HTTP_401_UNAUTHORIZED)
        
        username = self.request.data['username']

        if username:
            user = get_object_or_404(User, username=username)
            managers = Group.objects.get(name="DeliveryCrew")
            managers.user_set.add(user)

        return Response({"message": "user added to group"}, status=status.HTTP_200_OK)
    

    def delete(self, request, userId):

        if not self.IsManagerOrIsAdmin():
            return Response({"message": "You are not authorized to perform this action"}, status=status.HTTP_401_UNAUTHORIZED)
        

        if userId is None:
            return Response({"message": "Missing userId"}, status=status.HTTP_400_BAD_REQUEST)


        user = get_object_or_404(User, id=userId)
        managers = Group.objects.get(name="DeliveryCrew")
        managers.user_set.remove(user)
        
        return Response({"message": "user removed from group"}, status=status.HTTP_200_OK)

    
