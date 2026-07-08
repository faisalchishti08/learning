---
card: java
gi: 429
slug: deque-interface-arraydeque
title: Deque interface & ArrayDeque
---

## 1. What it is

`Deque<E>` ("deck," short for **double-ended queue**), added in Java 6, is a collection that supports adding and removing elements from **both** ends efficiently: `addFirst`/`addLast`, `removeFirst`/`removeLast`, `peekFirst`/`peekLast`. Because of this, a single `Deque` can act as either a **stack** (via `push`/`pop`, which operate on the front) or a **queue** (via `offer`/`poll`, which add at the back and remove from the front). `ArrayDeque` is the go-to general-purpose implementation — backed by a resizable circular array, and (per its own documentation) usually faster than both `Stack` and `LinkedList` for these use cases.

## 2. Why & when

Before `Deque`, Java's `Stack` class (from Java 1.0) was the conventional stack type, but it's a holdover that extends `Vector` and inherits a bunch of legacy, unrelated, `synchronized` methods it doesn't need — generally considered a design mistake in retrospect. `LinkedList` could serve as a double-ended structure too, but each node carries object overhead that `ArrayDeque`'s backing array avoids. `Deque`/`ArrayDeque` were introduced to give a clean, modern, non-legacy type that does both stack and queue duty well, without `Stack`'s baggage or `LinkedList`'s per-node overhead.

You reach for `ArrayDeque` any time you need LIFO behavior (undo history, a call stack you manage yourself, backtracking algorithms) or FIFO behavior (a simple task queue, breadth-first search) — and, notably, sometimes **both at once** within the same feature, since one `ArrayDeque` instance can be treated as a stack in one part of your code and a queue in another, as needed.

## 3. Core concept

```java
import java.util.*;

Deque<String> deque = new ArrayDeque<>();

// Used as a STACK (LIFO): push/pop operate on the front
deque.push("first");
deque.push("second");
deque.pop();  // "second" -- most recently pushed comes off first

// Used as a QUEUE (FIFO): offer adds at the back, poll removes from the front
deque.offer("third");
deque.poll(); // whatever is currently at the FRONT

// True double-ended access, either end, explicitly:
deque.addFirst("front item");
deque.addLast("back item");
deque.removeLast(); // trims from the BACK specifically, regardless of stack/queue framing
```

The same object, the same underlying array — `push`/`pop`/`offer`/`poll` are just different names for operations on the front or back, chosen to match whichever mental model (stack or queue) fits the code using it.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An ArrayDeque supports adding and removing from both the front and back; push/pop use the front for stack behavior, offer/poll use the back and front for queue behavior">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="320" y="26" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">front &lt;-- [ C ][ B ][ A ] --&gt; back</text>

  <text x="120" y="70" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">push/pop (stack)</text>
  <line x1="120" y1="80" x2="120" y2="55" stroke="#6db33f" marker-end="url(ad1)"/>
  <text x="120" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">operate on FRONT</text>

  <text x="520" y="70" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">offer (queue add)</text>
  <text x="520" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">adds at BACK</text>
  <text x="120" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">poll (queue remove) also reads the FRONT</text>
  <text x="320" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Same array, same object -- different method names for front-only vs. either-end access.</text>
</svg>

Stack semantics use only the front; queue semantics add at the back and remove from the front — both are views onto the same underlying deque.

## 5. Runnable example

Scenario: undo/redo history for a tiny text editor — the same document-editing feature, evolved from a basic undo stack, through adding redo support with a second stack, to a bounded undo history that automatically discards the oldest snapshots once a size limit is exceeded.

### Level 1 — Basic

```java
import java.util.*;

public class UndoBasic {
    public static void main(String[] args) {
        Deque<String> undoStack = new ArrayDeque<>(); // used as a STACK here: push/pop at one end
        StringBuilder document = new StringBuilder();

        String[] edits = {"Hello", ", World", "!"};
        for (String edit : edits) {
            undoStack.push(document.toString()); // save the state BEFORE this edit
            document.append(edit);
            System.out.println("After edit: \"" + document + "\"");
        }

        System.out.println("\nUndoing twice:");
        document = new StringBuilder(undoStack.pop());
        System.out.println("After undo: \"" + document + "\"");
        document = new StringBuilder(undoStack.pop());
        System.out.println("After undo: \"" + document + "\"");
    }
}
```

**How to run:** `java UndoBasic.java`

Each edit pushes the document's state *before* the change onto `undoStack`; undoing pops the most recent snapshot off — classic LIFO behavior, using `ArrayDeque` purely as a stack via `push`/`pop`.

### Level 2 — Intermediate

```java
import java.util.*;

public class UndoRedo {
    static Deque<String> undoStack = new ArrayDeque<>();
    static Deque<String> redoStack = new ArrayDeque<>();
    static StringBuilder document = new StringBuilder();

    static void edit(String text) {
        undoStack.push(document.toString());
        redoStack.clear(); // a fresh edit invalidates any previously undone redo history
        document.append(text);
    }

    static void undo() {
        if (undoStack.isEmpty()) return;
        redoStack.push(document.toString());
        document = new StringBuilder(undoStack.pop());
    }

    static void redo() {
        if (redoStack.isEmpty()) return;
        undoStack.push(document.toString());
        document = new StringBuilder(redoStack.pop());
    }

    public static void main(String[] args) {
        edit("Hello");
        edit(", World");
        edit("!");
        System.out.println("Document: \"" + document + "\"");

        undo();
        System.out.println("After undo: \"" + document + "\"");
        undo();
        System.out.println("After undo: \"" + document + "\"");

        redo();
        System.out.println("After redo: \"" + document + "\"");

        edit(" Goodbye"); // a NEW edit after undoing
        System.out.println("After new edit: \"" + document + "\"");

        redo(); // nothing to redo -- the new edit cleared the redo history
        System.out.println("After attempted redo (should be unchanged): \"" + document + "\"");
    }
}
```

