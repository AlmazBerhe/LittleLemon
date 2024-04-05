from django.urls import path, include
from . import views

urlpatterns = [
    path('categories', views.CategoriesView.as_view()),
    path('menu-items', views.MenuItemsView.as_view()),
    path('menu-items/<int:pk>', views.SingleMenuItemView.as_view()),
    path('groups/manager/users', views.ManagersView.as_view()),
    path('groups/manager/users/<int:userId>', views.ManagersView.as_view()),
    path('groups/delivery-crew/users', views.DeliveryCrewsView.as_view()),
    path('groups/delivery-crew/users/<int:userId>', views.DeliveryCrewsView.as_view()),
    path('cart/menu-items', views.CartMenuItemsView.as_view()),
    path('orders', views.OrderItemsView.as_view()),
    path('orders/<int:orderId>', views.SingleOrderView.as_view()),
]