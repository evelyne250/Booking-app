# booking/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.book_appointment, name='book_appointment'),
     path('home/', views.home, name='home'),
    path('confirm/', views.confirm, name='confirm'),
    
    path('dashboard/', views.dashboard, name='dashboard'),  # New dashboard route

]
