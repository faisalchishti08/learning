# -*- coding: utf-8 -*-
"""CS & Interview Prep — System Design, Data Structures, LeetCode Patterns.

Generator-driven checklist subjects (same shape as data_microservices etc.).
Microtopics only; tutorial content generated later via the standard pipeline.
"""


def _design(name, bottleneck):
    """One use-case-design group: the 9 standard design steps for `name`."""
    return {"g": "Design %s" % name, "items": [
        "%s — functional requirements" % name,
        "%s — non-functional requirements" % name,
        "%s — capacity estimation" % name,
        "%s — API design" % name,
        "%s — high-level architecture" % name,
        "%s — data model & schema" % name,
        "%s — deep-dive: %s" % (name, bottleneck),
        "%s — scaling & tradeoffs" % name,
        "%s — Spring/Java implementation approach" % name,
    ]}


def _pat(num, name, tag, signal, template, complexity,
         easy=None, medium=None, hard=None):
    """One LeetCode-pattern section: a concept group + named-problem groups.

    Concept items are name-prefixed so their slugs stay unique across the subject.
    """
    groups = [{"g": "Pattern & when to use", "items": [
        "%s — signal: %s" % (name, signal),
        "%s — template: %s" % (name, template),
        "%s — complexity: %s" % (name, complexity),
    ]}]
    for label, probs in (("Easy", easy), ("Medium", medium), ("Hard", hard)):
        if probs:
            groups.append({"g": label, "items": list(probs)})
    return {"name": "%d. %s" % (num, name), "tag": tag, "groups": groups}


