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
    "sections": [],
}

PROJECTS = [SYSTEM_DESIGN, DATA_STRUCTURES, LEETCODE]
