from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import random
from decimal import Decimal

class CurrencyRate(models.Model):
    """Модель для хранения курса валют"""
    usd_to_rub = models.DecimalField(max_digits=10, decimal_places=2, default=75.00)
    last_updated = models.DateTimeField(auto_now=True)
    
    @classmethod
    def get_current_rate(cls):
        """Получить текущий курс"""
        rate, created = cls.objects.get_or_create(id=1)
        return rate.usd_to_rub
    
    @classmethod
    def update_rate(cls):
        """Обновить курс с шансом краха или роста"""
        rate, _ = cls.objects.get_or_create(id=1)
        
        # Шанс на событие: 5% краха, 5% резкого роста, 90% небольшое изменение
        chance = random.random()
        
        if chance < 0.05:  # 5% краха
            change = random.uniform(-0.3, -0.1)  # Падение на 10-30%
        elif chance < 0.10:  # 5% резкого роста
            change = random.uniform(0.1, 0.3)  # Рост на 10-30%
        else:  # 90% нормальных изменений
            change = random.uniform(-0.02, 0.02)  # Небольшое изменение ±2%
        
        new_rate = rate.usd_to_rub * (Decimal(1) + Decimal(str(change)))
        
        # Минимальный курс 10 рублей, максимальный 200
        if new_rate < 10:
            new_rate = Decimal(10)
        elif new_rate > 200:
            new_rate = Decimal(200)
            
        rate.usd_to_rub = new_rate
        rate.save()
        return new_rate

class UserProfile(models.Model):
    """Расширенный профиль пользователя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    balance_rub = models.DecimalField(max_digits=15, decimal_places=2, default=50000.00)
    balance_usd = models.DecimalField(max_digits=15, decimal_places=2, default=1000.00)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - RUB: {self.balance_rub}, USD: {self.balance_usd}"

class Company(models.Model):
    """Модель компании"""
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='companies_owned')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    balance_rub = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    balance_usd = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(User, related_name='companies', blank=True)
    
    def __str__(self):
        return f"{self.name} (Владелец: {self.owner.username})"

class Transaction(models.Model):
    """Модель транзакции"""
    TRANSACTION_TYPES = [
        ('transfer', 'Перевод'),
        ('exchange', 'Обмен'),
        ('company_transfer', 'Перевод в компанию'),
        ('company_withdraw', 'Вывод из компании'),
        ('company_create', 'Создание компании'),
    ]
    
    CURRENCIES = [
        ('RUB', 'Рубли'),
        ('USD', 'Доллары'),
    ]
    
    from_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_transactions')
    to_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='received_transactions')
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCIES)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} {self.currency}"

# Сигналы для создания профиля при создании пользователя
