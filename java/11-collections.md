# Java Collections — Complete Deep Dive

## Overview

The Java Collections Framework provides a unified architecture for storing and manipulating groups of objects. It includes interfaces (List, Set, Map, Queue, Deque), implementations (ArrayList, HashMap, TreeSet, etc.), and utility classes (Collections, Arrays). This is one of the most interview-tested areas of Java.

---

## 1. Collection Hierarchy

### Visual Diagram

```
java.lang.Iterable
    └── java.util.Collection
            ├── List (ordered, indexed, duplicates allowed)
            │     ├── ArrayList
            │     ├── LinkedList
            │     ├── Vector (legacy)
            │     └── Stack (legacy)
            ├── Set (no duplicates)
            │     ├── HashSet
            │     ├── LinkedHashSet
            │     └── SortedSet → NavigableSet → TreeSet
            └── Queue (FIFO ordering)
                  ├── PriorityQueue
                  ├── LinkedList (also implements Deque)
                  └── Deque (double-ended queue)
                        ├── ArrayDeque
                        └── LinkedList

Map (NOT a Collection — key-value pairs):
    ├── HashMap
    ├── LinkedHashMap
    ├── Hashtable (legacy)
    └── SortedMap → NavigableMap → TreeMap

[Java 21] New sequenced interfaces:
    SequencedCollection (has getFirst/getLast/addFirst/addLast/reversed)
        └── implemented by: ArrayList, LinkedList, ArrayDeque, TreeSet, LinkedHashSet
    SequencedSet extends SequencedCollection + Set
    SequencedMap (has firstEntry/lastEntry/sequencedKeySet/sequencedValues/reversed)
        └── implemented by: LinkedHashMap, TreeMap
```

---

## 2. List — ArrayList

### What is it

ArrayList is a resizable array. It provides O(1) random access and O(1) amortized append. Internally it holds an `Object[]` that grows when needed.

### Visual Diagram — Internal Array

```
ArrayList state after adding [10, 20, 30, 40, 50]:

Internal array (capacity=10):
Index:  [ 0] [ 1] [ 2] [ 3] [ 4] [ 5] [ 6] [ 7] [ 8] [ 9]
Value:  [ 10] [20] [30] [40] [50] [  ] [  ] [  ] [  ] [  ]
         ←─── size = 5 ──────►   ←── unused slots ──────►

size  = 5  (number of actual elements)
capacity = 10 (length of internal array)
```

### Method Table — O() Complexity

| Method                   | Time Complexity | Notes                         |
|--------------------------|-----------------|-------------------------------|
| `add(E)`                 | O(1) amortized  | O(n) when resize needed       |
| `add(int idx, E)`        | O(n)            | shifts elements right         |
| `get(int idx)`           | O(1)            | direct array access           |
| `set(int idx, E)`        | O(1)            | direct array write            |
| `remove(int idx)`        | O(n)            | shifts elements left          |
| `remove(Object o)`       | O(n)            | linear search + shift         |
| `contains(Object o)`     | O(n)            | linear search                 |
| `size()`                 | O(1)            |                               |
| `isEmpty()`              | O(1)            |                               |
| `indexOf(Object o)`      | O(n)            |                               |
| `subList(from, to)`      | O(1)            | view, not copy                |
| `sort(Comparator)`       | O(n log n)      | TimSort                       |
| `iterator()`             | O(1)            |                               |
| `clear()`                | O(n)            | nulls all elements            |

### Example 1 — Basic ArrayList Operations

```java
import java.util.*;

public class ArrayListBasics {
    public static void main(String[] args) {
        List<String> list = new ArrayList<>();

        // Adding
        list.add("Alice");
        list.add("Bob");
        list.add("Charlie");
        list.add(1, "Zara");  // insert at index 1

        System.out.println(list);         // [Alice, Zara, Bob, Charlie]
        System.out.println(list.get(2));  // Bob
        System.out.println(list.size());  // 4

        // Removing
        list.remove("Bob");               // by value
        list.remove(0);                   // by index — removes "Alice"
        System.out.println(list);         // [Zara, Charlie]

        // Iteration
        for (String s : list) System.out.print(s + " ");
        System.out.println();

        // Contains / indexOf
        System.out.println(list.contains("Zara"));   // true
        System.out.println(list.indexOf("Charlie")); // 1
    }
}
```

**What this does:** Core ArrayList operations. `remove(int)` removes by index; `remove(Object)` removes by value — be careful with `List<Integer>`: `list.remove(1)` removes index 1, `list.remove(Integer.valueOf(1))` removes the value 1.

### Dry Run — ArrayList Resize at Element 11

```java
List<Integer> list = new ArrayList<>();  // capacity = 10
for (int i = 1; i <= 11; i++) list.add(i);
```

| add() call | size before | capacity | Action                              |
|------------|-------------|----------|-------------------------------------|
| add(1)     | 0           | 10       | arr[0] = 1; size=1                  |
| ...        | ...         | 10       | elements 2-10 fill normally         |
| add(10)    | 9           | 10       | arr[9] = 10; size=10                |
| add(11)    | 10          | 10       | **RESIZE**: newCap=10+(10>>1)=15    |
|            |             |          | allocate int[15], copy 10 elements  |
|            |             |          | arr[10] = 11; size=11; capacity=15  |

