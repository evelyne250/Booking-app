# booking/models.py
from django.db import models
from django.core.exceptions import ValidationError
from datetime import timedelta

def validate_account_number(value):
    if len(value) not in [12, 15]:
        raise ValidationError("Account number must be either 12 or 15 digits long.")
    # Check for duplicate account_number
    if Booking.objects.filter(account_number=self.account_number).exclude(pk=self.pk).exists():
        raise ValueError("A booking with this account number already exists.")

    super().save(*args, **kwargs)

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
    def save(self, *args, **kwargs):
        # Normalize the name to uppercase before saving
        self.name = self.name.upper()
        super().save(*args, **kwargs)

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
    full_name = models.CharField(max_length=200)  # Full name for both individuals and businesses
    account_number = models.CharField(max_length=15)  # Optional for individuals
    phone_number = models.CharField(max_length=15)  # Required for both
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
    business_name = models.CharField(max_length=100, null=True, blank=True)  # Only for businesses

    def __str__(self):
        return f"{self.branch} - {self.service} at {self.date} {self.time}"
    
    def save(self, *args, **kwargs):
        # Ensure account_number is filled for both individuals and businesses
        if not self.account_number:
            raise ValueError("Account number is required for all users.")
        super().save(*args, **kwargs)


class TimeSlot(models.Model):
    branch = models.CharField(max_length=100)
    service = models.CharField(max_length=100)
    date = models.DateField()
    time = models.TimeField()
    bookings = models.IntegerField(default=0)
    capacity = models.IntegerField(default=10)  # Default capacity


from django.db import models

class Customer(models.Model):
    customer_no = models.CharField(max_length=100, unique=True)  # CUSTOMER_NO
    given_names = models.CharField(max_length=255)
    family_name = models.CharField(max_length=255)
    email_1 = models.EmailField(null=True, blank=True)
    sms_1 = models.CharField(max_length=20, null=True, blank=True)  # SMS_1
    date_of_birth = models.DateField(null=True, blank=True)
    legal_id = models.CharField(max_length=100, null=True, blank=True)
    legal_doc_file = models.FileField(upload_to='kyc_docs/', null=True, blank=True)  # for uploads
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.given_names} {self.family_name}"

class ServiceTime(models.Model):
    service_name = models.CharField(max_length=100, unique=True)
    average_time = models.DurationField(null=True, blank=True)  # Store time as a duration

    def __str__(self):
        return self.service_name

    def get_average_time(self):
        # Return the average time or default to 6 minutes
        return self.average_time if self.average_time else timedelta(minutes=6)