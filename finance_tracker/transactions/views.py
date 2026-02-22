"""
Transaction Views
==================
Full CRUD (Create, Read, Update, Delete) for categories and transactions.
All views require login — we use @login_required decorator.
"""
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.conf import settings

from .models import Transaction, Category
from .forms import TransactionForm, CategoryForm, TransactionFilterForm


# ────────────────────────────────────────
# HELPER: Currency conversion
# ────────────────────────────────────────

def convert_currency(amount, from_currency, to_currency):
    """
    Convert amount from one currency to another using live exchange rates.
    Falls back to returning the original amount if API fails.
    """
    if from_currency == to_currency:
        return amount

    try:
        api_key = settings.EXCHANGE_RATE_API_KEY
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/pair/{from_currency}/{to_currency}/{amount}"
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get('result') == 'success':
            return round(data['conversion_result'], 2)
    except Exception:
        pass  # If API fails, return original amount

    return amount  # Fallback


# ────────────────────────────────────────
# CATEGORY VIEWS
# ────────────────────────────────────────

@login_required
def category_list(request):
    """Show all categories for the logged-in user."""
    income_cats = Category.objects.filter(user=request.user, type='income')
    expense_cats = Category.objects.filter(user=request.user, type='expense')
    return render(request, 'transactions/category_list.html', {
        'income_categories': income_cats,
        'expense_categories': expense_cats,
    })


@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user  # Assign to current user
            category.save()
            messages.success(request, f'Category "{category.name}" created!')
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'transactions/category_form.html', {'form': form, 'action': 'Create'})


@login_required
def category_edit(request, pk):
    # get_object_or_404 returns 404 if not found (prevents errors)
    # We also ensure the category belongs to the current user (security!)
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{category.name}" updated!')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'transactions/category_form.html', {'form': form, 'action': 'Edit'})


@login_required
def category_delete(request, pk):
    """
    EDGE CASE: Deleting a category with existing transactions.
    We show a warning and let the user confirm.
    The Transaction model uses on_delete=SET_NULL, so transactions
    won't be deleted — they just lose their category reference.
    """
    category = get_object_or_404(Category, pk=pk, user=request.user)
    transaction_count = category.transactions.count()

    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.warning(
            request,
            f'Category "{name}" deleted. '
            f'{transaction_count} transaction(s) now have no category.'
        )
        return redirect('category_list')

    return render(request, 'transactions/category_confirm_delete.html', {
        'category': category,
        'transaction_count': transaction_count,
    })


# ────────────────────────────────────────
# TRANSACTION VIEWS
# ────────────────────────────────────────

@login_required
def transaction_list(request):
    """
    List all transactions with filtering support.
    """
    transactions = Transaction.objects.filter(user=request.user).select_related('category')
    filter_form = TransactionFilterForm(request.user, request.GET)

    if filter_form.is_valid():
        data = filter_form.cleaned_data

        if data.get('type'):
            transactions = transactions.filter(type=data['type'])
        if data.get('category'):
            transactions = transactions.filter(category=data['category'])
        if data.get('month'):
            transactions = transactions.filter(date__month=data['month'])
        if data.get('year'):
            transactions = transactions.filter(date__year=data['year'])
        if data.get('min_amount'):
            transactions = transactions.filter(amount__gte=data['min_amount'])
        if data.get('max_amount'):
            transactions = transactions.filter(amount__lte=data['max_amount'])

    return render(request, 'transactions/transaction_list.html', {
        'transactions': transactions,
        'filter_form': filter_form,
        'total_count': transactions.count(),
    })


@login_required
def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.user, request.POST, request.FILES)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user

            # Convert to user's preferred currency and store it
            preferred_currency = request.user.profile.preferred_currency
            transaction.amount_in_preferred_currency = convert_currency(
                transaction.amount,
                transaction.currency,
                preferred_currency
            )
            transaction.save()

            # Check if this transaction causes a budget overrun
            _check_budget_alert(request, transaction)

            messages.success(request, 'Transaction added successfully!')
            return redirect('transaction_list')
    else:
        form = TransactionForm(request.user)

    return render(request, 'transactions/transaction_form.html', {
        'form': form,
        'action': 'Add'
    })


@login_required
def transaction_edit(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.user, request.POST, request.FILES, instance=transaction)
        if form.is_valid():
            transaction = form.save(commit=False)
            # Update converted amount
            preferred_currency = request.user.profile.preferred_currency
            transaction.amount_in_preferred_currency = convert_currency(
                transaction.amount, transaction.currency, preferred_currency
            )
            transaction.save()
            messages.success(request, 'Transaction updated!')
            return redirect('transaction_list')
    else:
        form = TransactionForm(request.user, instance=transaction)

    return render(request, 'transactions/transaction_form.html', {
        'form': form,
        'action': 'Edit',
        'transaction': transaction
    })


@login_required
def transaction_delete(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Transaction deleted.')
        return redirect('transaction_list')
    return render(request, 'transactions/transaction_confirm_delete.html', {
        'transaction': transaction
    })


@login_required
def transaction_detail(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    return render(request, 'transactions/transaction_detail.html', {'transaction': transaction})


# ────────────────────────────────────────
# HELPER: Budget alert check
# ────────────────────────────────────────

def _check_budget_alert(request, transaction):
    """
    After adding an expense transaction, check if any budget for its
    category has been exceeded and send an email alert if so.
    """
    from budgets.models import Budget
    from budgets.utils import send_budget_alert

    if transaction.type != 'expense' or not transaction.category:
        return

    from django.db.models import Sum
    from datetime import date

    today = date.today()
    budgets = Budget.objects.filter(
        user=request.user,
        category=transaction.category,
        start_date__lte=today,
        end_date__gte=today,
    )

    for budget in budgets:
        usage_percent = budget.usage_percentage
        threshold = request.user.profile.budget_alert_threshold

        if usage_percent >= threshold:
            # Show alert on screen
            messages.warning(
                request,
                f'⚠️ Budget alert: You have used {usage_percent:.0f}% of your '
                f'"{budget.category.name}" budget!'
            )
            # Send email if user wants it
            if request.user.profile.budget_alert_email:
                send_budget_alert(request.user, budget, usage_percent)
