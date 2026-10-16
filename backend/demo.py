"""Deterministic material for the original included sample only."""
from .models import GeneratedCourse, Verification

DEMO_VERSION = "source-scoped-v2"


def demo_course(document: dict, questions: int, target_id: str | None = None):
    if not document["is_sample"]:
        raise ValueError("Offline demo is available only for the original included sample.")
    passages = document["passages"]
    def evidence(index, quote):
        p = passages[index]
        if quote not in p["text"]:
            raise ValueError("The original sample has changed; offline demo evidence must be updated.")
        return [{"passage_id":p["id"], "quote":quote}]
    sections = []
    def add(id, kind, title, body, ev=None, answer=None, explanation=None):
        sections.append(dict(id=id, kind=kind, title=title, body=body, answer=answer, explanation=explanation,evidence=ev or []))
    soil = evidence(1,"If the soil feels dry at that depth, the container needs water.")
    slow = evidence(2,"Slow watering gives water time to soak into the soil rather than run over the edge of the container.")
    record = evidence(3,"A simple watering record contains the date, the soil observation, and the action taken.")
    change = evidence(4,"A container may dry faster on a warm, windy day than on a cool, still day.")
    compare = evidence(5,"Based on these observations, water Container A slowly and wait before watering Container B.")
    add("objectives","objectives","Proposed learning objectives","By the end of this module, practice interpreting soil observations, explaining slow watering, and keeping a watering record.")
    add("introduction","introduction","Observe before watering","The chapter recommends checking soil about two centimeters below the surface before deciding whether to water.", evidence(1,"Push a finger about two centimeters into the soil."))
    add("readings","readings","Assigned readings · proposed selection","Read Observing soil, Watering slowly, Keeping a record, Changing conditions, and Comparing two containers in the supplied chapter.",soil+slow+record+change+compare)
    add("notes","notes","Learning notes","Use the soil observation to guide the action: dry soil at two centimeters calls for water. Apply water slowly so it can soak in. Record the date, soil observation, and action. Conditions can change how quickly a container dries.",soil+slow+record+change)
    add("announcement","announcement","Proposed module announcement","Before starting the assignment, read the chapter and open the source links. Review your answers against the supplied passages.")
    add("assignment","assignment","Written assignment · proposed task","Compare the chapter's two containers: A is dry at two centimeters, while B is moist at the same depth. Write a short recommendation for each container and propose one record entry per container. Explain your choices using the supplied passage.",evidence(5,"Suppose Container A feels dry at two centimeters and Container B feels moist at the same depth."))
    add("rubric","rubric","Proposed assignment rubric","Observation: 2 points for distinguishing each container's soil condition.\nReasoning: 2 points for linking recommendations to the supplied chapter.\nRecord: 2 points for including the date, observation, and action.\nClarity: 2 points for concise, understandable writing.\nThis rubric is a learning proposal, not an institutional grading policy.")
    qs = [
        ("What observation indicates a container needs water?","The soil feels dry about two centimeters below the surface.","The chapter ties the watering decision to dryness at that depth, rather than the surface alone.",soil),
        ("Why does the chapter recommend applying water slowly?","It gives water time to soak into the soil instead of running over the container edge.","Slow application lets the soil absorb the water.",slow),
        ("What three items belong in a watering record?","The date, the soil observation, and the action taken.","The chapter lists these three items as the components of a simple record.",record),
        ("How can a warm, windy day affect a container compared with a cool, still day?","The container may dry faster.","The chapter identifies warmth and wind as conditions that can increase drying speed.",change),
        ("In the chapter's two-container example, which container should be watered?","Water Container A slowly and wait before watering Container B.","Container A is dry at two centimeters; Container B is moist at the same depth.",compare+evidence(5,"Suppose Container A feels dry at two centimeters and Container B feels moist at the same depth."))]
    for i, (question, answer, explanation, ev) in enumerate(qs[:questions], 1):
        add(f"quiz-{i}","quiz",f"Quiz · question {i}",question,ev,answer,explanation)
    if target_id:
        sections = [s for s in sections if s["id"] == target_id]
    generated = GeneratedCourse(sections=sections)
    verified = Verification(results=[{"section_id":s["id"],"status":"supported","reason":"Authored original-sample offline demonstration; no provider call."} for s in sections])
    return generated, verified


def demo_module(document: dict, payload: dict):
    """Source-scoped, quotation-based demo for editable module distributions."""
    if not document["is_sample"]:
        raise ValueError("Offline demo is available only for the original included sample.")
    passages = payload["passages"]
    # Keep excerpts literal, including their uncertainty and qualification.
    excerpts = [{"passage_id":p["id"],"quote":p["text"][:500]} for p in passages]
    # Short headings remain assigned reading, but use substantive source text
    # for the study material and questions whenever this module supplies it.
    substantive_ids = {p["id"] for p in passages if len(p["text"]) >= 80}
    study_excerpts = [excerpt for excerpt in excerpts if excerpt["passage_id"] in substantive_ids] or excerpts
    sections = []
    def add(identifier,kind,title,body,evidence=None,answer=None,explanation=None):
        sections.append({"id":identifier,"kind":kind,"title":title,"body":body,
            "evidence":evidence or [],"answer":answer,"explanation":explanation})
    module = payload["module"]
    add("objectives","objectives","Proposed learning objectives","\n".join(module["objectives"]))
    add("introduction","introduction",module["title"],"Read this original source excerpt:\n"+study_excerpts[0]["quote"],[study_excerpts[0]])
    add("readings","readings","Assigned readings · proposed selection",
        "Read the selected source passages: "+", ".join(p["location"] for p in passages)+".",excerpts[:12])
    add("notes","notes","Learning notes","Compare these original excerpts:\n\n"+"\n\n".join(e["quote"] for e in study_excerpts[:12]),study_excerpts[:12])
    add("announcement","announcement","Proposed module announcement","Read the selected passages and use their source links to check your work.")
    for index in range(module["assignments"]):
        excerpt = study_excerpts[index % len(study_excerpts)]
        add(f"assignment-{index+1}","assignment",f"Proposed written assignment {index+1}",
            "Explain the following excerpt in your own words, then identify one detail that the excerpt does not establish:\n"+excerpt["quote"],[excerpt])
        add(f"rubric-{index+1}","rubric",f"Proposed assignment {index+1} rubric",
            "Source accuracy: 2 points. Distinguishing evidence from inference: 2 points. Clear explanation: 2 points. This is a proposed personal study rubric.")
    for index in range(module["quizzes"] * payload["options"]["questions_per_quiz"]):
        excerpt = study_excerpts[index % len(study_excerpts)]
        passage = next(p for p in passages if p["id"] == excerpt["passage_id"])
        add(f"quiz-{index+1}","quiz",f"Quiz · question {index+1}",
            f"Quote a detail stated in {passage['location']} and distinguish it from a conclusion the source does not state.",
            [excerpt],excerpt["quote"],"Compare your quotation with this exact source excerpt. Any additional conclusion needs separate evidence.")
    if payload.get("target_section"):
        target = payload["target_section"]
        section = next(s for s in sections if s["kind"] == target["kind"])
        section["id"] = target["id"]
        sections = [section]
    return GeneratedCourse(sections=sections),Verification(results=[
        {"section_id":s["id"],"status":"supported","reason":"Quotation-based original-sample demonstration; no provider call."} for s in sections])
