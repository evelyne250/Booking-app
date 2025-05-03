from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from booking.models import Booking  # Assuming Booking contains full_name, account_number, and phone_number

class CustomAuthBackend(BaseBackend):
    def authenticate(self, request, full_name=None, account_number=None, phone_number=None, **kwargs):
        try:
            # Authenticate using Booking model
            booking = Booking.objects.get(
                full_name=full_name,
                account_number=account_number,
                phone_number=phone_number
            )
            # If a match is found, return a User object (or create one if needed)
            user, created = User.objects.get_or_create(username=booking.full_name)
            return user
        except Booking.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None