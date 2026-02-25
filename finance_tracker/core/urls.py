"""
Main URL Configuration
=======================
This file wires together all the different apps' URLs.
Think of it as the "table of contents" of your website.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django admin panel — go to /admin/ to manage all data
    path('admin/', admin.site.urls),

    # Accounts: login, register, profile
    path('accounts/', include('accounts.urls')),

    # Google OAuth (allauth handles all the OAuth flow automatically)
    path('accounts/', include('allauth.urls')),

    # Main features
    path('dashboard/', include('dashboard.urls')),
    path('transactions/', include('transactions.urls')),
    path('budgets/', include('budgets.urls')),
    path('reports/', include('reports.urls')),

    # Redirect root URL to dashboard
    path('', include('dashboard.urls')),
]

# Serve media files (uploaded receipts) during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
