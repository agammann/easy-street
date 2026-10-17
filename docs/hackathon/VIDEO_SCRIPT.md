# Demonstration video script

Target duration: **2 minutes 45 seconds**. This is a recording plan, not proof that any pending feature or deployment works. Two approved live Nebius runs completed technically, including revised prompt v2.1. The revised introduction improved, but separate inspection still found citation-coverage/precision gaps. Record after owner content review, deliberate corrections, and fresh deployed-session acceptance; see [VERIFICATION.md](VERIFICATION.md). Rehearse to keep the published video below three minutes.

Use only the original garden chapter and application UI. Do not record secret-manager screens, environment files, terminal history, provider credentials, billing details, judge credentials, personal documents, or private browser tabs. Use no music or third-party footage. Show accurate provider/model and job states. A cached result must be labeled as cached; it must not be portrayed as a new inference call.

| Time | Screen action | Narration |
| --- | --- | --- |
| 0:00–0:15 | Open the real app in a fresh session. Show the main workspace. | “Easy Street turns material you own into an editable mini-course. It is built for instructors and independent learners who want to check the source behind a draft.” |
| 0:15–0:35 | Choose **Try the sample chapter**, show the original chapter and extraction. Briefly point to normal upload and the separate **Generate sample with Nebius** shortcut. | “I can upload a PDF, DOCX, or text chapter. For this demonstration I am using the original sample included with the project. I can inspect the extracted passages before sending anything for generation.” |
| 0:35–0:55 | Choose modules and assessment counts. Review source coverage and approve the outline. | “I choose modules, assignments, quizzes, and source coverage. This outline is a proposal I can review. Educational claims must stay within the selected material; the workflow does not search the web.” |
| 0:55–1:15 | Start one real Nebius job. Show provider/model, bounded estimate, and progress. | “The server calls NVIDIA Nemotron through Nebius Token Factory to create this course and review support. The operator-funded judging demo keeps its key on the server. Regular installations keep the user's own provider setup.” |
| 1:15–1:40 | Show the completed course. Open evidence beside notes and a quiz. | “Each factual section links to source evidence. I can compare the statement with the exact quotation and its location. The support check can flag missing or conflicting information. A quotation alone does not guarantee that every claim follows from it.” |
| 1:40–2:00 | Edit a sentence and regenerate a different section; show the edit survives. | “I can correct the text myself and regenerate a section while retaining unrelated edits. Course options, versions, and job recovery make this a workspace I can actually use.” |
| 2:00–2:20 | Show separate learner/answer exports; download learner HTML. | “Learner material and answer keys export separately. JSON backs up the course without embedding the complete original document.” |
| 2:20–2:35 | Show deletion/retention UI and visitor privacy statement. | “The hosted demonstration separates visitor workspaces, bounds generation, and provides deletion and temporary cleanup. No visitor needs a personal API key to judge the application.” |
| 2:35–2:45 | Return to a clear course/evidence view; show approved repo/demo links. | “Easy Street is open source. Its purpose is practical: turn a chapter into useful learning work while keeping the original evidence within reach.” |

## Recording checks

- Use an uncached sample generation only after its test spending is approved. If the run is slow, shorten idle footage with an explicit “generation wait shortened” caption; retain the real start and result. Do not replace the result with unrelated mock content.
- Keep more than one minute of actual application interaction on screen. Record desktop interaction at readable text size; show a brief mobile view only if it was tested and helps the story.
- The first real sample returned zero automatic flags, yet a separate inspection caught a title-only introduction citation and an unsupported assurance. The second v2.1 sample improved that introduction but still had coverage/precision gaps despite zero automatic flags. Show the honest review state or a deliberate correction when demonstrating a missed claim. If evidence is insufficient, keep that visible. Do not claim perfect source grounding or guaranteed correctness.
- Verify every shown feature, button label, provider/model, access instruction, and link against the final tested revision. [VERIFICATION.md](VERIFICATION.md) separates the fully green packaging-correction revision from later edits and records live/deployment gates. The exact model name must match the deployed runtime.
- Inspect the entire recording for accidental secrets or personal data before approval. The source branch and draft PR are public with approval; merge and a new release remain unapproved. The owner must approve video publication. Upload to the approved public YouTube destination only after that approval.

The [official rules](https://nebiusglobalaihackathon.devpost.com/rules) specify the public YouTube demonstration format. No recording, upload, or publication is performed by this script.
