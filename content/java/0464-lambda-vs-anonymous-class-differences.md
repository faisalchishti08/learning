---
card: java
gi: 464
slug: lambda-vs-anonymous-class-differences
title: Lambda vs anonymous class differences
---

## 1. What it is

Lambdas and anonymous classes both let you supply a piece of behaviour inline, without a separate named class file, and both can implement a functional interface — but they are not the same mechanism underneath. They differ in what `this` refers to inside them, whether they can have their own fields and multiple methods, how they're compiled, and whether they can implement more than one abstract method.

## 2. Why & when

Anonymous classes existed long before lambdas and remain the only option when you need more than a lambda can offer: implementing an interface with **more than one** abstract method, extending an abstract (non-interface) class, declaring your own instance fields, or needing `this` to refer to the anonymous class instance itself rather than the surrounding object. Lambdas are strictly narrower by design — they exist only to implement functional interfaces (exactly one abstract method) — and that narrowness is what makes them so much lighter to write.

You reach for a lambda whenever the target is a genuine functional interface and you don't need any of the anonymous-class-only features. You reach for an anonymous class when the interface has more than one method to implement, when you're subclassing a class rather than implementing an interface, or when you specifically need a private `this` scope distinct from the enclosing object — situations lambdas cannot express at all, not just situations where they'd be awkward.

## 3. Core concept

```java
Runnable lambdaRunnable = () -> System.out.println("lambda this: " + this);

Runnable anonRunnable = new Runnable() {
    @Override
    public void run() {
        System.out.println("anonymous class this: " + this);
    }
};
```

Inside the lambda, `this` refers to the **enclosing instance** (whatever `this` would mean at the point the lambda is written) — a lambda has no `this` of its own. Inside the anonymous class, `this` refers to the anonymous class instance itself — a genuinely separate object with its own identity.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A lambda shares this with its enclosing instance; an anonymous class creates its own separate instance with its own this">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="260" height="120" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="50" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Lambda</text>
  <text x="160" y="72" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">no own "this"</text>
  <text x="160" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">"this" = enclosing instance</text>
  <text x="160" y="108" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">one method only</text>
  <text x="160" y="126" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">no own fields</text>

  <rect x="350" y="30" width="260" height="120" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="480" y="50" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Anonymous class</text>
  <text x="480" y="72" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">has its own "this"</text>
  <text x="480" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">separate object identity</text>
  <text x="480" y="108" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">can implement 2+ methods</text>
  <text x="480" y="126" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">can have its own fields</text>
</svg>

The lambda "sees through" to the surrounding object; the anonymous class is genuinely its own object.

## 5. Runnable example

Scenario: an event handler that needs to know which object it belongs to — evolved from a lambda that transparently reads the enclosing instance's field, through an anonymous class that shadows the same field with its own, to a case requiring an anonymous class because the target has two abstract methods a lambda simply cannot implement.

### Level 1 — Basic

```java
public class LambdaThisBasic {
    private final String label = "outer";

    Runnable makeLambdaRunnable() {
        return () -> System.out.println("lambda sees label: " + label);
    }

    public static void main(String[] args) {
        LambdaThisBasic outer = new LambdaThisBasic();
        outer.makeLambdaRunnable().run();
    }
}
```

**How to run:** `java LambdaThisBasic.java`

Expected output:
```
lambda sees label: outer
```

`label` inside the lambda resolves directly to `LambdaThisBasic.this.label` — the lambda has no scope of its own to introduce a competing `label`, so there's no ambiguity: it always means the enclosing instance's field.

### Level 2 — Intermediate

```java
public class AnonymousThisComparison {
    private final String label = "outer";

    Runnable makeAnonymousRunnable() {
        return new Runnable() {
            private final String label = "anonymous"; // shadows the outer field within THIS scope
            @Override
            public void run() {
                System.out.println("anonymous 'this.label': " + this.label);
                System.out.println("outer 'AnonymousThisComparison.this.label': "
                        + AnonymousThisComparison.this.label);
            }
        };
    }

    public static void main(String[] args) {
        AnonymousThisComparison outer = new AnonymousThisComparison();
        outer.makeAnonymousRunnable().run();
    }
}
```

**How to run:** `java AnonymousThisComparison.java`

Expected output:
```
anonymous 'this.label': anonymous
outer 'AnonymousThisComparison.this.label': outer
```

