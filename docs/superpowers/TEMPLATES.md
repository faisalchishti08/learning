# Tutorial Templates & Writing Guide

Read this file before authoring any tutorial. Read **two** things: (1) the *Global
writing rules* below — they apply to every page; (2) the one *stream playbook* that
matches the card you are writing for.

The build lint requires the same **7 top-level headings** on every page (this keeps
600+ existing pages valid). So every stream uses that fixed spine — but *what you put
inside each part* changes per stream. You may add `### ` sub-sections freely; the lint
only checks that the 7 `## ` headings are all present, in order.

The fixed spine (never rename, never drop, keep this order):

```
## 1. What it is
## 2. Why & when
## 3. Core concept
## 4. Diagram
## 5. Runnable example
## 6. Walkthrough
## 7. Gotchas & takeaways
```

Stream → playbook map (by card stem):

| Stem | Playbook |
|---|---|
| `data-structures` | Data Structures |
| `leetcode-patterns` | LeetCode Patterns |
| `system-design` | System Design |
| `microservices` | Microservices |
| `genai` | Generative AI (Python) |
| `java` | Java Language |
| `spring-*` (all) | Spring Frameworks |
| `webdev` | Web Development |

---

## Global writing rules (EVERY page, no exceptions)

The current biggest quality problem is writing that runs on, uses complicated English,
and is hard to follow. Fix it with these rules:

1. **One idea per sentence. Full stop after each.** Aim for 12–18 words. Hard cap ~25.
   If a sentence has two ideas joined by "and", "which", "so", or a comma splice, split
   it into two sentences.
2. **Active voice.** Write "the client sends the request", not "the request is sent".
3. **Simple, everyday words.** Prefer "use" over "utilise", "start" over "commence",
   "about" over "regarding". Write like you are explaining to a smart beginner.
4. **Expand every acronym on first use:** "Least Recently Used (LRU) cache". After that,
   the short form is fine.
5. **Define a term before you use it.** Never use jargon the reader has not met yet.
6. **Short paragraphs: 2–4 sentences.** One point per paragraph. Use lists for steps.
7. **Second person ("you").** Speak to the reader directly.
8. **Read every paragraph back.** If you stumble, the reader will too — rewrite it.
9. **Grammar and punctuation must be correct.** Proper capitalisation, correct commas,
   a full stop ending every sentence.

Before/after (do this):

> BEFORE (bad — run-on, complicated): "The dispatcher servlet which is the front
> controller receives the request and then it delegates to the handler mapping which
> finds the controller and then the controller which has the business logic returns a
> model and view that is then rendered so the response goes back."
>
> AFTER (good — simple, stops): "The DispatcherServlet is the front controller. It
> receives every request first. It asks the handler mapping which controller should
> handle the request. The controller runs the business logic. It returns a model and a
> view name. The view renders the final HTML. That HTML is sent back as the response."

---

## Common rules for parts 1, 2, 7 (all streams)

- **Part 1 — What it is:** 2–3 short paragraphs. Plain definition. One analogy if it
  helps. State where this fits in the bigger picture.
- **Part 2 — Why & when:** the problem it solves, when to reach for it, the main
  alternative. A short bullet list of concrete use-cases.
- **Part 7 — Gotchas & takeaways:** at least one `>` blockquote for a common mistake,
  then a bullet list of key takeaways.

Parts 3–6 are where streams differ. Each playbook below tells you how to fill them.

---

## Playbook: Data Structures  (stem `data-structures`, language Java)

**Learner goal:** picture the structure in memory, know its operations, and know the
cost of each operation.

- **Part 3 — Core concept:** describe the shape of the structure and its **invariants**
  (the rules that always hold, e.g. "a binary search tree keeps left < node < right").
  Explain how it is laid out in memory (array-backed vs node-and-pointer). Crucially,
  explain **how each invariant makes the operations fast** — for example, "because the
  tree stays sorted, search can throw away half the nodes at each step, which is why it
  is O(log n)". Connect the structure's rules to its performance so the reader understands
  the *algorithm*, not just the picture.
- **Part 4 — Diagram:** draw the structure with an inline `<svg>` (boxes for
  array slots or nodes, arrows for pointers). Show a real small instance, not an
  abstract shape. Label the parts.
- **Part 5 — Runnable example (Java):** a single `.java` file that builds the structure
  and exercises its operations. The 3 levels grow the SAME structure:
  - **Level 1 — Basic:** create it and do the core operation (insert / push / add).
  - **Level 2 — Intermediate:** add the rest of the operations (search, delete, traverse)
    and print results so the output is visible.
  - **Level 3 — Advanced:** a realistic variant — make it generic (`<T>`), handle
    resizing/balancing, or apply it to a small real problem.
- **Part 6 — Walkthrough:** pick ONE operation (e.g. insert) and **trace it step by
  step** on the diagram's instance. Show the structure after each step (an ASCII or
  `<svg>` "before → after" frame helps a lot). Then give a **complexity table**:

  | Operation | Time | Space | Why |
  |---|---|---|---|
  | Access | O(1) | O(1) | direct index |
  | Search | O(n) | O(1) | scan every element |

  Always include Big-O for time and space, and one line explaining each.

