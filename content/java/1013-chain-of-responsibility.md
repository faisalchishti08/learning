---
card: java
gi: 1013
slug: chain-of-responsibility
title: Chain of Responsibility
---

## 1. What it is

The **Chain of Responsibility** pattern passes a request along a chain of handler objects until one of them handles it. Each handler decides independently whether it can process the request; if it can't (or after it's done some partial work), it forwards the request to the next handler in the chain. The sender of the request doesn't know — and doesn't need to know — which handler will ultimately deal with it, or how many handlers the request passes through first.

## 2. Why & when

A single method with a growing `if`/`else if` chain deciding how to handle different request types couples all that decision logic together in one place, and the sender has to know the full decision tree up front. Chain of Responsibility breaks that decision apart into independent handler objects, each responsible for one kind of check or one kind of processing, linked together in a sequence — a request travels down the chain, and whichever handler recognizes it deals with it (optionally still letting it continue further down the chain). Adding a new handler means inserting it into the chain, not editing a shared decision method.

Reach for Chain of Responsibility when a request might need to pass through several independent, sequential checks or processing stages — a support-ticket escalation system routing a ticket up through levels of staff, a middleware/filter pipeline processing an HTTP request through logging, authentication, and rate-limiting steps in order. It's unnecessary when there's exactly one handler for every request type — that's just a direct method call or a simple lookup, no chain required.

## 3. Core concept

```
abstract class SupportHandler {
    protected SupportHandler next;
    SupportHandler setNext(SupportHandler next) { this.next = next; return this; }

    void handle(String issue, int severity) {
        if (canHandle(severity)) {
            process(issue);
        } else if (next != null) {
            next.handle(issue, severity); // pass it further down the chain
        } else {
            System.out.println("No handler could resolve: " + issue);
        }
    }

    abstract boolean canHandle(int severity);
    abstract void process(String issue);
}

class Tier1Support extends SupportHandler {
    boolean canHandle(int severity) { return severity <= 1; }
    void process(String issue) { System.out.println("Tier1 resolved: " + issue); }
}
class Tier2Support extends SupportHandler {
    boolean canHandle(int severity) { return severity <= 3; }
    void process(String issue) { System.out.println("Tier2 resolved: " + issue); }
}

SupportHandler chain = new Tier1Support();
chain.setNext(new Tier2Support());
chain.handle("password reset", 1);  // Tier1 handles it directly
chain.handle("data corruption", 3); // Tier1 can't -> forwarded to Tier2
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request passing through Tier1Support, then Tier2Support, then Tier3Support in sequence until one handler accepts it">
  <rect x="20" y="55" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Tier1Support</text>

  <rect x="230" y="55" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="305" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Tier2Support</text>

  <rect x="440" y="55" width="150" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="515" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Tier3Support</text>

  <line x1="170" y1="75" x2="230" y2="75" stroke="#8b949e" marker-end="url(#a)"/>
  <text x="200" y="65" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">can't handle</text>
  <line x1="380" y1="75" x2="440" y2="75" stroke="#8b949e" marker-end="url(#a)"/>
  <text x="410" y="65" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">can't handle</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A request enters at `Tier1Support` and moves down the chain only as far as needed — the first handler that accepts it stops the chain.

## 5. Runnable example

Scenario: a support-ticket escalation system, evolving from a single method with a hardcoded severity check into a proper handler chain that new tiers can join without modifying existing tiers.

### Level 1 — Basic

```java
// File: ChainBasic.java
public class ChainBasic {
    static void handle(String issue, int severity) {
        if (severity <= 1) {
            System.out.println("Tier1 resolved: " + issue);
        } else if (severity <= 3) {
            System.out.println("Tier2 resolved: " + issue);
        } else {
            System.out.println("No handler could resolve: " + issue);
        }
    }

