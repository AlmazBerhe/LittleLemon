from django.urls import path, include
from . import views

urlpatterns = [
    path('categories', views.CategoriesView.as_view()),
    path('menu-items', views.MenuItemsView.as_view()),
    path('menu-items/<int:pk>', views.SingleMenuItemView.as_view()),
    path('groups/manager/users', views.ManagersView.as_view()),
    path('groups/manager/users/<int:userId>', views.ManagersView.as_view()),
]