SYSTEM_DESIGN = {
    "file": "system-design.html", "title": "System Design", "logo": "SD",
    "cat": "CS & Interview Prep",
    "subtitle": "Every micro-topic of system design — concepts (scaling, caching, data, "
                "consistency, messaging, resiliency) plus 29 end-to-end use-case designs — "
                "each mapped to how Java & Spring implement it.",
    "sections": [

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
            "The design interview framework (steps & timeboxing)",
        ]},
    ]},

    {"name": "2. Networking & Communication", "tag": "networking", "groups": [
        {"g": "Protocols", "items": [
            "DNS resolution & record types",
            "IP addressing, TCP vs UDP",
            "HTTP/1.1, HTTP/2, HTTP/3 (QUIC)",
            "TLS/SSL handshake basics",
            "Keep-alive & connection pooling",
        ]},
        {"g": "Communication Styles", "items": [
            "REST over HTTP",
            "RPC & gRPC (Protobuf)",
            "WebSocket (full-duplex)",
            "Server-Sent Events (SSE)",
            "Long polling vs short polling",
            "Webhooks (server-push callbacks)",
            "Synchronous vs asynchronous communication",
        ]},
        {"g": "How Java/Spring implements this", "items": [
            "RestClient / WebClient / RestTemplate for HTTP calls",
            "Spring gRPC for RPC services",
            "Spring WebSocket & STOMP messaging",
            "Server-Sent Events with Spring WebFlux",
        ]},
    ]},

    {"name": "3. Load Balancing & Reverse Proxy", "tag": "load-balancing", "groups": [
        {"g": "Concepts", "items": [
            "Why load balance (scale & availability)",
            "L4 (transport) vs L7 (application) load balancing",
            "Reverse proxy vs forward proxy",
            "API gateway role at the edge",
            "Global server load balancing (GeoDNS / anycast)",
        ]},
        {"g": "Algorithms & Health", "items": [
            "Round-robin & weighted round-robin",
            "Least connections / least response time",
            "IP-hash & consistent-hash routing",
            "Sticky sessions (session affinity)",
            "Health checks & passive failure detection",
        ]},
        {"g": "How Java/Spring implements this", "items": [
            "Spring Cloud Gateway as the edge gateway",
            "Spring Cloud LoadBalancer for client-side balancing",
            "Service discovery integration (Eureka / Consul)",
        ]},
    ]},

    {"name": "4. Caching & CDN", "tag": "caching", "groups": [
        {"g": "Caching Patterns", "items": [
            "Cache-aside (lazy loading)",
            "Read-through cache",
            "Write-through cache",
            "Write-back (write-behind) cache",
            "Refresh-ahead cache",
        ]},
        {"g": "Cache Mechanics", "items": [
            "Eviction policies (LRU, LFU, FIFO, TTL)",
            "Cache invalidation strategies",
            "Hot keys & key distribution",
            "Thundering herd / cache stampede & mitigation",
            "Cache consistency & staleness",
            "Client / CDN / application / database cache layers",
        ]},
        {"g": "CDN", "items": [
            "How a CDN works (edge PoPs)",
            "Push vs pull CDN",
            "Cache-Control, ETag & conditional requests",
        ]},
        {"g": "How Java/Spring implements this", "items": [
            "Spring Cache abstraction (@Cacheable / @CacheEvict)",
            "Redis / Memcached as a cache provider",
            "Spring Data Redis for distributed caching",
        ]},
    ]},

    {"name": "5. SQL Databases", "tag": "sql", "groups": [
        {"g": "Relational Model", "items": [
            "Tables, rows, keys & relationships",
            "Normalization (1NF–3NF, BCNF)",
            "Denormalization for read performance",
        ]},
        {"g": "Indexing & Queries", "items": [
            "B-tree, hash & composite indexes",
            "Covering indexes & index-only scans",
            "Query planning & the N+1 problem",
        ]},
        {"g": "Transactions", "items": [
            "ACID properties",
            "Isolation levels (read-committed, repeatable-read, serializable)",
            "Optimistic vs pessimistic locking",
            "Connection pooling",
        ]},
        {"g": "How Java/Spring implements this", "items": [
            "Spring Data JPA & repositories",
            "@Transactional & declarative transaction management",
            "HikariCP connection pool defaults in Spring Boot",
        ]},
    ]},

    {"name": "6. NoSQL & Polyglot Persistence", "tag": "nosql", "groups": [
        {"g": "NoSQL Families", "items": [
            "Key-value stores",
            "Document stores",
            "Wide-column stores",
            "Graph databases",
            "Time-series databases",
        ]},
        {"g": "Tradeoffs", "items": [
            "BASE vs ACID",
            "Denormalization & data duplication",
            "Access-pattern-first data modeling",
            "When to choose SQL vs NoSQL",
            "Polyglot persistence in one system",
        ]},
        {"g": "How Java/Spring implements this", "items": [
            "Spring Data MongoDB",
            "Spring Data Cassandra",
            "Spring Data Redis / Neo4j modules",
        ]},
    ]},

    {"name": "7. Data Partitioning & Sharding", "tag": "sharding", "groups": [
        {"g": "Partitioning", "items": [
            "Horizontal vs vertical partitioning",
            "Functional partitioning by service",
        ]},
        {"g": "Sharding Strategies", "items": [
            "Range-based sharding",
            "Hash-based sharding",
            "Directory-based sharding",
            "Geo / entity-based sharding",
        ]},
        {"g": "Scaling Shards", "items": [
            "Consistent hashing & virtual nodes",
            "Hot spots & skew",
            "Rebalancing & resharding",
            "Cross-shard joins & queries",
        ]},
    ]},

    {"name": "8. Replication & Consistency", "tag": "consistency", "groups": [
        {"g": "Replication", "items": [
            "Leader-follower (primary-replica) replication",
            "Multi-leader replication",
            "Leaderless replication (Dynamo-style)",
            "Synchronous vs asynchronous replication",
            "Replication lag & read-your-writes",
        ]},
        {"g": "Consistency Models", "items": [
            "Strong consistency",
            "Eventual consistency",
            "Causal & monotonic consistency",
            "Quorum reads/writes (R + W > N)",
        ]},
        {"g": "Theory & Conflicts", "items": [
            "CAP theorem",
            "PACELC theorem",
            "Conflict resolution (last-write-wins, vector clocks, CRDTs)",
        ]},
    ]},

    {"name": "9. Messaging & Async Processing", "tag": "messaging", "groups": [
        {"g": "Messaging Models", "items": [
            "Message queues (point-to-point)",
            "Publish/subscribe",
            "Event streaming vs message queues",
            "Brokers & topics/partitions",
        ]},
        {"g": "Delivery & Ordering", "items": [
            "Delivery semantics (at-most / at-least / exactly-once)",
            "Message ordering guarantees",
            "Idempotent consumers",
            "Backpressure & flow control",
            "Dead-letter queues & poison messages",
        ]},
        {"g": "How Java/Spring implements this", "items": [
            "Spring for Apache Kafka (KafkaTemplate / @KafkaListener)",
            "Spring AMQP / RabbitMQ",
            "Spring Cloud Stream binder abstraction",
        ]},
    ]},

    {"name": "10. Scalability & Performance", "tag": "scalability", "groups": [
        {"g": "Scaling", "items": [
            "Vertical vs horizontal scaling",
            "Stateless services & externalized state",
            "Load shedding & graceful degradation",
        ]},
        {"g": "Performance", "items": [
            "Throughput vs latency",
            "Tail latency & percentiles (p50/p95/p99)",
            "Batching & request coalescing",
            "Connection reuse & pooling",
            "Profiling & finding bottlenecks",
        ]},
    ]},

    {"name": "11. Reliability, Availability & Resiliency", "tag": "resiliency", "groups": [
        {"g": "Availability", "items": [
            "Redundancy & replication",
            "Active-active vs active-passive failover",
            "Health checks & heartbeats",
            "Single points of failure elimination",
        ]},
        {"g": "Resiliency Patterns", "items": [
            "Timeouts",
            "Retries with exponential backoff & jitter",
            "Circuit breaker",
            "Bulkhead isolation",
            "Fallbacks & graceful degradation",
            "Chaos engineering",
        ]},
        {"g": "How Java/Spring implements this", "items": [
            "Resilience4j (circuit breaker, retry, bulkhead, rate limiter)",
            "Spring Cloud CircuitBreaker abstraction",
            "Spring Boot Actuator health indicators",
        ]},
    ]},

    {"name": "12. Rate Limiting & Throttling", "tag": "rate-limiting", "groups": [
        {"g": "Algorithms", "items": [
            "Token bucket",
            "Leaky bucket",
            "Fixed-window counter",
            "Sliding-window log & sliding-window counter",
        ]},
        {"g": "Distributed Rate Limiting", "items": [
            "Centralized counter (Redis) rate limiting",
            "Per-user vs global quotas",
            "Rate-limit response headers & 429 handling",
        ]},
        {"g": "How Java/Spring implements this", "items": [
            "Bucket4j for token-bucket rate limiting",
            "Spring Cloud Gateway RequestRateLimiter (Redis)",
        ]},
    ]},

    {"name": "13. Storage Systems", "tag": "storage", "groups": [
        {"g": "Storage Types", "items": [
            "Object / blob storage (S3-like)",
            "Block storage",
            "File / network file systems",
            "Distributed file systems (HDFS/GFS)",
        ]},
        {"g": "Data Platforms", "items": [
            "Data lake vs data warehouse",
            "Hot / warm / cold storage tiers",
            "Erasure coding vs replication for durability",
        ]},
    ]},

    {"name": "14. Search & Indexing", "tag": "search", "groups": [
        {"g": "Search Internals", "items": [
            "Inverted index",
            "Tokenization, stemming & analyzers",
            "Relevance ranking (TF-IDF / BM25)",
            "Fuzzy search & typo tolerance",
            "Autocomplete / typeahead",
        ]},
        {"g": "How Java/Spring implements this", "items": [
            "Spring Data Elasticsearch",
            "Elasticsearch cluster basics (shards & replicas)",
        ]},
    ]},

    {"name": "15. Concurrency & Coordination", "tag": "coordination", "groups": [
        {"g": "Locking", "items": [
            "Optimistic vs pessimistic concurrency",
            "Distributed locks (Redis Redlock / ZooKeeper)",
            "Idempotency keys for safe retries",
        ]},
        {"g": "Coordination", "items": [
            "Leader election",
            "Consensus (Paxos / Raft) overview",
            "ZooKeeper / etcd as coordination services",
            "Distributed transactions (2PC / 3PC) & their cost",
            "Saga as an alternative to distributed transactions",
        ]},
    ]},

    {"name": "16. Security & Auth at Scale", "tag": "security", "groups": [
        {"g": "AuthN & AuthZ", "items": [
            "Authentication vs authorization",
            "Sessions vs tokens",
            "OAuth2 & OpenID Connect",
            "JWT structure & validation",
            "API keys & mutual TLS (mTLS)",
        ]},
        {"g": "Protection", "items": [
            "Encryption in transit (TLS) & at rest",
            "Secrets management & rotation",
            "Rate limiting & DDoS protection at the edge",
            "OWASP Top 10 awareness",
        ]},
        {"g": "How Java/Spring implements this", "items": [
            "Spring Security resource server (JWT)",
            "Spring Authorization Server (OAuth2 provider)",
            "Spring Cloud Vault for secrets",
        ]},
    ]},

    {"name": "17. Observability", "tag": "observability", "groups": [
        {"g": "Pillars", "items": [
            "Structured logging & log aggregation",
            "Metrics (counters, gauges, histograms)",
            "Distributed tracing & correlation IDs",
            "The RED & USE methods",
        ]},
        {"g": "Operations", "items": [
            "Dashboards & SLO-based alerting",
            "On-call, runbooks & incident response",
        ]},
        {"g": "How Java/Spring implements this", "items": [
            "Micrometer metrics + Prometheus",
            "Micrometer Tracing (OpenTelemetry)",
            "Spring Boot Actuator endpoints",
        ]},
    ]},

    {"name": "18. Architecture Patterns", "tag": "patterns", "groups": [
        {"g": "Structural", "items": [
            "Monolith & modular monolith",
            "Microservices",
            "Service-oriented architecture (SOA)",
            "Hexagonal / ports-and-adapters",
            "Backend-for-frontend (BFF)",
        ]},
        {"g": "Event & Data", "items": [
            "Event-driven architecture",
            "CQRS (command-query responsibility segregation)",
            "Event sourcing",
            "Saga (orchestration vs choreography)",
            "Transactional outbox",
            "Strangler-fig migration",
        ]},
    ]},

    {"name": "19. API Design", "tag": "api-design", "groups": [
        {"g": "REST", "items": [
            "Resource modeling & naming",
            "Richardson maturity model",
            "Versioning strategies",
            "Pagination, filtering & sorting",
            "Idempotency & safe methods",
            "Error contracts & problem+json",
        ]},
        {"g": "Beyond REST", "items": [
            "GraphQL (schema & resolvers)",
            "gRPC & streaming APIs",
            "Rate-limit & caching headers",
            "API gateway & BFF composition",
        ]},
    ]},

    {"name": "20. Deployment & Infrastructure", "tag": "deployment", "groups": [
        {"g": "Delivery", "items": [
            "Containers & images",
            "Kubernetes (pods, deployments, services)",
            "Blue-green deployment",
            "Canary release & feature flags",
            "Immutable infrastructure & IaC",
        ]},
        {"g": "Resilient Topology", "items": [
            "Multi-AZ & multi-region deployment",
            "Disaster recovery (RPO / RTO)",
            "Autoscaling (horizontal pod autoscaling)",
        ]},
    ]},

    {"name": "21. Use-Case Designs", "tag": "use-cases", "groups": [
        _design("URL Shortener", "unique key generation & collisions"),
        _design("Rate Limiter", "distributed counter accuracy & algorithm choice"),
        _design("Pastebin", "blob storage & TTL-based expiration cleanup"),
        _design("Web Crawler", "URL frontier, dedup & politeness"),
        _design("Notification System", "fan-out, delivery guarantees & retries"),
        _design("News Feed", "feed generation: fan-out on write vs read"),
        _design("Twitter", "timeline fan-out & the celebrity (hot-user) problem"),
        _design("Chat System", "message delivery, presence & fan-out"),
        _design("Typeahead", "trie/prefix ranking & top-k caching"),
        _design("Search Engine", "inverted index building & ranking"),
        _design("Video Streaming", "transcoding pipeline & CDN delivery"),
        _design("Photo Sharing", "media storage & feed fan-out"),
        _design("Ride-Hailing", "geospatial indexing & rider-driver matching"),
        _design("Ticketing", "inventory locking & overselling prevention"),
        _design("E-commerce", "inventory consistency & cart/checkout flow"),
        _design("Payment System", "idempotency, double-spend & exactly-once"),
        _design("Distributed Cache", "sharding, eviction & consistency"),
        _design("Key-Value Store", "partitioning, replication & quorum"),
        _design("Message Queue", "partitioning, ordering & consumer offsets"),
        _design("File Storage", "chunking, dedup & sync conflict resolution"),
        _design("ID Generator", "global uniqueness & rough time ordering (Snowflake)"),
        _design("Leaderboard", "ranking at scale with sorted sets"),
        _design("Ad-Click Aggregator", "stream aggregation & exactly-once counting"),
        _design("Airbnb", "search, availability & booking concurrency"),
        _design("Food Delivery", "matching, ETA & real-time tracking"),
        _design("Collaborative Editor", "concurrent editing (OT vs CRDT)"),
        _design("Job Scheduler", "scheduling, leader election & at-least-once execution"),
        _design("Metrics System", "time-series ingestion & rollups"),
        _design("Recommendation System", "candidate generation & ranking"),
    ]},

    ],
}

