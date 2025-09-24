from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from core.models import HeroSlide, HeroContent, HomeCard, About, Service, BlogPost, PartnerLogo, BlogCategory, Comment, Profile, Patient, Doctor, Appointment, Report, Message, Department
from core.forms import CommentForm, PatientForm, ReportForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings
from django.db.models import Q
from .decorators import session_required
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime, timedelta, time
from django.http import JsonResponse


def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        role = request.POST.get("user_role", "").strip().lower()
        phone = request.POST.get("phone")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect("signup")

        user = User.objects.create_user(username=username, email=email, password=password)
        profile, created = Profile.objects.get_or_create(user=user)

        if role == "doctor":
            dept_id = request.POST.get("department")
            if not dept_id:  # 👈 safeguard: department is missing
                messages.error(request, "Please select a department.")
                user.delete()  # cleanup created user
                return redirect("signup")

            department = Department.objects.filter(id=dept_id).first()
            if not department:  # 👈 safeguard: invalid department
                messages.error(request, "Invalid department selected.")
                user.delete()
                return redirect("signup")

            profile.role = "pending"  # waiting admin approval
            doctor = Doctor.objects.create(
                name=username,
                phone=phone,
                email=email,
                department=department
            )
            hospital_id = doctor.doctor_id

        else:  # patient
            profile.role = "patient"
            patient = Patient.objects.create(
                name=username,
                phone=phone,
                age=0,
                gender="M"  # could make this dynamic later
            )
            profile.hospital_id = patient.patient_id
            profile.save()
            hospital_id = patient.patient_id

        profile.save()

        request.session["new_hospital_id"] = hospital_id
        return redirect("login")

    # GET request
    departments = Department.objects.all().order_by("name")
    return render(request, "signup.html", {"departments": departments})



def login_view(request):
    prefill_id = request.session.pop("new_hospital_id", "")  # remove after reading
    if request.method == "POST":
        hospital_id = request.POST.get("hospital_id", "").strip()

        # Try Doctor login
        doctor = Doctor.objects.filter(doctor_id=hospital_id).first()
        if doctor:
            if not doctor.approved:
                messages.error(request, "Your account is pending approval. Please wait for admin verification.")
                return redirect("login")

            # ensure profile role matches approval
            profile = Profile.objects.filter(user__username=doctor.name).first()
            if profile and profile.role != "doctor":
                profile.role = "doctor"
                profile.save()

            request.session["user_role"] = "doctor"
            request.session["doctor_id"] = doctor.id
            request.session["username"] = doctor.name   # 👈 for navbar
            messages.success(request, f"Welcome Dr. {doctor.name}")
            return redirect("dashboard")

        # Try Patient login
        patient = Patient.objects.filter(patient_id=hospital_id).first()
        if patient:
            request.session["user_role"] = "patient"
            request.session["patient_id"] = patient.id
            request.session["username"] = patient.name
            messages.success(request, f"Welcome {patient.name}")
            return redirect("dashboard")

        # If no match
        messages.error(request, "Invalid Doctor ID or Patient ID.")

    return render(request, "login.html", {"prefill_id": prefill_id})




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

        try:
            # Context for both templates
            context = {
                "name": name,
                "email": email,
                "message": message,
                "year": timezone.now().year,
            }

            # -------- Email 1: Notify Admin --------
            subject_admin = f"📩 New Contact Form Submission from {name}"
            html_admin = render_to_string("emails/contact_notification.html", context)
            text_admin = strip_tags(html_admin)

            msg_admin = EmailMultiAlternatives(
                subject=subject_admin,
                body=text_admin,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.EMAIL_HOST_USER],  # Admin inbox
                reply_to=[email],
            )
            msg_admin.attach_alternative(html_admin, "text/html")
            msg_admin.send()

            # -------- Email 2: Confirmation to Visitor --------
            subject_user = "✅ Covenant Hospital - We Received Your Message"
            html_user = render_to_string("emails/contact_confirmation.html", context)
            text_user = strip_tags(html_user)

            msg_user = EmailMultiAlternatives(
                subject=subject_user,
                body=text_user,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],  # Visitor’s email
            )
            msg_user.attach_alternative(html_user, "text/html")
            msg_user.send()

            messages.success(request, "Your message has been sent successfully! Please check your email for confirmation.")

        except Exception as e:
            messages.error(request, f"Error sending message: {e}")

        return redirect("contact")

    return render(request, "contact.html", {"partners": partners})


