"""
Budget Utilities
=================
Helper functions for budget-related features,
including sending email notifications.
"""
from django.core.mail import send_mail
from django.conf import settings


def send_budget_alert(user, budget, usage_percent):
    """
    Send an email to the user when they're approaching or exceeding their budget.
    In development, this prints to the console instead of sending a real email.
    """
    subject = f"⚠️ Budget Alert: {budget.category.name}"

    if usage_percent >= 100:
        message = (
            f"Hi {user.first_name or user.username},\n\n"
            f"You have EXCEEDED your budget for '{budget.category.name}'!\n\n"
            f"Budget: {budget.currency} {budget.amount}\n"
            f"Spent: {budget.currency} {budget.spent_amount:.2f}\n"
            f"Over by: {budget.currency} {abs(budget.remaining_amount):.2f}\n\n"
            f"Consider reviewing your spending or increasing your budget.\n\n"
            f"— Finance Tracker"
        )
    else:
        message = (
            f"Hi {user.first_name or user.username},\n\n"
            f"You've used {usage_percent:.0f}% of your '{budget.category.name}' budget.\n\n"
            f"Budget: {budget.currency} {budget.amount}\n"
            f"Spent: {budget.currency} {budget.spent_amount:.2f}\n"
            f"Remaining: {budget.currency} {budget.remaining_amount:.2f}\n\n"
            f"— Finance Tracker"
        )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,  # Don't crash the app if email fails
        )
    except Exception as e:
        print(f"Email error: {e}")  # Log but don't crash
