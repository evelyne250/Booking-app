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
from datetime import datetime, timedelta
import re
import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import datetime,timedelta
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.utils.timezone import localtime
from .Recommendation import recommend_options  
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def book_appointment(request):
    recommendations = None  # Initialize recommendations
    form = BookingForm()  # Initialize the form by default

    if request.method == 'POST':
        # Check if the request is for recommendations or booking
        if 'get_recommendations' in request.POST:
            # Step 1: Fetch recommendations
            service_name = request.POST.get('service')
            if service_name:
                # Retrieve the service object based on the submitted service name
                service = Service.objects.filter(name=service_name).first()
                if service:
                    # Fetch recommendations for the selected service
                    recommendations = recommend_options(service.name)
                    # Pre-fill the form with the selected service
                    form = BookingForm(initial={'service': service})
                    return render(request, 'booking/index.html', {'form': form, 'recommendations': recommendations})
        
        elif 'book_slot' in request.POST:
            # Step 2: Book the slot
            form = BookingForm(request.POST)
            if form.is_valid():
                booking = form.save(commit=False)

                # Retrieve the ServiceTime object for the selected service
                service_time = ServiceTime.objects.filter(service_name=booking.service.name).first()

                # Get the average time or default to 6 minutes
                if service_time and service_time.average_time:
                    average_time = service_time.average_time
                else:
                    average_time = timedelta(minutes=6)

                # Calculate the next available time
                last_booking = Booking.objects.filter(branch=booking.branch).order_by('-time').first()
                if last_booking:
                    # Convert last_booking.time (datetime.time) to a datetime object
                    last_booking_datetime = datetime.combine(booking.date, last_booking.time)
                    next_available_datetime = last_booking_datetime + average_time

                    # Check if the selected time is too close to the last booking
                    selected_datetime = datetime.combine(booking.date, booking.time)
                    if selected_datetime < next_available_datetime:
                        # Adjust the booking time to the next available time
                        booking.time = next_available_datetime.time()
                        messages.warning(
                            request,
                            f"The selected time was too close to another booking. "
                            f"Your service has been booked at {next_available_datetime.strftime('%I:%M %p')} instead."
                        )
                    else:
                        messages.success(
                            request,
                            f"Your service has been booked at {selected_datetime.strftime('%I:%M %p')}."
                        )
                else:
                    # If no previous bookings, use the selected time
                    messages.success(
                        request,
                        f"Your service has been booked at {booking.time.strftime('%I:%M %p')}."
                    )

                booking.save()
                # Render the index.html page with the messages
                return render(request, 'booking/index.html', {'form': BookingForm(), 'recommendations': None})

    # Render the form and recommendations (if any) for GET requests or unhandled POST requests
    return render(request, 'booking/index.html', {'form': form, 'recommendations': recommendations})

@csrf_exempt
def get_recommendations(request):
    if request.method == 'POST':
        service_id = request.POST.get('service')  # Get the service ID
        print(f"Service ID: {service_id}")  # Debug statement
        if service_id:
            # Retrieve the service object based on the ID
            service = Service.objects.filter(id=service_id).first()
            if service:
                # Use the service name for recommendations
                recommendations = recommend_options(service.name)
                return JsonResponse({'recommendations': recommendations}, status=200)
            else:
                print("Service not found.")  # Debug statement
                return JsonResponse({'error': 'Service not found.'}, status=404)
        else:
            print("Service ID is missing.")  # Debug statement
            return JsonResponse({'error': 'Service ID is missing.'}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def confirm(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            form_data = {
                'full_name': data.get('full_name'),
                'email': data.get('email'),
                'phone_number': data.get('phone_number'),
                'account_number': data.get('account_number', ''),
                'branch': data.get('branch'),
                'manual_branch': data.get('manual_branch', ''),
                'service': data.get('service'),
                'date': data.get('date'),
                'time': data.get('time'),
                'customer_type': data.get('customer_type'),
                'business_name': data.get('business_name', ''),
                'user_type': data.get('user_type')
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
    
@login_required
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


def custom_login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            full_name = form.cleaned_data['full_name']
            account_number = form.cleaned_data['account_number']
            phone_number = form.cleaned_data['phone_number']

            # Authenticate using the custom backend
            user = authenticate(
                request,
                full_name=full_name,
                account_number=account_number,
                phone_number=phone_number
            )
            if user is not None:
                login(request, user)
                return redirect('dashboard')  # Redirect to dashboard or any other page
            else:
                form.add_error(None, "Invalid credentials. Please try again.")
    else:
        form = CustomLoginForm()

    return render(request, 'custom_login.html', {'form': form})


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