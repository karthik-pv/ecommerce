from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("product/<int:pk>/", views.product_detail, name="product_detail"),
    path("search", views.product_search, name="product_search"),
    path("chat/", views.product_chat, name="product_chat"),
]
