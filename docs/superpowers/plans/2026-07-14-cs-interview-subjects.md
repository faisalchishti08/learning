# CS & Interview Prep Subjects — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add three generator-driven checklist subjects — System Design, Data Structures, LeetCode Patterns — with all microtopics enumerated and plugged into the existing UI (index cards + per-subject checklist pages + tutorial/manifest scaffolding). No tutorial content authored now.

**Architecture:** Each subject is a Python dict (`file/title/logo/cat/subtitle/sections[].groups[].items[]`) living in one new module `_build/data_cs.py`, registered in `_build/generate.py`'s `PROJECTS` loop. The existing pipeline (`shell.render`, `build_index`, `build_tutorials`, `manifest.build`) renders everything unchanged. Empty `content/<stem>/` = no tutorials built yet; the phase manifest auto-lists the new cards as `pending` for later content generation.

**Tech Stack:** Python 3 (stdlib only), `unittest`. Output is static HTML written into repo root by `python3 _build/generate.py`.

## Global Constraints

- New module: `_build/data_cs.py`, exporting `PROJECTS = [SYSTEM_DESIGN, DATA_STRUCTURES, LEETCODE]`.
- Project dict shape (exact keys): `{"file","title","logo","cat","subtitle","sections":[...]}`. Section shape: `{"name","tag","groups":[...]}`. Group shape: `{"g","items":[...]}`. `items` are plain strings (microtopic labels).
- `cat` for all three = `"CS & Interview Prep"` (exact string).
- Files/logos: System Design → `system-design.html` / `SD`; Data Structures → `data-structures.html` / `DS`; LeetCode Patterns → `leetcode-patterns.html` / `LC`.
- Index placement: `data_cs` inserted **after `data_webdev`, before `data_core`** in `generate.py`'s module tuple, so the category renders after "Web Development".
- Slugs (`topics.slugify`) truncate to 60 chars. **Slugs must be unique within each subject** — duplicate slugs would collide as tutorial filenames later. Tests enforce this.
- Section `name` convention (matches existing subjects): `"N. Title"` with a leading ordinal. `tag` is a short kebab/lowercase identifier, unique within a subject.
- Reproduce no copyrighted text: LeetCode items are problem **titles** only (public names), not problem statements.
- Do not modify existing subjects, `java.html`, or any `data_*.py` other than the new file + the 2-line `generate.py` edit.
- Run tests from repo root: `python3 -m pytest _build/tests/ -q` (or `python3 -m unittest discover -s _build/tests`).

---

### Task 1: Scaffold module, register in generator, structural invariant test

**Files:**
- Create: `_build/data_cs.py`
- Modify: `_build/generate.py` (import line + `PROJECTS` loop tuple)
- Test: `_build/tests/test_data_cs.py`

**Interfaces:**
- Produces: `data_cs.PROJECTS` — a list of exactly 3 project dicts (`SYSTEM_DESIGN`, `DATA_STRUCTURES`, `LEETCODE`). Later tasks fill each dict's `sections`.
- Consumes: existing `topics.enumerate_topics`, `topics.slugify`, `topics.card_stem`.

- [ ] **Step 1: Write the failing test** — `_build/tests/test_data_cs.py`

