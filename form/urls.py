from django.urls import path
from django.conf.urls import url

from . import views

app_name = 'form'

urlpatterns = [
    # ex: /
    path('', views.home, name='home'),
    # ex: /signup
    path('signup', views.signup, name='signup'),
    # ex: /privacy
    path('privacy', views.privacy, name='privacy'),
    # ex: /login
    url(r'^login/$', views.login, name='login'),
    # ex: /dashboard
    path('dashboard', views.dashboard, name='dashboard'),
]