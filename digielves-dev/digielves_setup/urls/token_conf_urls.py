from django.urls import path

from digielves_setup.view.token_conf import CustomTokenRefreshView

urlpatterns = [
    
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
]
