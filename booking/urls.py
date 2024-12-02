# booking/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.book_appointment, name='book_appointment'),
     path('home/', views.home, name='home'),
    path('confirm/', views.confirm, name='confirm'),
    path('branches/', views.fetch_branches, name='fetch_branches'),
    path('services/', views.fetch_services, name='fetch_services'),
    path('dashboard/', views.dashboard, name='dashboard'),  # New dashboard route

]
