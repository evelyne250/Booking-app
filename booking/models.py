# booking/models.py
from django.db import models

class Branch(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    is_for_individual = models.BooleanField(default=True)
    is_for_business = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_for_individual = models.BooleanField(default=True)
    is_for_business = models.BooleanField(default=False)
    def __str__(self):
        return self.name

class Booking(models.Model):
    CUSTOMER_TYPE_CHOICES = [
        ('new-customer', 'New Customer'),
        ('existing-customer', 'Existing Customer'),
    ]

    USER_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('business', 'Business'),
    ]
    user_type = models.CharField(
        max_length=20, 
        choices=USER_TYPE_CHOICES, 
        default='individual'
    )
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15, null=True) 
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True)
    manual_branch = models.CharField(max_length=100, null=True, blank=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    customer_type = models.CharField(
        max_length=20, 
        choices=CUSTOMER_TYPE_CHOICES, 
        default='new-customer'
    )

    business_name = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.branch} - {self.service} at {self.date} {self.time}"