Skeleton for part 3–6: shape + invariants → structure diagram → build/operate/apply
Java → traced operation + complexity table.

---

## Playbook: LeetCode Patterns  (stem `leetcode-patterns`, language Java)

**Learner goal:** recognise which pattern a problem needs, and code the optimal
solution with correct complexity.

- **Part 2 — Why & when:** list the **recognition signals** — the words or shapes in a
  problem statement that hint at this pattern (e.g. "sorted array + pair that sums to
  target → two pointers").
- **Part 3 — Core concept:** explain the **algorithm/technique** properly, in three
  passes: (1) state the key idea in ONE sentence; (2) give the steps as a numbered list,
  each step one short sentence; (3) explain the **intuition and why it is correct** — why
  this approach works and why it never misses a valid answer (e.g. "the array is sorted,
  so if the sum is too small only a larger left value can help, therefore moving the left
  pointer right can never skip the answer"). The reader must understand *why*, not just
  memorise the moves. Also state the algorithm's time and space complexity here in one
  line, and why the brute-force approach is slower.
- **Part 4 — Diagram:** visualise the technique in action — two pointers moving toward
  each other, a window sliding, a recursion tree. Use `<svg>` or an ASCII frame.
- **Part 5 — Runnable example (Java):** ONE concrete problem, solved at 3 levels — this
  is the natural brute-force → optimal → hardened progression:
  - **Level 1 — Basic (brute force):** the obvious solution. State its complexity
    (usually O(n^2) or worse). This shows *why* we need the pattern.
  - **Level 2 — Intermediate (the pattern):** the optimal solution using the pattern.
    State the improved complexity (e.g. O(n)).
  - **Level 3 — Advanced (hardened / follow-up):** handle edge cases (empty input,
    duplicates, overflow) or a common follow-up variant of the problem.
  Each level is a runnable `main` that prints the result for a sample input.
- **Part 6 — Walkthrough:** **dry-run the optimal solution on one concrete input** as a
  trace table — one row per step, showing the pointers/window/variables changing:

  | Step | left | right | window sum | action |
  |---|---|---|---|---|
  | 1 | 0 | 0 | 4 | sum < target, move right |

  Then state the final **time and space complexity** and why.
- **Part 7:** include a short "**related problems**" bullet list (other problems that
  use the same pattern).

---

## Playbook: System Design  (stem `system-design`, language Java)

**Learner goal:** design a system step by step, justify each choice, and know the
trade-offs and bottlenecks.

- **Part 2 — Why & when:** frame the **use-case** and gather **requirements** — split
  into functional ("what it must do") and non-functional ("scale, latency,
  availability"). Add a rough **back-of-the-envelope estimate** (users, requests/sec,
  storage) when the topic is a full design.
- **Part 3 — Core concept:** explain the key idea or component (e.g. consistent hashing,
  a write-ahead log, CAP theorem) in plain language, from first principles.
- **Part 4 — Diagram:** an **architecture diagram** with `<svg>` — boxes for components
  (client, load balancer, service, cache, database, queue), arrows for data flow. For a
  flow, a **sequence diagram** (who calls whom, in order).
- **Part 5 — Runnable example (Java):** designs are conceptual, so make the example
  demonstrate the **key mechanism** as a small runnable `.java` file (e.g. a token-bucket
  rate limiter, an LRU cache, a consistent-hash ring). The 3 levels grow the DESIGN:
  - **Level 1 — Basic:** the naive single-server / in-memory version that works but does
    not scale. Draw its simple diagram.
  - **Level 2 — Intermediate:** scale it — add a cache, replicas, sharding, or a queue.
    Explain which bottleneck each addition removes. Update the diagram.
  - **Level 3 — Advanced:** production concerns — failure handling, consistency,
    hot-key/skew, monitoring. Show the final architecture.
- **Part 6 — Walkthrough:** trace **one end-to-end request** through the final
  architecture, in order — what each component does, and how the data changes as it
  passes through each layer. Then a **trade-offs table**:

  | Choice | Pro | Con | When to pick |
  |---|---|---|---|
  | SQL | strong consistency | harder to scale writes | financial data |

- **Part 7:** list the main **bottlenecks** and **trade-offs**, not just coding gotchas.

---

## Playbook: Microservices  (stem `microservices`, language Java)

**Learner goal:** understand a distributed pattern and how services interact under it.

- **Part 3 — Core concept:** explain the pattern and the distributed problem it solves
  (network calls fail, services scale independently, data is spread out).
- **Part 4 — Diagram:** a **service-interaction / sequence diagram** with `<svg>` —
  multiple services, the calls between them, and where the pattern sits (gateway, sidecar,
  circuit breaker, message broker).
- **Part 5 — Runnable example (Java):** the 3 levels grow the pattern:
  - **Level 1 — Basic:** the minimal pattern (e.g. a plain REST call, or a simple
    circuit-breaker state machine) as runnable Java.
  - **Level 2 — Intermediate:** add one production concern (retry, timeout, fallback,
    config).
  - **Level 3 — Advanced:** combine concerns as you would in production (e.g. retry +
    circuit breaker + bulkhead), or show the Spring Cloud / Resilience4j form.
- **Part 6 — Walkthrough:** trace **one request across services** in order. Show the
  **request and response** at each hop (method, URL, JSON body, status). Show how state
  changes at each service and what happens when a call fails.
- **Part 7:** distributed gotchas (retry storms, cascading failure, idempotency).

---

## Playbook: Generative AI  (stem `genai`, language **Python**)

**Learner goal:** understand the concept and run a small Python example against a modern
LLM workflow.

- **Part 3 — Core concept:** explain the idea plainly (tokens, embeddings, RAG,
  prompt templating, agents). Use an analogy for abstract ideas.
- **Part 4 — Diagram:** a **pipeline / data-flow diagram** with `<svg>` — the stages the
  data passes through (prompt → model → output; or document → chunk → embed → store →
  retrieve → answer for RAG).
- **Part 5 — Runnable example (Python):** runnable `.py`, run with `python3`. Keep it
  self-contained; if it needs a library, name the `pip install` in the "How to run" line
  and prefer standard tools. Use the **latest Claude models** when the example calls an
  LLM. The 3 levels grow the SAME pipeline:
  - **Level 1 — Basic:** the simplest working call or computation.
  - **Level 2 — Intermediate:** add one real concern (a prompt template, output parsing,
    batching, a retry).
  - **Level 3 — Advanced:** production shape (streaming, error handling, evaluation, or a
    small RAG loop).
- **Part 6 — Walkthrough:** trace the pipeline in order — the **input** (the prompt or
  data), what the model/step does, and the **output** at each stage, showing how the data
  transforms end to end.
- **Part 7:** GenAI-specific gotchas (hallucination, token limits, cost, prompt
  injection).

---

## Playbook: Java Language  (stem `java`, language Java)

**Learner goal:** understand a language feature — what it does, the syntax, and when to
use it — often comparing "before this feature" vs "with it".

- **Part 3 — Core concept:** explain the feature and the rule/behaviour precisely. If it
  replaces an older way, show the **before → after** contrast.
- **Part 4 — Diagram:** use `<svg>` where a picture helps (memory model, the JVM/class
  loading, generics bounds, a state change). If a topic is purely syntactic, a small
  labelled before/after code comparison in a fenced block is acceptable as the "diagram".
- **Part 5 — Runnable example (Java):** runnable `.java`, `java File.java`, JDK 17+.
  - **Level 1 — Basic:** the feature in its simplest use.
  - **Level 2 — Intermediate:** a realistic use with a real type/collection.
  - **Level 3 — Advanced:** an edge case, a combination with another feature, or a
    performance-aware use.
- **Part 6 — Walkthrough:** step through the example in execution order. Show what each
  line does and the **exact output**. If the feature changes state (collections, streams),
  show the value at each step.

---

## Playbook: Spring Frameworks  (stems `spring-*`, language Java)

**Learner goal:** use a Spring feature correctly — the annotation/API, the configuration,
and how a request flows through it.

- **Part 3 — Core concept:** explain the feature, the key annotations/beans, and how
  Spring wires it (auto-configuration, the bean lifecycle, the relevant abstraction).
- **Part 4 — Diagram:** a **layered flow diagram** with `<svg>` — the request path
  through the layers (Controller → Service → Repository → DB, or Filter → DispatcherServlet
  → Handler), or the bean/component relationships.
- **Part 5 — Runnable example (Java):** prefer a minimal, self-contained snippet. If a
  full Spring context is heavy, a focused `@Configuration`/`@Component` example or a small
  `main` that wires the pieces is fine — but it must compile and be explained as runnable.
  - **Level 1 — Basic:** the feature with default configuration.
  - **Level 2 — Intermediate:** realistic configuration (properties, a custom bean).
  - **Level 3 — Advanced:** a production concern (error handling, security, testing, a
    custom extension point).
- **Part 6 — Walkthrough:** trace **one request end to end through the layers**. Show the
  concrete **request** (method, URL, headers, JSON body) and **response** (status, headers,
  body). Show how the data changes at each layer: raw request → controller (DTO) → service
  (domain object) → repository (entity/row) → and back up to the response JSON.

---

## Playbook: Web Development  (stem `webdev`, language varies — HTML/JS/CSS/Node)

**Learner goal:** understand a web concept and see it run in a browser or Node.

Follow the gold-standard page `content/webdev/0001-clientserver-model.md`. Diagram in
part 4, one scenario growing through 3 levels in part 5, sequential end-to-end walkthrough
in part 6 (show request/response where relevant). Use the language natural to the topic
(HTML, CSS, JavaScript, or Node via `node file.js` — no installs).

---

## Reminder

Whatever the stream: keep the 7 headings, apply the Global writing rules, make the code
actually run, explain sequentially, and use diagrams wherever a picture beats words. The
goal is a page a beginner can read top-to-bottom and fully understand, with nothing left
unexplained.
