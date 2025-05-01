# booking/forms.py
from django import forms
from django.utils import timezone
from datetime import datetime, timedelta
from .models import *
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.timezone import make_aware
class CustomLoginForm(forms.Form):
    full_name = forms.CharField(max_length=200, required=True, label="Full Name")
    account_number = forms.CharField(max_length=50, required=True, label="Account Number")
    phone_number = forms.CharField(max_length=15, required=True, label="Phone Number")

class CustomerUploadForm(forms.Form):
    file = forms.FileField(label="Upload CSV File")

class BookingForm(forms.ModelForm):
    CUSTOMER_TYPE_CHOICES = [
        ('new-customer', 'New Customer'),
        ('existing-customer', 'Existing Customer'),
    ]

    USER_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('business', 'Business'),
    ]
    branch = forms.ModelChoiceField(queryset=Branch.objects.all(), required=False)
    manual_branch = forms.CharField(
        max_length=100, 
        required=False,
        label='Branch Name/Location'
    )
    
    service = forms.ModelChoiceField(queryset=Service.objects.all(), required=True)
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True)
    time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=True)
    customer_type = forms.ChoiceField(choices=CUSTOMER_TYPE_CHOICES, required=True)
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES, 
        required=True,
    )
    business_name = forms.CharField(
        max_length=100, 
        required=False, 
        label='Business Name'
    )

    class Meta:
        model = Booking
        fields = [ 'user_type',
            'full_name',
            'account_number',
            'phone_number',
            'branch',
            'service',
            'date',
            'time',
            'customer_type',
            'business_name',]

    def clean(self):
        cleaned_data = super().clean()
        branch = cleaned_data.get("branch")
        manual_branch = cleaned_data.get("manual_branch")
        service = cleaned_data.get("service")
        date = cleaned_data.get("date")
        time = cleaned_data.get("time")
        user_type = cleaned_data.get("user_type")
        business_name = cleaned_data.get("business_name")

        if not branch and not manual_branch:
            raise forms.ValidationError("Please select a branch or enter a branch name.")
        
        if branch and manual_branch:
            cleaned_data['branch'] = None

        if user_type == 'business':
            if not business_name:
                self.add_error('business_name', 'Business name is required for business bookings')
            else:
                cleaned_data['business_name'] = ''

        if (branch or manual_branch) and service and date and time:
            # Check if there is a recent booking within 6 minutes
            booking_datetime = make_aware(
                datetime.combine(date, time)
            )
            time_limit = booking_datetime - timedelta(minutes=6)

            recent_booking = Booking.objects.filter(
                Q(branch=branch) | Q(manual_branch=manual_branch),
                service=service,
                date=date,
                time__gte=time_limit,
                time__lt=booking_datetime
            ).exists()

            if recent_booking:
                # Instead of raising a ValidationError, adjust the time in the view
                cleaned_data['adjusted_time'] = True  # Add a flag to indicate adjustment
                cleaned_data['adjusted_booking_datetime'] = booking_datetime + timedelta(minutes=6)

        return cleaned_data
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # If no database branch is selected but manual branch is provided
        if not instance.branch and self.cleaned_data.get('manual_branch'):
            if self.cleaned_data.get('manual_branch'):
                temp_branch, created = Branch.objects.get_or_create(
                name=self.cleaned_data['manual_branch'],
                defaults={'location': 'Unknown'}
            )
            instance.branch = temp_branch
            instance.manual_branch = self.cleaned_data['manual_branch']
        
        if commit:
            instance.save()
        return instance


class CustomerSearchForm(forms.Form):
    customer_no = forms.CharField(label='Customer Number', max_length=100)


class CustomerUpdateForm(forms.ModelForm):
    proof_document = forms.FileField(required=False)  # Optional file upload

    class Meta:
        model = Customer
        fields = ['given_names', 'family_name', 'email_1', 'sms_1', 'proof_document']