from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField


# HERO SECTION
class HeroContent(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.TextField(blank=True, null=True)
    button_text = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.title


class HeroSlide(models.Model):
    image = models.ImageField(upload_to="hero/")

    def __str__(self):
        return f"Slide {self.id}"



# CARDS SECTION
class HomeCard(models.Model):
    icon_class = models.CharField(max_length=100)  # e.g. "fas fa-user-md fa-3x"
    title = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.title


# ABOUT SECTION
class About(models.Model):
    story = models.TextField()
    about_text = models.TextField()
    vision = models.TextField()
    mission = models.TextField()
    video_file = models.FileField(upload_to="about/videos/", blank=True, null=True)

    def __str__(self):
        return "About Section"


# SERVICES SECTION
class Service(models.Model):
    icon_class = models.CharField(max_length=100)  # e.g. "fas fa-stethoscope fa-2x"
    title = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.title


# BLOG SECTION
class BlogCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100, default="Admin")
    date = models.DateField(auto_now_add=True)
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True, blank=True)
    likes = models.ManyToManyField(User, related_name='blog_likes', blank=True)
    content = RichTextUploadingField()
    image = models.ImageField(upload_to="blogs/")
    views = models.PositiveIntegerField(default=0)

    def total_likes(self):
        return self.likes.count()
    
    def __str__(self):
        return self.title

class Comment(models.Model):
    blog = models.ForeignKey(BlogPost, related_name="comments", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    text = models.TextField()
    date = models.DateTimeField(default=timezone.now)
    parent = models.ForeignKey("self", null=True, blank=True, related_name="replies", on_delete=models.CASCADE)
        
    def __str__(self):
        return f"Comment by {self.name} on {self.blog.title}"

# ACCREDITATION (Partners)
class PartnerLogo(models.Model):
    image = models.ImageField(upload_to="partners/")
    alt_text = models.CharField(max_length=200)

    def __str__(self):
        return self.alt_text
