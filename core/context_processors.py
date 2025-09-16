from core.models import Doctor, Patient

def session_info(request):
    role = request.session.get("user_role")
    name = None

    if role == "doctor":
        doctor_id = request.session.get("doctor_id")
        doctor = Doctor.objects.filter(id=doctor_id).first()
        if doctor:
            name = f"Dr. {doctor.name}"
    elif role == "patient":
        patient_id = request.session.get("patient_id")
        patient = Patient.objects.filter(id=patient_id).first()
        if patient:
            name = patient.name

    return {
        "session_role": role,
        "session_name": name,
    }

