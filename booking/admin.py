# booking/admin.py
from django.contrib import admin
from .models import Branch, Service, Booking

admin.site.register(Branch)
admin.site.register(Service)
admin.site.register(Booking)