@session_required
def dashboard(request):
    role = request.session.get("user_role")

    doctor = None
    patient = None

    if role == "doctor":
        doctor_id = request.session.get("doctor_id")
        doctor = Doctor.objects.filter(id=doctor_id).first()
        if not doctor:
            messages.error(request, "Doctor account not linked properly.")
            return render(request, "dashboard/dashboard.html", {})

        appointments = Appointment.objects.filter(doctor=doctor).order_by("-date")[:5]
        patients = (
            Patient.objects.filter(appointments__doctor=doctor)
            .distinct()
            .order_by("-date_added")[:5]
            .prefetch_related("appointments__doctor")
        )
        reports = Report.objects.filter(author=doctor).order_by("-date")[:5]
        messages_qs = Message.objects.filter(recipient_doctor=doctor).order_by("-date_sent")[:5]

    elif role == "patient":
        patient_id = request.session.get("patient_id")
        patient = Patient.objects.filter(id=patient_id).first()
        if not patient:
            messages.error(request, "Patient account not linked properly.")
            return render(request, "dashboard/dashboard.html", {})

        appointments = patient.appointments.all().order_by("-date")[:5]
        patients = Patient.objects.filter(id=patient.id).prefetch_related("appointments__doctor").order_by("-date_added")
        reports = patient.reports.all().order_by("-date")[:5]
        messages_qs = []  # 👈 no messages for patients

    else:  # admin/staff
        appointments = Appointment.objects.all().order_by("-date")[:5]
        patients = Patient.objects.all().order_by("-date_added")[:5]
        reports = Report.objects.all().order_by("-date")[:5]
        messages_qs = Message.objects.all().order_by("-date_sent")[:5]

    return render(request, "dashboard/dashboard.html", {
        "appointments": appointments,
        "patients": patients,
        "reports": reports,
        "messages": messages_qs,
        "session_role": role,   # 👈 role for template
        "doctor": doctor,       # 👈 doctor object if role == doctor
        "patient": patient,     # 👈 patient object if role == patient
    })


# ------------------ PATIENTS ------------------
@session_required
def patients(request):
    role = request.session.get("user_role")
    q = request.GET.get("q", "").strip()

    if role == "doctor":
        doctor_id = request.session.get("doctor_id")
        doctor = Doctor.objects.filter(id=doctor_id).first()
        patients_list = (
            Patient.objects.filter(appointments__doctor=doctor)
            .distinct()
            .order_by("-date_added")
        )

    elif role == "patient":
        patient_id = request.session.get("patient_id")
        # join with appointment so we can show doctor + date
        patients_list = (
            Patient.objects.filter(id=patient_id)
            .prefetch_related("appointments__doctor")
            .order_by("-date_added")
        )

    else:  # admin
        patients_list = Patient.objects.all().order_by("-date_added")

    if q:
        patients_list = patients_list.filter(
            Q(name__icontains=q)
            | Q(phone__icontains=q)
        )

    paginator = Paginator(patients_list, 10)
    page_number = request.GET.get("page")
    patients_page = paginator.get_page(page_number)

    return render(
        request,
        "dashboard/patients.html",
        {
            "patients_page": patients_page,
            "query": q,
            "role": role,  # pass role to template for safety
        },
    )

def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    role = request.session.get("user_role", None)  # doctor or patient
    return render(request, "dashboard/patient_detail.html", {
        "patient": patient,
        "role": role
    })

