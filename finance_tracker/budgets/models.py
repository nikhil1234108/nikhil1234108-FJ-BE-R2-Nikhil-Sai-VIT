"""
Budget Models
==============
Budgets allow users to set spending limits for categories.
e.g. "I want to spend max $500 on Food this month"
"""

from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class Budget(models.Model):
    """
    A budget goal for a specific expense category over a date range.
    """

    # ✅ Currency choices added
    CURRENCY_CHOICES = [
        ('USD', 'USD'),
        ('INR', 'INR'),
        ('EUR', 'EUR'),
        ('GBP', 'GBP'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='budgets'
    )

    category = models.ForeignKey(
        'transactions.Category',
        on_delete=models.CASCADE,
        related_name='budgets',
        limit_choices_to={'type': 'expense'}  # Only expense categories
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Maximum amount you want to spend"
    )

    # ✅ FIXED: Added choices here
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='USD'
    )

    # Budget period
    start_date = models.DateField()
    end_date = models.DateField()

    name = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g. 'Monthly Groceries Budget'"
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name or self.category.name} Budget: {self.currency} {self.amount}"

    # ─────────────────────────────────────────────
    # Calculations
    # ─────────────────────────────────────────────

    @property
    def spent_amount(self):
        """
        Calculate total expenses in this category during the budget period.
        Subtract refunds from total.
        """
        from transactions.models import Transaction

        transactions = Transaction.objects.filter(
            user=self.user,
            category=self.category,
            type='expense',
            date__range=[self.start_date, self.end_date]
        )

        total = Decimal('0.00')

        for t in transactions:
            if t.is_refund:
                total -= t.amount
            else:
                total += t.amount

        return max(total, Decimal('0.00'))

    @property
    def remaining_amount(self):
        """How much budget is left."""
        return self.amount - self.spent_amount

    @property
    def usage_percentage(self):
        """What % of the budget has been used."""
        if self.amount == 0:
            return 0
        return float((self.spent_amount / self.amount) * 100)

    @property
    def is_exceeded(self):
        """True if budget exceeded."""
        return self.spent_amount > self.amount

    @property
    def status(self):
        """Human-readable status."""
        pct = self.usage_percentage
        if pct >= 100:
            return 'exceeded'
        elif pct >= 80:
            return 'warning'
        else:
            return 'good'

    class Meta:
        ordering = ['-start_date']