DATA_STRUCTURES = {
    "file": "data-structures.html", "title": "Data Structures", "logo": "DS",
    "cat": "CS & Interview Prep",
    "subtitle": "Every core data-structure concept in Java — arrays, lists, stacks, queues, "
                "hashing, trees, heaps, tries, graphs, advanced/range structures, union-find, "
                "and the Java Collections Framework — with operations, complexity & JDK classes.",
    "sections": [

    {"name": "1. Foundations", "tag": "foundations", "groups": [
        {"g": "Complexity Analysis", "items": [
            "Abstract data type vs data structure",
            "Big-O, Big-Theta, Big-Omega notation",
            "Best / average / worst case analysis",
            "Amortized analysis (dynamic-array doubling)",
            "Time vs space tradeoffs",
            "Common growth rates (constant to factorial)",
            "Recursion, the call stack & stack depth",
            "Recursive vs iterative tradeoffs",
            "In-place vs auxiliary-space algorithms",
        ]},
        {"g": "Java Memory Model Basics", "items": [
            "Primitives vs references",
            "Stack vs heap allocation",
            "Autoboxing / unboxing & its cost",
            "Arrays as objects in the JVM",
            "equals() & hashCode() contract",
        ]},
    ]},

    {"name": "2. Arrays & Dynamic Arrays", "tag": "arrays", "groups": [
        {"g": "Concept", "items": [
            "Static (fixed-size) arrays",
            "Multi-dimensional & jagged arrays",
            "Contiguous memory & cache locality",
        ]},
        {"g": "Operations & Complexity", "items": [
            "Random access by index (O(1))",
            "Insert / delete shifting cost",
            "Array resizing & amortized append",
            "Two-pointer & sliding-window on arrays",
            "Prefix-sum & difference arrays",
            "In-place rotation & reversal",
            "Kadane's maximum-subarray technique",
            "Binary search on a sorted array",
        ]},
        {"g": "Java implementation", "items": [
            "Java array syntax & initialization",
            "java.util.ArrayList internals (backing array, capacity)",
            "Arrays utility class (sort, fill, copyOf, binarySearch)",
            "System.arraycopy & array copying",
            "2D matrix traversal & rotation",
            "Converting between arrays and collections",
        ]},
    ]},

    {"name": "3. Strings", "tag": "strings", "groups": [
        {"g": "Concept", "items": [
            "String as a character sequence",
            "String immutability in Java",
            "String pool & interning",
            "char[] vs String",
        ]},
        {"g": "Operations & Complexity", "items": [
            "Concatenation cost & why StringBuilder",
            "Substring, indexOf & searching",
            "Character encoding (UTF-8 / UTF-16)",
            "Anagram & frequency-count problems",
            "Palindrome checking",
            "Pattern matching (naive, KMP, Rabin-Karp overview)",
        ]},
        {"g": "Java implementation", "items": [
            "StringBuilder vs StringBuffer",
            "String methods (split, replace, chars)",
            "Comparing strings (equals vs ==)",
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
            "Delete by node & by value",
            "Traversal of a linked list",
            "Reverse a linked list (iterative & recursive)",
            "Cycle detection (Floyd's tortoise & hare)",
            "Find middle & nth-from-end",
            "Merge two sorted linked lists",
            "Detect intersection of two lists",
            "Check a linked-list palindrome",
            "Copy a list with random pointers",
        ]},
        {"g": "Java implementation", "items": [
            "java.util.LinkedList (List + Deque)",
            "Building a custom Node class",
            "LinkedList vs ArrayList tradeoffs",
        ]},
    ]},

    {"name": "5. Stacks", "tag": "stacks", "groups": [
        {"g": "Concept", "items": [
            "LIFO semantics",
            "Array-backed vs linked stack",
        ]},
        {"g": "Operations & Applications", "items": [
            "push / pop / peek (O(1))",
            "Balanced-parentheses & expression parsing",
            "Infix / postfix / prefix evaluation",
            "Undo/redo & the call stack",
            "Monotonic stack technique",
            "Next-greater-element problems",
        ]},
        {"g": "Java implementation", "items": [
            "ArrayDeque as a stack (preferred)",
            "Legacy java.util.Stack & why to avoid it",
        ]},
    ]},

    {"name": "6. Queues & Deques", "tag": "queues", "groups": [
        {"g": "Concept", "items": [
            "FIFO semantics",
            "Double-ended queue (deque)",
            "Circular buffer / ring buffer",
            "Priority queue concept",
            "Monotonic queue technique",
        ]},
        {"g": "Operations & Complexity", "items": [
            "enqueue / dequeue / peek",
            "offer / poll vs add / remove semantics",
            "Sliding-window maximum with a deque",
            "BFS level-order using a queue",
        ]},
        {"g": "Java implementation", "items": [
            "ArrayDeque as queue & deque",
            "Queue & Deque interfaces",
            "java.util.PriorityQueue (binary heap)",
            "BlockingQueue implementations (overview)",
        ]},
    ]},

    {"name": "7. Hashing", "tag": "hashing", "groups": [
        {"g": "Concept", "items": [
            "Hash functions & desirable properties",
            "Load factor & rehashing",
            "Collision resolution: separate chaining",
            "Collision resolution: open addressing (linear/quadratic/double)",
        ]},
        {"g": "Operations & Complexity", "items": [
            "Average O(1) insert/lookup/delete",
            "Worst-case degradation & mitigation",
        ]},
        {"g": "Java implementation", "items": [
            "HashMap internals (buckets, treeify at 8)",
            "HashSet & LinkedHashMap ordering",
            "hashCode/equals for correct keys",
            "IdentityHashMap & WeakHashMap (overview)",
            "EnumMap & EnumSet",
            "Frequency maps & grouping (computeIfAbsent / merge)",
        ]},
    ]},

    {"name": "8. Trees", "tag": "trees", "groups": [
        {"g": "Concept", "items": [
            "Tree terminology (root, height, depth, leaf)",
            "Binary tree & binary search tree (BST)",
            "Complete / full / perfect / balanced trees",
            "N-ary & general trees",
        ]},
        {"g": "Traversal & Operations", "items": [
            "In-order / pre-order / post-order traversal",
            "Level-order (BFS) traversal",
            "BST insert / search / delete",
            "BST successor & predecessor",
            "Validate a BST",
            "Lowest common ancestor (LCA)",
            "Tree height, depth & diameter",
            "Path-sum & root-to-leaf problems",
            "Serialize & deserialize a tree",
        ]},
        {"g": "Balanced Trees", "items": [
            "AVL trees & rotations",
            "Red-black trees",
            "Why balancing matters (skew to O(n))",
        ]},
        {"g": "Java implementation", "items": [
            "TreeMap & TreeSet (red-black backed)",
            "NavigableMap / NavigableSet operations",
        ]},
    ]},

    {"name": "9. Heaps / Priority Queues", "tag": "heaps", "groups": [
        {"g": "Concept", "items": [
            "Binary heap (min-heap & max-heap)",
            "Heap property & array representation",
            "d-ary heaps (overview)",
        ]},
        {"g": "Operations & Complexity", "items": [
            "insert & sift-up",
            "extract-min/max & sift-down",
            "build-heap in O(n)",
            "Heap sort",
        ]},
        {"g": "Java implementation", "items": [
            "PriorityQueue with a Comparator",
            "Top-K elements with a heap",
            "Merge K sorted lists with a heap",
            "Running median with two heaps",
        ]},
    ]},

    {"name": "10. Tries", "tag": "tries", "groups": [
        {"g": "Concept", "items": [
            "Prefix tree (trie) structure",
            "Compressed trie / radix tree",
            "Ternary search tree",
        ]},
        {"g": "Operations & Applications", "items": [
            "Insert / search / startsWith",
            "Autocomplete & prefix queries",
            "Spell-check & dictionary lookup",
        ]},
        {"g": "Java implementation", "items": [
            "Trie node with a children map/array",
            "Word search & wildcard matching on a trie",
            "Memory tradeoffs (array vs HashMap children)",
        ]},
    ]},

    {"name": "11. Graphs", "tag": "graphs", "groups": [
        {"g": "Concept", "items": [
            "Directed vs undirected graphs",
            "Weighted vs unweighted graphs",
            "Cyclic vs acyclic (DAG)",
            "Connectivity & components",
            "Degree, path & cycle",
        ]},
        {"g": "Representation", "items": [
            "Adjacency list",
            "Adjacency matrix",
            "Edge list",
            "Modeling a graph in Java (Map<V, List<V>>)",
        ]},
        {"g": "Traversal & Operations", "items": [
            "Breadth-first search (BFS)",
            "Depth-first search (DFS)",
            "Topological sort",
            "Shortest path overview (Dijkstra / Bellman-Ford)",
            "Minimum spanning tree overview (Kruskal / Prim)",
            "Connected components & flood fill",
            "Cycle detection (directed & undirected)",
            "Bipartite check (graph coloring)",
        ]},
    ]},

    {"name": "12. Advanced Trees & Range Structures", "tag": "advanced-trees", "groups": [
        {"g": "Range Structures", "items": [
            "Segment tree (range query & update)",
            "Fenwick tree / Binary Indexed Tree (BIT)",
            "Interval tree",
            "Sparse table (static range queries)",
            "Lazy propagation in segment trees",
            "Range-sum & range-min/max queries",
        ]},
        {"g": "Disk & Spatial", "items": [
            "B-tree & B+-tree (database indexes)",
            "Suffix tree & suffix array",
            "k-d tree (spatial partitioning)",
            "Quadtree & geohashing (spatial indexing)",
        ]},
    ]},

    {"name": "13. Disjoint Set / Union-Find", "tag": "union-find", "groups": [
        {"g": "Concept", "items": [
            "Disjoint-set data structure",
            "find & union operations",
        ]},
        {"g": "Optimizations & Uses", "items": [
            "Union by rank / size",
            "Path compression",
            "Near-constant amortized complexity (inverse Ackermann)",
            "Applications (connectivity, Kruskal's MST, cycle detection)",
            "Number of islands / connected components with union-find",
            "Weighted union-find & accounts merge",
        ]},
    ]},

    {"name": "14. Probabilistic & Specialized", "tag": "probabilistic", "groups": [
        {"g": "Probabilistic", "items": [
            "Skip list",
            "Bloom filter (false positives)",
            "Count-min sketch (overview)",
        ]},
        {"g": "Caching Structures", "items": [
            "LRU cache (HashMap + doubly linked list)",
            "LFU cache (overview)",
            "LinkedHashMap access-order for LRU",
        ]},
        {"g": "Specialized", "items": [
            "HyperLogLog for cardinality estimation",
            "Fenwick vs segment tree tradeoffs",
            "Disjoint interval / ordered set tricks",
        ]},
    ]},

    {"name": "15. Java Collections Framework", "tag": "jcf", "groups": [
        {"g": "Interfaces", "items": [
            "Collection hierarchy (Collection/List/Set/Queue/Map)",
            "List implementations (ArrayList, LinkedList, Vector)",
            "Set implementations (HashSet, LinkedHashSet, TreeSet)",
            "Map implementations (HashMap, LinkedHashMap, TreeMap)",
            "Queue/Deque implementations",
        ]},
        {"g": "Behaviors", "items": [
            "Iterator & ListIterator",
            "Comparable vs Comparator",
            "Collections utility methods (sort, binarySearch, unmodifiable)",
            "Fail-fast vs fail-safe iterators",
            "Immutable / unmodifiable collections",
            "Arrays.asList & List.of factory methods",
            "Sorting with Comparator chains (thenComparing)",
        ]},
        {"g": "Concurrency", "items": [
            "ConcurrentHashMap",
            "CopyOnWriteArrayList",
            "Concurrent queues (overview)",
        ]},
    ]},

    {"name": "16. Complexity Cheat-Sheet & Selection", "tag": "cheatsheet", "groups": [
        {"g": "Reference", "items": [
            "Time/space complexity table across structures",
            "Choosing a structure by access pattern",
            "Ordered vs unordered structure tradeoffs",
            "Array vs linked structure memory tradeoffs",
            "When to use a heap vs a balanced tree",
            "When to use a trie vs a hash map",
            "Common pitfalls & anti-patterns",
        ]},
    ]},

    ],
}

