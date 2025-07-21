from django.contrib import admin
from .models import Cart, CartItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    readonly_fields = ('created_at', 'updated_at')
    fields = ('product', 'quantity', 'price', 'created_at', 'updated_at')
    show_change_link = True

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product', 'quantity', 'price', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('cart__user__username', 'product__name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('cart', 'product')
        }),
        ('Quantity and Price', {
            'fields': ('quantity', 'price')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('cart',)
        return self.readonly_fields

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_items', 'total_price', 'created_at', 'status')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    inlines = [CartItemInline]
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Cart Information', {
            'fields': ('user', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_abandoned', 'mark_as_completed']
    
    def total_items(self, obj):
        return obj.cartitem_set.count()
    total_items.short_description = 'Number of Items'
    
    def total_price(self, obj):
        return sum(item.price * item.quantity for item in obj.cartitem_set.all())
    total_price.short_description = 'Total Price'
    
    def mark_as_abandoned(self, request, queryset):
        queryset.update(status='abandoned')
    mark_as_abandoned.short_description = "Mark selected carts as abandoned"
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
    mark_as_completed.short_description = "Mark selected carts as completed"
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('user',)
        return self.readonly_fields