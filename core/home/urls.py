from django.contrib import admin
from django.urls import path
from home import views

urlpatterns = [
    path('logout/', views.custom_logout, name='custom_logout'),
    path('pdf/', views.pdf , name='pdf'),
    path('admin/', admin.site.urls),
    path('login/' , views.login_page, name='login'),
    path('register/', views.register_page, name='register'),
    path('', views.expenses, name='expenses'),
    path('update_expense/<id>', views.update_expense, name='update_expense'),
    path('delete_expense/<id>', views.delete_expense, name='delete_expense'),
    path('settings/', views.settings, name='settings'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('reports/', views.reports, name='reports'),
    path('reports/pdf/', views.export_pdf, name='export_pdf'),
    path('reports/csv/', views.export_csv, name='export_csv'),
]
