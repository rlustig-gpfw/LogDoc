# LogDoc

## Problem, Audience, and Scope

**Problem** - Security Operations Center (SOC) analysts need to quickly triage network telemetry, map activity to threats, and get evidence-based next steps from playbooks yet today this requires manual correlation, knowing where to look, and is slow and inconsistent.

### Why this is a problem?

The primary user is a security analyst or SOC analyst who gathers network telemetry logs from their environment. Their job is to decide what happened, whether it’s benign or malicious, which techniques might be in play, and what to do next. Doing this well means: (1) interpreting log fields and patterns, (2) mapping to a shared language (e.g. MITRE ATT&CK), and (3) pulling in the right playbooks so actions are consistent and auditable. Today, that often means switching between security and event views, internal wikis, and PDF playbooks, and applying judgment without a single place that ties logs to classification and next steps. The context switching slows triage, increases inconsistency between analysts, and makes it harder to standardize on organizational playbooks.

LogDoc targets that gap: one place where an analyst can ask SOC questions, submit telemetry, get a clear classification and MITRE mapping when the data supports it, and get recommended actions grounded in the same playbooks the org already uses.

### Evaluation - input–output pairs

#### A. Log triage

| # | Input (summary or question) | What to evaluate |
|---|------------------------------|-------------------|
| 1 | Paste a short Zeek `conn.log` slice showing a clear port scan (many distinct destinations from one origin in a short window). | Response includes classification (e.g. suspicious/malicious), a relevant MITRE technique (e.g. T1046), rationale citing log fields (e.g. count of connections, ports), and at least one concrete recommended action. |
| 2 | Paste Zeek logs suggesting brute-force SSH (many failed connections to port 22 from one source). | Classification and MITRE technique (e.g. T1110) are appropriate; rationale references the log evidence; recommended actions align with brute-force response (e.g. block, review credentials, check playbook). |


#### B. Playbook usage (RAG)

| # | Input (question) | What to evaluate |
|---|-------------------|-------------------|
| 3 | “What is the incident response playbook for a network brute force attack? What immediate steps should I take?” | Answer cites or reflects content from the ingested brute-force playbook; includes ordered or prioritized steps (e.g. contain, preserve evidence, notify). |
| 4 | “Show me the Network Scan Incident Response Playbook” or “What does our playbook say about DDoS?” | Answer pulls in relevant playbook content (from RAG) and response sites details in the knowledge base. |

#### C. General SOC / in-scope questions

| # | Input (question) | What to evaluate |
|---|-------------------|-------------------|
| 5 | “What MITRE ATT&CK techniques are commonly associated with DNS tunneling, and how can I detect them in network logs?” | Lists relevant techniques (e.g. T1071, DNS); gives at least one concrete detection approach in a network/log context. |

## Proposed Solution

**Look and Feel:** Users interact with LogDoc through a single chat interface: they ask playbook questions, paste telemetry logs (still work in progress), or ask general SOC questions (e.g. “How do I respond to a brute-force attack?”). Responses stream in real time. The agent uses tools in the background (searching the playbook knowledge base, and optionally the web), and the UI shows brief status hints (e.g. “Searching knowledge base...”) so the analyst sees that answers are grounded in validated sources. Outputs are structured where it matters: classification, MITRE technique, rationale, and recommended actions for triage-style queries; for playbook questions, answers cite or summarize content from the ingested runbooks.

**How it's built (and next steps):** The current implementation is a first iteration: one agent that handles both log triage and playbook support, with two tools (RAG over playbooks and web search). The next iteration will introduce a supervisor that classifies the type of question (e.g. “log triage” vs “playbook / how-to”) and hands off to specialist agents. For example, a log triage specialist will focus on classification, MITRE, evidence from telemetry and a playbook support specialist will find, retrieve, and summarize playbooks. This process of iteratively improving the agent ensures the additional complexity is truly improving the final product.

### ADD DIAGRAM ###

### Tech Stack

