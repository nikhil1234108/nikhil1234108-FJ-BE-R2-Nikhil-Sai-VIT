"""
Reports Views
==============
Generate monthly, yearly, and custom reports of financial data.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from decimal import Decimal
from datetime import date
import json

from transactions.models import Transaction, Category


@login_required
def monthly_report(request):
    """
    Generate a monthly income vs expense report.
    User can select which month/year to view.
    """
    today = date.today()

    # Get month/year from query params, default to current month
    try:
        month = int(request.GET.get('month', today.month))
        year = int(request.GET.get('year', today.year))
    except ValueError:
        month, year = today.month, today.year

    # Validate ranges
    month = max(1, min(12, month))
    year = max(2000, min(today.year + 1, year))

    user = request.user

    # All transactions for the selected month
    transactions = Transaction.objects.filter(
        user=user,
        date__month=month,
        date__year=year
    ).select_related('category').order_by('date')

    # Income summary
    income_transactions = transactions.filter(type='income')
    total_income = income_transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Expense summary (handling refunds)
    expense_transactions = transactions.filter(type='expense')
    total_expenses = Decimal('0.00')
    for t in expense_transactions:
        total_expenses += t.effective_amount  # Uses effective_amount property (handles refunds)

    # Net savings
    net_savings = total_income - total_expenses
    savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0

    # Income by category
    income_by_cat = (
        income_transactions
        .values('category__name', 'category__icon')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    # Expenses by category
    expense_by_cat = {}
    for t in expense_transactions:
        cat_name = t.category.name if t.category else 'Uncategorized'
        cat_icon = t.category.icon if t.category else '❓'
        key = cat_name
        if key not in expense_by_cat:
            expense_by_cat[key] = {'name': cat_name, 'icon': cat_icon, 'total': Decimal('0.00')}
        expense_by_cat[key]['total'] += t.effective_amount

    expense_by_cat = sorted(expense_by_cat.values(), key=lambda x: x['total'], reverse=True)

    # Month names for the dropdown
    month_names = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]

    # Generate year list (last 5 years)
    years = list(range(today.year, today.year - 6, -1))

    context = {
        'month': month,
        'year': year,
        'selected_month_name': date(year, month, 1).strftime('%B %Y'),
        'transactions': transactions,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_savings': net_savings,
        'savings_rate': savings_rate,
        'income_by_cat': income_by_cat,
        'expense_by_cat': expense_by_cat,
        'month_names': month_names,
        'years': years,
        'income_transactions': income_transactions,
        'expense_transactions': expense_transactions,
    }
    return render(request, 'reports/monthly_report.html', context)


@login_required
def yearly_report(request):
    """
    Yearly summary: monthly breakdown of income vs expenses.
    """
    today = date.today()
    try:
        year = int(request.GET.get('year', today.year))
    except ValueError:
        year = today.year

    user = request.user
    monthly_data = []

    for month in range(1, 13):
        month_txns = Transaction.objects.filter(
            user=user, date__month=month, date__year=year
        )
        income = month_txns.filter(type='income').aggregate(
            total=Sum('amount'))['total'] or Decimal('0.00')

        expenses = sum(
            t.effective_amount for t in month_txns.filter(type='expense')
        )

        monthly_data.append({
            'month': date(year, month, 1).strftime('%b'),
            'income': float(income),
            'expense': float(max(expenses, 0)),
            'savings': float(income - max(expenses, 0)),
        })

    total_income = sum(m['income'] for m in monthly_data)
    total_expense = sum(m['expense'] for m in monthly_data)

    years = list(range(today.year, today.year - 6, -1))

    context = {
        'year': year,
        'monthly_data': monthly_data,
        'monthly_data_json': json.dumps(monthly_data),
        'total_income': total_income,
        'total_expense': total_expense,
        'net_savings': total_income - total_expense,
        'years': years,
    }
    return render(request, 'reports/yearly_report.html', context)
