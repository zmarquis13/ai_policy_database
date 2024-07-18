#configuration for the admin page (what's visible, what can be searched, etc.)

from django.contrib import admin

# Register your models here.
from .models import Bill

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('title', 'state', 'status_date')
    ordering = ('status_date',)
    search_fields = ('title', 'description', 'text')
    list_filter = ('status_date', 'state', 'content_collection', 'source')

