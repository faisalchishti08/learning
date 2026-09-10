# Interview Mastery Map — DSA · LLD · HLD · System Design
### Target: Senior Technical Lead / Staff Engineer (Java, 10 YOE)

> Companion to `java-tech-lead-mastery-roadmap.md`.
> That file = **what you must know**. This file = **what you must be able to perform, under time pressure, on a call**.

---

## 0. How To Use This File

### 0.1 Legend
| Marker | Meaning |
|---|---|
| `- [ ]` | Not started · `- [~]` in progress · `- [x]` performable under timed pressure |
| 🔴 | Appears in ≥50% of loops. Non-negotiable. |
| 🟡 | Appears regularly, differentiates senior from mid |
| 🟢 | Depth signal, situational, or company-specific |
| ⏱ | Timed drill — practice against a clock, not just "understand" |

### 0.2 The Only Real Measure
Reading ≠ readiness. A topic is done when you can, **on a shared screen, talking out loud, in the time limit**:
1. Restate the problem and its constraints correctly
2. Propose an approach and justify it against ≥1 alternative
3. Produce working code / a coherent diagram
4. Name the failure modes of your own solution
5. Answer 2 follow-ups that change the constraints

### 0.3 Round-Type Map — where each Part pays off

| Round | Duration | Parts to prepare |
|---|---|---|
| Phone screen / online assessment | 60–90m | 1, 2, 3, 4, 5 |
| DSA coding (onsite) | 45–60m | 1–5, 19 |
| Low-level design / OOD | 45–60m | 6, 7, 19 |
| Machine coding | 90–180m | 7 |
| High-level / system design | 45–75m | 8, 9, 10, 11, 19 |
| Java deep dive | 45–60m | 5, + core roadmap Parts 1–3 |
| Database / SQL | 45m | 10.1, 10.2 |
| Debugging / troubleshooting | 45m | 13 |
| Code review | 45m | 14 |
| Behavioral / leadership | 45–60m | 15 |
| Hiring manager | 45m | 15, 16 |
| Bar raiser / cross-functional | 60m | 15, 16, 19 |
| Architecture presentation | 45–60m | 17 |

### 0.4 Progress Dashboard

| Part | Area | Priority | Status | Timed-drill pass? |
|---|---|---|---|---|
| 1 | Complexity & Problem-Solving Frameworks | 🔴 | ☐ | ☐ |
| 2 | Data Structures | 🔴 | ☐ | ☐ |
| 3 | Algorithms & Techniques | 🔴 | ☐ | ☐ |
| 4 | Pattern → Problem Catalog | 🔴 | ☐ | ☐ |
| 5 | Java for Coding Rounds | 🔴 | ☐ | ☐ |
| 6 | Low-Level Design (OOD) | 🔴 | ☐ | ☐ |
| 7 | Machine Coding Round | 🟡 | ☐ | ☐ |
| 8 | System Design Building Blocks | 🔴 | ☐ | ☐ |
| 9 | System Design Problem Catalog | 🔴 | ☐ | ☐ |
| 10 | Deep-Dive Subsystems | 🔴 | ☐ | ☐ |
| 11 | Estimation & Capacity Math | 🔴 | ☐ | ☐ |
| 12 | Enterprise / Domain Design | 🟡 | ☐ | ☐ |
| 13 | Debugging & Troubleshooting Round | 🔴 | ☐ | ☐ |
| 14 | Code Review Round | 🟡 | ☐ | ☐ |
| 15 | Behavioral & Leadership | 🔴 | ☐ | ☐ |
| 16 | Company Formats & Level Calibration | 🟡 | ☐ | ☐ |
| 17 | Your Own Architecture Story | 🔴 | ☐ | ☐ |
| 18 | Drill Plans & Schedules | 🔴 | ☐ | ☐ |
| 19 | Communication & Execution Skills | 🔴 | ☐ | ☐ |

---
---

# PART 1 — COMPLEXITY & PROBLEM-SOLVING FRAMEWORKS 🔴

## 1.1 Complexity Analysis
- [ ] Big-O, Big-Θ, Big-Ω — precise definitions, not hand-waving
- [ ] Best / average / worst case; why average case needs a distribution assumption
- [ ] Amortized analysis: aggregate, accounting, potential method (ArrayList growth, union-find)
- [ ] Space complexity: auxiliary vs total; recursion stack counts
- [ ] Common complexity classes and growth intuition: O(1), O(log n), O(√n), O(n), O(n log n), O(n²), O(2ⁿ), O(n!)
- [ ] Recurrence relations & Master Theorem
- [ ] Complexity of recursion trees; T(n) = 2T(n/2) + n
- [ ] Complexity of common JDK operations — memorized table 🔴
- [ ] Practical constants: why O(n log n) sort can beat O(n) hash approach at small n
- [ ] Complexity of your solution stated *before* you code it (interviewers grade this)

### 1.1.1 JDK Complexity Table — memorize 🔴
- [ ] `ArrayList`: get O(1), add amortized O(1), add(i) O(n), remove O(n), contains O(n)
- [ ] `LinkedList`: get O(n), addFirst/addLast O(1), remove(node) O(1)
- [ ] `HashMap`: get/put O(1) avg, O(log n) worst (treeified), O(n) pathological pre-Java 8
- [ ] `TreeMap`: get/put/remove O(log n), ordered traversal O(n)
- [ ] `LinkedHashMap`: O(1) with predictable order
- [ ] `PriorityQueue`: offer/poll O(log n), peek O(1), **contains/remove(Object) O(n)**
- [ ] `ArrayDeque`: push/pop/peek O(1) amortized
- [ ] `TreeSet` navigation: floor/ceiling/higher/lower O(log n)
- [ ] `Arrays.sort` primitives O(n log n) dual-pivot quicksort (O(n²) adversarial), objects TimSort stable
- [ ] `Collections.sort` = TimSort, O(n) on nearly-sorted input
- [ ] `String.substring` O(n) since Java 7u6, `concat` O(n+m), `StringBuilder.append` amortized O(1)

## 1.2 Problem-Solving Framework 🔴
- [ ] **Step 1 — Clarify (2–4 min):** input types, ranges, nulls, duplicates, sorted?, empty?, memory limits, streaming vs in-memory, expected output format, can I mutate input?
- [ ] **Step 2 — Examples:** work one normal, one edge, one degenerate case by hand
- [ ] **Step 3 — Brute force first:** state it, state its complexity, then improve. Never skip this.
- [ ] **Step 4 — Identify the pattern** (see Part 4) — sorted → binary search / two pointers; "top K" → heap; "all subsets" → backtracking; overlapping subproblems → DP
- [ ] **Step 5 — Optimize:** what's the bottleneck? Trade space for time (hash), preprocessing, better structure, amortization
- [ ] **Step 6 — Confirm the approach out loud before coding** ("Does this direction work for you?")
- [ ] **Step 7 — Code:** clean names, helper methods, no golfing
- [ ] **Step 8 — Dry run** on your example, line by line
- [ ] **Step 9 — Edge cases:** empty, one element, all same, max size, overflow, negatives, unicode
- [ ] **Step 10 — Complexity + trade-offs + how you'd test it**

## 1.3 Recognizing the Pattern from Constraints 🔴
- [ ] n ≤ 12 → permutations / brute force O(n!)
- [ ] n ≤ 20 → bitmask DP / subsets O(2ⁿ)
- [ ] n ≤ 100 → O(n³) allowed (Floyd-Warshall, interval DP)
- [ ] n ≤ 1,000 → O(n²) allowed
- [ ] n ≤ 10⁵–10⁶ → O(n log n) required (sort, heap, binary search)
- [ ] n ≤ 10⁸ → O(n) or O(log n) only
- [ ] "K-th largest / top K" → heap or quickselect
- [ ] "Contiguous subarray" → sliding window / prefix sum / Kadane
- [ ] "Sorted array" → binary search / two pointers
- [ ] "Count of ways / min-max cost" → DP
- [ ] "Shortest path" → BFS (unweighted) / Dijkstra (weighted) / Bellman-Ford (negative)
- [ ] "Connected components / merge groups" → union-find or DFS
- [ ] "Next greater / previous smaller" → monotonic stack
- [ ] "Range query with updates" → segment tree / BIT
- [ ] "Prefix / autocomplete" → trie
- [ ] "Cycle detection" → fast-slow pointers / DFS colors / union-find
- [ ] "In-place, O(1) space" → pointer manipulation / index-as-hash / cyclic sort

---
---

# PART 2 — DATA STRUCTURES 🔴

## 2.1 Arrays & Strings 🔴
- [ ] Traversal, in-place modification, index-as-hashmap trick
- [ ] Two pointers: opposite ends, same direction, fast-slow
- [ ] Sliding window: fixed size, variable size, window with counts/frequency map
- [ ] Prefix sums, suffix sums, 2D prefix sums
- [ ] Difference arrays / range update trick
- [ ] Kadane's algorithm (max subarray) and variants (circular, product, 2D)
- [ ] Dutch national flag / 3-way partition
- [ ] Cyclic sort (values 1..n)
- [ ] Rotation: reversal trick, juggling
- [ ] Matrix: spiral, rotate in place, transpose, diagonal traversal, search in sorted matrix
- [ ] String: palindromes (expand around center, Manacher 🟢), anagrams, subsequences vs substrings
- [ ] String matching: KMP, Rabin-Karp (rolling hash), Z-algorithm 🟡
- [ ] Encoding/decoding, run-length, string compression
- [ ] Java specifics: `char[]` vs `String`, `StringBuilder` in loops, `toCharArray()` cost

