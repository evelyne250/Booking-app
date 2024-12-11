# booking/views.py
import json
from django.http import JsonResponse
from django.shortcuts import render, redirect
import requests
from .forms import BookingForm
from django.db.models import Count
from .models import Booking, Branch, Service
from django.conf import settings
from django.db.models import Q

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
    branches = Branch.objects.values('id', 'name', 'location')
    return JsonResponse(list(branches), safe=False)

def fetch_services(request):
    services = Service.objects.values('id', 'name', 'description')
    return JsonResponse(list(services), safe=False)

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