# ------------------ APPOINTMENTS ------------------
@session_required
def appointments(request):
    role = request.session.get("user_role")
    q = request.GET.get("q", "").strip()

    if role == "doctor":
        doctor_id = request.session.get("doctor_id")
        doctor = Doctor.objects.filter(id=doctor_id).first()
        appointments_list = Appointment.objects.filter(doctor=doctor).select_related("patient", "doctor").order_by("-date")

    elif role == "patient":
        patient_id = request.session.get("patient_id")
        patient = Patient.objects.filter(id=patient_id).first()
        appointments_list = Appointment.objects.filter(patient=patient).select_related("patient", "doctor").order_by("-date")

    else:  # admin
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


def appointment_detail(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    role = request.session.get("user_role", None)  # if you’re using role in session

    return render(request, "dashboard/appointment_detail.html", {
        "appointment": appointment,
        "role": role,
    })



# ------------------ REPORTS ------------------
@session_required
def reports(request):
    role = request.session.get("user_role")
    q = request.GET.get("q", "").strip()

    if role == "doctor":
        doctor_id = request.session.get("doctor_id")
        doctor = Doctor.objects.filter(id=doctor_id).first()
        reports_list = Report.objects.filter(author=doctor).select_related("author", "patient").order_by("-date")

    elif role == "patient":
        patient_id = request.session.get("patient_id")
        patient = Patient.objects.filter(id=patient_id).first()
        reports_list = Report.objects.filter(patient=patient).select_related("author", "patient").order_by("-date")

    else:  # admin
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


@session_required
def create_report(request, appointment_id):
    role = request.session.get("user_role")
    if role != "doctor":
        messages.error(request, "Only doctors can generate reports.")
        return redirect("dashboard")

    doctor_id = request.session.get("doctor_id")
    doctor = Doctor.objects.filter(id=doctor_id).first()
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=doctor)

    if hasattr(appointment, "report"):  # already has a report
        messages.warning(request, "This appointment already has a report.")
        return redirect("report_detail", report_id=appointment.report.id)

    if request.method == "POST":
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.author = doctor
            report.patient = appointment.patient
            report.appointment = appointment
            report.save()

            # mark appointment as concluded
            appointment.status = "concluded"
            appointment.save()

            messages.success(request, "Report created successfully.")
            return redirect("report_detail", report_id=report.id)
    else:
        form = ReportForm()

    return render(request, "dashboard/create_report.html", {
        "form": form,
        "appointment": appointment
    })