```python
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import data_cs, topics, generate

STEMS = ["system-design", "data-structures", "leetcode-patterns"]

def by_stem():
    return {topics.card_stem(p): p for p in data_cs.PROJECTS}

class TestMetadata(unittest.TestCase):
    def test_three_projects(self):
        self.assertEqual(len(data_cs.PROJECTS), 3)

    def test_files_and_logos(self):
        m = by_stem()
        self.assertEqual(set(m), set(STEMS))
        self.assertEqual(m["system-design"]["logo"], "SD")
        self.assertEqual(m["data-structures"]["logo"], "DS")
        self.assertEqual(m["leetcode-patterns"]["logo"], "LC")

    def test_category_is_cs_interview_prep(self):
        for p in data_cs.PROJECTS:
            self.assertEqual(p["cat"], "CS & Interview Prep")

    def test_required_keys_and_types(self):
        for p in data_cs.PROJECTS:
            for k in ("file", "title", "logo", "cat", "subtitle", "sections"):
                self.assertIn(k, p)
            self.assertIsInstance(p["sections"], list)

    def test_registered_in_generator_after_webdev_before_core(self):
        files = [p["file"] for p in generate.PROJECTS]
        self.assertIn("system-design.html", files)
        self.assertIn("data-structures.html", files)
        self.assertIn("leetcode-patterns.html", files)
        wd = files.index("webdev.html")
        sd = files.index("system-design.html")
        # first data_core file is spring-framework.html
        core = files.index("spring-framework.html")
        self.assertLess(wd, sd)
        self.assertLess(sd, core)

class TestStructuralInvariants(unittest.TestCase):
    """Runs for whatever sections exist; tightened as later tasks add content."""
    def test_items_are_nonempty_strings(self):
        for p in data_cs.PROJECTS:
            for s in p["sections"]:
                self.assertIsInstance(s["name"], str)
                for g in s["groups"]:
                    self.assertTrue(g["items"])
                    for it in g["items"]:
                        self.assertIsInstance(it, str)
                        self.assertTrue(it.strip())

    def test_section_tags_unique_per_subject(self):
        for p in data_cs.PROJECTS:
            tags = [s["tag"] for s in p["sections"]]
            self.assertEqual(len(tags), len(set(tags)), p["file"])

    def test_slugs_unique_per_subject(self):
        for p in data_cs.PROJECTS:
            if not p["sections"]:
                continue
            slugs = [t["slug"] for t in topics.enumerate_topics(p)]
            dupes = sorted({s for s in slugs if slugs.count(s) > 1})
            self.assertEqual(dupes, [], "%s dup slugs: %s" % (p["file"], dupes))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest _build/tests/test_data_cs.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'data_cs'`.

- [ ] **Step 3: Create `_build/data_cs.py` scaffold**

```python
# -*- coding: utf-8 -*-
"""CS & Interview Prep — System Design, Data Structures, LeetCode Patterns.

Generator-driven checklist subjects (same shape as data_microservices etc.).
Microtopics only; tutorial content generated later via the standard pipeline.
"""

SYSTEM_DESIGN = {
    "file": "system-design.html", "title": "System Design", "logo": "SD",
    "cat": "CS & Interview Prep",
    "subtitle": "Every micro-topic of system design — concepts (scaling, caching, data, "
                "consistency, messaging, resiliency) plus 29 end-to-end use-case designs — "
                "each mapped to how Java & Spring implement it.",
    "sections": [],
}

DATA_STRUCTURES = {
    "file": "data-structures.html", "title": "Data Structures", "logo": "DS",
    "cat": "CS & Interview Prep",
    "subtitle": "Every core data-structure concept in Java — arrays, lists, stacks, queues, "
                "hashing, trees, heaps, tries, graphs, advanced/range structures, union-find, "
                "and the Java Collections Framework — with operations, complexity & JDK classes.",
    "sections": [],
}

LEETCODE = {
    "file": "leetcode-patterns.html", "title": "LeetCode Patterns", "logo": "LC",
    "cat": "CS & Interview Prep",
    "subtitle": "Every coding-interview pattern with when to recognize it and the named "
                "LeetCode problems that drill it — two pointers, sliding window, BFS/DFS, "
                "backtracking, dynamic programming, graphs, and more.",
    "sections": [],
}

PROJECTS = [SYSTEM_DESIGN, DATA_STRUCTURES, LEETCODE]
```

- [ ] **Step 4: Register in `_build/generate.py`**

Edit the import line (add `, data_cs` at the end):

```python
import data_java, data_microservices, data_genai, data_webdev, data_core, data_data_cloud, data_security, data_messaging, data_web, data_apps, data_cs
```

Edit the `PROJECTS` loop tuple — insert `data_cs` after `data_webdev`, before `data_core`:

