"""
Transactions Models
====================
These are the core models of our app.

Category: Groups transactions (e.g. "Food", "Salary", "Rent")
Transaction: A single income or expense event
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class Category(models.Model):
    """
    A category groups related transactions.
    Examples: "Groceries", "Salary", "Netflix", "Freelance"
    """
    TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,  # Delete categories when user is deleted
        related_name='categories'
    )
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    icon = models.CharField(
        max_length=50,
        blank=True,
        default='💰',
        help_text="An emoji to represent this category"
    )
    color = models.CharField(
        max_length=7,
        default='#4CAF50',
        help_text="Hex color for charts (e.g. #FF5733)"
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.icon} {self.name} ({self.type})"

    class Meta:
        verbose_name_plural = "Categories"
        # Each user can only have one category with a given name+type combo
        unique_together = ['user', 'name', 'type']
        ordering = ['type', 'name']

    def delete(self, *args, **kwargs):
        """
        EDGE CASE: When deleting a category that has existing transactions,
        we set those transactions' category to None (null) rather than
        deleting the transactions themselves.
        This is handled by on_delete=models.SET_NULL in Transaction.
        """
        super().delete(*args, **kwargs)


class Transaction(models.Model):
    """
    A single financial event — either income or expense.

    Key design decisions:
    - Amount is stored as a positive Decimal (never negative in DB)
    - Type field tells us if it's income or expense
    - For refunds: we store them as negative expenses using the 'is_refund' flag
    - Currency stored on each transaction (multi-currency support)
    """
    TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'USD - US Dollar'),
        ('EUR', 'EUR - Euro'),
        ('GBP', 'GBP - British Pound'),
        ('INR', 'INR - Indian Rupee'),
        ('JPY', 'JPY - Japanese Yen'),
        ('CAD', 'CAD - Canadian Dollar'),
        ('AUD', 'AUD - Australian Dollar'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')

    # Category can be null (if the category gets deleted, transaction stays with null category)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,  # EDGE CASE: Don't delete transactions when category deleted
        null=True,
        blank=True,
        related_name='transactions'
    )

    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    # EDGE CASE: Decimal precision — use DecimalField, NEVER FloatField for money!
    # max_digits=12 allows up to 999,999,999.99
    # decimal_places=2 for cents
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]  # Minimum 1 cent
    )

    # EDGE CASE: Refunds — expense that gives money back
    is_refund = models.BooleanField(
        default=False,
        help_text="If True, this is a refund (negative expense)"
    )

    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')

    # Amount converted to user's preferred currency (updated when transaction is saved)
    amount_in_preferred_currency = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    date = models.DateField()
    description = models.CharField(max_length=255)
    notes = models.TextField(blank=True)

    # Receipt image upload
    receipt = models.ImageField(
        upload_to='receipts/%Y/%m/',  # Organized by year/month
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        sign = '-' if self.is_refund else '+'
        return f"{self.date} | {self.type} | {sign}{self.currency} {self.amount} | {self.description}"

    @property
    def effective_amount(self):
        """
        Returns the actual amount considering refunds.
        Refunds are stored as positive numbers but should be treated as negative expenses.
        """
        if self.is_refund:
            return -self.amount
        return self.amount

    @property
    def signed_amount(self):
        """
        For net calculations:
        - Income: positive
        - Expense: negative
        - Refund: positive (money coming back)
        """
        if self.type == 'income':
            return self.amount
        else:  # expense
            if self.is_refund:
                return self.amount   # Refund is positive (money back)
            return -self.amount      # Normal expense is negative

    class Meta:
        ordering = ['-date', '-created_at']