## 2.2 Hashing 🔴
- [ ] Hash table internals: buckets, collisions (chaining vs open addressing), load factor, resize
- [ ] Designing a good hash function; distribution and clustering
- [ ] `HashMap` vs `HashSet` vs `LinkedHashMap` vs `TreeMap` — choose correctly under pressure
- [ ] Frequency counting, grouping, index maps
- [ ] Two-sum family and complement lookup
- [ ] Prefix-sum + hashmap (subarray sum equals K)
- [ ] Custom keys: implementing `equals`/`hashCode`, records as keys, `List` as key caution
- [ ] Rolling hash & collision handling
- [ ] Consistent hashing (comes up in both DSA and HLD) 🔴
- [ ] Bloom filter: false positives, sizing, use cases 🟡
- [ ] Count-Min Sketch, HyperLogLog 🟡
- [ ] Hash collision DoS awareness (why keys are randomized in some languages)

## 2.3 Linked Lists 🟡
- [ ] Singly, doubly, circular; sentinel/dummy node technique
- [ ] Reverse (iterative + recursive), reverse in k-groups
- [ ] Fast-slow pointers: middle, cycle detection (Floyd), cycle start, palindrome check
- [ ] Merge two/K sorted lists
- [ ] Remove Nth from end, remove duplicates
- [ ] Copy list with random pointer
- [ ] Flatten multilevel list
- [ ] LRU cache = doubly linked list + hashmap 🔴
- [ ] LFU cache 🟡
- [ ] Skip lists (concept, `ConcurrentSkipListMap`) 🟡

## 2.4 Stacks & Queues 🔴
- [ ] Stack applications: balanced parens, expression evaluation (infix/postfix), backtracking undo
- [ ] Monotonic stack: next greater/smaller element, largest rectangle in histogram, trapping rain water, stock span 🔴
- [ ] Min stack / max stack O(1)
- [ ] Queue via two stacks; stack via two queues
- [ ] Monotonic deque: sliding window maximum 🔴
- [ ] Circular buffer / ring buffer design
- [ ] `ArrayDeque` over `Stack`/`LinkedList` — know why
- [ ] Bounded blocking queue implementation (concurrency crossover) 🔴

## 2.5 Trees 🔴
- [ ] Terminology: height, depth, balanced, complete, full, perfect
- [ ] Traversals: preorder, inorder, postorder (recursive + iterative), level order (BFS)
- [ ] Morris traversal (O(1) space) 🟢
- [ ] BST: insert, delete, search, validate BST, inorder successor/predecessor
- [ ] BST from sorted array / preorder; kth smallest
- [ ] Balanced trees: AVL rotations, red-black properties (conceptual; `TreeMap` uses RB) 🟡
- [ ] Lowest common ancestor (BST and general tree, with/without parent pointers)
- [ ] Diameter, max path sum, height/depth problems
- [ ] Serialize/deserialize a tree 🔴
- [ ] Path sum family, root-to-leaf problems
- [ ] Tree views: left/right/top/bottom, vertical order
- [ ] Symmetric/mirror, same tree, subtree of another tree
- [ ] N-ary trees, tree from parent array
- [ ] Segment tree: build, range query, point/range update, lazy propagation 🟡
- [ ] Fenwick tree / BIT: prefix sums with updates 🟡
- [ ] Trie: insert, search, prefix search, delete; autocomplete, word search, XOR-maximum trie 🔴
- [ ] B-tree / B+ tree conceptually — why databases use them (crossover to HLD) 🔴
- [ ] LSM tree vs B-tree write/read amplification 🔴

## 2.6 Heaps & Priority Queues 🔴
- [ ] Binary heap: array representation, sift up/down, build-heap O(n)
- [ ] `PriorityQueue` in Java: min-heap default, custom comparators, no O(1) update
- [ ] Top-K elements, K-th largest, K closest points
- [ ] Merge K sorted lists/arrays
- [ ] Two-heap pattern: median of a stream, IPO/scheduling problems 🔴
- [ ] Heap + hashmap for decrease-key simulation (Dijkstra in Java)
- [ ] Task scheduler, meeting rooms II, CPU scheduling
- [ ] Quickselect as heap alternative for K-th element (O(n) average)
- [ ] Indexed priority queue, Fibonacci heap (concept only) 🟢

## 2.7 Graphs 🔴
- [ ] Representations: adjacency list, adjacency matrix, edge list; when each wins
- [ ] Directed vs undirected, weighted vs unweighted, DAG, multigraph
- [ ] BFS: shortest path in unweighted graph, level tracking, multi-source BFS 🔴
- [ ] DFS: recursive and iterative, visited sets, path tracking
- [ ] Grid as graph: islands, flood fill, rotting oranges, word search, shortest path in maze 🔴
- [ ] Cycle detection: undirected (union-find / DFS parent), directed (DFS colors / Kahn)
- [ ] Topological sort: DFS-based and Kahn's algorithm; course schedule family 🔴
- [ ] Connected components, strongly connected components (Tarjan/Kosaraju) 🟡
- [ ] Bipartite check / graph coloring
- [ ] Union-Find (DSU): path compression, union by rank, complexity α(n) 🔴
- [ ] Dijkstra: implementation with PQ, why it fails on negative edges 🔴
- [ ] Bellman-Ford, negative cycle detection 🟡
- [ ] Floyd-Warshall all-pairs 🟡
- [ ] A* search 🟢
- [ ] Minimum spanning tree: Kruskal (with DSU), Prim 🟡
- [ ] Bridges & articulation points 🟢
- [ ] Max flow / min cut (Ford-Fulkerson concept) 🟢
- [ ] 0-1 BFS (deque) 🟢
- [ ] Bidirectional BFS 🟢
- [ ] Graph problems disguised as something else (word ladder, alien dictionary, evaluate division)

## 2.8 Specialized & Advanced Structures 🟡
- [ ] Disjoint set with rollback 🟢
- [ ] Sparse table / range minimum query 🟢
- [ ] Suffix array / suffix automaton 🟢
- [ ] Interval tree, ordered map for interval merge
- [ ] Ordered statistics tree / `TreeMap` for rank queries
- [ ] Circular buffer, ring buffer (Disruptor concept)
- [ ] Immutable/persistent data structures 🟢
- [ ] Concurrent data structures (crossover to Java roadmap Part 3)

---
---

# PART 3 — ALGORITHMS & TECHNIQUES 🔴

## 3.1 Sorting & Searching 🔴
- [ ] Comparison sorts: bubble/insertion/selection (know when insertion wins), merge, quick, heap
- [ ] Quicksort: pivot strategies, worst case, in-place partition; quickselect
- [ ] Merge sort: stability, external merge sort for data > memory 🔴
- [ ] Heapsort: in-place, not stable
- [ ] Non-comparison: counting sort, radix sort, bucket sort — when applicable
- [ ] TimSort: runs, galloping, why Java uses it for objects
- [ ] Stability: what it means and when it matters
- [ ] Sorting with custom comparators; multi-key sort; `Comparator` chaining in Java
- [ ] The `IllegalArgumentException: Comparison method violates its general contract` trap 🔴
- [ ] Binary search: exact, first/last occurrence, lower/upper bound, rotated array, 2D matrix
- [ ] Binary search on the answer (min capacity / max distance / Koko eating bananas) 🔴
- [ ] Ternary search 🟢
- [ ] Search in infinite/unbounded array
- [ ] Overflow-safe mid: `lo + (hi - lo) / 2` 🔴

## 3.2 Recursion, Backtracking & Bitmask 🔴
- [ ] Recursion mechanics: base case, recursive case, call stack, tail recursion (no TCO in Java)
- [ ] Converting recursion to iteration with explicit stack
- [ ] Subsets/power set (iterative, recursive, bitmask)
- [ ] Permutations (with and without duplicates)
- [ ] Combinations, combination sum family
- [ ] N-Queens, Sudoku solver, word search, rat in maze
- [ ] Palindrome partitioning
- [ ] Pruning strategies; why pruning is the actual interview signal
- [ ] Bit manipulation: AND/OR/XOR/NOT, shifts, masks
- [ ] XOR tricks: single number, missing number, swap without temp
- [ ] Bit counting (`Integer.bitCount`, Brian Kernighan), lowest set bit `n & -n`
- [ ] Power of two check, set/clear/toggle bit
- [ ] Bitmask DP / subset enumeration 🟡
- [ ] `Integer`/`Long` bit methods in Java, `BitSet`

## 3.3 Dynamic Programming 🔴
- [ ] Identifying DP: optimal substructure + overlapping subproblems
- [ ] Memoization (top-down) vs tabulation (bottom-up); converting between them
- [ ] State definition — the hardest part; practice articulating `dp[i][j] means ...` 🔴
- [ ] Space optimization: rolling arrays, 1D from 2D
- [ ] **1D DP:** climbing stairs, house robber, decode ways, jump game, LIS (O(n²) and O(n log n))
- [ ] **Knapsack family:** 0/1, unbounded, subset sum, partition equal subset, target sum, coin change (min coins + count ways) 🔴
- [ ] **String DP:** edit distance, LCS, longest palindromic subsequence/substring, regex/wildcard matching, distinct subsequences 🔴
- [ ] **Grid DP:** unique paths, min path sum, maximal square, dungeon game
- [ ] **Interval DP:** matrix chain multiplication, burst balloons, stone game
- [ ] **Tree DP:** house robber III, tree diameter, max path sum
- [ ] **Bitmask DP:** TSP, assignment problems 🟡
- [ ] **Digit DP** 🟢
- [ ] **DP on stocks:** all 6 variants (1, 2, k transactions, cooldown, fee, unlimited) 🔴
- [ ] **Game theory DP:** minimax, Nim 🟢
- [ ] Recognizing when greedy beats DP (and proving it)

