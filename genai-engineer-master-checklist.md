# Senior Generative AI Engineer (10 YOE) — Master Knowledge & Interview Checklist

> A complete macro → micro topic map of what a senior Generative AI / LLM engineer is expected to know:
> ML & transformer foundations, LLM APIs, prompt & context engineering, embeddings & vector search, **RAG**, **agents**,
> **MCP (Model Context Protocol)**, fine-tuning, inference & serving, evaluation, guardrails & security, LLMOps,
> GenAI system design, and leadership.
>
> **Reality check:** GenAI as a discipline is only a few years old, so "10 years of experience" in this role usually means
> ~10 years in software/ML/data engineering plus 2–4 years shipping LLM systems. Interviewers therefore test **both**
> strong engineering fundamentals **and** current GenAI depth. This checklist covers both.
>
> Tick `[ ]` → `[x]` as you go. Rate yourself 1–5 per macro topic and revisit weekly. The field moves monthly —
> verify version-specific details (model names, spec versions, framework APIs) against official docs before interviews.

## Legend

| Tag | Meaning |
|-----|---------|
| **P0** | Must know deeply — asked in almost every senior interview. Be able to explain, whiteboard, and code it. |
| **P1** | Should know well — commonly asked, expected at senior level. |
| **P2** | Awareness — know what it is, when to use it, and the trade-offs. |
| 🎯 | Frequently asked interview questions for that area |

---

## Table of Contents

