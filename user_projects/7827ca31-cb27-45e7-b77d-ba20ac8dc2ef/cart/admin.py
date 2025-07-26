from django.contrib import admin
from .models import Cart, CartItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    readonly_fields = ('created_at', 'updated_at')
    fields = ('product', 'quantity', 'created_at', 'updated_at')

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('cart__user__username', 'product__name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Cart Information', {
            'fields': ('cart', 'product')
        }),
        ('Quantity Details', {
            'fields': ('quantity',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at', 'item_count')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CartItemInline]

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def item_count(self, obj):
        return obj.cartitem_set.count()
    item_count.short_description = 'Number of Items'

    actions = ['clear_cart']

    def clear_cart(self, request, queryset):
        for cart in queryset:
            cart.cartitem_set.all().delete()
    clear_cart.short_description = "Clear selected carts"