## 3.4 Greedy & Intervals 🔴
- [ ] Greedy choice property & exchange argument proofs
- [ ] Activity selection / non-overlapping intervals
- [ ] Merge intervals, insert interval, interval intersection 🔴
- [ ] Meeting rooms I & II (sweep line + heap)
- [ ] Minimum platforms / max concurrent events (sweep line) 🔴
- [ ] Jump game, gas station, candy distribution
- [ ] Huffman coding
- [ ] Fractional knapsack
- [ ] Scheduling with deadlines/profits
- [ ] Sweep line & event sorting as a general technique 🔴

## 3.5 Math & Miscellaneous 🟡
- [ ] GCD/LCM, Euclid's algorithm, extended Euclid
- [ ] Primes: sieve of Eratosthenes, primality test, prime factorization
- [ ] Modular arithmetic, fast exponentiation, modular inverse
- [ ] Combinatorics: nCr, Pascal's triangle, Catalan numbers
- [ ] Probability & expected value problems 🟢
- [ ] Reservoir sampling 🟡
- [ ] Fisher-Yates shuffle 🔴
- [ ] Random number generation, weighted random pick, random pick with blacklist
- [ ] Overflow handling: `Math.addExact`, using `long`, `BigInteger`
- [ ] Number-to-string, string-to-number (atoi) with all edge cases
- [ ] Base conversion, roman numerals, excel column
- [ ] Matrix operations, matrix exponentiation 🟢
- [ ] Geometry basics: points, lines, orientation, convex hull 🟢
- [ ] Bit-level tricks for performance

## 3.6 Streaming, Large-Data & System-Flavored Algorithms 🔴
*(These bridge DSA and system design — high signal at senior level)*
- [ ] External sort (sort 100GB with 1GB RAM) 🔴
- [ ] Top-K over a stream (heap + count-min sketch)
- [ ] Distinct count over a stream (HyperLogLog)
- [ ] Membership over a huge set (Bloom filter)
- [ ] Median of a stream (two heaps)
- [ ] Moving average / sliding window aggregates over a stream
- [ ] Rate limiter algorithms: token bucket, leaky bucket, fixed window, sliding window log, sliding window counter 🔴
- [ ] LRU / LFU / TinyLFU cache implementation 🔴
- [ ] Consistent hashing with virtual nodes 🔴
- [ ] Distributed unique ID generation (Snowflake, UUIDv7, ULID) 🔴
- [ ] Deduplication at scale
- [ ] MapReduce-style thinking: word count, join, aggregation
- [ ] Sharding a hot key
- [ ] Sampling strategies for telemetry

---
---

# PART 4 — PATTERN → PROBLEM CATALOG 🔴

> Practice by **pattern**, not by random problem. Target: recognize the pattern in <60 seconds.

## 4.1 The 20 Patterns 🔴
- [ ] 1. Two Pointers ⏱
- [ ] 2. Sliding Window (fixed & variable) ⏱
- [ ] 3. Fast & Slow Pointers ⏱
- [ ] 4. Merge Intervals ⏱
- [ ] 5. Cyclic Sort / index-as-hash ⏱
- [ ] 6. In-place Linked List Reversal ⏱
- [ ] 7. BFS (tree + graph + grid) ⏱
- [ ] 8. DFS / Backtracking ⏱
- [ ] 9. Two Heaps ⏱
- [ ] 10. Subsets / Combinations / Permutations ⏱
- [ ] 11. Modified Binary Search ⏱
- [ ] 12. Top-K Elements (heap / quickselect) ⏱
- [ ] 13. K-way Merge ⏱
- [ ] 14. Monotonic Stack / Deque ⏱
- [ ] 15. Prefix Sum / Difference Array ⏱
- [ ] 16. Union-Find ⏱
- [ ] 17. Topological Sort ⏱
- [ ] 18. Trie ⏱
- [ ] 19. Dynamic Programming (by sub-family) ⏱
- [ ] 20. Greedy + Sweep Line ⏱

## 4.2 Must-Solve Problem List (Blind-75 / NeetCode-150 core) 🔴
Mark done only when solved **from scratch in ≤35 min without hints**, twice, ≥1 week apart.

### Arrays & Hashing
- [ ] Two Sum · Contains Duplicate · Valid Anagram · Group Anagrams
- [ ] Top K Frequent Elements · Product of Array Except Self
- [ ] Longest Consecutive Sequence · Encode/Decode Strings
- [ ] Subarray Sum Equals K · Maximum Subarray (Kadane)

### Two Pointers & Sliding Window
- [ ] Valid Palindrome · 3Sum · Container With Most Water · Trapping Rain Water
- [ ] Longest Substring Without Repeating Characters · Longest Repeating Character Replacement
- [ ] Minimum Window Substring · Permutation in String · Sliding Window Maximum

### Stack
- [ ] Valid Parentheses · Min Stack · Evaluate RPN · Generate Parentheses
- [ ] Daily Temperatures · Car Fleet · Largest Rectangle in Histogram

### Binary Search
- [ ] Binary Search · Search 2D Matrix · Koko Eating Bananas
- [ ] Search in Rotated Sorted Array · Find Minimum in Rotated Sorted Array
- [ ] Time Based Key-Value Store · Median of Two Sorted Arrays

### Linked List
- [ ] Reverse Linked List · Merge Two Sorted Lists · Reorder List
- [ ] Remove Nth Node · Copy List with Random Pointer · Add Two Numbers
- [ ] Linked List Cycle (+ find start) · Find Duplicate Number · LRU Cache · Merge K Sorted Lists

### Trees
- [ ] Invert Binary Tree · Max Depth · Diameter · Balanced Binary Tree · Same Tree · Subtree
- [ ] LCA of BST · Level Order Traversal · Right Side View
- [ ] Count Good Nodes · Validate BST · Kth Smallest in BST
- [ ] Construct Tree from Preorder+Inorder · Binary Tree Max Path Sum · Serialize/Deserialize

### Tries
- [ ] Implement Trie · Design Add and Search Words · Word Search II

### Heap / Priority Queue
- [ ] Kth Largest in Stream · Last Stone Weight · K Closest Points
- [ ] Kth Largest Element in Array · Task Scheduler · Design Twitter · Find Median from Data Stream

### Backtracking
- [ ] Subsets (+ II) · Combination Sum (+ II) · Permutations (+ II)
- [ ] Word Search · Palindrome Partitioning · Letter Combinations · N-Queens

### Graphs
- [ ] Number of Islands · Clone Graph · Max Area of Island · Pacific Atlantic
- [ ] Surrounded Regions · Rotting Oranges · Course Schedule (+ II)
- [ ] Redundant Connection · Number of Connected Components · Word Ladder
- [ ] Alien Dictionary · Network Delay Time · Cheapest Flights K Stops · Swim in Rising Water

### Dynamic Programming
- [ ] Climbing Stairs · Min Cost Climbing Stairs · House Robber (+ II)
- [ ] Longest Palindromic Substring · Palindromic Substrings · Decode Ways
- [ ] Coin Change (+ II) · Maximum Product Subarray · Word Break · Longest Increasing Subsequence
- [ ] Partition Equal Subset Sum · Unique Paths · Longest Common Subsequence
- [ ] Best Time to Buy/Sell Stock with Cooldown · Target Sum · Interleaving String
- [ ] Edit Distance · Burst Balloons · Regular Expression Matching

### Greedy & Intervals
- [ ] Maximum Subarray · Jump Game (+ II) · Gas Station · Hand of Straights
- [ ] Merge Intervals · Insert Interval · Non-overlapping Intervals · Meeting Rooms (+ II)

### Math & Bit
- [ ] Single Number · Number of 1 Bits · Counting Bits · Reverse Bits
- [ ] Missing Number · Sum of Two Integers · Rotate Image · Spiral Matrix · Set Matrix Zeroes · Pow(x,n)

## 4.3 Senior-Flavored Coding Problems 🔴
*(more common at 10 YOE than pure LeetCode-hard)*
- [ ] Implement an LRU cache with TTL
- [ ] Implement a thread-safe bounded blocking queue
- [ ] Implement a rate limiter (token bucket) — single node, then distributed
- [ ] Implement a simple in-memory key-value store with expiry
- [ ] Implement a retry with exponential backoff + jitter
- [ ] Implement a circuit breaker state machine
- [ ] Implement a connection pool
- [ ] Implement an event bus / pub-sub with topic filtering
- [ ] Implement a job scheduler with priorities and delays
- [ ] Implement a file-system tree with path resolution
- [ ] Implement a simple JSON/CSV parser
- [ ] Implement a versioned key-value store (time-travel reads)
- [ ] Implement a snapshot/undo (memento) for an editor
- [ ] Implement dependency resolution (topological sort in disguise)
- [ ] Implement a sharded counter / distributed counter simulation
- [ ] Implement a producer-consumer pipeline with backpressure
- [ ] Implement an object pool with idle eviction
- [ ] Parse and evaluate an expression / rule engine

---
---

# PART 5 — JAVA FOR CODING ROUNDS 🔴