### Example 2 — Sort and removeIf

```java
import java.util.*;

public class ArrayListAdvanced {
    public static void main(String[] args) {
        List<Integer> nums = new ArrayList<>(Arrays.asList(5, 2, 8, 1, 9, 3, 7, 4, 6));

        // Sort with Comparator
        nums.sort(Comparator.naturalOrder());
        System.out.println(nums);  // [1, 2, 3, 4, 5, 6, 7, 8, 9]

        nums.sort(Comparator.reverseOrder());
        System.out.println(nums);  // [9, 8, 7, 6, 5, 4, 3, 2, 1]

        // removeIf [Java 8+] — safe removal during "iteration"
        nums.removeIf(n -> n % 2 == 0);  // remove all even
        System.out.println(nums);  // [9, 7, 5, 3, 1]

        // replaceAll [Java 8+]
        nums.replaceAll(n -> n * 10);
        System.out.println(nums);  // [90, 70, 50, 30, 10]

        // subList — backed by original list
        List<Integer> sub = nums.subList(1, 4);
        System.out.println(sub);  // [70, 50, 30]
        sub.set(0, 999);
        System.out.println(nums); // [90, 999, 50, 30, 10] — original changed!
    }
}
```

**What this does:** `removeIf` uses internal iteration — safe from ConcurrentModificationException. `subList` returns a view backed by the original — modifications propagate both ways.

> ⚠️ **Pitfall:** `list.remove(1)` on `List<Integer>` removes index 1, not value 1. Use `list.remove(Integer.valueOf(1))` to remove by value.

---

## 3. List — LinkedList

### What is it

Doubly-linked list. Each element is a Node holding the element plus references to previous and next nodes. O(1) at head/tail, O(n) for index access.

### Visual Diagram — Doubly-Linked Nodes

```
LinkedList: [A] ↔ [B] ↔ [C] ↔ [D]

Node structure:
┌──────────────────────┐
│ prev │ element │ next │
└──────────────────────┘

first ──► [null|A|─]──►[─|B|─]──►[─|C|─]──►[─|D|null] ◄── last
              ◄────────────────────────────────────────
```

### Method Table

| Method              | Time  | Notes                        |
|---------------------|-------|------------------------------|
| `get(int idx)`      | O(n)  | traverses to index           |
| `add(E)` at tail    | O(1)  | direct tail pointer          |
| `add(int,E)`        | O(n)  | must traverse to index first |
| `addFirst/addLast`  | O(1)  | Deque methods                |
| `removeFirst/Last`  | O(1)  | Deque methods                |
| `contains/indexOf`  | O(n)  | linear scan                  |

### Example 1 — LinkedList as List and Deque

```java
import java.util.*;

public class LinkedListDemo {
    public static void main(String[] args) {
        LinkedList<String> list = new LinkedList<>();

        // As List
        list.add("B");
        list.add("C");
        list.addFirst("A");  // Deque method — O(1)
        list.addLast("D");   // Deque method — O(1)
        System.out.println(list); // [A, B, C, D]

        // Deque operations — O(1)
        System.out.println(list.peekFirst()); // A (no remove)
        System.out.println(list.pollFirst()); // A (removes)
        System.out.println(list.peekLast());  // D
        System.out.println(list);             // [B, C, D]

        // As Queue (FIFO)
        Queue<String> queue = new LinkedList<>();
        queue.offer("first");
        queue.offer("second");
        System.out.println(queue.poll()); // first
    }
}
```

**What this does:** LinkedList implements both `List` and `Deque`. Use `addFirst/addLast` and `removeFirst/removeLast` for O(1) operations. Note: `get(idx)` is O(n) — don't use LinkedList when random access is needed.

> ⚠️ **Pitfall:** Iterating LinkedList with `get(i)` in a loop is O(n²). Use iterator or for-each instead.

---

## 4. Legacy — Vector and Stack

```java
// Vector = synchronized ArrayList (all methods synchronized = slow)
// Stack extends Vector — exposes push/pop/peek/empty/search
// AVOID BOTH. Use instead:
//   ArrayList or ArrayDeque — for unsynchronized use
//   CopyOnWriteArrayList    — for thread-safe list
//   ArrayDeque              — for stack/queue operations
Deque<Integer> stack = new ArrayDeque<>();
stack.push(1); stack.push(2); stack.push(3);
System.out.println(stack.pop());  // 3 (LIFO)
```

---

## 5. Set — HashSet

### What is it

Unordered collection of unique elements. Backed by a HashMap (element is the key, a dummy `PRESENT` constant is the value). O(1) average for add/remove/contains.

### Method Table

| Method         | Time      | Notes                        |
|----------------|-----------|------------------------------|
| `add(E)`       | O(1) avg  | O(n) worst (all same bucket) |
| `remove(E)`    | O(1) avg  |                              |
| `contains(E)`  | O(1) avg  |                              |
| `size()`       | O(1)      |                              |
| `iterator()`   | O(1)      | iteration is O(n)            |
| `isEmpty()`    | O(1)      |                              |

### Example 1 — HashSet Basics and Set Operations

