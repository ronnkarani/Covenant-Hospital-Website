from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from core.models import HeroSlide, HeroContent, HomeCard, About, Service, BlogPost, PartnerLogo, BlogCategory, Comment, Profile, Patient, Doctor, Appointment, Report, Message
from core.forms import CommentForm
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
        role = request.POST.get("role")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect("signup")

        user = User.objects.create_user(username=username, email=email, password=password)
        
        # ✅ Ensure Profile exists
        profile, created = Profile.objects.get_or_create(user=user)

        # ✅ Prevent self-registering as Doctor
        if role.lower() == "doctor":
            profile.role = "pending"   # mark for admin approval
        else:
            profile.role = role

        profile.save()

        messages.success(request, "Account created successfully! Awaiting approval if needed.")
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
@login_required
def dashboard(request):
    appointments = Appointment.objects.all().order_by("-date")[:5]
    patients = Patient.objects.all().order_by("-date_added")[:5]
    reports = Report.objects.all().order_by("-date")[:5]
    messages = Message.objects.all().order_by("-date_sent")[:5]

    return render(request, "dashboard/dashboard.html", {
        "appointments": appointments,
        "patients": patients,
        "reports": reports,
        "messages": messages,
    }) 


# ------------------ PATIENTS ------------------
def patients(request):
    q = request.GET.get("q", "").strip()
    patients_list = Patient.objects.all().order_by("-date_added")

    if q:
        patients_list = patients_list.filter(
            Q(name__icontains=q) |
            Q(phone__icontains=q) |
            Q(department__icontains=q)
        )

    paginator = Paginator(patients_list, 10)  # 10 per page
    page_number = request.GET.get("page")
    patients_page = paginator.get_page(page_number)

    return render(request, "dashboard/patients.html", {
        "patients_page": patients_page,
        "query": q
    })


# ------------------ APPOINTMENTS ------------------
def appointments(request):
    q = request.GET.get("q", "").strip()
    appointments_list = Appointment.objects.select_related("patient", "doctor").all().order_by("-date")

    if q:
        appointments_list = appointments_list.filter(
            Q(patient__name__icontains=q) |
            Q(patient__phone__icontains=q) |
            Q(doctor__name__icontains=q)
        )

    paginator = Paginator(appointments_list, 10)
    page_number = request.GET.get("page")
    appointments_page = paginator.get_page(page_number)

    return render(request, "dashboard/appointments.html", {
        "appointments": appointments_page,
        "query": q
    })


# ------------------ REPORTS ------------------
def reports(request):
    q = request.GET.get("q", "").strip()
    reports_list = Report.objects.select_related("author", "patient").all().order_by("-date")

    if q:
        reports_list = reports_list.filter(
            Q(title__icontains=q) |
            Q(author__name__icontains=q) |
            Q(patient__name__icontains=q)
        )

    paginator = Paginator(reports_list, 10)
    page_number = request.GET.get("page")
    reports_page = paginator.get_page(page_number)

    return render(request, "dashboard/reports.html", {
        "reports": reports_page,
        "query": q
    })


# ------------------ MESSAGES ------------------
def messages_view(request):
    q = request.GET.get("q", "").strip()
    messages_list = Message.objects.all().order_by("-date_sent")

    if q:
        messages_list = messages_list.filter(
            Q(sender__icontains=q) |
            Q(subject__icontains=q) |
            Q(content__icontains=q)
        )

    paginator = Paginator(messages_list, 5)  # 5 per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Counts for dashboard cards
    unread_count = messages_list.filter(status="unread").count()
    total_messages = messages_list.count()

    return render(request, "dashboard/messages.html", {
        "page_obj": page_obj,
        "unread_count": unread_count,
        "total_messages": total_messages,
        "query": q
    })