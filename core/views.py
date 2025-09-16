from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from core.models import HeroSlide, HeroContent, HomeCard, About, Service, BlogPost, PartnerLogo, BlogCategory, Comment, Profile, Patient, Doctor, Appointment, Report, Message
from core.forms import CommentForm, PatientForm
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

#LOGIN VIEW
def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        role = request.POST.get("user_role", "").strip().lower()

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect("signup")

        user = User.objects.create_user(username=username, email=email, password=password)
        
        # ✅ Ensure Profile exists
        profile, created = Profile.objects.get_or_create(user=user)

        # ✅ Role handling
        if role == "doctor":
            profile.role = "pending"
            doctor = Doctor.objects.create(
                name=username,
                specialty="General",
                department="General",
                approved=False,
                email=email
            )
            hospital_id = doctor.doctor_id   # assign doctor ID
        else:
            profile.role = "patient"
            patient = Patient.objects.create(
            name=username,
            phone="N/A",    # or capture from signup form later
            age=0,          # or optional field on signup
            gender="M"      # or optional field on signup
            )
            # link hospital_id for login
            profile.hospital_id = patient.patient_id
            profile.save()
            hospital_id = patient.patient_id   # assign patient ID


        profile.save()

        # ✅ Send welcome email
        if email:
            try:
                if role == "doctor":
                    subject = "Welcome to Covenant Hospital - Pending Approval"
                    message = (
                        f"Hello Dr. {username},\n\n"
                        f"Thank you for registering with Covenant Hospital.\n"
                        f"Your account is currently pending approval by the admin team.\n\n"
                        f"Once approved, you will be able to log in using your Doctor ID: {doctor.doctor_id}\n\n"
                        f"We will notify you once your account is approved.\n\n"
                        f"Regards,\nCovenant Hospital Admin"
                    )
                else:  # patient
                    subject = "Welcome to Covenant Hospital"
                    message = (
                        f"Hello {username},\n\n"
                        f"Thank you for registering with Covenant Hospital.\n"
                        f"You can now log in using your Patient ID: {profile.hospital_id}\n\n"
                        f"Regards,\nCovenant Hospital Admin"
                    )

                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=True,
                )
            except Exception as e:
                messages.warning(request, f"⚠️ Account created, but email could not be sent: {e}")

         # ✅ Role-specific success messages shown on login page
        if role == "doctor":
            messages.success(
                request,
                mark_safe(
                    f"🎉 Account created successfully for Dr. {username}! "
                    f"Your Doctor ID is <strong style='color:maroon;'>{doctor.doctor_id}</strong>. "
                    f"You will be able to log in once approved by the admin."
                )
            )
        else:
            messages.success(
                request,
                mark_safe(
                    f"🎉 Account created successfully for {username}! "
                    f"Your Patient ID is <strong style='color:maroon;'>{profile.hospital_id}</strong>. "
                    f"You can now log in immediately using this ID."
                )
            )
            request.session["new_hospital_id"] = hospital_id
        return redirect("login")

    return render(request, "signup.html")

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


@session_required
def dashboard(request):
    role = request.session.get("user_role")

    if role == "doctor":
        doctor_id = request.session.get("doctor_id")
        doctor = Doctor.objects.filter(id=doctor_id).first()
        if not doctor:
            messages.error(request, "Doctor account not linked properly.")
            return render(request, "dashboard/dashboard.html", {})

        appointments = Appointment.objects.filter(doctor=doctor).order_by("-date")[:5]
        patients = Patient.objects.filter(appointments__doctor=doctor).distinct().order_by("-date_added")[:5]
        reports = Report.objects.filter(author=doctor).order_by("-date")[:5]
        messages_qs = Message.objects.filter(recipient_doctor=doctor).order_by("-date_sent")[:5]

    elif role == "patient":
        patient_id = request.session.get("patient_id")
        patient = Patient.objects.filter(id=patient_id).first()
        if not patient:
            messages.error(request, "Patient account not linked properly.")
            return render(request, "dashboard/dashboard.html", {})

        appointments = patient.appointments.all().order_by("-date")[:5]
        # tailor "patients" to be just the current patient with doctor + date info
        patients = Patient.objects.filter(id=patient.id).select_related().order_by("-date_added")
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
        "session_role": role,   # pass role to template
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

def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
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
        department = request.POST.get("department")
        doctor_id = request.POST.get("doctor")
        issue = request.POST.get("issue")
        appointment_date = request.POST.get("date")  # optional: user picks date/time

        # Create patient if not exists
        if not patient:
            patient = Patient.objects.create(
                name=name,
                phone=phone,
                age=age,
                gender=gender
            )
            request.session["patient_id"] = patient.id

        # Fetch doctor
        doctor = Doctor.objects.filter(id=doctor_id, department=department).first()
        if not doctor:
            messages.error(request, "Selected doctor is not valid for the chosen department.")
            return redirect("book_appointment")

        # Create appointment
        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            date=timezone.now() if not appointment_date else appointment_date,
            status="pending"
        )

        messages.success(request, f"Appointment booked successfully with Dr. {doctor.name}!")
        return redirect("appointments")  # show in portal

    # GET request: show form
    departments = Doctor.objects.values_list("department", flat=True).distinct()
    doctors = Doctor.objects.all()

    return render(request, "book_appointment.html", {
        "patient": patient,
        "departments": departments,
        "doctors": doctors,
    })

