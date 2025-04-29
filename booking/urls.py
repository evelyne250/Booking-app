# booking/urls.py
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.book_appointment, name='book_appointment'),
     path('home/', views.home, name='home'),
    path('confirm/', views.confirm, name='confirm'),
    path('branches/', views.fetch_branches, name='fetch_branches'),
    path('services/', views.fetch_services, name='fetch_services'),
    path('nearby-banks/', views.fetch_nearby_banks, name='nearby_banks'),
    path('dashboard/', views.dashboard, name='dashboard'),  # New dashboard route
    path('api/search-branches/', views.search_branches, name='search_branches'),
    path('upload-customers/', views.upload_customers_csv, name='upload_customers'),
    path('search-customer/', views.search_customer, name='search_customer'),
    path('update-customer/<int:pk>/', views.update_customer, name='update_customer'),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)