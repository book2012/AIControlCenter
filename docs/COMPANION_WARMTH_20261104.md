# Warm companion communication — 2026-11-04

## Scope and evidence

User requested everyday warm language. Reviewed HSE and British Heart Foundation listening guidance: leave room, match pace, reflect what is said, avoid assumptions, minimizing, over-reassurance and unsolicited solutions. These are communication principles, not evidence that this AI provides therapy. Do not import clinical protocols into every ordinary chat.

Sources checked 2026-11-04:
- https://www.hse.ie/mental-health/helping-someone-else/what-to-say/
- https://www.bhf.org.uk/informationsupport/heart-matters-magazine/wellbeing/how-to-talk-about-health-problems/active-listening

## Implementation

A short versioned system policy is shared by existing chat and NDJSON stream, with concise Korean tone instructions. No scraped quote corpus, model-weight fine-tuning, automatic web fetching, new personal memories or background LLM calls. Current tools remain disabled. Fast and quality profiles remain pinned with the same context/output caps; policy adds prefill tokens, not another inference call. Task questions must receive direct useful answers without a compulsory comforting preface. Feelings get a brief grounded acknowledgement, at most one optional question, and advice only when wanted. Silence/goodbye are respected; no exclusive relationship or return pressure. Uncertainty and no-invented-actions rules remain.

Site original idle lines rotate no more than once per 90s in visible tabs. Quiet mode suppresses them. Not notifications or user-mood detection. Small close stage and actual 3D character motion remain; new plush proportions, large amber eyes, cat/dog/hedgehog selection, bounded geometric nap on WebGL, lower-detail lit meshes in software fallback. This is a procedural approximation, not a production sculpt matching all reference fur detail. Original provided PNGs are reference thumbnails/static failure fallback only.

## Acceptance

Focused runtime tests must pass. Evaluate synthetic fatigue, listening-only, good-news, factual task, uncertain plan and goodbye cases on local Qwen, documenting failures honestly; generated wording is nondeterministic. Preserve leased streaming, origin/host checks and no-tool boundary. Activate an immutable primary runtime release with exact plist rollback; notebook bridge stays unchanged. Shopping/Ubuntu/public ingress are outside scope.

The first experimental longer example-based prompt overcopied a fatigue example, mixed Chinese into Korean, and failed a simple arithmetic check. It was rejected before activation; the final policy removes few-shot copying and keeps task accuracy/directness explicit. Preserve these failures as evaluation evidence, not a quality claim.

Final synthetic evaluation: listening-only and good-news replies were warm without solution lists on fast and quality profiles; tentative meeting stayed unconfirmed. Natural wording/register is not fully reliable. Existing active 4B policy also returned 140 for 17*8; the final warm policy did not introduce or solve this limitation. 9B returned136. Treat this as a known model capability limit, not a passing arithmetic evaluation. Keep a broader factual/grounding evaluation and deterministic verification as commercial gates.