```java
import java.util.*;

public class HashSetDemo {
    public static void main(String[] args) {
        Set<String> set = new HashSet<>();
        set.add("Alice");
        set.add("Bob");
        set.add("Alice");   // duplicate — ignored
        System.out.println(set.size());       // 2
        System.out.println(set.contains("Bob")); // true

        // Set operations
        Set<Integer> a = new HashSet<>(Arrays.asList(1, 2, 3, 4, 5));
        Set<Integer> b = new HashSet<>(Arrays.asList(4, 5, 6, 7, 8));

        // Union
        Set<Integer> union = new HashSet<>(a);
        union.addAll(b);
        System.out.println(union);  // [1, 2, 3, 4, 5, 6, 7, 8]

        // Intersection
        Set<Integer> intersection = new HashSet<>(a);
        intersection.retainAll(b);
        System.out.println(intersection);  // [4, 5]

        // Difference (a - b)
        Set<Integer> difference = new HashSet<>(a);
        difference.removeAll(b);
        System.out.println(difference);  // [1, 2, 3]
    }
}
```

**What this does:** HashSet rejects duplicates silently (add returns false for duplicates). `addAll/retainAll/removeAll` implement set algebra. Order is not guaranteed.

---

## 6. Set — LinkedHashSet

Maintains insertion order via a doubly-linked list threading through entries. O(1) operations like HashSet but predictable iteration order.

```java
Set<String> linked = new LinkedHashSet<>();
linked.add("Banana"); linked.add("Apple"); linked.add("Cherry");
System.out.println(linked); // [Banana, Apple, Cherry] — insertion order preserved
```

---

## 7. Set — TreeSet

### What is it

Red-black tree. Elements kept in sorted order. All operations O(log n). Implements `NavigableSet`.

### Method Table

| Method                    | Time     | Notes                    |
|---------------------------|----------|--------------------------|
| `add(E)`                  | O(log n) |                          |
| `remove(E)`               | O(log n) |                          |
| `contains(E)`             | O(log n) |                          |
| `first()` / `last()`      | O(log n) | smallest/largest         |
| `floor(E)`                | O(log n) | largest ≤ E              |
| `ceiling(E)`              | O(log n) | smallest ≥ E             |
| `lower(E)`                | O(log n) | largest < E (strict)     |
| `higher(E)`               | O(log n) | smallest > E (strict)    |
| `headSet(to)`             | O(log n) | elements < to            |
| `tailSet(from)`           | O(log n) | elements ≥ from          |
| `subSet(from, to)`        | O(log n) | elements in [from, to)   |
| `descendingSet()`         | O(1)     | reverse-order view       |
| `pollFirst()/pollLast()`  | O(log n) | retrieves and removes    |

### Example 1 — TreeSet Navigation

```java
import java.util.*;

public class TreeSetDemo {
    public static void main(String[] args) {
        TreeSet<Integer> ts = new TreeSet<>(Arrays.asList(5, 1, 9, 3, 7, 2, 8));
        System.out.println(ts);          // [1, 2, 3, 5, 7, 8, 9] (sorted)

        System.out.println(ts.first());  // 1
        System.out.println(ts.last());   // 9
        System.out.println(ts.floor(6)); // 5 (largest ≤ 6)
        System.out.println(ts.ceiling(6)); // 7 (smallest ≥ 6)
        System.out.println(ts.lower(5)); // 3 (strictly less than 5)
        System.out.println(ts.higher(5)); // 7 (strictly greater than 5)

        System.out.println(ts.headSet(5));     // [1, 2, 3] (< 5)
        System.out.println(ts.tailSet(5));     // [5, 7, 8, 9] (≥ 5)
        System.out.println(ts.subSet(3, 8));   // [3, 5, 7] ([3,8))

        // Custom comparator (reverse order)
        TreeSet<String> reverse = new TreeSet<>(Comparator.reverseOrder());
        reverse.addAll(Arrays.asList("banana", "apple", "cherry"));
        System.out.println(reverse); // [cherry, banana, apple]
    }
}
```

**What this does:** TreeSet's navigation methods make it ideal for range queries, finding nearest values, and ordered processing. All navigation is O(log n).

> ⚠️ **Pitfall:** TreeSet requires elements to be Comparable (or a Comparator provided). Adding non-Comparable objects throws ClassCastException.

---

## 8. Map — HashMap (Most Important!)

### What is it

The most-used Map. Hash table implementation. O(1) average for get/put/remove. Does NOT maintain insertion order.

### Visual Diagram — Internal Structure

```
HashMap (capacity=16, load factor=0.75):

Bucket Array:
[0]  → null
[1]  → null
[2]  → Node("cat"=3) → null
[3]  → null
[4]  → Node("dog"=5) → Node("god"=7) → null   ← collision! linked list
[5]  → null
...
[14] → Node("hat"=1) → null
[15] → null

When bucket [4] gets ≥ 8 entries → converts linked list to Red-Black Tree [Java 8+]

put("key", value) steps:
1. hash = key.hashCode() ^ (hashCode >>> 16)   ← spreads high bits
2. index = hash & (capacity - 1)               ← fast modulo via bitmask
3. if bucket empty → create node
   if key exists → update value
   if collision → add to linked list (or tree)
4. if size > capacity * 0.75 → resize (double capacity, rehash all)
```

### Method Table

