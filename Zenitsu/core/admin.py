from django.contrib import admin
from .models import UserInfo, certifications, EmailLog
from django.utils.html import format_html

# Register your models here.
@admin.register(UserInfo)
class UserInfoAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'created_at')
    search_fields = ('username', 'email')
    ordering = ('-created_at',)

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('recipient_email', 'status', 'subject', 'sent_at', 'certificate_link')
    list_filter = ('status', 'sent_at')
    search_fields = ('recipient_email', 'subject', 'error_message')
    readonly_fields = ('certificate', 'recipient_email', 'subject', 'status', 'error_message', 'sent_at')
    
    def certificate_link(self, obj):
        return format_html('<a href="/admin/core/certifications/{}/change/">{}</a>', 
                         obj.certificate.id, 
                         obj.certificate.certificate_number)
    certificate_link.short_description = 'Certificate'

@admin.register(certifications)
class CertificationsAdmin(admin.ModelAdmin):
    list_display = ('certificate_name', 'recipient_name', 'issued_by', 'issued_date', 'completion_date', 'is_sent', 'sent_at')
    search_fields = ('recipient_name', 'recipient_email', 'certificate_name', 'issued_by')
    list_filter = ('is_sent', 'issued_date')
    readonly_fields = ('certificate_number','issued_date', 'sent_at')

    actions = ['send_certifications', 'resend_certifications']

    def send_certifications(self, request, queryset):
        count = 0
        for certification in queryset:
            if not certification.is_sent:
                if certification.send_certificate_email():
                    count += 1
        self.message_user(request, f"{count} certifications sent successfully.")
    send_certifications.short_description = "Send selected certifications via email"

    def resend_certifications(self, request, queryset):
        count = 0
        for certification in queryset:
            if certification.send_certificate_email():
                count += 1
        self.message_user(request, f"{count} certifications resent successfully.")
    resend_certifications.short_description = "Resend selected certifications via email"




