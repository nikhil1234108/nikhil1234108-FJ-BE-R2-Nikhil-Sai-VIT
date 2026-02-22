from django.contrib import admin
from .models import Category, Transaction

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'user', 'icon', 'created_at']
    list_filter = ['type', 'user']
    search_fields = ['name', 'user__username']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['date', 'user', 'type', 'amount', 'currency', 'category', 'description', 'is_refund']
    list_filter = ['type', 'currency', 'is_refund', 'date']
    search_fields = ['description', 'user__username']
    date_hierarchy = 'date'
