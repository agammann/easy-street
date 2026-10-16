import json
from pathlib import Path
from fastapi.testclient import TestClient
from backend.exports import export_course
from backend.main import create_app
from backend.workspace import MAX_BACKUP, parse_backup


class NoCalls:
    def generate(self, payload):
        raise AssertionError("Workspace operations must not call a provider")

    verify = generate


def fixture(tmp_path):
    app = create_app(tmp_path, provider=NoCalls())
    client = TestClient(app, base_url="http://127.0.0.1:8000")
    document = client.post("/api/documents/sample").json()
    course = client.post("/api/courses",json={"document_id":document["id"],"title":"Restore me","mode":"demo"}).json()
    course_path = "/api/courses/" + course["id"]
    assert client.post(course_path + "/approve",json={"provider_disclosure_accepted":True}).status_code == 200
    assert client.post(course_path + "/generate",json={"idempotency_key":"workspace-fixture"}).status_code == 200
    course = client.get(course_path).json()
    assert course["sections"]
    return client, course, client.get(course_path + "/export?format=json").content


def test_backup_roundtrip_missing_source_and_reattach(tmp_path):
    _, original, backup = fixture(tmp_path / "first")
    client = TestClient(create_app(tmp_path / "second",provider=NoCalls()),base_url="http://127.0.0.1:8000")
    response = client.post("/api/courses/import",files={"file":("course.json",backup,"application/json")})
    assert response.status_code == 200, response.text
    imported = response.json()
    assert imported["id"] != original["id"] and imported["source_missing"]
    assert len(imported["sections"]) == len(original["sections"])
    assert all(s["support_status"] == "needs_review" for s in imported["sections"])
    path = "/api/courses/" + imported["id"]
    assert client.get(path + "/estimate").status_code == 400
    assert client.get(path + "/export?format=html").status_code == 200
    reexport = client.get(path + "/export?format=json").json()
    assert reexport["source_manifest"]["passages"]
    assert client.post(path + "/source",files={"file":("wrong.txt",b"not the source")}).status_code == 422
    source = Path(__file__).parents[1] / "sample" / "chapter.txt"
    response = client.post(path + "/source",files={"file":("original.txt",source.read_bytes())})
    assert response.status_code == 200, response.text
    assert not response.json()["source_missing"]
    assert client.get("/api/documents/" + original["document_id"]).json()["passages"]
    assert client.get("/api/usage").json()["records"] == []


def test_import_does_not_overwrite_existing_and_rejects_bad_references(tmp_path):
    client, original, backup = fixture(tmp_path)
    copied = client.post("/api/courses/import",files={"file":("course.json",backup)}).json()
    assert copied["id"] != original["id"] and not copied["source_missing"]
    assert client.get("/api/courses/" + original["id"]).json() == original
    bad = json.loads(backup)
    bad["course"]["sections"][0]["evidence"] = [{"passage_id":"unknown","quote":"not source"}]
    assert client.post("/api/courses/import",files={"file":("course.json",json.dumps(bad))}).status_code == 400
    bad = json.loads(backup)
    bad["course"]["sections"].append(bad["course"]["sections"][0])
    assert client.post("/api/courses/import",files={"file":("course.json",json.dumps(bad))}).status_code == 400
    assert len(client.get("/api/courses").json()) == 2


def test_backup_omits_unused_locations_and_roundtrips_all_course_references(tmp_path):
    client, course, _ = fixture(tmp_path)
    document = client.get("/api/documents/" + course["document_id"]).json()
    required = {p["id"] for p in document["passages"]}
    # Keep references required only by each of the three consumers.
    course["outline"]["selected_passage_ids"] = [document["passages"][0]["id"]]
    course["outline"]["modules"][0]["selected_passage_ids"] = [document["passages"][1]["id"]]
    document["passages"].extend({"id":f"unused-{index}", "location":f"Paragraph {index}", "page":None,
        "paragraph":index, "text":"A"} for index in range(10,1010))
    body, _, _ = export_course(course,"json",document)
    assert len(body.encode()) < MAX_BACKUP
    backup = json.loads(body)
    assert {p["id"] for p in backup["source_manifest"]["passages"]} == required
    assert backup["source_manifest"]["sha256"] == document["sha256"]
    imported, missing_source = parse_backup(body.encode())
    assert len(imported["sections"]) == len(course["sections"])
    assert {p["id"] for p in missing_source["source_references"]} == required
    reexport, _, _ = export_course(imported,"json",missing_source)
    assert json.loads(reexport)["source_manifest"] == backup["source_manifest"]


def test_archive_is_reversible_and_version_restore_keeps_current_work(tmp_path):
    client, course, _ = fixture(tmp_path)
    path = "/api/courses/" + course["id"]
    assert client.post(path + "/archive",json={"archived":True}).json()["archived"]
    assert client.post(path + "/archive",json={"archived":False}).json()["archived"] is False
    section = course["sections"][0]
    client.patch(path + "/sections/" + section["id"],json={"body":"My later edit"})
    versions = client.get(path + "/versions").json()
    before_edit = next(v for v in versions if v["reason"] == "Before manual section edit")
    restored = client.post(path + "/restore",json={"version_id":before_edit["id"]})
    assert restored.status_code == 200
    assert restored.json()["sections"][0]["body"] == section["body"]
    latest = client.get(path + "/versions").json()[0]
    assert latest["course"]["sections"][0]["body"] == "My later edit"
    assert client.post(path + "/restore",json={"version_id":999999}).status_code == 404


def test_import_retains_completed_module_progress_and_large_paragraph_locations(tmp_path):
    client, _, _ = fixture(tmp_path)
    source_id = client.get("/api/documents").json()[0]["id"]
    course = client.post("/api/courses",json={"document_id":source_id,"title":"Two modules","mode":"demo","modules":2}).json()
    path = "/api/courses/" + course["id"]
    client.post(path + "/approve",json={"provider_disclosure_accepted":True})
    client.post(path + "/generate",json={"idempotency_key":"two-module-backup"})
    backup = client.get(path + "/export?format=json").json()
    backup["course"]["sections"] = [s for s in backup["course"]["sections"] if s["module_id"] == "module-1"]
    backup["course"]["generated_module_ids"] = ["module-1"]
    backup["source_manifest"]["passages"][0]["paragraph"] = 5002
    response = client.post("/api/courses/import",files={"file":("partial.json",json.dumps(backup))})
    assert response.status_code == 200, response.text
    imported = response.json()
    assert imported["generated_module_ids"] == ["module-1"]
    path = "/api/courses/" + imported["id"]
    client.post(path + "/approve",json={"provider_disclosure_accepted":True})
    job = client.post(path + "/generate",json={"idempotency_key":"import-remaining-module"})
    assert job.status_code == 200, job.text
    completed = client.get(path).json()
    assert completed["generated_module_ids"] == ["module-1","module-2"]
    assert len(completed["sections"]) > len(imported["sections"])
