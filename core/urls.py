from django.urls import path
from . import views

app_name = 'core' 

urlpatterns = [
    path('', views.staff_list, name='staff_list'),
    path('create/', views.staff_create, name='staff_create'),
    path('staff/<str:unique_id>/', views.staff_detail, name='staff_detail'),
    path('<str:unique_id>/update/', views.staff_update, name='staff_update'),
    path('department/<int:dept_id>/', views.department_staff, name='department_staff'),
    path('api/staff/', views.staff_api, name='staff_api'),
    path('staff/<str:staff_id>/delete/', views.delete_staff, name='delete_staff'),
]