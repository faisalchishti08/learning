---
card: data-structures
gi: 67
slug: undo-redo-the-call-stack
title: Undo/redo & the call stack
---

## 1. What it is

**Undo/redo** is a feature built from two stacks: an undo stack, holding actions you can reverse, and a redo stack, holding actions you just undid and could reapply. The **call stack** is a stack the JVM itself maintains, tracking which functions are currently running — every method call pushes a frame, every return pops one.

## 2. Why & when

Undo/redo is the direct, everyday application of LIFO order: the most recent action is always the first one undone. The call stack matters because it explains recursion, `StackOverflowError`, and how local variables and return addresses are managed automatically — every recursive algorithm you write is secretly using this stack.

## 3. Core concept

**Undo/redo with two stacks.** Every time the user performs an action, push it onto the `undoStack`. `undo()` pops the most recent action off `undoStack`, reverses its effect, and pushes it onto `redoStack`. `redo()` pops from `redoStack`, reapplies the action, and pushes it back onto `undoStack`. A brand-new action after an undo should clear the `redoStack`, since the old redo history no longer makes sense once the timeline has branched.

**The call stack — how it works.** Every method call creates a **stack frame**: a block holding that call's local variables, parameters, and the address to return to. Calling a method pushes its frame; returning pops it. This is exactly why local variables in different calls do not interfere — each call has its own frame.

**Recursion depth and `StackOverflowError`.** Because each recursive call pushes another frame without popping until it returns, a recursion that goes too deep (or never reaches its base case) keeps pushing frames until the JVM's call stack runs out of space, throwing `StackOverflowError`. This is the same LIFO structure as any other stack — just one you do not manage explicitly.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two panels: left shows undo and redo stacks after a sequence of type, type, undo actions; right shows the call stack growing as factorial calls itself recursively">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="16" fill="#8b949e">undo/redo after: type A, type B, undo()</text>
    <text x="20" y="40" fill="#e6edf3">undoStack: [ typeA ]</text>
    <text x="20" y="60" fill="#79c0ff">redoStack: [ typeB ]</text>
    <text x="380" y="16" fill="#8b949e">call stack for factorial(3)</text>
    <rect x="380" y="30" width="120" height="22" fill="#161b22" stroke="#8b949e"/><text x="440" y="45" fill="#e6edf3" text-anchor="middle" font-size="9">factorial(1)</text>
    <rect x="380" y="54" width="120" height="22" fill="#161b22" stroke="#8b949e"/><text x="440" y="69" fill="#e6edf3" text-anchor="middle" font-size="9">factorial(2)</text>
    <rect x="380" y="78" width="120" height="22" fill="#0d1117" stroke="#f0883e"/><text x="440" y="93" fill="#e6edf3" text-anchor="middle" font-size="9">factorial(3) -- entry point</text>
    <text x="440" y="115" fill="#f0883e" text-anchor="middle" font-size="9">deepest call is on top</text>
  </g>
</svg>

The undo stack holds reversible past actions; the redo stack holds undone actions ready to reapply. The call stack's deepest, most-recent call sits on top, just like any stack.

## 5. Runnable example

