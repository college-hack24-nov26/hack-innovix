from app.models import LabResult, MedicalEvent, Medication


def build_timeline(patient_id: int) -> list[dict]:
    items = []
    for ev in MedicalEvent.query.filter_by(patient_id=patient_id).all():
        items.append(
            {
                "date": ev.event_date.isoformat() if ev.event_date else None,
                "type": ev.event_type,
                "title": ev.title,
                "details": ev.details,
                "source": ev.source_note,
                "document_id": ev.document_id,
            }
        )
    for med in Medication.query.filter_by(patient_id=patient_id).all():
        items.append(
            {
                "date": med.created_at.date().isoformat() if med.created_at else None,
                "type": "prescription",
                "title": med.name,
                "details": " ".join(filter(None, [med.dose, med.frequency, med.duration])),
                "source": med.source_note,
                "document_id": med.document_id,
            }
        )
    for lab in LabResult.query.filter_by(patient_id=patient_id).all():
        items.append(
            {
                "date": lab.collected_on.isoformat() if lab.collected_on else (lab.created_at.date().isoformat() if lab.created_at else None),
                "type": "laboratory",
                "title": lab.test_name,
                "details": f"{lab.result_value} {lab.unit or ''}".strip(),
                "source": "Laboratory report",
                "document_id": lab.document_id,
            }
        )
    items.sort(key=lambda x: x.get("date") or "", reverse=True)
    return items
