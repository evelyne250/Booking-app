# booking/forms.py
from django import forms
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Booking, Branch, Service

class BookingForm(forms.ModelForm):
    CUSTOMER_TYPE_CHOICES = [
        ('new-customer', 'New Customer'),
        ('existing-customer', 'Existing Customer'),
    ]
    branch = forms.ModelChoiceField(queryset=Branch.objects.all(), required=True)
    service = forms.ModelChoiceField(queryset=Service.objects.all(), required=True)
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True)
    time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=True)
    customer_type = forms.ChoiceField(choices=CUSTOMER_TYPE_CHOICES, required=True)

    class Meta:
        model = Booking
        fields = ['name', 'email', 'branch', 'service', 'date', 'time', 'customer_type']

    def clean(self):
        cleaned_data = super().clean()
        branch = cleaned_data.get("branch")
        service = cleaned_data.get("service")
        date = cleaned_data.get("date")
        time = cleaned_data.get("time")

        if branch and service and date and time:
            # Check if there is a recent booking within 6 minutes
            booking_datetime = timezone.make_aware(
                datetime.combine(date, time)
            )
            time_limit = booking_datetime - timedelta(minutes=6)

            recent_booking = Booking.objects.filter(
                branch=branch,
                service=service,
                date=date,
                time__gte=time_limit,
                time__lt=booking_datetime
            ).exists()

            if recent_booking:
                raise forms.ValidationError(
                    "This time slot is too close to another booking. Please choose a time at least 6 minutes later."
                )
        
        return cleaned_data
