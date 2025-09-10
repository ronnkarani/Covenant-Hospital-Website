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

def patients(request):
    # Raw dummy patients (more than 10 so pagination shows multiple pages)
    raw_patients = [
        {"id": 1, "name": "John Doe", "phone": "0712345678", "department": "Cardiology", "age": 45, "gender": "M"},
        {"id": 2, "name": "Jane Smith", "phone": "0798765432", "department": "Neurology", "age": 38, "gender": "F"},
        {"id": 3, "name": "Michael Brown", "phone": "0722334455", "department": "Orthopedics", "age": 52, "gender": "M"},
        {"id": 4, "name": "Alice Walker", "phone": "0711002003", "department": "Pediatrics", "age": 29, "gender": "F"},
        {"id": 5, "name": "Samuel Karanja", "phone": "0722113344", "department": "ENT", "age": 61, "gender": "M"},
        {"id": 6, "name": "Grace Mwangi", "phone": "0733004455", "department": "Gynaecology", "age": 34, "gender": "F"},
        {"id": 7, "name": "Peter Otieno", "phone": "0744005566", "department": "Dermatology", "age": 27, "gender": "M"},
        {"id": 8, "name": "Linda Njoroge", "phone": "0755006677", "department": "Ophthalmology", "age": 48, "gender": "F"},
        {"id": 9, "name": "David Kimani", "phone": "0766007788", "department": "Cardiology", "age": 60, "gender": "M"},
        {"id": 10, "name": "Ann Wanjiru", "phone": "0777008899", "department": "Neurology", "age": 41, "gender": "F"},
        {"id": 11, "name": "Josephine A.", "phone": "0788009900", "department": "Pediatrics", "age": 8, "gender": "F"},
        {"id": 12, "name": "Brian Chege", "phone": "0799001122", "department": "Orthopedics", "age": 53, "gender": "M"},
        {"id": 13, "name": "Catherine O.", "phone": "0700112233", "department": "Geriatrics", "age": 72, "gender": "F"},
        {"id": 14, "name": "Mark Otieno", "phone": "0700223344", "department": "ENT", "age": 36, "gender": "M"},
        {"id": 15, "name": "Ruth N.", "phone": "0700334455", "department": "Dermatology", "age": 25, "gender": "F"},
        {"id": 16, "name": "Samuel Mworia", "phone": "0700445566", "department": "Cardiology", "age": 58, "gender": "M"},
        {"id": 17, "name": "Esther Kimani", "phone": "0700556677", "department": "Ophthalmology", "age": 39, "gender": "F"},
        {"id": 18, "name": "Kevin Otieno", "phone": "0700667788", "department": "General Surgery", "age": 30, "gender": "M"},
        {"id": 19, "name": "Martha W.", "phone": "0700778899", "department": "Gynaecology", "age": 33, "gender": "F"},
        {"id": 20, "name": "Felix O.", "phone": "0700889900", "department": "Cardiology", "age": 50, "gender": "M"},
    ]

    # simple search filter by q (name, phone or department)
    q = request.GET.get('q', '').strip()
    if q:
        filtered = []
        q_lower = q.lower()
        for p in raw_patients:
            if q_lower in str(p['name']).lower() or q_lower in str(p['phone']).lower() or q_lower in str(p['department']).lower():
                filtered.append(p)
        patients_list = filtered
    else:
        patients_list = raw_patients

    # pagination: 10 patients per page
    paginator = Paginator(patients_list, 10)
    page = request.GET.get('page')
    patients_page = paginator.get_page(page)

    return render(request, 'patients.html', {
        'patients_page': patients_page,
    })
    
    
def appointments(request):
    query = request.GET.get("q", "")

    # Raw dummy appointments
    all_appointments = [
        {"id": 1, "patient_name": "John Doe", "phone": "0712345678", "date": "2025-09-10", "status": "Pending"},
        {"id": 2, "patient_name": "Jane Smith", "phone": "0798765432", "date": "2025-09-12", "status": "Concluded"},
        {"id": 3, "patient_name": "Michael Brown", "phone": "0722334455", "date": "2025-09-15", "status": "Cancelled"},
        {"id": 4, "patient_name": "Emily Davis", "phone": "0788991122", "date": "2025-09-18", "status": "Pending"},
        {"id": 5, "patient_name": "Chris Wilson", "phone": "0733445566", "date": "2025-09-20", "status": "Concluded"},
        {"id": 6, "patient_name": "Sarah Johnson", "phone": "0700123456", "date": "2025-09-22", "status": "Pending"},
        {"id": 7, "patient_name": "David White", "phone": "0799123456", "date": "2025-09-23", "status": "Cancelled"},
        {"id": 8, "patient_name": "Laura Green", "phone": "0744332211", "date": "2025-09-25", "status": "Concluded"},
        {"id": 9, "patient_name": "Kevin Black", "phone": "0722001100", "date": "2025-09-27", "status": "Pending"},
        {"id": 10, "patient_name": "Linda Moore", "phone": "0711889900", "date": "2025-09-29", "status": "Concluded"},
        {"id": 11, "patient_name": "Mark Brown", "phone": "0755443322", "date": "2025-09-30", "status": "Pending"},
    ]

    # Search filter
    if query:
        all_appointments = [appt for appt in all_appointments if query.lower() in appt["patient_name"].lower()]

    # Pagination
    paginator = Paginator(all_appointments, 10)  # 10 per page
    page = request.GET.get("page")
    appointments = paginator.get_page(page)

    return render(request, "appointments.html", {
        "appointments": appointments,
        "query": query
    })
    
    
