from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Company, Transaction, CurrencyRate

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Профиль'

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'profile_balance')
    
    def profile_balance(self, obj):
        return f"{obj.profile.balance_rub} RUB / {obj.profile.balance_usd} USD"
    profile_balance.short_description = 'Баланс'

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'balance_rub', 'balance_usd', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'owner__username')
    filter_horizontal = ('members',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'amount', 'currency', 'from_user', 'to_user', 'company', 'timestamp')
    list_filter = ('transaction_type', 'currency', 'timestamp')
    search_fields = ('from_user__username', 'to_user__username', 'description')
    readonly_fields = ('timestamp',)

@admin.register(CurrencyRate)
class CurrencyRateAdmin(admin.ModelAdmin):
    list_display = ('usd_to_rub', 'last_updated')
    readonly_fields = ('last_updated',)
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

# Перерегистрируем UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)