    public static void main(String[] args) {
        handle("password reset", 1);
        handle("data corruption", 3);
        handle("server outage", 5);
    }
}
```

**How to run:** save as `ChainBasic.java`, then `javac ChainBasic.java && java ChainBasic` (JDK 17+).

Expected output:
```
Tier1 resolved: password reset
Tier2 resolved: data corruption
No handler could resolve: server outage
```

All the escalation logic lives in one method — adding a Tier3 for the highest-severity issues means editing this method directly, and it grows harder to follow as more tiers are added.

### Level 2 — Intermediate

```java
// File: ChainIntermediate.java
abstract class SupportHandler {
    protected SupportHandler next;
    SupportHandler setNext(SupportHandler next) { this.next = next; return this; }

    void handle(String issue, int severity) {
        if (canHandle(severity)) {
            process(issue);
        } else if (next != null) {
            next.handle(issue, severity);
        } else {
            System.out.println("No handler could resolve: " + issue);
        }
    }

    abstract boolean canHandle(int severity);
    abstract void process(String issue);
}

class Tier1Support extends SupportHandler {
    boolean canHandle(int severity) { return severity <= 1; }
    void process(String issue) { System.out.println("Tier1 resolved: " + issue); }
}
class Tier2Support extends SupportHandler {
    boolean canHandle(int severity) { return severity <= 3; }
    void process(String issue) { System.out.println("Tier2 resolved: " + issue); }
}

public class ChainIntermediate {
    public static void main(String[] args) {
        SupportHandler chain = new Tier1Support();
        chain.setNext(new Tier2Support());

        chain.handle("password reset", 1);
        chain.handle("data corruption", 3);
        chain.handle("server outage", 5);
    }
}
```

**How to run:** save as `ChainIntermediate.java`, then `javac ChainIntermediate.java && java ChainIntermediate` (JDK 17+).

Expected output:
```
Tier1 resolved: password reset
Tier2 resolved: data corruption
No handler could resolve: server outage
```

The real-world concern added: escalation logic is now split across independent handler classes, each linked to the next. `Tier1Support` and `Tier2Support` know nothing about each other's internal logic, only that a `next` handler exists to forward to.

### Level 3 — Advanced

```java
// File: ChainAdvanced.java
abstract class SupportHandler {
    protected SupportHandler next;
    SupportHandler setNext(SupportHandler next) { this.next = next; return this; }

    void handle(String issue, int severity) {
        if (canHandle(severity)) {
            process(issue);
            // Some handlers ALSO forward even after handling -- e.g. for logging
            // or escalation visibility -- a realistic wrinkle beyond simple stop-on-handle.
            if (shouldEscalateAfterHandling() && next != null) {
                next.logEscalation(issue, severity);
            }
        } else if (next != null) {
            next.handle(issue, severity);
        } else {
            System.out.println("No handler could resolve: " + issue);
        }
    }

    boolean shouldEscalateAfterHandling() { return false; }
    void logEscalation(String issue, int severity) {
        System.out.println("[log] " + this.getClass().getSimpleName() + " notified of: " + issue);
    }

    abstract boolean canHandle(int severity);
    abstract void process(String issue);
}

class Tier1Support extends SupportHandler {
    boolean canHandle(int severity) { return severity <= 1; }
    void process(String issue) { System.out.println("Tier1 resolved: " + issue); }
}

// A NEW tier added purely by inserting it into the chain -- Tier1Support and
// Tier2Support required zero changes to accommodate it.
class Tier2Support extends SupportHandler {
    boolean canHandle(int severity) { return severity <= 3; }
    void process(String issue) { System.out.println("Tier2 resolved: " + issue); }
    @Override boolean shouldEscalateAfterHandling() { return true; } // notify Tier3 anyway
}

class Tier3Support extends SupportHandler {
    boolean canHandle(int severity) { return severity <= 10; }
    void process(String issue) { System.out.println("Tier3 resolved: " + issue); }
}

