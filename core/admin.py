from django.contrib import admin
from .models import HeroSlide,HeroContent, HomeCard, About, Service, BlogPost, PartnerLogo, BlogCategory, Comment, Profile,Patient, Doctor, Appointment, Report, Message
from django.core.mail import send_mail
from django.conf import settings


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
    list_display = ("name", "doctor_id", "specialty", "department", "approved")
    list_filter = ("approved", "department", "specialty")
    search_fields = ("name", "doctor_id", "specialty", "department")

    actions = ["approve_doctors", "revoke_approval"]

    def approve_doctors(self, request, queryset):
        updated = 0
        for doctor in queryset:
            if not doctor.approved:
                doctor.approved = True
                doctor.save()
                updated += 1

                # ✅ Sync their Profile role (in case still pending)
                profile = Profile.objects.filter(user__username=doctor.name).first()
                if profile and profile.role != "doctor":
                    profile.role = "doctor"
                    profile.save()

                # ✅ Send approval email
                if doctor.email:
                    try:
                        send_mail(
                            subject="Your Covenant Hospital Account Has Been Approved",
                            message=(
                                f"Hello Dr. {doctor.name},\n\n"
                                f"Good news! Your Covenant Hospital account has been approved.\n\n"
                                f"Here are your login details:\n"
                                f"Doctor ID: {doctor.doctor_id}\n\n"
                                f"You can now log in via the portal.\n\n"
                                f"Best regards,\n"
                                f"Covenant Hospital Admin Team"
                            ),
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[doctor.email],
                            fail_silently=True,
                        )
                    except Exception as e:
                        self.message_user(request, f"⚠️ Error sending email to {doctor.name}: {e}")

        self.message_user(request, f"{updated} doctor(s) approved successfully and notified via email.")

    approve_doctors.short_description = "✅ Approve selected doctors (and notify by email)"

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

admin.site.register(Patient)
admin.site.register(Appointment)
admin.site.register(Report)
admin.site.register(Message)
