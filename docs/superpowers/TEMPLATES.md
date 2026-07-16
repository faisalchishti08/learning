# Tutorial Templates & Writing Guide

Read this before authoring any tutorial. The old version used one generic template for a
whole card. That is wrong: a "functional requirements" page and a "runnable algorithm"
page need completely different shapes. So you now do two things:

1. Apply the **Global writing rules** (every page).
2. **Classify the topic from its text**, then follow the matching **sub-template**.

## The fixed spine (lint requires these 7 headings, in this order, on every page)

```
## 1. What it is
## 2. Why & when
## 3. Core concept
## 4. Diagram
## 5. Runnable example
## 6. Walkthrough
## 7. Gotchas & takeaways
```

You may not rename or drop them (600+ existing pages depend on them). But **what goes
inside each part changes by topic type**, and you may add `### ` sub-sections freely.

**Part 5 holds the concrete ARTIFACT for the topic — it is not always code.** The lint only
needs one fenced ``` block there. Use the right artifact for the type and add a `### ` label
saying what it is:
- coding topic → runnable code (Java, or Python for genai);
- API-design facet → an API spec (```http or ```json);
- data-model facet → a schema (```sql DDL, or a JSON document shape);
- estimation facet → the worked calculation (```text);
- requirements facet → the requirement list / user stories (```text);
- architecture / scaling facet → a component list or config block (```text or ```yaml) plus
  the real diagram in Part 4.

---

## Global writing rules (EVERY page, no exceptions)

The biggest quality problem is writing that runs on and uses complicated English. Fix it:

1. **One idea per sentence. Full stop after each.** Aim 12–18 words, hard cap ~25. If a
   sentence joins two ideas with "and", "which", "so", or a comma splice, split it.
2. **Active voice.** "The client sends the request", not "the request is sent".
3. **Simple everyday words.** "use" not "utilise", "start" not "commence".
4. **Expand every acronym on first use:** "Queries Per Second (QPS)".
5. **Define a term before you use it.**
6. **Short paragraphs (2–4 sentences).** Use lists for steps.
7. **Second person ("you").**
8. **Read every paragraph back.** If you stumble, rewrite it.
9. **Correct grammar and punctuation.** A full stop ends every sentence.

Before → after:
> BAD (run-on): "The dispatcher servlet which is the front controller receives the request
> and then delegates to the handler mapping which finds the controller and returns a model
> and view that is rendered so the response goes back."
> GOOD: "The DispatcherServlet is the front controller. It receives every request first. It
> asks the handler mapping which controller should handle the request. The controller runs
> the business logic. It returns a model and a view name. The view renders the HTML. That
> HTML is sent back as the response."

Parts 1, 2, 7 are similar for all types: Part 1 = plain definition (+ analogy). Part 2 =
the problem it solves, when to use it, the alternative. Part 7 = a `>` gotcha + takeaways.
Parts 3–6 change by type, below.

---

## STEP A — classify the topic from its text, BEFORE writing

| If the topic text… | Type | Go to |
|---|---|---|
| matches "`<System> — <facet>`" (e.g. "URL Shortener — API design") | System-design **use-case facet** | §SD-FACET |
| is a standalone design concept/mechanism (e.g. "Token bucket", "Consistent hashing", "Latency numbers", "CAP theorem") on a `system-design` card | System-design **concept** | §SD-CONCEPT |
| ends with "`— signal: …`", "`— template: …`", or "`— complexity: …`" (leetcode) | LeetCode **pattern-meta** | §LC-META |
| is a named LeetCode problem (e.g. "Two Sum II", "LRU Cache") | LeetCode **problem** | §LC-PROBLEM |
| introduces a data structure (e.g. "Binary tree & BST", "Linked list") | DS **structure** | §DS-STRUCT |
| is an operation/concept on a structure (e.g. "BST insert / search / delete", "traversal") | DS **operation** | §DS-OP |
| is about `java.util` collections (section "Java Collections Framework") | DS **collections** | §DS-COLL |
| is a comparison / selection / cheat-sheet | DS **selection** | §DS-SELECT |
| is a `java` language feature | Java | §JAVA |
| is a `spring-*` feature | Spring | §SPRING |
| is a microservices pattern | Microservices | §MICRO |
| is a `genai` topic | GenAI (Python) | §GENAI |
| is a `webdev` topic | Web Dev | §WEBDEV |

---

## §SD-FACET — System Design, use-case facet

The card breaks each named system into facets. **Each page covers ONE facet of ONE
system. Do not redesign the whole system on every page.** In Parts 1–2, state which system
and which facet this is, in two or three sentences, and name the sibling facet pages that
cover the rest. Then go deep on THIS facet only. The "3-level example" does NOT apply here;
instead deliver the facet's artifact and reasoning. Use the row for the facet suffix:

| Facet suffix | Part 3 (Core concept) | Part 4 (Diagram) | Part 5 artifact (fenced) | Part 6 (Walkthrough) |
|---|---|---|---|---|
| functional requirements | the concrete things the system must do; prioritise them (must / should / could); say what is explicitly out of scope | a simple actor / use-case diagram | the requirements as a numbered list or user stories (```text) | take each requirement and explain what it implies for the design |
| non-functional requirements | the quality targets: scale, latency, availability, consistency, durability | a labelled table/quadrant `<svg>` | the NFRs as measurable targets, e.g. "p99 < 100 ms; 99.99% uptime; 1M QPS" (```text) | justify each number from the use-case; note the tension between targets |
| capacity estimation | the estimation method and the assumptions | — | the WORKED math (```text): daily users → QPS (avg & peak) → storage/day & 5-yr → bandwidth | derive every number step by step; show the arithmetic |
| API design | the endpoints, verbs, parameters, status codes, idempotency | a request→response sequence `<svg>` | the API spec (```http or ```json): each endpoint with a sample request and response body | walk each endpoint; show the concrete request and response; list error codes |
| high-level architecture | the components (client, LB, service, cache, DB, queue) and the request path | the architecture diagram `<svg>` (this is the star of the page) | a component list + key config as ```text (also keeps lint happy) | trace one request across every component, in order |
| data model & schema | the entities, relationships, keys, and indexes; SQL vs NoSQL choice | an entity-relationship `<svg>` | the schema: ```sql DDL, or the JSON document shape for NoSQL | explain each field, key, and index, and why |
| deep-dive: X | the one hard sub-problem (e.g. unique-key generation, collisions); the algorithm | an algorithm `<svg>` | runnable **Java** of the mechanism | trace the algorithm on a concrete input |
| scaling & tradeoffs | the bottlenecks and the moves that remove them (cache, shard, replicate, queue) | a before → after architecture `<svg>` | a tradeoff summary as ```text | each bottleneck → the fix → the new tradeoff it introduces |
| Spring/Java implementation approach | how you would build this in Spring Boot; the key beans/annotations | a layered flow `<svg>` (Controller→Service→Repo→DB) | runnable **Java** / a focused Spring snippet | trace one request through the layers; show request and response |

Always include at least one fenced ``` block in Part 5 so the build passes, even when the
main artifact is a diagram (add a component list or config block).

