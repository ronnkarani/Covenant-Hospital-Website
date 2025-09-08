from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from .models import HeroSlide, HeroContent, HomeCard, About, Service, BlogPost, PartnerLogo, BlogCategory, Comment
from .forms import CommentForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings

#LOGIN VIEW
def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect("signup")

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        messages.success(request, "Account created successfully! You can log in.")
        return redirect("login")

    return render(request, "signup.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("index")  # change to your homepage
        else:
            messages.error(request, "Invalid username or password")
            return redirect("login")

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("index")


#HOME PAGE
def index(request):
    hero_content = HeroContent.objects.first()
    hero_slides = HeroSlide.objects.all()
    home_cards = HomeCard.objects.all()
    about = About.objects.first()
    services = Service.objects.all()
    blogs = BlogPost.objects.order_by('-id')[:4]
    partners = PartnerLogo.objects.all()

    return render(request, 'index.html', {
        "hero_content": hero_content,
        "hero_slides": hero_slides,
        "home_cards": home_cards,
        "about": about,
        "services": services,
        "blogs": blogs,
        "partners": partners
    })


#ABOUT PAGE
def about(request):
    about_page = About.objects.first()
    services = Service.objects.all()
    partners = PartnerLogo.objects.all()

    return render(request, "about.html", {
        "about_page": about_page,
        "services": services,
        "partners": partners
    })

#BLOG PAGE
def blog(request):
    query = request.GET.get("q")
    category_id = request.GET.get("category")

    blogs = BlogPost.objects.all().order_by("-date")

    # Search
    if query:
        blogs = blogs.filter(title__icontains=query) | blogs.filter(content__icontains=query)

    # Category filter
    if category_id:
        blogs = blogs.filter(category__id=category_id)

    # Pagination
    paginator = Paginator(blogs, 4)  # 5 posts per page
    page = request.GET.get("page")
    blogs = paginator.get_page(page)

    categories = BlogCategory.objects.all()
    recent_posts = BlogPost.objects.order_by("-date")[:5]
    partners = PartnerLogo.objects.all()

    return render(request, "blog.html", {
        "blogs": blogs,
        "categories": categories,
        "recent_posts": recent_posts,
        "partners": partners
    })



def blog_detail(request, pk):
    blog = get_object_or_404(BlogPost, pk=pk)
    blog.views += 1
    blog.save()

    comments = blog.comments.filter(parent__isnull=True)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.blog = blog
            new_comment.save()
            return redirect("blog_detail", pk=pk)
    else:
        form = CommentForm()

    recent_posts = BlogPost.objects.order_by("-date")[:3]
    popular_posts = BlogPost.objects.order_by("-views")[:4]
    partners = PartnerLogo.objects.all()

    return render(request, "blog_detail.html", {
        "blog": blog,
        "comments": comments,
        "comment_form": form,
        "recent_posts": recent_posts,
        "popular_posts": popular_posts,
        "partners": partners,
    })


@login_required
def blog_like(request, pk):
    blog = get_object_or_404(BlogPost, pk=pk)
    if request.user in blog.likes.all():
        blog.likes.remove(request.user)
    else:
        blog.likes.add(request.user)
    return redirect('blog_detail', pk=pk)

#CONTACT PAGE
def contact(request):
    partners = PartnerLogo.objects.all()
    

    return render(request, "contact.html", {        "partners": partners,
})
def contact(request):
    partners = PartnerLogo.objects.all()
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        subject = f"New Contact Form Submission from {name}"
        full_message = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"

        try:
            send_mail(
                subject,
                full_message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.EMAIL_HOST_USER],  # receiver = your Gmail
            )
            messages.success(request, "Your message has been sent successfully!")
        except Exception as e:
            messages.error(request, f"Error sending message: {e}")

        return redirect("contact")  # reload page after form submission

    return render(request, "contact.html", {"partners": partners})


#DASHBOARD VIEWS
def dashboard(request):
    # Raw dummy appointments
    appointments = [
        {"id": 1, "patient_name": "John Doe", "phone": "0712345678", "date": "2025-09-10", "status": "Pending"},
        {"id": 2, "patient_name": "Jane Smith", "phone": "0798765432", "date": "2025-09-12", "status": "Concluded"},
        {"id": 3, "patient_name": "Michael Brown", "phone": "0722334455", "date": "2025-09-15", "status": "Cancelled"},
    ]

    # Raw dummy patients
    patients = [
        {"id": 1, "name": "John Doe", "phone": "0712345678", "department": "Cardiology"},
        {"id": 2, "name": "Jane Smith", "phone": "0798765432", "department": "Neurology"},
        {"id": 3, "name": "Michael Brown", "phone": "0722334455", "department": "Orthopedics"},
    ]
    
    # Raw dummy reports
    reports = [
        {"id": 1, "title": "Blood Test Results", "date": "2025-09-05", "doctor": "Dr. Adams"},
        {"id": 2, "title": "X-Ray Analysis", "date": "2025-09-06", "doctor": "Dr. Brown"},
        {"id": 3, "title": "MRI Scan Report", "date": "2025-09-07", "doctor": "Dr. Carter"},
    ]

    # Raw dummy messages
    messages = [
        {"id": 1, "sender": "Admin", "subject": "System Update"},
        {"id": 2, "sender": "Patient", "subject": "Appointment Request"},
        {"id": 3, "sender": "Doctor", "subject": "Lab Results Uploaded"},
    ]


    return render(request, "dashboard.html", {
        "appointments": appointments,
        "patients": patients,
        "reports": reports,
        "messages": messages
    })