| Component | Choice | Why this choice |
|-----------|----------------------------|------------------|
| **LLM(s)** | OpenAI (e.g. gpt-4.1-mini for agent/RAG, gpt-4.1 for evaluation) | Strong instruction-following and tool, helps to balance performance and quality. A more capable model used for evaluation where quality matters. |
| **Orchestration** | LangChain / LangGraph | Allows easy definition of single agent with tools and streaming today, and will support a supervisor + specialist graph in the next iteration with minimal rework |
| **Tool(s)** | RAG for playbooks (retriever chain), Tavily web search | Playbook knowledge base tool grounds answers in docs; web search covers recent threats and docs not yet in the knowledge base. |
| **Embedding model** | OpenAI `text-embedding-3-small` | Same vendor as the LLM, keeps consistency with good quality for semantic search over playbooks |
| **Vector database** | Qdrant (in-memory in MVP; persistent optional later) | Simple API and LangChain integration for indexing and retrieving playbook chunks |
| **Monitoring tool** | Not yet implemented; LangSmith planned for future iterations | LangSmith tracing and debugging tools are used in industry and work well. |
| **Evaluation framework** | RAGAS (Context Precision/Recall, Faithfulness, Response Relevancy, Noise Sensitivity) | Designed for RAG pipelines and gives repeatable metrics to compare across agent/prompt/RAG changes |
| **User interface** | React (Vite, TypeScript, Tailwind) + FastAPI backend with SSE streaming | Chat-first UX fits analyst workflows; FastAPI + SSE keeps streaming simple |
| **Deployment tool** | Not yet determined | To be chosen to run the API and optional persistent Qdrant in a consistent environment for demos or internal use. |
| **Other components** | Cohere Rerank (optional retriever chain), RAGAS test-set generation (SDG) | Rerank improves retrieval quality when used; SDG + RAGAS gives synthetic Q&A pairs to evaluate retrieval and response quality without manual labeling alone. |

### RAG components

**RAG** = embedding model + vector store + retriever (+ optional reranker) + retrieve-then-answer chain

- **Indexing:** Playbook content (from PDF and web sources) is loaded, split into chunks (`RecursiveCharacterTextSplitter`), embedded with the chosen embedding model, and stored in the vector store (Qdrant).
- **Retrieval:** For a given query (from the agent’s tool call), the retriever returns the top-k most similar chunks from the vector store. An optional **reranker** (e.g. Cohere) can rerank those chunks for relevance.
- **RAG chain:**  (1) Takes a question, (2) runs retrieval, (3) formats the retrieved chunks as context, (4) calls an LLM with a prompt that says “answer using this context,” and (5) returns the model response (and optionally the retrieved context for evaluation). To be clear, this chain is invoked by the agent as a tool. The agent does not run RAG by default on every turn as it decides when to call the tool.

### Agent components

- **Current Agent Iteration:** A single LangGraph-based agent (built with `create_agent`) with a SOC-focused system prompt and access to tools:
    - **search_playbooks_knowledge_base** — invokes the RAG chain above and returns the answer
    - **search_web** — Tavily search for recent or external cybersecurity content. The agent decides when to call each tool, how many times, and how to combine tool results into a final reply.
- **Planned Agent Iteration:** A supervisor node classifies the user request (e.g. log triage vs playbook support) and routes to specialist agents:
    - **log triage specialist** - emphasizes classification, MITRE, evidence from logs and may still need playbook tool info for recommended actions
    - **playbook support specialist**  - focuses on retrieving and summarizing runbooks

## RAG Data Sources