public class ChainAdvanced {
    public static void main(String[] args) {
        SupportHandler chain = new Tier1Support();
        chain.setNext(new Tier2Support().setNext(new Tier3Support()));

        chain.handle("password reset", 1);
        chain.handle("data corruption", 3);  // Tier2 handles, but also notifies Tier3
        chain.handle("server outage", 8);
    }
}
```

**How to run:** save as `ChainAdvanced.java`, then `javac ChainAdvanced.java && java ChainAdvanced` (JDK 17+).

Expected output:
```
Tier1 resolved: password reset
Tier2 resolved: data corruption
[log] Tier3Support notified of: data corruption
Tier3 resolved: server outage
```

The production-flavored hard case: `Tier2Support` overrides `shouldEscalateAfterHandling()` to notify the next tier even after fully handling an issue itself — a realistic pattern where "handled" doesn't always mean "the chain stops caring," and `Tier3Support` was added as a brand-new class without touching `Tier1Support` or `Tier2Support` at all.

## 6. Walkthrough

Tracing `chain.handle("data corruption", 3)` in `ChainAdvanced.main`:

1. `chain` is `Tier1Support`. `chain.handle("data corruption", 3)` checks `canHandle(3)`: `3 <= 1` is `false`, so it forwards via `next.handle("data corruption", 3)` — `next` is the `Tier2Support` instance.
2. `Tier2Support.handle` checks `canHandle(3)`: `3 <= 3` is `true`, so `process("data corruption")` runs, printing `"Tier2 resolved: data corruption"`.
3. After processing, `shouldEscalateAfterHandling()` is checked — `Tier2Support` overrides it to return `true` (unlike `Tier1Support` and `Tier3Support`, which use the base default of `false`), and `next != null` (it's `Tier3Support`), so `next.logEscalation("data corruption", 3)` runs.
4. `logEscalation` is inherited unchanged from `SupportHandler` by `Tier3Support` — it prints `"[log] Tier3Support notified of: data corruption"`, using `this.getClass().getSimpleName()` to identify which handler is logging (here, `Tier3Support`, since `logEscalation` was called *on* the `Tier3Support` instance).
5. Control returns back up through the chain of method calls (`Tier1Support.handle` → `Tier2Support.handle` → done), and `main` moves to the next line.
6. Compare with `chain.handle("server outage", 8)`: `Tier1Support` and `Tier2Support` both fail their `canHandle` checks (`8 <= 1` and `8 <= 3` are both false), forwarding twice until `Tier3Support.canHandle(8)` (`8 <= 10`) succeeds, printing `"Tier3 resolved: server outage"` — and since `Tier3Support` doesn't override `shouldEscalateAfterHandling()`, no further logging happens after it.

## 7. Gotchas & takeaways

> **Gotcha:** a chain with no handler that unconditionally accepts everything can silently drop a request if none of the handlers claim it — as seen with `"No handler could resolve"` in the earlier examples. Either ensure the last handler in the chain has a catch-all `canHandle` (like `Tier3Support`'s `severity <= 10` covering everything realistic), or make the "nothing handled this" case an explicit, visible failure rather than a silent no-op.

- Chain of Responsibility passes a request through a sequence of independent handler objects, each deciding whether to process it, forward it, or both.
- Adding a new handler means inserting it into the chain — existing handlers need no changes, satisfying [SOLID — Open/Closed](0990-solid-open-closed.md).
- A handler can choose to both process a request *and* forward it further (as `Tier2Support` does for logging), rather than treating "handled" and "forwarded" as mutually exclusive.
- The sender only ever talks to the first handler in the chain — it has no idea how many handlers the request actually passes through.
- Don't reach for a full handler chain when there's exactly one handler per request type — a direct dispatch or lookup table is simpler there.
- This pattern is the conceptual basis for servlet filter chains, middleware pipelines in web frameworks, and many logging/interceptor frameworks.
