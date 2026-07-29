---
card: data-structures
gi: 11
slug: stack-vs-heap-allocation
title: Stack vs heap allocation
---

## 1. What it is

The **stack** is a fixed-size region of memory holding local variables and method call information, organized as [a stack of frames](0007-recursion-the-call-stack-stack-depth.md), one per active method call — memory here is automatically reclaimed the instant a method returns. The **heap** is a much larger, dynamically managed region holding all objects (anything created with `new`, including arrays and class instances) — memory here is reclaimed later, and indirectly, by the garbage collector once nothing references the object anymore.

## 2. Why & when

Understanding where data lives explains both performance characteristics (stack allocation and deallocation is extremely cheap — just moving a pointer — while heap allocation involves more bookkeeping, and heap objects must eventually be garbage collected) and lifetime rules (a local primitive variable disappears the instant its method returns, but an object on the heap persists as long as *any* reference to it still exists, possibly held by a completely different part of the program).

## 3. Core concept

**What lives where, in Java specifically:** local primitive variables (`int x = 5;` inside a method) live directly on the stack, as part of that method's stack frame. Reference variables *also* live on the stack (the reference itself — the address — is a small fixed-size value), but the *object* that reference points to always lives on the heap, regardless of whether it was created inside a deeply nested method call or at the top level. This is true even for primitives *inside* an object — an `int` field inside a class instance lives on the heap, as part of that object, not on the stack, because it is part of an object whose lifetime is not tied to any single method call.

**Why the stack is fast and automatically managed:** stack allocation is just moving a single pointer (the "stack top") forward to reserve space, and moving it back to release space — an O(1) operation with essentially zero overhead. This works precisely because stack memory follows a strict last-in-first-out discipline: the most recently allocated frame is always the first one freed, matching exactly how function calls return in reverse order of how they were called.

**Why the heap needs a garbage collector, while the stack does not:** heap objects do not follow a simple call-order lifetime — an object might be created inside one method but handed off (via a returned reference, or stored in a field) so that it outlives the method that created it, and gets used by completely unrelated parts of the program for an unpredictable duration. Since there is no simple rule for "when is this heap object safe to free," the JVM must actively track which objects are still reachable (referenced from somewhere still in use) and reclaim only the ones that are not — this ongoing bookkeeping is what a garbage collector does.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A stack frame holding local variables including a reference, which points to an object living separately on the heap">
  <g font-family="sans-serif" font-size="12">
    <text x="150" y="20" fill="#8b949e" text-anchor="middle">stack (method frame)</text>
    <rect x="40" y="30" width="220" height="110" fill="none" stroke="#3fb950"/>
    <text x="150" y="55" fill="#e6edf3" text-anchor="middle" font-size="11">int count = 5</text>
    <text x="150" y="80" fill="#e6edf3" text-anchor="middle" font-size="11">Person p = (address)</text>
    <text x="150" y="120" fill="#8b949e" text-anchor="middle" font-size="10">freed instantly on return</text>
    <text x="520" y="20" fill="#8b949e" text-anchor="middle">heap (dynamically managed)</text>
    <rect x="410" y="30" width="220" height="80" fill="none" stroke="#f0883e"/>
    <text x="520" y="55" fill="#e6edf3" text-anchor="middle" font-size="11">Person object</text>
    <text x="520" y="75" fill="#8b949e" text-anchor="middle" font-size="10">name, age fields</text>
    <text x="520" y="130" fill="#8b949e" text-anchor="middle" font-size="10">freed later, by garbage collector</text>
    <line x1="230" y1="80" x2="410" y2="60" stroke="#79c0ff" marker-end="url(#a18)"/>
    <defs><marker id="a18" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
  </g>
</svg>

The reference variable `p` itself is a small, fixed-size value living on the stack; the actual `Person` object it points to lives separately on the heap, with an independent lifetime.

## 5. Runnable example

The artifact below demonstrates the lifetime difference directly: an object created inside a method, but returned via a reference, outlives that method's own stack frame — something only possible because the object itself lives on the heap, not the stack.

```java
// StackVsHeapAllocation.java
public class StackVsHeapAllocation {

    static class Counter {
        int value;
        Counter(int value) { this.value = value; }
    }

    // The Counter object created here outlives this method's own stack frame.
    static Counter createCounter() {
        int localPrimitive = 42; // lives on the stack, gone the instant this method returns
        Counter c = new Counter(10); // 'c' (the reference) is on the stack; the object is on the heap
        return c; // only the reference is returned; the object itself was never "on" this frame
    }

    public static void main(String[] args) {
        Counter counter = createCounter();
        // createCounter()'s stack frame is gone by now, including its local 'localPrimitive'
        // and its local reference variable 'c' - but the Counter OBJECT itself is still alive,
        // because 'counter' here in main() still references it.
        System.out.println("counter.value after method returned: " + counter.value);

        counter.value = 100; // mutating the heap object through the reference held in main()
        System.out.println("counter.value after mutation: " + counter.value);
    }
}
```

**How to run:** save as `StackVsHeapAllocation.java`, then run `java StackVsHeapAllocation.java`.

## 6. Walkthrough

1. `createCounter()` is called: a new stack frame is pushed, containing the local variable `localPrimitive` (an `int`, directly on the stack) and the local reference variable `c` (also on the stack, but holding the *address* of a newly created `Counter` object).
2. `new Counter(10)` allocates the actual `Counter` object on the heap — this allocation is independent of `createCounter`'s stack frame; the object exists in a separate memory region entirely.
3. `return c;` copies the value of `c` (the heap address) back to the caller. `createCounter`'s entire stack frame — including `localPrimitive` and the local variable `c` itself — is then popped and gone.
4. Back in `main`, `counter` now holds that same address, and `counter.value` correctly reads `10` — proving the `Counter` object survived past the destruction of the stack frame that originally created it, because the object itself was never stored *on* that stack frame; it lived independently on the heap the entire time.
5. `counter.value = 100;` mutates the heap object directly through `main`'s reference — this change would be visible from anywhere else in the program that also happens to hold a reference to this same object.

## 7. Gotchas & takeaways

> Gotcha: assuming an object "disappears" as soon as the method that created it returns is incorrect and can lead to confusion when debugging — an object on the heap persists for as long as *any* reachable reference to it exists, anywhere in the program, completely independent of which method originally created it.

- Local primitives and reference variables themselves live on the stack, freed automatically and instantly when their method returns; the objects those references point to live on the heap, with an independent lifetime managed by the garbage collector.
- Stack allocation/deallocation is extremely cheap (moving a pointer); heap allocation involves more bookkeeping, and heap memory reclamation is deferred to the garbage collector.
- Related concepts: [Recursion, the call stack & stack depth](0007-recursion-the-call-stack-stack-depth.md) (the stack's structure in more detail), [Primitives vs references](0010-primitives-vs-references.md) (why references themselves are small stack-resident values pointing at heap-resident objects).
