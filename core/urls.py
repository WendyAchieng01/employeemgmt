from django.urls import path
from . import views
import payroll.views as payroll_views

app_name = 'core'

urlpatterns = [
    path('', views.staff_list, name='staff_list'),
    path('locumers/', views.lcdash, name='locumdash'),
    path('casuals/', views.cdash, name='casuals'),
    path('create/', views.staff_create, name='staff_create'),
    path('staff/<str:unique_id>/', views.staff_detail, name='staff_detail'),
    path('<str:unique_id>/update/', views.staff_update, name='staff_update'),
    path('department/<int:dept_id>/', views.department_staff, name='department_staff'),
    path('api/staff/', views.staff_api, name='staff_api'),
    path('staff/<str:unique_id>/delete/', views.delete_staff, name='delete_staff'),
    path('staff/<str:unique_id>/contract/create/', views.contract_create, name='contract_create'),
    path('contracts/', views.contracts, name='contracts'),
    path('contract/<str:unique_id>/renew/', views.contract_renew, name='contract_renew'),
    path('contract/<str:unique_id>/', views.contract_detail, name='contract_detail'),
    path('contract/<str:unique_id>/update/', views.contract_update, name='contract_update'),
    path('contract/<str:unique_id>/delete/', views.contract_delete, name='contract_delete'),
    path('billing/', views.billing, name='billing'),
    path('about/', views.about, name='about'),
    path('staff/<str:unique_id>/payroll/create/', 
     payroll_views.payroll_create_view, 
     name='payroll_create'),
    path('staff/<str:unique_id>/payroll/edit/', 
     payroll_views.payroll_update_view, 
     name='payroll_update'),
]