def report_detail(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    role = request.session.get("user_role")
    return render(request, "dashboard/report_detail.html", {"report": report, "role": role})


# ------------------ MESSAGES ------------------
@session_required
def messages_view(request):
    role = request.session.get("user_role")
    q = request.GET.get("q", "").strip()

    if role == "doctor":
        doctor_id = request.session.get("doctor_id")
        doctor = Doctor.objects.filter(id=doctor_id).first()
        messages_list = Message.objects.filter(recipient_doctor=doctor).order_by("-date_sent")

    elif role == "patient":
        patient_id = request.session.get("patient_id")
        patient = Patient.objects.filter(id=patient_id).first()
        

    else:  # admin/staff
        messages_list = Message.objects.all().order_by("-date_sent")

    if q:
        messages_list = messages_list.filter(
            Q(sender__icontains=q) |
            Q(subject__icontains=q) |
            Q(content__icontains=q)
        )

    paginator = Paginator(messages_list, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    unread_count = messages_list.filter(status="unread").count()
    total_messages = messages_list.count()

    return render(request, "dashboard/messages.html", {
        "page_obj": page_obj,
        "unread_count": unread_count,
        "total_messages": total_messages,
        "query": q
    })
    

@session_required
def messages_all(request):
    role = request.session.get("user_role")
    q = request.GET.get("q", "").strip()

    if role == "doctor":
        doctor_id = request.session.get("doctor_id")
        doctor = Doctor.objects.filter(id=doctor_id).first()
        messages_list = Message.objects.filter(recipient_doctor=doctor).order_by("-date_sent")
    elif role == "patient":
        patient_id = request.session.get("patient_id")
        patient = Patient.objects.filter(id=patient_id).first()
        messages_list = Message.objects.filter(recipient_patient=patient).order_by("-date_sent")
    else:
        messages_list = Message.objects.all().order_by("-date_sent")

    if q:
        messages_list = messages_list.filter(
            Q(sender__icontains=q) |
            Q(subject__icontains=q) |
            Q(content__icontains=q)
        )

    paginator = Paginator(messages_list, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    unread_count = Message.objects.filter(status="unread").count() if role != "doctor" else messages_list.filter(status="unread").count()
    total_messages = messages_list.count()

    return render(request, "dashboard/messages_list.html", {
        "page_obj": page_obj,
        "unread_count": unread_count,
        "total_messages": total_messages,
        "query": q,
        "view_type": "all",
        "session_role": role,
    })


@session_required
def messages_unread(request):
    role = request.session.get("user_role")
    q = request.GET.get("q", "").strip()

    if role == "doctor":
        doctor_id = request.session.get("doctor_id")
        doctor = Doctor.objects.filter(id=doctor_id).first()
        messages_list = Message.objects.filter(recipient_doctor=doctor, status="unread").order_by("-date_sent")
    elif role == "patient":
        patient_id = request.session.get("patient_id")
        patient = Patient.objects.filter(id=patient_id).first()
        messages_list = Message.objects.filter(recipient_patient=patient, status="unread").order_by("-date_sent")
    else:
        messages_list = Message.objects.filter(status="unread").order_by("-date_sent")

    if q:
        messages_list = messages_list.filter(
            Q(sender__icontains=q) |
            Q(subject__icontains=q) |
            Q(content__icontains=q)
        )

    paginator = Paginator(messages_list, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    unread_count = messages_list.count()
    total_messages = Message.objects.all().count()

    return render(request, "dashboard/messages_list.html", {
        "page_obj": page_obj,
        "unread_count": unread_count,
        "total_messages": total_messages,
        "query": q,
        "view_type": "unread",
        "session_role": role,
    })

@session_required
def message_detail(request, pk):
    message = get_object_or_404(Message, pk=pk)
    return render(request, "dashboard/message_detail.html", {
        "message": message
    })


#------ PROFILE VIEW ------
@session_required
def profile(request):
    role = request.session.get("user_role")
    context = {"session_role": role}

    if role == "doctor":
        doctor_id = request.session.get("doctor_id")
        doctor = Doctor.objects.filter(id=doctor_id).first()
        context["doctor"] = doctor

    elif role == "patient":
        patient_id = request.session.get("patient_id")
        patient = Patient.objects.filter(id=patient_id).first()
        context["patient"] = patient

    return render(request, "dashboard/profile.html", context)


@session_required
def add_patient(request):
    role = request.session.get("user_role")

    if role != "doctor":
        messages.error(request, "Only doctors can add patients.")
        return redirect("dashboard")

    doctor_id = request.session.get("doctor_id")
    doctor = Doctor.objects.filter(id=doctor_id).first()

    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        age = request.POST.get("age")
        gender = request.POST.get("gender")

        if not all([name, phone, age, gender]):
            messages.error(request, "Please fill in all required fields.")
            return render(request, "dashboard/add_patient.html")

        # Create patient
        patient = Patient.objects.create(
            name=name,
            phone=phone,
            age=age,
            gender=gender
        )

        # Link patient to doctor via first appointment
        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            date=timezone.now(),
            status="pending"
        )

        messages.success(request, f"Patient {patient.name} added successfully!")

        # Fetch updated patients list for this doctor
        patients_list = Patient.objects.filter(
            appointments__doctor=doctor
        ).distinct().order_by("-date_added")

        # Pagination
        paginator = Paginator(patients_list, 10)
        page_number = request.GET.get("page") or 1
        patients_page = paginator.get_page(page_number)

        # Render patients page with new patient highlighted
        return render(request, "dashboard/patients.html", {
            "patients_page": patients_page,
            "role": role,
            "new_patient": patient,  # template can highlight this
            "query": "",
        })

    return render(request, "dashboard/add_patient.html")


@session_required
def add_appointment(request):
    role = request.session.get("user_role")
    if role != "doctor":
        messages.error(request, "Only doctors can add appointments.")
        return redirect("dashboard")

    doctor_id = request.session.get("doctor_id")
    doctor = Doctor.objects.filter(id=doctor_id).first()

    if request.method == "POST":
        name = request.POST.get("patient_name")
        phone = request.POST.get("phone")
        age = request.POST.get("age")
        gender = request.POST.get("gender")
        date = request.POST.get("date")

        # Check if patient exists
        patient = Patient.objects.filter(name__iexact=name, phone=phone).first()
        if not patient:
            patient = Patient.objects.create(
                name=name,
                phone=phone,
                age=age,
                gender=gender
            )

        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            date=date,
            status="pending"
        )

        messages.success(request, f"Appointment for {patient.name} added successfully!")
        return redirect("appointments")

    return render(request, "dashboard/add_appointment.html")


@session_required
def available_slots(request):
    doctor_id = request.GET.get("doctor")
    date_str = request.GET.get("date")

    if not doctor_id or not date_str:
        return JsonResponse({"slots": []})

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"slots": []})

    doctor = Doctor.objects.filter(id=doctor_id).first()
    if not doctor:
        return JsonResponse({"slots": []})

    # Working hours: 9AM–5PM
    start_time = time(9, 0)
    end_time = time(17, 0)
    slot_duration = timedelta(minutes=30)

    slots = []
    current = datetime.combine(date_obj, start_time)
    end = datetime.combine(date_obj, end_time)

    while current < end:
        slots.append(current.strftime("%H:%M"))
        current += slot_duration

    # Already booked slots
    booked_times = Appointment.objects.filter(
        doctor=doctor,
        date__date=date_obj,
        status__in=["pending", "concluded"]
    ).values_list("date", flat=True)

    booked_set = {dt.strftime("%H:%M") for dt in booked_times}

    available = [s for s in slots if s not in booked_set]

    return JsonResponse({"slots": available})

