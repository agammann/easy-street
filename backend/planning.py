"""Deterministic, editable course planning without provider calls."""
from collections import deque
from .evidence_catalog import MAX_CATALOG_ENTRIES, build_catalog
from .models import OutlineModule

SOURCE_LIMIT = 24_000


def course_modules(course):
    modules = course["outline"].get("modules")
    if modules:
        return modules
    outline = course["outline"]
    return [{"id":"module-1", "title":outline["module_title"], "objectives":outline["objectives"],
             "selected_passage_ids":outline.get("selected_passage_ids", []),
             "assignments":course["options"].get("assignments",1), "quizzes":course["options"].get("quizzes",1)}]


def module_passages(document, module):
    identifiers = module["selected_passage_ids"]
    lookup = {p["id"]:p for p in document["passages"]}
    if not identifiers or len(set(identifiers)) != len(identifiers) or any(id not in lookup for id in identifiers):
        raise ValueError("Each module needs distinct source passages from this document.")
    passages = [lookup[id] for id in identifiers]
    if sum(len(p["text"]) for p in passages) > SOURCE_LIMIT:
        raise ValueError("A module exceeds 24,000 source characters. Remove passages or split the material across modules.")
    return passages


def propose_modules(document, options):
    passages = document["passages"]
    if len(passages) < options.modules:
        raise ValueError("The source has fewer passages than requested modules. Use fewer modules or a longer source.")
    # Partition by source order across the complete document. Long partitions are
    # sampled throughout their span, with every omission reported in the outline.
    chunks = [passages[i * len(passages) // options.modules:(i+1) * len(passages) // options.modules]
              for i in range(options.modules)]
    modules = []
    for i, chunk in enumerate(chunks):
        # One passage can require several exact evidence excerpts. Count the
        # actual catalog boundaries before proposing a plan that must be estimable.
        entries = [len(build_catalog([passage])) for passage in chunk]
        if sum(len(p["text"]) for p in chunk) <= SOURCE_LIMIT and sum(entries) <= MAX_CATALOG_ENTRIES:
            selected = chunk
        else:
            selected, size, catalog_size = [], 0, 0
            # Start at both boundaries, then repeatedly fill the widest gap.
            indices = [0] if len(chunk) == 1 else [0, len(chunk)-1]
            intervals = deque([(1,len(chunk)-2)])
            while intervals:
                left,right = intervals.popleft()
                if left > right:
                    continue
                index = (left+right)//2
                indices.append(index)
                intervals.extend(((left,index-1),(index+1,right)))
            for index in indices:
                passage = chunk[index]
                if size + len(passage["text"]) <= SOURCE_LIMIT and catalog_size + entries[index] <= MAX_CATALOG_ENTRIES:
                    selected.append(passage)
                    size += len(passage["text"])
                    catalog_size += entries[index]
            positions = {p["id"]:index for index,p in enumerate(chunk)}
            selected.sort(key=lambda p:positions[p["id"]])
        headings = list(dict.fromkeys(p["heading"].strip() for p in selected if p["heading"].strip()))
        modules.append({"id":f"module-{i+1}", "title":(headings[0] if headings else f"Module {i+1}")[:150],
            "objectives":[f"Examine {heading[:120]}." for heading in headings[:3]] or ["Explain the selected source material."],
            "selected_passage_ids":[p["id"] for p in selected],
            "assignments":options.assignments // options.modules + int(i < options.assignments % options.modules),
            "quizzes":options.quizzes // options.modules + int(i < options.quizzes % options.modules)})
    return modules


def sync_outline(course, document):
    modules = course_modules(course)
    if len(modules) != course["options"]["modules"] or [m["id"] for m in modules] != [f"module-{i+1}" for i in range(len(modules))]:
        raise ValueError("Keep every module exactly once in its original order.")
    for module in modules:
        try:
            OutlineModule.model_validate(module)
        except ValueError:
            raise ValueError("Check each module's title, objectives, source selection, and assessment limits.") from None
        module_passages(document,module)
    for kind in ("assignments","quizzes"):
        if sum(m[kind] for m in modules) != course["options"][kind]:
            raise ValueError(f"Module {kind} must add up to the approved course total of {course['options'][kind]}.")
    selected = set(id for module in modules for id in module["selected_passage_ids"])
    warnings = list(document.get("warnings",[]))
    if len(selected) != len(document["passages"]):
        warnings.append(f"Selected {len(selected)} of {len(document['passages'])} extracted passages across {len(modules)} modules, at most 24,000 characters and {MAX_CATALOG_ENTRIES} evidence excerpts per module. Unselected passages are not covered; review or adjust source selection before approval.")
    for index,module in enumerate(modules,1):
        if module["quizzes"] * course["options"]["questions_per_quiz"] > len(module["selected_passage_ids"]):
            warnings.append(f"Module {index} has more questions than selected passages; review for repeated coverage.")
    course["outline"].update(modules=modules,module_title=modules[0]["title"],objectives=modules[0]["objectives"],
        selected_passage_ids=[p["id"] for p in document["passages"] if p["id"] in selected], warnings=warnings,
        course_objectives=list(dict.fromkeys(objective for module in modules for objective in module["objectives"])),
        distribution=[{"module":i+1,"assignments":m["assignments"],"quizzes":m["quizzes"],"questions":m["quizzes"] * course["options"]["questions_per_quiz"]} for i,m in enumerate(modules)])
    return course
