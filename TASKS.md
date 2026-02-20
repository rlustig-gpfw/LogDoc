# LogDoc – Task checklist & plan (from .cursorrules)

Use this checklist to track progress against the MVP goals. Order follows the cursorrules task list.

---

## Task 1 – Problem, audience, scope

**Goal:** Clearly define the SOC problem, who the user is, and that the system answers real analyst questions.

- [ ] Document the SOC problem being solved (1–2 paragraphs).
- [ ] Define primary user: Security analyst / SOC analyst (persona or user story).
- [ ] List 3–5 concrete analyst questions the system must answer.

---

## Task 2 – Proposed solution & UX

**Goal:** Define interaction model, high-level architecture, and separation between agent and retrieval.

- [ ] Describe how the user interacts with the system (CLI, API, notebook, etc.).
- [ ] Document high-level architecture: Zeek logs → LLM → MITRE / analysis → RAG → SOC response.
- [ ] List major components (LLM, RAG, tools) and what each does.
- [ ] Clarify what the agent reasons over vs what retrieval provides (runbooks/playbooks).

---

## Task 3 – Data & knowledge sources

**Goal:** Decide inputs (Zeek-style data) and RAG sources; ensure the agent can reason over telemetry and enrich with context.

- [ ] Define what Zeek-style data the system consumes (log types, format, sample size).
- [ ] Choose external or internal knowledge sources for RAG (runbooks, playbooks, docs).
- [ ] Ingest and index RAG content (e.g. Qdrant `log_doc` collection).
- [ ] Confirm the agent can use telemetry + RAG results together (e.g. multi-turn tool use).

---

## Task 4 – End-to-end prototype

**Goal:** Working local system: user submits Zeek-style logs and receives SOC-style triage output.

- [ ] Ingest Zeek-style logs or preprocessed summaries.
- [ ] LLM classification & analysis (structured output: classification, MITRE, rationale, actions, confidence).
- [ ] MITRE ATT&CK technique identification in the pipeline.
- [ ] RAG lookup for playbooks/runbooks (tools wired and callable by the agent).
- [ ] SOC-style response generation (what happened, why it matters, what to do).
- [ ] Single flow: submit logs → get triage JSON (and optionally natural-language summary).
- [ ] Prompts centralized and versioned (per cursorrules §3).

---

## Task 5 – Evaluation (baseline)

**Goal:** Golden dataset, quality metrics, and a baseline to improve from.

- [ ] Create a small, clean test set (golden dataset) of Zeek log samples with expected labels/outcomes.
- [ ] Define how you measure “how well” (classification accuracy, MITRE match, explanation quality).
- [ ] Establish a baseline (e.g. RAGAS or similar) and record results.

---

## Task 6 – Improvement loop

**Goal:** Improve retrieval or reasoning and compare to baseline.

- [ ] Identify one improvement (e.g. prompt, RAG chunking, or tool description).
- [ ] Re-run evaluation and compare to Task 5 baseline.
- [ ] Document what changed and whether quality improved.

---

## Task 7 – Next steps / demo day decision

**Goal:** Decide what is “good enough” to demo and capture tradeoffs.

- [ ] Define demo-ready criteria (e.g. “handles X log types”, “baseline metric above Y”).
- [ ] Decide go/no-go for demo.
- [ ] Document architectural tradeoffs and future directions (post-MVP).

---

## Cross-cutting (apply throughout)

**Prompting (cursorrules §3)**  
- [ ] All prompts: SOC analyst role + triage objective stated.  
- [ ] Structured outputs (e.g. classification, mitre_technique, rationale, recommended_actions).  
- [ ] Evidence-based reasoning; “unknown” / “insufficient evidence” when data is insufficient.  
- [ ] Prompts centralized and versioned/named for eval.

**Engineering (cursorrules §4)**  
- [ ] Prioritize end-to-end flow over premature optimization.  
- [ ] For any new feature: “Does this improve SOC-style triage quality for Zeek telemetry?”

**Scope guardrails (cursorrules §5)**  
- [ ] In scope: SOC triage and response from Zeek-style telemetry.  
- [ ] Out of scope for MVP: full SIEM, real-time production automation, perfect detection.

---

*Generated from `.cursorrules`. Update this file as you complete items.*