| Method                      | Time      | Notes                          |
|-----------------------------|-----------|--------------------------------|
| `put(K, V)`                 | O(1) avg  | O(n) worst (all same bucket)   |
| `get(K)`                    | O(1) avg  |                                |
| `remove(K)`                 | O(1) avg  |                                |
| `containsKey(K)`            | O(1) avg  |                                |
| `containsValue(V)`          | O(n)      | must scan all buckets          |
| `size()`                    | O(1)      |                                |
| `keySet()`                  | O(1)      | returns view                   |
| `values()`                  | O(1)      | returns view                   |
| `entrySet()`                | O(1)      | returns view                   |
| `putIfAbsent(K, V)`         | O(1) avg  | only puts if key absent        |
| `getOrDefault(K, def)`      | O(1) avg  |                                |
| `computeIfAbsent(K, fn)`    | O(1) avg  | compute and store if absent    |
| `computeIfPresent(K, fn)`   | O(1) avg  | compute and store if present   |
| `compute(K, BiFunction)`    | O(1) avg  | always compute new value       |
| `merge(K, V, BiFunction)`   | O(1) avg  | merge with existing value      |
| `forEach(BiConsumer)`       | O(n)      |                                |
| `replaceAll(BiFunction)`    | O(n)      |                                |

### Dry Run — HashMap.put() Sequence

```java
HashMap<String, Integer> map = new HashMap<>();  // capacity=16
map.put("dog", 1);   // hash("dog") & 15 = let's say bucket 4
map.put("cat", 2);   // hash("cat") & 15 = bucket 9
map.put("god", 3);   // hash("god") & 15 = bucket 4 → COLLISION with "dog"
```

| Step | Key   | hashCode() | Adjusted hash | Bucket | Action                           |
|------|-------|------------|---------------|--------|----------------------------------|
| 1    | "dog" | 99473      | 99427         | 4      | bucket empty → create node       |
| 2    | "cat" | 98262      | 98231         | 9      | bucket empty → create node       |
| 3    | "god" | 102387     | 102354        | 4      | bucket has "dog" → add to chain  |

Bucket 4 now has: `Node("dog"=1) → Node("god"=3)`

### Example 1 — HashMap CRUD

```java
import java.util.*;

public class HashMapCRUD {
    public static void main(String[] args) {
        Map<String, Integer> scores = new HashMap<>();

        scores.put("Alice", 95);
        scores.put("Bob", 87);
        scores.put("Charlie", 92);
        scores.put("Alice", 98);  // update — returns old value 95

        System.out.println(scores.get("Bob"));           // 87
        System.out.println(scores.getOrDefault("Dave", 0)); // 0 (not found)
        System.out.println(scores.containsKey("Charlie")); // true
        System.out.println(scores.size());               // 3

        scores.remove("Bob");
        System.out.println(scores); // {Alice=98, Charlie=92} (order not guaranteed)

        // Iterate
        for (Map.Entry<String, Integer> entry : scores.entrySet()) {
            System.out.println(entry.getKey() + " → " + entry.getValue());
        }

        // forEach [Java 8+]
        scores.forEach((k, v) -> System.out.println(k + ": " + v));
    }
}
```

**What this does:** Basic HashMap CRUD. `put` returns the previous value (or null). `getOrDefault` avoids null checks. `entrySet()` is the most efficient way to iterate both keys and values simultaneously.

### Example 2 — computeIfAbsent for Grouping

```java
import java.util.*;

public class HashMapCompute {
    public static void main(String[] args) {
        // Group words by first letter
        String[] words = {"apple", "ant", "banana", "bear", "cherry", "cat"};
        Map<Character, List<String>> byLetter = new HashMap<>();

        for (String word : words) {
            char key = word.charAt(0);
            // computeIfAbsent: if key absent, create empty list, then add
            byLetter.computeIfAbsent(key, k -> new ArrayList<>()).add(word);
        }
        System.out.println(byLetter);
        // {a=[apple, ant], b=[banana, bear], c=[cherry, cat]}

        // merge: word frequency count
        String[] text = {"the", "cat", "sat", "on", "the", "mat", "the"};
        Map<String, Integer> freq = new HashMap<>();
        for (String w : text) {
            freq.merge(w, 1, Integer::sum);
            // if absent: put w=1; if present: apply Integer::sum(existing, 1)
        }
        System.out.println(freq); // {the=3, cat=1, sat=1, on=1, mat=1}
    }
}
```

**What this does:** `computeIfAbsent` is the idiomatic way to build multi-valued maps — check if key exists, create default value if not, then use the value. `merge` is perfect for accumulation (frequency counts, summing, concatenation).

> ⚠️ **Pitfall:** HashMap allows one null key and multiple null values. Hashtable and ConcurrentHashMap do NOT allow null keys or values.

---

## 9. Map — LinkedHashMap

Maintains insertion order (or optionally access order). Backed by HashMap plus a doubly-linked list threading through entries.

### Example 1 — LRU Cache Implementation

```java
import java.util.*;

public class LRUCache<K, V> extends LinkedHashMap<K, V> {
    private final int capacity;

    public LRUCache(int capacity) {
        // accessOrder=true: iterates in access order (LRU → MRU)
        super(capacity, 0.75f, true);
        this.capacity = capacity;
    }

    @Override
    protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
        return size() > capacity;  // remove LRU entry when over capacity
    }

    public static void main(String[] args) {
        LRUCache<Integer, String> cache = new LRUCache<>(3);
        cache.put(1, "one");
        cache.put(2, "two");
        cache.put(3, "three");
        cache.get(1);         // access 1 → moves to most recently used
        cache.put(4, "four"); // evicts LRU (which is now 2)
        System.out.println(cache.containsKey(2)); // false — evicted
        System.out.println(cache.containsKey(1)); // true  — was accessed
        System.out.println(cache);  // {3=three, 1=one, 4=four}
    }
}
```