## §SD-CONCEPT — System Design, standalone concept/mechanism

For a technique, number, or model (Token bucket, Leaky bucket, Consistent hashing, CAP,
caching strategies, latency numbers). Here code fits, so the 3-level example applies.
- **Part 3:** explain the mechanism from first principles; how it works and why; state its
  time/space or its guarantees.
- **Part 4:** an `<svg>` of the mechanism (the bucket filling/draining, the hash ring).
- **Part 5 (runnable Java):** the mechanism in code, growing through 3 levels — Basic (the
  core mechanism), Intermediate (add one real concern, e.g. concurrency or refill), Advanced
  (production form, e.g. distributed via Redis, or thread-safe). Each level with "How to run".
- **Part 6:** trace the mechanism step by step on a concrete sequence of requests.
- **Part 7:** when to pick it over the alternatives; failure modes.

---

## §LC-META — LeetCode pattern-meta ("— signal / — template / — complexity")

These teach the PATTERN, not one problem. Keep them tight and practical.
- **Part 2:** the recognition signals — the exact words/shapes in a problem that point to
  this pattern.
- **Part 3:** the pattern's idea in one sentence, then the general steps, then WHY it works.
- **Part 4:** an `<svg>` of the technique (pointers converging, window sliding, DP table
  filling).
- **Part 5 (Java):** the **reusable template** for the pattern as runnable Java, with a tiny
  sample `main`. (Not three problems — one clean template.)
- **Part 6:** apply the template to one short example, tracing the variables.
- **Part 7:** the complexity, and a bullet list of problems that use this pattern.

## §LC-PROBLEM — LeetCode named problem

Give a real, submittable solution and teach the algorithm.
- **Part 1–2:** restate the problem in plain words; give a tiny input/output example; list the
  constraints; name the pattern it belongs to.
- **Part 3:** explain the algorithm properly — key idea in one sentence, numbered steps, then
  the intuition and why it is correct.
- **Part 4:** an `<svg>` showing the approach on a small input.
- **Part 5 (runnable Java), the 3-level algorithm progression:**
  - **Level 1 — Brute force:** the obvious solution; explain it; state its Big-O; show what
    work it wastes.
  - **KEY INSIGHT:** one paragraph naming the single realisation that removes the wasted work.
  - **Level 2 — Optimal:** the pattern solution; explain how it uses the insight; state the
    improved Big-O.
  - **Level 3 — Hardened:** edge cases (empty, duplicates, overflow) or a follow-up variant.
  Use the real LeetCode method signature (e.g. `public int[] twoSum(int[] nums, int target)`)
  plus a `main` that runs it on the sample, so `java File.java` works.
- **Part 6:** dry-run the optimal solution as a trace table (one row per step, variables
  changing). Then restate final time and space complexity.
- **Part 7:** common wrong turns + a "related problems" list.

---

## §DS-STRUCT — Data structure introduction

- **Part 3:** the structure's shape and its **invariants**; how it sits in memory
  (array-backed vs nodes+pointers); and **how each invariant makes operations fast** (e.g.
  "the BST stays sorted, so search discards half the nodes each step → O(log n)").
