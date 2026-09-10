# Generative AI Engineering — Complete Roadmap
### Target: Senior Technical Lead / Staff Engineer (Java background, 10 YOE)

> Scope: everything a **backend/platform lead** needs to design, build, ship, secure, evaluate and operate LLM-powered systems — RAG, agents, MCP, evals, guardrails, cost & latency engineering.
> Not scope: training foundation models from scratch, ML research math. Those are flagged 🟢 as awareness-only.

---

## 0. How To Use This File

### 0.1 Legend
| Marker | Meaning |
|---|---|
| `- [ ]` not started · `- [~]` in progress · `- [x]` can build it and defend the design |
| 🔴 | **Must-know.** You will be asked to design or debug this |
| 🟡 | **Should-know.** Comes up in real projects and senior interviews |
| 🟢 | **Awareness.** Know the concept and when to call an expert |
| 🔨 | **Build it** — there is a hands-on deliverable in Part 18 for this topic |

### 0.2 The Senior Lead's Actual Job in GenAI
You are rarely asked to train a model. You **are** asked to:
1. Decide whether AI is even the right solution (often: no) 🔴
2. Choose model + architecture under cost/latency/accuracy/privacy constraints
3. Build retrieval and tool-use that is *correct*, not just demo-able
4. Prove quality with evaluations, not vibes 🔴
5. Prevent prompt injection, data leakage, and unbounded spend 🔴
6. Operate it: observability, caching, fallbacks, rate limits, versioning
7. Explain the trade-offs and the ROI to non-technical leadership

### 0.3 Progress Dashboard

| Part | Area | Priority | Status | Built something? |
|---|---|---|---|---|
| 1 | LLM Foundations | 🔴 | ☐ | ☐ |
| 2 | Model Landscape & Selection | 🔴 | ☐ | ☐ |
| 3 | Prompt Engineering | 🔴 | ☐ | ☐ |
| 4 | Structured Output & Tool Calling | 🔴 | ☐ | ☐ |
| 5 | Embeddings & Vector Search | 🔴 | ☐ | ☐ |
| 6 | RAG — Retrieval Augmented Generation | 🔴 | ☐ | ☐ |
| 7 | Agents & Orchestration | 🔴 | ☐ | ☐ |
| 8 | MCP — Model Context Protocol | 🔴 | ☐ | ☐ |
| 9 | Fine-Tuning & Model Adaptation | 🟡 | ☐ | ☐ |
| 10 | Evaluation & Quality | 🔴 | ☐ | ☐ |
| 11 | Security, Safety & Guardrails | 🔴 | ☐ | ☐ |
| 12 | Java Implementation Stack | 🔴 | ☐ | ☐ |
| 13 | Production Architecture & Ops | 🔴 | ☐ | ☐ |
| 14 | Cost & Latency Engineering | 🔴 | ☐ | ☐ |
| 15 | Infrastructure & Self-Hosting | 🟡 | ☐ | ☐ |
| 16 | Multimodal & Adjacent Capabilities | 🟡 | ☐ | ☐ |
| 17 | Governance, Legal & Compliance | 🟡 | ☐ | ☐ |
| 18 | Leadership & Adoption | 🔴 | ☐ | ☐ |
| 19 | Hands-On Project Ladder | 🔴 | ☐ | ☐ |

---
---

# PART 1 — LLM FOUNDATIONS 🔴

## 1.1 What a Model Actually Does
- [ ] Next-token prediction; autoregressive generation; why "reasoning" emerges from it
- [ ] Tokenization: BPE/SentencePiece, subwords, why token ≠ word, non-English & code token inflation 🔴
- [ ] Token counting in practice (~4 chars ≈ 1 token English; wildly different for code/JSON/CJK)
- [ ] Vocabulary, special tokens, chat templates, system/user/assistant roles
- [ ] Context window: what it includes (system + history + retrieved docs + tools + output) 🔴
- [ ] Context window ≠ effective context: "lost in the middle" degradation 🔴
- [ ] Attention (conceptual): why cost grows with sequence length; KV cache 🟡
- [ ] Transformer architecture at a block-diagram level (embeddings → attention → FFN → logits) 🟡
- [ ] Encoder-only (BERT-family, embeddings) vs decoder-only (GPT-family, generation) vs encoder-decoder 🟡
- [ ] Mixture of Experts (MoE) — why some big models are cheap to serve 🟢
- [ ] Pretraining → instruction tuning → preference tuning (RLHF/DPO) pipeline 🟡
- [ ] Reasoning/thinking models: extended chain-of-thought, thinking budgets, when they're worth the latency 🔴
- [ ] Knowledge cutoff and why the model doesn't know your data 🔴
- [ ] Hallucination: why it happens mechanically, and what does/doesn't reduce it 🔴
- [ ] Determinism: why the same prompt gives different answers; temperature=0 is not fully deterministic 🔴

## 1.2 Inference Parameters 🔴
- [ ] `temperature` — what it actually changes; when 0 is right, when it's wrong
- [ ] `top_p` (nucleus sampling), `top_k`; don't tune both temperature and top_p blindly
- [ ] `max_tokens` / max output tokens; truncation failure mode 🔴
- [ ] `stop` sequences
- [ ] `frequency_penalty` / `presence_penalty` 🟢
- [ ] `seed` for reproducibility (best-effort)
- [ ] `n` / multiple candidates; self-consistency voting
- [ ] Streaming vs non-streaming; time-to-first-token vs total time 🔴
- [ ] Log probabilities and confidence estimation 🟡
- [ ] Thinking/reasoning effort controls where available

## 1.3 Economics & Physics of Inference 🔴
- [ ] Input tokens vs output tokens pricing asymmetry (output usually far more expensive)
- [ ] Prompt caching: what's cacheable, TTL, cost savings, cache-friendly prompt ordering 🔴
- [ ] Batch APIs for non-interactive workloads (large discount, hours of latency)
- [ ] TTFT (time to first token) vs TPOT (time per output token) vs total latency 🔴
- [ ] Why output length dominates latency — and how to shorten outputs by design
- [ ] Throughput vs latency trade-off in serving; batching
- [ ] Rate limits: RPM, TPM, concurrency; how to design around them 🔴
- [ ] Cost per request/session/user — model it before you build 🔴

## 1.4 Capability Boundaries — say "no AI" when correct 🔴
- [ ] Arithmetic & exact computation → use a tool/code, not the model
- [ ] Deterministic business rules → use code, not a prompt 🔴
- [ ] Anything requiring audit-grade correctness without human review
- [ ] Real-time low-latency paths (<100 ms budgets)
- [ ] Tasks where a classifier/regex/search is cheaper and better 🔴
- [ ] Tasks needing guaranteed recall over a large corpus
- [ ] High-stakes autonomous action without human approval
- [ ] Where LLMs genuinely excel: unstructured→structured extraction, summarization, classification with fuzzy criteria, natural-language interfaces, code generation, drafting, semantic search, routing

---
---

# PART 2 — MODEL LANDSCAPE & SELECTION 🔴

## 2.1 The Landscape
- [ ] Frontier closed models: Anthropic Claude family, OpenAI GPT family, Google Gemini family 🔴
- [ ] Claude model line: Opus (max capability), Sonnet (balanced), Haiku (fast/cheap) — and the tier trade-off pattern that repeats across vendors 🔴
- [ ] Open-weight models: Llama, Mistral/Mixtral, Qwen, DeepSeek, Gemma, Phi 🟡
- [ ] Embedding models (separate from chat models) and their dimensions/cost 🔴
- [ ] Reranker models (cross-encoders) 🔴
- [ ] Small/on-device models and their real ceiling 🟡
- [ ] Specialized: code models, vision models, speech (ASR/TTS), OCR/document models 🟡
- [ ] Access paths: direct vendor API, AWS Bedrock, Google Vertex AI, Azure AI Foundry, self-host 🔴
- [ ] Why "best model" changes every quarter — design for swappability 🔴

## 2.2 Selection Framework 🔴
- [ ] Start from the eval set, not the leaderboard 🔴
- [ ] Dimensions: accuracy on *your* task, latency, cost, context window, tool-calling quality, structured-output reliability, multilingual, multimodal, rate limits, region/data residency, provider SLA, fine-tuning availability
- [ ] Model tiering strategy: cheap model for routing/classification, strong model for hard steps 🔴
- [ ] Cascade / fallback pattern: try small → escalate on low confidence 🔴
- [ ] Router models & task classification
- [ ] Open vs closed decision: data sensitivity, cost at volume, latency control, compliance, ops burden 🔴
- [ ] Multi-provider abstraction: avoid deep coupling, but don't over-abstract away capabilities 🔴
- [ ] Version pinning & migration testing when a provider deprecates a model 🔴
- [ ] Benchmarks (MMLU, HumanEval, SWE-bench, GPQA, etc.) — what they do and don't tell you 🟡
- [ ] Contamination and benchmark gaming — why your own eval matters more 🔴

