from django.urls import path
from . import views

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
    path('staff/<str:unique_id>/contract/create/', views.ContractCreateView.as_view(), name='contract_create'),
    path('contracts/', views.contracts, name='contracts'),
    path('contract/<uuid:pk>/renew/', views.ContractRenewView.as_view(), name='contract_renew'),
    path('contract/<uuid:pk>/', views.ContractDetailView.as_view(), name='contract_detail'),
    path('contract/<uuid:pk>/update/', views.ContractUpdateView.as_view(), name='contract_update'),
    path('contract/<uuid:pk>/delete/', views.ContractDeleteView.as_view(), name='contract_delete'),
    path('billing/', views.billing, name='billing'),
    path('about/', views.about, name='about'),
]