LEETCODE = {
    "file": "leetcode-patterns.html", "title": "LeetCode Patterns", "logo": "LC",
    "cat": "CS & Interview Prep",
    "subtitle": "Every coding-interview pattern with when to recognize it and the named "
                "LeetCode problems that drill it — two pointers, sliding window, BFS/DFS, "
                "backtracking, dynamic programming, graphs, and more.",
    "sections": [

    _pat(1, "Two Pointers", "two-pointers",
         "sorted array, pair-sum, or in-place partitioning",
         "opposite-ends or same-direction pointers",
         "O(n) time, O(1) space",
         easy=["Two Sum II - Input Array Is Sorted", "Valid Palindrome",
               "Remove Duplicates from Sorted Array", "Merge Sorted Array",
               "Squares of a Sorted Array", "Move Zeroes", "Reverse String",
               "Intersection of Two Arrays II", "Backspace String Compare",
               "Is Subsequence", "Merge Strings Alternately", "Reverse Vowels of a String"],
         medium=["3Sum", "3Sum Closest", "Container With Most Water", "Sort Colors",
                 "Remove Nth Node From End of List", "4Sum", "Boats to Save People",
                 "Partition Labels", "Sort Array By Parity II", "Bag of Tokens",
                 "Longest Mountain in Array"],
         hard=["Trapping Rain Water"]),

    _pat(2, "Sliding Window", "sliding-window",
         "longest/shortest contiguous subarray or substring",
         "expand right, shrink left while a window condition holds",
         "O(n) time, O(k) space",
         easy=["Maximum Average Subarray I", "Contains Duplicate II"],
         medium=["Longest Substring Without Repeating Characters",
                 "Longest Repeating Character Replacement", "Permutation in String",
                 "Find All Anagrams in a String", "Max Consecutive Ones III",
                 "Fruit Into Baskets", "Minimum Size Subarray Sum",
                 "Subarray Product Less Than K", "Grumpy Bookstore Owner",
                 "Count Number of Nice Subarrays", "Get Equal Substrings Within Budget",
                 "Maximum Points You Can Obtain from Cards", "Binary Subarrays With Sum",
                 "Longest Turbulent Subarray",
                 "Number of Substrings Containing All Three Characters"],
         hard=["Minimum Window Substring", "Sliding Window Maximum",
               "Longest Substring with At Most K Distinct Characters",
               "Substring with Concatenation of All Words"]),

    _pat(3, "Fast & Slow Pointers", "fast-slow",
         "cycle detection or finding the middle of a sequence",
         "two pointers moving at different speeds",
         "O(n) time, O(1) space",
         easy=["Linked List Cycle", "Middle of the Linked List", "Happy Number",
               "Palindrome Linked List", "Intersection of Two Linked Lists"],
         medium=["Linked List Cycle II", "Reorder List", "Find the Duplicate Number",
                 "Circular Array Loop", "Sort List", "Add Two Numbers"]),

    _pat(4, "Merge Intervals", "merge-intervals",
         "overlapping intervals or scheduling",
         "sort by start, then merge or sweep",
         "O(n log n) time",
         easy=["Summary Ranges"],
         medium=["Merge Intervals", "Insert Interval", "Non-overlapping Intervals",
                 "Meeting Rooms II", "Interval List Intersections",
                 "Minimum Number of Arrows to Burst Balloons", "Car Pooling",
                 "Employee Free Time", "Teemo Attacking", "Remove Covered Intervals",
                 "Divide Intervals Into Minimum Number of Groups"],
         hard=["Data Stream as Disjoint Intervals"]),

    _pat(5, "Cyclic Sort", "cyclic-sort",
         "array of numbers in a known range [1..n]",
         "place each number at its index by swapping",
         "O(n) time, O(1) space",
         easy=["Missing Number", "Find All Numbers Disappeared in an Array",
               "Set Mismatch", "Kth Missing Positive Number", "Sort Array By Parity"],
         medium=["Find All Duplicates in an Array", "Find the Missing and Repeated Values"],
         hard=["First Missing Positive", "Couples Holding Hands"]),

    _pat(6, "In-place LinkedList Reversal", "ll-reversal",
         "reverse all or part of a linked list without extra space",
         "track prev/current/next and relink pointers",
         "O(n) time, O(1) space",
         easy=["Reverse Linked List", "Remove Linked List Elements"],
         medium=["Reverse Linked List II", "Rotate List", "Swap Nodes in Pairs",
                 "Odd Even Linked List", "Split Linked List in Parts",
                 "Remove Duplicates from Sorted List II", "Partition List"],
         hard=["Reverse Nodes in k-Group"]),

    _pat(7, "Tree BFS", "tree-bfs",
         "level-by-level traversal of a tree",
         "queue holding one level at a time",
         "O(n) time, O(w) space (width)",
         easy=["Average of Levels in Binary Tree", "Minimum Depth of Binary Tree",
               "Cousins in Binary Tree"],
         medium=["Binary Tree Level Order Traversal",
                 "Binary Tree Zigzag Level Order Traversal", "Binary Tree Right Side View",
                 "Populating Next Right Pointers in Each Node",
                 "Find Largest Value in Each Tree Row",
                 "Binary Tree Level Order Traversal II", "All Nodes Distance K in Binary Tree",
                 "Maximum Width of Binary Tree", "Add One Row to Tree", "Even Odd Tree",
                 "Deepest Leaves Sum", "Maximum Level Sum of a Binary Tree"]),

    _pat(8, "Tree DFS", "tree-dfs",
         "root-to-leaf paths or recursive subtree computation",
         "recurse pre/in/post-order, combine child results",
         "O(n) time, O(h) space (height)",
         easy=["Maximum Depth of Binary Tree", "Same Tree", "Symmetric Tree",
               "Path Sum", "Invert Binary Tree", "Diameter of Binary Tree",
               "Balanced Binary Tree", "Subtree of Another Tree"],
         medium=["Path Sum II", "Path Sum III", "Count Good Nodes in Binary Tree",
                 "Lowest Common Ancestor of a Binary Tree", "Validate Binary Search Tree",
                 "Kth Smallest Element in a BST",
                 "Construct Binary Tree from Preorder and Inorder Traversal",
                 "Flatten Binary Tree to Linked List", "House Robber III",
                 "Binary Tree Paths", "Sum Root to Leaf Numbers", "Maximum Binary Tree",
                 "Binary Search Tree Iterator", "Delete Node in a BST",
                 "Convert Sorted Array to Binary Search Tree", "Range Sum of BST"],
         hard=["Binary Tree Maximum Path Sum", "Serialize and Deserialize Binary Tree",
               "Vertical Order Traversal of a Binary Tree"]),

    _pat(9, "Graph BFS/DFS", "graph-traversal",
         "traversing or exploring a general graph",
         "BFS with a queue or DFS with recursion/stack + visited set",
         "O(V + E) time",
         medium=["Clone Graph", "Number of Provinces", "Pacific Atlantic Water Flow",
                 "Rotting Oranges", "Snakes and Ladders", "Minimum Genetic Mutation",
                 "Keys and Rooms", "Is Graph Bipartite?", "Find if Path Exists in Graph",
                 "Open the Lock", "Shortest Bridge", "All Paths From Source to Target",
                 "Find the Town Judge", "Nearest Exit from Entrance in Maze",
                 "Detonate the Maximum Bombs",
                 "Count Unreachable Pairs of Nodes in an Undirected Graph",
                 "As Far from Land as Possible"],
         hard=["Word Ladder", "Word Ladder II", "Reconstruct Itinerary"]),

    _pat(10, "Matrix / Number of Islands", "islands",
         "connected regions in a 2D grid",
         "flood-fill each cell with BFS/DFS, mark visited",
         "O(m*n) time",
         easy=["Flood Fill", "Island Perimeter"],
         medium=["Number of Islands", "Max Area of Island", "Surrounded Regions",
                 "Number of Closed Islands", "Walls and Gates", "01 Matrix",
                 "Number of Enclaves", "Count Sub Islands", "Coloring A Border",
                 "Shortest Path in Binary Matrix", "Number of Distinct Islands"],
         hard=["Making A Large Island", "Shortest Path to Get All Keys"]),

    _pat(11, "Two Heaps", "two-heaps",
         "track a running median or split by a threshold",
         "a max-heap for the low half, a min-heap for the high half",
         "O(log n) per insert",
         medium=["Find Right Interval", "Furthest Building You Can Reach",
                 "Maximum Average Pass Ratio", "Single-Threaded CPU",
                 "Process Tasks Using Servers"],
         hard=["Find Median from Data Stream", "Sliding Window Median", "IPO",
               "Minimize Deviation in Array", "Constrained Subsequence Sum",
               "The Skyline Problem", "Meeting Rooms III"]),

    _pat(12, "Subsets (Combinations & Permutations)", "subsets",
         "generate all subsets, combinations, or permutations",
         "BFS build-up or DFS include/exclude decisions",
         "O(2^n) or O(n!) time",
         medium=["Subsets", "Subsets II", "Permutations", "Permutations II",
                 "Combinations", "Combination Sum", "Combination Sum II",
                 "Letter Combinations of a Phone Number", "Generate Parentheses",
                 "Palindrome Partitioning", "Letter Tile Possibilities",
                 "Find Unique Binary String", "Iterator for Combination"]),

    _pat(13, "Modified Binary Search", "mod-binary-search",
         "sorted (or rotated) input, or monotonic answer space",
         "binary search on index or on the answer",
         "O(log n) time",
         easy=["Binary Search", "Search Insert Position", "First Bad Version",
               "Sqrt(x)", "Guess Number Higher or Lower", "Arranging Coins"],
         medium=["Search in Rotated Sorted Array", "Find Minimum in Rotated Sorted Array",
                 "Find First and Last Position of Element in Sorted Array",
                 "Search a 2D Matrix", "Find Peak Element", "Koko Eating Bananas",
                 "Capacity To Ship Packages Within D Days",
                 "Single Element in a Sorted Array", "Time Based Key-Value Store",
                 "Peak Index in a Mountain Array", "Find K Closest Elements",
                 "Minimum Speed to Arrive on Time", "Search in Rotated Sorted Array II",
                 "Maximum Number of Removable Characters", "Successful Pairs of Spells and Potions"],
         hard=["Median of Two Sorted Arrays", "Split Array Largest Sum",
               "Find in Mountain Array", "Kth Smallest Number in Multiplication Table"]),

    _pat(14, "Bitwise XOR / Bit Manipulation", "bit-xor",
         "pairing, toggling, or counting bits",
         "XOR cancellation, masks, and shifts",
         "O(n) time, O(1) space",
         easy=["Single Number", "Number of 1 Bits", "Counting Bits", "Reverse Bits",
               "Hamming Distance", "Power of Two", "Complement of Base 10 Integer",
               "Find the Difference", "Binary Watch", "Decode XORed Array"],
         medium=["Single Number II", "Single Number III", "Sum of Two Integers",
                 "Bitwise AND of Numbers Range", "Maximum XOR of Two Numbers in an Array",
                 "Gray Code", "Divide Two Integers", "XOR Queries of a Subarray",
                 "Minimum Flips to Make a OR b Equal to c"]),

    _pat(15, "Top-K Elements", "top-k",
         "k largest/smallest/most-frequent elements",
         "a size-k heap or bucket sort by frequency",
         "O(n log k) time",
         medium=["Top K Frequent Elements", "Kth Largest Element in an Array",
                 "K Closest Points to Origin", "Sort Characters By Frequency",
                 "Kth Largest Element in a Stream", "Task Scheduler", "Reorganize String",
                 "Least Number of Unique Integers after K Removals", "Top K Frequent Words",
                 "Find the Kth Largest Integer in the Array", "Sort the People",
                 "Kth Distinct String in an Array", "Maximum Number of Coins You Can Get"]),

    _pat(16, "K-way Merge", "k-way-merge",
         "merge k sorted lists/arrays or pick across k sequences",
         "a min-heap holding one head from each list",
         "O(n log k) time",
         easy=["Merge Two Sorted Lists"],
         medium=["Kth Smallest Element in a Sorted Matrix", "Find K Pairs with Smallest Sums",
                 "Ugly Number II", "Super Ugly Number"],
         hard=["Merge k Sorted Lists", "Smallest Range Covering Elements from K Lists",
               "Find K-th Smallest Pair Distance"]),

    _pat(17, "Backtracking", "backtracking",
         "constraint-satisfaction search over choices",
         "choose, recurse, un-choose (prune invalid branches)",
         "exponential in the worst case",
         medium=["Word Search", "Combination Sum III", "Restore IP Addresses",
                 "Beautiful Arrangement", "Matchsticks to Square",
                 "Partition to K Equal Sum Subsets", "Letter Case Permutation",
                 "Additive Number", "Split Array into Fibonacci Sequence",
                 "Numbers With Same Consecutive Differences"],
         hard=["N-Queens", "N-Queens II", "Sudoku Solver", "Permutation Sequence",
               "Remove Invalid Parentheses", "Expression Add Operators", "24 Game",
               "Word Squares"]),

    _pat(18, "DP: 0/1 Knapsack", "dp-01-knapsack",
         "pick/skip items with a capacity constraint (each item once)",
         "dp[i][w] over items and remaining capacity",
         "O(n*W) time",
         medium=["Partition Equal Subset Sum", "Target Sum", "Last Stone Weight II",
                 "Ones and Zeroes", "Maximum Value of K Coins From Piles",
                 "Filling Bookcase Shelves"],
         hard=["Profitable Schemes", "Tallest Billboard", "Number of Ways to Earn Points"]),

    _pat(19, "DP: Unbounded Knapsack", "dp-unbounded-knapsack",
         "items reusable an unlimited number of times",
         "dp over amount, iterate coins/items in the inner loop",
         "O(n*amount) time",
         medium=["Coin Change", "Coin Change II", "Combination Sum IV", "Perfect Squares",
                 "Minimum Cost For Tickets", "Integer Break",
                 "Number of Dice Rolls With Target Sum", "Word Break"],
         hard=["Word Break II"]),

    _pat(20, "DP: Fibonacci / Linear", "dp-fibonacci",
         "each state depends on a few previous states",
         "dp[i] from dp[i-1], dp[i-2] (rolling variables)",
         "O(n) time, O(1) space",
         easy=["Climbing Stairs", "Fibonacci Number", "N-th Tribonacci Number",
               "Min Cost Climbing Stairs", "Get Maximum in Generated Array"],
         medium=["House Robber", "House Robber II", "Delete and Earn", "Decode Ways",
                 "Maximum Product Subarray", "Domino and Tromino Tiling",
                 "Count Vowels Permutation", "Knight Dialer"],
         hard=["Number of Ways to Stay in the Same Place After Some Steps",
               "Student Attendance Record II"]),

    _pat(21, "DP: Longest Common Subsequence", "dp-lcs",
         "matching/aligning two sequences",
         "2D dp over prefixes of both strings",
         "O(m*n) time",
         medium=["Longest Common Subsequence", "Delete Operation for Two Strings",
                 "Minimum ASCII Delete Sum for Two Strings", "Uncrossed Lines",
                 "Interleaving String", "Maximum Length of Repeated Subarray"],
         hard=["Edit Distance", "Distinct Subsequences", "Shortest Common Supersequence"]),

    _pat(22, "DP: Palindromic Subsequence", "dp-palindrome",
         "palindrome substrings/subsequences or partitions",
         "expand-around-center or interval dp[i][j]",
         "O(n^2) time",
         easy=["Valid Palindrome II"],
         medium=["Longest Palindromic Substring", "Longest Palindromic Subsequence",
                 "Palindromic Substrings"],
         hard=["Palindrome Partitioning II",
               "Minimum Insertion Steps to Make a String Palindrome",
               "Count Different Palindromic Subsequences",
               "Longest Chunked Palindrome Decomposition"]),

    _pat(23, "DP: Longest Increasing Subsequence", "dp-lis",
         "longest/optimal increasing chain",
         "dp[i] = best ending at i, or patience sorting with binary search",
         "O(n log n) with binary search",
         medium=["Longest Increasing Subsequence", "Largest Divisible Subset",
                 "Number of Longest Increasing Subsequence", "Maximum Length of Pair Chain",
                 "Longest Arithmetic Subsequence", "Longest String Chain",
                 "Best Team With No Conflicts"],
         hard=["Russian Doll Envelopes", "Minimum Number of Removals to Make Mountain Array"]),

    _pat(24, "DP: Grid / Matrix", "dp-grid",
         "paths or costs through a 2D grid",
         "dp[r][c] from top and left neighbors",
         "O(m*n) time",
         medium=["Unique Paths", "Unique Paths II", "Minimum Path Sum", "Triangle",
                 "Maximal Square", "Minimum Falling Path Sum",
                 "Count Square Submatrices with All Ones", "Where Will the Ball Fall",
                 "Out of Boundary Paths", "Longest Increasing Path in a Matrix",
                 "Path with Maximum Gold"],
         hard=["Cherry Pickup", "Dungeon Game", "Unique Paths III"]),

    _pat(25, "DP: Interval / Partition", "dp-interval",
         "optimal way to split or combine a range",
         "dp[i][j] over subintervals, try every split point",
         "O(n^3) time",
         medium=["Guess Number Higher or Lower II", "Predict the Winner", "Stone Game",
                 "Minimum Score Triangulation of Polygon"],
         hard=["Burst Balloons", "Strange Printer", "Remove Boxes",
               "Minimum Cost to Merge Stones", "Minimum Cost to Cut a Stick"]),

    _pat(26, "DP: State Machine (Stocks)", "dp-state-machine",
         "sequential decisions with a few discrete states",
         "track dp per state (hold/sold/rest) across time",
         "O(n) or O(n*k) time",
         easy=["Best Time to Buy and Sell Stock"],
         medium=["Best Time to Buy and Sell Stock II",
                 "Best Time to Buy and Sell Stock with Cooldown",
                 "Best Time to Buy and Sell Stock with Transaction Fee", "Paint House"],
         hard=["Best Time to Buy and Sell Stock III",
               "Best Time to Buy and Sell Stock IV",
               "Maximum Profit in Job Scheduling", "Paint House II"]),

    _pat(27, "Greedy", "greedy",
         "a locally optimal choice yields a global optimum",
         "sort or use a heap, then commit greedily with an exchange argument",
         "O(n log n) time",
         easy=["Assign Cookies", "Lemonade Change", "Can Place Flowers"],
         medium=["Jump Game", "Jump Game II", "Gas Station", "Hand of Straights",
                 "Dota2 Senate", "Queue Reconstruction by Height", "Non-decreasing Array",
                 "Wiggle Subsequence", "Partition Array into Disjoint Intervals",
                 "Minimum Deletions to Make Character Frequencies Unique",
                 "Advantage Shuffle", "Two City Scheduling",
                 "Reduce Array Size to The Half", "Eliminate Maximum Number of Monsters"],
         hard=["Candy", "Minimum Number of Refueling Stops",
               "Maximum Number of Events That Can Be Attended II"]),

    _pat(28, "Monotonic Stack", "monotonic-stack",
         "next greater/smaller element or histogram spans",
         "keep an increasing/decreasing stack, pop on violation",
         "O(n) time",
         easy=["Next Greater Element I", "Final Prices With a Special Discount in a Shop"],
         medium=["Daily Temperatures", "Next Greater Element II", "Online Stock Span",
                 "Sum of Subarray Minimums", "Remove K Digits", "Remove Duplicate Letters",
                 "Asteroid Collision", "Car Fleet", "132 Pattern", "Sum of Subarray Ranges",
                 "Remove Nodes From Linked List", "Steps to Make Array Non-decreasing"],
         hard=["Largest Rectangle in Histogram", "Maximal Rectangle",
               "Number of Visible People in a Queue", "Maximum Subarray Min-Product"]),

    _pat(29, "Prefix Sum", "prefix-sum",
         "range sums or subarray-sum conditions",
         "precompute cumulative sums; use a hash map of prefixes",
         "O(n) time",
         easy=["Running Sum of 1d Array", "Find Pivot Index", "Range Sum Query - Immutable"],
         medium=["Subarray Sum Equals K", "Contiguous Array", "Product of Array Except Self",
                 "Range Sum Query 2D - Immutable", "Continuous Subarray Sum",
                 "Subarray Sums Divisible by K", "Maximum Size Subarray Sum Equals k",
                 "Corporate Flight Bookings", "Number of Ways to Split Array",
                 "Sum of Absolute Differences in a Sorted Array",
                 "Maximum Sum of Distinct Subarrays With Length K",
                 "Count Number of Homogenous Substrings"]),

    _pat(30, "Trie", "trie",
         "prefix search, word dictionaries, or bit-tries",
         "tree of character/bit nodes with an end marker",
         "O(L) per operation (L = word length)",
         medium=["Implement Trie (Prefix Tree)",
                 "Design Add and Search Words Data Structure", "Map Sum Pairs",
                 "Replace Words", "Implement Magic Dictionary", "Search Suggestions System",
                 "Longest Word in Dictionary", "Design File System", "Camelcase Matching",
                 "Short Encoding of Words"],
         hard=["Word Search II", "Concatenated Words", "Palindrome Pairs",
               "Stream of Characters", "Prefix and Suffix Search"]),

    _pat(31, "Union-Find", "union-find",
         "dynamic connectivity or grouping by equivalence",
         "disjoint sets with union by rank + path compression",
         "near O(1) amortized per operation",
         medium=["Redundant Connection",
                 "Number of Connected Components in an Undirected Graph", "Accounts Merge",
                 "Most Stones Removed with Same Row or Column",
                 "Satisfiability of Equality Equations", "Graph Valid Tree",
                 "Smallest String With Swaps", "Evaluate Division"],
         hard=["Redundant Connection II", "Number of Islands II", "Swim in Rising Water"]),

    _pat(32, "Topological Sort", "topo-sort",
         "ordering with dependency (prerequisite) constraints",
         "Kahn's BFS on in-degrees, or DFS post-order",
         "O(V + E) time",
         medium=["Course Schedule", "Course Schedule II", "Minimum Height Trees",
                 "Find Eventual Safe States", "All Ancestors of a Directed Acyclic Graph"],
         hard=["Alien Dictionary", "Parallel Courses III",
               "Sort Items by Groups Respecting Dependencies", "Sequence Reconstruction"]),

    _pat(33, "Shortest Path", "shortest-path",
         "weighted shortest path or minimum-cost traversal",
         "Dijkstra (heap), Bellman-Ford, or 0-1 BFS",
         "O(E log V) with a heap",
         medium=["Network Delay Time", "Cheapest Flights Within K Stops",
                 "Path with Maximum Probability", "Path With Minimum Effort"],
         hard=["Bus Routes", "Minimum Cost to Make at Least One Valid Path in a Grid",
               "Shortest Path in a Grid with Obstacles Elimination",
               "Find the City With the Smallest Number of Neighbors at a Threshold Distance"]),

    _pat(34, "Segment Tree / BIT", "segment-tree",
         "range queries with point/range updates",
         "segment tree or Fenwick tree over the array",
         "O(log n) per query/update",
         medium=["Range Sum Query - Mutable", "Range Sum Query 2D - Mutable",
                 "My Calendar I", "My Calendar II"],
         hard=["Count of Smaller Numbers After Self", "Reverse Pairs", "Count of Range Sum",
               "My Calendar III", "Falling Squares", "Range Module"]),

    _pat(35, "Design", "design",
         "implement a data structure to a required interface",
         "compose maps, heaps, and linked lists for O(1)/O(log n) ops",
         "per-operation complexity is the goal",
         medium=["LRU Cache", "Design HashMap", "Design HashSet", "Design Linked List",
                 "Insert Delete GetRandom O(1)", "Min Stack", "Design Browser History",
                 "Design Circular Queue", "Design Underground System", "Snapshot Array",
                 "Design Hit Counter", "Design Circular Deque", "Logger Rate Limiter",
                 "Design Most Recently Used Queue", "Design a Number Container System"],
         hard=["LFU Cache", "All O`one Data Structure", "Design Twitter",
               "Design In-Memory File System", "Max Stack"]),

    _pat(36, "Math & Geometry", "math-geometry",
         "number theory, matrix manipulation, or coordinate geometry",
         "modular arithmetic, in-place matrix moves, line slopes",
         "varies by problem",
         easy=["Palindrome Number", "Roman to Integer", "Plus One",
               "Excel Sheet Column Number", "Add Digits", "Power of Three", "Fizz Buzz",
               "Reverse Integer", "Ugly Number", "Add Binary", "Self Dividing Numbers"],
         medium=["Rotate Image", "Spiral Matrix", "Set Matrix Zeroes", "Pow(x, n)",
                 "Multiply Strings", "Integer to Roman", "Rotate Array", "Count Primes",
                 "Excel Sheet Column Title", "Fraction to Recurring Decimal",
                 "Factorial Trailing Zeroes", "Angle Between Hands of a Clock",
                 "Spiral Matrix II"],
         hard=["Max Points on a Line", "Basic Calculator", "Integer to English Words"]),

    ],
}

PROJECTS = [SYSTEM_DESIGN, DATA_STRUCTURES, LEETCODE]
