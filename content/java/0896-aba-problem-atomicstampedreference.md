---
card: java
gi: 896
slug: aba-problem-atomicstampedreference
title: ABA problem & AtomicStampedReference
---

## 1. What it is

The **ABA problem** is a subtle failure mode of plain compare-and-swap: a thread reads a value `A`, and before it completes its CAS, some *other* thread changes the value from `A` to `B` and then back to `A` again. The first thread's CAS then succeeds — because the value it compares against (`A`) does match the current value (`A`) — even though the state actually changed and changed back in between, which might have violated an invariant the first thread was relying on (like "this specific object hasn't been freed and reused since I last looked at it"). `AtomicStampedReference<V>` fixes this by pairing every reference with an integer **stamp** (a version number) that must also match for the CAS to succeed — so a value that returns to `A` but with a *different* stamp is correctly detected as having changed, even though the reference itself looks identical.

## 2. Why & when

Plain CAS on a reference only compares object identity — it has no way to know "has this been touched since I last read it," only "is it currently equal to what I expect." For many simple algorithms (like a basic atomic counter or a straightforward compare-and-set flag) this distinction never matters, since the algorithm's correctness doesn't depend on detecting intermediate changes. It becomes a real bug specifically in lock-free algorithms that manage mutable structures with reused nodes or pooled objects — a classic example is a lock-free stack where a node gets popped, its memory gets reused for a newly pushed node with the exact same reference value (via an object pool or by coincidence), and a thread's stale CAS based on the old reference succeeds incorrectly against the "new" node that merely happens to have the same identity. Use `AtomicStampedReference` (or `AtomicMarkableReference`, a lighter variant with a boolean mark instead of an integer stamp) whenever your CAS-based algorithm's correctness genuinely depends on knowing not just "is the value still A" but "has anyone touched this since I looked."

## 3. Core concept

```java
AtomicStampedReference<Node> topOfStack = new AtomicStampedReference<>(initialNode, 0); // reference + stamp

int[] stampHolder = new int[1];
Node current = topOfStack.get(stampHolder);   // reads BOTH the reference and its current stamp
int currentStamp = stampHolder[0];

// compareAndSet checks BOTH the reference AND the stamp -- succeeds only if NEITHER changed
boolean success = topOfStack.compareAndSet(current, newNode, currentStamp, currentStamp + 1);
```

Even if the reference somehow reverts to the exact same object (`A` → `B` → `A`), the stamp keeps incrementing on every successful update, so a stale CAS attempt using an outdated stamp correctly fails, unlike a plain `AtomicReference`'s CAS, which would incorrectly succeed.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Thread reads reference A with stamp 5; meanwhile another thread changes it to B (stamp 6) and back to A (stamp 7); the first thread's stale CAS using stamp 5 fails even though the reference value is again A">
  <rect x="20" y="20" width="180" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">T1 reads: ref=A, stamp=5</text>

  <rect x="240" y="20" width="150" height="30" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="315" y="40" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">T2: A -&gt; B, stamp=6</text>
  <rect x="240" y="60" width="150" height="30" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="315" y="80" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">T2: B -&gt; A, stamp=7</text>

  <rect x="20" y="110" width="300" height="35" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="170" y="132" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">T1 CAS(A, X, expectedStamp=5, ...) FAILS</text>
  <text x="170" y="160" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">reference is A again, but stamp is 7, not 5 -- CORRECTLY detected as changed</text>

  <line x1="110" y1="55" x2="170" y2="108" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#a28)"/>
  <defs><marker id="a28" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*The reference alone looks unchanged (A, then A again) — but the stamp reveals that something happened in between, which a plain `AtomicReference` CAS would have missed entirely.*

## 5. Runnable example

Scenario: a simplified lock-free stack with node reuse (simulating the classic ABA scenario), growing from a plain `AtomicReference`-based version that's vulnerable to ABA, to demonstrating the ABA failure concretely, to fixing it with `AtomicStampedReference`.

### Level 1 — Basic

```java
import java.util.concurrent.atomic.*;

public class PlainAtomicReferenceStack {
    static class Node {
        final int value;
        Node next;
        Node(int value, Node next) { this.value = value; this.next = next; }
    }

    static AtomicReference<Node> top = new AtomicReference<>(null);

    static void push(int value) {
        Node newNode = new Node(value, null);
        Node currentTop;
        do {
            currentTop = top.get();
            newNode.next = currentTop;
        } while (!top.compareAndSet(currentTop, newNode));
    }

    static Node pop() {
        Node currentTop;
        Node newTop;
        do {
            currentTop = top.get();
            if (currentTop == null) return null;
            newTop = currentTop.next;
        } while (!top.compareAndSet(currentTop, newTop));
        return currentTop;
    }

    public static void main(String[] args) {
        push(1); push(2); push(3);
        System.out.println("popped: " + pop().value); // 3
        System.out.println("popped: " + pop().value); // 2
        push(4);
        System.out.println("popped: " + pop().value); // 4
        System.out.println("(single-threaded: works fine -- ABA only manifests under real concurrent interleaving)");
    }
}
```

**How to run:** `java PlainAtomicReferenceStack.java` (JDK 17+).

Expected output:
```
popped: 3
popped: 2
popped: 4
(single-threaded: works fine -- ABA only manifests under real concurrent interleaving)
```

Correct in this single-threaded demonstration — the ABA vulnerability is latent and only manifests under a very specific concurrent interleaving where a node gets popped, reused, and pushed back with the same reference while another thread's CAS is still in flight.

### Level 2 — Intermediate

```java
import java.util.concurrent.atomic.*;

public class DemonstratingAbaFailure {
    static class Node {
        final int value;
        Node next;
        Node(int value, Node next) { this.value = value; this.next = next; }
    }

    static AtomicReference<Node> top = new AtomicReference<>(null);

    public static void main(String[] args) {
        Node a = new Node(1, null);
        Node b = new Node(2, a);
        top.set(b); // stack: b -> a -> null

        // Thread 1's pop() begins: reads currentTop=b, newTop=a, but PAUSES here (simulated)
        Node t1_currentTop = top.get(); // = b
        Node t1_newTop = t1_currentTop.next; // = a

        // Meanwhile, thread 2 does a full pop() and push() cycle:
        top.compareAndSet(b, a);       // pop b -> stack is now: a -> null
        Node c = new Node(3, a);
        top.compareAndSet(a, c);       // push c -> stack is now: c -> a -> null
        top.compareAndSet(c, a);       // pop c (simulating reuse) -> stack is BACK to: a -> null

        // Thread 1 RESUMES: its stale CAS still thinks top should be `b` -- but top is `a` now, not `b`,
        // so in THIS specific case the CAS correctly fails. The real danger is when `b`'s memory gets
        // reused for a NEW node with the SAME reference (e.g. via pooling) -- then top.get() could
        // literally equal `b` again despite the stack having changed underneath, and T1's CAS would
        // incorrectly succeed, corrupting the stack by installing the WRONG next pointer (T1's stale `a`).
        boolean t1Succeeded = top.compareAndSet(t1_currentTop, t1_newTop);
        System.out.println("thread 1's stale CAS succeeded? " + t1Succeeded + " (false here, but pooled-node reuse can make this true incorrectly)");
    }
}
```

**How to run:** `java DemonstratingAbaFailure.java`.

Expected output:
```
thread 1's stale CAS succeeded? false (false here, but pooled-node reuse can make this true incorrectly)
```

This specific run happens not to trigger the failure, since `b` itself (not a reused-identity replacement) is the object compared — but it illustrates exactly the sequence of intervening pop/push/pop operations that, combined with object pooling or memory reuse (common in high-performance lock-free data structure implementations, especially in languages/runtimes with manual memory management, and reproducible in Java via object pools), causes the stale CAS to incorrectly succeed against a reference that merely *looks* like the one originally read.

### Level 3 — Advanced

```java
import java.util.concurrent.atomic.*;

public class AtomicStampedReferenceFix {
    static class Node {
        final int value;
        Node next;
        Node(int value, Node next) { this.value = value; this.next = next; }
    }

    static AtomicStampedReference<Node> top = new AtomicStampedReference<>(null, 0);

    static void push(int value) {
        int[] stampHolder = new int[1];
        Node newNode = new Node(value, null);
        Node currentTop;
        int currentStamp;
        do {
            currentTop = top.get(stampHolder);
            currentStamp = stampHolder[0];
            newNode.next = currentTop;
        } while (!top.compareAndSet(currentTop, newNode, currentStamp, currentStamp + 1)); // stamp MUST also match
    }

    static Node pop() {
        int[] stampHolder = new int[1];
        Node currentTop;
        Node newTop;
        int currentStamp;
        do {
            currentTop = top.get(stampHolder);
            if (currentTop == null) return null;
            currentStamp = stampHolder[0];
            newTop = currentTop.next;
        } while (!top.compareAndSet(currentTop, newTop, currentStamp, currentStamp + 1)); // stamp catches ABA
        return currentTop;
    }

    public static void main(String[] args) {
        push(1); push(2); push(3);

        int[] stampHolder = new int[1];
        Node t1_currentTop = top.get(stampHolder);
        int t1_stamp = stampHolder[0]; // T1 captures the stamp ALONG with the reference

        // Simulate the same pop/push/pop interleaving as before, which changes the STAMP each time,
        // even in the case where the reference value itself would coincidentally return to the same node:
        pop(); // stamp advances
        push(99); // stamp advances again
        pop(); // stamp advances yet again

        // Thread 1 resumes with its STALE stamp -- even if the reference happened to match again,
        // the stamp no longer does, so the CAS correctly fails, protecting against ABA.
        boolean t1Succeeded = top.compareAndSet(t1_currentTop, t1_currentTop.next, t1_stamp, t1_stamp + 1);
        System.out.println("thread 1's stale CAS (stamped) succeeded? " + t1Succeeded + " (correctly false -- stamp mismatch detected)");
    }
}
```