```python
for mod in (data_java, data_microservices, data_genai, data_webdev, data_cs, data_core, data_data_cloud, data_security, data_messaging, data_web, data_apps):
    PROJECTS.extend(mod.PROJECTS)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 -m pytest _build/tests/test_data_cs.py -q`
Expected: PASS (all metadata/registration tests green; structural tests trivially pass on empty sections).

- [ ] **Step 6: Commit**

```bash
git add _build/data_cs.py _build/generate.py _build/tests/test_data_cs.py
git commit -m "feat: scaffold CS & Interview Prep subjects + register in generator"
```

---

### Task 2: System Design — enumerate all sections

**Files:**
- Modify: `_build/data_cs.py` (`SYSTEM_DESIGN["sections"]`)
- Test: `_build/tests/test_data_cs.py` (add `TestSystemDesign`)

**Interfaces:**
- Consumes: `SYSTEM_DESIGN` scaffold from Task 1.
- Produces: `SYSTEM_DESIGN["sections"]` fully populated — 21 sections (20 concept + 1 use-case).

**Section plan (from spec).** Concept sections 1–20 use `tag`s like `fundamentals, networking, load-balancing, caching, sql, nosql, sharding, consistency, messaging, scalability, resiliency, rate-limiting, storage, search, coordination, security, observability, patterns, api-design, deployment`. Each concept section ends with a `"How Java/Spring implements this"` group where the spec marks `[+Spring]`. Section 21 `tag=use-cases`: **one group per use-case design** (29 designs from the spec), and **every design group has these 9 items in order**: `"<Design> — functional requirements"`, `"<Design> — non-functional requirements"`, `"<Design> — capacity estimation"`, `"<Design> — API design"`, `"<Design> — high-level architecture"`, `"<Design> — data model & schema"`, `"<Design> — deep-dive: <the key bottleneck>"`, `"<Design> — scaling & tradeoffs"`, `"<Design> — Spring/Java implementation approach"`.

- [ ] **Step 1: Write the failing test** — append to `_build/tests/test_data_cs.py`

```python
class TestSystemDesign(unittest.TestCase):
    def sd(self):
        return by_stem()["system-design"]

    def test_has_21_sections(self):
        self.assertEqual(len(self.sd()["sections"]), 21)

    def test_concept_and_usecase_tags_present(self):
        tags = [s["tag"] for s in self.sd()["sections"]]
        for t in ("fundamentals", "caching", "consistency", "resiliency",
                  "api-design", "use-cases"):
            self.assertIn(t, tags)

    def test_usecase_section_has_29_designs_each_9_steps(self):
        uc = [s for s in self.sd()["sections"] if s["tag"] == "use-cases"][0]
        self.assertEqual(len(uc["groups"]), 29)
        for g in uc["groups"]:
            self.assertEqual(len(g["items"]), 9)
            self.assertTrue(g["items"][-1].endswith("Spring/Java implementation approach"))

    def test_total_topic_count_floor(self):
        # 20 concept sections * multiple groups + 29*9 use-case items
        n = len(topics.enumerate_topics(self.sd()))
        self.assertGreaterEqual(n, 450)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest _build/tests/test_data_cs.py::TestSystemDesign -q`
Expected: FAIL (`len(sections)` is 0, not 21).

- [ ] **Step 3: Populate `SYSTEM_DESIGN["sections"]`**

Enumerate every microtopic for the 20 concept sections + the use-case section, following the spec's "Subject 1 — System Design" skeleton exhaustively. Format (this is the exact structure; fill all 21 sections the same way — sample shows two concept sections + one use-case group):

