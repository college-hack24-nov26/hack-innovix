from datetime import datetime

from app.extensions import db
from app.models import FHIRRecord, Patient
from app.services.audit_service import log_action


def export_patient_bundle(patient: Patient, user_id=None) -> dict:
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": str(patient.id),
                    "name": [{"family": patient.last_name, "given": [patient.first_name]}],
                    "gender": patient.gender,
                    "identifier": [
                        {"system": "hospital", "value": patient.hospital_patient_id},
                        {"system": "abha", "value": patient.abha_id},
                    ],
                }
            }
        ],
    }
    rec = FHIRRecord(patient_id=patient.id, payload=bundle)
    db.session.add(rec)
    db.session.commit()
    log_action(user_id, "fhir_export", "patient", patient.id)
    return bundle
