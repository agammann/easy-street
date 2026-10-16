import html
import json
from .grounding import proposal_title
from .planning import course_modules


def export_course(course: dict, format: str, document: dict | None = None):
    references = (document.get("passages") or document.get("source_references",[])) if document else []
    locations = {p["id"]:p["location"] for p in references}
    if format == "json":
        outline = course.get("outline",{})
        needed = set(outline.get("selected_passage_ids",[]))
        for module in outline.get("modules",[]):
            needed.update(module.get("selected_passage_ids",[]))
        needed.update(evidence["passage_id"] for section in course["sections"] for evidence in section["evidence"])
        # Retain every course reference without copying unused chapter locations.
        # The original digest and OCR options still identify the file to reattach.
        source_manifest = ({"document_id":document["id"],"filename":document["filename"],"sha256":document["sha256"],
            "format":document["format"],"ocr_pages":document.get("ocr_pages",[]),
            "passages":[{k:p[k] for k in ("id","location","page","paragraph")} for p in references if p["id"] in needed]} if document else None)
        backup = {"format":"easy-street-course-v1","source_text_included":False,
            "notice":"Original documents and extracted passages are excluded. Source locations cover the course's selected passages and cited evidence only. Short evidence quotes are included. Review content before sharing.","source_manifest":source_manifest,"course":course}
        return json.dumps(backup,ensure_ascii=False,indent=2),"application/json","easy-street-backup.json"
    answers = format == "answers"
    esc = html.escape
    blocks = []
    modules = course_modules(course) if "outline" in course else [{"id":"module-1","title":course["title"],"objectives":[],"assignments":1,"quizzes":1}]
    module_titles = {m["id"]:m["title"] for m in modules}
    active_module = None
    for section in sorted(course["sections"],key=lambda s:s["order"]):
        if answers and section["kind"] != "quiz":
            continue
        module_id = section.get("module_id") or modules[0]["id"]
        if module_id != active_module:
            blocks.append(f"<h2 class='module'>{esc(module_titles.get(module_id,module_id))}</h2>")
            active_module = module_id
        body = f"<h2>{esc(proposal_title(section['kind'], section['title']))}</h2><p>{esc(section['body']).replace(chr(10),'<br>')}</p>"
        if answers:
            body += f"<h3>Answer</h3><p>{esc(section['answer'] or '')}</p><h3>Explanation</h3><p>{esc(section['explanation'] or '')}</p>"
        if section["review_notes"]:
            review = ("This question requires review. See the separate answer key for evidence-review details."
                      if section["kind"] == "quiz" and not answers else " ".join(section["review_notes"]))
            body += "<aside>Review required: " + esc(review) + "</aside>"
        if section["evidence"]:
            body += "<details><summary>Source references</summary><ul>"
            for ev in section["evidence"]:
                # Learner quizzes include locations only: evidence quotes can reveal answers.
                quote = f" — {esc(ev['quote'])}" if answers or section["kind"] != "quiz" else ""
                location = locations.get(ev["passage_id"],ev["passage_id"])
                source_label = f"{document['filename']} · {location}" if document else location
                body += f"<li>{esc(source_label)}{quote}</li>"
            body += "</ul></details>"
        blocks.append(f"<section>{body}</section>")
    label = "Answer key" if answers else "Learner course"
    mode = "<p class='notice'>Offline demo — original sample, no provider generation.</p>" if course["mode"] == "demo" else ""
    syllabus = ""
    if not answers:
        objectives = course.get("outline",{}).get("course_objectives") or list(dict.fromkeys(item for module in modules for item in module["objectives"]))
        syllabus = "<section class='syllabus'><h2>Proposed syllabus</h2><h3>Course objectives</h3><ul>" + "".join(f"<li>{esc(item)}</li>" for item in objectives) + "</ul><table><thead><tr><th>Module</th><th>Assignments</th><th>Quizzes</th><th>Questions per quiz</th></tr></thead><tbody>"
        syllabus += "".join(f"<tr><td>{esc(m['title'])}</td><td>{m['assignments']}</td><td>{m['quizzes']}</td><td>{course.get('options',{}).get('questions_per_quiz',3) if m['quizzes'] else '—'}</td></tr>" for m in modules)
        syllabus += "</tbody></table><p>Use the modules in this order at your own pace. Assessment tasks and rubrics are study proposals, not institutional requirements.</p></section>"
        if course.get("outline",{}).get("warnings"):
            syllabus += "<aside>Source coverage: " + esc(" ".join(course["outline"]["warnings"])) + "</aside>"
    document = f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(course['title'])} · {label}</title><style>body{{font:17px/1.65 system-ui;max-width:850px;margin:40px auto;padding:0 24px;color:#202a24}}h1,h2{{line-height:1.2}}section{{border-top:1px solid #ddd;padding:24px 0}}aside,.notice{{background:#fff3cd;padding:12px}}details{{font-size:14px}}.module{{background:#e2f3df;padding:16px}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:8px;text-align:left}}@media print{{body{{margin:0;max-width:none;font-size:11pt}}.module{{break-before:page}}section,aside,tr{{break-inside:avoid}}details{{display:block}}}}</style>
<h1>{esc(course['title'])}</h1><p>{label} · Easy Street</p>{mode}<p>Personal learning proposals based on supplied material. Review source support before sharing. Original source files are not included.</p>{syllabus}{''.join(blocks)}</html>"""
    return document,"text/html","easy-street-answers.html" if answers else "easy-street-course.html"
