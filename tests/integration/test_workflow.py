"""User-facing offline workflow checks; no paid provider requests are made."""

import json


def make_course(client, *, approved=False, questions=2):
    document = client.post("/api/documents/sample").json()
    response = client.post("/api/courses", json={
        "document_id": document["id"], "title": "Evidence review course",
        "difficulty": "introductory", "modules": 1, "assignments": 1,
        "quizzes": 1, "questions_per_quiz": questions, "mode": "demo",
    })
    assert response.status_code in (200, 201), response.text
    course = response.json()
    if approved:
        response = client.post(f"/api/courses/{course['id']}/approve", json={"provider_disclosure_accepted": True})
        assert response.status_code == 200, response.text
        course = response.json()
    return document, course


def generate(client, course, *, key="initial-generation", section_id=None):
    payload = {"idempotency_key": key}
    if section_id:
        payload["section_id"] = section_id
    response = client.post(f"/api/courses/{course['id']}/generate", json=payload)
    assert response.status_code in (200, 201, 202), response.text
    job = client.get(f"/api/jobs/{response.json()['id']}").json()
    assert job["status"] == "complete", job
    return client.get(f"/api/courses/{course['id']}").json(), job


def test_document_cache_and_text_locations(client):
    source = b"A locally authored lesson\n\nA sample can be selected from a population.\n\nA larger sample does not remove a biased selection method. Selection matters because some members may have no chance of inclusion."
    first = client.post("/api/documents", files={"file": ("lesson.txt", source, "text/plain")})
    second = client.post("/api/documents", files={"file": ("renamed.txt", source, "text/plain")})
    assert first.status_code in (200, 201), first.text
    assert second.status_code in (200, 201), second.text
    a, b = first.json(), second.json()
    assert a["id"] == b["id"]
    assert a["passages"] == b["passages"]
    assert a["passages"]
    assert all(p["page"] is None for p in a["passages"])
    assert all("page" not in p["location"].lower() for p in a["passages"])


def test_upload_rejects_disguised_pdf_and_empty_text(client):
    for name, content, mime in [("bad.pdf", b"This is not PDF data", "application/pdf"), ("empty.txt", b"   \n\t", "text/plain"), ("code.exe", b"MZ", "application/octet-stream")]:
        response = client.post("/api/documents", files={"file": (name, content, mime)})
        assert 400 <= response.status_code < 500, response.text


def test_counts_and_demo_source_are_explicitly_bounded(client):
    document, course = make_course(client)
    payload = {"document_id": document["id"], "title": "Bounded course", "difficulty": "introductory", "modules": 7, "assignments": 1, "quizzes": 1, "questions_per_quiz": 1, "mode": "demo"}
    response = client.post("/api/courses", json=payload)
    assert 400 <= response.status_code < 500
    uploaded = client.post("/api/documents", files={"file": ("own.txt", b"Private chapter. Sampling means selecting a subset from a population. A biased selection process can systematically miss people. A larger sample alone does not correct that selection process.", "text/plain")}).json()
    payload.update(document_id=uploaded["id"], modules=1)
    response = client.post("/api/courses", json=payload)
    assert 400 <= response.status_code < 500


def test_outline_approval_gate_and_disclosure(client):
    _, course = make_course(client)
    generated = client.post(f"/api/courses/{course['id']}/generate", json={"idempotency_key": "too-early"})
    assert 400 <= generated.status_code < 500
    refused = client.post(f"/api/courses/{course['id']}/approve", json={"provider_disclosure_accepted": False})
    assert 400 <= refused.status_code < 500
    assert not client.get(f"/api/courses/{course['id']}").json()["outline_approved"]


def test_outline_change_revokes_approval(client):
    _, course = make_course(client, approved=True)
    changed = client.patch(f"/api/courses/{course['id']}/outline", json={"module_title": "Revised module"})
    assert changed.status_code == 200, changed.text
    assert changed.json()["outline_approved"] is False
    generated = client.post(f"/api/courses/{course['id']}/generate", json={"idempotency_key": "approval-was-revoked"})
    assert 400 <= generated.status_code < 500


