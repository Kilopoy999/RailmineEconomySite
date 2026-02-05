from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Company

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Логин'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Пароль'
        })
    )

class TransferForm(forms.Form):
    to_user_id = forms.IntegerField(
        label='ID получателя',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ID пользователя'
        })
    )
    amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Сумма'
        })
    )
    currency = forms.ChoiceField(
        choices=[('RUB', 'Рубли'), ('USD', 'Доллары')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Описание (необязательно)'
        })
    )

class ExchangeForm(forms.Form):
    OPERATION_CHOICES = [
        ('buy_usd', 'Купить доллары за рубли'),
        ('sell_usd', 'Продать доллары за рубли'),
    ]
    
    operation = forms.ChoiceField(
        choices=OPERATION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Сумма'
        })
    )

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название компании'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Описание компании'
            }),
        }

class CompanyTransferForm(forms.Form):
    to_user_id = forms.IntegerField(
        label='ID получателя',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ID пользователя'
        })
    )
    amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Сумма'
        })
    )
    currency = forms.ChoiceField(
        choices=[('RUB', 'Рубли'), ('USD', 'Доллары')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Описание'
        })
    )

class CompanyWithdrawForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Сумма'
        })
    )
    currency = forms.ChoiceField(
        choices=[('RUB', 'Рубли'), ('USD', 'Доллары')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )