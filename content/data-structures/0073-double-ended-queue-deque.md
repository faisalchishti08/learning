---
card: data-structures
gi: 73
slug: double-ended-queue-deque
title: Double-ended queue (deque)
---

## 1. What it is

A **deque** (pronounced "deck," short for double-ended queue) is a structure that supports insertion and removal at **both** ends — front and back — each in O(1). It generalizes both the stack (use only one end) and the queue (insert one end, remove the other): a deque can behave as either, or as something with a richer access pattern than plain LIFO or FIFO.

## 2. Why & when

Reach for a deque whenever a problem needs to add or remove from both ends, or when the access pattern is not purely LIFO or purely FIFO — for example, a sliding window that drops old elements from the front while adding new ones at the back, or an undo history where you sometimes need to trim old entries from the far end. In Java, `ArrayDeque` is the standard implementation, and it can fully replace both `Stack` and `LinkedList`-as-queue.

## 3. Core concept

**The structure's shape and invariants.** A deque keeps track of both a front position and a back position. Whether backed by a circular array or a doubly linked list, both ends must be reachable in O(1) — that reachability is the entire invariant, and every operation is defined relative to one end or the other.

**How each invariant makes operations fast.** Because both ends are tracked directly (not found by scanning), `addFirst`, `addLast`, `removeFirst`, `removeLast`, `peekFirst`, and `peekLast` are all O(1). None of them require shifting other elements or walking the structure — the operation touches only the one end it targets.

**Array-backed vs linked, same tradeoff as a plain queue or stack.** A circular-array-backed deque (like `ArrayDeque`) has better cache locality and less memory overhead. A doubly linked deque never needs to resize but pays for a node object and two pointers per element. This mirrors the [Array-backed vs linked stack](0063-array-backed-vs-linked-stack.md) tradeoff exactly, just with two active ends instead of one.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A deque with elements 10, 20, 30, showing four operations at both ends: addFirst and removeFirst at the front, addLast and removeLast at the back">
  <g font-family="sans-serif" font-size="11">
    <rect x="220" y="50" width="46" height="30" fill="#161b22" stroke="#8b949e"/><text x="243" y="70" fill="#e6edf3" text-anchor="middle" font-size="9">10</text>
    <rect x="290" y="50" width="46" height="30" fill="#161b22" stroke="#8b949e"/><text x="313" y="70" fill="#e6edf3" text-anchor="middle" font-size="9">20</text>
    <rect x="360" y="50" width="46" height="30" fill="#161b22" stroke="#8b949e"/><text x="383" y="70" fill="#e6edf3" text-anchor="middle" font-size="9">30</text>
    <text x="243" y="40" fill="#79c0ff" text-anchor="middle" font-size="9">front</text>
    <text x="383" y="40" fill="#f0883e" text-anchor="middle" font-size="9">back</text>
    <line x1="216" y1="65" x2="180" y2="65" stroke="#79c0ff" marker-end="url(#f1)"/>
    <text x="130" y="55" fill="#79c0ff" font-size="9">addFirst / removeFirst</text>
    <line x1="410" y1="65" x2="446" y2="65" stroke="#f0883e" marker-end="url(#f2)"/>
    <text x="410" y="55" fill="#f0883e" font-size="9">addLast / removeLast</text>
    <defs>
      <marker id="f1" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M8,0 L0,4 L8,8 z" fill="#79c0ff"/></marker>
      <marker id="f2" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#f0883e"/></marker>
    </defs>
    <text x="310" y="120" fill="#8b949e" text-anchor="middle">using only the front pair = stack; front-in/back-out = queue; using both = full deque</text>
  </g>
</svg>

Both ends support insertion and removal in O(1); which subset of operations you call determines whether the deque acts as a stack, a queue, or something more flexible.

## 5. Runnable example

