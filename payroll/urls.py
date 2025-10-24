from django.urls import path
from . import views
from .views import *

app_name = 'payroll'

urlpatterns = [
    path('staff/<str:unique_id>/payroll/create/', 
         PayrollCreateView.as_view(), 
         name='payroll_create'),
    path('staff/<str:unique_id>/', PayrollDetailView.as_view(), name='payroll_detail'),
]