## 5.1 Speed & Idiom Fluency
- [ ] `List`/`Map`/`Set` creation, `List.of`, `new ArrayList<>(List.of(...))` mutability trap
- [ ] `Map.getOrDefault`, `computeIfAbsent`, `merge` for counting 🔴
- [ ] `PriorityQueue` with comparator lambdas; max-heap via `Comparator.reverseOrder()`
- [ ] `TreeMap` navigation methods for range problems
- [ ] `Deque` as stack and queue
- [ ] `Arrays.sort` with comparator; sorting `int[][]` by column
- [ ] `Collections.sort` vs `list.sort`
- [ ] Streams when they help and when they hurt readability in an interview
- [ ] `StringBuilder` reverse/append/deleteCharAt/setCharAt
- [ ] `char` arithmetic: `c - 'a'`, frequency arrays of size 26
- [ ] `Integer.MAX_VALUE`/`MIN_VALUE`, overflow avoidance
- [ ] `long` vs `int` decisions
- [ ] 2D array init: `new int[n][m]`, `Arrays.fill`, `Arrays.deepToString` for debugging
- [ ] Records/inner classes for tuples; `int[]` as a lightweight pair
- [ ] `Objects.equals`/`hash` for custom keys
- [ ] Iterating `Map.entrySet` cleanly
- [ ] Writing a `Comparator` that doesn't overflow (`Integer.compare`, not `a - b`) 🔴

## 5.2 Interview-Specific Java Traps 🔴
- [ ] `Integer` caching and `==` comparison
- [ ] Autoboxing in hot loops
- [ ] `ArrayList.remove(int)` vs `remove(Object)` overload ambiguity
- [ ] Modifying a collection during iteration → `ConcurrentModificationException`
- [ ] `Arrays.asList` fixed-size
- [ ] `PriorityQueue` iteration order is not sorted
- [ ] `HashMap` iteration order is not insertion order
- [ ] Integer division truncation and negative modulo
- [ ] String `==` vs `equals` with interning
- [ ] Recursion depth → `StackOverflowError` (~10k frames)
- [ ] Mutable objects as `HashMap` keys

## 5.3 Writing Interview-Quality Code 🔴
- [ ] Meaningful names even under time pressure
- [ ] Extract helper methods rather than nesting 4 levels
- [ ] Guard clauses for edge cases at the top
- [ ] No premature micro-optimization; correctness first
- [ ] Comments only where the *why* isn't obvious
- [ ] Explicit input validation discussion (even if not coded)
- [ ] Testability: pure functions, injectable dependencies
- [ ] Say what you'd add in production (logging, metrics, error handling) — big senior signal 🔴

---
---

# PART 6 — LOW-LEVEL DESIGN (OOD) 🔴

## 6.1 LLD Interview Framework 🔴
- [ ] **1. Clarify scope (5 min):** which features are in, which are explicitly out; single-machine vs distributed; scale hints; who are the actors
- [ ] **2. Use cases / user stories:** list 5–8, get agreement on the core 3
- [ ] **3. Identify entities:** nouns → classes; distinguish entity / value object / service
- [ ] **4. Define relationships:** association, aggregation, composition, inheritance; multiplicities
- [ ] **5. Define interfaces & responsibilities:** one responsibility per class, name the abstractions
- [ ] **6. Apply patterns where they earn their place** — and say why, and what you rejected
- [ ] **7. Core class diagram** on the whiteboard
- [ ] **8. Code the critical 2–3 classes** with real method signatures
- [ ] **9. Concurrency & consistency:** what's shared, what's locked, what's idempotent
- [ ] **10. Extensibility:** "how would you add X?" — answer before they ask
- [ ] **11. Trade-offs & alternatives** summary

## 6.2 OOD Principles Under Pressure 🔴
- [ ] SOLID applied concretely (not recited) — be ready to point at your own diagram and name where each applies
- [ ] Composition over inheritance; showing where inheritance would break LSP
- [ ] Encapsulation & invariants; who is allowed to mutate what
- [ ] Interface segregation for plugin points
- [ ] Dependency inversion for testability (injecting the clock, the repository, the notifier)
- [ ] Immutability for value objects & thread safety
- [ ] Law of Demeter and avoiding train-wreck code
- [ ] Cohesion & coupling as the explicit vocabulary you use out loud
- [ ] Modeling state machines explicitly instead of boolean soup
- [ ] Avoiding god objects, anemic models, and over-abstraction

## 6.3 Pattern Toolkit for LLD 🔴
*(be able to justify + code each in <10 min)*
- [ ] Strategy — pricing rules, payment methods, parking fee calculation
- [ ] Factory / Abstract Factory — object creation by type
- [ ] Builder — complex object construction, ordering
- [ ] Singleton — and when to say "no, I'd inject it"
- [ ] Observer — notifications, event publishing
- [ ] State — order lifecycle, elevator states, vending machine
- [ ] Command — undo/redo, remote control, task queue
- [ ] Chain of Responsibility — approval flows, middleware
- [ ] Decorator — pizza toppings, coffee add-ons, stream wrapping
- [ ] Template Method — algorithm skeletons
- [ ] Adapter — third-party integration
- [ ] Composite — file system, menu trees, org charts
- [ ] Proxy — lazy loading, access control
- [ ] Repository + Unit of Work — persistence abstraction
- [ ] Facade — simplifying a subsystem
- [ ] Null Object — avoiding null checks
- [ ] Visitor / sealed + pattern matching — operations over a type hierarchy
- [ ] Flyweight — shared immutable state at scale
- [ ] Mediator — chat room, air traffic control
- [ ] Publish-Subscribe / Event Bus

## 6.4 Concurrency in LLD Answers 🔴
- [ ] Identify shared mutable state explicitly
- [ ] Choose: immutability > confinement > concurrent collection > lock
- [ ] `ConcurrentHashMap` + `computeIfAbsent` vs synchronized block
- [ ] Optimistic (`@Version`/CAS) vs pessimistic locking choice
- [ ] Atomic counters, `LongAdder` for hot counters
- [ ] Lock granularity: per-resource locks (per parking spot, per seat, per account)
- [ ] Deadlock avoidance by lock ordering (transfer between two accounts) 🔴
- [ ] Idempotency for retried operations (booking, payment)
- [ ] Double-booking prevention: DB unique constraint vs distributed lock vs optimistic version 🔴
- [ ] Thread-safe singleton (holder idiom / enum)
- [ ] Bounded queues and backpressure in producer-consumer designs

## 6.5 LLD Problem Catalog 🔴
Solve each end-to-end: requirements → classes → diagram → key code → concurrency → extensions.

### Tier 1 — most frequently asked 🔴
- [ ] Parking Lot ⏱
- [ ] Elevator / Lift System ⏱
- [ ] Vending Machine ⏱
- [ ] ATM ⏱
- [ ] Library Management System ⏱
- [ ] Tic-Tac-Toe / Chess ⏱
- [ ] Splitwise (expense sharing) ⏱
- [ ] BookMyShow / Movie ticket booking (seat locking!) ⏱
- [ ] Rate Limiter ⏱
- [ ] LRU Cache (as a design, not just code) ⏱

### Tier 2 — common 🟡
- [ ] Snake & Ladder / Deck of Cards
- [ ] Food delivery (Swiggy/Zomato) order flow
- [ ] Cab booking (Uber/Ola) matching
- [ ] Hotel booking / inventory reservation
- [ ] Online shopping cart & checkout
- [ ] Notification service (multi-channel, templates, retries)
- [ ] Logging framework (levels, appenders, async)
- [ ] In-memory key-value store with TTL
- [ ] File system (directories, files, search)
- [ ] Task/Job scheduler (cron-like)
- [ ] Amazon locker system
- [ ] Traffic signal control system
- [ ] Airline reservation / seat allocation
- [ ] Meeting room scheduler / calendar
- [ ] Stack Overflow / Q&A system
- [ ] Restaurant table reservation

### Tier 3 — differentiators 🟢
- [ ] Payment gateway abstraction (multiple PSPs, idempotency, webhooks)
- [ ] Order management state machine with sagas
- [ ] Rule engine / discount & promotion engine
- [ ] Workflow engine (steps, retries, compensation)
- [ ] Feature flag system
- [ ] Audit logging framework
- [ ] Multi-tenant configuration service
- [ ] Distributed lock abstraction
- [ ] Circuit breaker library
- [ ] Connection pool
- [ ] ORM/query builder mini-design
- [ ] CSV/JSON parser & serializer
- [ ] Text editor with undo/redo & versioning
- [ ] Spreadsheet with formula dependency graph
- [ ] Search autocomplete (trie-backed) as an LLD

## 6.6 Common LLD Mistakes to Avoid 🔴
- [ ] Jumping to classes before clarifying requirements
- [ ] Designing for imaginary future requirements (over-engineering)
- [ ] Pattern-dropping without justification
- [ ] Ignoring concurrency entirely in a booking/inventory problem 🔴
- [ ] Anemic classes with only getters/setters
- [ ] Not mentioning persistence at all
- [ ] Not handling money/currency correctly (`double` for money) 🔴
- [ ] No discussion of error handling or validation
- [ ] Silence while thinking
- [ ] Running out of time because you gold-plated the class diagram

---
---

# PART 7 — MACHINE CODING ROUND 🟡

## 7.1 Format & Expectations
- [ ] 90–180 minutes, working code, usually no external DB (in-memory), no UI
- [ ] Evaluated on: working demo, code structure, OOP quality, extensibility, tests, naming, git hygiene
- [ ] Deliverable: runnable via `main` or tests, plus a README

## 7.2 Execution Checklist 🔴
- [ ] Read the problem twice; list the *must-have* commands/features
- [ ] Timebox: 15% design, 60% core, 15% tests, 10% polish
- [ ] Package structure: `model`, `service`, `repository`, `exception`, `util`, `controller/cli`
- [ ] In-memory repositories behind interfaces
- [ ] Constructor injection everywhere (no statics, no singletons)
- [ ] Custom exceptions with meaningful messages
- [ ] Input validation at boundaries
- [ ] Enums for fixed sets; state machines for lifecycle
- [ ] Money as `BigDecimal` or long-minor-units 🔴
- [ ] Thread safety if the problem hints at concurrency
- [ ] At least 5–8 meaningful unit tests (happy + edge)
- [ ] `README.md`: how to run, assumptions, design decisions, what's out of scope 🔴
- [ ] Working demo path prioritized over completeness

