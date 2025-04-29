from django.core.management.base import BaseCommand
import csv
from booking.models import *  # Replace with your actual model

class Command(BaseCommand):
    help = 'Import services from CSV'

    def handle(self, *args, **kwargs):
        with open('Service_Time.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                Service.objects.update_or_create(
                    service_name=row['Service Name'],
                    defaults={'avg_service_time': row['Average Service Time']}
                )
        self.stdout.write(self.style.SUCCESS('Successfully imported services'))