**What this does:** `accessOrder=true` reorders entries on every `get`/`put`. `removeEldestEntry` is called after every `put` — returning true evicts the oldest (LRU) entry. Classic interview question implementation.

---

## 10. Map — TreeMap

Red-black tree. Keys kept sorted. All operations O(log n). Implements `NavigableMap`.

```java
import java.util.*;

public class TreeMapDemo {
    public static void main(String[] args) {
        TreeMap<String, Integer> map = new TreeMap<>();
        map.put("banana", 2); map.put("apple", 1); map.put("cherry", 3);
        System.out.println(map);             // {apple=1, banana=2, cherry=3} (sorted)

        System.out.println(map.firstKey()); // apple
        System.out.println(map.lastKey());  // cherry
        System.out.println(map.floorKey("b"));   // apple (largest key ≤ "b")
        System.out.println(map.ceilingKey("b")); // banana (smallest key ≥ "b")
        System.out.println(map.headMap("cherry"));     // {apple=1, banana=2}
        System.out.println(map.tailMap("banana"));     // {banana=2, cherry=3}
        System.out.println(map.subMap("apple", "cherry")); // {apple=1, banana=2}

        // First/last entries [Java 21 via SequencedMap]
        System.out.println(map.firstEntry()); // apple=1
        System.out.println(map.lastEntry());  // cherry=3
    }
}
```

---

## 11. Legacy Maps

```java
// Hashtable — synchronized, no null keys/values, legacy
// Use ConcurrentHashMap instead for thread-safe maps

// Properties — extends Hashtable, for .properties files
Properties props = new Properties();
props.setProperty("host", "localhost");
props.setProperty("port", "8080");
System.out.println(props.getProperty("host")); // localhost
System.out.println(props.getProperty("timeout", "30")); // 30 (default)
// Load from file: props.load(new FileReader("config.properties"))
```

---

## 12. Specialized Maps

```java
import java.util.*;

// WeakHashMap: keys held by weak references — GC can collect them
// Use for caches where entries should be released when key no longer referenced
WeakHashMap<Object, String> cache = new WeakHashMap<>();
Object key = new Object();
cache.put(key, "data");
key = null;  // key no longer referenced
System.gc();
// cache entry may be removed after GC

// IdentityHashMap: uses == (not equals) for key comparison
// Use when you need object identity, not value equality
IdentityHashMap<String, Integer> idMap = new IdentityHashMap<>();
String a = new String("key");
String b = new String("key");
idMap.put(a, 1);
idMap.put(b, 2);
System.out.println(idMap.size()); // 2 (a != b by reference, even though a.equals(b))
```

---

## 13. Queue — PriorityQueue

### What is it

A min-heap (by default). The element with the smallest value according to natural ordering (or Comparator) is always at the head. Useful for task scheduling, Dijkstra's algorithm, top-K problems.

### Visual Diagram — Heap Array Representation

```
Binary min-heap stored as array:

Array: [1, 3, 2, 7, 4, 5, 6]
Index:  0  1  2  3  4  5  6

Tree representation:
              1          ← index 0 (root)
           /     \
          3       2      ← index 1, 2
         / \     / \
        7   4   5   6    ← index 3, 4, 5, 6

Parent of index i:  (i-1) / 2
Left child of i:    2*i + 1
Right child of i:   2*i + 2

Property: parent ≤ both children (min-heap)
```

### Method Table

| Method       | Time     | Notes                              |
|--------------|----------|------------------------------------|
| `offer(E)`   | O(log n) | adds + sifts up                    |
| `poll()`     | O(log n) | removes min + sifts down; null if empty |
| `peek()`     | O(1)     | returns min without removing; null if empty |
| `add(E)`     | O(log n) | same as offer but throws on failure |
| `remove()`   | O(log n) | same as poll but throws if empty   |
| `element()`  | O(1)     | same as peek but throws if empty   |
| `size()`     | O(1)     |                                    |
| `contains(E)` | O(n)   | linear scan                        |

### Dry Run — offer() Maintaining Heap Property

```java
PriorityQueue<Integer> pq = new PriorityQueue<>();
pq.offer(5); pq.offer(3); pq.offer(8); pq.offer(1); pq.offer(4);
```

| Step  | Value | Array after       | Sift-up action                  |
|-------|-------|-------------------|---------------------------------|
| offer(5) | 5  | [5]               | root, done                      |
| offer(3) | 3  | [3, 5]            | 3 < parent(5) → swap → [3,5]    |
| offer(8) | 8  | [3, 5, 8]         | 8 > parent(3) → no swap         |
| offer(1) | 1  | [1, 3, 8, 5]      | 1 at idx3, parent=5, swap; parent=3, swap |
| offer(4) | 4  | [1, 3, 8, 5, 4]   | 4 at idx4, parent=3, no swap    |