```python
SYSTEM_DESIGN["sections"] = [
    {"name": "1. Fundamentals & Estimation", "tag": "fundamentals", "groups": [
        {"g": "What & Why", "items": [
            "What system design is (and what interviewers assess)",
            "Functional vs non-functional requirements",
            "Requirements gathering & scoping the problem",
            "Constraints, assumptions & clarifying questions",
        ]},
        {"g": "Back-of-the-Envelope Estimation", "items": [
            "Powers of two & data-size units (KB/MB/GB/TB/PB)",
            "Latency numbers every engineer should know",
            "QPS estimation (average vs peak)",
            "Storage estimation (per-record & total)",
            "Bandwidth estimation (ingress/egress)",
            "Read:write ratio & its design impact",
        ]},
        {"g": "Targets & Tradeoffs", "items": [
            "SLA, SLO, SLI defined",
            "Availability math (nines & downtime budgets)",
            "Latency vs throughput tradeoffs",
            "Cost vs performance vs complexity tradeoffs",
        ]},
    ]},
    {"name": "2. Networking & Communication", "tag": "networking", "groups": [
        {"g": "Protocols", "items": [
            "DNS resolution & records",
            "IP, TCP vs UDP",
            "HTTP/1.1, HTTP/2, HTTP/3 (QUIC)",
            "TLS/SSL handshake basics",
        ]},
        {"g": "Communication Styles", "items": [
            "REST over HTTP",
            "RPC & gRPC",
            "WebSocket (full-duplex)",
            "Server-Sent Events (SSE)",
            "Long polling vs short polling",
            "Webhooks (server push callbacks)",
        ]},
        {"g": "How Java/Spring implements this", "items": [
            "RestClient / WebClient / RestTemplate for HTTP calls",
            "spring-grpc & Spring for gRPC",
            "Spring WebSocket & STOMP",
            "Server-Sent Events with Spring WebFlux",
        ]},
    ]},
    # ... sections 3–20 per spec, each ending with a
    # "How Java/Spring implements this" group where the spec marks [+Spring] ...
    {"name": "21. Use-Case Designs", "tag": "use-cases", "groups": [
        {"g": "Design a URL Shortener (TinyURL)", "items": [
            "URL Shortener — functional requirements",
            "URL Shortener — non-functional requirements",
            "URL Shortener — capacity estimation",
            "URL Shortener — API design",
            "URL Shortener — high-level architecture",
            "URL Shortener — data model & schema",
            "URL Shortener — deep-dive: unique key generation & collisions",
            "URL Shortener — scaling & tradeoffs",
            "URL Shortener — Spring/Java implementation approach",
        ]},
        # ... remaining 28 designs, same 9-item shape, from the spec list ...
    ]},
]
```

