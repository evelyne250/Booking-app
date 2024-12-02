# booking/views.py
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .forms import BookingForm
from django.db.models import Count
from .models import Booking, Branch, Service

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