poll() returns 1 (root), replaces with last (4), sifts down.

### Example 1 — Min-Heap, Max-Heap, Custom Priority

```java
import java.util.*;

public class PriorityQueueDemo {
    public static void main(String[] args) {
        // Default: min-heap
        PriorityQueue<Integer> minPQ = new PriorityQueue<>();
        minPQ.offer(5); minPQ.offer(1); minPQ.offer(3);
        System.out.println(minPQ.poll()); // 1 (minimum)
        System.out.println(minPQ.poll()); // 3
        System.out.println(minPQ.poll()); // 5

        // Max-heap: reverse order
        PriorityQueue<Integer> maxPQ = new PriorityQueue<>(Comparator.reverseOrder());
        maxPQ.offer(5); maxPQ.offer(1); maxPQ.offer(3);
        System.out.println(maxPQ.poll()); // 5 (maximum)

        // Custom objects
        record Task(String name, int priority) {}
        PriorityQueue<Task> tasks = new PriorityQueue<>(
            Comparator.comparingInt(Task::priority)
        );
        tasks.offer(new Task("Low", 3));
        tasks.offer(new Task("Critical", 1));
        tasks.offer(new Task("Medium", 2));
        while (!tasks.isEmpty()) {
            System.out.println(tasks.poll().name());
        }
        // Critical, Medium, Low (sorted by priority ascending)

        // K-th largest element
        int[] nums = {3, 1, 4, 1, 5, 9, 2, 6};
        int k = 3;
        PriorityQueue<Integer> kth = new PriorityQueue<>();  // min-heap of size k
        for (int n : nums) {
            kth.offer(n);
            if (kth.size() > k) kth.poll();
        }
        System.out.println("3rd largest: " + kth.peek()); // 5
    }
}
```

**What this does:** Min-heap (default) always dequeues smallest. Max-heap uses `Comparator.reverseOrder()`. Custom priority by any field via `Comparator.comparingInt`. K-th largest: maintain min-heap of size k — the top is the k-th largest.

---

## 14. Deque — ArrayDeque

### What is it

A resizable circular array implementing Deque (double-ended queue). Faster than LinkedList for both stack and queue operations. No null allowed.

### Visual Diagram — Circular Array

```
ArrayDeque (capacity=8, head=5, tail=1):

Index: [0] [1] [2] [3] [4] [5] [6] [7]
Value: [ C] [ ] [ ] [ ] [ ] [ A] [ B] [ ]
                                ↑ head      ↑ tail

Logical order (head → tail): A(5), B(6), C(0)
offerFirst → decrements head (wraps: 5→4)
offerLast  → increments tail (wraps: 7→0)
```

### Example 1 — ArrayDeque as Stack, Queue, and Deque

```java
import java.util.*;

public class ArrayDequeDemo {
    public static void main(String[] args) {
        // As Stack (LIFO) — push/pop/peek
        Deque<Integer> stack = new ArrayDeque<>();
        stack.push(1); stack.push(2); stack.push(3);
        System.out.println(stack.pop());   // 3 (LIFO)
        System.out.println(stack.peek());  // 2 (no remove)

        // As Queue (FIFO) — offer/poll/peek
        Queue<String> queue = new ArrayDeque<>();
        queue.offer("first"); queue.offer("second"); queue.offer("third");
        System.out.println(queue.poll());  // first (FIFO)

        // As Deque — full double-ended access
        Deque<String> deque = new ArrayDeque<>();
        deque.offerFirst("B");
        deque.offerFirst("A");  // A is now at front
        deque.offerLast("C");
        System.out.println(deque);  // [A, B, C]
        System.out.println(deque.pollFirst()); // A
        System.out.println(deque.pollLast());  // C
        System.out.println(deque); // [B]
    }
}
```

**What this does:** ArrayDeque is the recommended stack AND queue replacement for Stack/LinkedList. No null elements. Amortized O(1) for all head/tail operations.

> ⚠️ **Pitfall:** `ArrayDeque.push(x)` adds to the FRONT (like stack). `ArrayDeque.offer(x)` adds to the BACK (like queue). Don't mix them accidentally.

---

## 15. Iterating Collections

### Example 1 — Iterator and Safe Removal

```java
import java.util.*;

public class IteratorDemo {
    public static void main(String[] args) {
        List<Integer> list = new ArrayList<>(Arrays.asList(1, 2, 3, 4, 5, 6));

        // WRONG: ConcurrentModificationException
        // for (Integer n : list) { if (n % 2 == 0) list.remove(n); }

        // RIGHT: Iterator.remove()
        Iterator<Integer> it = list.iterator();
        while (it.hasNext()) {
            int n = it.next();
            if (n % 2 == 0) it.remove();  // safe removal
        }
        System.out.println(list); // [1, 3, 5]

        // BETTER [Java 8+]: removeIf
        List<Integer> list2 = new ArrayList<>(Arrays.asList(1, 2, 3, 4, 5, 6));
        list2.removeIf(n -> n % 2 == 0);
        System.out.println(list2); // [1, 3, 5]

        // ListIterator — bidirectional + modification
        List<String> words = new ArrayList<>(Arrays.asList("hello", "world", "java"));
        ListIterator<String> lit = words.listIterator();
        while (lit.hasNext()) {
            String s = lit.next();
            lit.set(s.toUpperCase()); // replace current element
        }
        System.out.println(words); // [HELLO, WORLD, JAVA]
    }
}
```

