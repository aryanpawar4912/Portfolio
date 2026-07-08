from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import Project, Contact, PageView, SiteStatistic

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'featured', 'created_at')
    list_filter = ('category', 'featured')
    search_fields = ('title', 'description')

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'status_badge', 'view_message')
    list_filter = ('created_at', 'is_read')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('created_at', 'message_display')
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email')
        }),
        ('Message', {
            'fields': ('subject', 'message_display')
        }),
        ('Meta', {
            'fields': ('created_at', 'is_read')
        }),
    )
    
    def status_badge(self, obj):
        if obj.is_read:
            return format_html('<span style="color: green;">✓ Read</span>')
        else:
            return format_html('<span style="color: red;">✗ Unread</span>')
    status_badge.short_description = 'Status'
    
    def view_message(self, obj):
        return format_html(
            '<a class="button" href="#" onclick="alert(\'{}\'); return false;">View</a>',
            obj.message.replace("'", "\\'").replace("\n", "\\n")
        )
    view_message.short_description = 'Message'
    
    def message_display(self, obj):
        return obj.message
    message_display.short_description = 'Message'


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ('page', 'ip_address', 'timestamp')
    list_filter = ('page', 'timestamp')
    search_fields = ('ip_address',)
    readonly_fields = ('page', 'ip_address', 'user_agent', 'timestamp', 'referrer')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SiteStatistic)
class SiteStatisticAdmin(admin.ModelAdmin):
    list_display = ('total_views', 'total_unique_visitors', 'total_contacts', 'last_updated')
    readonly_fields = ('total_views', 'total_unique_visitors', 'total_contacts', 'last_updated')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

from django.contrib import admin
from .models import (Education, Experience, Certification, Award, Publication, Skill, CoreStrength, Interest)

@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('title', 'institution', 'duration', 'order')
    list_editable = ('order',)

@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'duration', 'order')
    list_editable = ('order',)

@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'issuer', 'date', 'order')
    list_editable = ('order',)

@admin.register(Award)
class AwardAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_organizer', 'date', 'order')
    list_editable = ('order',)

@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ('title', 'publish_date')

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'percentage', 'order')
    list_editable = ('percentage', 'order')

@admin.register(CoreStrength)
class CoreStrengthAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon_name', 'order')
    list_editable = ('order',)

@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon_name', 'order')
    list_editable = ('order',)