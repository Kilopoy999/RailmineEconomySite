from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction as db_transaction
from django.http import JsonResponse
from decimal import Decimal
from .models import *
from .forms import *
from django.db.models import Max

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
        else:
            messages.error(request, 'Неверный логин или пароль')
    else:
        form = LoginForm()
    
    return render(request, 'core/login.html', {'form': form})

@login_required
def dashboard(request):
    # Обновляем курс в 10% случаев при загрузке страницы
    import random
    if random.random() < 0.1:
        CurrencyRate.update_rate()
    
    profile = request.user.profile
    companies = request.user.companies.all()
    owned_companies = request.user.companies_owned.all()
    
    # Последние транзакции
    transactions = Transaction.objects.filter(
        models.Q(from_user=request.user) | 
        models.Q(to_user=request.user)
    ).order_by('-timestamp')[:10]
    
    context = {
        'profile': profile,
        'companies': companies,
        'owned_companies': owned_companies,
        'transactions': transactions,
        'exchange_rate': CurrencyRate.get_current_rate(),
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def transfer_money(request):
    if request.method == 'POST':
        form = TransferForm(request.POST)
        if form.is_valid():
            try:
                with db_transaction.atomic():
                    to_user_id = form.cleaned_data['to_user_id']
                    amount = form.cleaned_data['amount']
                    currency = form.cleaned_data['currency']
                    description = form.cleaned_data['description']
                    
                    # Проверяем, перевод ли это компании
                    try:
                        company = Company.objects.get(id=to_user_id)
                        # Перевод компании
                        profile = request.user.profile
                        
                        if currency == 'RUB':
                            if profile.balance_rub < amount:
                                messages.error(request, 'Недостаточно рублей на счету!')
                                return redirect('transfer')
                            profile.balance_rub -= amount
                            company.balance_rub += amount
                        else:  # USD
                            if profile.balance_usd < amount:
                                messages.error(request, 'Недостаточно долларов на счету!')
                                return redirect('transfer')
                            profile.balance_usd -= amount
                            company.balance_usd += amount
                        
                        profile.save()
                        company.save()
                        
                        Transaction.objects.create(
                            from_user=request.user,
                            company=company,
                            amount=amount,
                            currency=currency,
                            transaction_type='company_transfer',
                            description=description
                        )
                        
                        messages.success(request, f'Перевод {amount} {currency} компании "{company.name}" выполнен!')
                        return redirect('dashboard')
                        
                    except Company.DoesNotExist:
                        # Обычный перевод пользователю (старый код)
                        if to_user_id == request.user.id:
                            messages.error(request, 'Нельзя переводить самому себе!')
                            return redirect('transfer')
                        
                        to_user = get_object_or_404(User, id=to_user_id)
                        
                        profile = request.user.profile
                        if currency == 'RUB':
                            if profile.balance_rub < amount:
                                messages.error(request, 'Недостаточно рублей на счету!')
                                return redirect('transfer')
                            profile.balance_rub -= amount
                            to_user.profile.balance_rub += amount
                        else:  # USD
                            if profile.balance_usd < amount:
                                messages.error(request, 'Недостаточно долларов на счету!')
                                return redirect('transfer')
                            profile.balance_usd -= amount
                            to_user.profile.balance_usd += amount
                        
                        profile.save()
                        to_user.profile.save()
                        
                        Transaction.objects.create(
                            from_user=request.user,
                            to_user=to_user,
                            amount=amount,
                            currency=currency,
                            transaction_type='transfer',
                            description=description
                        )
                        
                        messages.success(request, f'Перевод {amount} {currency} пользователю {to_user.username} выполнен!')
                        return redirect('dashboard')
                        
            except Exception as e:
                messages.error(request, f'Ошибка при переводе: {str(e)}')
    else:
        form = TransferForm()
    
    # Получаем компании пользователя для отображения
    companies = request.user.companies.all()
    
    return render(request, 'core/transfer.html', {
        'form': form,
        'companies': companies
    })

@login_required
def exchange_currency(request):
    if request.method == 'POST':
        form = ExchangeForm(request.POST)
        if form.is_valid():
            try:
                with db_transaction.atomic():
                    operation = form.cleaned_data['operation']
                    amount = form.cleaned_data['amount']
                    profile = request.user.profile
                    rate = CurrencyRate.get_current_rate()
                    
                    if operation == 'buy_usd':
                        # Покупка долларов за рубли
                        rub_needed = amount * rate
                        if profile.balance_rub < rub_needed:
                            messages.error(request, f'Недостаточно рублей для покупки! Нужно: {rub_needed:.2f} RUB')
                            return redirect('exchange')
                        
                        profile.balance_rub -= rub_needed
                        profile.balance_usd += amount
                        profile.save()
                        
                        Transaction.objects.create(
                            from_user=request.user,
                            amount=amount,
                            currency='USD',
                            transaction_type='exchange',
                            description=f'Покупка {amount} USD за {rub_needed:.2f} RUB по курсу {rate}'
                        )
                        
                        messages.success(request, f'Успешно! Куплено {amount} USD за {rub_needed:.2f} RUB')
                    
                    else:  # sell_usd
                        # Продажа долларов за рубли
                        if profile.balance_usd < amount:
                            messages.error(request, f'Недостаточно долларов для продажи! На счету: {profile.balance_usd} USD')
                            return redirect('exchange')
                        
                        rub_received = amount * rate
                        profile.balance_usd -= amount
                        profile.balance_rub += rub_received
                        profile.save()
                        
                        Transaction.objects.create(
                            from_user=request.user,
                            amount=amount,
                            currency='USD',
                            transaction_type='exchange',
                            description=f'Продажа {amount} USD за {rub_received:.2f} RUB по курсу {rate}'
                        )
                        
                        messages.success(request, f'Успешно! Продано {amount} USD за {rub_received:.2f} RUB')
                    
                    return redirect('dashboard')
                    
            except Exception as e:
                messages.error(request, f'Ошибка при обмене: {str(e)}')
                return redirect('exchange')
    else:
        form = ExchangeForm()
    
    rate = CurrencyRate.get_current_rate()
    profile = request.user.profile
    
    return render(request, 'core/exchange.html', {
        'form': form, 
        'rate': rate,
        'profile': profile
    })

@login_required
def create_company(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            try:
                with db_transaction.atomic():
                    profile = request.user.profile
                    creation_cost = Decimal('2000000')
                    
                    if profile.balance_usd < creation_cost:
                        messages.error(request, 'Недостаточно средств! Требуется 2,000,000 USD')
                        return redirect('create_company')
                    
                    # Списываем средства
                    profile.balance_usd -= creation_cost
                    profile.save()
                    
                    # 🔥 МИНИМАЛЬНОЕ ВМЕШАТЕЛЬСТВО - НАЧИНАЕМ С ID 1000 🔥
                    # Получаем максимальный ID
                    max_id = Company.objects.aggregate(max_id=Max('id'))['max_id']
                    if max_id is None:
                        company_id = 1000  # Первая компания получит ID 1000
                    else:
                        # Если есть компании, берем следующий ID, но не меньше 1000
                        company_id = max(max_id + 1, 1000)
                    
                    # Создаем компанию с ручным ID
                    company = Company(
                        id=company_id,  # Указываем ID вручную
                        owner=request.user,
                        name=form.cleaned_data['name'],
                        description=form.cleaned_data.get('description', ''),
                        balance_usd=creation_cost
                    )
                    company.save()
                    company.members.add(request.user)
                    
                    # Запись о транзакции
                    Transaction.objects.create(
                        from_user=request.user,
                        company=company,
                        amount=creation_cost,
                        currency='USD',
                        transaction_type='company_create',
                        description=f'Создание компании "{company.name}" (ID: {company_id})'
                    )
                    
                    messages.success(request, f'Компания "{company.name}" создана! ID: {company_id}')
                    return redirect('company_dashboard', company_id=company_id)
                    
            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
    else:
        form = CompanyForm()
    
    return render(request, 'core/company_create.html', {'form': form})

@login_required
def company_dashboard(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    
    # Проверяем доступ
    if request.user not in company.members.all() and request.user != company.owner:
        messages.error(request, 'У вас нет доступа к этой компании!')
        return redirect('dashboard')
    
    # Получаем транзакции компании
    transactions = Transaction.objects.filter(company=company).order_by('-timestamp')[:20]
    
    context = {
        'company': company,
        'transactions': transactions,
        'is_owner': request.user == company.owner,
    }
    return render(request, 'core/company_dashboard.html', context)

@login_required
def company_transfer(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    
    # Проверяем доступ
    if request.user not in company.members.all():
        messages.error(request, 'У вас нет доступа к этой компании!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CompanyTransferForm(request.POST)
        if form.is_valid():
            try:
                with db_transaction.atomic():
                    to_user_id = form.cleaned_data['to_user_id']
                    amount = form.cleaned_data['amount']
                    currency = form.cleaned_data['currency']
                    description = form.cleaned_data['description']
                    
                    to_user = get_object_or_404(User, id=to_user_id)
                    
                    # Проверяем баланс компании
                    if currency == 'RUB':
                        if company.balance_rub < amount:
                            messages.error(request, 'Недостаточно рублей на счету компании!')
                            return redirect('company_transfer', company_id=company_id)
                        company.balance_rub -= amount
                        to_user.profile.balance_rub += amount
                    else:  # USD
                        if company.balance_usd < amount:
                            messages.error(request, 'Недостаточно долларов на счету компании!')
                            return redirect('company_transfer', company_id=company_id)
                        company.balance_usd -= amount
                        to_user.profile.balance_usd += amount
                    
                    company.save()
                    to_user.profile.save()
                    
                    # Создаем запись о транзакции
                    Transaction.objects.create(
                        from_user=request.user,
                        to_user=to_user,
                        company=company,
                        amount=amount,
                        currency=currency,
                        transaction_type='company_transfer',
                        description=description
                    )
                    
                    messages.success(request, f'Перевод {amount} {currency} успешно выполнен!')
                    return redirect('company_dashboard', company_id=company_id)
                    
            except Exception as e:
                messages.error(request, f'Ошибка при переводе: {str(e)}')
    else:
        form = CompanyTransferForm()
    
    return render(request, 'core/company_manage.html', {
        'form': form,
        'company': company,
        'action': 'transfer'
    })

@login_required
def company_withdraw(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    
    # Проверяем, что пользователь - владелец
    if request.user != company.owner:
        messages.error(request, 'Только владелец может выводить средства!')
        return redirect('company_dashboard', company_id=company_id)
    
    if request.method == 'POST':
        form = CompanyWithdrawForm(request.POST)
        if form.is_valid():
            try:
                with db_transaction.atomic():
                    amount = form.cleaned_data['amount']
                    currency = form.cleaned_data['currency']
                    
                    # Проверяем баланс компании
                    if currency == 'RUB':
                        if company.balance_rub < amount:
                            messages.error(request, 'Недостаточно рублей на счету компании!')
                            return redirect('company_withdraw', company_id=company_id)
                        company.balance_rub -= amount
                        request.user.profile.balance_rub += amount
                    else:  # USD
                        if company.balance_usd < amount:
                            messages.error(request, 'Недостаточно долларов на счету компании!')
                            return redirect('company_withdraw', company_id=company_id)
                        company.balance_usd -= amount
                        request.user.profile.balance_usd += amount
                    
                    company.save()
                    request.user.profile.save()
                    
                    # Создаем запись о транзакции
                    Transaction.objects.create(
                        from_user=request.user,
                        company=company,
                        amount=amount,
                        currency=currency,
                        transaction_type='company_withdraw',
                        description=f'Вывод средств владельцем'
                    )
                    
                    messages.success(request, f'Выведено {amount} {currency} на личный счет!')
                    return redirect('company_dashboard', company_id=company_id)
                    
            except Exception as e:
                messages.error(request, f'Ошибка при выводе средств: {str(e)}')
    else:
        form = CompanyWithdrawForm()
    
    return render(request, 'core/company_manage.html', {
        'form': form,
        'company': company,
        'action': 'withdraw'
    })

@login_required
def update_exchange_rate(request):
    """API для обновления курса (можно вызывать вручную)"""
    if request.user.is_superuser:
        new_rate = CurrencyRate.update_rate()
        return JsonResponse({'new_rate': float(new_rate), 'status': 'updated'})
    return JsonResponse({'error': 'Недостаточно прав'}, status=403)

def logout_view(request):
    logout(request)

    return redirect('login')

# В самый конец views.py, после всех функций
from django.contrib.auth.models import User
from django.db.utils import ProgrammingError, OperationalError
import os

def create_superuser_if_not_exists():
    """Создает суперпользователя если его нет"""
    try:
        # Проверяем, есть ли уже пользователи
        if not User.objects.exists():
            username = os.environ.get('ADMIN_USERNAME', 'admin')
            email = os.environ.get('ADMIN_EMAIL', 'admin@bank.com')
            password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            
            # Создаем суперпользователя
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            print(f"✅ Суперпользователь создан: {username}")
        else:
            print("✅ Пользователи уже существуют")
    except (ProgrammingError, OperationalError) as e:
        # База данных еще не готова
        print(f"⚠️  База данных не готова: {e}")
    except Exception as e:
        print(f"⚠️  Ошибка создания пользователя: {e}")

# Вызываем при импорте
create_superuser_if_not_exists()
