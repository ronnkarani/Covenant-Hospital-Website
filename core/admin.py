from django.contrib import admin
from .models import HeroSlide,HeroContent, HomeCard, About, Service, BlogPost, PartnerLogo, BlogCategory, Comment


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
    
admin.site.register(HeroContent)
admin.site.register(HeroSlide)
admin.site.register(HomeCard)
admin.site.register(About)
admin.site.register(Service)
admin.site.register(PartnerLogo)
