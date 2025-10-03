from django.urls import path
from . import views

app_name = 'accounts' 

urlpatterns = [
    path('', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('signout/', views.signout, name='signout'),
    path('change_password/', views.change_password, name='change_password'),
    path('profile/', views.profile, name='profile'),
]