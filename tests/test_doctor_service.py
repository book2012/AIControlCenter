from core.doctor.service import DoctorService


def test_doctor_service_run():
    doctor = DoctorService()

    result = doctor.run()

    assert "overall" in result
    assert "checks" in result
    assert len(result["checks"]) >= 4


def test_doctor_service_format_text():
    doctor = DoctorService()

    text = doctor.format_text()

    assert "AIControlCenter Doctor" in text
    assert "Overall" in text
