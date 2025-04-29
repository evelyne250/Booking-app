# booking/views.py
from django.contrib.auth.decorators import user_passes_test
import json
from django.http import JsonResponse
from django.shortcuts import render, redirect
import requests
from .forms import *
from django.db.models import Count
from .models import *
from django.conf import settings
from django.db.models import Q
from datetime import timedelta
import re
import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import datetime

def book_appointment(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('confirm')
    else:
        form = BookingForm()
    return render(request, 'booking/index.html', {'form': form})

def confirm(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            form_data = {
                'name': data.get('name'),
                'email': data.get('email'),
                'branch': data.get('branch'),
                'manual_branch': data.get('manual_branch', ''),
                'service': data.get('service'),
                'date': data.get('date'),
                'time': data.get('time'),
                'customer_type': data.get('customer_type')
            }
            
            form = BookingForm(form_data)
            
            if form.is_valid():
                booking = form.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Booking confirmed',
                    'booking_id': booking.id
                }, status=200)
            else:
                return JsonResponse({
                    'status': 'error',
                    'errors': form.errors
                }, status=400)
        
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error', 
                'message': 'Invalid JSON'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': str(e)
            }, status=500)
    return render(request, 'booking/confirm.html')

def home(request):
    return render(request, 'booking/home.html')

def fetch_branches(request):
    user_type = request.GET.get('user_type', 'individual')
    
    if user_type == 'individual':
        branches = Branch.objects.filter(is_for_individual=True)
    else:
        branches = Branch.objects.filter(is_for_business=True)
    
    return JsonResponse([
        {
            'id': branch.id, 
            'name': branch.name, 
            'location': branch.location
        } for branch in branches
    ], safe=False)


def fetch_services(request):
    user_type = request.GET.get('user_type', 'individual')
    
    if user_type == 'individual':
        services = Service.objects.filter(is_for_individual=True)
    else:
        services = Service.objects.filter(is_for_business=True)
    
    return JsonResponse([
        {
            'id': service.id, 
            'name': service.name, 
            'description': service.description
        } for service in services
    ], safe=False)

def dashboard(request):
    # Count bookings by branch
    bookings_by_branch = Booking.objects.values('branch__name').annotate(count=Count('id'))
    branch_names = [item['branch__name'] for item in bookings_by_branch]
    branch_counts = [item['count'] for item in bookings_by_branch]
    
    # Count bookings by service
    bookings_by_service = Booking.objects.values('service__name').annotate(count=Count('id'))
    service_names = [item['service__name'] for item in bookings_by_service]
    service_counts = [item['count'] for item in bookings_by_service]

    # Fetch recent bookings
    recent_bookings = Booking.objects.order_by('-date', '-time')[:10]

    context = {
        'branch_names': branch_names,
        'branch_counts': branch_counts,
        'service_names': service_names,
        'service_counts': service_counts,
        'recent_bookings': recent_bookings
    }

    return render(request, 'booking/dashboard.html', context)

def dashboard_view(request):
    total_bookings = Booking.objects.count()  # Counts all booking records
    
    # Pass total_bookings to your template context
    return render(request, 'booking/dashboard.html', {'total_bookings': total_bookings})