def reports(request):
    query = request.GET.get("q", "")

    # Raw dummy reports
    all_reports = [
        {"id": 1, "title": "Cardiology Summary", "author": "Dr. Jane Doe", "date": "2025-08-01", "status": "Approved"},
        {"id": 2, "title": "Surgery Outcomes", "author": "Dr. Michael Smith", "date": "2025-08-05", "status": "Pending"},
        {"id": 3, "title": "Lab Analysis Q2", "author": "Dr. Emily Davis", "date": "2025-08-10", "status": "Rejected"},
        {"id": 4, "title": "Radiology Findings", "author": "Dr. Chris Johnson", "date": "2025-08-12", "status": "Approved"},
        {"id": 5, "title": "Oncology Research", "author": "Dr. Sarah Wilson", "date": "2025-08-15", "status": "Pending"},
        {"id": 6, "title": "Pediatrics Growth Data", "author": "Dr. Laura Brown", "date": "2025-08-18", "status": "Approved"},
        {"id": 7, "title": "Orthopedics Study", "author": "Dr. Kevin White", "date": "2025-08-20", "status": "Rejected"},
        {"id": 8, "title": "Dermatology Update", "author": "Dr. Mark Green", "date": "2025-08-22", "status": "Pending"},
        {"id": 9, "title": "Neurology Report", "author": "Dr. David Black", "date": "2025-08-25", "status": "Approved"},
        {"id": 10, "title": "Psychiatry Cases", "author": "Dr. Linda Moore", "date": "2025-08-27", "status": "Pending"},
        {"id": 11, "title": "Nutrition Findings", "author": "Dr. Rachel Adams", "date": "2025-08-29", "status": "Approved"},
    ]

    # Search filter
    if query:
        all_reports = [rep for rep in all_reports if query.lower() in rep["title"].lower()]

    # Pagination
    paginator = Paginator(all_reports, 10)
    page = request.GET.get("page")
    reports = paginator.get_page(page)

    return render(request, "reports.html", {
        "reports": reports,
        "query": query
    })
    

def messages_view(request):
    # ----- RAW DATA -----
    messages = [
        {"id": 1, "sender": "Dr. Smith", "subject": "Lab Results", "content": "Your test results are ready.", "status": "unread"},
        {"id": 2, "sender": "Nurse Joy", "subject": "Appointment Reminder", "content": "Don’t forget your appointment tomorrow.", "status": "read"},
        {"id": 3, "sender": "Admin", "subject": "System Update", "content": "New features have been added to the portal.", "status": "unread"},
        {"id": 4, "sender": "Dr. Adams", "subject": "Follow-up", "content": "Please schedule your follow-up visit.", "status": "read"},
        {"id": 5, "sender": "Reception", "subject": "Billing Notice", "content": "Your invoice is available online.", "status": "read"},
        {"id": 6, "sender": "Lab Technician", "subject": "Sample Issue", "content": "Please re-submit your blood sample.", "status": "unread"},
        {"id": 7, "sender": "Dr. Brown", "subject": "Medication Update", "content": "Your prescription has been updated.", "status": "read"},
    ]

    # ----- SEARCH -----
    query = request.GET.get("q")
    if query:
        messages = [
            m for m in messages
            if query.lower() in m["sender"].lower()
            or query.lower() in m["subject"].lower()
            or query.lower() in m["content"].lower()
        ]

    # ----- PAGINATION -----
    paginator = Paginator(messages, 5)  # 5 per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Counts for cards
    unread_count = sum(1 for m in messages if m["status"] == "unread")
    total_messages = len(messages)

    return render(request, "messages.html", {
        "page_obj": page_obj,
        "unread_count": unread_count,
        "total_messages": total_messages,
    })