- Primary Data Sources: [Lumu Incident Response Playbooks](https://docs.lumu.io/portal/en/kb/incident-response)
- Seconday Data Sources: [CISA Response Playbooks](https://www.cisa.gov/sites/default/files/2024-08/Federal_Government_Cybersecurity_Incident_and_Vulnerability_Response_Playbooks_508C.pdf)

### Default Chunking Strategy

The default strategy is recursive character splitting using `RecursiveCharacterTextSplitter` with chunk size 1000 characters, overlap 300 characters, and separators `["\n\n", "\n", ". ", " ", ""]` (in that order). The splitter tries to break on paragraph boundaries first, then lines, then sentences, etc, so that chunks stay semantically coherent where possible.

Playbook content is narrative and section-based (headings, bullet lists, step-by-step procedures). Splitting on `\n\n` and `\n` first keeps intact “one idea per chunk” (e.g. a procedure or a section) and avoids cutting in the middle of a sentence when possible. The 1000-character target keeps each chunk small enough to fit several into the LLM context without blowing the window, while 300 characters of overlap reduces the chance that a key phrase or step is split across a boundary and lost at retrieval. With each playbook ranging from 10000-30000 characters, this initial strategy should provide useful as a baseline.

### Data Sources

#### Knowledge Base

- Serves as the primary RAG data source, which is produved by ingesting URL content and PDFs. PDFs are converted to markdown and cleaned to remove characters that don't play nicely with JSON. Web pages are loaded with LangChain's `WebBaseLoader`.
- This knowledge base is the authoritative, internal knowledge the agent uses to answer playbook and incident response questions. It is loaded at retriever build time, chunked with the strategy above, embedded, and indexed in the vector store (Qdrant). No external call is made at query time once the retriever index is fully built (one-time startup cost).

### Tavily Web Search

- Tavily is a search API used as the web search tool. It will retrieve a maximum of 3 results on the search query.
- It provides live, external context the agent can use when the local playbook store is insufficient, such as recent CVEs, new attack trends, or public playbooks/docs not yet ingested. The agent decides when to call it (after or instead of the playbook tool) based on the user question.

### Interaction

1. User asks a question in the chat
2. Agent receives the message and may call one or both tools in one or more steps:
   - Knowledge base search: query → vector search over the chunked playbook index → LLM with “answer from this context” → returns the model response
   - Tavily search: query → search query adjusted by LLM and sent to Tavily → receive web search responses → LLM with “answer from this context” → returns the model response
3. Agent combines tool outputs (and its own reasoning) into a final answer and streams it to the user.

## Evaluation

### Retriever Performance Comparison

| Retriever                 | Context Recall | Context Precision | Faithfulness | Answer Relevancy | Noise Sensitivity |
| ------------------------- | -------------- | ----------------- | ------------ | ---------------- | ----------------- |
| Naive Retrieval           | 0.533          | 0.892             | 0.763        | 0.939            | 0.040             |
| Parent-Document Retrieval | 0.869          | 0.894             | 0.821        | 0.950            | 0.308             |
| **% Change**              | **+63%**       | **~0%**           | **+8%**      | **+1%**          | **+670%**         |

---

### Cost & Latency Comparison

| Retriever                 | Avg Latency (s) | P95 Latency (s) | Avg Total Tokens | Total Tokens (Sum) |
| ------------------------- | --------------- | --------------- | ---------------- | ------------------ |
| Naive Retrieval           | 9.5             | 13.2            | 1099.6           | 13195              |
| Parent-Document Retrieval | 9.9             | 14.1            | 2102.3           | 25228              |
| **% Change**              | **+4%**         | **+7%**         | **+91%**         | **+91%**           |

#### Why Parent-Document Retrieval?
Parent-Document retrieval is selected as an advanced retriever because it works well for playbooks. The child query will often match to a small part within a playbook but the additional context from the surrounding procedure is helpful to the overall answer. Additionally, this large context reduces any missing steps within the playbook. For example, the child retriever might extract a section on "Detection", but may not include a section on "Containment." This is where the parent context is helpful. Lastly, this retriever will work best assuming the playbook documents are already split into sections.

### Takeaways
- Naive retrieval gives a strong baseline for playbook retrieval and analyst trust: context precision and answer relevancy are high, and faithfulness is solid. Context recall is lower mainly because the evaluator uses full-doc references while the retriever returns only a few small chunks. Noise sensitivity is very low, so answers stay stable when irrelevant context is present. Latency and token use are relatively low as well.
- Parent-document retrieval improves context recall by returning the parent document around each matched child chunk, so more of the information behind the reference answer is available. Context precision and answer relevancy stay high and faithfulness improves slightly. The tradeoff is higher noise sensitivity. The extra parent context can include irrelevant sections, and the model is more sensitive to that noise. Token usage is about twice that of naive retrieval, with little change in latency.
- For production systems:
    - If cost is a concern, naive retrieval is the best option as the critical metrics (context precision, answer relevancy, and faithfulness) needed to gain an analyst's trust are high.
    - If overall performance is the main priority, parent-document retrieval is the best option as it directionally improves all metrics with a small impact to the noise sensitivity.


## Next Steps
The playbook RAG implementation is a core feature of this project so it is required for the Demo Day project. However, as already discussed, the agent orchestration will be updated to better manage the different types of incoming requests. 
