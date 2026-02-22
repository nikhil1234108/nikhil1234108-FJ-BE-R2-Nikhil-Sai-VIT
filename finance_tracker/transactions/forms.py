from django import forms
from .models import Transaction, Category


# --------------------------------------------------
# CATEGORY FORM
# --------------------------------------------------
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'type', 'icon', 'color', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'icon': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }


# --------------------------------------------------
# TRANSACTION FORM
# --------------------------------------------------
class TransactionForm(forms.ModelForm):

    new_category = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new category name'
        })
    )

    class Meta:
        model = Transaction
        fields = [
            'type', 'category', 'new_category', 'amount', 'currency',
            'date', 'description', 'notes', 'is_refund', 'receipt'
        ]
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'receipt': forms.FileInput(attrs={'class': 'form-control'}),
            'is_refund': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['category'].queryset = Category.objects.filter(user=user)
        self.fields['category'].required = False

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        new_category = cleaned_data.get('new_category')
        transaction_type = cleaned_data.get('type')

        if new_category:
            category_obj, created = Category.objects.get_or_create(
                name=new_category.strip(),
                type=transaction_type,
                user=self.user,
                defaults={
                    "icon": "📌",
                    "color": "#6366f1"
                }
            )
            cleaned_data['category'] = category_obj

        elif category and transaction_type:
            if category.type != transaction_type:
                raise forms.ValidationError(
                    f"Category '{category.name}' is for {category.type}, "
                    f"but you selected {transaction_type}."
                )

        return cleaned_data


# --------------------------------------------------
# TRANSACTION FILTER FORM
# --------------------------------------------------
class TransactionFilterForm(forms.Form):

    MONTH_CHOICES = [
        ('', 'All Months'),
        ('1', 'January'), ('2', 'February'), ('3', 'March'),
        ('4', 'April'), ('5', 'May'), ('6', 'June'),
        ('7', 'July'), ('8', 'August'), ('9', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ]

    type = forms.ChoiceField(
        choices=[('', 'All Types'), ('income', 'Income'), ('expense', 'Expense')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Year'
        })
    )

    min_amount = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    max_amount = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user)