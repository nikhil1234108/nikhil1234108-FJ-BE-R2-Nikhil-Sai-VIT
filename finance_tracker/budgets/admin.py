from django.contrib import admin
from .models import Budget

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'amount', 'currency', 'start_date', 'end_date']
    list_filter = ['currency', 'user']