```java
// DequeDemo.java
import java.util.ArrayDeque;
import java.util.Deque;

public class DequeDemo {

    // Basic: the four core two-ended operations.
    static void basicLevel() {
        Deque<Integer> deque = new ArrayDeque<>();
        deque.addFirst(20);
        deque.addFirst(10); // deque: [10, 20]
        deque.addLast(30);  // deque: [10, 20, 30]
        System.out.println("basic: deque -> " + deque);
        System.out.println("basic: removeFirst -> " + deque.removeFirst());
        System.out.println("basic: removeLast -> " + deque.removeLast());
        System.out.println("basic: remaining -> " + deque);
    }

    // Intermediate: use the SAME deque as a stack (one end) and separately as a queue (both ends), to show the generalization.
    static void intermediateLevel() {
        Deque<String> asStack = new ArrayDeque<>();
        asStack.push("a"); // push/pop == addFirst/removeFirst
        asStack.push("b");
        System.out.println("intermediate: as a stack, pop -> " + asStack.pop()); // "b", LIFO

        Deque<String> asQueue = new ArrayDeque<>();
        asQueue.offer("x"); // offer/poll == addLast/removeFirst
        asQueue.offer("y");
        System.out.println("intermediate: as a queue, poll -> " + asQueue.poll()); // "x", FIFO
    }

    // Advanced: a palindrome check using both ends at once -- a genuinely two-ended use, neither pure stack nor pure queue.
    static boolean isPalindrome(String s) {
        Deque<Character> deque = new ArrayDeque<>();
        for (char c : s.toCharArray()) deque.addLast(c);

        while (deque.size() > 1) {
            if (deque.removeFirst() != deque.removeLast()) return false; // compare from both ends inward
        }
        return true;
    }

    static void advancedLevel() {
        System.out.println("advanced: isPalindrome(\"racecar\") -> " + isPalindrome("racecar"));
        System.out.println("advanced: isPalindrome(\"hello\") -> " + isPalindrome("hello"));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `DequeDemo.java`, then run `java DequeDemo.java`.

## 6. Walkthrough

1. `basicLevel()` builds `[10, 20, 30]` by mixing `addFirst` and `addLast`. `removeFirst()` returns `10`, `removeLast()` returns `30`, leaving only `[20]` — each operation touches only the end it targets.
2. `intermediateLevel()` shows the same `Deque` interface driving two different behaviors depending only on which method pair you call: `push`/`pop` (both at the front) give LIFO; `offer`/`poll` (`offer` at the back, `poll` at the front) give FIFO.
3. `advancedLevel()`'s `isPalindrome` genuinely needs both ends: it repeatedly compares and removes the front and back characters simultaneously, shrinking inward. For `"racecar"`, `r==r`, then `a==a`, then `c==c`, leaving one character (`e`) — loop stops since `size() == 1`, and every comparison matched, so it returns `true`. For `"hello"`, `h != o` on the first comparison, returning `false` immediately.

## 7. Gotchas & takeaways

> Gotcha: `Deque`'s method names overlap in confusing ways — `push`/`pop` operate on the front only (stack semantics), while `add`/`remove` (no `First`/`Last` suffix) also default to the front for most implementations, but the *intent* differs. Always use the explicit `addFirst`/`addLast`/`removeFirst`/`removeLast` names when two-ended behavior matters, so the code's intent is unambiguous to a reader.

- A deque generalizes both the stack and the queue by supporting O(1) insertion and removal at both ends.
- `ArrayDeque` is the standard Java implementation, backed by a circular array.
- Which method pair you call (`push`/`pop`, `offer`/`poll`, or `addFirst`/`addLast`/`removeFirst`/`removeLast`) determines whether it behaves like a stack, a queue, or a true two-ended structure.
- Related concepts: [FIFO semantics](0072-fifo-semantics.md), [LIFO semantics](0062-lifo-semantics.md), [ArrayDeque as queue & deque](0081-arraydeque-as-queue-deque.md).
