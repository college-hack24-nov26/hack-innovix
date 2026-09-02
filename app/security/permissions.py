def can_access_patient(user, patient) -> bool:
    if user.role in ("doctor", "admin", "triage"):
        return True
    if user.role == "patient" and user.patient_id == patient.id:
        return True
    return False