def test_complete_demo_has_resolving_evidence_and_requested_counts(client):
    document, course = make_course(client, approved=True, questions=3)
    generated, job = generate(client, course)
    sections = generated["sections"]
    assert len([s for s in sections if s["kind"] == "assignment"]) == 1
    assert len([s for s in sections if s["kind"] == "quiz"]) == 3
    assert {"objectives", "introduction", "readings", "notes", "announcement", "rubric"} <= {s["kind"] for s in sections}
    passages = {p["id"]: p for p in document["passages"]}
    for section in sections:
        if section["kind"] in ("notes", "assignment", "quiz"):
            assert section["evidence"], section
        for evidence in section["evidence"]:
            assert evidence["passage_id"] in passages
            assert evidence["quote"] and evidence["quote"] in passages[evidence["passage_id"]]["text"]
    assert job["estimated_max_usd"] == 0


def test_duplicate_submission_returns_original_job(client):
    _, course = make_course(client, approved=True)
    _, first = generate(client, course, key="stable-client-key")
    response = client.post(f"/api/courses/{course['id']}/generate", json={"idempotency_key": "stable-client-key"})
    assert response.status_code in (200, 201, 202)
    assert response.json()["id"] == first["id"]
    assert client.get("/api/usage").json()["budget"]["spent_usd"] == 0


def test_manual_edit_survives_other_section_regeneration_and_reload(client):
    _, course = make_course(client, approved=True)
    course, _ = generate(client, course)
    notes = next(s for s in course["sections"] if s["kind"] == "notes")
    announcement = next(s for s in course["sections"] if s["kind"] == "announcement")
    marker = "My saved note is retained across an unrelated regeneration."
    response = client.patch(f"/api/courses/{course['id']}/sections/{notes['id']}", json={"body": marker})
    assert response.status_code == 200, response.text
    course, _ = generate(client, course, key="regen-announcement", section_id=announcement["id"])
    updated = next(s for s in course["sections"] if s["id"] == notes["id"])
    assert updated["body"] == marker
    assert updated["edited"] is True
    assert updated["support_status"] == "needs_review"


def test_regeneration_keeps_prior_manual_edit_in_version_history(client):
    _, course = make_course(client, approved=True)
    course, _ = generate(client, course)
    notes = next(s for s in course["sections"] if s["kind"] == "notes")
    marker = "An earlier manual version remains recoverable."
    changed = client.patch(f"/api/courses/{course['id']}/sections/{notes['id']}", json={"body": marker})
    assert changed.status_code == 200
    generate(client, course, key="regen-notes", section_id=notes["id"])
    history = client.get(f"/api/courses/{course['id']}/versions").json()
    assert any(any(s["body"] == marker for s in v["course"]["sections"]) for v in history)


def test_reorder_requires_exact_section_set(client):
    _, course = make_course(client, approved=True)
    course, _ = generate(client, course)
    ids = [s["id"] for s in course["sections"]]
    rejected = client.post(f"/api/courses/{course['id']}/reorder", json={"section_ids": [ids[0]] * len(ids)})
    assert 400 <= rejected.status_code < 500
    response = client.post(f"/api/courses/{course['id']}/reorder", json={"section_ids": list(reversed(ids))})
    assert response.status_code == 200, response.text
    assert [s["id"] for s in response.json()["sections"]] == list(reversed(ids))


def test_export_separation_escape_and_source_exclusion(client):
    document, course = make_course(client, approved=True)
    course, _ = generate(client, course)
    quiz = next(s for s in course["sections"] if s["kind"] == "quiz")
    answer = "ANSWER_ONLY_CANARY_235819"
    explanation = "EXPLANATION_ONLY_CANARY_947281"
    dangerous = '<script>alert("course-render")</script>'
    changed = client.patch(f"/api/courses/{course['id']}/sections/{quiz['id']}", json={"answer": answer, "explanation": explanation, "body": dangerous})
    assert changed.status_code == 200
    learner = client.get(f"/api/courses/{course['id']}/export?format=html")
    answers = client.get(f"/api/courses/{course['id']}/export?format=answers")
    backup = client.get(f"/api/courses/{course['id']}/export?format=json")
    assert all(r.status_code == 200 for r in (learner, answers, backup))
    assert answer not in learner.text and explanation not in learner.text
    assert answer in answers.text and explanation in answers.text
    assert dangerous not in learner.text and "&lt;script&gt;" in learner.text
    data = backup.json()
    assert "passages" not in data and "api_key" not in json.dumps(data).lower()
    for passage in document["passages"]:
        if len(passage["text"]) > 200:
            assert passage["text"] not in backup.text