- **Part 4:** an `<svg>` of a real small instance, with labels and pointer arrows.
- **Part 5 (runnable Java), 3 levels:** Basic (build it + core op), Intermediate (all
  operations, printing results), Advanced (generic `<T>`, resizing/balancing, or applied).
- **Part 6:** trace ONE operation step by step with before→after frames; then a Big-O table
  (operation | time | space | why).

## §DS-OP — Data structure operation/concept

For a specific operation or idea (BST insert/delete, traversals, hashing collisions).
- **Part 3:** how the operation works and the invariant it must preserve.
- **Part 4:** an `<svg>` showing the operation transforming the structure.
- **Part 5 (runnable Java):** just this operation on a small structure, printing before/after.
  3 levels = the simple case → the tricky case (e.g. delete a node with two children) →
  the optimised/iterative form.
- **Part 6:** trace it step by step; state its Big-O and why.

## §DS-COLL — Java Collections Framework

For `java.util` types (ArrayList, HashMap, TreeMap, ArrayDeque).
- **Part 3:** what backs it, its ordering/complexity guarantees, and when to choose it.
- **Part 4:** an `<svg>` of its internal layout (buckets, resizing, tree-ification).
- **Part 5 (runnable Java):** real API usage — Basic (common methods), Intermediate (iteration,
  comparators, views), Advanced (a realistic task, e.g. frequency count, LRU via LinkedHashMap).
- **Part 6:** step through the code and outputs; note the Big-O of the methods used.

## §DS-SELECT — Comparison / selection / cheat-sheet

- **Part 3:** the decision criteria (ordering? duplicates? lookup vs scan? memory?).
- **Part 4:** a comparison `<svg>` or a decision tree.
- **Part 5:** a comparison **table** plus a tiny runnable Java snippet that demonstrates the
  key difference (```java, so lint passes).
- **Part 6:** walk the decision with 2–3 concrete "pick X because…" scenarios.

---

## §JAVA — Java language feature

- **Part 3:** the feature and its exact rule/behaviour; if it replaces an older way, show
  before → after.
- **Part 4:** an `<svg>` where a picture helps (memory, class loading, generics); else a small
  labelled before/after code block.
- **Part 5 (runnable Java), 3 levels:** Basic use → realistic use with a real type → advanced
  (edge case or combined with another feature). `java File.java`, JDK 17+.
- **Part 6:** step through in execution order; show the exact output and any state change.

## §SPRING — Spring framework feature

- **Part 3:** the feature, key annotations/beans, and how Spring wires it (auto-config,
  lifecycle, the abstraction).
- **Part 4:** a layered flow `<svg>`: Filter → DispatcherServlet → Controller → Service →
  Repository → DB, or the bean relationships.
- **Part 5 (runnable Java):** a minimal focused snippet (a `@Configuration`/`@Component` or a
  small `main` wiring the pieces). 3 levels: default config → realistic config (properties,
  custom bean) → production concern (error handling, security, testing).
- **Part 6:** trace ONE request end to end through the layers. Show the concrete request
  (method, URL, headers, JSON body) and response (status, headers, body). Show how the data
  changes at each layer: request → controller DTO → service domain object → repository entity
  → and back to the response JSON.

## §MICRO — Microservices pattern

- **Part 3:** the pattern and the distributed problem it solves.
- **Part 4:** a service-interaction / sequence `<svg>` across multiple services.
- **Part 5 (runnable Java), 3 levels:** minimal pattern → add one production concern (retry,
  timeout, fallback) → combine (retry + circuit breaker + bulkhead), or the Resilience4j /
  Spring Cloud form.
- **Part 6:** trace one request across services; show request/response at each hop and what
  happens when a call fails.

## §GENAI — Generative AI (Python)

- **Part 3:** the concept plainly (tokens, embeddings, RAG, agents), with an analogy.
- **Part 4:** a pipeline/data-flow `<svg>` (prompt → model → output; or doc → chunk → embed →
  store → retrieve → answer).
- **Part 5 (runnable Python, `python3`), 3 levels:** simplest call/computation → add one
  concern (prompt template, parsing, retry) → production form (streaming, error handling, a
  small RAG loop). Name any `pip install` in "How to run". Use the latest Claude models for LLM
  calls.
- **Part 6:** trace the pipeline in order — input, what each step does, output at each stage.

## §WEBDEV — Web Development

Follow the gold-standard page `content/webdev/0001-clientserver-model.md`: part-4 diagram,
one scenario growing through 3 levels in part 5, sequential end-to-end walkthrough in part 6
(show request/response where relevant). Use the language natural to the topic (HTML, CSS,
JavaScript, or Node via `node file.js`, no installs).

---

## Reminder

Classify first, then use the matching sub-template. Keep the 7 headings. Apply the Global
writing rules. Make Part 5's artifact the right kind for the topic. Explain sequentially, use
diagrams wherever a picture beats words, and leave nothing unexplained. The test: a beginner
can read the page top to bottom and fully understand it.
