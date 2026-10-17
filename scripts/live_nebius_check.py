"""Opt-in, persistent, capped live acceptance. Never prints keys or raw API errors."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


@contextmanager
def exclusive_acceptance_lock(directory):
    """One acceptance process; failed/stale locks require deliberate review."""
    directory.mkdir(parents=True,exist_ok=True)
    path = directory/"active.lock"
    try:
        descriptor = os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError:
        raise SystemExit("A live acceptance run is active, or a previous run left its safety lock. Stop any active process and review its durable ledger and outcome before manually removing active.lock. No provider request was made by this run.") from None
    identity = os.fstat(descriptor)
    completed = False
    try:
        with os.fdopen(descriptor,"w",encoding="utf-8",closefd=False) as stream:
            json.dump({"pid":os.getpid(),"started_at":datetime.now(timezone.utc).isoformat(),
                "notice":"Do not remove this lock until the process has stopped and its ledger and outcome have been reviewed."},stream)
            stream.flush()
            os.fsync(descriptor)
        yield path
        completed = True
    finally:
        os.close(descriptor)
        # Failures and interruptions retain the lock. Never infer that an old PID
        # or elapsed time proves a request was not billed or can safely be repeated.
        if completed and path.exists():
            current = path.stat()
            if (current.st_dev,current.st_ino) == (identity.st_dev,identity.st_ino):
                path.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approved-budget-usd",type=float,required=True)
    parser.add_argument("--output",type=Path,required=True,help="Private evidence directory outside the repository")
    args = parser.parse_args()
    if not 0 < args.approved_budget_usd <= 1:
        raise SystemExit("This acceptance script supports an explicitly approved cap up to $1.")
    directory = args.output.resolve()
    if directory.is_relative_to(ROOT):
        raise SystemExit("Keep live accounting and evidence outside the public repository.")
    from dotenv import dotenv_values
    key = os.environ.get("NEBIUS_API_KEY") or dotenv_values(ROOT/".env.local").get("NEBIUS_API_KEY")
    if not key:
        raise SystemExit("Nebius is not configured. Use the private masked setup; never paste a key into chat.")
    with exclusive_acceptance_lock(directory):
        _run_acceptance(args,directory,key)


def _run_acceptance(args,directory,key):
    import httpx
    from openai import OpenAI
    from backend.provider import NebiusProvider,NEBIUS_MODEL,NEBIUS_BASE_URL
    from backend.demo_control import DemoLedger,MeteredProvider
    from backend.models import CourseInput,GenerateInput
    from backend.service import Service
    from backend.extraction import SAMPLE_PATH
    # This GET is an access check, not inference. Pin the verified model; no silent fallback.
    try:
        with httpx.Client(trust_env=False,follow_redirects=False) as transport:
            client = OpenAI(api_key=key,base_url=NEBIUS_BASE_URL,max_retries=0,timeout=30,http_client=transport)
            available = any(model.id == NEBIUS_MODEL for model in client.models.list().data)
    except Exception:
        raise SystemExit("The authenticated Nebius model check failed. No inference was started and no raw response was printed.") from None
    if not available:
        raise SystemExit("The pinned NVIDIA model is not listed for this account. No inference was started; review official supported models before choosing another.")
    ledger = DemoLedger(directory/"development-usage.sqlite3",args.approved_budget_usd,1)
    provider = MeteredProvider(NebiusProvider(api_key=key),ledger,"approved-development-acceptance")
    service = Service(directory/"workspace",args.approved_budget_usd,providers={"nebius":provider})
    state_path = directory/"state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text())
        job = service.store.get("jobs",state["job_id"])
        if not job or job["status"] != "complete":
            raise SystemExit("A previous live attempt is incomplete. Review its ledger and outcome; this script will not repeat a possibly billed request.")
        elapsed = state.get("elapsed_seconds")
    else:
        document = service.document(SAMPLE_PATH.read_bytes(),"small-garden-watering.txt")
        course = service.create_course(CourseInput(document_id=document["id"],title="Small Garden Watering — live Nemotron acceptance",mode="nebius"))
        course.update(outline_approved=True,status="ready")
        service.store.put_course(course,"Before approved live acceptance")
        estimate = service.estimate(course)
        if estimate["estimated_max_usd"] > ledger.snapshot()["remaining_usd"]:
            raise SystemExit("The conservative test estimate does not fit the approved allowance. No inference was started.")
        job,_ = service.submit(course["id"],GenerateInput(idempotency_key="approved-nebius-acceptance-v1"))
        state = {"job_id":job["id"],"course_id":course["id"],"estimated_max_usd":estimate["estimated_max_usd"]}
        state_path.write_text(json.dumps(state,indent=2))
        started = time.monotonic()
        service.run(job["id"])
        elapsed = round(time.monotonic()-started,2)
        state["elapsed_seconds"] = elapsed
        state_path.write_text(json.dumps(state,indent=2))
        job = service.store.get("jobs",job["id"])
    course = service.store.get("courses",state["course_id"])
    document = service.store.get("documents",course["document_id"])
    passages = {p["id"]:p["text"] for p in document["passages"]}
    matches = all(e["passage_id"] in passages and e["quote"] in passages[e["passage_id"]] for s in course["sections"] for e in s["evidence"])
    records = service.store.usage_records()
    result = {"kind":"live","model":NEBIUS_MODEL,"catalog_access_verified":True,
        "approved_cap_usd":args.approved_budget_usd,"job_status":job["status"],
        "sections":len(course["sections"]),"exact_source_quotes":matches,
        "review_flag_count":len(course["review_flags"]),"elapsed_seconds":elapsed,
        "input_tokens":sum(r["input_tokens"] for r in records),"output_tokens":sum(r["output_tokens"] for r in records),
        "budget":ledger.snapshot(),"usage":records,"human_content_review":"pending",
        "notice":"Measured usage is an application estimate, not an invoice. Exact quotes do not guarantee factual support."}
    (directory/"result.json").write_text(json.dumps(result,indent=2))
    (directory/"course-review.json").write_text(json.dumps({"course":course,"source":document},ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
    if (job["status"] != "complete" or len(course["sections"]) != 10 or not matches
            or result["budget"]["reserved_usd"] or result["budget"]["uncertain_calls"]):
        raise SystemExit("Live acceptance did not pass. Review the saved outcome without automatically repeating inference.")


if __name__ == "__main__":
    main()