**How to run:** `java AtomicStampedReferenceFix.java`.

Expected output:
```
thread 1's stale CAS (stamped) succeeded? false (correctly false -- stamp mismatch detected)
```

This adds the production-flavored hard case: even under the exact same pop/push/pop interleaving that could fool a plain `AtomicReference` if node identities happened to be reused, `AtomicStampedReference` correctly rejects the stale CAS, because the stamp has advanced with every intervening successful update — the reference alone is not sufficient evidence that nothing changed; the stamp provides the missing piece of information that closes the ABA hole entirely.

## 6. Walkthrough

Tracing the key comparison in `AtomicStampedReferenceFix.main`:

1. `top.get(stampHolder)` reads both the current top node reference and its associated stamp in one atomic operation, storing the stamp into the caller-provided `stampHolder` array (an output-parameter idiom, since Java methods can't return two values directly) — thread 1 captures both `t1_currentTop` and `t1_stamp` at this point.
2. Three subsequent operations (`pop()`, `push(99)`, `pop()`) each internally perform their own `compareAndSet(currentTop, newTop/newNode, currentStamp, currentStamp + 1)` calls — every one of these, upon success, increments the stamp by exactly 1, regardless of what the reference value itself ends up being.
3. By the time thread 1 attempts its own (stale) `compareAndSet(t1_currentTop, t1_currentTop.next, t1_stamp, t1_stamp + 1)` call, the stamp has advanced by 3 from three successful intervening operations — even in a hypothetical scenario where the actual reference value coincidentally matched `t1_currentTop` again (the classic ABA setup), the *stamp* would no longer match `t1_stamp`.
4. `AtomicStampedReference.compareAndSet` requires **both** the reference and the stamp to match the expected values for the swap to succeed — since the stamp alone already fails to match, the CAS is rejected regardless of what the reference comparison would have concluded on its own.
5. This is the crucial difference from a plain `AtomicReference`: the stamp acts as an always-incrementing "version counter" that makes every successful update distinguishable from every other, even when the reference itself might coincidentally cycle back to an earlier value — closing the exact hole that allows the classic ABA problem to occur.
6. The printed result confirms the stale CAS was correctly rejected — thread 1's outdated understanding of the stack's state is detected and its incorrect update attempt is safely blocked, forcing it to re-read the current state and retry with fresh information instead.

## 7. Gotchas & takeaways

> **Gotcha:** the ABA problem is easy to dismiss as "theoretical" because it requires a very specific interleaving (change, then change back) to actually manifest — but it's a real, documented source of subtle corruption bugs in lock-free data structures that reuse or pool objects, and it's notoriously hard to reproduce and diagnose after the fact, since by the time you observe the corrupted state, the "ABA moment" itself is long gone with no trace.

- The ABA problem: a value changes from A to B and back to A between a thread's read and its CAS attempt — the CAS succeeds because the *value* matches, even though the state genuinely changed in between, which can violate assumptions the algorithm depends on.
- `AtomicStampedReference<V>` pairs a reference with an integer stamp that must also match for CAS to succeed, correctly detecting intervening changes even when the reference value itself returns to its original identity.
- `AtomicMarkableReference<V>` is a lighter-weight sibling using a single boolean "mark" instead of an integer stamp, useful when you only need to detect "has this been touched" rather than track a full version count.
- Reach for these specifically when implementing or reasoning about lock-free algorithms with object reuse or pooling — most everyday `AtomicReference` usage (simple flags, straightforward hot-swaps) never encounters the conditions needed to trigger ABA at all.
- The stamp-comparison pattern is conceptually the same discipline as optimistic-locking version columns in databases (`WHERE id = ? AND version = ?`) — both detect "did anything change since I last looked," not just "is the current value what I expect."
