from celery import shared_task
from .models import TimeSlot

@shared_task
def adjust_slot_availability():
    time_slots = TimeSlot.objects.all()
    for slot in time_slots:
        if slot.bookings / slot.capacity > 0.8:  # High-demand threshold
            slot.capacity = max(slot.capacity - 1, 1)  # Prevent zero capacity
        elif slot.bookings / slot.capacity < 0.5:  # Low-demand threshold
            slot.capacity += 1
        slot.save()
    return f"Adjusted {time_slots.count()} slots."