## 7.3 Practice Problems ⏱
- [ ] Splitwise (with settlement simplification)
- [ ] Parking lot with pricing strategies
- [ ] Snake & ladder simulation
- [ ] Ride-sharing matching service
- [ ] Task management / to-do with priorities & tags
- [ ] Inventory management with reservations
- [ ] Cricket/game scoreboard simulation
- [ ] Elevator simulation with scheduling algorithm
- [ ] Book/library system with holds and fines
- [ ] Distributed-cache-like in-memory store with eviction policies

---
---

# PART 8 — SYSTEM DESIGN BUILDING BLOCKS 🔴

## 8.1 The Framework (use this literally) 🔴
- [ ] **1. Requirements (5–8 min)**
  - [ ] Functional: list them, get the interviewer to prioritize the top 3
  - [ ] Non-functional: scale (DAU, QPS, data size), latency SLO, availability target, consistency needs, read:write ratio, retention, geography
  - [ ] Explicit out-of-scope statement
- [ ] **2. Capacity estimation (3–5 min)** — QPS, storage/day & /5yr, bandwidth, memory for cache
- [ ] **3. API design (5 min)** — the 4–6 endpoints/events that matter, with request/response shape
- [ ] **4. Data model (5 min)** — entities, keys, access patterns, DB choice with justification
- [ ] **5. High-level architecture (10 min)** — boxes and arrows, request flow narrated end-to-end
- [ ] **6. Deep dives (15–20 min)** — interviewer picks, or you offer the 2 hardest parts
- [ ] **7. Bottlenecks, failure modes, scaling** — what breaks at 10×
- [ ] **8. Trade-offs & wrap-up** — what you'd do differently with more time/money

## 8.2 Core Components — know cold 🔴
- [ ] Load balancer: L4 vs L7, algorithms, health checks, sticky sessions, SSL termination
- [ ] Reverse proxy / API gateway: auth, rate limit, routing, aggregation, transformation
- [ ] CDN: edge caching, cache keys, invalidation, origin shield, static vs dynamic
- [ ] DNS: resolution, TTL, GeoDNS, anycast, failover
- [ ] Application servers: stateless design, horizontal scaling, session handling
- [ ] Caches: local vs distributed, layers, patterns, eviction, stampede protection
- [ ] Databases: SQL vs NoSQL choice, replication, sharding, indexes
- [ ] Message queues & streams: broker choice, ordering, retention, consumer groups
- [ ] Object storage: blobs, presigned URLs, lifecycle, CDN in front
- [ ] Search index: inverted index, relevance, near-real-time indexing
- [ ] Job/batch systems: schedulers, workers, idempotency, dead letters
- [ ] Coordination services: ZooKeeper/etcd, leader election, config, locks
- [ ] Rate limiter (distributed): Redis-based token bucket, sliding window
- [ ] ID generation: Snowflake, UUIDv7, ULID, DB sequences — trade-offs 🔴
- [ ] Service discovery & service mesh
- [ ] Notification/push infrastructure (APNs/FCM, email, SMS)
- [ ] Analytics pipeline: events → stream → warehouse → dashboards
- [ ] Feature flags & config service
- [ ] Observability stack (metrics, logs, traces)

## 8.3 Cross-Cutting Design Concerns 🔴
- [ ] Read vs write path separation; CQRS & read models
- [ ] Sync vs async: what can be deferred to a queue
- [ ] Consistency choice per feature (strong for money, eventual for feed)
- [ ] Idempotency keys on all mutating endpoints 🔴
- [ ] Retries + backoff + jitter, and their interaction with idempotency
- [ ] Timeouts & timeout budgets across hops
- [ ] Circuit breakers & bulkheads
- [ ] Backpressure & load shedding
- [ ] Hot key / hot partition handling (celebrity problem) 🔴
- [ ] Fan-out on write vs fan-out on read (feed problem) 🔴
- [ ] Pagination & cursoring at scale
- [ ] Multi-region: active-active vs active-passive, data residency, conflict resolution
- [ ] Zero-downtime migration & backfill strategy 🔴
- [ ] Cost awareness: storage tiering, egress, over-provisioning 🔴
- [ ] Security: authN/authZ, encryption, secrets, tenant isolation
- [ ] Observability: what you'd instrument and alert on
- [ ] Testing strategy for the design (load tests, chaos, canary)

## 8.4 Scale Numbers Every Engineer Should Know 🔴
- [ ] L1 cache ~1 ns · L2 ~4 ns · RAM ~100 ns
- [ ] SSD random read ~100 µs · disk seek ~10 ms
- [ ] Same-DC round trip ~0.5 ms · cross-region ~50–150 ms
- [ ] 1 Gbps ≈ 125 MB/s
- [ ] Single Postgres node: ~5–15k simple QPS; single Redis node: ~100k+ ops/s
- [ ] Single Kafka broker: ~100k+ msgs/s
- [ ] Typical web server: ~1–10k RPS depending on work per request
- [ ] 1M requests/day ≈ 12 QPS average; peak is 2–10× average 🔴
- [ ] 1 KB × 1M/day ≈ 1 GB/day ≈ 365 GB/year
- [ ] Availability: 99.9% = 8.7h/yr, 99.99% = 52min/yr, 99.999% = 5min/yr 🔴

---
---

# PART 9 — SYSTEM DESIGN PROBLEM CATALOG 🔴

> For each: requirements → estimation → API → data model → architecture → 2 deep dives → failure modes.
> Do them **timed (45 min)** and **out loud**.

## 9.1 Tier 1 — Classic, highest frequency 🔴
- [ ] URL Shortener (TinyURL) ⏱ — ID generation, redirect latency, analytics
- [ ] Rate Limiter (distributed) ⏱ — algorithms, Redis, race conditions, per-user/per-IP
- [ ] Pastebin / text storage ⏱ — blob storage, expiry, access control
- [ ] Web Crawler ⏱ — politeness, dedup, frontier, DNS, distributed coordination
- [ ] Twitter/X Timeline ⏱ — fan-out on write vs read, celebrity problem, caching
- [ ] Instagram/Photo sharing ⏱ — media pipeline, CDN, feed, storage
- [ ] WhatsApp/Chat system ⏱ — connection management, delivery receipts, ordering, offline, E2E
- [ ] Notification System ⏱ — multi-channel, templates, retries, DLQ, preferences, throttling
- [ ] Design a Key-Value Store ⏱ — consistent hashing, replication, quorum, gossip, CAP
- [ ] Design a Distributed Cache ⏱ — sharding, eviction, hot keys, invalidation

## 9.2 Tier 2 — Very common 🔴
- [ ] News Feed / Timeline (generic ranking + delivery)
- [ ] YouTube / Netflix (upload, transcode, ABR streaming, CDN, recommendations)
- [ ] Uber / Ride-sharing (geospatial index, matching, ETA, surge, tracking)
- [ ] Food delivery (Swiggy/DoorDash) — order lifecycle, dispatch, tracking
- [ ] Ticketmaster / BookMyShow — seat inventory, holds, high-contention writes 🔴
- [ ] E-commerce checkout & inventory reservation — oversell prevention 🔴
- [ ] Payment system — idempotency, ledger, reconciliation, PSP integration, double-entry 🔴
- [ ] Search autocomplete / typeahead — trie, ranking, personalization
- [ ] Search engine (basic) — crawling, indexing, ranking, serving
- [ ] Google Drive / Dropbox — chunking, dedup, sync, conflict resolution, metadata service
- [ ] Google Docs / collaborative editor — OT vs CRDT, presence, cursors
- [ ] Distributed Job Scheduler — cron at scale, leader election, exactly-once execution
- [ ] Metrics & Monitoring system — ingestion, TSDB, downsampling, alerting
- [ ] Log aggregation & search system
- [ ] Ad click aggregation / real-time analytics — streaming, dedup, late data, exactly-once
- [ ] Leaderboard / gaming ranking — Redis sorted sets, sharding, ties
- [ ] Online code judge / CI runner — sandboxing, queueing, resource limits
- [ ] API Gateway / reverse proxy
- [ ] Distributed message queue (design Kafka)
- [ ] Object storage (design S3)

## 9.3 Tier 3 — Senior/staff differentiators 🟡
- [ ] Multi-tenant SaaS platform — isolation models, noisy neighbor, per-tenant scaling & cost 🔴
- [ ] Feature flag & experimentation (A/B) platform
- [ ] Fraud detection pipeline (streaming rules + ML scoring)
- [ ] Recommendation system architecture (candidate gen → ranking → serving)
- [ ] Data warehouse / analytics platform (CDC → lake → warehouse → BI)
- [ ] Workflow / orchestration engine (Temporal-like: durable execution)
- [ ] Consent & privacy platform (GDPR deletion across services)
- [ ] Audit & compliance logging platform
- [ ] Billing & subscription system (proration, invoicing, dunning, tax)
- [ ] Content moderation pipeline
- [ ] IoT telemetry ingestion at scale
- [ ] Real-time bidding / low-latency auction
- [ ] Global config/secret distribution
- [ ] Migration design: monolith → microservices for a named domain 🔴
- [ ] Migration design: on-prem → cloud, or DB engine change with zero downtime 🔴
- [ ] Design your own current system, but 100× the traffic 🔴

