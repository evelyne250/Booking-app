import csv
from datetime import timedelta
from django.core.management.base import BaseCommand
from booking.models import ServiceTime

class Command(BaseCommand):
    help = "Load service times from Service_Time.csv"

    def handle(self, *args, **kwargs):
        with open('Service_Time.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                service_name = row['Service']
                time_parts = row['Avrg service time (Hrs:Min:Sec)'].split(':')
                average_time = timedelta(
                    hours=int(time_parts[0]),
                    minutes=int(time_parts[1]),
                    seconds=int(time_parts[2])
                )
                ServiceTime.objects.update_or_create(
                    service_name=service_name,
                    defaults={'average_time': average_time}
                )
        self.stdout.write(self.style.SUCCESS("Service times loaded successfully!"))