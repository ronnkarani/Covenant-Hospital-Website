from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
import uuid


#USER MODEL
class Profile(models.Model):
    ROLE_CHOICES = (
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
        ('pending', 'Pending'),   # ✅ Add pending state
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    hospital_id = models.CharField(max_length=20, unique=True, blank=True, null=True)  # ✅ Unique hospital ID

    def save(self, *args, **kwargs):
        if not self.hospital_id:
            prefix = "DOC" if self.role == "doctor" else "PAT"
            self.hospital_id = f"{prefix}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} ({self.hospital_id}) - {self.role}"


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


class Patient(models.Model):
    patient_id = models.CharField(max_length=20, unique=True, editable=False, blank=True, null=True)  # ✅
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=1, choices=(('M', 'Male'), ('F', 'Female')))
    date_added = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.patient_id:
            self.patient_id = f"PAT-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.patient_id})"


# DOCTOR MODEL
class Doctor(models.Model):
    doctor_id = models.CharField(max_length=20, unique=True, editable=False, blank=True, null=True)  # ✅
    name = models.CharField(max_length=200)
    specialty = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100)

    def save(self, *args, **kwargs):
        if not self.doctor_id:
            self.doctor_id = f"DOC-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Dr. {self.name} ({self.doctor_id}) - {self.specialty}"


# APPOINTMENT MODEL
class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('concluded', 'Concluded'),
        ('cancelled', 'Cancelled'),
    )
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, related_name="appointments")
    date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.patient.name} with {self.doctor} on {self.date}"



# REPORT MODEL
class Report(models.Model):
    STATUS_CHOICES = (
        ('approved', 'Approved'),
        ('pending', 'Pending'),
        ('rejected', 'Rejected'),
    )
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="reports")
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    content = RichTextField()

    def __str__(self):
        return self.title


# MESSAGE MODEL
class Message(models.Model):
    STATUS_CHOICES = (
        ('unread', 'Unread'),
        ('read', 'Read'),
    )
    sender = models.CharField(max_length=200)
    recipient_doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, null=True, blank=True, related_name="doctor_messages")
    subject = models.CharField(max_length=200)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unread')
    date_sent = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} from {self.sender}"