## 9.4 Deep-Dive Questions You Must Have Answers For 🔴
- [ ] "How do you prevent double booking / overselling?" (3 approaches with trade-offs)
- [ ] "How do you make this idempotent?"
- [ ] "What happens when this service is down?"
- [ ] "How do you handle a hot key / celebrity user?"
- [ ] "How do you shard this? What's the shard key and why?"
- [ ] "How do you re-shard without downtime?"
- [ ] "How do you keep the cache and DB consistent?"
- [ ] "How do you handle duplicate messages from the queue?"
- [ ] "How do you guarantee ordering?"
- [ ] "What's your p99 and where does it come from?"
- [ ] "How would you migrate this schema with zero downtime?"
- [ ] "How does this behave in a network partition?"
- [ ] "What's the cost of this design per month?"
- [ ] "What would you monitor and alert on?"
- [ ] "What's the blast radius of a bad deploy here?"

---
---

# PART 10 — DEEP-DIVE SUBSYSTEMS 🔴

## 10.1 Databases in Design Interviews 🔴
- [ ] SQL vs NoSQL decision framework — lead with access patterns, not preference
- [ ] Normalization vs denormalization for read performance
- [ ] Index design for the queries you named; composite index column order
- [ ] Read replicas & replication lag; read-your-own-writes strategies
- [ ] Sharding: key choice, range vs hash vs directory, resharding, cross-shard queries/joins 🔴
- [ ] Hot partition mitigation: salting, sub-sharding, request coalescing
- [ ] Multi-master conflicts & resolution
- [ ] Transactions across shards → saga / outbox 🔴
- [ ] Isolation levels & anomalies (write skew in booking systems) 🔴
- [ ] Optimistic vs pessimistic locking for contention (seat booking, inventory) 🔴
- [ ] Connection pool sizing at scale
- [ ] Schema evolution & zero-downtime migration (expand/contract) 🔴
- [ ] Time-series & append-only data modeling; partitioning by time
- [ ] Ledger design: double-entry, immutability, reconciliation 🟡
- [ ] Choosing Postgres vs MySQL vs DynamoDB vs Cassandra vs Mongo — one-sentence justification each

## 10.2 SQL Round Prep 🔴
- [ ] Joins including self-join and anti-join patterns
- [ ] Aggregation with `GROUP BY` / `HAVING`
- [ ] Window functions: running totals, rank per group, top-N per group, LAG/LEAD deltas 🔴
- [ ] CTEs and recursive CTEs (org hierarchy, path traversal)
- [ ] Date/time bucketing, cohort analysis, retention queries
- [ ] Deduplication queries (`ROW_NUMBER` + partition)
- [ ] Gaps & islands problems
- [ ] Pivoting/unpivoting
- [ ] `EXISTS` vs `IN` vs `JOIN`
- [ ] NULL handling pitfalls
- [ ] Reading `EXPLAIN ANALYZE` and proposing an index 🔴
- [ ] Writing an upsert
- [ ] Query rewriting for performance
- [ ] Practice sets: LeetCode SQL 50, StrataScratch, DataLemur

## 10.3 Caching 🔴
- [ ] Where to cache: client, CDN, gateway, app-local, distributed, DB
- [ ] Patterns: cache-aside, read-through, write-through, write-behind, refresh-ahead
- [ ] Eviction: LRU, LFU, TinyLFU, TTL + jitter
- [ ] Invalidation strategies & the versioned-key trick
- [ ] Stampede/thundering herd: locking, early recompute, request coalescing 🔴
- [ ] Penetration (caching negatives, bloom filter), avalanche (TTL jitter)
- [ ] Consistency: cache-then-DB vs DB-then-cache ordering, delete-vs-update 🔴
- [ ] Hot key mitigation: local L1 + replicated keys
- [ ] Sizing: working set, hit ratio targets, memory math
- [ ] Redis specifics: data structures, pipelining, Lua atomicity, cluster slots, persistence, eviction policy

## 10.4 Messaging & Streaming in Design 🔴
- [ ] When to introduce a queue at all (decoupling, buffering, retries, fan-out)
- [ ] Queue vs stream (log) semantics
- [ ] Ordering guarantees & partition key selection 🔴
- [ ] Consumer scaling & lag management
- [ ] Delivery semantics and idempotent consumers 🔴
- [ ] Outbox pattern for atomic DB-write + publish 🔴
- [ ] DLQ design, poison messages, retry topics
- [ ] Schema evolution & compatibility for events
- [ ] Backpressure & flow control
- [ ] Exactly-once vs effectively-once framing in an interview
- [ ] Event-driven choreography vs orchestration; saga design 🔴

## 10.5 Networking & Protocols in Design 🟡
- [ ] HTTP/1.1 vs HTTP/2 vs HTTP/3 trade-offs
- [ ] Long polling vs SSE vs WebSocket vs gRPC streaming — choose for chat/notifications 🔴
- [ ] Connection limits, keep-alive, connection pooling at scale
- [ ] Load balancer behavior with long-lived connections
- [ ] TLS termination & mTLS placement
- [ ] Idempotent retries at the HTTP layer
- [ ] gRPC vs REST for internal services
- [ ] Latency budget breakdown across hops 🔴

## 10.6 Storage & Files 🟡
- [ ] Blob storage design: chunking, multipart upload, resumable uploads
- [ ] Deduplication (content-addressed storage)
- [ ] Presigned URLs & direct-to-storage upload (offloading your servers) 🔴
- [ ] Media pipeline: transcode, thumbnails, async processing
- [ ] Storage tiering & lifecycle policies (cost)
- [ ] Metadata service vs blob store separation
- [ ] Consistency & versioning in object stores

## 10.7 Search 🟡
- [ ] Inverted index construction, tokenization, analyzers
- [ ] Relevance: TF-IDF, BM25, boosting, personalization
- [ ] Near-real-time indexing pipeline (DB → CDC → index)
- [ ] Sharding & replication of the index
- [ ] Autocomplete: trie, n-grams, ranking by popularity
- [ ] Faceting, filtering, pagination at depth (deep paging problem)
- [ ] Hybrid search (keyword + vector) 🟡

## 10.8 Geospatial 🟡
- [ ] Geohash, quadtree, S2, H3 — trade-offs
- [ ] Proximity search, "drivers near me" queries
- [ ] Real-time location updates at scale (write amplification)
- [ ] ETA computation & routing (conceptual)

---
---

# PART 11 — ESTIMATION & CAPACITY MATH 🔴

- [ ] Powers of two & data size conversions (KB/MB/GB/TB/PB) instantly
- [ ] Seconds in a day ≈ 86,400 ≈ 10⁵ 🔴
- [ ] DAU → QPS: `DAU × actions/day / 86400`, then peak factor 2–10× 🔴
- [ ] Storage: `records/day × bytes/record × retention`, +30–50% for indexes/overhead
- [ ] Bandwidth: `QPS × payload size`; ingress vs egress; egress cost
- [ ] Cache sizing: working set = hot fraction × total; 80/20 rule
- [ ] Server count: `peak QPS / per-server QPS`, plus headroom & N+1 redundancy
- [ ] DB sizing: rows, index size, IOPS, connection count
- [ ] Kafka sizing: partitions = max(throughput/partition-throughput, consumer parallelism)
- [ ] Cost estimation: instances + storage + egress + managed service premiums 🔴
- [ ] Latency budget: sum of hops must be < SLO; where the p99 hides
- [ ] Rounding discipline — use round numbers, state assumptions, don't calculate to 3 decimals
- [ ] Practice: 10 estimation drills timed at 3 minutes each ⏱

---
---

# PART 12 — ENTERPRISE / DOMAIN DESIGN 🟡

> Common in product companies and enterprise interviews for leads — less "design Twitter", more "design our actual problem".

- [ ] Order management system: state machine, saga, compensations, partial fulfilment
- [ ] Inventory & reservation service: holds, expiry, oversell prevention, warehouse allocation
- [ ] Billing/subscription: plans, proration, invoices, retries, dunning, tax, revenue recognition
- [ ] Payment orchestration: multi-PSP routing, idempotency, webhooks, reconciliation, refunds, chargebacks 🔴
- [ ] KYC/onboarding workflow with external providers & async callbacks
- [ ] Document management: upload, versioning, permissions, retention, e-sign integration
- [ ] Reporting service: OLTP → OLAP separation, pre-aggregation, export at scale
- [ ] Bulk import/export pipeline (millions of rows, validation, partial failure, progress)
- [ ] Integration platform: third-party API sync, rate limits, retries, drift reconciliation
- [ ] Scheduling/appointment system with time zones and conflicts
- [ ] Multi-tenant data isolation & per-tenant customization
- [ ] Legacy modernization: strangler fig plan with milestones & rollback
- [ ] Batch → real-time migration of an existing pipeline
- [ ] Regulatory: audit trail, data retention, right-to-erasure across services 🔴
- [ ] Internal platform/service template design (golden path for other teams) 🟡

---
---

# PART 13 — DEBUGGING & TROUBLESHOOTING ROUND 🔴

> "Production is on fire — walk me through it." Increasingly common for leads. Highest-signal round.

## 13.1 General Method 🔴
- [ ] Stabilize first (mitigate), diagnose second — say this out loud
- [ ] Scope the blast radius: all users or some? all endpoints? since when? correlates with a deploy?
- [ ] Check the four golden signals: latency, traffic, errors, saturation
- [ ] Recent-change bias: deploys, config, feature flags, dependency updates, data volume, traffic shift 🔴
- [ ] Binary-search the system: which hop introduces the latency/error?
- [ ] Form a hypothesis, name the evidence that would confirm/refute it, then look
- [ ] Don't fix without a root cause hypothesis; don't chase without mitigating

