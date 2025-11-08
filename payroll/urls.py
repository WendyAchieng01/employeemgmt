from django.urls import path
from . import views
from .views import *

app_name = 'payroll'

urlpatterns = [
    path('payslip/<uuid:pk>/', views.payroll_detail_view, name='payroll_detail'),
    path('staff/<str:unique_id>/create/', views.payroll_create_view, name='payroll_create'),
    path('payslip/update/<uuid:pk>/', views.payroll_update_view, name='payroll_update'),
    path('payrolls/', views.payrolldash, name='payroll_dash'),
    path('payslip/<uuid:pk>/<str:action>/', views.payroll_process_view, name='payroll_process'),
]