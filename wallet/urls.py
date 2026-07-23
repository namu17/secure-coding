from django.urls import path

from wallet import views

app_name = 'wallet'

urlpatterns = [
    path('charge/', views.ChargeView.as_view(), name='charge'),
    path('chats/<int:room_id>/transfer/', views.TransferView.as_view(), name='transfer'),
]
