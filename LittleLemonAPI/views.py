from django.forms import ValidationError
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, BasePermission
from .models import MenuItem, Category, Cart, Order, OrderItem
from .serializers import MenuItemsSerializer, CategorySerializer, SingleMenuItemSerializer, GroupsSerializer, CartItemsSerializer, OrdersSerializer, OrderItemsSerializer, OrderMenuItemSerializer
from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404
from datetime import datetime
from django.core.paginator import Paginator, EmptyPage
from rest_framework.throttling import UserRateThrottle
from decimal import Decimal, InvalidOperation
import bleach
from django.core.exceptions import FieldError


class IsManagerOrIsAdmin(BasePermission):
    
    def has_permission(self, request, view):
        return request.user.groups.filter(name="Manager").exists() or request.user.is_staff 

class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class MenuItemsView(generics.ListCreateAPIView):
    throttle_classes = [UserRateThrottle]
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemsSerializer

    def get(self, request):
        items = MenuItem.objects.select_related('category').all()

        category_name = request.data.get('category')
        min_price = request.data.get('price_from')
        max_price = request.data.get('price_to')
        ordering = request.data.get('ordering')
        per_page = request.data.get('per_page', len(items))
        
        try:
            per_page = int(per_page)
        except ValueError:
            return Response({"message": "Value error"}, status=status.HTTP_400_BAD_REQUEST)
            
        page = request.data.get('page', 1)
        
        try:
            page = int(page)
        except ValueError:
            return Response({"message": "Value error"}, status=status.HTTP_400_BAD_REQUEST)
        
        if category_name:
            category_name = bleach.clean(category_name)
            items = items.filter(category__title__icontains=category_name)

        if min_price:
            try:
                min_price = Decimal(min_price)
            except InvalidOperation:
                return Response({"message": "Value error"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                items = items.filter(price__gte=min_price)

        if max_price:
            try:
                max_price = Decimal(max_price)
            except InvalidOperation:
                return Response({"message": "Value error"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                items = items.filter(price__lte=max_price)
            

        if ordering:
            ordering = bleach.clean(ordering)
            ordering_fields = ordering.split(",")
            try:
                items = items.order_by(*ordering_fields)
            except FieldError:
                return Response({"message": "Field error"}, status=status.HTTP_400_BAD_REQUEST)
            

        paginator = Paginator(items, per_page=per_page)
        try:
            items = paginator.page(number=page)
        except EmptyPage:
            items = []

        serializer = MenuItemsSerializer(items, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)   
    
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
           
        return [IsManagerOrIsAdmin()]
    

class CartMenuItemsView(generics.ListCreateAPIView):
    throttle_classes = [UserRateThrottle]
    serializer_class = CartItemsSerializer

    def get_queryset(self):

        user = self.request.user

        return Cart.objects.filter(user=user)
    

    def post(self, request): 

        menuitemId = self.request.data.get('menuitemId')

        if not menuitemId:
            return Response({"message": "Fields missing"}, status=status.HTTP_400_BAD_REQUEST)
        
        quantity = int(self.request.data.get('quantity', 1))
        
        try:
            menuItem = get_object_or_404(MenuItem.objects.filter(id=menuitemId))
        except ValueError:
            return Response({"message": "Value error"}, status=status.HTTP_400_BAD_REQUEST)

        
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
    throttle_classes = [UserRateThrottle]
    queryset = MenuItem.objects.all()
    serializer_class = SingleMenuItemSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
           
        return [IsManagerOrIsAdmin()]
     
    
class ManagersView(generics.ListCreateAPIView):
    throttle_classes = [UserRateThrottle]
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
        
        if not user.groups.filter(name="Manager").exists():
            return Response({"message": "Resource not found"}, status=status.HTTP_404_NOT_FOUND)

        
        managers = Group.objects.get(name="Manager")
        managers.user_set.remove(user)
        
        return Response({"message": "user removed from group"}, status=status.HTTP_200_OK)
    

class DeliveryCrewsView(generics.ListCreateAPIView):
    throttle_classes = [UserRateThrottle]
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
    throttle_classes = [UserRateThrottle]
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
        
        order_status = request.data.get('status')
        ordering = request.data.get('ordering')
        per_page = request.data.get('per_page', len(orders))
        
        try:
            per_page = int(per_page)
        except ValueError:
            return Response({"message": "Value error"}, status=status.HTTP_400_BAD_REQUEST)
        
        page = request.data.get('page', 1)
        
        try:
            page = int(page)
        except ValueError:
            return Response({"message": "Value error"}, status=status.HTTP_400_BAD_REQUEST)

        if order_status:
            try:
                orders = orders.filter(status=order_status)
            except ValidationError:
                return Response({"message": "Value error"}, status=status.HTTP_400_BAD_REQUEST)

        if ordering:
            ordering_fields = ordering.split(",")
            try:
                orders = orders.order_by(*ordering_fields)
            except FieldError:
                return Response({"message": "Field error"}, status=status.HTTP_400_BAD_REQUEST)
            

        paginator = Paginator(orders, per_page=per_page)
        try:
            orders = paginator.page(number=page)
        except EmptyPage:
            orders = []
       
        serializer = OrdersSerializer(orders, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    def post(self, request):

        user = self.request.user
        cart = get_object_or_404(Cart.objects.filter(user=user))

        total_order_price = 0
        for item in cart:
            total_order_price += Decimal(item.price)

        # if not cart:
        #     return Response({"message": "Resources not found"}, status=status.HTTP_404_NOT_FOUND)
        
        order = Order(
            user=user,
            total=total_order_price,
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
    throttle_classes = [UserRateThrottle]
    
    def IsManagerOrIsAdmin(self):
        return self.request.user.groups.filter(name="Manager").exists() or self.request.user.is_staff
        

    def get(self, request, orderId):

        user = request.user

        order = get_object_or_404(Order.objects.filter(id=orderId, user=user))

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
        
        return Response({"message": "You are not authorized to perform this action"}, status=status.HTTP_401_UNAUTHORIZED)


    def patch(self, request, orderId):
        order = get_object_or_404(Order.objects.filter(id=orderId))
        
        if self.IsManagerOrIsAdmin() or request.user.groups.filter(name="DeliveryCrew").exists():
            order_status = request.data.get('status')

            if request.user.groups.filter(name="DeliveryCrew").exists():
                order = get_object_or_404(Order.objects.filter(id=orderId, delivery_crew=request.user))
                
            
            if order_status:

                order.status = order_status
                order.save()

                return Response({"message": "Order updated."}, status=status.HTTP_200_OK)
        
        
        if self.IsManagerOrIsAdmin():
            delivery_crew_id = request.data.get('delivery_crew')
            delivery_crew = User.objects.get(id=delivery_crew_id)
            
            if delivery_crew:

                order.delivery_crew = delivery_crew
                order.save()
                
                return Response({"message": "Order updated."}, status=status.HTTP_200_OK)
        
        return Response({"message": "You are not authorized to perform this action"}, status=status.HTTP_401_UNAUTHORIZED)


    
    def delete(self, request, orderId):

        if self.IsManagerOrIsAdmin():
            order = get_object_or_404(Order.objects.filter(id=orderId))

            order.delete()

            return Response({"message": "Order deleted."}, status=status.HTTP_200_OK)
        

        return Response({"message": "You are not authorized to perform this action"}, status=status.HTTP_401_UNAUTHORIZED)
    

class OrderMenuitemView(generics.RetrieveUpdateDestroyAPIView):
    
    def get(self, request, orderId, orderitemId):
        
        order = get_object_or_404(Order.objects.filter(user=request.user, id=orderId))
        
        order_item = get_object_or_404(OrderItem.objects.filter(order=order, id=orderitemId))
       
        serializer = OrderMenuItemSerializer(order_item)
       
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    def patch(self, request, orderId, orderitemId):
        
        quantity = request.data.get("quantity")
        
        if not quantity:
            return Response({"message": "Fields missing"}, status=status.HTTP_400_BAD_REQUEST)

        order = get_object_or_404(Order.objects.filter(user=request.user, id=orderId))
        
        order_item = get_object_or_404(OrderItem.objects.filter(order=order, id=orderitemId))
        
        try:
            order_item.quantity = quantity
            order_item.price = Decimal(quantity) * order_item.unit_price
        except InvalidOperation:
            return Response({"message": "Value error"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            order_item.save()
        
        order_items = OrderItem.objects.filter(order=order)
        
        new_order_total = 0
        for item in order_items:
            new_order_total += item.price
            
        order.total = new_order_total
        order.save()
        
        
        return Response({"message": "Updated successfully"}, status=status.HTTP_200_OK)
    

    def delete(self, request, orderId, orderitemId):
        
        order = get_object_or_404(Order.objects.filter(user=request.user, id=orderId))
        
        if IsAdminUser():
            order = get_object_or_404(Order.objects.filter(id=orderId))
        
        order_item = get_object_or_404(OrderItem.objects.filter(order=order, id=orderitemId))
        
        order_item.delete()
        
        return Response({"message": "Item removed from order successfully"}, status=status.HTTP_200_OK)
        
        
        