**How to run:** `java UndoRedo.java`

A second `ArrayDeque`, `redoStack`, captures snapshots undone from `undoStack` — `redo()` moves them back. Making a fresh `edit()` after undoing correctly `clear()`s `redoStack`, since a new edit invalidates the "future" that redo would have restored (the same behavior any real text editor's undo/redo exhibits).

### Level 3 — Advanced

```java
import java.util.*;

public class UndoBounded {
    static final int MAX_UNDO_LEVELS = 3;
    static Deque<String> undoStack = new ArrayDeque<>(); // head = most recent, tail = oldest
    static StringBuilder document = new StringBuilder();

    static void edit(String text) {
        undoStack.push(document.toString()); // addFirst -- newest snapshot goes to the HEAD
        if (undoStack.size() > MAX_UNDO_LEVELS) {
            undoStack.removeLast(); // trim the OLDEST snapshot, at the TAIL, once over capacity
        }
        document.append(text);
    }

    static void undo() {
        if (undoStack.isEmpty()) return;
        document = new StringBuilder(undoStack.pop());
    }

    public static void main(String[] args) {
        for (String edit : new String[]{"A", "B", "C", "D", "E"}) {
            edit(edit);
            System.out.println("After edit '" + edit + "': doc=\"" + document + "\" undoStack=" + undoStack);
        }

        System.out.println("\nUndo history is capped at " + MAX_UNDO_LEVELS + " levels -- oldest snapshots were dropped.");
        System.out.println("Attempting to undo all the way back:");
        while (!undoStack.isEmpty()) {
            undo();
            System.out.println("After undo: \"" + document + "\"");
        }
    }
}
```

**How to run:** `java UndoBounded.java`

This is where `Deque`'s double-ended nature earns its keep in a single feature: `push` (stack behavior) adds new snapshots at the **front**, while `removeLast()` explicitly trims from the **back** — the oldest snapshot — once the history grows past `MAX_UNDO_LEVELS`. The undo stack still behaves like a stack for `push`/`pop`, but capacity management reaches directly to the other end.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `undoStack` starts empty; `document` is an empty `StringBuilder`.

`edit("A")`: `undoStack.push("")` (the document's state before this edit) puts `""` at the front — `undoStack` is now `[""]` (size 1, not over the cap of 3). `document` becomes `"A"`.

`edit("B")`: `undoStack.push("A")` puts `"A"` at the front, ahead of the existing `""` — `undoStack` is now `["A", ""]` (size 2). `document` becomes `"AB"`.

`edit("C")`: `undoStack.push("AB")` — `undoStack` is now `["AB", "A", ""]` (size 3, still not over the cap since `3 > 3` is `false`). `document` becomes `"ABC"`.

`edit("D")`: `undoStack.push("ABC")` — `undoStack` becomes `["ABC", "AB", "A", ""]` (size 4). Now `4 > 3` is `true`, so `undoStack.removeLast()` removes the **oldest** snapshot, the empty string at the tail — `undoStack` shrinks back to `["ABC", "AB", "A"]` (size 3). `document` becomes `"ABCD"`. Notice: the original empty-document snapshot is now **gone forever**.

`edit("E")`: similarly, `undoStack.push("ABCD")` grows it to size 4, and `removeLast()` trims the new oldest entry, `"A"` — `undoStack` ends as `["ABCD", "ABC", "AB"]`. `document` becomes `"ABCDE"`.

The final `while (!undoStack.isEmpty())` loop then pops repeatedly: first pop returns `"ABCD"` (`document` becomes `"ABCD"`), second pop returns `"ABC"`, third pop returns `"AB"` — after three pops, `undoStack` is empty, and the loop ends. Critically, the document can **never** be undone all the way back to its original empty state, since that snapshot was silently discarded once the bounded history filled up.

Expected output:
```
After edit 'A': doc="A" undoStack=[]
After edit 'B': doc="AB" undoStack=[A, ]
After edit 'C': doc="ABC" undoStack=[AB, A, ]
After edit 'D': doc="ABCD" undoStack=[ABC, AB, A]
After edit 'E': doc="ABCDE" undoStack=[ABCD, ABC, AB]

Undo history is capped at 3 levels -- oldest snapshots were dropped.
Attempting to undo all the way back:
After undo: "ABCD"
After undo: "ABC"
After undo: "AB"
```

## 7. Gotchas & takeaways

> A bounded undo history that silently discards the oldest entries means the user can eventually lose the ability to undo all the way back to the true original state — as demonstrated above, the empty-document snapshot was quietly dropped once the history filled up, and no amount of further undoing can recover it. If "undo to the original" must always be possible, either don't bound the history, or explicitly retain the very first snapshot separately from the bounded recent-history deque.

- `Deque` supports efficient addition and removal at **both** ends; `push`/`pop` operate on the front (stack/LIFO), `offer`/`poll` add at the back and remove from the front (queue/FIFO).
- `ArrayDeque` is the modern, general-purpose choice for both stack and queue use — generally faster than the legacy `Stack` class and lower-overhead than using `LinkedList` for the same purpose.
- One `ArrayDeque` instance can be used with stack methods in one part of a feature and directly manipulated at both ends (`addFirst`/`removeLast`, etc.) in another, as the bounded-history example shows.
- `Stack` (from Java 1.0) is now considered a legacy type — prefer `Deque`/`ArrayDeque` for new code needing stack behavior.
- `ArrayDeque` does not permit `null` elements (unlike `LinkedList`), since `null` is used internally to signal an empty slot.