---
---

# PART 3 — PROMPT ENGINEERING 🔴

## 3.1 Fundamentals 🔴
- [ ] Anatomy: system prompt (role, rules, constraints) vs user message vs assistant prefill
- [ ] Be specific: task, audience, format, length, tone, constraints, success criteria
- [ ] Show, don't just tell: few-shot examples and how many are enough
- [ ] Zero-shot vs one-shot vs few-shot; example selection & ordering effects
- [ ] Delimiters & structure (XML tags, markdown headers, JSON) — reduces ambiguity 🔴
- [ ] Putting long documents *before* the instruction for long-context models 🟡
- [ ] Prefilling the assistant response to force format
- [ ] Negative instructions are weak — state what to do, not only what not to do
- [ ] Explicit "if you don't know, say so" + grounding rules to reduce hallucination 🔴
- [ ] Output format specification & schema in the prompt
- [ ] Prompt length vs quality: longer isn't better past a point
- [ ] Role/persona prompting — where it helps, where it's cargo cult
- [ ] Language & locale handling

## 3.2 Reasoning Techniques 🔴
- [ ] Chain-of-thought: explicit step-by-step; when it helps and when it wastes tokens
- [ ] Structured reasoning tags (`<thinking>`, then a clean final answer) 🔴
- [ ] Self-consistency: sample N, majority vote 🟡
- [ ] Decomposition: break one hard prompt into a chain of simple ones 🔴
- [ ] Plan-then-execute
- [ ] Self-critique / reflexion loops — and their diminishing returns 🟡
- [ ] ReAct (reason + act) for tool use 🔴
- [ ] Least-to-most prompting 🟢
- [ ] Tree of thoughts / graph of thoughts 🟢
- [ ] Native reasoning models vs prompted CoT — when to just use the reasoning model 🔴

## 3.3 Engineering Prompts Like Code 🔴
- [ ] Prompts live in version control, not in string literals scattered across services 🔴
- [ ] Prompt templating & variable injection (and escaping user input!) 🔴
- [ ] Prompt versioning & A/B testing in production
- [ ] Prompt registry / management (config service, DB, or a managed tool)
- [ ] Separating stable system prompt (cacheable) from volatile content 🔴
- [ ] Token budgeting per prompt section (system / history / retrieved / output)
- [ ] Regression testing prompts against a golden set on every change 🔴
- [ ] Prompt "diff review" as part of code review
- [ ] Multi-tenant prompt customization without forking the pipeline
- [ ] Localization of prompts
- [ ] Documenting prompt intent and known failure modes

## 3.4 Context Engineering 🔴
*(The senior-level evolution of prompt engineering: managing what enters the window.)*
- [ ] Context budget allocation across system, tools, history, retrieval, output 🔴
- [ ] Conversation history strategies: full, sliding window, summarization, hierarchical summary 🔴
- [ ] Compaction: when to summarize and what must survive compaction verbatim (IDs, decisions, constraints) 🔴
- [ ] Selective retrieval — fetch on demand instead of stuffing everything 🔴
- [ ] Tool result truncation & pagination
- [ ] Ordering: most important content near the start/end (recency & primacy effects)
- [ ] Deduplicating retrieved content
- [ ] Structured state (a JSON scratchpad the agent updates) vs free-text memory
- [ ] Long-context vs RAG: when a 1M-token window replaces retrieval, and when it doesn't (cost, latency, precision) 🔴
- [ ] Measuring context utilization and pruning what never influences output

---
---

# PART 4 — STRUCTURED OUTPUT & TOOL CALLING 🔴

## 4.1 Structured Output 🔴
- [ ] Why free text breaks pipelines; structured output as an integration contract
- [ ] JSON mode vs schema-constrained/structured outputs vs prompt-only JSON 🔴
- [ ] JSON Schema design for LLMs: flat > deeply nested, enums over free strings, descriptions matter 🔴
- [ ] Required vs optional fields; nullability; defaults
- [ ] Handling refusals and "unknown" values explicitly in the schema 🔴
- [ ] Parsing & validation on your side regardless of provider guarantees 🔴
- [ ] Repair loop: validation error → feed back → retry (with a cap) 🔴
- [ ] Streaming partial JSON and incremental parsing 🟡
- [ ] Extraction patterns: document → typed record, with confidence and provenance
- [ ] Classification with a fixed label set + "other"
- [ ] Java: mapping to records/POJOs, Jackson validation, Bean Validation on outputs 🔴
- [ ] Cost of schema complexity on accuracy — simplify the schema before blaming the model

## 4.2 Tool / Function Calling 🔴
- [ ] Mechanics: you send tool definitions → model returns a tool-use request → you execute → return result → model continues 🔴
- [ ] Tool schema design: name, description, parameter schema; the description IS the prompt 🔴
- [ ] Writing tool descriptions that actually get used correctly (examples, when-to-use, when-NOT-to-use) 🔴
- [ ] Number of tools vs accuracy; tool set curation and dynamic tool filtering 🔴
- [ ] Parallel tool calls; sequential dependencies
- [ ] Forced tool use / tool choice control
- [ ] Handling tool errors: return structured errors the model can recover from, not stack traces 🔴
- [ ] Timeouts, retries and idempotency for tools 🔴
- [ ] **Authorization for tools: the model must never be the security boundary** 🔴
- [ ] Confirmation gates for destructive/irreversible tools (write, delete, send, pay) 🔴
- [ ] Tool result size management (truncate, paginate, summarize)
- [ ] Observability per tool call: latency, error rate, invocation counts
- [ ] Testing tools independently of the model
- [ ] Code execution as a tool (sandboxing!) 🔴
- [ ] Computer use / browser automation — capabilities and risks 🟡

---
---

# PART 5 — EMBEDDINGS & VECTOR SEARCH 🔴

## 5.1 Embeddings 🔴
- [ ] What an embedding is; semantic similarity in vector space
- [ ] Dimensions, model families, Matryoshka/truncatable embeddings 🟡
- [ ] Similarity metrics: cosine, dot product, Euclidean — and normalization 🔴
- [ ] Symmetric vs asymmetric search (query vs document embeddings, instruction-tuned embedders) 🔴
- [ ] Embedding model selection: MTEB, but validate on your domain 🔴
- [ ] Domain adaptation & fine-tuned embedders 🟡
- [ ] Multilingual embeddings
- [ ] Multimodal embeddings (text↔image) 🟡
- [ ] Embedding drift when you change models → full re-index required 🔴
- [ ] Cost and latency of embedding at ingest and at query time
- [ ] Caching embeddings; deduplication by content hash
- [ ] Batch embedding pipelines & rate limits

## 5.2 Vector Indexes & Databases 🔴
- [ ] Exact (flat) search vs approximate nearest neighbor (ANN); recall vs latency trade-off 🔴
- [ ] HNSW: graph structure, `M`, `efConstruction`, `efSearch` tuning 🔴
- [ ] IVF / IVF-PQ; product quantization; memory savings vs recall 🟡
- [ ] ScaNN, DiskANN 🟢
- [ ] Quantization: float32 → int8 → binary; memory & recall impact 🟡
- [ ] Filtering: pre-filter vs post-filter, and why metadata filtering breaks naive ANN 🔴
- [ ] Hybrid search: BM25/keyword + vector, fusion methods (RRF, weighted) 🔴
- [ ] Sparse vectors (SPLADE, BM25 as vectors) 🟡
- [ ] Index size math: `vectors × dims × bytes` + graph overhead 🔴
- [ ] Updates, deletes and tombstones; re-index strategy 🔴
- [ ] Sharding & replication of a vector index
- [ ] Multi-tenancy: namespace per tenant vs metadata filter vs separate index 🔴
- [ ] Options: **pgvector/pgvectorscale** (start here if you already run Postgres), Elasticsearch/OpenSearch kNN, Redis vector, Qdrant, Milvus, Weaviate, Pinecone, Vespa, Chroma, LanceDB 🔴
- [ ] Decision framework: do you actually need a dedicated vector DB? (often no) 🔴
- [ ] Backup, disaster recovery and reproducible re-indexing from source of truth 🔴

---
---

# PART 6 — RAG (RETRIEVAL AUGMENTED GENERATION) 🔴 🔨

## 6.1 Why RAG, and When Not To 🔴
- [ ] The problem RAG solves: private/current data, grounding, citation, cost vs fine-tuning
- [ ] RAG vs fine-tuning vs long-context vs tool-calling-a-real-API — decision matrix 🔴
- [ ] When RAG is the wrong tool: precise structured queries (use SQL), small corpora (stuff the context), constantly-changing transactional data (call the API) 🔴
- [ ] "Retrieval" doesn't have to be vector search — SQL, search index, graph, or an API call all count 🔴