**Part A — Foundations**
1. [Math & Classical ML Foundations](#1-math--classical-ml-foundations-p1)
2. [Deep Learning Fundamentals & PyTorch](#2-deep-learning-fundamentals--pytorch-p1)
3. [NLP Foundations & Tokenization](#3-nlp-foundations--tokenization-p0)
4. [Transformer Architecture (Deep)](#4-transformer-architecture-deep-p0)
5. [How LLMs Are Trained (Pre-training → Post-training → Reasoning)](#5-how-llms-are-trained-p0)
6. [Model Landscape & Model Selection](#6-model-landscape--model-selection-p0)

**Part B — Building with LLMs**
7. [LLM APIs, Parameters & Structured Outputs](#7-llm-apis-parameters--structured-outputs-p0)
8. [Prompt Engineering & Context Engineering](#8-prompt-engineering--context-engineering-p0)
9. [Embeddings & Vector Search](#9-embeddings--vector-search-p0)
10. [Retrieval-Augmented Generation (RAG) — Deep](#10-retrieval-augmented-generation-rag--deep-p0)
11. [Agents & Agentic Systems](#11-agents--agentic-systems-p0)
12. [Model Context Protocol (MCP) — Deep](#12-model-context-protocol-mcp--deep-p0)
13. [Agent & LLM Frameworks](#13-agent--llm-frameworks-p1)
14. [Multimodal, Voice & Specialized Applications](#14-multimodal-voice--specialized-applications-p1)

**Part C — Adapting, Serving & Operating Models**
15. [Fine-Tuning & Model Adaptation](#15-fine-tuning--model-adaptation-p0)
16. [Inference, Serving & Optimization](#16-inference-serving--optimization-p0)
17. [Evaluation (Evals)](#17-evaluation-evals-p0)
18. [Guardrails, Safety & LLM Security](#18-guardrails-safety--llm-security-p0)
19. [LLMOps & Production Engineering](#19-llmops--production-engineering-p0)
20. [Responsible AI, Governance & Compliance](#20-responsible-ai-governance--compliance-p1)

**Part D — Engineering Foundations for AI Engineers**
21. [Python & Backend Engineering for AI](#21-python--backend-engineering-for-ai-p0)
22. [Data Engineering for AI](#22-data-engineering-for-ai-p1)
23. [MLOps & Infrastructure (GPUs, Kubernetes, Cloud)](#23-mlops--infrastructure-p1)
24. [Classic Distributed Systems & System Design Essentials](#24-classic-distributed-systems--system-design-essentials-p1)

**Part E — GenAI System Design**
25. [GenAI System Design Framework & Estimation](#25-genai-system-design-framework--estimation-p0)
26. [Classic GenAI System Design Problems](#26-classic-genai-system-design-problems-p0)
27. [Product Thinking & AI UX](#27-product-thinking--ai-ux-p1)

**Part F — Coding Interviews**
28. [ML/LLM Coding From Scratch](#28-mlllm-coding-from-scratch-p0)
29. [Applied GenAI Coding & Take-Homes](#29-applied-genai-coding--take-homes-p0)
30. [DSA in Python](#30-dsa-in-python-p1)

**Part G — Leadership, Behavioral & Career**
31. [Technical Leadership in AI Teams](#31-technical-leadership-in-ai-teams-p0)
32. [Behavioral Interviews & Story Bank](#32-behavioral-interviews--story-bank-p0)
33. [Portfolio, Project Deep-Dive, Resume & Negotiation](#33-portfolio-project-deep-dive-resume--negotiation-p0)
34. [Interview Formats](#34-interview-formats)

**Part H — Execution**
35. [Rapid-Fire Questions (Top 100)](#35-rapid-fire-questions-top-100)
36. [12-Week Preparation Plan](#36-12-week-preparation-plan)
37. [Resources (Books, Papers, Courses)](#37-resources)
38. [Final Readiness Checklist](#38-final-readiness-checklist)

---

# PART A — FOUNDATIONS

## 1. Math & Classical ML Foundations (P1)

### 1.1 Linear Algebra
- [ ] Vectors, matrices, tensors; dot product & **cosine similarity** (the core of embeddings/attention); norms (L1, L2); matrix multiplication shapes; transpose
- [ ] Eigenvalues/eigenvectors, **SVD**, low-rank approximation (the intuition behind LoRA), PCA
- [ ] Orthogonality, projections, high-dimensional geometry intuitions (curse of dimensionality, why ANN search is needed)

### 1.2 Probability & Statistics
- [ ] Random variables, distributions (Bernoulli, categorical, Gaussian), expectation, variance
- [ ] Conditional probability, **Bayes' rule**, independence
- [ ] **Maximum likelihood estimation**; language modeling as maximizing log-likelihood of next tokens
- [ ] **Entropy, cross-entropy, KL divergence** (loss functions, distillation, RLHF KL penalty), **perplexity**
- [ ] Sampling from distributions (temperature, top-k, top-p as distribution reshaping)
- [ ] Statistical testing — confidence intervals, significance, sample sizes for evals & A/B tests, bootstrap

### 1.3 Calculus & Optimization
- [ ] Derivatives, partial derivatives, gradients, **chain rule → backpropagation**
- [ ] Gradient descent, SGD, momentum, **Adam/AdamW** (weight decay), learning-rate schedules (warmup, cosine decay), gradient clipping
- [ ] Loss landscapes, local minima, saddle points; vanishing/exploding gradients

### 1.4 Classical ML
- [ ] Supervised vs unsupervised vs self-supervised vs reinforcement learning
- [ ] **Bias–variance trade-off**, overfitting/underfitting, regularization (L1/L2, dropout, early stopping)
- [ ] Train/validation/test splits, cross-validation, **data leakage**
- [ ] Linear & logistic regression, decision trees, random forests, gradient boosting (XGBoost/LightGBM), k-NN, k-means, naive Bayes, SVMs (awareness)
- [ ] **Metrics** — accuracy, precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix, calibration; regression metrics (MAE, RMSE); ranking metrics (MRR, nDCG, MAP, recall@k)
- [ ] Class imbalance handling; feature engineering; when classical ML beats an LLM (cost, latency, explainability)

---

## 2. Deep Learning Fundamentals & PyTorch (P1)

- [ ] **Neural networks** — neurons, layers, forward pass, **backpropagation**, computational graphs
- [ ] **Activation functions** — sigmoid, tanh, ReLU, GELU, **SwiGLU** (modern LLM FFNs), softmax
- [ ] **Loss functions** — cross-entropy (next-token prediction), MSE, contrastive losses (InfoNCE — used for embedding models)
- [ ] **Initialization**, **normalization** (BatchNorm, **LayerNorm**, **RMSNorm**), **residual connections**, dropout
- [ ] **Architectures history** — MLPs, CNNs, RNNs/LSTMs/GRUs (and why transformers replaced them), seq2seq with attention, autoencoders, VAEs, GANs, diffusion models (basics)
- [ ] **Training mechanics** — batches, epochs, gradient accumulation, mixed precision (FP16/BF16), gradient checkpointing, learning-rate finders
- [ ] **PyTorch** — tensors & broadcasting, autograd, `nn.Module`, optimizers, `Dataset`/`DataLoader`, training loop, `torch.no_grad`/`inference_mode`, device management (CUDA/MPS), saving/loading (`state_dict`, safetensors), `torch.compile`, distributed basics (DDP, FSDP)
- [ ] **JAX/Flax** — awareness
- [ ] **Hugging Face Transformers** — `AutoModel`/`AutoTokenizer`, pipelines, `generate()` parameters, model hub, `datasets`, `accelerate`

---

## 3. NLP Foundations & Tokenization (P0)

### 3.1 NLP Evolution
- [ ] Bag-of-words, TF-IDF, n-grams, **BM25** (still a key retrieval baseline)
- [ ] Word embeddings — word2vec (skip-gram, CBOW), GloVe, fastText; static vs contextual embeddings
- [ ] RNN language models → seq2seq → attention (Bahdanau) → **Transformer** (2017) → BERT/GPT era → instruction-tuned chat models → reasoning models
- [ ] Classic NLP tasks — classification, NER, summarization, translation, QA, sentiment; how LLMs subsumed many of them

### 3.2 Tokenization (P0)
- [ ] **Why subword tokenization** — open vocabulary, OOV handling, compression
- [ ] **BPE** (byte-pair encoding) — merge algorithm; **byte-level BPE** (GPT family, tiktoken), **WordPiece** (BERT), **Unigram/SentencePiece** (T5, Llama earlier)
- [ ] **Vocabulary size trade-offs** — sequence length vs embedding matrix size
- [ ] **Practical consequences** — token counting for cost & context limits, tokenization artifacts (arithmetic, spelling, counting letters), whitespace & casing effects, **multilingual token inflation** (non-English costs more), code tokenization
- [ ] **Special tokens & chat templates** — BOS/EOS, role tokens, system/user/assistant formatting; getting templates wrong silently degrades fine-tuned models
- [ ] Tools — tiktoken, Hugging Face tokenizers, provider token-counting endpoints

### 🎯 Frequently Asked
- How does BPE work? Why do LLMs struggle to count letters in a word?
- Why does the same text cost more tokens in Hindi/Japanese than English?
- What is a chat template and why does it matter for fine-tuned models?

---

## 4. Transformer Architecture (Deep) (P0)

### 4.1 Core Mechanism
- [ ] **Embeddings** — token embeddings + positional information; the residual stream view
- [ ] **Self-attention** — queries, keys, values; **scaled dot-product attention** `softmax(QKᵀ / √d_k) V`; why scale by √d_k
- [ ] **Multi-head attention** — heads attend to different subspaces; output projection
- [ ] **Causal (masked) attention** for decoder-only models; padding masks
- [ ] **Feed-forward network (MLP)** per position (often 4× hidden; SwiGLU variants); where much "knowledge" is stored
- [ ] **Layer normalization placement** — pre-LN vs post-LN; RMSNorm
- [ ] **Residual connections** & deep stacking
- [ ] **Output head** — final norm → unembedding → logits → softmax over vocabulary; weight tying
- [ ] **Autoregressive generation** — one token at a time; why generation is sequential and decode is memory-bandwidth bound

### 4.2 Architecture Variants
- [ ] **Encoder-only** (BERT — bidirectional, masked LM; embeddings, classification, rerankers)
- [ ] **Decoder-only** (GPT, Llama, Claude-style — causal LM; dominant for generation)
- [ ] **Encoder-decoder** (T5, BART — seq2seq; translation/summarization)
- [ ] **Positional encodings** — sinusoidal, learned absolute, **RoPE** (rotary; context extension via scaling such as NTK/YaRN), **ALiBi**
- [ ] **Attention variants** — Multi-Query Attention (MQA), **Grouped-Query Attention (GQA)** (smaller KV cache), **Multi-head Latent Attention (MLA)** (DeepSeek), sliding-window/local attention, sparse attention, linear attention (awareness)
- [ ] **Mixture of Experts (MoE)** — router/gating, top-k experts per token, total vs active parameters, load-balancing losses, expert parallelism; why MoE gives quality at lower inference FLOPs but needs more memory
- [ ] **Long-context techniques** — RoPE scaling, efficient attention, ring attention (awareness), memory/retrieval hybrids; effective vs advertised context length
- [ ] **State Space Models / hybrids** — Mamba, hybrid attention-SSM models (awareness)
- [ ] **Multimodal architectures** — vision encoders (ViT, CLIP/SigLIP) + projector + LLM; audio encoders; native multimodal models; image generation (diffusion, autoregressive image models)

### 4.3 Efficiency Concepts
- [ ] **KV cache** — what is cached, why it speeds decoding, memory formula ≈ 2 × layers × KV heads × head_dim × seq_len × batch × bytes per element
- [ ] **FlashAttention** — IO-aware exact attention (tiling, avoiding materializing the N×N matrix in HBM)
- [ ] **Compute cost** — training FLOPs ≈ 6 × parameters × tokens; inference ≈ 2 × parameters per token; attention is O(n²) in sequence length
- [ ] **Scaling laws** — Kaplan et al., **Chinchilla** (compute-optimal ≈ 20 tokens/parameter), modern over-training of smaller models for cheaper inference; emergent abilities debate

### 🎯 Frequently Asked
- Walk me through a forward pass of a decoder-only transformer
- Why divide by √d_k in attention?
- What is the KV cache and how much memory does it need for a 70B model at 32k context?
- MHA vs MQA vs GQA — trade-offs
- How does RoPE work and how is context length extended?
- What is MoE and why is it popular?
- Encoder vs decoder models — which would you use for embeddings, classification, generation?

---

## 5. How LLMs Are Trained (P0)

### 5.1 Pre-training
- [ ] **Objective** — next-token prediction (causal LM) on trillions of tokens; self-supervised
- [ ] **Data pipeline** — web crawls (Common Crawl), code, books, papers; **deduplication** (exact & near-dup/MinHash), quality filtering (classifiers, heuristics), toxicity/PII filtering, data mixing/curriculum, contamination concerns
- [ ] **Distributed training** — data parallelism (DDP), **FSDP/ZeRO** (sharding optimizer states/gradients/params), **tensor parallelism**, **pipeline parallelism**, sequence/context parallelism, expert parallelism; frameworks (Megatron-LM, DeepSpeed, torchtitan); mixed precision (BF16, FP8); checkpointing; loss spikes & instabilities
- [ ] **Mid-training / continued pre-training** — domain adaptation, long-context extension, annealing on high-quality data

### 5.2 Post-training (P0)
- [ ] **Supervised Fine-Tuning (SFT) / instruction tuning** — curated prompt–response pairs, chat formatting
- [ ] **RLHF** — preference data collection, **reward model**, **PPO** with KL penalty to the reference model; reward hacking
- [ ] **Direct preference methods** — **DPO**, IPO, KTO, ORPO, SimPO — preference optimization without an explicit RL loop
- [ ] **RLAIF & Constitutional AI** — AI feedback guided by principles (Anthropic)
- [ ] **Reasoning models** — chain-of-thought, **RL with verifiable rewards** (math/code unit tests), **GRPO** (DeepSeek-R1), test-time compute scaling, thinking/reasoning tokens & budgets, process vs outcome reward models
- [ ] **Tool-use & agentic training** — training models to call tools, browse, write code; long-horizon RL environments
- [ ] **Distillation** — training smaller models on outputs/logits of larger ones
- [ ] **Synthetic data** — generation, filtering, model collapse risks
- [ ] **Safety training** — refusals, harmlessness vs helpfulness trade-offs, red-teaming, system-card disclosures
- [ ] **Model merging** (task arithmetic, TIES, SLERP) — awareness

### 5.3 Model Behaviors to Understand
- [ ] **Hallucination** — causes (training objective, knowledge gaps, exposure bias, sycophancy), mitigation (grounding, retrieval, abstention, verification)
- [ ] **Knowledge cutoff**, in-context learning, instruction following, sycophancy, position bias ("lost in the middle"), context rot over long inputs, prompt sensitivity, non-determinism
- [ ] **Emergent & reasoning capabilities** — what reasoning models are good/bad at; cost/latency of thinking

### 🎯 Frequently Asked
- Explain the stages from a base model to a chat assistant
- RLHF vs DPO — how do they differ?
- How do reasoning models work (GRPO, verifiable rewards, test-time compute)?
- Why do LLMs hallucinate and how do you mitigate it in production?

---

## 6. Model Landscape & Model Selection (P0)

- [ ] **Frontier closed models** — Anthropic Claude family (Opus/Sonnet/Haiku tiers), OpenAI GPT & o-series reasoning models, Google Gemini (Pro/Flash), xAI Grok — know current tiers, context windows, tool-use, multimodality, pricing shape (verify current versions before interviews)
- [ ] **Open-weight models** — Meta Llama, Mistral/Mixtral, Alibaba Qwen, DeepSeek (V3/R1 lineage), Google Gemma, Microsoft Phi, OpenAI gpt-oss, others; licenses (Apache 2.0 vs custom community licenses), sizes & quantized variants
- [ ] **Specialized models** — embedding models, rerankers, code models, vision-language models, speech (Whisper, TTS), image/video generation, small language models for edge
- [ ] **Selection criteria** — task quality on **your** evals, latency (TTFT, tokens/s), cost (input/output/cached tokens), context window, tool-use reliability, structured output support, multimodality, multilingual quality, rate limits, data privacy/residency (zero data retention, regional endpoints), deployment options (API, cloud marketplaces like Bedrock/Vertex/Azure, self-host), licensing, vendor risk
- [ ] **Model routing & cascades** — small/cheap model first, escalate to larger; task-specific routing
- [ ] **Benchmarks & their limits** — MMLU/MMLU-Pro, GPQA, HumanEval/LiveCodeBench, **SWE-bench Verified**, AIME/MATH, ARC-AGI, Humanity's Last Exam, τ-bench, LMArena (human preference); contamination, saturation, benchmark ≠ your product
- [ ] **Pricing math** — cost per request = input tokens × in-price + output tokens × out-price (+ thinking tokens); prompt caching discounts; batch API discounts (~50%); total cost of ownership for self-hosting (GPUs, ops, utilization)
- [ ] **Model lifecycle risk** — deprecations, behavior changes across versions, pinning model versions, regression testing on upgrades

---

# PART B — BUILDING WITH LLMs

## 7. LLM APIs, Parameters & Structured Outputs (P0)

### 7.1 API Fundamentals
- [ ] **Message format** — system prompt, user/assistant turns, multi-turn state (stateless APIs: you resend history), content blocks (text, images, documents, tool use/results)
- [ ] **Provider SDKs** — Anthropic, OpenAI (Chat Completions vs Responses API), Google GenAI; sync/async clients, streaming helpers, retries & timeouts configuration
- [ ] **OpenAI-compatible endpoints** (vLLM, Ollama, many providers), **multi-provider gateways** (LiteLLM, Portkey, OpenRouter, Cloudflare/Kong AI gateways)
- [ ] **Cloud platforms** — AWS Bedrock, Azure AI Foundry/Azure OpenAI, Google Vertex AI — enterprise auth, VPC/private access, data residency, provisioned throughput

### 7.2 Generation Parameters (P0)
- [ ] **Temperature**, **top-p (nucleus)**, **top-k**, min-p; greedy vs sampling; how each reshapes the distribution
- [ ] **max tokens** (output limits; truncated responses & `stop_reason`/`finish_reason`), **stop sequences**
- [ ] Frequency/presence penalties, **logprobs** (confidence, classification, eval), `seed` & non-determinism (batching effects on outputs)
- [ ] **Reasoning/thinking controls** — thinking budgets/effort levels, interleaved thinking with tools, cost & latency trade-offs
- [ ] **Prefilling** the assistant response (where supported) to steer format

### 7.3 Streaming (P0)
- [ ] Server-Sent Events, token/delta events, tool-call streaming, handling partial JSON, time-to-first-token UX, cancellation, proxying streams through your backend (FastAPI/Node), backpressure, reconnect semantics

### 7.4 Structured Outputs (P0)
- [ ] **JSON mode vs JSON Schema–constrained outputs** vs tool/function-call arguments as structure
- [ ] **Pydantic/Zod schemas** → JSON Schema; **Instructor**, Outlines, provider-native structured outputs, BAML
- [ ] Validation + retry loops (re-ask with error), partial streaming of structured output
- [ ] **Constrained decoding** (grammars, JSON schema enforcement) in self-hosted inference (xgrammar, Outlines, llguidance)
- [ ] Schema design tips — enums for categories, reasoning field before answer field, optional vs required, keeping schemas small

### 7.5 Tool / Function Calling (P0)
- [ ] Tool definitions (name, description, JSON Schema input), model decides to call → you execute → return tool result → model continues
- [ ] `tool_choice` (auto/any/specific/none), parallel tool calls, tool-call IDs, error results back to the model
- [ ] **Server-side/built-in tools** (web search, code execution, file search, computer use) vs client tools
- [ ] Tool description quality as prompt engineering; number of tools & tool selection accuracy; tool search/lazy loading for large toolsets

### 7.6 Cost, Limits & Reliability
- [ ] **Rate limits** — RPM, input/output TPM, concurrent requests; 429 handling with exponential backoff + jitter; client-side token-bucket throttling; queueing
- [ ] **Prompt caching** — cache prefixes (system prompts, tools, long documents), cache breakpoints, TTLs, hit-rate monitoring, ordering prompts for cacheability (static first, dynamic last)
- [ ] **Batch APIs** — async, ~50% cheaper, for offline workloads (classification, evals, backfills)
- [ ] **Token counting** — pre-flight counting, budgeting context, truncation strategies
- [ ] **Context windows** — limits, long-context pricing tiers, context management (summarization, compaction, retrieval)
- [ ] **Files/documents APIs**, citations features, PDF support
- [ ] **Errors** — overloaded/5xx, timeouts, content-filter refusals, malformed outputs; fallbacks to other models/providers

### 🎯 Frequently Asked
- Temperature vs top-p — what do they do and what do you set for extraction vs creative tasks?
- How do you guarantee valid JSON output?
- How do you handle provider rate limits at 10k requests/minute?
- How does prompt caching work and how do you design prompts to maximize hits?

---

## 8. Prompt Engineering & Context Engineering (P0)

### 8.1 Prompt Engineering Principles
- [ ] **Be clear, specific and direct**; give context and the *why*; define the audience and success criteria
- [ ] **System prompts / roles** — persona, constraints, tone, output format
- [ ] **Structure** — XML tags/Markdown sections to separate instructions, context, examples, and inputs; long documents first, question last
- [ ] **Few-shot examples** — diverse, representative, including edge cases; avoiding over-anchoring; example ordering effects
- [ ] **Chain-of-thought** — "think step by step", structured reasoning sections, separating reasoning from final answer; when native reasoning models make manual CoT unnecessary
- [ ] **Output control** — explicit formats, schemas, length limits, prefilling, stop sequences
- [ ] **Prompt chaining / decomposition** — split complex tasks into steps (extract → analyze → write), each verifiable
- [ ] **Self-consistency** (sample many, vote), **self-critique/reflection**, **evaluator-optimizer loops**
- [ ] **ReAct** (reason + act with tools), plan-and-solve, tree-of-thoughts (awareness)
- [ ] **Grounding instructions** — answer only from provided context, cite sources, say "I don't know"
- [ ] **Handling ambiguity** — asking clarifying questions vs making stated assumptions
- [ ] **Model-specific prompting** — differences between providers & model generations; re-tuning prompts on model upgrades
- [ ] **Multilingual prompting**, code-generation prompting, data extraction prompting

### 8.2 Context Engineering (P0 — the 2025–26 framing)
- [ ] **Context engineering** = curating the *entire* context window (system prompt, tools, retrieved docs, memory, conversation history, tool results) for each LLM call
- [ ] **Context budget** — what earns its place; signal-to-noise; **context rot** (quality degrades with long, noisy context)
- [ ] **Techniques** — retrieval (just-in-time vs pre-loaded), summarization/compaction of history, structured note-taking/scratchpads, sub-agents with isolated contexts, tool-result trimming, progressive disclosure (load skills/docs only when needed)
- [ ] **Ordering & caching** — stable prefix for prompt caching, dynamic content last
- [ ] **Long-context vs RAG** decision — cost, latency, accuracy, "lost in the middle"

### 8.3 Prompt Management & Optimization
- [ ] **Prompts as code** — version control, templating (Jinja), environment promotion, feature flags & A/B tests for prompts, prompt registries (Langfuse, LangSmith, PromptLayer)
- [ ] **Evaluation-driven prompt iteration** (§17) — never ship prompt changes without evals
- [ ] **Automatic prompt optimization** — **DSPy** (signatures, modules, optimizers like MIPRO/GEPA), TextGrad, provider prompt improvers
- [ ] **Prompt injection-aware prompting** (§18) — delimiting untrusted content, instruction hierarchy

### 🎯 Frequently Asked
- How do you systematically improve a prompt that's 80% accurate?
- Few-shot vs fine-tuning — when each?
- What is context engineering and how is it different from prompt engineering?
- How do you manage prompts across environments and model versions?

---

## 9. Embeddings & Vector Search (P0)

### 9.1 Embeddings
- [ ] **What embeddings are** — dense vectors capturing semantics; trained with contrastive objectives (in-batch negatives, hard negatives)
- [ ] **Bi-encoders vs cross-encoders** — embeddings for retrieval (fast) vs rerankers for precision (slow, pairwise)
- [ ] **Embedding models** — OpenAI text-embedding-3, Cohere Embed, Voyage, Google Gemini embeddings, open models (BGE, E5, GTE, Nomic, Jina, Qwen3-Embedding, sentence-transformers); multilingual & code embeddings; multimodal embeddings (CLIP/SigLIP, ColPali for documents)
- [ ] **Choosing a model** — MTEB leaderboard as a start, then **evaluate on your data**; dimensions vs cost vs quality; max input length; domain fit
- [ ] **Matryoshka embeddings** (truncatable dimensions), **quantization** (int8, binary) for storage/speed
- [ ] **Normalization** & similarity metrics — cosine vs dot product vs Euclidean (equivalent for normalized vectors)
- [ ] **Asymmetric retrieval** — query vs document prefixes/instructions (e.g., "query:"/"passage:")
- [ ] **Fine-tuning embeddings** on domain pairs (sentence-transformers, synthetic query generation), hard-negative mining
- [ ] **Re-embedding cost** when changing models — versioning indexes, dual-writing during migrations

### 9.2 Vector Search Algorithms (P0)
- [ ] **Exact (brute-force) kNN** vs **Approximate Nearest Neighbor (ANN)**
- [ ] **HNSW** — layered proximity graph; params `M`, `efConstruction`, `efSearch`; memory heavy, great recall/latency; deletes & updates behavior
- [ ] **IVF** (inverted file with k-means clusters; `nlist`, `nprobe`), **PQ** (product quantization), IVF-PQ, **ScaNN**, **DiskANN** (SSD-based), LSH (awareness)
- [ ] **Recall vs latency vs memory vs cost** trade-offs; measuring recall@k against exact search
- [ ] **Filtering** — metadata filters with ANN (pre-filter vs post-filter vs filtered HNSW), selectivity issues, multi-tenancy (namespaces/partitions per tenant)
- [ ] **Sparse retrieval** — BM25, **SPLADE** (learned sparse); **hybrid search** = dense + sparse, fused with **Reciprocal Rank Fusion (RRF)** or weighted scores
- [ ] **Late interaction** — **ColBERT** (token-level multi-vector), ColPali (document images)

### 9.3 Vector Databases (P0)
- [ ] **Options** — **pgvector** (+ pgvectorscale) on Postgres, Pinecone, Weaviate, Qdrant, Milvus/Zilliz, Chroma, LanceDB, Vespa, Turbopuffer, Elasticsearch/OpenSearch kNN, Redis, MongoDB Atlas Vector Search, Databricks Vector Search, Azure AI Search, Vertex AI Vector Search, S3 Vectors
- [ ] **Selection criteria** — scale (vectors count & dimensions), latency, filtering capability, hybrid search, multi-tenancy, consistency/freshness of updates, deletes, cost model (memory vs disk vs serverless), operational burden, existing stack ("use Postgres until you can't")
- [ ] **Index lifecycle** — upserts, deletes, re-indexing, backups, versioning, sharding & replication
- [ ] **Capacity estimation** — memory ≈ vectors × dimensions × bytes (e.g., 10M × 1024 × 4 B ≈ 41 GB raw float32, plus HNSW graph overhead)

### 🎯 Frequently Asked
- How does HNSW work? What do `M` and `efSearch` control?
- Bi-encoder vs cross-encoder — where does each fit in a retrieval pipeline?
- Why use hybrid search? How does RRF work?
- pgvector vs a dedicated vector DB — how do you decide?
- How do you handle metadata filtering and multi-tenancy in vector search?

---

## 10. Retrieval-Augmented Generation (RAG) — Deep (P0)

### 10.1 When & Why
- [ ] **Why RAG** — grounding in private/fresh data, fewer hallucinations, citations, access control, cheaper than fine-tuning for knowledge
- [ ] **RAG vs fine-tuning vs long context vs tools/APIs** — knowledge (RAG) vs behavior/format/style (fine-tuning) vs small corpora (long context + caching) vs structured live data (tools/text-to-SQL)

### 10.2 Ingestion / Indexing Pipeline (P0)
- [ ] **Sources & loaders** — PDFs, Word, HTML, Confluence/SharePoint/Google Drive, tickets, code repos, databases; connectors & sync (incremental, webhooks)
- [ ] **Parsing** — layout-aware PDF parsing, tables, images/charts (OCR, VLM captioning), headers/footers removal; tools: Unstructured, LlamaParse, Docling, Azure Document Intelligence, AWS Textract, Reducto, marker, VLM-based parsing
- [ ] **Cleaning & normalization** — dedupe, boilerplate removal, language detection, PII handling
- [ ] **Chunking strategies** (P0) — fixed-size with overlap, recursive character splitting, sentence/paragraph-based, **structure-aware** (Markdown headings, HTML sections, code AST), **semantic chunking** (embedding-similarity boundaries), **parent–child / small-to-big** (retrieve small, return parent), sentence-window retrieval, **late chunking**, **contextual retrieval** (prepend LLM-generated chunk context before embedding/BM25 — Anthropic), proposition chunking; chunk size trade-offs (precision vs context)
- [ ] **Metadata enrichment** — source, title, section path, timestamps, author, ACLs/permissions, document type, language, extracted entities, summaries, hypothetical questions per chunk
- [ ] **Embedding & indexing** — batching, rate limits, retries, idempotent upserts keyed by chunk hash, model versioning
- [ ] **Freshness & lifecycle** — incremental updates, deletions/tombstones propagated to the index, re-embedding on model change, backfills, monitoring index lag

### 10.3 Retrieval (P0)
- [ ] **Query understanding** — **query rewriting** (from conversation context — "condense question"), expansion, **multi-query** generation, **HyDE** (hypothetical document embeddings), **step-back** prompting, **decomposition** for multi-part questions, query classification & **routing** (which index/tool), metadata filter extraction (self-query)
- [ ] **Retrieval methods** — dense, sparse (BM25), **hybrid** (RRF), metadata-filtered search, keyword boosts, recency boosts
- [ ] **Reranking** (P0) — cross-encoder rerankers (Cohere Rerank, Voyage, bge-reranker, Jina), LLM-as-reranker; retrieve top-50/100 then rerank to top-5/10
- [ ] **Diversity** — MMR (maximal marginal relevance), dedupe near-identical chunks
- [ ] **Top-k & thresholds** — tuning k, similarity thresholds, "no relevant context" detection

### 10.4 Generation (P0)
- [ ] **Context assembly** — ordering (most relevant at start/end — "lost in the middle"), deduplication, compression (extractive, LLMLingua-style), token budgeting, including source metadata for citations
- [ ] **Grounded prompting** — answer only from context, cite chunk IDs, abstain when unsupported, handle conflicting sources, quote extraction before answering
- [ ] **Citations** — inline references, verifying citations post-hoc, provider citation features
- [ ] **Conversational RAG** — history-aware retrieval, memory, follow-up questions
- [ ] **Streaming answers** with sources

### 10.5 Advanced RAG Patterns (P1)
- [ ] **Agentic RAG** — the model decides when/what to retrieve, iterative retrieval, multiple tools (search, SQL, APIs)
- [ ] **Corrective RAG (CRAG)**, **Self-RAG** (reflection tokens), adaptive retrieval
- [ ] **Multi-hop retrieval** & question decomposition
- [ ] **GraphRAG** — entity/relationship extraction into knowledge graphs, community summaries (Microsoft GraphRAG), LightRAG; global vs local questions; cost of graph construction
- [ ] **Structured data RAG** — **text-to-SQL** (schema linking, few-shot examples, semantic layer, query validation, read-only roles, result summarization), table QA, hybrid structured + unstructured
- [ ] **Multimodal RAG** — images, tables, charts, slides; ColPali/vision embeddings; VLM answer generation
- [ ] **Personalized & permission-aware RAG** — per-user ACL filtering at query time (never rely on the LLM to enforce access), tenant isolation, document-level security sync from source systems
- [ ] **Caching** — query/result caches, semantic caches, embedding caches

### 10.6 RAG Evaluation & Debugging (P0)
- [ ] **Retrieval metrics** — recall@k, precision@k, hit rate, MRR, nDCG; needs labeled query→relevant-chunk sets (human or synthetic)
- [ ] **Generation metrics** — **faithfulness/groundedness**, answer relevance, answer correctness, **context precision/recall**, citation accuracy, completeness
- [ ] **Tools** — RAGAS, DeepEval, TruLens, Arize Phoenix, LangSmith, Braintrust, promptfoo
- [ ] **Golden datasets** — real user questions, synthetic Q&A generation from documents, edge cases (unanswerable, ambiguous, multi-hop, recency)
- [ ] **Failure analysis** — classify failures: parsing → chunking → retrieval (missed/ranked low) → context assembly → generation (ignored context, hallucinated) → citation; fix the earliest failing stage
- [ ] **Online signals** — thumbs up/down, follow-up rephrasing, escalation to humans, click-through on citations

### 🎯 Frequently Asked
- Walk through a production RAG pipeline end to end
- How do you choose chunk size and chunking strategy?
- Retrieval is returning irrelevant chunks — how do you debug and improve it?
- How do you evaluate a RAG system? Which metrics?
- How do you enforce document permissions in RAG?
- How do you keep the index fresh when documents change or are deleted?
- When would you use GraphRAG or text-to-SQL instead of vector RAG?
- RAG vs fine-tuning vs long context for a 500-page policy manual

---

## 11. Agents & Agentic Systems (P0)

### 11.1 Concepts
- [ ] **Agent definition** — an LLM using tools in a loop, deciding its own next steps based on environment feedback, until a goal or stop condition
- [ ] **Workflows vs agents** — predefined code paths (predictable, cheaper) vs model-directed control flow (flexible, costlier, riskier); **start with the simplest thing that works**
- [ ] **Workflow patterns** (Anthropic's "Building effective agents") — **prompt chaining**, **routing**, **parallelization** (sectioning, voting), **orchestrator–workers**, **evaluator–optimizer**
- [ ] **The agent loop** — observe → think → act (tool call) → observe result → repeat; stop conditions (task done, max steps, budget, human handoff)
- [ ] **Planning** — ReAct, plan-and-execute, re-planning on failure, task decomposition, reflection/self-critique
- [ ] **Augmented LLM building blocks** — retrieval, tools, memory

### 11.2 Tool Design (P0)
- [ ] **Agent–computer interface (ACI)** — clear names, rich descriptions with when-to-use guidance, typed parameters, examples, sensible defaults; tool documentation is prompt engineering
- [ ] **Granularity** — fewer, higher-level tools that match workflows vs thin API wrappers; avoiding overlapping tools
- [ ] **Outputs** — concise, high-signal, token-efficient results; pagination/truncation; helpful error messages that guide recovery
- [ ] **Safety** — read vs write tools, idempotency for retries, dry-run modes, confirmation for destructive actions, least privilege credentials, rate limits
- [ ] **Scale** — dozens/hundreds of tools → tool search/retrieval, namespacing, dynamic tool loading

### 11.3 Memory (P1)
- [ ] **Short-term** — conversation history, scratchpads, context window management (compaction, summarization, trimming tool results)
- [ ] **Long-term** — episodic (past interactions), semantic (facts/user preferences), procedural (learned instructions/skills); storage in vector DBs, KV stores, files; memory write/read policies, decay, conflicts, privacy & user control; memory tools (Mem0, Letta/MemGPT, Zep, provider memory features)
- [ ] **State management** — checkpoints, resumable runs, durable execution (LangGraph checkpointers, Temporal, Restate, Inngest)

### 11.4 Multi-Agent Systems (P1)
- [ ] **Architectures** — supervisor/orchestrator–subagents, hierarchical teams, handoffs/swarm, peer collaboration/debate, pipelines
- [ ] **When multi-agent helps** — parallelizable research, context isolation (each subagent gets a clean window), specialization; **costs** — many more tokens, coordination failures, harder debugging
- [ ] **Inter-agent protocols** — **A2A (Agent2Agent)** protocol (agent cards, tasks, messages; Linux Foundation project) vs MCP (agent ↔ tools/context)

### 11.5 Specialized Agents (P1)
- [ ] **Coding agents** — repo context, file editing tools, running tests, sandboxes, PR workflows (Claude Code, Codex, Cursor agents, Devin-style); evaluation via SWE-bench
- [ ] **Computer-use / browser agents** — screenshots + mouse/keyboard actions, DOM-based browser automation (Playwright MCP), reliability & safety concerns
- [ ] **Research agents** — iterative search, source evaluation, synthesis with citations (deep research)
- [ ] **Customer support agents** — policies, tool access to orders/accounts, escalation to humans, compliance
- [ ] **Data/analytics agents** — text-to-SQL, notebooks, chart generation
- [ ] **Long-running/background agents** — hours-long tasks, progress reporting, compaction, checkpoints, human approvals

### 11.6 Reliability, Safety & Cost (P0)
- [ ] **Failure modes** — infinite loops, repeated tool calls, hallucinated tool names/arguments, error compounding over steps, premature completion claims, goal drift, context overflow, reward hacking in evals
- [ ] **Controls** — max iterations, token/cost budgets, timeouts, loop detection, validation of tool arguments, structured outputs, verification steps, checkpoints
- [ ] **Human-in-the-loop** — approval gates for high-impact actions, interrupts, editable plans, escalation
- [ ] **Sandboxing** — code execution in isolated containers/microVMs (E2B, Firecracker, gVisor), network egress controls, filesystem limits
- [ ] **Permissions** — least privilege per tool, scoped OAuth tokens, user-delegated vs service credentials, audit logs of every action
- [ ] **Agent evaluation** — task success rate, trajectory evaluation (right tools, right order), tool-call accuracy, steps/cost per success, human review; benchmarks (SWE-bench, τ-bench, GAIA, WebArena, OSWorld, Terminal-Bench); simulated users & environments for testing
- [ ] **Observability** — full traces of thoughts/tool calls/results, replay of runs, cost per run

### 🎯 Frequently Asked
- Workflow vs agent — when would you choose each?
- How do you design tools for an agent? What makes a good tool?
- How do you prevent an agent from looping or taking destructive actions?
- How do you evaluate an agent?
- Single agent vs multi-agent — trade-offs
- How do you manage context/memory for a long-running agent?

---

## 12. Model Context Protocol (MCP) — Deep (P0)

### 12.1 Why MCP
- [ ] **Problem** — every AI app × every tool/data source = N×M bespoke integrations; MCP standardizes how AI applications connect to tools, data, and prompts ("USB-C for AI")
- [ ] **History & governance** — introduced by Anthropic (Nov 2024), adopted across major AI clients/IDEs/providers in 2025; donated to the Linux Foundation's **Agentic AI Foundation** (Dec 2025); official MCP Registry for discovering servers
- [ ] **MCP vs function calling** — function calling is the model-level mechanism; MCP is the application-level protocol for discovering and invoking tools/resources across processes and vendors
- [ ] **MCP vs A2A** — MCP: agent ↔ tools/context; A2A: agent ↔ agent
- [ ] **MCP vs plugins/OpenAPI tools** — standard lifecycle, capability negotiation, bidirectional features, transport options

### 12.2 Architecture (P0)
- [ ] **Host** (the AI application, e.g., Claude Desktop/Code, IDEs, ChatGPT, custom agents) → one **client** per server connection → **server** (exposes capabilities)
- [ ] **Base protocol** — **JSON-RPC 2.0** messages: requests, responses, notifications; stateful sessions
- [ ] **Lifecycle** — `initialize` request (protocol version + client capabilities + client info) → server responds with its capabilities → `notifications/initialized` → operation → shutdown
- [ ] **Capability negotiation** — tools, resources (subscribe, listChanged), prompts, logging, completions; client capabilities (roots, sampling, elicitation)

### 12.3 Server Primitives (P0)
- [ ] **Tools** (model-controlled) — `tools/list`, `tools/call`; name, description, `inputSchema` (JSON Schema), optional `outputSchema` & **structured content**, **tool annotations** (readOnlyHint, destructiveHint, idempotentHint, openWorldHint — hints, not security guarantees), `isError` results for model-visible errors
- [ ] **Resources** (application-controlled) — URI-identified context data (files, DB rows, API objects), `resources/list`, `resources/read`, resource templates (URI templates), subscriptions & update notifications, resource links in tool results
- [ ] **Prompts** (user-controlled) — reusable prompt templates with arguments, surfaced as slash commands/menus, `prompts/list`, `prompts/get`
- [ ] **Utilities** — logging, progress notifications, cancellation, pagination (cursors), argument completion, ping

### 12.4 Client Primitives (P1)
- [ ] **Sampling** — server asks the client's LLM to generate (server-side agentic behavior without its own API keys; human-in-the-loop approval)
- [ ] **Roots** — client tells server which filesystem/URI boundaries it may operate in
- [ ] **Elicitation** — server requests structured input from the user mid-operation (forms; URL-based elicitation for sensitive flows like OAuth/payments)

### 12.5 Transports (P0)
- [ ] **stdio** — local subprocess, JSON-RPC over stdin/stdout; simplest, used for local tools; never write logs to stdout
- [ ] **Streamable HTTP** (current standard for remote servers) — single endpoint, POST for client messages, optional SSE streaming for responses/notifications, session IDs (`Mcp-Session-Id`), resumability, protocol version header
- [ ] **HTTP+SSE** (original remote transport) — deprecated in favor of Streamable HTTP; know it for legacy servers
- [ ] **Stateless vs stateful servers**, horizontal scaling (session affinity or external session state), serverless deployment

### 12.6 Authorization (P0 for remote servers)
- [ ] Based on **OAuth 2.1** — MCP server acts as an **OAuth resource server**; authorization server can be separate (e.g., your IdP)
- [ ] **Protected Resource Metadata** (RFC 9728) for discovering the authorization server; authorization server metadata (RFC 8414)
- [ ] **Client registration** — Dynamic Client Registration (RFC 7591) and Client ID Metadata Documents (newer spec revisions)
- [ ] **PKCE** mandatory; **resource indicators** (RFC 8707) to bind tokens to the specific MCP server (audience)
- [ ] **Token audience validation**; **no token passthrough** (server must not forward client tokens to upstream APIs — use its own credentials or token exchange)
- [ ] Enterprise patterns — SSO-integrated auth, gateway-based auth, scoped permissions per tool

### 12.7 Spec Evolution (verify latest before interviews)
- [ ] **2024-11-05** — initial spec (stdio + HTTP/SSE, tools/resources/prompts/sampling)
- [ ] **2025-03-26** — OAuth 2.1 authorization framework, **Streamable HTTP**, tool annotations, audio content, JSON-RPC batching (later removed)
- [ ] **2025-06-18** — structured tool output (`outputSchema`), **elicitation**, resource links, OAuth resource-server classification + resource indicators, security best practices, removal of JSON-RPC batching, protocol version header
- [ ] **2025-11-25** — further maturation (e.g., experimental async **tasks** for long-running operations, URL-mode elicitation, sampling with tools, client ID metadata documents, icons) — check the changelog for exact details
- [ ] **Extensions & ecosystem** — MCP Apps (interactive UI from servers), registries, gateways, **Agent Skills** (packaged instructions/scripts loaded on demand — complementary to MCP)

### 12.8 Building MCP Servers (P0)
- [ ] **SDKs** — official Python SDK (with **FastMCP**-style decorators), TypeScript SDK, Java (Spring AI integration), Kotlin, C#, Go, Rust, Swift, Ruby, PHP
- [ ] **Design** — expose workflows, not raw APIs; concise tool outputs; good descriptions; pagination; error messages that guide the model; read-only by default; idempotent writes
- [ ] **Testing & debugging** — **MCP Inspector**, unit tests of tool handlers, integration tests with a client, logging to stderr/log notifications
- [ ] **Deployment** — local (stdio, packaged via npm/uvx/Docker/MCP bundles), remote (Streamable HTTP on containers/serverless/Cloudflare Workers), behind gateways; versioning tool contracts
- [ ] **Using MCP from code** — MCP clients in agent frameworks (OpenAI Agents SDK, Claude Agent SDK, LangChain MCP adapters, Pydantic AI), provider-side MCP connectors

### 12.9 MCP Security (P0)
- [ ] **Prompt injection via tool results/resources** — untrusted content entering context (emails, web pages, tickets) can hijack the agent
- [ ] **Tool poisoning** — malicious instructions hidden in tool descriptions/metadata; **rug pulls** (tool definitions changing after approval); tool name shadowing across servers
- [ ] **Confused deputy** problems with proxy servers & OAuth; **token passthrough** anti-pattern; token theft & over-broad scopes
- [ ] **Local server risks** — arbitrary code execution, supply-chain risk of installing servers (`npx`/`uvx` packages), DNS rebinding on localhost HTTP servers (validate Origin, bind to 127.0.0.1)
- [ ] **Session hijacking**, SSRF via servers fetching URLs
- [ ] **Mitigations** — allowlisted/vetted servers, pinned versions, signed packages, least-privilege scopes, human approval for sensitive tools, sandboxing, output sanitization, monitoring & audit logs, separating untrusted-content tools from high-privilege tools ("lethal trifecta" awareness — §18)

### 🎯 Frequently Asked
- What problem does MCP solve? MCP vs function calling vs A2A
- Explain MCP's architecture: hosts, clients, servers, and the three server primitives
- stdio vs Streamable HTTP — when each? How do you scale a remote MCP server?
- How does authorization work for remote MCP servers?
- What are the main security risks of MCP and how do you mitigate them?
- Design an MCP server for your company's internal APIs — what tools would you expose and how?

---

## 13. Agent & LLM Frameworks (P1)

- [ ] **When to use a framework vs plain code** — frameworks speed prototyping and add abstractions (checkpointing, tracing, integrations) but can obscure prompts and control flow; many production teams use thin custom loops + provider SDKs
- [ ] **LangChain** — chat models, prompt templates, LCEL/runnables, tools, retrievers, document loaders, output parsers; integrations ecosystem
- [ ] **LangGraph** — stateful graphs (nodes, edges, conditional routing), checkpointers & persistence, human-in-the-loop interrupts, streaming, multi-agent patterns, LangGraph Platform
- [ ] **LlamaIndex** — data connectors, indexes, query engines, retrievers, node postprocessors, workflows (event-driven), LlamaParse
- [ ] **Provider agent SDKs** — **OpenAI Agents SDK** (agents, handoffs, guardrails, tracing), **Claude Agent SDK** (agent loop powering Claude Code: tools, subagents, MCP, hooks, permissions), **Google ADK**, AWS Strands Agents
- [ ] **Pydantic AI** (type-safe agents, structured outputs, DI), **DSPy** (programming, not prompting — optimizers), **Haystack** (pipelines), **Semantic Kernel** & **Microsoft Agent Framework** (successor direction for AutoGen + SK), **CrewAI** (role-based multi-agent), **AutoGen/AG2**, **smolagents** (code agents), **Mastra** & **Vercel AI SDK** (TypeScript), **Spring AI** & **LangChain4j** (Java)
- [ ] **Structured output libraries** — Instructor, Outlines, Guidance, BAML, Marvin
- [ ] **Durable execution for agents** — Temporal, Restate, Inngest, DBOS
- [ ] **Low-code/no-code** — n8n, Dify, Flowise, Langflow, Copilot Studio — awareness and when they're appropriate
- [ ] **Framework evaluation criteria** — transparency of prompts, control flow flexibility, observability, async/streaming support, typing, maturity & breaking-change velocity, vendor neutrality, team skills

---

## 14. Multimodal, Voice & Specialized Applications (P1)

- [ ] **Vision-language** — image understanding, document/chart/screenshot QA, OCR via VLMs, visual grounding; image token costs & resolution trade-offs
- [ ] **Document AI** — invoices/receipts/contracts extraction with VLMs + structured outputs; layout models; human review queues; confidence scoring
- [ ] **Speech & voice agents** — STT (Whisper, Deepgram, AssemblyAI), TTS (ElevenLabs, provider TTS), **realtime speech-to-speech APIs**, cascaded (STT → LLM → TTS) vs end-to-end; latency budget (< ~800 ms turn latency), **voice activity detection & turn detection**, barge-in/interruptions, telephony (Twilio, SIP), frameworks (LiveKit Agents, Pipecat)
- [ ] **Image generation** — diffusion models (latent diffusion, U-Net/DiT, guidance, ControlNet, LoRA styles), autoregressive/native image generation; safety & IP concerns; video generation (awareness)
- [ ] **Code generation** — completion vs agentic coding, repo context retrieval, test-driven verification, sandboxed execution, security of generated code
- [ ] **Summarization at scale** — map-reduce, refine, hierarchical summarization, long-context single-pass; evaluation (faithfulness, coverage)
- [ ] **Classification, extraction & routing with LLMs** — zero/few-shot classification, logprob-based confidence, LLMs to label data then distill into small classifiers
- [ ] **Translation & localization**, **search & recommendations** with LLMs (query understanding, LLM reranking, generative retrieval — awareness)
- [ ] **On-device / edge LLMs** — small models, quantization (GGUF, MLX), llama.cpp, privacy & latency benefits

---

# PART C — ADAPTING, SERVING & OPERATING MODELS

## 15. Fine-Tuning & Model Adaptation (P0)

### 15.1 Decision Framework
- [ ] **Adaptation ladder** — prompt engineering → few-shot → RAG/tools → fine-tuning → continued pre-training → training from scratch (rarely justified)
- [ ] **Fine-tune when** — consistent format/style/tone, specialized behavior, latency/cost reduction by distilling into a smaller model, domain jargon, tool-calling reliability for your tools, classification at scale; **don't fine-tune** to inject frequently changing knowledge (use RAG)
- [ ] **Costs & risks** — data collection/labeling, training compute, eval effort, catastrophic forgetting, maintenance on base-model upgrades, hosting of custom models

### 15.2 Techniques (P0)
- [ ] **Full fine-tuning** vs **parameter-efficient fine-tuning (PEFT)**
- [ ] **LoRA** — low-rank update matrices (W + BA), rank `r`, `alpha` scaling, target modules (attention projections, MLP), merging adapters, serving many adapters on one base model (multi-LoRA serving)
- [ ] **QLoRA** — 4-bit NF4 quantized base + LoRA adapters, double quantization, paged optimizers — fine-tune large models on a single GPU
- [ ] **Other PEFT** — DoRA, adapters, prefix/prompt tuning, IA³ (awareness)
- [ ] **SFT** (instruction tuning) with chat templates & loss masking on prompts
- [ ] **Preference tuning** — DPO/ORPO/KTO/SimPO on chosen/rejected pairs
- [ ] **RL fine-tuning** — GRPO/PPO with reward functions or verifiers; reinforcement fine-tuning offerings from providers
- [ ] **Distillation** — teacher-generated data or logit distillation into a smaller student
- [ ] **Embedding & reranker fine-tuning** (contrastive pairs, hard negatives), classification heads on encoders
- [ ] **Vision/multimodal fine-tuning** — awareness

### 15.3 Data for Fine-Tuning (P0)
- [ ] **Quality > quantity** — hundreds to a few thousand excellent examples often beat large noisy sets
- [ ] **Sources** — production logs (with consent & PII scrubbing), expert-written examples, **synthetic data** from stronger models (with filtering & dedupe), human preference labeling
- [ ] **Formatting** — correct chat template, system prompts consistent with inference, multi-turn examples, tool-call examples
- [ ] **Splits & decontamination** — held-out eval sets, no leakage of eval data into training
- [ ] **Data versioning** & lineage

### 15.4 Training Practicalities
- [ ] **Hyperparameters** — learning rate (lower for full FT), epochs (1–3 typical; watch overfitting), batch size & gradient accumulation, warmup, LoRA rank/alpha, max sequence length & packing
- [ ] **Hardware & memory math** — full FT needs ~16+ bytes/param (weights, grads, Adam states) vs QLoRA far less; gradient checkpointing; FSDP/DeepSpeed ZeRO for multi-GPU
- [ ] **Tooling** — Hugging Face **TRL** (SFTTrainer, DPOTrainer, GRPOTrainer), **PEFT**, Accelerate, **Unsloth**, **Axolotl**, LLaMA-Factory, torchtune; managed fine-tuning (OpenAI, Bedrock, Vertex, Together, Fireworks, Databricks)
- [ ] **Evaluation** — task-specific evals before/after, general capability regression checks, safety regression, A/B in production
- [ ] **Experiment tracking** — Weights & Biases, MLflow; model registry & versioning
- [ ] **Licensing** — base model license terms for fine-tuned derivatives & commercial use

### 🎯 Frequently Asked
- When would you fine-tune instead of using RAG or prompting?
- Explain LoRA and QLoRA — why do they work and what are `r` and `alpha`?
- How much data do you need and how do you build it?
- How do you avoid catastrophic forgetting?
- SFT vs DPO — when each?

---

## 16. Inference, Serving & Optimization (P0)

### 16.1 Inference Fundamentals
- [ ] **Prefill vs decode** phases — prefill is compute-bound (parallel over prompt tokens), decode is memory-bandwidth-bound (one token at a time)
- [ ] **Latency metrics** — **TTFT** (time to first token), **TPOT/ITL** (time per output token / inter-token latency), end-to-end latency, **throughput** (tokens/s per GPU, requests/s), goodput under SLOs; percentiles (p50/p95/p99)
- [ ] **Memory** — weights (params × bytes per param: FP16 = 2 B, INT8 = 1 B, INT4 = 0.5 B) + KV cache + activations; e.g., 70B in FP16 ≈ 140 GB weights → multi-GPU
- [ ] **GPU basics** — VRAM, HBM bandwidth, compute (TFLOPs), NVLink/InfiniBand, tensor cores; NVIDIA A100/H100/H200/B200/L4/L40S, AMD MI300X, Google TPUs, AWS Inferentia/Trainium; Apple Silicon for local inference
- [ ] **Roofline intuition** — why batching increases throughput (amortizing weight reads) but raises latency

### 16.2 Optimization Techniques (P0)
- [ ] **Batching** — static vs dynamic vs **continuous (in-flight) batching**
- [ ] **PagedAttention** (vLLM) — KV cache in pages, less fragmentation, higher batch sizes
- [ ] **Prefix/prompt caching** (automatic prefix caching, radix-tree caching in SGLang) — reuse KV for shared prompts
- [ ] **Quantization** — weight-only (GPTQ, AWQ), INT8 (LLM.int8, SmoothQuant), **FP8** (H100+), FP4/MXFP4 (newer GPUs), **GGUF** (llama.cpp k-quants), bitsandbytes; KV-cache quantization; quality trade-offs & evaluating quantized models
- [ ] **Speculative decoding** — draft model proposes tokens, target verifies in parallel; Medusa heads, EAGLE, n-gram/prompt lookup decoding
- [ ] **Parallelism for serving** — tensor parallelism (split layers across GPUs), pipeline parallelism, expert parallelism for MoE, data-parallel replicas
- [ ] **Disaggregated prefill/decode** serving (separate pools), KV-cache transfer (NVIDIA Dynamo, llm-d) — awareness
- [ ] **Kernel optimizations** — FlashAttention, fused kernels, CUDA graphs, `torch.compile`
- [ ] **Structured/constrained decoding** overhead & engines (xgrammar)
- [ ] **Smaller models & distillation**, early exit (awareness), model cascades/routing
- [ ] **Long-context serving** — chunked prefill, context caching

### 16.3 Serving Stack (P0)
- [ ] **Engines** — **vLLM** (PagedAttention, continuous batching, OpenAI-compatible server, multi-LoRA), **SGLang** (RadixAttention, structured outputs), **TensorRT-LLM** (NVIDIA-optimized), **TGI** (Hugging Face), **NVIDIA Triton / Dynamo**, **llama.cpp**, **Ollama**, LM Studio, MLX, LMDeploy
- [ ] **Platforms** — KServe, Ray Serve, BentoML, SageMaker endpoints, Vertex AI endpoints, Bedrock custom model import, Modal, Baseten, Together, Fireworks, Replicate, RunPod
- [ ] **Kubernetes for GPUs** — NVIDIA device plugin/GPU operator, node pools, MIG (multi-instance GPU), time-slicing, gang scheduling (Kueue/Volcano), large image/model weight loading (cold starts), model caching on nodes
- [ ] **Autoscaling** — on queue depth/concurrency/KV-cache utilization (not CPU), scale-to-zero trade-offs, warm pools, cold-start mitigation
- [ ] **Load balancing** — prefix-aware/KV-cache-aware routing, session affinity, request prioritization, fairness across tenants
- [ ] **Self-host vs API economics** — utilization is everything; cost per million tokens at given QPS; data privacy needs; ops burden; when hybrid makes sense

### 16.4 Application-Level Latency Optimization
- [ ] Streaming to reduce perceived latency; parallelizing independent LLM calls; smaller/faster models for sub-tasks; prompt caching; shorter prompts & outputs (output tokens dominate latency); speculative execution of likely next steps; precomputation & caching of answers; edge/regional endpoints

### 🎯 Frequently Asked
- Why is decoding memory-bound? What does continuous batching do?
- How does PagedAttention work?
- How much GPU memory do you need to serve a 70B model at 16k context for 32 concurrent users?
- What quantization would you choose and how do you validate quality?
- Explain speculative decoding
- Self-hosting vs API — how do you decide?
- How do you autoscale LLM inference?

---

## 17. Evaluation (Evals) (P0)

> Evals are the single most important practice that separates prototypes from production GenAI. Expect deep questions here.

### 17.1 Philosophy & Process
- [ ] **Eval-driven development** — define success criteria first; every prompt/model/retrieval change is measured; regression suites in CI
- [ ] **Error analysis first** — read real traces/outputs, categorize failures (open coding → axial coding into failure taxonomies), prioritize by frequency & impact, then build targeted evals
- [ ] **Offline vs online evals** — pre-deployment test sets vs production monitoring, A/B tests, user feedback
- [ ] **Levels** — unit-test-style assertions (format, contains/not contains, JSON validity, tool called) → model-graded evals → human evals → A/B business metrics

### 17.2 Methods (P0)
- [ ] **Code-based checks** — exact match, regex, schema validation, execution (code passes tests), SQL result equivalence, tool-call correctness
- [ ] **Reference-based metrics** — exact match, F1, BLEU/ROUGE (weak for open-ended), BERTScore, embedding similarity — and their limitations
- [ ] **LLM-as-a-judge** — pointwise scoring with rubrics, **pairwise comparison**, reference-guided judging; binary pass/fail often more reliable than 1–10 scales; chain-of-thought before verdict; **biases** (position, verbosity, self-preference, leniency); calibrating judges against human labels (agreement, Cohen's kappa, precision/recall of the judge); using different/stronger judge models; judge prompt versioning
- [ ] **Human evaluation** — expert review, annotation guidelines, inter-annotator agreement, side-by-side preference, cost management
- [ ] **Task-specific metrics** — RAG (faithfulness, context recall/precision, answer correctness), agents (task success, trajectory, steps, cost), classification (precision/recall/F1), summarization (faithfulness, coverage), safety (refusal correctness, jailbreak resistance), conversational quality
- [ ] **Statistical rigor** — dataset size, confidence intervals, variance across runs (non-determinism), significance testing for model comparisons

### 17.3 Datasets (P0)
- [ ] **Golden datasets** — curated inputs + expected outputs/criteria; sampled from production; cover edge cases, adversarial inputs, multiple languages, long inputs
- [ ] **Synthetic data generation** for evals — persona/scenario-driven generation, dimension-based sampling, filtering for realism
- [ ] **Dataset maintenance** — versioning, adding every production bug as a test case, avoiding overfitting to the eval set, refreshing as product changes
- [ ] **Public benchmarks vs product evals** — benchmarks guide model shortlisting only

### 17.4 Tooling
- [ ] **promptfoo**, **DeepEval**, **RAGAS**, **Braintrust**, **LangSmith**, **Langfuse**, **Arize Phoenix**, **W&B Weave**, **Inspect AI** (UK AISI), OpenAI Evals, MLflow GenAI evaluation, Patronus, Galileo
- [ ] **CI integration** — run evals on PRs touching prompts/retrieval/models; thresholds & gating; cost control (sampled eval sets)

### 17.5 Online Evaluation & Monitoring
- [ ] Production sampling + async LLM-judge scoring, user feedback (explicit & implicit), escalation/deflection rates, task completion, A/B testing models/prompts with business metrics, drift detection in input distributions, guardrail trigger rates

### 🎯 Frequently Asked
- How do you evaluate an LLM feature before launch?
- How do you make LLM-as-a-judge trustworthy?
- Walk me through your error analysis process
- How do you evaluate a RAG system / an agent?
- How do you know a new model version is better for your product?
- How do you prevent eval sets from going stale or being overfit?

---

## 18. Guardrails, Safety & LLM Security (P0)

### 18.1 Threat Landscape
- [ ] **OWASP Top 10 for LLM Applications (2025)** — LLM01 Prompt Injection, LLM02 Sensitive Information Disclosure, LLM03 Supply Chain, LLM04 Data and Model Poisoning, LLM05 Improper Output Handling, LLM06 Excessive Agency, LLM07 System Prompt Leakage, LLM08 Vector and Embedding Weaknesses, LLM09 Misinformation, LLM10 Unbounded Consumption
- [ ] **Prompt injection** — direct (user tries to override instructions) vs **indirect** (malicious instructions in retrieved docs, web pages, emails, tool results, images); it is not fully solvable by prompting alone
- [ ] **Jailbreaks** — role-play, encoding/obfuscation, many-shot, multi-turn escalation
- [ ] **Data exfiltration** — via rendered Markdown images/links, tool calls to attacker URLs, hidden in outputs; the **"lethal trifecta"** — access to private data + exposure to untrusted content + ability to communicate externally → design so an agent never has all three unguarded
- [ ] **Excessive agency** — over-privileged tools, autonomous destructive actions
- [ ] **Model/data supply chain** — malicious model weights (pickle → prefer **safetensors**), poisoned fine-tuning/RAG data, compromised packages/MCP servers
- [ ] **Unbounded consumption** — denial-of-wallet, token flooding, recursive agent loops
- [ ] **Vector store risks** — cross-tenant leakage, embedding inversion, poisoned documents

### 18.2 Defenses (P0)
- [ ] **Architecture first** — least privilege tools, separating untrusted-content processing from privileged actions, **dual-LLM / quarantined LLM pattern**, CaMeL-style capability/data-flow control, plan-then-execute with fixed plans, allowlisted destinations
- [ ] **Human approval** for high-impact actions; read-only defaults; scoped, short-lived credentials
- [ ] **Input guardrails** — injection/jailbreak classifiers (Llama Prompt Guard, provider classifiers, Lakera, Azure Prompt Shields), topic restrictions, PII detection & redaction (Presidio), length/rate limits
- [ ] **Output guardrails** — moderation (provider moderation APIs, Llama Guard, ShieldGemma), PII/secret scanning, schema validation, grounding/citation checks, **sanitizing outputs before rendering** (no raw HTML/Markdown images to arbitrary URLs), never executing model output without sandboxing (SQL/code/shell)
- [ ] **Spotlighting/delimiting** untrusted content, instruction hierarchy, system prompt hardening (assume system prompts will leak — no secrets in prompts)
- [ ] **Guardrail frameworks** — NVIDIA NeMo Guardrails, Guardrails AI, AWS Bedrock Guardrails, Azure AI Content Safety, LLM Guard
- [ ] **Rate limiting & quotas** per user/tenant (tokens & cost), budget alerts, max steps for agents
- [ ] **Red teaming** — manual & automated (PyRIT, garak, promptfoo red-team), adversarial eval suites, bug bounties
- [ ] **Monitoring** — logging prompts/outputs (with privacy controls), anomaly detection, incident response for AI failures

### 18.3 Hallucination & Reliability
- [ ] Grounding with retrieval, requiring citations, verification passes (self-check, second model, fact-checking against sources), constrained outputs, abstention ("I don't know") with calibrated thresholds, domain restriction, user-facing uncertainty communication

### 🎯 Frequently Asked
- How do you defend against indirect prompt injection in an agent that reads emails?
- What is the "lethal trifecta" and how do you design around it?
- How do you prevent sensitive data leakage through an LLM app?
- What guardrails would you put on a customer-facing chatbot?
- How do you red-team an LLM application?

---

## 19. LLMOps & Production Engineering (P0)

### 19.1 Reference Architecture
- [ ] Client → API/BFF → **LLM gateway** (auth, routing, rate limits, quotas, caching, fallbacks, logging, cost tracking) → orchestration layer (chains/agents) → retrieval & tools (vector DB, search, APIs, MCP servers) → model providers/self-hosted inference → guardrails → observability & eval pipelines → feedback store

### 19.2 Observability (P0)
- [ ] **Tracing** every LLM call & agent step — prompts, completions, tool calls, retrieved docs, latency, tokens, cost, model version, user/tenant
- [ ] **Tools** — Langfuse (open source), LangSmith, Arize Phoenix, Helicone, Braintrust, Datadog LLM Observability, W&B Weave; **OpenTelemetry GenAI semantic conventions**, OpenLLMetry/OpenInference
- [ ] **Dashboards** — latency (TTFT, total), error/refusal rates, token usage & cost per feature/tenant, cache hit rates, guardrail triggers, eval scores over time, user feedback
- [ ] **Privacy** — PII redaction in logs, retention policies, access controls on trace data

### 19.3 Reliability (P0)
- [ ] **Timeouts, retries with backoff + jitter** (only on retryable errors), **fallback models/providers**, circuit breakers on degraded providers, hedged requests for latency-critical paths
- [ ] **Idempotency** for side-effecting tool calls & retried agent steps
- [ ] **Graceful degradation** — cached answers, smaller models, non-AI fallback paths
- [ ] **Async processing** for long tasks — queues, background workers, webhooks/polling, progress streaming
- [ ] **Rate-limit management** — client-side throttling, request prioritization, provisioned throughput, multi-region/multi-account capacity

### 19.4 Cost Management (P0)
- [ ] Token accounting per request/feature/tenant; budgets & alerts
- [ ] **Levers** — model routing/cascades, prompt compression & shorter outputs, **prompt caching**, **semantic caching** (embedding-similarity cache with thresholds & invalidation; risk of wrong cache hits), exact caching, batch APIs for offline work, distillation/fine-tuned small models, limiting agent steps, retrieving fewer but better chunks
- [ ] **Unit economics** — cost per conversation/task vs revenue/value; pricing your AI features

### 19.5 Change Management (P0)
- [ ] **Versioning** — prompts, models (pin exact versions), retrieval configs, tools, eval datasets; reproducible runs
- [ ] **Release process** — offline evals → shadow mode → canary/A-B → full rollout; feature flags; rollback
- [ ] **Model upgrades & deprecations** — regression evals, prompt re-tuning, behavior diffing
- [ ] **Feedback loops & data flywheel** — capture feedback & corrections → improve prompts/retrieval/evals → fine-tuning datasets (with consent)
- [ ] **CI/CD for LLM apps** — unit tests (mocked LLMs), eval gates, prompt linting, security scans

### 19.6 Scaling & Multi-Tenancy
- [ ] Per-tenant isolation (data, vector namespaces, quotas, model configs), noisy neighbors, BYO-key models, data residency, enterprise SSO & audit logs

---

## 20. Responsible AI, Governance & Compliance (P1)

- [ ] **Principles** — fairness, transparency, accountability, privacy, safety, human oversight
- [ ] **Bias & fairness** — sources (training data, prompts, retrieval), measuring disparities, mitigation
- [ ] **Transparency** — disclosing AI use, model/system cards, explaining limitations, citations
- [ ] **Regulation** — **EU AI Act** (risk tiers; prohibited practices applicable from Feb 2025; general-purpose AI model obligations from Aug 2025; high-risk system obligations phasing in from 2026–2027), GDPR (lawful basis, automated decision-making, data subject rights for logs/memory), sector rules (finance, healthcare/HIPAA), India's DPDP Act & AI governance guidelines, US state laws & sector guidance
- [ ] **Frameworks & standards** — NIST AI RMF (+ Generative AI profile), ISO/IEC 42001 (AI management systems), internal AI governance boards & review processes
- [ ] **Data governance for AI** — consent for training on user data, zero-data-retention agreements with providers, data residency, PII minimization, retention of prompts/outputs
- [ ] **Intellectual property** — copyright concerns for training data & outputs, license compliance of open models, code-generation license risks, indemnification offerings
- [ ] **Environmental cost** — energy/compute awareness, efficiency choices

---

# PART D — ENGINEERING FOUNDATIONS FOR AI ENGINEERS

## 21. Python & Backend Engineering for AI (P0)

- [ ] **Python depth** — data model, generators, decorators, context managers, typing (Protocols, generics, TypedDict), dataclasses & **Pydantic v2**, packaging with **uv**, testing with pytest (mocking LLM clients, fixtures, snapshot tests of prompts)
- [ ] **Concurrency** — **asyncio** for parallel LLM/tool calls (`gather`/`TaskGroup`, semaphores for rate limits, timeouts, cancellation), threads vs processes, avoiding blocking the event loop
- [ ] **APIs** — **FastAPI** (async endpoints, dependency injection, SSE/WebSocket streaming, background tasks, lifespan for model/client init), request validation, auth (OAuth/JWT), API design for long-running AI tasks (202 + polling, webhooks)
- [ ] **Queues & workers** — Celery/RQ/Arq/Temporal for ingestion, batch inference, long agent runs; idempotency & retries
- [ ] **Data stores** — Postgres (+ pgvector), Redis (caching, rate limiting, session/memory), object storage (S3) for documents, search engines (Elasticsearch/OpenSearch)
- [ ] **TypeScript** familiarity — many AI apps are full-stack (Next.js + Vercel AI SDK); MCP servers often in TS
- [ ] **Software engineering hygiene** — clean architecture around LLM calls (provider-agnostic interfaces where useful), configuration management, secrets, logging, error handling, code review standards for prompts

---

## 22. Data Engineering for AI (P1)

- [ ] **Document ingestion pipelines** — connectors, change detection, parsing at scale, dedupe, PII handling, metadata & ACL capture
- [ ] **Batch embedding pipelines** — Spark/Ray/Dask for large corpora, rate-limited API embedding with retries, GPU batch embedding with open models, cost estimation, incremental refresh
- [ ] **Data quality for AI** — garbage in, garbage out; document freshness, duplicates, contradictory sources, labeling quality
- [ ] **Training/eval data management** — dataset versioning (DVC, lakeFS, Hugging Face Datasets), lineage, splits, consent tracking
- [ ] **Structured data access** — SQL proficiency, semantic layers for text-to-SQL, data warehouses (Snowflake/BigQuery/Databricks) and their AI functions
- [ ] **Orchestration** — Airflow/Dagster/Prefect for ingestion & eval jobs
- [ ] **Streaming** — Kafka for real-time indexing & event-driven agents (awareness)

---

## 23. MLOps & Infrastructure (P1)

- [ ] **ML lifecycle tooling** — experiment tracking (MLflow, W&B), model registry, feature stores (Feast), pipelines (Kubeflow, SageMaker Pipelines, Vertex Pipelines, Metaflow, ZenML), model monitoring (drift — Evidently)
- [ ] **Cloud AI platforms** — AWS (Bedrock, SageMaker, Bedrock Knowledge Bases & Agents), Azure (AI Foundry, AI Search, OpenAI service), GCP (Vertex AI, Model Garden, Vertex AI Search, Agent Builder); managed RAG vs custom trade-offs
- [ ] **Containers & Kubernetes** — Docker images with CUDA, image size & cold starts, GPU scheduling, KServe/Ray Serve, autoscaling, spot GPUs for batch
- [ ] **Distributed compute** — Ray (Data, Train, Serve, Tune), Spark for preprocessing
- [ ] **IaC & CI/CD** — Terraform, GitHub Actions, environment promotion, secrets management
- [ ] **Networking & security** — private endpoints to model providers, VPC-hosted inference, egress control for agents/sandboxes, IAM least privilege

---

## 24. Classic Distributed Systems & System Design Essentials (P1)

> Senior AI engineers are often given a classic system design round too, and GenAI designs rely on these fundamentals.

- [ ] **Building blocks** — load balancers, API gateways, caches (Redis), SQL vs NoSQL, object storage, message queues/streams (Kafka, SQS), search, CDNs, workers
- [ ] **Concepts** — horizontal scaling, replication, sharding & consistent hashing, CAP & consistency models, idempotency, retries with backoff, circuit breakers, rate limiting (token bucket), backpressure, outbox pattern, sagas
- [ ] **Estimation** — QPS, storage, bandwidth (1 day ≈ 10⁵ s); add token & GPU estimation for AI systems
- [ ] **Real-time communication** — SSE vs WebSockets vs polling (streaming tokens!)
- [ ] **Classic problems** — rate limiter, URL shortener, notification system, chat system, news feed, search autocomplete, web crawler (for RAG ingestion), distributed job scheduler
- [ ] **Observability & SRE** — logs/metrics/traces, SLOs & error budgets, incident management

---

# PART E — GENAI SYSTEM DESIGN

## 25. GenAI System Design Framework & Estimation (P0)

### 25.1 Framework
- [ ] **1. Problem & success criteria** — user, task, business value; what "good" looks like (quality metrics), **is an LLM even the right tool?** (rules, classical ML, search may suffice)
- [ ] **2. Requirements** — functional scope; non-functional: latency (TTFT, total), throughput/QPS, quality targets, cost per request budget, availability, data privacy/residency, safety/compliance, languages, modalities
- [ ] **3. Data** — sources, volume, freshness, structure, permissions, PII; ingestion & indexing design
- [ ] **4. Model strategy** — API vs open-weight self-hosted; model tiers & routing; prompting vs RAG vs fine-tuning; embedding & reranker choices
- [ ] **5. Architecture** — components & data flow (gateway, orchestration, retrieval, tools/MCP, memory, guardrails, caching, async workers), sequence of a request, streaming path
- [ ] **6. Evaluation plan** — offline golden sets, LLM judges, human review, online metrics & A/B, feedback loops
- [ ] **7. Safety & security** — prompt injection, data leakage, access control, output handling, human-in-the-loop, abuse prevention
- [ ] **8. Operations** — observability, cost controls, rate limits, fallbacks, model upgrades, incident response
- [ ] **9. Scale & cost estimation** — tokens, GPU needs, storage (vectors), $/month
- [ ] **10. Iteration roadmap** — MVP → v2 (fine-tuning, agents, personalization); risks & mitigations

### 25.2 Estimation Cheat Sheet
- [ ] **Tokens** — ~4 characters ≈ 1 token in English (~0.75 words/token); a page ≈ 500–800 tokens
- [ ] **Cost/request** = (input tokens × input price) + (output tokens × output price) [+ thinking tokens]; apply cache discounts; monthly = cost/request × requests/day × 30
- [ ] **Latency** ≈ TTFT + output tokens × TPOT (e.g., 500 output tokens × 20 ms = 10 s → stream it, or shrink outputs)
- [ ] **Self-hosted capacity** — tokens/s per GPU (model & batch dependent) → GPUs needed = peak output tokens/s ÷ per-GPU throughput (with headroom); weights + KV cache memory must fit
- [ ] **Vector storage** — chunks = docs × avg chunks/doc; memory ≈ chunks × dims × bytes (+ index overhead); embedding cost = total tokens × embedding price
- [ ] **Throughput limits** — provider TPM/RPM quotas vs peak load → need for quota increases, multiple deployments, or queueing

---

## 26. Classic GenAI System Design Problems (P0)

> Practice each aloud: requirements → data → model strategy → architecture → evals → safety → ops → cost.

| # | Problem | Key deep dives |
|---|---------|----------------|
| 1 | [ ] **Enterprise knowledge assistant (RAG over 10M docs from Confluence/SharePoint/Drive)** | Connectors & incremental sync, parsing, chunking, hybrid search + rerank, **ACL-aware retrieval**, citations, freshness/deletes, evals, multi-tenant |
| 2 | [ ] **Customer support chatbot with escalation** | Intent routing, RAG over help center, tools (order lookup via APIs/MCP), policies & guardrails, human handoff, deflection metrics, multilingual |
| 3 | [ ] **AI coding assistant / coding agent** | Repo indexing (code embeddings + symbol graph), context selection, edit/apply tools, test execution sandbox, latency for completions, evaluation (SWE-bench-like) |
| 4 | [ ] **AI search engine (Perplexity-like)** | Query understanding, web search APIs/crawling, fetching & extraction, reranking, synthesis with citations, freshness, cost per query, caching |
| 5 | [ ] **Text-to-SQL analytics assistant** | Schema linking/semantic layer, few-shot retrieval of example queries, SQL validation & sandboxed read-only execution, result explanation & charts, access control, evaluation by execution accuracy |
| 6 | [ ] **Document processing pipeline (invoices/contracts extraction)** | Parsing/VLMs, structured outputs, validation rules, confidence & human review queue, batch processing, throughput & cost |
| 7 | [ ] **Company-wide LLM gateway/platform** | Multi-provider routing, auth & quotas per team, rate limiting by tokens, caching (prompt/semantic), PII redaction, logging & cost attribution, fallbacks, policy enforcement |
| 8 | [ ] **Multi-agent deep research assistant** | Orchestrator–subagents, parallel search, context isolation, source evaluation, report synthesis with citations, budgets & stop conditions |
| 9 | [ ] **Voice agent for a call center** | Realtime STT/LLM/TTS pipeline, latency budget, turn detection & barge-in, tool calls (CRM), compliance (recording consent), escalation, monitoring |
| 10 | [ ] **Meeting summarizer & action-item extractor** | Long transcripts (chunked/hierarchical summarization), speaker diarization, structured outputs, integrations (calendar, tasks), privacy |
| 11 | [ ] **Personalized content/email generation at scale** | Batch APIs, templates + LLM, brand/safety guardrails, quality sampling, cost per message, A/B testing |
| 12 | [ ] **Content moderation system with LLMs** | Tiered classifiers (cheap model → LLM → human), policy prompts, latency, appeals, adversarial users, metrics (precision/recall per policy) |
| 13 | [ ] **Semantic product search & recommendations for e-commerce** | Hybrid search, query rewriting, multimodal embeddings, LLM reranking, latency at high QPS, caching, relevance evals |
| 14 | [ ] **Agent platform with an MCP tool ecosystem** | Tool registry, MCP servers per internal system, OAuth & scoped permissions, approval workflows, sandboxing, audit logs, observability |
| 15 | [ ] **LLM evaluation platform** | Dataset management, judge models, experiment tracking, CI integration, human annotation workflows, dashboards |
| 16 | [ ] **Fine-tuning platform (self-serve for teams)** | Data pipelines, job scheduling on GPUs, LoRA adapters registry, eval gates, multi-LoRA serving |
| 17 | [ ] **LLM inference serving platform (multi-model, self-hosted)** | vLLM/SGLang clusters, GPU scheduling, autoscaling on queue depth, prefix-aware routing, quantization, multi-LoRA, SLOs per tenant, cost per token |
| 18 | [ ] **Long-term memory system for an AI assistant** | Memory extraction, storage (vector + structured), retrieval & relevance, updates/conflicts, user controls & privacy, evaluation |
| 19 | [ ] **Guardrails/safety service** | Input/output classifiers, PII redaction, injection detection, latency budget, policy configuration per product, monitoring |
| 20 | [ ] **"Chat with your PDFs" SaaS** | Upload pipeline, parsing, per-user indexes, multi-tenancy, cost controls, citations with page highlights |
| 21 | [ ] **AI code review bot** | PR diff context, repo retrieval, comment generation & dedupe, false-positive control, eval with historical PRs, security |
| 22 | [ ] **Legal/healthcare assistant with strict compliance** | Data residency, PHI/PII handling, citations & abstention, audit trails, human review, regulatory constraints |
| 23 | [ ] **Ticket triage & routing with LLMs** | Classification (LLM vs fine-tuned small model), confidence thresholds, human fallback, drift monitoring, batch vs realtime |
| 24 | [ ] **Generative UI / AI features inside an existing SaaS product** | Feature selection, streaming UX, guardrails, per-tenant data isolation, rollout & evals |
| 25 | [ ] **Real-time translation/localization pipeline** | Glossaries & terminology, quality estimation, human post-editing, caching, cost |

---

## 27. Product Thinking & AI UX (P1)

- [ ] **Problem selection** — high-value, error-tolerant tasks first; where AI augments vs automates; build vs buy (copilots, managed RAG)
- [ ] **When NOT to use LLMs** — deterministic logic, strict correctness with no verification, very low latency budgets, tiny margins; simpler ML/search alternatives
- [ ] **AI UX patterns** — streaming, showing sources/citations, confidence & uncertainty cues, easy correction/undo, editable drafts, suggestions vs auto-actions, explicit approvals for actions, transparent limitations, feedback controls, latency masking (progress, partial results), graceful failure messages
- [ ] **Measuring success** — task success, time saved, deflection/resolution rates, CSAT, retention, adoption, cost per successful outcome; tying evals to business KPIs
- [ ] **ROI & roadmap** — quantifying value vs inference cost; experiments; prioritization; communicating AI uncertainty to stakeholders

---

# PART F — CODING INTERVIEWS

## 28. ML/LLM Coding From Scratch (P0)

> Common in AI engineer / applied scientist loops. Implement in Python/NumPy/PyTorch without libraries doing the core work.

- [ ] **Softmax** (numerically stable), **cross-entropy loss**, **cosine similarity** & top-k nearest neighbors (vectorized)
- [ ] **Scaled dot-product attention** & **multi-head self-attention** with causal mask (NumPy & PyTorch)
- [ ] **A transformer block** (attention + MLP + LayerNorm/RMSNorm + residuals); a tiny GPT forward pass
- [ ] **Autoregressive generation loop** with temperature, top-k, top-p sampling; greedy & beam search (awareness)
- [ ] **KV cache** implementation in a generation loop
- [ ] **BPE tokenizer** (training merges on a small corpus, encode/decode)
- [ ] **LoRA layer** (wrapping a linear layer with low-rank A/B matrices)
- [ ] **Classical ML** — logistic regression with gradient descent, k-means, k-NN, linear regression; train/test split & metrics (precision/recall/F1)
- [ ] **Retrieval** — BM25 scoring, TF-IDF, a simple vector index with brute-force search, RRF fusion of two ranked lists, MMR
- [ ] **Evaluation metrics** — recall@k, MRR, nDCG implementations
- [ ] **Training loop** in PyTorch for a small classifier (DataLoader, optimizer, scheduler, eval)

---

## 29. Applied GenAI Coding & Take-Homes (P0)

- [ ] **Build a RAG pipeline end to end** — load docs, chunk, embed, store (pgvector/Chroma/FAISS), hybrid retrieve, rerank, generate with citations, plus an eval script with a small golden set
- [ ] **Chunkers** — recursive splitter with overlap; Markdown-aware splitter
- [ ] **ReAct/tool-calling agent loop** from scratch using a provider SDK — tool registry, JSON schema tools, max steps, error handling, tracing
- [ ] **Build an MCP server** (Python or TypeScript) exposing 2–3 tools and a resource; test with MCP Inspector; connect from a client
- [ ] **Structured extraction** — Pydantic schema → LLM → validate → retry on failure
- [ ] **Async batching of LLM calls** with concurrency limits (semaphore), retries with exponential backoff & jitter, rate-limit handling (token bucket)
- [ ] **Streaming endpoint** — FastAPI SSE that proxies provider token streams, handles client disconnects & cancellation
- [ ] **Semantic cache** — embedding similarity lookup with threshold & TTL
- [ ] **LLM-as-judge evaluator** — rubric prompt, pairwise comparison, agreement with human labels
- [ ] **Text-to-SQL** with schema retrieval and safe execution (read-only, LIMIT, validation)
- [ ] **Parse SSE stream / partial JSON** from a streaming response
- [ ] **Take-home best practices** — clear README with design decisions & trade-offs, evals included, tests, config via env, Docker, cost/latency notes, limitations & next steps

---

## 30. DSA in Python (P1)

> Many AI engineer loops still include 1–2 standard coding rounds (Easy–Medium). Target **150–200 problems**.

- [ ] **Patterns** — arrays/hashing, two pointers, sliding window, stacks (monotonic), binary search, linked lists, trees (BFS/DFS), heaps (top-K — very relevant to retrieval), graphs (BFS/DFS, topological sort), intervals, backtracking, DP basics (1D/2D, knapsack, LIS/LCS/edit distance — edit distance relates to text metrics), tries (autocomplete/tokenization), union-find
- [ ] **Python idioms** — `heapq`, `collections` (`Counter`, `defaultdict`, `deque`), `bisect`, `functools.cache`, `itertools`, sorting with keys
- [ ] **AI-flavored problems** — top-K similar vectors, merge K sorted result lists, LRU cache for embeddings, rate limiter, rolling-window stats for monitoring, string similarity (edit distance), tokenization-like string parsing, dependency graphs for agent task plans (topological sort)

---

# PART G — LEADERSHIP, BEHAVIORAL & CAREER

## 31. Technical Leadership in AI Teams (P0)

- [ ] **AI strategy** — identifying high-ROI use cases, build vs buy vs partner, model/provider strategy & vendor risk, platform vs product investments, responsible AI policies
- [ ] **Setting engineering standards** — eval-driven development, prompt/version management, observability requirements, security reviews for agents/MCP, cost budgets, production readiness checklists for AI features
- [ ] **Managing uncertainty** — probabilistic systems in deterministic orgs; communicating quality levels, risks and timelines to executives; prototype → production gap; setting expectations against hype
- [ ] **Cross-functional leadership** — product, design (AI UX), legal/compliance, security, data teams, domain experts for evals/labeling
- [ ] **Execution** — scoping AI projects with go/no-go gates based on evals, iterative delivery, managing GPU/API budgets, vendor management
- [ ] **People** — mentoring engineers transitioning into AI, building eval culture, hiring AI engineers (interview design: practical builds + evals + system design), knowledge sharing in a fast-moving field
- [ ] **Track decision** — Staff/Principal AI engineer vs AI engineering manager vs applied scientist path

---

## 32. Behavioral Interviews & Story Bank (P0)

### 32.1 Format
- [ ] STAR / STAR-L; 2–3 minutes; "I" not "we"; quantify (accuracy 72% → 91% on evals, cost −60% via routing/caching, p95 latency −45%, deflection +25%, hours saved); show trade-offs & judgment; real failures; prepare for deep follow-ups

### 32.2 Story Bank (15–20 stories)
- [ ] Shipping an LLM feature from prototype to production · biggest GenAI system you designed (RAG/agent/platform) · a key architecture/model decision with trade-offs (API vs self-host, RAG vs fine-tune) · an AI quality incident (hallucination reached users, prompt injection, data leak, runaway cost) and the fix · failure/mistake (over-built an agent when a workflow sufficed) · building an eval culture/framework · convincing stakeholders on realistic AI scope or on investing in evals/guardrails · disagreement with product/research/leadership about launching · influencing without authority · mentoring engineers into AI · tight deadline with model uncertainty · ambiguity (vague "add AI" requests) · cost or latency optimization with numbers · security/compliance handling (PII, EU AI Act, customer data) · data-driven decision (A/B test of models/prompts) · learning a new area fast (e.g., MCP, fine-tuning) · customer obsession (user research on AI UX) · delivering bad news (feature not reliable enough to ship) · hiring/building an AI team · pre-GenAI career stories that show fundamentals (distributed systems, data, ML)

### 32.3 Common Questions
- [ ] Tell me about yourself (90–120 s — connect your 10-year engineering foundation to your GenAI depth) · **why the career break** (intentional 2–3 months of upskilling — cite the projects you built: RAG with evals, MCP server, fine-tuned model) · why this company/role · strengths/weaknesses · greatest achievement · 5-year plan · IC vs manager · how you keep up with the field (and filter hype) · your view on AI risks/safety · how you use AI coding tools in your own workflow
- [ ] Company frameworks — Amazon LPs, Google, Meta, AI-lab-specific values (safety, mission alignment, intellectual honesty); map stories to values
- [ ] Questions to ask — how AI features are evaluated before launch, model/provider strategy, GPU/API budgets, AI governance & safety review process, team composition (research vs engineering), biggest AI quality challenges today

---

## 33. Portfolio, Project Deep-Dive, Resume & Negotiation (P0)

- [ ] **Portfolio (very strong signal in AI hiring)** — 2–3 polished public projects with READMEs, architecture diagrams, **eval results**, and demos: e.g., (1) production-style RAG with hybrid search, reranking, ACLs & RAGAS/promptfoo evals; (2) MCP server + agent with guardrails & tracing; (3) fine-tuned small model (LoRA/QLoRA) beating a prompt baseline on a defined eval; optional blog posts explaining decisions
- [ ] **Deep dives (2–3 projects)** — problem & users, data, model choices & alternatives, architecture, eval methodology & results, failure analysis, safety measures, latency/cost numbers, incidents, what you'd change, how it would scale 10×
- [ ] **Resume** — impact bullets with metrics; keywords (LLMs, RAG, agents, MCP, evals, LangGraph/LlamaIndex, vector DBs, fine-tuning LoRA/QLoRA, vLLM, Python/FastAPI, AWS Bedrock/Azure OpenAI/Vertex, Kubernetes, guardrails); show the engineering foundation too
- [ ] **Search & negotiation** — tiered targets (AI labs, big tech AI orgs, AI-native startups, enterprises adopting AI), referrals, apply by week 4–6, track pipeline, research comp (AI roles often carry premiums; evaluate equity carefully at startups), negotiate level & total comp

---

## 34. Interview Formats

| Company type | Typical loop for a senior GenAI engineer | Prep emphasis |
|--------------|------------------------------------------|---------------|
| **AI labs / model providers** | Coding (practical + DSA) · ML/LLM fundamentals deep dive · system design (inference, evals, agents) · behavioral/values (safety, mission) | Transformer internals, inference, evals, safety, strong coding |
| **Big Tech AI orgs** | DSA (1–2) · ML/GenAI system design · applied LLM deep dive · behavioral | DSA + GenAI system design + fundamentals |
| **AI-native startups** | Take-home or live build (RAG/agent) · system design · product sense · founder chat | Shipping speed, evals, pragmatism, product thinking |
| **Enterprises adopting AI** | GenAI architecture & cloud platform (Bedrock/Azure/Vertex) · RAG/agents design · governance & security · stakeholder scenarios | Enterprise RAG, security, compliance, integration |
| **Consulting / solutions roles** | Case-style architecture · client communication · demos | Breadth, communication, reference architectures |
| **Staff/Principal** | AI strategy & platform architecture · past-work review · cross-team leadership | Vision, trade-offs, influence, risk management |

---

# PART H — EXECUTION

## 35. Rapid-Fire Questions (Top 100)

**Foundations**
1. [ ] Cross-entropy, KL divergence, perplexity — definitions & roles in LLMs
2. [ ] Bias–variance trade-off; overfitting in fine-tuning
3. [ ] Precision vs recall; when each matters for AI features
4. [ ] How BPE tokenization works
5. [ ] Why token counts differ across languages
6. [ ] Self-attention step by step; why √d_k
7. [ ] Multi-head attention purpose
8. [ ] Encoder vs decoder vs encoder-decoder
9. [ ] RoPE & context extension
10. [ ] MQA/GQA/MLA
11. [ ] KV cache & its memory cost
12. [ ] FlashAttention idea
13. [ ] Mixture of Experts
14. [ ] Scaling laws & Chinchilla
15. [ ] Pre-training → SFT → RLHF/DPO pipeline
16. [ ] RLHF vs DPO
17. [ ] Reasoning models & GRPO/verifiable rewards
18. [ ] Causes of hallucination
19. [ ] Lost in the middle & context rot
20. [ ] Model selection criteria

**APIs, Prompting & Context**
21. [ ] Temperature vs top-p vs top-k
22. [ ] Structured outputs & JSON schema enforcement
23. [ ] Tool/function calling flow
24. [ ] Prompt caching & cache-friendly prompt design
25. [ ] Batch APIs use cases
26. [ ] Handling rate limits at scale
27. [ ] Few-shot vs fine-tuning
28. [ ] Chain-of-thought vs native reasoning models
29. [ ] Prompt chaining & decomposition
30. [ ] Context engineering techniques
31. [ ] Prompt versioning & management
32. [ ] DSPy — what problem it solves

**Embeddings, Retrieval & RAG**
33. [ ] How embedding models are trained (contrastive learning)
34. [ ] Bi-encoder vs cross-encoder
35. [ ] HNSW parameters & trade-offs
36. [ ] IVF/PQ & quantized vectors
37. [ ] Hybrid search & RRF
38. [ ] Choosing a vector DB; pgvector limits
39. [ ] Metadata filtering & multi-tenancy
40. [ ] RAG pipeline end to end
41. [ ] Chunking strategies & chunk size trade-offs
42. [ ] Contextual retrieval
43. [ ] Query rewriting, HyDE, multi-query
44. [ ] Reranking — why and how
45. [ ] Permission-aware retrieval
46. [ ] Index freshness & deletes
47. [ ] GraphRAG — when it helps
48. [ ] Text-to-SQL pitfalls
49. [ ] RAG evaluation metrics
50. [ ] Debugging a failing RAG system
51. [ ] RAG vs fine-tuning vs long context

**Agents & MCP**
52. [ ] Workflow vs agent
53. [ ] Anthropic's agentic workflow patterns
54. [ ] Designing good tools
55. [ ] Agent memory types
56. [ ] Preventing loops & runaway costs
57. [ ] Human-in-the-loop design
58. [ ] Single vs multi-agent trade-offs
59. [ ] Evaluating agents (trajectory vs outcome)
60. [ ] What MCP is & the problem it solves
61. [ ] MCP hosts, clients, servers
62. [ ] Tools vs resources vs prompts
63. [ ] Sampling, roots, elicitation
64. [ ] stdio vs Streamable HTTP
65. [ ] MCP authorization (OAuth 2.1, resource indicators, no token passthrough)
66. [ ] MCP security risks (tool poisoning, rug pulls, injection)
67. [ ] MCP vs A2A vs function calling
68. [ ] Frameworks vs plain code for agents

**Fine-Tuning & Inference**
69. [ ] When to fine-tune
70. [ ] LoRA & QLoRA mechanics
71. [ ] Fine-tuning data preparation & chat templates
72. [ ] Catastrophic forgetting
73. [ ] Distillation
74. [ ] Prefill vs decode
75. [ ] TTFT, TPOT, throughput
76. [ ] Continuous batching & PagedAttention
77. [ ] Quantization options & validation
78. [ ] Speculative decoding
79. [ ] GPU memory sizing for serving
80. [ ] vLLM vs SGLang vs TensorRT-LLM vs Ollama
81. [ ] Autoscaling inference
82. [ ] Self-host vs API economics

**Evals, Safety & Ops**
83. [ ] Eval-driven development
84. [ ] Error analysis process
85. [ ] LLM-as-judge biases & calibration
86. [ ] Building golden datasets
87. [ ] Online evaluation & A/B testing
88. [ ] OWASP Top 10 for LLM apps
89. [ ] Direct vs indirect prompt injection defenses
90. [ ] The lethal trifecta
91. [ ] PII protection in LLM pipelines
92. [ ] Guardrail frameworks
93. [ ] LLM observability & tracing
94. [ ] Cost reduction levers
95. [ ] Semantic caching risks
96. [ ] Handling model deprecations/upgrades
97. [ ] EU AI Act basics

**Design & Leadership**
98. [ ] Design an enterprise RAG assistant with ACLs
99. [ ] Design an LLM gateway
100. [ ] A GenAI launch decision you made (or blocked) and why

---

## 36. 12-Week Preparation Plan

### Daily Template (≈ 8–9 focused hours, 6 days/week)
| Block | Time | Activity |
|-------|------|----------|
| Morning | 2 h | **Coding** — DSA (2 problems) or ML-from-scratch implementation (alternate) |
| Late morning | 2.5 h | **Core GenAI topic of the week** — read docs/papers, take notes |
| Afternoon | 2 h | **Build** — portfolio project increment (RAG → evals → agent → MCP → fine-tune) |
| Evening | 1.5 h | **GenAI system design** (alternate with classic design / behavioral) |
| End of day | 15 min | Update checklist; Anki review; skim one paper/blog |

### Week-by-Week
| Week | Core Topic | Build / Coding | Design / Behavioral |
|------|------------|----------------|---------------------|
| **1** | Math/ML refresh, NLP & tokenization (§1–3) | Softmax, cross-entropy, BPE tokenizer; DSA arrays/hashing | GenAI design framework (§25); resume & intro pitch |
| **2** | Transformers deep (§4) | Attention & transformer block from scratch; DSA two pointers/windows | Story candidate list; estimation practice |
| **3** | Training lifecycle & model landscape (§5–6) | Tiny GPT generation loop with sampling & KV cache | 5 STAR stories |
| **4** | LLM APIs, structured outputs, prompting & context engineering (§7–8) | Async batched LLM client with retries & rate limiting; structured extraction | Customer support chatbot design; target list & referrals |
| **5** | Embeddings & vector search (§9) | Hybrid search + RRF + reranker; vector index benchmarks | Semantic search design; **start applying** |
| **6** | RAG deep (§10) | **Portfolio #1: production-style RAG + eval suite** | Enterprise RAG with ACLs design; project deep-dive #1 |
| **7** | Agents (§11) & frameworks (§13) | ReAct agent from scratch; LangGraph version | Deep research agent design; mocks start |
| **8** | **MCP deep** (§12) | **Portfolio #2: MCP server + agent with guardrails & tracing** | Agent platform with MCP design; project deep-dive #2 |
| **9** | Evals (§17) & guardrails/security (§18) | LLM-as-judge evaluator calibrated vs human labels; red-team your agent | LLM gateway & guardrail service designs; behavioral mocks |
| **10** | Fine-tuning (§15) | **Portfolio #3: QLoRA fine-tune vs prompt baseline with evals** | Fine-tuning platform design; apply to dream tier |
| **11** | Inference & serving (§16), LLMOps (§19), responsible AI (§20) | Serve a model with vLLM; load-test TTFT/throughput | Inference platform & voice agent designs; negotiation prep |
| **12** | Rapid-fire 100 & revision; latest releases review | Mock coding rounds | Final mocks; rest |

### Throughout
- [ ] 10+ mocks (coding ×3, GenAI system design ×4, ML fundamentals ×2, behavioral ×1+)
- [ ] Stay current: weekly scan of major model releases, MCP spec changelog, framework release notes — but prioritize fundamentals over news

---

## 37. Resources

### Books
- [ ] **AI Engineering** — Chip Huyen (the core book for this role)
- [ ] **Designing Machine Learning Systems** — Chip Huyen
- [ ] **Hands-On Large Language Models** — Jay Alammar & Maarten Grootendorst
- [ ] **Build a Large Language Model (From Scratch)** — Sebastian Raschka
- [ ] **LLM Engineer's Handbook** — Iusztin & Labonne
- [ ] **Prompt Engineering for LLMs** — Berryman & Ziegler
- [ ] **Natural Language Processing with Transformers** — Tunstall, von Werra & Wolf
- [ ] **Deep Learning** — Goodfellow et al.; **Dive into Deep Learning** (free online); **Understanding Deep Learning** — Simon Prince (free)
- [ ] **Designing Data-Intensive Applications** — Kleppmann (engineering foundation)
- [ ] **The Staff Engineer's Path** — Tanya Reilly

### Key Papers (know the core idea of each)
- [ ] Attention Is All You Need (2017) · BERT · GPT-2/GPT-3 (few-shot learners) · Scaling Laws (Kaplan) · **Chinchilla** · InstructGPT (RLHF) · **Constitutional AI** · **DPO** · **LoRA** · **QLoRA** · **RAG** (Lewis et al., 2020) · Dense Passage Retrieval · ColBERT · **ReAct** · Toolformer · Chain-of-Thought prompting · Self-Consistency · **Lost in the Middle** · **FlashAttention** · **PagedAttention (vLLM)** · Speculative Decoding · Mixtral / Switch Transformer (MoE) · Llama 2/3 technical reports · **DeepSeek-V3 & DeepSeek-R1** · Judging LLM-as-a-Judge (MT-Bench) · Self-RAG · GraphRAG · Prompt injection literature (indirect injection, CaMeL) · Sentence-BERT · HNSW

### Courses & Online
- [ ] **Andrej Karpathy — Neural Networks: Zero to Hero** (build GPT from scratch), "Intro to LLMs", "Deep Dive into LLMs"
- [ ] **Hugging Face courses** (LLM, Agents, MCP), **DeepLearning.AI short courses** (RAG, agents, evals, MCP), **fast.ai**, **Stanford CS224N** (NLP), **CS336** (LLMs from scratch), **CS25** (Transformers United)
- [ ] **Official docs** — Anthropic (prompt engineering, tool use, "Building effective agents", context engineering, contextual retrieval posts), OpenAI Cookbook, Google Gemini docs, **modelcontextprotocol.io** (spec, SDKs, security best practices), vLLM/SGLang docs, LangGraph/LlamaIndex docs
- [ ] **Blogs/newsletters** — Lilian Weng, Eugene Yan, **Hamel Husain** (evals), Shreya Shankar, Simon Willison (security, prompt injection), Jay Alammar (illustrated transformer), Sebastian Raschka (Ahead of AI), Chip Huyen, Latent Space podcast, Interconnects (Nathan Lambert), The Batch
- [ ] **Practice** — LeetCode/NeetCode (DSA), Deep-ML (ML coding problems), Kaggle (applied ML), building & shipping your own projects

---

## 38. Final Readiness Checklist

### Interview Readiness
- [ ] Can explain transformers, attention, KV cache, tokenization, and the training pipeline from first principles
- [ ] Can implement attention, sampling, BPE, cosine top-k, BM25, and RRF from scratch
- [ ] Can design and defend a production RAG system with ACLs, evals, and freshness handling
- [ ] Can design agents with good tools, safety controls, and evaluation; can explain workflows vs agents
- [ ] Can explain MCP architecture, primitives, transports, authorization, and security risks — and have built a server
- [ ] Can explain fine-tuning (LoRA/QLoRA/DPO) and when to use it; inference optimization and GPU sizing
- [ ] Have an evals story: error analysis, golden sets, calibrated LLM judges, CI gates
- [ ] 2–3 portfolio projects with READMEs, diagrams, and eval results
- [ ] 15+ GenAI system designs practiced aloud with token/cost estimation
- [ ] 15–20 STAR stories; confident intro and career-break narrative
- [ ] Rapid-fire 100 answered aloud; 10+ mocks completed

### Production-Ready GenAI Feature Checklist (great interview answer too)
- [ ] **Quality** — success criteria defined; golden dataset; offline evals passing thresholds; calibrated LLM judges; human review of samples; regression evals in CI
- [ ] **Grounding** — retrieval with citations, abstention when unsupported, permission-aware retrieval, fresh index
- [ ] **Safety & security** — prompt injection defenses (architecture + classifiers), output sanitization, least-privilege tools, human approval for risky actions, PII redaction, abuse rate limits, red-teamed
- [ ] **Reliability** — timeouts, retries with jitter, fallback models/providers, circuit breakers, idempotent tool actions, graceful degradation
- [ ] **Performance & cost** — streaming, latency SLOs (TTFT/total), caching (prompt/semantic), model routing, token budgets, cost per request tracked and within budget
- [ ] **Observability** — full traces (prompts, tools, retrieval, tokens, cost), dashboards, alerts, user feedback capture
- [ ] **Change management** — pinned model versions, versioned prompts/configs, shadow/canary rollout, rollback plan, model-upgrade regression process
- [ ] **Governance** — data retention & residency honored, provider agreements (ZDR), audit logs, documentation of limitations, compliance review (e.g., EU AI Act classification)

---

> **Final advice:** Senior GenAI interviews reward candidates who combine **first-principles understanding** (transformers, retrieval, inference) with **production judgment** (evals, safety, cost, reliability) and **honesty about limitations**. For every topic, be ready to explain **what**, **how it works**, **when to use / not use**, **trade-offs**, and **a real system you built and measured**.