## 13.2 Scenario Playbooks 🔴
- [ ] **High CPU** — `top -H` → nid → thread dump / async-profiler; GC vs application code vs regex vs serialization
- [ ] **High memory / OOMKilled** — heap vs off-heap vs metaspace vs container limit; heap dump + MAT
- [ ] **Long GC pauses** — GC logs, allocation rate, live set, humongous objects, collector choice
- [ ] **Latency spike, low CPU** — lock contention, connection pool exhaustion, downstream latency, GC, network, disk
- [ ] **Thread pool exhaustion** — blocked threads, missing timeouts, slow downstream, thread dump analysis
- [ ] **Connection pool exhaustion** — leaked connections, long transactions, pool sizing, `leakDetectionThreshold`
- [ ] **Deadlock** — thread dump deadlock section, lock ordering fix
- [ ] **DB slow queries** — `pg_stat_statements`, `EXPLAIN`, missing index, plan flip after stats change, lock waits
- [ ] **Kafka consumer lag** — rebalances, slow processing, partition skew, `max.poll.interval`
- [ ] **Cascading failure** — retry storm, missing circuit breaker, timeout mismatch, capacity loss
- [ ] **Intermittent 5xx** — one bad instance, LB health check, canary, DNS, TLS expiry
- [ ] **Memory leak over days** — heap trend, static collections, `ThreadLocal`, classloader leak, cache without bound
- [ ] **Data inconsistency** — race condition, missing idempotency, dual write, replication lag, cache staleness 🔴
- [ ] **Works locally, fails in prod** — config, timezone/locale, charset, resource limits, network policy, data scale
- [ ] **Disk full** — logs, temp files, heap dumps, DB WAL
- [ ] **After-deploy failure** — rollback first; schema/app version mismatch; feature flag off

## 13.3 What Interviewers Grade 🔴
- [ ] Do you mitigate before root-causing?
- [ ] Do you ask for evidence rather than guessing wildly?
- [ ] Do you name the exact tool and the exact command?
- [ ] Do you consider the boring cause first (a deploy, a config, a full disk)?
- [ ] Do you talk about communication (status updates, incident channel, stakeholders)? 🔴
- [ ] Do you close with prevention (alert, test, guardrail, runbook, postmortem)? 🔴

---
---

# PART 14 — CODE REVIEW ROUND 🟡

- [ ] Read for correctness first: off-by-one, null, concurrency, error paths, resource leaks
- [ ] Then security: injection, authz check, secrets, unsafe deserialization, PII in logs 🔴
- [ ] Then design: SRP violations, leaky abstractions, wrong layer, hidden coupling
- [ ] Then performance: N+1, unbounded collections, blocking in async, missing pagination, hot-loop allocation
- [ ] Then reliability: missing timeout/retry, non-idempotent handler, missing transaction boundary
- [ ] Then tests: are the important branches covered? are they testing behavior?
- [ ] Then observability: log levels, metrics, correlation IDs
- [ ] Then readability & naming — last, and lightly
- [ ] Distinguish blocking issues from suggestions from nits explicitly 🔴
- [ ] Tone: specific, kind, with a suggested fix; ask questions instead of asserting
- [ ] Say what's *good* in the change too
- [ ] Know your top-10 review checklist by heart for Java/Spring code 🔴
- [ ] Practice: review a real open-source PR and write the comments out

---
---

# PART 15 — BEHAVIORAL & LEADERSHIP ROUNDS 🔴

## 15.1 Story Bank — write each out (200–300 words, STAR + metrics) 🔴
- [ ] Led a project end to end
- [ ] Made a hard architectural decision & the trade-offs
- [ ] Disagreed with a manager / senior peer
- [ ] Resolved conflict between two engineers
- [ ] Handled a severe production incident (your specific actions, minute by minute)
- [ ] Mentored someone with a measurable outcome
- [ ] Managed an underperformer
- [ ] Missed a deadline or shipped a failure; what you learned
- [ ] Pushed back on scope / said no to a stakeholder
- [ ] Convinced others without authority
- [ ] Introduced a new technology and de-risked it
- [ ] Paid down major technical debt and justified it commercially
- [ ] Improved delivery speed/quality with numbers (DORA metrics ideally)
- [ ] Scaled a system (before/after: QPS, latency, cost)
- [ ] Reduced cost significantly
- [ ] Handled extreme ambiguity
- [ ] Received hard feedback and changed behavior
- [ ] Made a wrong call and recovered
- [ ] Balanced quality vs speed under real pressure
- [ ] Influenced a decision across teams/orgs
- [ ] Hired/interviewed and improved the bar
- [ ] Dealt with a difficult stakeholder or exec
- [ ] Improved on-call health / reduced alert fatigue
- [ ] Drove a migration that touched many teams

## 15.2 Story Quality Checklist 🔴
- [ ] "I" not "we" for your actions; "we" for context — be explicit about your specific contribution
- [ ] Quantified outcome (%, ms, $, headcount-hours, incident count)
- [ ] Names the trade-off you accepted, not just the win
- [ ] Includes what you'd do differently
- [ ] 2–3 minutes spoken, not 6
- [ ] Has 2 prepared follow-up depths (technical detail + people detail)
- [ ] Recent (last 2–3 years) and verifiable
- [ ] Maps to a leadership principle / competency (adapt per company)

## 15.3 Lead-Specific Question Bank 🔴
- [ ] How do you set technical direction for a team?
- [ ] How do you decide what to build vs buy?
- [ ] How do you handle a teammate who resists code review feedback?
- [ ] How do you balance feature work against tech debt? (give your actual %) 
- [ ] How do you estimate, and what do you do when you're going to miss?
- [ ] How do you onboard a new engineer?
- [ ] How do you run a design review?
- [ ] How do you handle disagreement with your product manager?
- [ ] How do you keep quality high while shipping fast?
- [ ] How do you grow senior engineers vs juniors?
- [ ] How do you decide who works on what?
- [ ] What do you do in your first 90 days on a new team? 🔴
- [ ] How do you handle an underperforming team (not individual)?
- [ ] How do you make a decision when the team is split 50/50?
- [ ] What's your on-call philosophy?
- [ ] How do you measure your team's health and productivity?
- [ ] Tell me about a technical decision you regret
- [ ] How do you stay technical as a lead?
- [ ] What would make you leave a job?
- [ ] Why are you leaving your current role? / Why us?

## 15.4 Questions YOU Ask 🔴
- [ ] Team: size, seniority mix, tenure, attrition, who I'd work with
- [ ] Role: what does success look like at 3/6/12 months? Is this a lead-with-authority or lead-by-influence role?
- [ ] Tech: biggest architectural pain right now? What's the tech debt story?
- [ ] Process: how do you decide priorities? release cadence? on-call load?
- [ ] Quality: what's your test/deploy/incident story? DORA numbers?
- [ ] Growth: how are promotions decided? Who was promoted from this team recently?
- [ ] Red flags to probe: why is this role open, how long, what happened to the last person
- [ ] For the manager: what's your management style, how do you give feedback?

---
---

# PART 16 — COMPANY FORMATS & LEVEL CALIBRATION 🟡

## 16.1 Format Differences
- [ ] **Big tech (FAANG-like):** heavy DSA + HLD + strong behavioral (principles-based), leveling matters, bar raiser round
- [ ] **Product startups/scale-ups:** machine coding, practical LLD, real-world debugging, culture fit, ownership
- [ ] **Enterprise/services companies:** Java/Spring depth, project explanation, SQL, some DSA, client-communication scenarios
- [ ] **Fintech:** correctness, consistency, idempotency, ledger design, security, regulatory
- [ ] **Consultancies:** breadth, communication, estimation, client scenarios
- [ ] **Remote-first:** async communication, written exercises, documentation quality

## 16.2 Level Calibration — what "senior lead" must show 🔴
- [ ] Scope: owns a system/domain, not just tasks — evidence in every story
- [ ] Ambiguity: turns a vague problem into a plan
- [ ] Impact: business outcomes, not activity
- [ ] Multiplier effect: made others better (mentoring, tooling, docs, standards)
- [ ] Judgment: names trade-offs unprompted, knows when *not* to do something
- [ ] Cross-functional: works with PM, design, SRE, security, leadership
- [ ] Long-term thinking: migrations, debt, maintainability, cost
- [ ] Communication: adjusts depth for the audience 🔴
- [ ] Failure ownership without blame-shifting

## 16.3 Logistics
- [ ] Resume: impact bullets with metrics, tailored per role, 2 pages max
- [ ] LinkedIn & GitHub tidy; a public design doc or blog post is a strong signal 🟡
- [ ] Referral > cold apply; map your network before applying
- [ ] Interview scheduling strategy: warm-up companies first, target company later 🔴
- [ ] Note-taking template per interview; post-mortem after each round 🔴
- [ ] Offer stage: comp structure (base/bonus/equity/vesting), leveling, negotiation, competing offers
- [ ] Reference & background check readiness
- [ ] Notice period & transition planning

---
---

# PART 17 — YOUR OWN ARCHITECTURE STORY 🔴

> Most under-prepared, highest-leverage round for a 10-YOE lead.

- [ ] One-page C4-style context + container diagram of your flagship system
- [ ] The numbers, memorized: users, QPS (avg & peak), data volume, latency SLO & actual p50/p99, uptime, team size, deploy frequency, cost 🔴
- [ ] The business context: what problem it solves, what it's worth
- [ ] Your specific role and the decisions *you* made
- [ ] 3 hard technical problems you solved, with the alternatives you rejected
- [ ] Biggest incident and what changed afterwards
- [ ] Biggest performance/cost win with before/after numbers
- [ ] What you'd redesign today, and why you didn't then (constraints matter)
- [ ] How you'd scale it 10× and 100×
- [ ] What the tech debt is and your plan for it
- [ ] How you led the team through it (people, not just tech) 🔴
- [ ] A 5-minute version, a 15-minute version, and a slide-free whiteboard version ⏱
- [ ] Sanitized: no confidential numbers, no NDA breaches — practice the redacted version 🔴

