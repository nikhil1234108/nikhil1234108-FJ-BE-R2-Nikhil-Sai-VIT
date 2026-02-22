def __init__(self, user, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.user = user

    # Default: show only income categories first
    self.fields['category'].queryset = Category.objects.filter(
        user=user,
        type='income'
    )
    self.fields['category'].required = False