```java
// UndoRedoAndCallStack.java
import java.util.ArrayDeque;
import java.util.Deque;

public class UndoRedoAndCallStack {

    // Basic: a two-stack undo/redo for simple text-append actions.
    static class TextEditor {
        private StringBuilder text = new StringBuilder();
        private Deque<String> undoStack = new ArrayDeque<>(); // holds text BEFORE each action
        private Deque<String> redoStack = new ArrayDeque<>();

        void type(String s) {
            undoStack.push(text.toString()); // save state before the change
            text.append(s);
            redoStack.clear(); // new action invalidates any old redo history
        }

        void undo() {
            if (undoStack.isEmpty()) return;
            redoStack.push(text.toString());
            text = new StringBuilder(undoStack.pop());
        }

        void redo() {
            if (redoStack.isEmpty()) return;
            undoStack.push(text.toString());
            text = new StringBuilder(redoStack.pop());
        }

        String current() { return text.toString(); }
    }

    static void basicLevel() {
        TextEditor editor = new TextEditor();
        editor.type("Hello");
        editor.type(" World");
        System.out.println("basic: after typing -> \"" + editor.current() + "\"");
        editor.undo();
        System.out.println("basic: after undo -> \"" + editor.current() + "\"");
        editor.redo();
        System.out.println("basic: after redo -> \"" + editor.current() + "\"");
    }

    // Intermediate: a new action after undo must clear the redo stack.
    static void intermediateLevel() {
        TextEditor editor = new TextEditor();
        editor.type("A");
        editor.type("B");
        editor.undo(); // back to "A"; redoStack now holds "AB"
        editor.type("C"); // new branch: redoStack should be cleared
        editor.redo(); // no-op: nothing to redo
        System.out.println("intermediate: after undo, new type, then redo -> \"" + editor.current() + "\" (expected \"AC\")");
    }

    // Advanced: the call stack itself, shown via recursion depth and a StackOverflowError demonstration.
    static int factorial(int n, int depth) {
        System.out.println("advanced: entering factorial(" + n + "), call-stack depth -> " + depth);
        if (n <= 1) return 1;
        int result = n * factorial(n - 1, depth + 1); // this line's frame stays on the stack until the recursive call returns
        System.out.println("advanced: returning from factorial(" + n + "), popping frame");
        return result;
    }

    static void advancedLevel() {
        System.out.println("advanced: factorial(4) -> " + factorial(4, 1));

        try {
            recurseForever(0);
        } catch (StackOverflowError e) {
            System.out.println("advanced: caught StackOverflowError -- the call stack ran out of frames");
        }
    }

    static int recurseForever(int n) {
        return 1 + recurseForever(n + 1); // no base case: pushes a frame forever until the stack overflows
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `UndoRedoAndCallStack.java`, then run `java UndoRedoAndCallStack.java`.

## 6. Walkthrough

1. `basicLevel()` types `"Hello"` (pushing `""` onto `undoStack`), then `" World"` (pushing `"Hello"`). `current()` is `"Hello World"`. `undo()` pops `"Hello"` off `undoStack`, restores it, and pushes `"Hello World"` onto `redoStack`. `redo()` pops `"Hello World"` back off `redoStack`, restoring the full text.
2. `intermediateLevel()` types `"A"`, then `"B"` (text is `"AB"`), then `undo()`s back to `"A"` — `redoStack` now holds `"AB"`. Typing `"C"` appends to get `"AC"` and clears `redoStack`, since redoing `"AB"` no longer makes sense after a new branch was typed. The following `redo()` is correctly a no-op, leaving `"AC"`.
3. `advancedLevel()`'s `factorial(4, 1)` pushes a call-stack frame for each recursive call before the multiplication can complete — `factorial(4)` cannot finish computing `4 * factorial(3)` until `factorial(3)`'s entire call (including its own nested calls) returns. The print statements show frames being pushed on the way down (`depth` increasing) and implicitly popped on the way back up. `recurseForever` has no base case, so it pushes frames without ever popping, until the JVM's call stack is exhausted and throws `StackOverflowError`.

## 7. Gotchas & takeaways

> Gotcha: forgetting to clear `redoStack` on a new action after an `undo()` leaves a "dangling" redo history that reapplies stale state — always clear it, or the undo/redo timeline becomes inconsistent with what the user actually did.

- Undo/redo needs two stacks: one for reversible past actions, one for undone actions available to reapply.
- A new action after an undo must clear the redo stack, since it invalidates that branch of history.
- The JVM's call stack is a real stack: each method call pushes a frame, each return pops it.
- Deep or infinite recursion without a base case keeps pushing frames until `StackOverflowError` is thrown.
- Related concepts: [Recursion & the call stack / stack depth](0007-recursion-the-call-stack-stack-depth.md), [Recursive vs iterative tradeoffs](0008-recursive-vs-iterative-tradeoffs.md), [LIFO semantics](0062-lifo-semantics.md).
