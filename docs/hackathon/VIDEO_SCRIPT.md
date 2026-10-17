# Demonstration video script

Target duration: **2 minutes 45 seconds**. This is a recording plan, not proof that any pending feature or deployment works. Record after the approved live Nebius run and fresh-session acceptance. Rehearse to keep the published video below three minutes.

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
- If evidence is insufficient or a reviewer misses a claim, show the honest review state or a manual correction. Do not claim perfect source grounding or guaranteed correctness.
- Verify every shown feature, button label, provider/model, access instruction, and link against the final tested revision. The exact model name must match the deployed runtime.
- Inspect the entire recording for accidental secrets or personal data before approval. The source branch and draft PR are public with approval; merge and a new release remain unapproved. The owner must approve video publication. Upload to the approved public YouTube destination only after that approval.

The [official rules](https://nebiusglobalaihackathon.devpost.com/rules) specify the public YouTube demonstration format. No recording, upload, or publication is performed by this script.
