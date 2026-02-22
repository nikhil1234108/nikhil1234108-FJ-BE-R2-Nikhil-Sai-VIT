"""
Accounts Models
================
We extend Django's built-in User model with a UserProfile model
to store extra info like preferred currency.

Django's User already has: username, email, password, first_name, last_name
We add: preferred_currency, profile_picture, phone_number
"""
from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    One-to-one extension of the built-in User model.
    Every User automatically gets a UserProfile via the signal in apps.py.
    """
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar ($)'),
        ('EUR', 'Euro (€)'),
        ('GBP', 'British Pound (£)'),
        ('INR', 'Indian Rupee (₹)'),
        ('JPY', 'Japanese Yen (¥)'),
        ('CAD', 'Canadian Dollar (CA$)'),
        ('AUD', 'Australian Dollar (A$)'),
    ]

    # Link to Django's built-in User — if User is deleted, profile is also deleted
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    preferred_currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='USD',
        help_text="Your default currency for transactions and reports"
    )
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        null=True,
        blank=True
    )
    phone_number = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)

    # Notification preferences
    budget_alert_email = models.BooleanField(
        default=True,
        help_text="Receive email when you exceed a budget"
    )
    budget_alert_threshold = models.IntegerField(
        default=80,
        help_text="Send alert when budget usage reaches this % (e.g. 80 means 80%)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
