import html
import json


def export_course(course: dict, format: str, document: dict | None = None):
    source_manifest = ({"document_id":document["id"],"filename":document["filename"],"sha256":document["sha256"],
        "passages":[{k:p[k] for k in ("id","location","page","paragraph")} for p in document["passages"]]} if document else None)
    locations = {p["id"]:p["location"] for p in document["passages"]} if document else {}
    if format == "json":
        backup = {"format":"easy-street-course-v1","source_text_included":False,
            "notice":"Original documents and extracted passages are excluded. Short evidence quotes are included. Review content before sharing.","source_manifest":source_manifest,"course":course}
        return json.dumps(backup,ensure_ascii=False,indent=2),"application/json","easy-street-backup.json"
    answers = format == "answers"
    esc = html.escape
    blocks = []
    for section in sorted(course["sections"],key=lambda s:s["order"]):
        if answers and section["kind"] != "quiz":
            continue
        body = f"<h2>{esc(section['title'])}</h2><p>{esc(section['body']).replace(chr(10),'<br>')}</p>"
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
    document = f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(course['title'])} · {label}</title><style>body{{font:17px/1.65 system-ui;max-width:850px;margin:40px auto;padding:0 24px;color:#202a24}}h1,h2{{line-height:1.2}}section{{border-top:1px solid #ddd;padding:24px 0}}aside,.notice{{background:#fff3cd;padding:12px}}details{{font-size:14px}}@media print{{details{{display:block}}}}</style>
<h1>{esc(course['title'])}</h1><p>{label} · Easy Street</p>{mode}<p>Personal learning proposals based on supplied material. Review source support before sharing. Original source files are not included.</p>{''.join(blocks)}</html>"""
    return document,"text/html","easy-street-answers.html" if answers else "easy-street-course.html"
