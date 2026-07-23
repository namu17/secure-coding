from django.urls import path

from accounts import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', views.TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', views.ProfileView.as_view(), name='profile'),
    path('me/verify/', views.ProfileReauthView.as_view(), name='profile_reauth'),
]
