from django.contrib import admin
from .models import Event, Category

admin.site.register(Category)
admin.site.register(Event)