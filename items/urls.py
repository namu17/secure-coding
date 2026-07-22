from django.urls import path

from items import views

app_name = 'items'

urlpatterns = [
    path('', views.ItemListView.as_view(), name='list'),
    path('new/', views.ItemCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ItemDetailView.as_view(), name='detail'),
]
