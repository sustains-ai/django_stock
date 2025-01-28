from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Institute, FundManager, Portfolio, Stock

admin.site.register(Institute)
admin.site.register(FundManager)
admin.site.register(Portfolio)
admin.site.register(Stock)