## 6.2 Ingestion Pipeline 🔴
- [ ] Source connectors: files, S3, Confluence/SharePoint, DBs, tickets, code repos, web
- [ ] Format parsing: PDF (layout, tables, scans), DOCX, HTML, Markdown, CSV, images 🔴
- [ ] PDF is the hard one: text layer vs OCR, multi-column, tables, headers/footers 🔴
- [ ] OCR & document AI options 🟡
- [ ] Cleaning: boilerplate removal, dedup, normalization, language detection
- [ ] Table & chart handling (linearize, summarize, or store separately) 🔴
- [ ] Code-aware parsing (by function/class, not by characters)
- [ ] Metadata extraction: title, section, author, date, source URL, ACL, tenant 🔴
- [ ] **Permissions at ingest**: store ACLs with chunks or you will leak data 🔴
- [ ] Incremental sync: change detection, upserts, deletes, tombstones 🔴
- [ ] Idempotent, replayable ingestion (content hash as the key) 🔴
- [ ] Pipeline orchestration & failure handling; poison documents
- [ ] Freshness SLA and re-index cadence
- [ ] Observability: docs ingested, chunks created, failures by type

## 6.3 Chunking 🔴
- [ ] Why chunking exists (retrieval precision + context budget)
- [ ] Fixed-size with overlap; choosing size (typ. 256–1024 tokens) and overlap (10–20%) 🔴
- [ ] Recursive/structure-aware splitting (headings → paragraphs → sentences) 🔴
- [ ] Semantic chunking (embedding-similarity boundaries) 🟡
- [ ] Document-structure chunking (by section, by slide, by row group)
- [ ] Parent-document / small-to-big: embed small, return large 🔴
- [ ] Contextual retrieval: prepend a generated context blurb to each chunk before embedding 🔴
- [ ] Sentence-window retrieval 🟡
- [ ] Chunk metadata: doc id, section path, position, source link for citation 🔴
- [ ] Chunking is the #1 quality lever people ignore — evaluate multiple strategies 🔴
- [ ] Handling tables, code blocks and lists so they don't get split mid-structure

## 6.4 Retrieval 🔴
- [ ] Top-k selection and why k matters more than model choice sometimes
- [ ] Similarity thresholds & "no relevant results" handling → must be able to say "I don't know" 🔴
- [ ] Hybrid retrieval (BM25 + dense) with Reciprocal Rank Fusion 🔴
- [ ] Metadata filtering (tenant, ACL, date, doc type) applied *before* ranking 🔴
- [ ] Query transformation: rewriting, expansion, spelling correction 🔴
- [ ] Multi-query / query fan-out and result fusion 🟡
- [ ] HyDE (hypothetical document embeddings) 🟡
- [ ] Step-back prompting for broader context 🟢
- [ ] Query routing: which index/source should answer this? 🔴
- [ ] Conversational retrieval: resolving pronouns/follow-ups into standalone queries 🔴
- [ ] Recency & authority boosting
- [ ] Diversity (MMR) to avoid 5 near-identical chunks 🟡
- [ ] Retrieval latency budget & parallel retrieval across sources

## 6.5 Reranking & Context Assembly 🔴
- [ ] Cross-encoder rerankers: retrieve 50 → rerank → keep 5 🔴
- [ ] Reranker cost/latency vs quality gain
- [ ] LLM-as-reranker for small candidate sets 🟡
- [ ] Deduplication and merging adjacent chunks
- [ ] Ordering retrieved context (best last or best first — test it) 🟡
- [ ] Context compression / extractive filtering before generation 🟡
- [ ] Token budget enforcement with graceful truncation
- [ ] Attaching citations/source ids to each chunk for grounded answers 🔴

## 6.6 Generation & Grounding 🔴
- [ ] Grounding instructions: "answer only from the context; if absent, say you don't know" 🔴
- [ ] Citation generation and verification (does the cited chunk actually support the claim?) 🔴
- [ ] Refusal/abstention behavior as a feature, not a bug
- [ ] Handling conflicting sources
- [ ] Answer formatting & length control
- [ ] Streaming answers with citations
- [ ] Follow-up question suggestions
- [ ] Guarding against injected instructions inside retrieved documents 🔴🔴

## 6.7 Advanced RAG Patterns 🟡
- [ ] Agentic RAG: the model decides what/whether to retrieve, iteratively 🔴
- [ ] Self-RAG / corrective RAG (retrieve → critique → re-retrieve) 🟡
- [ ] Multi-hop retrieval for questions requiring chained facts 🔴
- [ ] GraphRAG: entity/relationship graph + community summaries; when it's worth the cost 🟡
- [ ] Structured + unstructured hybrid (text2SQL for numbers, RAG for prose) 🔴
- [ ] Text-to-SQL: schema in context, few-shot, validation, read-only role, query allowlisting 🔴
- [ ] Summary indexes & hierarchical retrieval (RAPTOR) 🟡
- [ ] Router over multiple specialized indexes 🔴
- [ ] Long-context "no-retrieval" baseline — always compare against it 🔴
- [ ] Caching: semantic cache of Q→A pairs, with invalidation on re-index 🔴