def fetch_nearby_banks(request):
    latitude = request.GET.get('latitude')
    longitude = request.GET.get('longitude')

    if not latitude or not longitude:
        return JsonResponse({
       
            'status': 'error',
            'message': 'Latitude and longitude are required'
        }, status=400)
    
    branches = Branch.objects.filter(
        Q(name__icontains='Bank of Kigali') | 
        Q(name__icontains='BK')
    )

    nearest_branch = None
    min_distance = float('inf')
    user_location = (float(latitude), float(longitude))
        
    try:
        api_key = settings.GOOGLE_API_KEY
        url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
        
        params = {
            'location': f'{latitude},{longitude}',
            'radius': 5000,
            'type': 'bank',
            'keyword': 'Bank of Kigali',
            'key': api_key
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        # Filter and process results
        results = data.get('results', [])
        processed_results = []
        
        for result in results:
            processed_results.append({
                'name': result.get('name'),
                'vicinity': result.get('vicinity'),
                'place_id': result.get('place_id'),
                'rating': result.get('rating'),
                'total_ratings': result.get('user_ratings_total')
            })
        
        return JsonResponse({
            'status': 'success',
            'results': processed_results
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def search_branches(request):
    search_term = request.GET.get('q', '').strip()  # Get 'q' parameter from request
    if search_term:
        branches = Branch.objects.filter(name__icontains=search_term)
    else:
        branches = Branch.objects.all()  # Return all branches if no search term provided

    results = [
        {'id': branch.id, 'name': branch.name, 'location': branch.location}
        for branch in branches
    ]
    return JsonResponse({'status': 'success', 'results': results})


    def adjust_slot_availability():
        time_slots = TimeSlot.objects.all()
        for slot in time_slots:
            if slot.bookings / slot.capacity > 0.8:  # High-demand threshold
                slot.capacity -= 1  # Reduce availability
            elif slot.bookings / slot.capacity < 0.5:  # Low-demand threshold
                slot.capacity += 1  # Increase availability
            slot.save()


def book_service(user, service, start_time):
    # Get average duration from the service
    service_duration = service.average_duration

    # Calculate the end time
    end_time = start_time + service_duration

    # Prevent overlapping with other bookings for the same user
    overlapping = Booking.objects.filter(
        user=user,
        start_time__lt=end_time,
        end_time__gt=start_time
    )

    if overlapping.exists():
        raise Exception("You have another booking that overlaps with this time slot.")

    # Save booking
    Booking.objects.create(
        user=user,
        service=service,
        start_time=start_time,
        end_time=end_time
    )

    def parse_duration(time_string):
        minutes = int(re.search(r'(\d+)\s*min', time_string).group(1))
        seconds = int(re.search(r'(\d+)\s*sec', time_string).group(1))
        return timedelta(minutes=minutes, seconds=seconds)

# Function to check if user is admin/staff
def is_admin(user):
    return user.is_staff  # or you can use user.is_superuser if you want even stricter

@user_passes_test(is_admin)


def upload_customers_csv(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']

        # Check if uploaded file is a CSV
        if not file.name.endswith('.csv'):
            messages.error(request, 'Please upload a CSV file.')
            return redirect('upload_customers')

        # Decode the uploaded file
        data = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(data)

        for row in reader:
            # Extract values safely
            customer_no = row.get('CUSTOMER_NO', '').strip()
            given_names = row.get('GIVEN_NAMES', '').strip()
            family_name = row.get('FAMILY_NAME', '').strip()
            email_1 = row.get('EMAIL_1', '').strip()
            sms_1 = row.get('SMS_1', '').strip()
            legal_id = row.get('LEGAL_ID', '').strip()
            date_of_birth_str = row.get('DATE_OF_BIRTH', '').strip()
         
            # Parse date fields carefully
            date_of_birth = None
            if date_of_birth_str:
                try:
                    date_of_birth = datetime.strptime(date_of_birth_str, '%d/%m/%Y').date()
                except ValueError:
                    pass  # Ignore bad date formats

          

            # Create or update customer
            if customer_no:
                Customer.objects.update_or_create(
                    customer_no=customer_no,
                    defaults={
                        'given_names': given_names,
                        'family_name': family_name,
                        'email_1': email_1,
                        'sms_1': sms_1,
                        'legal_id': legal_id,
                        'date_of_birth': date_of_birth,
                       
                    }
                )

        messages.success(request, 'Customers uploaded successfully.')
        return redirect('upload_customers')  # Replace with the page you want

    return render(request, 'upload_customers.html')


def search_customer(request):
    if request.method == 'POST':
        form = CustomerSearchForm(request.POST)
        if form.is_valid():
            customer_no = form.cleaned_data['customer_no']
            try:
                customer = Customer.objects.get(customer_no=customer_no)
                return redirect('update_customer', pk=customer.pk)
            except Customer.DoesNotExist:
                return render(request, 'search_customer.html', {'form': form, 'error': 'Customer not found'})
    else:
        form = CustomerSearchForm()
    return render(request, 'search_customer.html', {'form': form})

def update_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerUpdateForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('success_page')  # Redirect to a success page
    else:
        form = CustomerUpdateForm(instance=customer)
    return render(request, 'update_customer.html', {'form': form})