from django.urls import path

from notifications import views

app_name = 'notifications'

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='list'),
    path('mark-all-read/', views.NotificationMarkAllReadView.as_view(), name='mark_all_read'),
    path('<int:pk>/open/', views.NotificationOpenView.as_view(), name='open'),
]