## 6.8 RAG Failure Modes — memorize this list 🔴
- [ ] Missing content (it isn't in the corpus) → ingestion problem
- [ ] Missed the top-k (it exists but wasn't retrieved) → chunking/embedding/hybrid problem
- [ ] Not in the consolidated context (retrieved but truncated) → budget/rerank problem
- [ ] Not extracted (in context but the model missed it) → prompt/position/model problem
- [ ] Wrong format
- [ ] Incorrect specificity (too general / too narrow)
- [ ] Incomplete answer (multi-hop failure)
- [ ] Hallucinated despite context (grounding-prompt problem)
- [ ] Stale answer (index freshness problem)
- [ ] Data leak across tenants/users (ACL problem) 🔴
- [ ] **Diagnosis discipline: instrument each stage so you know WHICH one failed** 🔴

---
---

# PART 7 — AGENTS & ORCHESTRATION 🔴

## 7.1 Definitions & Sober Expectations 🔴
- [ ] Workflow (predetermined code path, LLM at steps) vs agent (LLM decides the path) 🔴
- [ ] **Start with the simplest thing that works: single prompt → chain → router → agent** 🔴
- [ ] Cost of autonomy: latency, spend, nondeterminism, debugging difficulty 🔴
- [ ] Error compounding across steps (95% per step ⁿ) — the core reason agents fail 🔴
- [ ] When agents genuinely win: open-ended tasks, variable step counts, tool-heavy workflows
- [ ] When they lose: fixed pipelines, latency-sensitive paths, high-stakes actions

## 7.2 Core Patterns 🔴
- [ ] Prompt chaining (sequential decomposition)
- [ ] Routing / classification then specialization
- [ ] Parallelization: sectioning and voting
- [ ] Orchestrator-workers (a planner spawning subtasks) 🔴
- [ ] Evaluator-optimizer (generate → critique → revise loop)
- [ ] ReAct loop (thought → action → observation) 🔴
- [ ] Plan-and-execute
- [ ] Reflection & self-correction, with iteration caps 🔴
- [ ] Human-in-the-loop checkpoints & approval gates 🔴
- [ ] Tool-use agent as the default shape for most enterprise use cases

## 7.3 Agent Engineering Concerns 🔴
- [ ] The agent loop: state, step limit, budget limit, timeout, termination conditions 🔴
- [ ] Stopping criteria & runaway-loop prevention (max steps, max tokens, max cost) 🔴
- [ ] Memory: short-term (context), working (scratchpad/state), long-term (vector/DB) 🔴
- [ ] Memory write policy — what's worth remembering, and forgetting/expiry 🟡
- [ ] Statefulness & durability: resuming a long-running agent after a crash 🔴
- [ ] Checkpointing & durable execution (Temporal-style) for multi-minute agents 🟡
- [ ] Tool result handling, truncation, and secondary summarization
- [ ] Subagents: isolation of context, cost control, result aggregation 🟡
- [ ] Multi-agent systems: when they help vs when they're expensive theater 🔴
- [ ] Agent-to-agent communication & handoff patterns 🟡
- [ ] Sandboxing code execution & filesystem access 🔴
- [ ] Permissions model: what the agent may do without asking 🔴
- [ ] Audit trail of every agent action 🔴
- [ ] Observability: full trace of prompts, tool calls, results, tokens, cost per run 🔴
- [ ] Testing agents: deterministic fixtures, replay of recorded traces, simulation environments 🔴
- [ ] Idempotency for agent-triggered side effects 🔴

## 7.4 Frameworks & Building It Yourself 🟡
- [ ] LangChain / LangGraph (graphs, state, checkpointing) — strengths and complexity cost
- [ ] LlamaIndex (retrieval-centric)
- [ ] Vendor agent SDKs and hosted agent runtimes
- [ ] CrewAI, AutoGen, Semantic Kernel 🟢
- [ ] **Java: LangChain4j, Spring AI** 🔴
- [ ] Temporal / durable workflow engines for reliable long-running agents 🟡
- [ ] The "just write the loop yourself" option — often correct for production 🔴
- [ ] Framework lock-in risk and the abstraction tax

---
---

# PART 8 — MCP (MODEL CONTEXT PROTOCOL) 🔴 🔨

## 8.1 What & Why 🔴
- [ ] The N×M integration problem MCP solves (M models/hosts × N tools) 🔴
- [ ] Open standard, originated at Anthropic (2024), broad multi-vendor adoption
- [ ] Positioning: MCP standardizes *how a model-facing app connects to context and tools* — it is not an agent framework, not a model API 🔴
- [ ] Compare to: OpenAPI (describes HTTP APIs for humans/codegen), plugins (vendor-specific), A2A (agent-to-agent) 🟡
- [ ] Spec versioning by date string (e.g. `2025-06-18`, `2025-11-25`); negotiate, don't assume 🔴

## 8.2 Architecture 🔴
- [ ] **Host** — the LLM application (IDE, chat app, agent runtime) that the user trusts
- [ ] **Client** — lives in the host, maintains a 1:1 stateful session with one server
- [ ] **Server** — exposes capabilities; local process or remote service
- [ ] JSON-RPC 2.0 message layer: requests, responses, notifications 🔴
- [ ] Lifecycle: `initialize` → capability negotiation → `initialized` → operation → shutdown 🔴
- [ ] Capability negotiation — both sides declare what they support 🔴
- [ ] Servers are isolated from each other; the host mediates 🔴
- [ ] The host controls what the model actually sees (server output is data, not commands) 🔴

## 8.3 Server Primitives 🔴
- [ ] **Tools** (model-controlled): `tools/list`, `tools/call`; name, description, `inputSchema`, optional `outputSchema` 🔴
- [ ] Tool annotations/hints: read-only, destructive, idempotent, open-world — advisory, never a security control 🔴
- [ ] Tool results: content blocks (text, image, resource links), `isError` handling 🔴
- [ ] Structured tool output & schema validation
- [ ] **Resources** (application-controlled): `resources/list`, `resources/read`, URI-addressed context (files, records, docs) 🔴
- [ ] Resource templates (URI templates with parameters), `resources/subscribe` + update notifications 🟡
- [ ] **Prompts** (user-controlled): `prompts/list`, `prompts/get` — reusable templates surfaced as slash commands/menus 🔴
- [ ] Choosing the right primitive: tool for actions, resource for context, prompt for user-invoked workflows 🔴
- [ ] `list_changed` notifications for dynamic capability sets
- [ ] Pagination via cursors on list operations
- [ ] Completions for argument autocomplete 🟡

## 8.4 Client Primitives 🟡
- [ ] **Sampling**: a server asks the host's model for a completion (server needs no API key); host approval & model preferences 🔴
- [ ] **Roots**: the client tells the server which filesystem/URI boundaries it may operate in 🔴
- [ ] **Elicitation**: a server requests structured input from the user mid-operation (added 2025-06-18) 🟡
- [ ] **Logging**: server → client log messages with levels
- [ ] Progress notifications for long operations, and cancellation 🟡
- [ ] Why these invert the usual direction and why they need user consent 🔴

## 8.5 Transports 🔴
- [ ] **stdio** — local subprocess, simplest, most common for desktop/CLI hosts 🔴
- [ ] **Streamable HTTP** — the remote transport (single endpoint, optional SSE streaming, session ids) 🔴
- [ ] Legacy HTTP+SSE transport (pre-2025-03-26) — deprecated; know it exists for compatibility 🟡
- [ ] Session management, resumability, and reconnection semantics 🟡
- [ ] Custom transports 🟢
- [ ] Choosing: local data/tools → stdio; shared/multi-user service → Streamable HTTP 🔴

## 8.6 Authentication & Authorization 🔴
- [ ] stdio servers: credentials via environment, never in the protocol 🔴
- [ ] HTTP servers: OAuth 2.1 authorization framework in the spec 🔴
- [ ] MCP server as an OAuth **resource server**; separate authorization server 🔴
- [ ] Protected Resource Metadata (RFC 9728) discovery; dynamic client registration 🟡
- [ ] Resource Indicators (RFC 8707) — tokens must be audience-bound to the specific MCP server 🔴
- [ ] **Token passthrough is explicitly forbidden** — a server must not forward the client's token to upstream APIs 🔴
- [ ] Consent screens; user must approve which server gets which scope 🔴
- [ ] Enterprise: SSO/IdP integration, per-user vs per-service identity, short-lived tokens 🔴

## 8.7 MCP Security — the part people skip 🔴🔴
- [ ] **Tool descriptions are untrusted input to the model** — treat server-provided text as data 🔴
- [ ] Tool poisoning / rug-pull: a server changing a tool's behavior or description after approval 🔴
- [ ] Prompt injection delivered through resource or tool-result content 🔴
- [ ] Confused deputy: the host acting with its own privileges on a server's instruction 🔴
- [ ] Cross-server attacks / tool shadowing when multiple servers are connected 🔴
- [ ] Session hijacking on HTTP transports; validate `Origin`, bind sessions to users, use non-deterministic session ids 🔴
- [ ] Localhost binding for local HTTP servers; don't expose 0.0.0.0 🔴
- [ ] Command injection & path traversal inside tool implementations 🔴
- [ ] Data exfiltration via a tool that can both read secrets and make network calls (capability combination risk) 🔴
- [ ] Human approval for destructive/irreversible tools 🔴
- [ ] Server allowlisting, pinning, signature/provenance checks; running untrusted servers in a sandbox/container 🔴
- [ ] Rate limiting, quota and cost controls per server
- [ ] Audit logging of every tool invocation with user identity 🔴
- [ ] Threat-model an MCP deployment as an exercise 🔨

## 8.8 Building MCP Servers & Clients 🔴 🔨
- [ ] SDK landscape: TypeScript, Python, **Java**, Kotlin, C#, Go, Rust, Ruby, Swift, PHP 🔴
- [ ] Java: MCP Java SDK; Spring AI MCP client & server starters (stdio + streamable HTTP) 🔴
- [ ] Building a server: define tools/resources/prompts, wire the transport, handle errors 🔨
- [ ] Designing good tools for models (naming, descriptions, granularity, few coarse tools > many fine ones) 🔴
- [ ] Returning results the model can use (concise, structured, with next-step hints)
- [ ] Testing: MCP Inspector, unit tests per tool, contract tests 🔴
- [ ] Building a client/host: connection management, capability discovery, consent UI, tool routing 🟡
- [ ] Wrapping an existing internal REST API as an MCP server — the common enterprise task 🔴 🔨
- [ ] Deployment: containerized remote servers, health checks, scaling, multi-tenancy 🔴
- [ ] Registry/discovery of servers in an org; internal catalog & governance 🟡
- [ ] Versioning & backward compatibility of your tools 🔴
- [ ] Observability: per-tool latency, error rate, token impact, cost attribution
- [ ] When NOT to use MCP: a single hardcoded internal integration, or a latency-critical inner loop 🔴

---
---

# PART 9 — FINE-TUNING & MODEL ADAPTATION 🟡

## 9.1 Decide Before You Tune 🔴
- [ ] The ladder: prompt → few-shot → RAG → tool use → fine-tune → pretrain (go down only when forced) 🔴
- [ ] What fine-tuning is good at: format/style/tone adherence, domain jargon, latency & cost via smaller models, narrow classification 🔴
- [ ] What it is **bad** at: injecting new factual knowledge reliably (use RAG), keeping data current 🔴
- [ ] Data requirements: usually hundreds–thousands of high-quality examples; quality ≫ quantity 🔴
- [ ] Total cost: data labeling, training, evaluation, hosting, re-tuning on model upgrades 🔴
- [ ] Lock-in: a fine-tuned model ties you to a base model version 🔴

## 9.2 Techniques 🟡
- [ ] Supervised fine-tuning (SFT) / instruction tuning
- [ ] PEFT: LoRA and QLoRA — rank, alpha, target modules, adapter merging 🟡
- [ ] Full fine-tuning vs adapters — cost & flexibility
- [ ] Preference optimization: RLHF, DPO, ORPO (concepts) 🟢
- [ ] Distillation: big model generates data → train a small model 🟡
- [ ] Continued pretraining on domain corpora 🟢
- [ ] Embedding model fine-tuning for retrieval quality 🟡
- [ ] Reranker fine-tuning 🟢
- [ ] Quantization for serving: GPTQ, AWQ, GGUF, int8/int4 quality impact 🟡
- [ ] Catastrophic forgetting & regression on general capability 🔴

## 9.3 Practice 🟡
- [ ] Dataset construction: sourcing, labeling, dedup, contamination check, train/val/test split 🔴
- [ ] Data quality gates & inter-annotator agreement
- [ ] Synthetic data generation and its risks (model collapse, bias amplification) 🟡
- [ ] Hyperparameters that matter: epochs, LR, batch size (and overfitting signs)
- [ ] Evaluating a fine-tune against the base model on YOUR eval set 🔴
- [ ] Serving: hosted fine-tuning vs self-hosted adapters; multi-adapter serving 🟡
- [ ] Versioning models and datasets together; reproducibility 🔴
- [ ] Rollback plan and shadow evaluation before switching traffic 🔴

---
---

# PART 10 — EVALUATION & QUALITY 🔴 🔨

## 10.1 Why Evals Are the Job 🔴
- [ ] "Vibes-based" development is the #1 cause of failed AI projects 🔴
- [ ] Evals as regression tests for a nondeterministic system 🔴
- [ ] Build the eval set **before** optimizing the prompt/pipeline 🔴
- [ ] Eval-driven development loop: baseline → change → measure → keep/revert 🔴
- [ ] Who owns the eval set (domain experts, not just engineers)

## 10.2 Building an Eval Set 🔴
- [ ] Golden dataset: real user queries, edge cases, adversarial cases, known failures 🔴
- [ ] Size: start with 30–50 well-chosen cases; grow from production failures 🔴
- [ ] Labeling rubric & ground truth definition; handling multiple valid answers
- [ ] Stratification by intent/difficulty/tenant/language
- [ ] Continuous harvesting: every production failure becomes an eval case 🔴
- [ ] Holdout to prevent overfitting the eval set
- [ ] Versioning eval sets alongside prompts and code 🔴

## 10.3 Metrics 🔴
- [ ] Deterministic checks first: schema valid, required fields, regex, exact match, numeric tolerance 🔴
- [ ] Classification metrics: accuracy, precision/recall, F1, confusion matrix — for routing/extraction 🔴
- [ ] Text similarity: exact/fuzzy match, ROUGE/BLEU (limited value) 🟢
- [ ] **RAG retrieval metrics**: recall@k, precision@k, MRR, NDCG, hit rate 🔴
- [ ] **RAG generation metrics**: faithfulness/groundedness, answer relevance, context precision/recall, citation accuracy 🔴
- [ ] Agent metrics: task success rate, steps taken, tool-call accuracy, cost per task, human-intervention rate 🔴
- [ ] Safety metrics: refusal correctness, injection resistance, PII leakage rate 🔴
- [ ] Operational metrics: latency p50/p99, TTFT, cost/request, error/timeout rate 🔴
- [ ] Business metrics: deflection rate, time saved, conversion, CSAT, escalation rate 🔴

## 10.4 LLM-as-Judge 🟡
- [ ] When it's appropriate (subjective quality) and when it isn't (factual correctness with ground truth) 🔴
- [ ] Rubric design; scoring scales; pairwise comparison > absolute scoring 🔴
- [ ] Known biases: position, verbosity, self-preference; mitigation (swap order, blind labels) 🔴
- [ ] Calibrating the judge against human labels — always do this 🔴
- [ ] Cost of judging; using a cheaper judge model
- [ ] Reference-free vs reference-based judging

## 10.5 Testing in the SDLC 🔴
- [ ] Unit tests for deterministic pieces (parsers, chunkers, retrievers, tools) 🔴
- [ ] Snapshot/record-replay tests with cached model responses for CI speed 🔴
- [ ] Contract tests for tool schemas
- [ ] Eval run as a CI gate with thresholds (fail the build on regression) 🔴
- [ ] Nondeterminism handling: fixed seeds, N-run averaging, tolerance bands 🔴
- [ ] Red-teaming as a test suite (see Part 11) 🔴
- [ ] Load & cost testing
- [ ] Shadow deployment / offline replay against production traffic 🔴
- [ ] A/B testing and online metrics; guardrail metrics
- [ ] Human review sampling in production (rated queue) 🔴
- [ ] Tools: promptfoo, Ragas, DeepEval, OpenAI Evals, LangSmith, Langfuse, Braintrust, Arize/Phoenix 🟡

---
---

# PART 11 — SECURITY, SAFETY & GUARDRAILS 🔴

## 11.1 OWASP Top 10 for LLM Applications 🔴
- [ ] LLM01 Prompt Injection (direct & indirect) 🔴
- [ ] LLM02 Sensitive Information Disclosure 🔴
- [ ] LLM03 Supply Chain (models, datasets, plugins, MCP servers) 🔴
- [ ] LLM04 Data & Model Poisoning
- [ ] LLM05 Improper Output Handling (treating model output as trusted code/SQL/HTML) 🔴
- [ ] LLM06 Excessive Agency (too many tools, too much permission) 🔴
- [ ] LLM07 System Prompt Leakage
- [ ] LLM08 Vector & Embedding Weaknesses (cross-tenant leakage, inversion) 🔴
- [ ] LLM09 Misinformation / overreliance
- [ ] LLM10 Unbounded Consumption (cost & DoS) 🔴

## 11.2 Prompt Injection — the central problem 🔴
- [ ] Direct injection ("ignore previous instructions") vs **indirect** (payload hidden in a document, web page, email, tool result, MCP resource) 🔴
- [ ] Why there is no complete fix — design assuming injection succeeds 🔴
- [ ] Trust boundary discipline: **instructions come only from your system prompt and the authenticated user** 🔴
- [ ] Never let retrieved/tool content grant privileges or trigger actions directly 🔴
- [ ] Delimiting and labeling untrusted content in the prompt (helps, doesn't solve)
- [ ] Least privilege on tools; separate read-capable and write-capable agents 🔴
- [ ] Human confirmation for irreversible actions 🔴
- [ ] Output-side defenses: validate, sanitize, never auto-execute 🔴
- [ ] Detection: injection classifiers, heuristics, canary tokens 🟡
- [ ] Dual-LLM / quarantine pattern for untrusted content 🟡
- [ ] Exfiltration vectors: markdown images, links with data in query params, tool calls to attacker URLs 🔴
- [ ] Test suite of injection payloads run in CI 🔴 🔨

## 11.3 Data Protection 🔴
- [ ] Data flow map: what leaves your perimeter, to which vendor, under what terms 🔴
- [ ] Vendor data usage & retention policies; zero-retention/enterprise tiers 🔴
- [ ] PII detection & redaction before sending to the model 🔴
- [ ] Tokenization/pseudonymization and re-identification after the response 🟡
- [ ] Secrets never in prompts; scanning prompts for credentials 🔴
- [ ] Tenant isolation in vector stores and caches 🔴
- [ ] ACL-aware retrieval: filter by the *requesting user's* permissions at query time 🔴
- [ ] Logging discipline: prompts/completions contain user data — redact, restrict, expire 🔴
- [ ] Training-data opt-out and contractual guarantees
- [ ] Cross-border data transfer & residency (region-pinned endpoints) 🔴
- [ ] Right to erasure across indexes, caches and logs 🔴

## 11.4 Output Safety & Guardrails 🔴
- [ ] Input guardrails: topic/intent filtering, injection detection, PII scan, length/rate limits
- [ ] Output guardrails: schema validation, toxicity/safety classifier, PII scan, groundedness check, policy rules 🔴
- [ ] Never render model output as raw HTML/markdown-with-scripts; escape it 🔴
- [ ] Never execute model-generated SQL/shell/code without sandbox + allowlist 🔴
- [ ] Deterministic post-processing for business rules 🔴
- [ ] Refusal & escalation paths; "I don't know" as a first-class outcome 🔴
- [ ] Content moderation APIs and self-hosted classifiers (Llama Guard etc.) 🟡
- [ ] Citation verification for grounded answers
- [ ] Confidence signals & when to route to a human 🔴
- [ ] Disclosure to users that they're talking to AI (often a legal requirement) 🔴

## 11.5 Abuse, Cost & Availability 🔴
- [ ] Per-user/per-tenant token quotas and hard spend caps 🔴
- [ ] Rate limiting at API and model layer; queueing and backpressure
- [ ] Prompt-bomb / long-input DoS; input size caps 🔴
- [ ] Recursive/agentic runaway loops → step & budget caps 🔴
- [ ] Caching to blunt repeat-cost attacks
- [ ] Anomaly alerting on spend and token volume 🔴
- [ ] Model provider outage → fallback model/provider, degraded mode 🔴
- [ ] Jailbreak monitoring & response process

## 11.6 Red Teaming 🟡 🔨
- [ ] Build an adversarial prompt suite for your app (injection, jailbreak, exfiltration, PII, bias, harmful content) 🔴
- [ ] Automated red-team runs in CI; track resistance rate over time 🔴
- [ ] Domain-specific abuse cases (financial advice, medical, legal, discrimination) 🔴
- [ ] Bug bounty / responsible disclosure for AI features
- [ ] Incident response plan for an AI-specific incident (leak, harmful output, injected action) 🔴

---
---

# PART 12 — JAVA IMPLEMENTATION STACK 🔴 🔨

## 12.1 Spring AI 🔴
- [ ] `ChatClient` fluent API; `ChatModel` / `EmbeddingModel` / `ImageModel` abstractions
- [ ] Provider portability: Anthropic, OpenAI, Bedrock, Vertex, Azure, Ollama, and the limits of portability 🔴
- [ ] Prompt templates & `PromptTemplate`
- [ ] Structured output converters → records/POJOs (`BeanOutputConverter`) 🔴
- [ ] Tool/function calling: `@Tool` annotations, `ToolCallback`, tool context 🔴
- [ ] Advisors: chat memory, QA/RAG advisor, logging, safe-guard advisors 🔴
- [ ] Chat memory implementations (in-memory, JDBC, Redis) & window/summary strategies 🔴
- [ ] `VectorStore` abstraction: pgvector, Redis, Elasticsearch, Qdrant, Milvus, Pinecone, Chroma 🔴
- [ ] Document readers (PDF, Tika, Markdown, JSON) & `DocumentTransformer` splitters 🔴
- [ ] ETL pipeline: reader → transformer → writer 🔨
- [ ] `@Observed` / Micrometer integration for tokens, latency, cost 🔴
- [ ] Spring AI **MCP client** starter (stdio & streamable HTTP) 🔴
- [ ] Spring AI **MCP server** starter — exposing your Spring beans as MCP tools 🔴 🔨
- [ ] Streaming responses with `Flux` / SSE to the browser 🔴
- [ ] Testing Spring AI code (mock `ChatModel`, recorded responses)
- [ ] Configuration, profiles, and per-tenant model selection

## 12.2 LangChain4j 🟡
- [ ] `ChatLanguageModel` / `StreamingChatLanguageModel`
- [ ] AI Services (declarative interfaces → prompts) 🔴
- [ ] Tools (`@Tool`) and tool execution
- [ ] Chat memory, memory stores
- [ ] `EmbeddingStore` + ingestor; document loaders & splitters
- [ ] `RetrievalAugmentor`, query transformers, content aggregators, rerankers 🔴
- [ ] MCP client support 🟡
- [ ] Spring Boot / Quarkus integrations
- [ ] LangChain4j vs Spring AI — how to choose 🔴

## 12.3 Direct SDKs & Plumbing 🔴
- [ ] Official Anthropic Java SDK / OpenAI Java SDK — when to skip the framework 🔴
- [ ] HTTP client choice, connection pooling, timeouts, retries with backoff+jitter 🔴
- [ ] Streaming: SSE parsing, partial JSON, cancellation, client disconnect handling 🔴
- [ ] Virtual threads for high-concurrency LLM I/O (thread-per-request without the cost) 🔴
- [ ] `CompletableFuture` / Reactor pipelines for parallel LLM + retrieval calls 🔴
- [ ] Rate-limit handling: 429 backoff, token-bucket client-side limiter, queueing 🔴
- [ ] Circuit breaker + fallback model (Resilience4j) 🔴
- [ ] Timeouts tuned for streaming vs non-streaming
- [ ] Serialization of message history; token counting on the JVM
- [ ] Secrets management for API keys (Vault/secret manager, never in config) 🔴
- [ ] Multi-tenancy: per-tenant keys, quotas, model choice, data isolation 🔴

## 12.4 Reference Java Architecture 🔴 🔨
- [ ] Layering: controller → orchestration service → (retriever | tools | model client) → guardrails → response
- [ ] Where to put prompts (resources + version control), where to put schemas
- [ ] Async ingestion pipeline (Spring Batch / Kafka consumers → chunk → embed → upsert) 🔨
- [ ] Postgres + pgvector as the default starting stack 🔴
- [ ] Caching layers: semantic cache (Redis), prompt cache (provider), response cache
- [ ] Observability wiring: Micrometer + OpenTelemetry spans per stage 🔴
- [ ] Feature flags for model/prompt rollout 🔴
- [ ] Idempotency for agent-triggered writes 🔴
- [ ] Testing strategy across the whole pipeline

---
---

# PART 13 — PRODUCTION ARCHITECTURE & OPS 🔴

## 13.1 System Architecture 🔴
- [ ] Reference architecture: client → API gateway → orchestrator → {retrieval, tools, model} → guardrails → response 🔴
- [ ] Sync request/response vs async job + polling/webhook for long tasks 🔴
- [ ] Streaming architecture end to end (LLM → server → SSE/WebSocket → UI), and cancellation propagation 🔴
- [ ] Queue-based decoupling for batch/bulk AI work
- [ ] Stateless services + externalized conversation state 🔴
- [ ] Multi-region and provider region pinning
- [ ] Model gateway / LLM proxy pattern (central auth, routing, quotas, logging, failover) 🔴
- [ ] Provider abstraction depth: enough to swap, not so much you lose features 🔴
- [ ] Graceful degradation: fallback model, cached answer, "unavailable" path 🔴
- [ ] Versioning: prompt version + model version + index version recorded per response 🔴

## 13.2 LLM Observability 🔴
- [ ] Trace every request end-to-end: prompt, retrieved docs, tool calls, tokens, latency, cost, model version 🔴
- [ ] Correlation IDs across the pipeline; link to your existing APM traces 🔴
- [ ] OpenTelemetry GenAI semantic conventions 🟡
- [ ] Metrics: requests, tokens in/out, cost, latency (TTFT & total), error rate, cache hit rate, tool error rate, retrieval recall proxy 🔴
- [ ] Quality signals in prod: thumbs up/down, edit-distance from accepted answer, escalation rate, abandonment 🔴
- [ ] Sampling & storing traces without leaking PII 🔴
- [ ] Alerting: cost spike, latency regression, error surge, refusal-rate spike, injection detections 🔴
- [ ] Dashboards for product owners (usage, satisfaction, deflection) vs engineers (latency, cost, errors)
- [ ] Tools: Langfuse, LangSmith, Arize Phoenix, Datadog LLM Observability, Helicone 🟡
- [ ] Debugging a bad answer in production: the replay workflow 🔴 🔨

## 13.3 Reliability 🔴
- [ ] Provider outages & multi-provider failover 🔴
- [ ] Retry policy that respects idempotency and cost 🔴
- [ ] Timeouts per stage, with total request budget
- [ ] Partial-failure UX (show retrieved sources even if generation failed)
- [ ] Rollback of a prompt/model change (feature flag, not a redeploy) 🔴
- [ ] Canary rollout of prompt/model changes with online metrics 🔴
- [ ] Index rebuild without downtime (blue/green index + alias swap) 🔴
- [ ] Runbook: "answers suddenly got worse" 🔴
- [ ] Runbook: "cost tripled overnight" 🔴
- [ ] Postmortems for AI incidents (including "the model changed")

---
---

# PART 14 — COST & LATENCY ENGINEERING 🔴

## 14.1 Cost 🔴
- [ ] Build a cost model before building the feature: tokens/request × requests/day × price 🔴
- [ ] Input vs output token asymmetry; shorten outputs by design (schemas, max_tokens, "be concise")
- [ ] Prompt caching: order prompts so the stable prefix is cacheable; measure hit rate 🔴
- [ ] Semantic caching of Q→A with similarity threshold and invalidation 🔴
- [ ] Model tiering & cascading (cheap first, escalate on need) 🔴
- [ ] Batch API for offline workloads 🟡
- [ ] Truncate/compress retrieved context; retrieve fewer, better chunks 🔴
- [ ] Avoid re-sending long history — summarize or externalize state 🔴
- [ ] Cap agent steps and tool loops 🔴
- [ ] Embedding cost: cache by content hash, only re-embed changed content 🔴
- [ ] Per-tenant cost attribution & chargeback 🔴
- [ ] Budget alerts and hard kill-switches 🔴
- [ ] Self-host break-even analysis (GPU hours vs API spend) 🟡
- [ ] Cost per resolved task, not cost per call — the metric leadership cares about 🔴

## 14.2 Latency 🔴
- [ ] Latency budget across stages: retrieval, rerank, generation, guardrails 🔴
- [ ] Stream to improve *perceived* latency (TTFT is the UX metric) 🔴
- [ ] Parallelize retrieval, tool calls, and guardrail checks 🔴
- [ ] Smaller/faster model for the interactive step; big model async
- [ ] Shorter outputs = lower latency (output tokens dominate) 🔴
- [ ] Skip reranking when the top-1 score is decisive
- [ ] Prefetch/predictive retrieval where the next query is guessable
- [ ] Speculative UI (optimistic rendering, skeletons, progressive disclosure)
- [ ] Reasoning models: budget control, or route only hard cases to them 🔴
- [ ] Cold-start & connection-pool warmth
- [ ] Measuring p50/p95/p99 per stage, not just overall 🔴

---
---

# PART 15 — INFRASTRUCTURE & SELF-HOSTING 🟡

- [ ] When self-hosting is justified: data residency, volume economics, latency control, customization, air-gapped 🔴
- [ ] When it isn't: small volume, frontier-quality needs, thin ops team 🔴
- [ ] Inference servers: vLLM, TGI, TensorRT-LLM, llama.cpp/Ollama (local dev) 🟡
- [ ] Serving concepts: continuous batching, PagedAttention/KV-cache management, tensor parallelism 🟡
- [ ] GPU sizing: model params × precision ≈ VRAM, plus KV cache per concurrent request 🔴
- [ ] GPU types & availability; spot/preemptible risk 🟡
- [ ] Quantization trade-offs for serving (int8/int4, GGUF/AWQ) 🟡
- [ ] Autoscaling GPU workloads & cold starts; scale-to-zero economics 🟡
- [ ] Kubernetes for GPU workloads: device plugin, node pools, scheduling 🟡
- [ ] Model registry & artifact management; model versioning in deploys 🟡
- [ ] Throughput benchmarking & capacity planning for self-hosted inference 🟡
- [ ] Total cost of ownership vs API pricing — do the math honestly 🔴
- [ ] Hybrid: self-host the cheap/high-volume path, API for the hard path 🔴
- [ ] Local dev: Ollama/LM Studio for offline iteration, Testcontainers for vector stores 🔴

---
---

# PART 16 — MULTIMODAL & ADJACENT CAPABILITIES 🟡

- [ ] Vision input: images in prompts, resolution/token cost, OCR-by-LLM vs dedicated OCR 🔴
- [ ] Document understanding: invoices, forms, IDs, tables — accuracy expectations & human review 🔴
- [ ] Image generation: use cases, licensing, provenance/watermarking 🟢
- [ ] Speech-to-text (ASR): streaming vs batch, diarization, latency 🟡
- [ ] Text-to-speech: voice cloning ethics & consent 🟡
- [ ] Realtime voice agents: turn-taking, interruption, latency budget 🟡
- [ ] Video understanding 🟢
- [ ] Multimodal embeddings & cross-modal search 🟡
- [ ] Code-specific capabilities: generation, review, migration, test generation 🔴
- [ ] AI coding assistants in your team's workflow: policy, review discipline, license/IP risk 🔴
- [ ] Computer use / browser agents: capability, failure rate, sandboxing 🟡
- [ ] Structured document generation (reports, slides) pipelines 🟢

---
---

# PART 17 — GOVERNANCE, LEGAL & COMPLIANCE 🟡

- [ ] Vendor terms: data usage for training, retention, sub-processors, SLA, indemnity 🔴
- [ ] DPA and GDPR roles (controller/processor) for AI vendors 🔴
- [ ] Data residency & cross-border transfer for model calls 🔴
- [ ] EU AI Act: risk tiers, obligations, timelines, transparency duties 🟡
- [ ] Sector rules: finance (advice, records), healthcare (PHI), legal, HR (hiring discrimination) 🔴
- [ ] Copyright & IP: training data disputes, ownership of AI output, code license contamination 🔴
- [ ] Open-weight model licenses (not all "open" models are permissive) 🔴
- [ ] Transparency & disclosure to end users 🔴
- [ ] Human oversight requirements for consequential decisions 🔴
- [ ] Bias & fairness: evaluation, documentation, mitigation 🔴
- [ ] Model cards / system cards; internal AI inventory & registry 🟡
- [ ] AI usage policy for engineers (what may be pasted into which tool) 🔴
- [ ] Audit trail & explainability expectations 🔴
- [ ] Procurement & security review process for AI vendors and MCP servers 🔴
- [ ] Accessibility and multilingual obligations 🟢

---
---

# PART 18 — LEADERSHIP & ADOPTION 🔴

## 18.1 Deciding What to Build 🔴
- [ ] Use-case selection: high volume × tolerant of imperfection × clear success metric 🔴
- [ ] The "would a human intern do this well?" heuristic
- [ ] Value framing: cost saved, revenue enabled, time reclaimed — with a baseline measurement 🔴
- [ ] Prototype in days, decide in weeks; kill fast if evals don't move 🔴
- [ ] Buy vs build: SaaS AI feature vs your own pipeline; where differentiation actually lives 🔴
- [ ] Avoiding "AI for AI's sake" and executive-driven feature theater — how to say no productively 🔴
- [ ] Risk classification of a use case (internal tool vs customer-facing vs regulated decision) 🔴

## 18.2 Delivering It 🔴
- [ ] Team shape: backend + domain expert + (optional) ML specialist; the domain expert is non-optional 🔴
- [ ] Getting SMEs to build & own the eval set 🔴
- [ ] Definition of done for an AI feature: evals, guardrails, observability, cost cap, rollback, human fallback 🔴
- [ ] Pilot → limited rollout → GA, with human review shrinking as evals prove out 🔴
- [ ] Setting expectations: this system will be wrong sometimes; design the UX for that 🔴
- [ ] UX patterns for uncertainty: citations, confidence, edit-before-send, easy correction, feedback capture 🔴
- [ ] Change management with the affected users (support agents, analysts) 🔴
- [ ] Measuring adoption and actual value post-launch 🔴
- [ ] Sunsetting: when to turn an AI feature off

## 18.3 Team Enablement 🟡
- [ ] AI tooling policy for developers (allowed tools, data rules, review requirements) 🔴
- [ ] Coding-assistant discipline: review generated code as if from a junior; never merge unread 🔴
- [ ] Measuring assistant impact honestly (DORA, not lines of code) 🟡
- [ ] Internal knowledge sharing: brown bags, prompt/eval libraries, shared MCP servers 🟡
- [ ] Keeping up: the field changes quarterly — a sustainable reading routine, not FOMO 🔴
- [ ] Hiring for AI-adjacent roles: what to actually screen for 🟡

## 18.4 Interview-Ready Positions 🔴
Be able to answer each in 2–3 minutes with a concrete example:
- [ ] "When would you use RAG vs fine-tuning vs long context?"
- [ ] "How do you prevent prompt injection in a tool-using agent?"
- [ ] "How do you know your RAG system is actually good?"
- [ ] "Your RAG answers got worse after a data migration — diagnose it."
- [ ] "How do you control cost for an LLM feature at 1M requests/day?"
- [ ] "Design a customer-support assistant over our internal docs." 🔴
- [ ] "Design an agent that can act on our internal APIs safely." 🔴
- [ ] "What is MCP and when would you build a server vs a plain REST API?" 🔴
- [ ] "How would you evaluate two models for our use case?"
- [ ] "Where would you refuse to use an LLM in our product, and why?" 🔴
- [ ] "How do you handle multi-tenant data isolation in a vector store?"
- [ ] "How do you roll out a prompt change safely?"

---
---

# PART 19 — HANDS-ON PROJECT LADDER 🔴 🔨

> Reading this file teaches nothing. Build these in order; each adds one hard capability.

- [ ] **P1 — Chat baseline (½ day):** Spring Boot + Spring AI, streaming SSE endpoint, system prompt in version control, token & cost logging.
- [ ] **P2 — Structured extraction (½ day):** document → typed Java record via structured output, with schema validation and a repair-retry loop.
- [ ] **P3 — Naive RAG (1 day):** Postgres + pgvector, PDF ingestion, fixed chunking, top-k retrieval, grounded prompt with citations.
- [ ] **P4 — Eval harness (1 day):** 40-case golden set, retrieval recall@k + faithfulness scoring, CI job that fails on regression. **Do this before optimizing P3.** 🔴
- [ ] **P5 — RAG v2 (2 days):** hybrid search (BM25 + vector + RRF), reranker, parent-document retrieval, query rewriting. Prove each change against P4's evals. 🔴
- [ ] **P6 — Multi-tenancy & ACLs (1 day):** per-tenant isolation, ACL-filtered retrieval, prove a cross-tenant leak test fails to leak. 🔴
- [ ] **P7 — Tool calling (1 day):** 3 tools over a real internal API, error handling, timeouts, idempotency, confirmation gate on the destructive one.
- [ ] **P8 — Agent loop (2 days):** ReAct loop with step/cost caps, durable state, full trace logging, replay of a failed run. 🔴
- [ ] **P9 — MCP server (1 day):** expose your P7 tools as an MCP server (stdio + streamable HTTP), test with MCP Inspector, then connect a host to it. 🔴 🔨
- [ ] **P10 — MCP hardening (1 day):** OAuth on the HTTP transport, audience-bound tokens, per-user authorization, audit log, threat model written down. 🔴
- [ ] **P11 — Red team (1 day):** 30 adversarial prompts (injection via ingested doc, exfiltration, jailbreak, PII), automated in CI, resistance rate tracked. 🔴
- [ ] **P12 — Production hardening (2 days):** semantic + prompt caching, model fallback with circuit breaker, per-tenant quotas, Micrometer/OTel dashboards, cost alerts, canary flag for prompt changes. 🔴
- [ ] **P13 — Cost/latency optimization (1 day):** measure, then cut cost ≥50% and TTFT ≥30% without eval regression. Document exactly what worked. 🔴
- [ ] **P14 — Write it up:** a design doc + a talk. Teaching it is the final test. 🔴

---
---

# APPENDIX A — REFERENCE ARCHITECTURE (RAG + AGENT, JAVA)

```
                    ┌─────────────────────────────────────────┐
   User ──HTTPS──▶  │  API Gateway (authn, rate limit, quota) │
                    └──────────────────┬──────────────────────┘
                                       ▼
                    ┌─────────────────────────────────────────┐
                    │  Orchestration Service (Spring Boot)     │
                    │  ├─ input guardrails (PII, injection)    │
                    │  ├─ query rewrite / route                │
                    │  ├─ retrieval (parallel)                 │
                    │  │    ├─ vector: pgvector                │
                    │  │    ├─ keyword: BM25/Elastic           │
                    │  │    └─ structured: SQL / internal API  │
                    │  ├─ rerank (cross-encoder)               │
                    │  ├─ context assembly (budget + ACL)      │
                    │  ├─ LLM call (streaming, tools/MCP)      │
                    │  ├─ output guardrails (schema, ground,   │
                    │  │   PII, policy)                        │
                    │  └─ trace: prompt/docs/tools/tokens/cost │
                    └───────┬───────────────────────┬──────────┘
                            ▼                       ▼
                   ┌────────────────┐      ┌──────────────────┐
                   │ Model Gateway  │      │ Semantic Cache   │
                   │ routing,       │      │ (Redis)          │
                   │ failover,      │      └──────────────────┘
                   │ key mgmt,      │
                   │ cost accounting│
                   └───────┬────────┘
                           ▼
              Primary model  ──fallback──▶  Secondary model

   Ingestion (async):
   Sources ─▶ Parse ─▶ Clean ─▶ Chunk ─▶ Enrich(ACL,meta) ─▶ Embed ─▶ Upsert
                                                    │
                                         (content-hash idempotency,
                                          blue/green index + alias swap)
```

# APPENDIX B — DECISION TREES

**Do I need AI at all?**
```
Deterministic rules exist?          → code it
Exact answer required, no review?   → don't use an LLM
Search would satisfy the user?      → search
Fuzzy language in, structure out?   → LLM
```

**RAG vs fine-tune vs long context**
```
Need current/private facts?          → RAG
Need a specific style/format/tone?   → fine-tune (or better prompt first)
Corpus fits in context & cost is ok? → long context (measure vs RAG)
Need an exact record?                → call the API/DB, not RAG
```

**Vector store choice**
```
Already on Postgres, <10M chunks?    → pgvector (+ pgvectorscale)
Already on Elastic, need hybrid?     → Elasticsearch kNN
>100M vectors, dedicated team?       → Qdrant / Milvus / Vespa
Want zero ops, cost tolerable?       → managed (Pinecone et al.)
```

**Workflow vs agent**
```
Fixed steps?                → chain
Few known branches?         → router
Unknown steps, needs tools?  → agent (with hard step/cost caps)
```

# APPENDIX C — GLOSSARY (be precise in interviews)

| Term | One-line meaning |
|---|---|
| Token | Sub-word unit; the billing and context unit |
| Context window | Total tokens the model can attend to in one call |
| KV cache | Cached attention state that makes generation incremental |
| Temperature | Randomness of sampling |
| Grounding | Constraining answers to provided source material |
| Hallucination | Confident, unsupported output |
| RAG | Retrieve relevant context at query time, then generate |
| Chunk | A retrievable unit of a document |
| Embedding | Vector representation capturing semantics |
| ANN / HNSW | Approximate nearest-neighbor search / graph index for it |
| Reranker | Cross-encoder that re-scores candidates for precision |
| RRF | Reciprocal rank fusion — merges rankings from multiple retrievers |
| Tool calling | Model requests a function; your code executes it |
| MCP | Open protocol standardizing model-app ↔ tool/context servers |
| Agent | LLM that chooses its own sequence of actions |
| ReAct | Reason → act → observe loop |
| Eval | Repeatable measurement of output quality on a fixed set |
| LLM-as-judge | Using a model to score outputs against a rubric |
| Prompt injection | Untrusted content hijacking the model's instructions |
| Guardrail | Deterministic check on input or output |
| LoRA | Low-rank adapter fine-tuning |
| Quantization | Lower-precision weights for cheaper serving |
| TTFT | Time to first token |
| Prompt caching | Provider-side reuse of a repeated prompt prefix |
| Semantic cache | Reuse of an answer for a semantically similar query |

# APPENDIX D — RESOURCES

### Primary sources (prefer these)
- [ ] Anthropic docs: prompt engineering, tool use, agents, Claude API 🔴
- [ ] Anthropic engineering blog: *Building effective agents*, contextual retrieval, MCP posts 🔴
- [ ] **modelcontextprotocol.io** — spec, architecture, SDKs, security best practices 🔴
- [ ] OpenAI / Google / AWS Bedrock docs for provider specifics
- [ ] Spring AI reference documentation 🔴
- [ ] LangChain4j documentation 🟡
- [ ] OWASP Top 10 for LLM Applications + OWASP Agentic Security guidance 🔴
- [ ] NIST AI Risk Management Framework 🟡
- [ ] EU AI Act official text/summaries 🟡

### Practical
- [ ] Ragas / promptfoo / DeepEval docs (eval tooling)
- [ ] pgvector + pgvectorscale docs
- [ ] vLLM docs (self-hosting)
- [ ] Simon Willison's blog (prompt injection, practical LLM engineering) 🔴
- [ ] Chip Huyen — *AI Engineering* 🔴
- [ ] Hamel Husain / Eugene Yan writing on evals 🔴
- [ ] Papers worth reading: RAG (Lewis 2020), ReAct, HyDE, Self-RAG, RAPTOR, GraphRAG, Lost in the Middle 🟡

### Routine
- [ ] One hands-on build per month (Part 19 ladder)
- [ ] Re-run your evals when a model version changes 🔴
- [ ] Quarterly: re-check model landscape & pricing; the right answer moves 🔴

---

# APPENDIX E — SELF-ASSESSMENT GATES

Mark a Part done only when you can answer without notes:

- **P1:** Why does the same prompt give different answers, and what actually reduces hallucination?
- **P2:** Pick a model for a 10M-request/month extraction pipeline and defend it on cost, latency and accuracy.
- **P3:** Show me a prompt you'd cache, and explain where you'd put the volatile parts.
- **P4:** Design a tool schema for "issue a refund" and list every safeguard around it.
- **P5:** Your recall is bad at k=5. Name six possible causes, in order.
- **P6:** Walk the eight RAG failure modes and how you'd instrument to tell them apart.
- **P7:** When is an agent the wrong answer, and what do you build instead?
- **P8:** Explain MCP's three server primitives, the three client primitives, and why token passthrough is forbidden.
- **P9:** Justify a fine-tune to a CFO, including the ongoing cost you'd be signing up for.
- **P10:** Build me an eval set for a support bot — what's in it and who writes it?
- **P11:** An attacker hides instructions in a PDF you ingest. Trace the attack and every place you'd stop it.
- **P12:** Sketch the Java service layout and where prompts, schemas and guardrails live.
- **P13:** Cost tripled overnight. Your first five checks?
- **P14:** Cut p99 latency 40% on a RAG endpoint — what do you try, in order?
- **P15:** When does self-hosting beat an API, with numbers?
- **P16:** Where would you use vision, and what's the human-review policy?
- **P17:** Which of our AI use cases are high-risk, and what does that obligate us to do?
- **P18:** Talk an exec out of a bad AI feature without saying "no".

---

*Living document. The models change quarterly; the engineering — retrieval quality, evals, guardrails, cost control — does not.*