The 29 designs (spec order): URL Shortener · Rate Limiter · Pastebin · Web Crawler · Notification/Push · News Feed · Twitter · Chat (WhatsApp) · Typeahead · Search Engine · Video Streaming (YouTube) · Photo Sharing (Instagram) · Ride-Hailing (Uber) · Ticketing (Ticketmaster) · E-commerce & Inventory (Amazon) · Payment/Wallet · Distributed Cache · Key-Value Store (DynamoDB) · Message Queue (Kafka) · File Storage & Sync (Dropbox) · Distributed ID Generator · Leaderboard · Ad-Click Aggregator · Airbnb · Food Delivery (DoorDash) · Collaborative Editor (Google Docs) · Distributed Job Scheduler · Metrics & Monitoring · Recommendation System. Choose each design's `deep-dive` item to name that design's signature bottleneck (e.g. Chat → "fan-out & presence"; Uber → "geospatial indexing / QuadTree").

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest _build/tests/test_data_cs.py -q`
Expected: PASS (`TestSystemDesign` + slug-uniqueness invariant green). If slug dupes appear, disambiguate the offending labels.

- [ ] **Step 5: Commit**

```bash
git add _build/data_cs.py _build/tests/test_data_cs.py
git commit -m "feat: enumerate System Design microtopics (concepts + 29 use-case designs)"
```

---

### Task 3: Data Structures — enumerate all sections

**Files:**
- Modify: `_build/data_cs.py` (`DATA_STRUCTURES["sections"]`)
- Test: `_build/tests/test_data_cs.py` (add `TestDataStructures`)

**Interfaces:**
- Consumes: `DATA_STRUCTURES` scaffold from Task 1.
- Produces: `DATA_STRUCTURES["sections"]` — 16 sections per spec.

**Section plan (from spec).** 16 sections, `tag`s: `foundations, arrays, strings, linked-lists, stacks, queues, hashing, trees, heaps, tries, graphs, advanced-trees, union-find, probabilistic, jcf, cheatsheet`. Per-structure groups follow Concept / Operations & Complexity / Java implementation / Variants / Applications (adapt where a group doesn't apply).

- [ ] **Step 1: Write the failing test** — append to `_build/tests/test_data_cs.py`

```python
class TestDataStructures(unittest.TestCase):
    def ds(self):
        return by_stem()["data-structures"]

    def test_has_16_sections(self):
        self.assertEqual(len(self.ds()["sections"]), 16)

    def test_expected_tags_present(self):
        tags = [s["tag"] for s in self.ds()["sections"]]
        for t in ("foundations", "arrays", "linked-lists", "hashing", "trees",
                  "heaps", "tries", "graphs", "union-find", "jcf"):
            self.assertIn(t, tags)

    def test_java_implementation_group_common(self):
        # most structure sections carry a Java-implementation group
        hits = 0
        for s in self.ds()["sections"]:
            if any("Java" in g["g"] for g in s["groups"]):
                hits += 1
        self.assertGreaterEqual(hits, 8)

    def test_total_topic_count_floor(self):
        n = len(topics.enumerate_topics(self.ds()))
        self.assertGreaterEqual(n, 200)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest _build/tests/test_data_cs.py::TestDataStructures -q`
Expected: FAIL (0 sections).

- [ ] **Step 3: Populate `DATA_STRUCTURES["sections"]`**

Enumerate every microtopic for the 16 sections following the spec's "Subject 2 — Data Structures" skeleton exhaustively. Sample format (fill all 16 the same way):

```python
DATA_STRUCTURES["sections"] = [
    {"name": "1. Foundations", "tag": "foundations", "groups": [
        {"g": "Complexity Analysis", "items": [
            "Abstract data type vs data structure",
            "Big-O, Big-Theta, Big-Omega",
            "Best / average / worst case",
            "Amortized analysis (dynamic array doubling)",
            "Time vs space tradeoffs",
        ]},
        {"g": "Java Memory Model Basics", "items": [
            "Primitives vs references",
            "Stack vs heap allocation",
            "Autoboxing / unboxing & its cost",
            "Arrays as objects in the JVM",
        ]},
    ]},
    {"name": "4. Linked Lists", "tag": "linked-lists", "groups": [
        {"g": "Concept", "items": [
            "Singly linked list",
            "Doubly linked list",
            "Circular linked list",
            "Sentinel / dummy nodes",
        ]},
        {"g": "Operations & Complexity", "items": [
            "Insert at head / tail / middle",
            "Delete by node / by value",
            "Search & traversal",
            "Reverse a linked list (iterative & recursive)",
            "Cycle detection (Floyd's)",
        ]},
        {"g": "Java implementation", "items": [
            "java.util.LinkedList (Deque + List)",
            "Building a custom node class",
            "LinkedList vs ArrayList tradeoffs",
        ]},
    ]},
    # ... sections 2,3,5–16 per spec (strings, stacks, queues, hashing, trees,
    #     heaps, tries, graphs, advanced-trees, union-find, probabilistic, jcf,
    #     cheatsheet) ...
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest _build/tests/test_data_cs.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add _build/data_cs.py _build/tests/test_data_cs.py
git commit -m "feat: enumerate Data Structures microtopics (Java-based, 16 sections)"
```

---

### Task 4: LeetCode Patterns — enumerate all patterns + named problems

**Files:**
- Modify: `_build/data_cs.py` (`LEETCODE["sections"]`)
- Test: `_build/tests/test_data_cs.py` (add `TestLeetCode`)

**Interfaces:**
- Consumes: `LEETCODE` scaffold from Task 1.
- Produces: `LEETCODE["sections"]` — one section per pattern (~37), each with a concept group + problem groups.

**Section plan (from spec).** ~37 pattern sections. Each section: group 1 `"Pattern & when to use"` (concept items — signal/template/complexity), then groups named by difficulty (`"Easy"`, `"Medium"`, `"Hard"`) whose items are **named LeetCode problem titles**. Target ≥8 problem items per pattern; ~800+ problem items total. Patterns list from spec (assign short unique `tag`s: `two-pointers, sliding-window, fast-slow, merge-intervals, cyclic-sort, ll-reversal, tree-bfs, tree-dfs, graph-traversal, islands, two-heaps, subsets, mod-binary-search, bit-xor, top-k, k-way-merge, backtracking, dp-01-knapsack, dp-unbounded-knapsack, dp-fibonacci, dp-lcs, dp-palindrome, dp-lis, dp-grid, dp-interval, dp-state-machine, greedy, monotonic-stack, prefix-sum, trie, union-find, topo-sort, shortest-path, segment-tree, design, math-geometry`).

- [ ] **Step 1: Write the failing test** — append to `_build/tests/test_data_cs.py`

```python
class TestLeetCode(unittest.TestCase):
    def lc(self):
        return by_stem()["leetcode-patterns"]

    def test_min_pattern_count(self):
        self.assertGreaterEqual(len(self.lc()["sections"]), 35)

    def test_expected_tags_present(self):
        tags = [s["tag"] for s in self.lc()["sections"]]
        for t in ("two-pointers", "sliding-window", "backtracking",
                  "dp-01-knapsack", "topo-sort", "trie"):
            self.assertIn(t, tags)

    def test_each_pattern_has_concept_group_and_problems(self):
        for s in self.lc()["sections"]:
            names = [g["g"].lower() for g in s["groups"]]
            self.assertTrue(any("pattern" in n or "when" in n for n in names),
                            "%s missing concept group" % s["tag"])
            problem_items = sum(len(g["items"]) for g in s["groups"]
                                if "pattern" not in g["g"].lower()
                                and "when" not in g["g"].lower())
            self.assertGreaterEqual(problem_items, 8, "%s < 8 problems" % s["tag"])

    def test_total_problem_count_floor(self):
        n = len(topics.enumerate_topics(self.lc()))
        self.assertGreaterEqual(n, 700)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest _build/tests/test_data_cs.py::TestLeetCode -q`
Expected: FAIL (0 sections).

- [ ] **Step 3: Populate `LEETCODE["sections"]`**

Enumerate every pattern with its named problems following the spec's "Subject 3 — LeetCode Patterns" list exhaustively. Sample format (fill all ~37 patterns the same way):

```python
LEETCODE["sections"] = [
    {"name": "1. Two Pointers", "tag": "two-pointers", "groups": [
        {"g": "Pattern & when to use", "items": [
            "Signal: sorted array / pair-sum / in-place partition",
            "Template: opposite-ends vs same-direction pointers",
            "Typical complexity: O(n) time, O(1) space",
        ]},
        {"g": "Easy", "items": [
            "Two Sum II - Input Array Is Sorted",
            "Valid Palindrome",
            "Remove Duplicates from Sorted Array",
            "Merge Sorted Array",
            "Squares of a Sorted Array",
        ]},
        {"g": "Medium", "items": [
            "3Sum",
            "3Sum Closest",
            "Container With Most Water",
            "Sort Colors",
            "Remove Nth Node From End of List",
        ]},
        {"g": "Hard", "items": [
            "Trapping Rain Water",
        ]},
    ]},
    # ... remaining ~36 patterns per spec, each: concept group + difficulty groups
    #     of named LeetCode problems (>=8 problems per pattern) ...
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest _build/tests/test_data_cs.py -q`
Expected: PASS. If slug-uniqueness fails on similarly-named problems (e.g. two "House Robber" variants truncating equal), keep the official distinct titles — they differ within 60 chars.

- [ ] **Step 5: Commit**

```bash
git add _build/data_cs.py _build/tests/test_data_cs.py
git commit -m "feat: enumerate LeetCode Patterns (~37 patterns, named problems as items)"
```

---

### Task 5: Generate output, verify UI wiring, commit built artifacts

**Files:**
- Regenerate (write): `index.html`, `system-design.html`, `data-structures.html`, `leetcode-patterns.html`, `content/_manifest.json`
- Test: `_build/tests/test_data_cs.py` (add `TestGeneratedOutput`)

**Interfaces:**
- Consumes: fully populated `data_cs.PROJECTS` (Tasks 2–4) and the registered generator (Task 1).

- [ ] **Step 1: Run the full generator**

Run: `python3 _build/generate.py`
Expected: exit 0; output lists `system-design.html`, `data-structures.html`, `leetcode-patterns.html` with their topic counts; no "Tutorial lint failed" (no `.md` content exists yet).

- [ ] **Step 2: Write the verification test** — append to `_build/tests/test_data_cs.py`

```python
class TestGeneratedOutput(unittest.TestCase):
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    def read(self, name):
        with open(os.path.join(self.ROOT, name), encoding="utf-8") as f:
            return f.read()

    def test_subject_pages_exist_and_titled(self):
        self.assertIn("System Design", self.read("system-design.html"))
        self.assertIn("Data Structures", self.read("data-structures.html"))
        self.assertIn("LeetCode Patterns", self.read("leetcode-patterns.html"))

    def test_index_has_category_and_three_cards(self):
        idx = self.read("index.html")
        self.assertIn("CS &amp; Interview Prep", idx.replace("&", "&amp;")
                      if "CS & Interview Prep" not in idx else idx)
        self.assertIn('href="system-design.html"', idx)
        self.assertIn('href="data-structures.html"', idx)
        self.assertIn('href="leetcode-patterns.html"', idx)

    def test_manifest_lists_new_cards(self):
        import json
        man = json.loads(self.read("content/_manifest.json"))
        for stem in ("system-design", "data-structures", "leetcode-patterns"):
            self.assertIn(stem, man["cards"])
```

Note on the index category assertion: `build_index` emits the raw `cat` string `CS & Interview Prep` (no HTML-escaping in the generator). Simplify the assertion to `self.assertIn("CS & Interview Prep", idx)` and drop the conditional if the raw string is present — verify by grepping the generated `index.html` first.

- [ ] **Step 3: Run tests to verify they pass**

Run: `python3 -m pytest _build/tests/ -q`
Expected: PASS (full suite — new subject tests + existing tests all green).

- [ ] **Step 4: Manual spot-check**

Open `index.html` in a browser: confirm a "CS & Interview Prep" category appears after "Web Development" with three cards (`SD`/`DS`/`LC`) showing topic counts. Click each → checklist page renders sections, groups, items; ticking a checkbox persists on reload (localStorage per file).

- [ ] **Step 5: Commit generated artifacts**

```bash
git add index.html system-design.html data-structures.html leetcode-patterns.html content/_manifest.json _build/tests/test_data_cs.py
git commit -m "feat: build CS & Interview Prep subject pages + index cards + manifest"
```

---

## Self-Review

**Spec coverage:**
- System Design concepts (20 sections) + 29 use-case designs → Task 2. ✓
- Data Structures (16 sections, Java-based) → Task 3. ✓
- LeetCode Patterns (~37, named problems) → Task 4. ✓
- New index category after Web Development → Task 1 (registration order) + Task 5 (verify). ✓
- Tutorial/manifest scaffolding auto-picks up new cards → Task 5 manifest test. ✓
- No tutorial content authored → no `content/<stem>/*.md` created; build tolerates absence. ✓
- Slug-uniqueness risk from spec → enforced by `test_slugs_unique_per_subject` (Task 1). ✓

**Placeholder scan:** Item-level enumeration is intentionally delegated to Tasks 2–4 with exact structural rules, count floors, and worked format samples — not "TODO". Tests fail if a subject is under-populated. No `add error handling`-style hand-waving (this is static data, no runtime error paths).

**Type consistency:** Dict keys (`file/title/logo/cat/subtitle/sections/name/tag/groups/g/items`) match `topics.enumerate_topics`, `shell.render`, and `manifest.build` usage verbatim. `card_stem` derives stems (`system-design` etc.) from `file` — tests reference the same stems.
