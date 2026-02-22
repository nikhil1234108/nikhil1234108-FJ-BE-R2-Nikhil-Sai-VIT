"""
Dashboard Views — Fixed
Bugs fixed:
1. Month/year calculation for 6-month chart was wrong (now uses relativedelta)
2. net_worth uses DB aggregation instead of Python loop
3. Safe profile access for Google OAuth users
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from decimal import Decimal
from datetime import date
import json

from transactions.models import Transaction
from budgets.models import Budget


def _months_ago(today, n):
    """Return (month, year) for n months before today. Handles year boundaries."""
    month = today.month - n
    year = today.year
    while month <= 0:
        month += 12
        year -= 1
    return month, year


def _get_currency(user):
    try:
        return user.profile.preferred_currency
    except Exception:
        return 'USD'


@login_required
def dashboard(request):
    today = date.today()
    user = request.user
    currency = _get_currency(user)

    # This month's stats
    monthly_qs = Transaction.objects.filter(
        user=user, date__month=today.month, date__year=today.year
    )

    monthly_income = monthly_qs.filter(
        type='income'
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0.00')

    monthly_expenses = Decimal('0.00')
    for t in monthly_qs.filter(type='expense'):
        monthly_expenses += t.effective_amount
    monthly_expenses = max(monthly_expenses, Decimal('0.00'))
    monthly_savings = monthly_income - monthly_expenses

    # All-time net worth via DB aggregation
    total_income = Transaction.objects.filter(
        user=user, type='income'
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0.00')
    total_expense = Transaction.objects.filter(
        user=user, type='expense', is_refund=False
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0.00')
    total_refunds = Transaction.objects.filter(
        user=user, type='expense', is_refund=True
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0.00')
    net_worth = total_income - total_expense + total_refunds

    # Pie chart — expenses by category this month
    exp_by_cat = (
        monthly_qs.filter(type='expense', is_refund=False)
        .values('category__name', 'category__color')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    chart_labels = [x['category__name'] or 'Uncategorized' for x in exp_by_cat]
    chart_values = [float(x['total']) for x in exp_by_cat]
    chart_colors = [x['category__color'] or '#6c757d' for x in exp_by_cat]

    # Last 6 months bar chart — FIXED using helper
    monthly_data = []
    for i in range(5, -1, -1):
        m, y = _months_ago(today, i)
        inc = Transaction.objects.filter(
            user=user, type='income', date__month=m, date__year=y
        ).aggregate(t=Sum('amount'))['t'] or 0
        exp = Transaction.objects.filter(
            user=user, type='expense', is_refund=False, date__month=m, date__year=y
        ).aggregate(t=Sum('amount'))['t'] or 0
        ref = Transaction.objects.filter(
            user=user, type='expense', is_refund=True, date__month=m, date__year=y
        ).aggregate(t=Sum('amount'))['t'] or 0
        monthly_data.append({
            'month': date(y, m, 1).strftime('%b %Y'),
            'income': float(inc),
            'expense': float(max(float(exp) - float(ref), 0)),
        })

    active_budgets = Budget.objects.filter(
        user=user, start_date__lte=today, end_date__gte=today
    ).select_related('category')[:5]

    recent_transactions = Transaction.objects.filter(
        user=user
    ).select_related('category').order_by('-date', '-created_at')[:8]

    context = {
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'monthly_savings': monthly_savings,
        'net_worth': net_worth,
        'currency': currency,
        'recent_transactions': recent_transactions,
        'active_budgets': active_budgets,
        'total_transactions': Transaction.objects.filter(user=user).count(),
        'chart_labels': json.dumps(chart_labels),
        'chart_values': json.dumps(chart_values),
        'chart_colors': json.dumps(chart_colors),
        'monthly_chart_data': json.dumps(monthly_data),
        'current_month_name': today.strftime('%B %Y'),
    }
    return render(request, 'dashboard/dashboard.html', context)
