from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django import forms
from .models import Budget
from transactions.models import Category

CSS = 'form-select'
INPUT = 'form-control'

class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['name', 'category', 'amount', 'currency', 'start_date', 'end_date', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT, 'placeholder': 'e.g. Monthly Groceries'}),
            'category': forms.Select(attrs={'class': CSS}),
            'amount': forms.NumberInput(attrs={'class': INPUT, 'step': '0.01', 'placeholder': '0.00'}),
            'currency': forms.Select(attrs={'class': CSS}),
            'start_date': forms.DateInput(attrs={'class': INPUT, 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': INPUT, 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': INPUT, 'rows': 2}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user, type='expense')

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and start >= end:
            raise forms.ValidationError("End date must be after start date.")
        return cleaned_data


@login_required
def budget_list(request):
    budgets = Budget.objects.filter(user=request.user).select_related('category')
    return render(request, 'budgets/budget_list.html', {'budgets': budgets})

@login_required
def budget_create(request):
    if request.method == 'POST':
        form = BudgetForm(request.user, request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            budget.save()
            messages.success(request, 'Budget created!')
            return redirect('budget_list')
    else:
        form = BudgetForm(request.user)
    return render(request, 'budgets/budget_form.html', {'form': form, 'action': 'Create'})

@login_required
def budget_edit(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    if request.method == 'POST':
        form = BudgetForm(request.user, request.POST, instance=budget)
        if form.is_valid():
            form.save()
            messages.success(request, 'Budget updated!')
            return redirect('budget_list')
    else:
        form = BudgetForm(request.user, instance=budget)
    return render(request, 'budgets/budget_form.html', {'form': form, 'action': 'Edit'})

@login_required
def budget_delete(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    if request.method == 'POST':
        budget.delete()
        messages.success(request, 'Budget deleted.')
        return redirect('budget_list')
    return render(request, 'budgets/budget_confirm_delete.html', {'budget': budget})