The real-world concern this reveals: an anonymous class can declare its **own** field named `label`, which shadows the outer one — `this.label` inside the anonymous class refers to *its own* field, and reaching the outer object's field requires the qualified form `AnonymousThisComparison.this.label`. A lambda has no such shadowing scope at all — there is only ever one `label` reachable from inside it.

### Level 3 — Advanced

```java
import java.awt.event.*;

public class AnonymousMultiMethodInterface {
    // A hand-rolled interface with TWO abstract methods -- NOT a functional interface,
    // so no lambda can ever implement it. An anonymous class is the only inline option.
    interface Lifecycle {
        void onStart();
        void onStop();
    }

    static void run(Lifecycle lifecycle) {
        lifecycle.onStart();
        System.out.println("...doing work...");
        lifecycle.onStop();
    }

    public static void main(String[] args) {
        run(new Lifecycle() {
            private long startedAt;

            @Override
            public void onStart() {
                startedAt = System.nanoTime();
                System.out.println("started");
            }

            @Override
            public void onStop() {
                long elapsedNanos = System.nanoTime() - startedAt;
                System.out.println("stopped, ran for >= 0 nanos: " + (elapsedNanos >= 0));
            }
        });
    }
}
```

**How to run:** `java AnonymousMultiMethodInterface.java`

Expected output:
```
started
...doing work...
stopped, ran for >= 0 nanos: true
```

`Lifecycle` has two abstract methods, `onStart` and `onStop` — this disqualifies it from being a functional interface entirely, so `run(() -> ...)` could never compile here. The anonymous class is not just more convenient in this case, it is the *only* inline option; it also needs its own field (`startedAt`) to pass state from `onStart` to `onStop`, another capability a lambda does not have.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `run(...)` is called with a newly constructed anonymous class instance implementing `Lifecycle`.

Inside `run`, `lifecycle.onStart()` executes first. This runs the anonymous class's `onStart` override: `startedAt = System.nanoTime()` records the current time into the anonymous class's own field, and `"started"` is printed.

Back in `run`, `"...doing work..."` prints next, representing whatever the caller's actual work would be between start and stop.

Then `lifecycle.onStop()` executes. This runs `onStop`, which reads `startedAt` — the **same field** `onStart` wrote a moment earlier, because both methods belong to the same anonymous class instance and share its field storage. `elapsedNanos = System.nanoTime() - startedAt` computes how much time passed between the two calls. `elapsedNanos >= 0` checks that this is non-negative (it always will be, since `System.nanoTime()` is monotonically non-decreasing during the life of a single program run), and prints the result.

```
run(lifecycle)
  lifecycle.onStart()  --> startedAt field written
  "...doing work..."
  lifecycle.onStop()   --> startedAt field read back, elapsed computed
```

This state-sharing between two methods on one object — `onStart` writes a field, `onStop` reads it back — is exactly the capability a lambda lacks: a lambda has no fields of its own to persist state in between separate invocations of separate methods, because a lambda can only ever implement one method to begin with.

## 7. Gotchas & takeaways

> Don't assume a lambda's `this` behaves like an anonymous class's `this` just because both "look like" inline behaviour. Code that relies on `this` referring to the handler object itself — registering `this` as a listener on itself, or comparing `this` for identity — needs an anonymous class (or a full named class); a lambda's `this` will silently mean something different (the enclosing instance), which is a common source of confusion when converting older anonymous-class code to lambdas without checking for `this` usage first.

- A lambda can only ever implement a functional interface (exactly one abstract method) — an anonymous class can implement any interface or extend any class, with any number of methods.
- Inside a lambda, `this` refers to the enclosing instance; inside an anonymous class, `this` refers to the anonymous class instance itself, a genuinely separate object.
- An anonymous class can declare its own fields to hold state between its method calls; a lambda cannot, since it has no persistent scope of its own beyond captured (effectively-final) local variables.
- When converting old anonymous-class code to a lambda, check for any use of `this`, multiple overridden methods, or instance fields on the anonymous class first — any of those means the conversion isn't a safe, behavior-preserving change.
- Lambdas are compiled very differently under the hood (via `invokedynamic`, generating the implementing class lazily at runtime) compared to anonymous classes (which the compiler generates as an ordinary `.class` file at compile time, such as `Outer$1.class`) — this is invisible in day-to-day coding but explains why lambdas have lower startup overhead per unique lambda expression.