**What this does:** `Iterator.remove()` is the only safe way to remove during iteration without `removeIf`. `ListIterator` adds `set()` and `add()` for in-place modification.

---

## 16. Collections Utility Class

### Example 1 — Sorting and Searching

```java
import java.util.*;

public class CollectionsUtil {
    public static void main(String[] args) {
        List<Integer> nums = new ArrayList<>(Arrays.asList(3, 1, 4, 1, 5, 9, 2, 6));

        Collections.sort(nums);                        // natural order
        System.out.println(nums);   // [1, 1, 2, 3, 4, 5, 6, 9]

        Collections.sort(nums, Comparator.reverseOrder()); // reverse
        System.out.println(nums);   // [9, 6, 5, 4, 3, 2, 1, 1]

        Collections.sort(nums);  // re-sort for binarySearch
        int idx = Collections.binarySearch(nums, 5);
        System.out.println("5 at index: " + idx); // 4

        Collections.reverse(nums);
        System.out.println(nums);   // [9, 6, 5, 4, 3, 2, 1, 1]

        Collections.shuffle(nums, new Random(42));
        System.out.println(nums);   // random order

        Collections.swap(nums, 0, nums.size()-1);

        System.out.println(Collections.min(nums));
        System.out.println(Collections.max(nums));
        System.out.println(Collections.frequency(nums, 1)); // 2

        List<Integer> filled = new ArrayList<>(Collections.nCopies(5, 0));
        System.out.println(filled);  // [0, 0, 0, 0, 0]
    }
}
```

### Example 2 — Unmodifiable and Synchronized Wrappers

```java
import java.util.*;

public class CollectionsWrappers {
    public static void main(String[] args) {
        List<String> mutable = new ArrayList<>(Arrays.asList("a", "b", "c"));

        // Unmodifiable view — original still mutable through mutable reference
        List<String> readOnly = Collections.unmodifiableList(mutable);
        // readOnly.add("d");  // UnsupportedOperationException
        mutable.add("d");      // this works — and readOnly sees the change!
        System.out.println(readOnly); // [a, b, c, d]

        // True immutability → List.of() [Java 9+]
        List<String> immutable = List.of("x", "y", "z");
        // immutable.add("w");  // UnsupportedOperationException
        // mutable reference can't change immutable — truly frozen

        // Thread-safe wrappers (all methods synchronized)
        List<String> syncList = Collections.synchronizedList(new ArrayList<>());
        // Must synchronize on the list during iteration:
        synchronized(syncList) {
            for (String s : syncList) System.out.println(s);
        }
    }
}
```

**What this does:** `Collections.unmodifiableList()` wraps with read-only view but the backing list can still be mutated. `List.of()` [Java 9+] is truly immutable. Synchronized wrappers still need external synchronization for compound operations and iteration.

---

## 17. Immutable Collections [Java 9+]

### Example 1 — List.of, Set.of, Map.of

```java
import java.util.*;

public class ImmutableCollections {
    public static void main(String[] args) {
        // List.of — immutable, no nulls, preserves order
        List<String> names = List.of("Alice", "Bob", "Charlie");
        System.out.println(names.get(1));  // Bob
        // names.add("Dave");   // UnsupportedOperationException
        // names.set(0, null);  // NullPointerException (no nulls!)

        // Set.of — immutable, no nulls, no duplicates
        Set<Integer> primes = Set.of(2, 3, 5, 7, 11);
        // Set.of(1, 1);  // IllegalArgumentException — duplicate!

        // Map.of — up to 10 entries
        Map<String, Integer> scores = Map.of(
            "Alice", 95,
            "Bob", 87,
            "Charlie", 92
        );
        System.out.println(scores.get("Alice")); // 95

        // Map.ofEntries — no limit on entries
        Map<String, Integer> big = Map.ofEntries(
            Map.entry("a", 1), Map.entry("b", 2), Map.entry("c", 3)
        );

        // copyOf — immutable copy of existing collection
        List<String> mutable = new ArrayList<>(Arrays.asList("x", "y", "z"));
        List<String> copy = List.copyOf(mutable);
        mutable.add("w");
        System.out.println(copy);    // [x, y, z] — copy is independent
        System.out.println(mutable); // [x, y, z, w]
    }
}
```

**What this does:** `List.of()` / `Set.of()` / `Map.of()` create truly immutable collections. `List.copyOf()` creates an independent immutable snapshot. Unlike `Collections.unmodifiableList()`, there's no mutable backing list to worry about.

---

## 18. Comparable vs Comparator

### What is it

Two mechanisms for defining sort order:
- **Comparable**: implemented by the class itself → defines natural ordering
- **Comparator**: external, separate ordering logic → multiple orderings possible

### Example 1 — Comparable Natural Ordering