---
---

# PART 18 — DRILL PLANS & SCHEDULES 🔴

## 18.1 12-Week Plan (part-time, ~10–12 h/week)

| Week | DSA | Design | Java/Other | Behavioral |
|---|---|---|---|---|
| 1 | Patterns 1–4, arrays/strings/hashing | SD framework + estimation drills | Collections & complexity table | Write 2 stories |
| 2 | Patterns 5–8, linked list, stack/queue | URL shortener, rate limiter | Concurrency basics | Write 2 stories |
| 3 | Trees, BFS/DFS | Chat system, notification service | JVM/GC | Write 2 stories |
| 4 | Heaps, top-K, two heaps | Key-value store, distributed cache | Spring/transactions | Write 2 stories |
| 5 | Graphs, union-find, topo sort | Twitter feed, Instagram | JPA/N+1 | Refine + record yourself |
| 6 | **Mock week**: 2 DSA mocks, 1 design mock | | | 1 behavioral mock |
| 7 | DP part 1 (1D, knapsack) | Uber, ticketing/inventory | SQL + window functions | Story polish |
| 8 | DP part 2 (strings, intervals) | Payment system, e-commerce | Kafka/messaging | Lead question bank |
| 9 | LLD: Tier 1 problems | Drive/Dropbox, Docs | Debugging playbooks | Architecture story v1 |
| 10 | LLD: Tier 2 + machine coding | Job scheduler, metrics system | Observability/security | Architecture story v2 |
| 11 | **Mock week**: 2 DSA, 2 design, 1 LLD | | | 2 behavioral mocks |
| 12 | Weak-area repair | Weak-area repair | Weak-area repair | Final polish + questions to ask |

## 18.2 6-Week Compressed Plan 🔴
- [ ] Weeks 1–2: patterns + top-75 problems, SD framework, 6 Tier-1 designs
- [ ] Week 3: LLD Tier 1, Java deep dive, SQL
- [ ] Week 4: DP + graphs, 6 Tier-2 designs, debugging playbooks
- [ ] Week 5: mocks (4+), behavioral stories, architecture story
- [ ] Week 6: weak areas, repeat missed problems, logistics & negotiation prep

## 18.3 Daily Discipline 🔴
- [ ] 1–2 DSA problems, timed, out loud, no IDE autocomplete ⏱
- [ ] Re-solve anything you failed after 3 days, then after 10 days (spaced repetition) 🔴
- [ ] 1 system design per 2 days, written on paper/whiteboard, 45 min ⏱
- [ ] 1 behavioral story written or refined per session
- [ ] Maintain a **mistake log**: every wrong approach + the correct trigger you missed 🔴
- [ ] Weekly: 1 full mock with a real human, recorded 🔴
- [ ] Weekly: review the mistake log, not new problems

## 18.4 Mock Interview Protocol 🔴
- [ ] Real time limits, camera on, share screen, no pausing
- [ ] Record and rewatch — count filler words and silent gaps
- [ ] Score against a rubric: correctness, communication, structure, trade-offs, code quality
- [ ] Sources: peers, Pramp/interviewing.io/Exponent, ex-colleagues, paid coaches
- [ ] Do at least 2 mocks with someone senior to your target level
- [ ] After each: 3 specific actions, not vague "be better"

---
---

# PART 19 — COMMUNICATION & EXECUTION SKILLS 🔴

- [ ] Think out loud continuously — silence reads as being stuck 🔴
- [ ] Signpost your structure: "I'll do requirements, then estimation, then API, then deep dives"
- [ ] Ask before assuming; state assumptions explicitly when you must assume
- [ ] Manage the clock; ask the interviewer where they want depth 🔴
- [ ] Draw first, talk second — diagram beats paragraph
- [ ] Use precise vocabulary (idempotent, linearizable, at-least-once) correctly — wrong usage is worse than not using it
- [ ] Handle "I don't know" well: say it, then reason from first principles toward an answer 🔴
- [ ] Take hints gracefully; interviewer hints are a scoring opportunity, not a failure
- [ ] Recover from a wrong path without spiraling — "that approach breaks because X, let me switch"
- [ ] Disagree respectfully with evidence when the interviewer is wrong
- [ ] Keep answers to 2–3 minutes; check in ("want more depth here?")
- [ ] Whiteboard/remote tools practice (Excalidraw, Miro, CoderPad) before the real thing 🔴
- [ ] Energy & pacing over a 5-hour loop: breaks, water, notes between rounds
- [ ] Post-round: write down every question asked, same day 🔴

---
---

# APPENDIX A — SYSTEM DESIGN ANSWER TEMPLATE

```
1. REQUIREMENTS (5 min)
   Functional:      [3-5 core, prioritized with interviewer]
   Out of scope:    [state explicitly]
   Non-functional:  DAU ___  QPS avg/peak ___  read:write ___
                    latency p99 ___  availability ___  consistency ___
                    data retention ___  regions ___

2. ESTIMATION (3 min)
   QPS      = DAU × actions/day ÷ 86,400 × peak factor
   Storage  = records/day × size × retention × 1.4
   Bandwidth= QPS × payload
   Cache    = hot % × working set

3. API (5 min)
   POST /v1/resource   (idempotency-key header)
   GET  /v1/resource?cursor=&limit=
   [events published: resource.created v1]

4. DATA MODEL (5 min)
   Entities, keys, shard key + WHY, index per query pattern
   DB choice + one-line justification

5. HIGH-LEVEL DESIGN (10 min)
   Client → CDN → LB → Gateway → Service(s) → Cache → DB
                                     ↘ Queue → Workers → Store
   Narrate one write path and one read path end to end.

6. DEEP DIVES (15-20 min)
   Pick the 2 hardest: [contention / hot key / consistency / scale bottleneck]

7. FAILURE MODES
   Each component down → what happens, what degrades, what's the fallback

8. SCALE 10x
   What breaks first? Then what?

9. TRADE-OFFS + WHAT I'D DO WITH MORE TIME
```

# APPENDIX B — LLD ANSWER TEMPLATE

```
1. Requirements in / out (5 min)
2. Actors & use cases
3. Entities: [Entity | ValueObject | Service | Repository]
4. Class diagram (relationships + multiplicity)
5. Key interfaces:
     interface PricingStrategy { Money price(Ticket t); }
     interface SlotAllocator  { Optional<Slot> allocate(Vehicle v); }
6. Core code: 2-3 classes with real signatures
7. Concurrency: shared state ___, strategy ___, deadlock avoidance ___
8. Persistence sketch
9. Extension points: "to add X, implement Y — no existing class changes"
10. Trade-offs & rejected alternatives
```

# APPENDIX C — MISTAKE LOG TEMPLATE

| Date | Problem / Round | What I did wrong | Correct trigger/approach | Re-test date | Passed? |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |

# APPENDIX D — RESOURCES

### DSA
- [ ] NeetCode 150 / Blind 75 (primary problem set)
- [ ] *Elements of Programming Interviews in Java* — Aziz et al.
- [ ] *Cracking the Coding Interview* (dated but useful for structure)
- [ ] LeetCode: company tags + "Top Interview 150"
- [ ] *Grokking the Coding Interview* patterns (concept source)
- [ ] *Algorithm Design Manual* — Skiena (for depth)

### System Design
- [ ] *System Design Interview* Vol 1 & 2 — Alex Xu
- [ ] *Designing Data-Intensive Applications* — Kleppmann 🔴
- [ ] ByteByteGo, Hello Interview, System Design Primer (GitHub)
- [ ] *Understanding Distributed Systems* — Vitillo
- [ ] Engineering blogs: Netflix, Uber, Airbnb, Stripe, Discord, Cloudflare, Dropbox, Slack
- [ ] Papers: Dynamo, Bigtable, GFS, MapReduce, Kafka, Raft, Spanner, Zanzibar 🟡

### LLD / OOD
- [ ] *Head First Design Patterns*
- [ ] *Design Patterns* — GoF
- [ ] refactoring.guru
- [ ] Awesome Low Level Design (GitHub)
- [ ] *Clean Code* + *Refactoring* (Fowler)

### Behavioral / Leadership
- [ ] *The Manager's Path* — Fournier
- [ ] *Staff Engineer* — Larson; *The Staff Engineer's Path* — Reilly
- [ ] *Cracking the PM/EM Interview* (behavioral structure)
- [ ] Company leadership principles (read the actual published list before the loop) 🔴

### Mocks
- [ ] interviewing.io · Pramp · Exponent · IGotAnOffer · peers

---

# APPENDIX E — FINAL WEEK CHECKLIST 🔴

- [ ] Re-solve 10 problems you previously failed
- [ ] Re-do 3 system designs cold, timed
- [ ] Rehearse the architecture story 3× out loud
- [ ] Rehearse top 8 behavioral stories out loud (not reading)
- [ ] Read the company's engineering blog + leadership principles
- [ ] Prepare 5 questions per interviewer type
- [ ] Test hardware, camera, lighting, drawing tool
- [ ] Print/keep: complexity table, estimation numbers, your story index
- [ ] Sleep, hydration, and a break plan between rounds
- [ ] Post-loop: write down every question within 2 hours

---

*Living document — add every question you actually get asked, and every mistake you actually make.*
