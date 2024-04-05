from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import MenuItem, Category, Cart, Order, OrderItem
from .serializers import MenuItemsSerializer, CategorySerializer, SingleMenuItemSerializer, GroupsSerializer, CartItemsSerializer, OrdersSerializer, OrderItemsSerializer
from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404
from datetime import datetime

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

    
class OrderItemsView(generics.ListAPIView):
    
    serializer_class = OrderItemsSerializer

    def IsManagerOrIsAdmin(self):
        return self.request.user.groups.filter(name="Manager").exists() or self.request.user.is_staff

    def get(self, request):
        
        user = self.request.user

        if self.IsManagerOrIsAdmin():
            orders = Order.objects.all()
        elif self.request.user.groups.filter(name="DeliveryCrew").exists():
            orders = Order.objects.filter(delivery_crew=user.id)
        else:
            orders = Order.objects.filter(user=user)
   
        if not orders:
            return Response(Order.objects.none(), status=status.HTTP_200_OK)
       
        serializer = OrdersSerializer(orders, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    def post(self, request):

        user = self.request.user
        cart = Cart.objects.filter(user=user)

        # Todo - this is not working
        total = 0
        [(total + item.price) for item in cart]

        if not cart:
            return Response({"message": "Resources not found"}, status=status.HTTP_404_NOT_FOUND)
        
        order = Order(
            user=user,
            total=total,
            date=datetime.now()
        )

        order.save()

        for item in cart:
            orderItem = OrderItem(
                order=order,
                menuitem=item.menuitem,
                quantity=item.quantity,
                unit_price=item.unit_price,
                price=item.price
            )
            orderItem.save()

        cart.delete()

        return Response({"message": "Order created"}, status=status.HTTP_200_OK)
    

class SingleOrderView(generics.RetrieveUpdateDestroyAPIView):

    # serializer_class = OrdersSerializer
    def IsManagerOrIsAdmin(self):
        return self.request.user.groups.filter(name="Manager").exists() or self.request.user.is_staff
        

    def get(self, request, orderId):

        user = request.user

        order = get_object_or_404(Order.objects.filter(id=orderId, user=user))

        # if not order:
        #     return Response({"message": "Resources not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serialzer = OrdersSerializer(order)

        return Response(serialzer.data, status=status.HTTP_200_OK)
    

    def put(self, request, orderId):

    
        if self.IsManagerOrIsAdmin():

            order = get_object_or_404(Order.objects.filter(id=orderId))

            order_status = request.data.get('status')
            delivery_crew_id = request.data.get('delivery_crew_id')

            delivery_group_id = Group.objects.filter(name="DeliveryCrew").first()
            delivery_crew = User.objects.filter(id=delivery_crew_id, groups=delivery_group_id).first()

            if not (order_status or delivery_crew):
                return Response({"message": "Missing fields"}, status=status.HTTP_400_BAD_REQUEST)

            if order_status:
                order.status = order_status

            if delivery_crew:
                order.delivery_crew = delivery_crew
            
            order.save()

            return Response({"message": "Status updated"}, status=status.HTTP_200_OK)
        

        # Todo - this is not working
        # customer update order

        order = get_object_or_404(Order.objects.filter(id=orderId, user=request.user))

        menuitems = MenuItem.objects.filter(order=order)

        menuitems.delete()

        menuitems = request.data.get('menuitems')  # what datatype should this accept? dict of menuitemid and quantity?

        for item in menuitems:
            order_item = OrderItem(
                order=order,
                menuitem=item.menuitem,
                quantity=item.quantity,
                unit_price=item.price,
                price=(item.price * item.quantity)
            )

            order_item.save()

        return Response({"message": "Order updated"}, status=status.HTTP_200_OK)


    def patch(self, request, orderId):
        
        if self.IsManagerOrIsAdmin() or request.user.groups.filter(name="DeliveryCrew").exists():
            order_status = request.data.get('status')

            if not order_status:
                return Response({"message": "Missing fields"}, status=status.HTTP_400_BAD_REQUEST)
            
            order = get_object_or_404(Order.objects.get(id=orderId))

            order.status = order_status
            order.save()

            return Response({"message": "Order updated."}, status=status.HTTP_200_OK)
        
        # Todo - this is not working
        # customer update order

        order = get_object_or_404(Order.objects.filter(id=orderId, user=request.user))

        menuitems = MenuItem.objects.filter(order=order)

        menuitems.delete()

        menuitems = request.data.get('menuitems')  # what datatype should this accept? dict of menuitemid and quantity?

        for item in menuitems:
            order_item = OrderItem(
                order=order,
                menuitem=item.menuitem,
                quantity=item.quantity,
                unit_price=item.price,
                price=(item.price * item.quantity)
            )

            order_item.save()

        return Response({"message": "Order updated"}, status=status.HTTP_200_OK)


    
    def delete(self, request, orderId):

        if self.IsManagerOrIsAdmin():
            order = get_object_or_404(Order.objects.filter(id=orderId))

            order.delete()

            return Response({"message": "Order deleted."}, status=status.HTTP_200_OK)
        

        return Response({"message": "You are not authorized to perform this action"}, status=status.HTTP_401_UNAUTHORIZED)

        

