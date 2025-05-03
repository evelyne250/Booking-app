# booking/admin.py
from django.contrib import admin
from .models import Booking, Service, ServiceTime,Customer, Branch

from django.contrib import admin
from django.shortcuts import render
from django.urls import path
from django.contrib import messages
import csv
# from .models import Branch
from django.urls import reverse

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'location')

    def changelist_view(self, request, extra_context=None):
        """Add the import link to the admin change list."""
        extra_context = extra_context or {}
        extra_context['import_link'] = reverse('admin:branch-import-data')
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        """Add a custom URL for file uploads in the admin."""
        urls = super().get_urls()
        custom_urls = [
            path('import-data/', self.admin_site.admin_view(self.import_data), name='branch-import-data'),
        ]
        return custom_urls + urls

    def import_data(self, request):
        """Custom admin view for importing branch data."""
        if request.method == "POST":
            if 'file' in request.FILES:
                file = request.FILES['file']
                try:
                    decoded_file = file.read().decode('utf-8').splitlines()
                    reader = csv.DictReader(decoded_file)
                    for row in reader:
                        Branch.objects.create(
                            name=row['name'],
                            location=row['location']
                        )
                    self.message_user(request, "Branches imported successfully!", level=messages.SUCCESS)
                    return render(request, "admin/import_data_success.html")
                except Exception as e:
                    self.message_user(request, f"Error processing file: {e}", level=messages.ERROR)

        return render(request, "admin/import_data_form.html")


admin.site.register(Booking)
admin.site.register(Service)
admin.site.register(ServiceTime)
admin.site.register(Customer)