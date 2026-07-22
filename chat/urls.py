from django.urls import path

from chat import views

app_name = 'chat'

urlpatterns = [
    path('', views.ChatRoomListView.as_view(), name='room_list'),
    path('<int:pk>/', views.ChatRoomDetailView.as_view(), name='room_detail'),
    path('start/<int:item_id>/', views.StartChatView.as_view(), name='start'),
]
