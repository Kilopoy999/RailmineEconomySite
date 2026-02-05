from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('transfer/', views.transfer_money, name='transfer'),
    path('exchange/', views.exchange_currency, name='exchange'),
    path('company/create/', views.create_company, name='create_company'),
    path('company/<int:company_id>/', views.company_dashboard, name='company_dashboard'),
    path('company/<int:company_id>/transfer/', views.company_transfer, name='company_transfer'),
    path('company/<int:company_id>/withdraw/', views.company_withdraw, name='company_withdraw'),
    path('api/update_rate/', views.update_exchange_rate, name='update_rate'),
]