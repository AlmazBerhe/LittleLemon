from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import MenuItem, Category
from .serializers import MenuItemsSerializer, CategorySerializer, SingleMenuItemSerializer, GroupsSerializer
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
    

class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = SingleMenuItemSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
           
        return [IsAdminUser()]
    
    
    
class ManagersView(generics.ListCreateAPIView):
    
    serializer_class = GroupsSerializer

    # def get_queryset(self):
    #     # user_group = Group.objects.filter(name="Manager").first()
    
    #     # if user_group:
    #     #     return User.objects.filter(groups=user_group)
        
    #     group = Group.objects.filter(name="Manager").first()

    #     if group:
    #         group_id = group.id
    #         if self.request.user.groups.filter(name="Manager").exists() or self.request.user.is_staff:
    #             return User.objects.filter(groups=group_id)
    #             # return Response({"message": "Users"}, status=status.HTTP_200_OK)
            
    #         # return Response({"message": "You are not authorized to view managers"}, status=status.HTTP_401_UNAUTHORIZED)
       
    #     return User.objects.none()

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

        # if group:
        #     group_id = group.id
        #     if self.IsManagerOrIsAdmin():
                
        #         users = User.objects.filter(groups=group_id)
        #         return Response(users.values('id', 'username', 'email', 'groups'), status=status.HTTP_200_OK)
            
        #     return Response({"message": "You are not authorized to perform this action"}, status=status.HTTP_401_UNAUTHORIZED)
       
        # return Response({"message": "Resource not found"}, status=status.HTTP_404_NOT_FOUND)
    

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
        # userId = self.request.data.get('userId')
        # return Response({"message": f"{userId}"}, status=status.HTTP_400_BAD_REQUEST)
        if not self.IsManagerOrIsAdmin():
            return Response({"message": "You are not authorized to perform this action"}, status=status.HTTP_401_UNAUTHORIZED)
        

        if userId is None:
            return Response({"message": "Missing userId"}, status=status.HTTP_400_BAD_REQUEST)


        user = get_object_or_404(User, id=userId)
        managers = Group.objects.get(name="Manager")
        managers.user_set.remove(user)
        
        return Response({"message": "user removed from group"}, status=status.HTTP_200_OK)

    