@session_required
def book_appointment(request):
    role = request.session.get("user_role")

    # Only patients can book
    if role != "patient":
        messages.error(request, "You must be logged in as a patient to book an appointment.")
        return redirect("login")

    patient_id = request.session.get("patient_id")
    patient = Patient.objects.filter(id=patient_id).first()

    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        age = request.POST.get("age")
        gender = request.POST.get("gender")
        department_id = request.POST.get("department")
        doctor_id = request.POST.get("doctor")
        issue = request.POST.get("issue")
        date_str = request.POST.get("appointment_date")
        time_str = request.POST.get("appointment_time")

        # Combine into one datetime
        try:
            appointment_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            messages.error(request, "Invalid date/time format.")
            return redirect("book_appointment")

        # Create patient if not exists
        if not patient:
            patient = Patient.objects.create(
                name=name,
                phone=phone,
                age=age,
                gender=gender
            )
            request.session["patient_id"] = patient.id

        # Fetch doctor linked to department
        department = Department.objects.filter(id=department_id).first()
        doctor = Doctor.objects.filter(id=doctor_id, department=department).first()
        if not doctor:
            messages.error(request, "Selected doctor is not valid for the chosen department.")
            return redirect("book_appointment")
        
         # 🔒 Check if doctor already has appointment at that datetime
        conflict = Appointment.objects.filter(
            doctor=doctor,
            date=appointment_datetime,
            status__in=["pending", "concluded"]  # avoid cancelled ones
        ).exists()

        if conflict:
            messages.error(request, f"Dr. {doctor.name} is not available at {appointment_datetime.strftime('%Y-%m-%d %H:%M')}. Please choose another time.")
            return redirect("book_appointment")

        # Create appointment
        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            date=appointment_datetime,
            status="pending"
        )

        messages.success(request, f"Appointment booked successfully with Dr. {doctor.name}  at {appointment_datetime.strftime('%Y-%m-%d %H:%M')}!")
        return redirect("appointments")  # show in portal

    # GET request: show form
    departments = Department.objects.filter(doctor__isnull=False).distinct()
    doctors = Doctor.objects.select_related("department").all()

    return render(request, "book_appointment.html", {
        "patient": patient,
        "departments": departments,
        "doctors": doctors,
    })