```java
import java.util.*;

public class ComparableDemo {
    record Person(String name, int age) implements Comparable<Person> {
        @Override
        public int compareTo(Person other) {
            // Natural order: by name alphabetically
            int nameCompare = this.name.compareTo(other.name);
            if (nameCompare != 0) return nameCompare;
            return Integer.compare(this.age, other.age); // secondary: by age
        }
    }

    public static void main(String[] args) {
        List<Person> people = new ArrayList<>(Arrays.asList(
            new Person("Charlie", 30),
            new Person("Alice", 25),
            new Person("Bob", 35),
            new Person("Alice", 20)
        ));

        Collections.sort(people);  // uses compareTo
        people.forEach(System.out::println);
        // Person[name=Alice, age=20]
        // Person[name=Alice, age=25]
        // Person[name=Bob, age=35]
        // Person[name=Charlie, age=30]
    }
}
```

**What this does:** `Comparable` defines the natural ordering built into the class. `compareTo` returns negative (this < other), 0 (equal), positive (this > other). `Collections.sort()` and `Arrays.sort()` use this automatically.

### Example 2 — Comparator Chains

```java
import java.util.*;

public class ComparatorDemo {
    record Employee(String dept, String name, double salary) {}

    public static void main(String[] args) {
        List<Employee> employees = Arrays.asList(
            new Employee("Engineering", "Charlie", 95000),
            new Employee("Marketing", "Alice", 80000),
            new Employee("Engineering", "Alice", 105000),
            new Employee("Marketing", "Bob", 75000)
        );

        // Multi-field sort: dept ASC, then salary DESC, then name ASC
        employees.sort(
            Comparator.comparing(Employee::dept)
                      .thenComparing(Comparator.comparingDouble(Employee::salary).reversed())
                      .thenComparing(Employee::name)
        );

        employees.forEach(e ->
            System.out.printf("%-15s %-12s %.0f%n", e.dept(), e.name(), e.salary())
        );
        // Engineering   Alice        105000
        // Engineering   Charlie       95000
        // Marketing     Alice         80000
        // Marketing     Bob           75000

        // Null-safe comparison
        List<String> withNulls = Arrays.asList("banana", null, "apple", null, "cherry");
        withNulls.sort(Comparator.nullsFirst(Comparator.naturalOrder()));
        System.out.println(withNulls); // [null, null, apple, banana, cherry]
    }
}
```

**What this does:** `Comparator.comparing()` creates a comparator from a key extractor. `thenComparing()` adds secondary sort. `reversed()` flips direction. `nullsFirst/nullsLast` handles null values safely.

### Dry Run — Multi-field Sort

```
Sorting 3 Persons: [("Bob",35), ("Alice",25), ("Alice",20)] by name then age

Step 1: Compare ("Bob",35) vs ("Alice",25): "Bob".compareTo("Alice") = positive → Bob goes after Alice
Step 2: Compare ("Alice",25) vs ("Alice",20): "Alice".compareTo("Alice") = 0 → tie → compare age: 25-20 = 5 → positive → 25 goes after 20
Result: [("Alice",20), ("Alice",25), ("Bob",35)]
```

---

## 19. When-to-Use Decision Guide

```
Need unique elements?
├── YES → Set
│         ├── Need sorted order?        → TreeSet
│         ├── Need insertion order?     → LinkedHashSet
│         └── Just fast lookup?         → HashSet  ← DEFAULT
└── NO → need key→value pairs?
    ├── YES → Map
    │         ├── Sorted keys?          → TreeMap
    │         ├── Insertion/access order? → LinkedHashMap (LRU cache)
    │         └── Fastest?              → HashMap  ← DEFAULT
    └── NO → List or Queue?
        ├── Indexed sequence?
        │         ├── Fast random access?      → ArrayList  ← DEFAULT
        │         └── Frequent head/tail ops?  → ArrayDeque
        └── Queue behavior?
              ├── Priority-based?         → PriorityQueue
              ├── FIFO queue?             → ArrayDeque
              └── LIFO stack?             → ArrayDeque (push/pop)

Thread-safe alternatives:
  ArrayList    → CopyOnWriteArrayList (read-heavy)
  HashMap      → ConcurrentHashMap
  Queue        → ArrayBlockingQueue / LinkedBlockingQueue
  TreeMap      → ConcurrentSkipListMap
```

---

## Quick Reference

```
List (ordered, indexed, duplicates):
  ArrayList:        O(1) get/set, O(n) insert/delete in middle, O(1) amortized add
  LinkedList:       O(n) get, O(1) add/remove at ends, implements Deque

Set (unique):
  HashSet:          O(1) avg add/remove/contains, unordered
  LinkedHashSet:    O(1) avg, insertion order
  TreeSet:          O(log n) all ops, sorted, NavigableSet

Map (key-value):
  HashMap:          O(1) avg put/get/remove, unordered, 1 null key
  LinkedHashMap:    O(1) avg, ordered, use for LRU with accessOrder=true
  TreeMap:          O(log n) all ops, sorted keys, NavigableMap

Queue/Deque:
  PriorityQueue:    O(log n) offer/poll, O(1) peek, min-heap by default
  ArrayDeque:       O(1) amortized all ends, use for stack AND queue

Immutable [Java 9+]:
  List.of(), Set.of(), Map.of(), Map.entry(), copyOf()
  No nulls, no duplicates in Set/Map keys, truly immutable

Key pitfalls:
  - HashMap key must have correct equals+hashCode
  - TreeSet/TreeMap require Comparable or Comparator
  - ConcurrentModificationException when modifying during for-each
  - Arrays.asList = fixed-size (no add/remove)
  - List.remove(1) vs List.remove(Integer.valueOf(1))
```
