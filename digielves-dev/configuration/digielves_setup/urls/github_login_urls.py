

from django.contrib import admin
from django.urls import path, include

from digielves_setup.view.github_login import GithubSocialAuthView

urlpatterns = [
    #path('github/', GithubSocialAuthView.as_view({'post': 'post'})),
    path('github/', GithubSocialAuthView.as_view(), name='github-social-auth'),
]