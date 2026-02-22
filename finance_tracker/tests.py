"""
Tests for the Finance Tracker
================================
Run with: python manage.py test

These tests cover:
- User registration and authentication
- Transaction creation with edge cases
- Budget calculations
- Report logic
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from datetime import date

from transactions.models import Transaction, Category
from budgets.models import Budget


class UserAuthTests(TestCase):
    """Test user registration and login."""

    def setUp(self):
        """Create a test client and test user before each test."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_user_can_register(self):
        """Test that a new user can register successfully."""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'complexpass123',
            'password2': 'complexpass123',
        })
        self.assertEqual(User.objects.filter(username='newuser').count(), 1)

    def test_user_profile_created_automatically(self):
        """Test that UserProfile is auto-created via signal."""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsNotNone(self.user.profile)

    def test_user_can_login(self):
        """Test that a user can log in."""
        logged_in = self.client.login(username='testuser', password='testpass123')
        self.assertTrue(logged_in)

    def test_dashboard_requires_login(self):
        """Test that dashboard redirects unauthenticated users to login."""
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, '/accounts/login/?next=/dashboard/')


class CategoryTests(TestCase):
    """Test category creation and deletion."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.client = Client()
        self.client.login(username='testuser', password='pass')

    def test_create_income_category(self):
        """Test creating an income category."""
        category = Category.objects.create(
            user=self.user, name='Salary', type='income'
        )
        self.assertEqual(str(category.type), 'income')
        self.assertEqual(category.user, self.user)

    def test_delete_category_keeps_transactions(self):
        """
        EDGE CASE: When a category is deleted, transactions should NOT be deleted.
        Their category field should be set to NULL.
        """
        category = Category.objects.create(user=self.user, name='Food', type='expense')
        transaction = Transaction.objects.create(
            user=self.user,
            category=category,
            type='expense',
            amount=Decimal('50.00'),
            date=date.today(),
            description='Lunch',
            currency='USD'
        )

        # Delete the category
        category.delete()

        # Transaction should still exist, but category should be None
        transaction.refresh_from_db()
        self.assertIsNone(transaction.category)


class TransactionTests(TestCase):
    """Test transaction creation and edge cases."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.category = Category.objects.create(
            user=self.user, name='Groceries', type='expense'
        )

    def test_decimal_precision(self):
        """Test that decimal amounts are stored precisely."""
        transaction = Transaction.objects.create(
            user=self.user,
            category=self.category,
            type='expense',
            amount=Decimal('99.99'),  # Must use Decimal, not float!
            date=date.today(),
            description='Groceries',
            currency='USD'
        )
        self.assertEqual(transaction.amount, Decimal('99.99'))

    def test_refund_effective_amount(self):
        """EDGE CASE: Refund should have negative effective amount."""
        refund = Transaction.objects.create(
            user=self.user,
            category=self.category,
            type='expense',
            amount=Decimal('20.00'),
            is_refund=True,
            date=date.today(),
            description='Store refund',
            currency='USD'
        )
        # Effective amount of a refund should be negative (money coming back)
        self.assertEqual(refund.effective_amount, Decimal('-20.00'))

    def test_signed_amount_income(self):
        """Income should have positive signed amount."""
        income_cat = Category.objects.create(user=self.user, name='Salary', type='income')
        income = Transaction.objects.create(
            user=self.user, category=income_cat, type='income',
            amount=Decimal('1000.00'), date=date.today(),
            description='Salary', currency='USD'
        )
        self.assertEqual(income.signed_amount, Decimal('1000.00'))

    def test_signed_amount_expense(self):
        """Expense should have negative signed amount."""
        expense = Transaction.objects.create(
            user=self.user, category=self.category, type='expense',
            amount=Decimal('50.00'), date=date.today(),
            description='Lunch', currency='USD'
        )
        self.assertEqual(expense.signed_amount, Decimal('-50.00'))


class BudgetTests(TestCase):
    """Test budget creation and calculations."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.category = Category.objects.create(
            user=self.user, name='Food', type='expense'
        )
        self.budget = Budget.objects.create(
            user=self.user,
            category=self.category,
            amount=Decimal('500.00'),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            currency='USD'
        )

    def test_budget_spent_amount(self):
        """Test that spent amount is correctly calculated."""
        # Add a transaction in the budget period
        Transaction.objects.create(
            user=self.user, category=self.category, type='expense',
            amount=Decimal('100.00'), date=date(2026, 1, 15),
            description='Food', currency='USD'
        )
        self.assertEqual(self.budget.spent_amount, Decimal('100.00'))

    def test_budget_with_refund(self):
        """Test that refunds correctly reduce spending."""
        Transaction.objects.create(
            user=self.user, category=self.category, type='expense',
            amount=Decimal('100.00'), date=date(2026, 1, 15),
            description='Food', currency='USD'
        )
        Transaction.objects.create(
            user=self.user, category=self.category, type='expense',
            amount=Decimal('20.00'), date=date(2026, 1, 16),
            description='Food refund', currency='USD', is_refund=True
        )
        # Net spending: 100 - 20 = 80
        self.assertEqual(self.budget.spent_amount, Decimal('80.00'))

    def test_budget_usage_percentage(self):
        """Test usage percentage calculation."""
        Transaction.objects.create(
            user=self.user, category=self.category, type='expense',
            amount=Decimal('250.00'), date=date(2026, 1, 15),
            description='Food', currency='USD'
        )
        # 250 / 500 = 50%
        self.assertAlmostEqual(self.budget.usage_percentage, 50.0)

    def test_budget_exceeded(self):
        """Test budget exceeded detection."""
        Transaction.objects.create(
            user=self.user, category=self.category, type='expense',
            amount=Decimal('600.00'), date=date(2026, 1, 15),
            description='Food', currency='USD'
        )
        self.assertTrue(self.budget.is_exceeded)
