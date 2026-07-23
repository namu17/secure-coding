from django.urls import path

from items import views

app_name = 'items'

urlpatterns = [
    path('', views.ItemListView.as_view(), name='list'),
    path('new/', views.ItemCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ItemDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ItemUpdateView.as_view(), name='update'),
    path('<int:pk>/status/', views.ItemStatusUpdateView.as_view(), name='status'),
    path('<int:pk>/delete/', views.ItemDeleteView.as_view(), name='delete'),
    path('<int:pk>/like/', views.ToggleLikeView.as_view(), name='like'),
    path('<int:pk>/report/', views.ReportItemView.as_view(), name='report'),
]
