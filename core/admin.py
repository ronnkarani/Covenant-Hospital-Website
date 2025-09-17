from django.contrib import admin
from .models import HeroSlide,HeroContent, HomeCard, About, Service, BlogPost, PartnerLogo, BlogCategory, Comment, Profile,Patient, Doctor, Appointment, Report, Message, Department
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "date", "category", "likes_count")
    list_filter = ("category", "date")
    search_fields = ("title", "author", "content")
    ordering = ("-date",)
    
    def likes_count(self, obj):
        return obj.likes.count()
    likes_count.short_description = 'Likes'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("blog", "name", "date")
    search_fields = ("name", "text")
    list_filter = ("date",)

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("name", "doctor_id", "department", "approved")
    list_filter = ("approved", "department")
    search_fields = ("name", "doctor_id", "department")

    actions = ["approve_doctors", "revoke_approval"]

    def approve_doctors(self, request, queryset):
        updated = 0
        for doctor in queryset:
            if not doctor.approved:
                doctor.approved = True
                doctor.save()
                updated += 1

                # ✅ Sync their Profile role
                profile = Profile.objects.filter(user__username=doctor.name).first()
                if profile and profile.role != "doctor":
                    profile.role = "doctor"
                    profile.save()

                # ✅ Send approval email
                if doctor.email:
                    try:
                        context = {
                            "doctor_name": doctor.name,
                            "doctor_id": doctor.doctor_id,
                            "login_url": request.build_absolute_uri("/login/"),
                            "year": timezone.now().year,
                        }
                        subject = "✅ Your Covenant Hospital Account Has Been Approved"
                        html_content = render_to_string("emails/doctor_approved.html", context)
                        text_content = strip_tags(html_content)

                        msg = EmailMultiAlternatives(
                            subject=subject,
                            body=text_content,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            to=[doctor.email],
                        )
                        msg.attach_alternative(html_content, "text/html")
                        msg.send()

                    except Exception as e:
                        self.message_user(request, f"⚠️ Error sending email to {doctor.name}: {e}")

        self.message_user(request, f"{updated} doctor(s) approved successfully and notified via email.")
        
    def revoke_approval(self, request, queryset):
        updated = queryset.update(approved=False)
        self.message_user(request, f"{updated} doctor(s) approval revoked.")

    revoke_approval.short_description = "🚫 Revoke approval for selected doctors"


admin.site.register(HeroContent)
admin.site.register(HeroSlide)
admin.site.register(HomeCard)
admin.site.register(About)
admin.site.register(Service)
admin.site.register(PartnerLogo)

admin.site.register(Department)
admin.site.register(Patient)
admin.site.register(Appointment)
admin.site.register(Report)
admin.site.register(Message)