def test_untrusted_origin_and_host_cannot_use_local_api(client):
    response = client.post("/api/documents/sample", headers={"Origin": "https://attacker.example"})
    assert response.status_code in (400, 403)
    response = client.get("/api/config", headers={"Host": "attacker.example"})
    assert response.status_code in (400, 403)
    response = client.post("/api/documents/sample", headers={"Origin": "http://localhost:5173"})
    assert response.status_code in (200, 201)



def minimal_pdf(page_texts):
    """Build a small original readable PDF without an extra test dependency."""
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b""]
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_ids = []
    for text in page_texts:
        page_id = len(objects) + 1
        stream_id = page_id + 1
        page_ids.append(page_id)
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents {stream_id} 0 R >>".encode())
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT /F1 10 Tf 30 750 Td ({escaped}) Tj ET".encode("ascii")
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[1] = f"<< /Type /Pages /Count {len(page_ids)} /Kids [{kids}] >>".encode()
    pdf = b"%PDF-1.4\n"
    offsets = [0]
    for i, content in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf += f"{i} 0 obj\n".encode() + content + b"\nendobj\n"
    xref_at = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    pdf += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
    pdf += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n".encode()
    return pdf


def test_readable_pdf_has_real_stable_page_references(client):
    content = minimal_pdf([
        "Sampling is selecting a subset from a population. The method of selection affects which people can be represented.",
        "A sample can be larger yet still biased. A larger sample does not remove a selection method that systematically misses people.",
    ])
    response = client.post("/api/documents", files={"file": ("two-pages.pdf", content, "application/pdf")})
    assert response.status_code in (200, 201), response.text
    document = response.json()
    assert {p["page"] for p in document["passages"]} == {1, 2}
    assert all(f"Page {p['page']}" in p["location"] for p in document["passages"])
    repeated = client.post("/api/documents", files={"file": ("two-pages.pdf", content, "application/pdf")}).json()
    assert [p["id"] for p in document["passages"]] == [p["id"] for p in repeated["passages"]]
    assert any("images" in w.lower() for w in document["warnings"])


def test_saved_edits_order_and_versions_survive_application_restart(client, tmp_path):
    from fastapi.testclient import TestClient
    from backend.main import create_app

    _, course = make_course(client, approved=True)
    course, _ = generate(client, course)
    notes = next(s for s in course["sections"] if s["kind"] == "notes")
    marker = "This saved note survives a fresh application instance."
    changed = client.patch(f"/api/courses/{course['id']}/sections/{notes['id']}", json={"body": marker})
    assert changed.status_code == 200
    ids = list(reversed([s["id"] for s in course["sections"]]))
    assert client.post(f"/api/courses/{course['id']}/reorder", json={"section_ids": ids}).status_code == 200
    with TestClient(create_app(data_dir=tmp_path, budget_limit=0.01), base_url="http://127.0.0.1:8000") as restarted:
        restored = restarted.get(f"/api/courses/{course['id']}").json()
        assert [s["id"] for s in restored["sections"]] == ids
        assert next(s for s in restored["sections"] if s["id"] == notes["id"])["body"] == marker
        history = restarted.get(f"/api/courses/{course['id']}/versions").json()
        assert history
        assert restarted.get(f"/api/documents/{course['document_id']}").status_code == 200


def test_streamed_upload_limit_and_sanitized_validation_errors(client):
    response = client.post("/api/documents", content=iter([b"x" * (1024 * 1024)] * 16), headers={"Content-Type": "application/octet-stream"})
    assert response.status_code == 413, response.text
    secret = "private-input-validation-canary"
    rejected = client.post("/api/courses", json={"document_id": secret, "title": secret, "mode": "invalid-mode"})
    assert rejected.status_code == 422
    assert secret not in rejected.text


def test_fetch_metadata_blocks_cross_site_requests_without_origin(client):
    response = client.post("/api/documents/sample", headers={"Sec-Fetch-Site": "cross-site"})
    assert response.status_code == 403
