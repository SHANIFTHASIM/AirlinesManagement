from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from armsApp.models import CustomUser, Airlines, Airport, Flights, Reservation
from django.utils.html import format_html

# Register CustomUser with photo field and include it in the UserAdmin form
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'first_name', 'last_name', 'email', 'photo', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    # Add photo to the user details view
    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="50" height="50" />', obj.photo.url)
        return "No Image"
    photo_preview.short_description = 'Profile Photo'

    fieldsets = (
        (None, {'fields': ('username', 'first_name', 'last_name', 'email', 'photo', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'photo'),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)

# Register other models
@admin.register(Airlines)
class AirlinesAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'delete_flag', 'date_added', 'date_created')
    list_filter = ('status',)
    search_fields = ('name',)
    ordering = ('-date_added',)

@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'delete_flag', 'date_added', 'date_created')
    list_filter = ('status',)
    search_fields = ('name',)
    ordering = ('-date_added',)

@admin.register(Flights)
class FlightsAdmin(admin.ModelAdmin):
    list_display = ('code', 'airline', 'from_airport', 'to_airport', 'departure', 'estimated_arrival', 'business_class_slots', 'economy_slots')
    list_filter = ('airline', 'from_airport', 'to_airport', 'departure')
    search_fields = ('code', 'airline__name', 'from_airport__name', 'to_airport__name')
    ordering = ('-date_added',)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('flight', 'first_name', 'last_name', 'email', 'status', 'date_added')
    list_filter = ('status', 'flight')
    search_fields = ('first_name', 'last_name', 'email', 'flight__code')
    ordering = ('-date_added',)
