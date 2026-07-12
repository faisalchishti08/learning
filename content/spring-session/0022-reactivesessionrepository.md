---
card: spring-session
gi: 22
slug: reactivesessionrepository
title: "ReactiveSessionRepository"
---

## 1. What it is

`ReactiveSessionRepository<S extends Session>` is the reactive counterpart to `SessionRepository` (card 0002) — same core responsibility (create, save, find, delete sessions), but every method returns a `Mono` instead of a blocking value, so implementations (like the Redis-backed `ReactiveRedisSessionRepository`) can perform their store I/O without ever blocking the calling thread.

## 2. Why & when

Card 0021 introduced *why* reactive session support exists at the framework level (`WebSession`, non-blocking WebFlux integration); this card is about the actual repository interface underneath that integration — the reactive equivalent of the abstraction covered in card 0002, worth understanding on its own terms for anyone writing code that interacts with sessions programmatically inside a reactive application, rather than only through the ordinary `WebSession` parameter injection.

Reach for understanding `ReactiveSessionRepository` directly when:

- Building reactive admin tooling or programmatic session management (an active-sessions API, a force-logout endpoint) inside a WebFlux application — this requires composing `Mono`-returning repository calls correctly, not the blocking patterns from card 0002.
- Writing a custom reactive session store implementation for a backend Spring Session doesn't support out of the box — understanding the exact contract (`createSession`, `save`, `findById`, `deleteById`, all `Mono`-returning) is the starting point.
- Debugging why a piece of session-related code that looks correct doesn't actually execute — a very common cause in reactive code is constructing a `Mono` chain without ever subscribing to it (returning it from a controller counts as an implicit subscription, but code outside that context needs its own explicit subscription or composition).

## 3. Core concept

Think of `SessionRepository`'s `S findById(String id)` as a phone call where you stay on the line, actively waiting, until the person you called finishes looking something up and reads it back to you — you're occupied the entire time. `ReactiveSessionRepository`'s `Mono<S> findById(String id)` is more like leaving a voicemail asking them to look it up and text you the answer whenever they have it — you hang up immediately (the calling thread is freed) and go do something else, and you (or whoever's watching for the text — the reactive pipeline's downstream operators) react the moment the answer actually arrives.

```java
public interface ReactiveSessionRepository<S extends Session> {
    Mono<S> createSession();
    Mono<Void> save(S session);
    Mono<S> findById(String id);
    Mono<Void> deleteById(String id);
}
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Every ReactiveSessionRepository method returns a Mono representing a future result, not the result itself">
  <rect x="30" y="70" width="200" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">findById(id)</text>
  <text x="130" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">called — returns immediately</text>

  <rect x="290" y="70" width="140" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="360" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Mono&lt;Session&gt;</text>
  <text x="360" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">not yet resolved</text>

  <rect x="480" y="70" width="140" height="60" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="550" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">subscriber notified</text>
  <text x="550" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">when store I/O completes</text>

  <line x1="230" y1="100" x2="285" y2="100" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="430" y1="100" x2="475" y2="100" stroke="#3fb950" stroke-width="1.5" stroke-dasharray="4"/>
</svg>

Nothing happens between the second and third box until something subscribes to the `Mono` — an unsubscribed `Mono` never actually executes its underlying operation.

## 5. Runnable example

The scenario: interacting with `ReactiveSessionRepository` directly to build a reactive admin lookup endpoint, growing to compose multiple repository calls correctly within one reactive pipeline (look up, then conditionally delete), and finally to handle the common "forgot to subscribe" bug explicitly, since it's one of the most frequent mistakes when working with this API for the first time.

### Level 1 — Basic

```java
// ReactiveSessionLookupController.java
import org.springframework.session.MapSession;
import org.springframework.session.ReactiveSessionRepository;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

@RestController
public class ReactiveSessionLookupController {

    private final ReactiveSessionRepository<? extends org.springframework.session.Session> sessionRepository;

    public ReactiveSessionLookupController(
            ReactiveSessionRepository<? extends org.springframework.session.Session> sessionRepository) {
        this.sessionRepository = sessionRepository;
    }

    @GetMapping("/admin/sessions/{id}")
    public Mono<String> describe(@PathVariable String id) {
        return sessionRepository.findById(id)
                .map(session -> "Session " + session.getId()
                        + " created " + session.getCreationTime()
                        + ", expires in " + session.getMaxInactiveInterval())
                .defaultIfEmpty("No session found for ID: " + id);
    }
}
```

**How to run:** with a reactive Redis session repository configured (card 0021), call `GET /admin/sessions/<a-real-session-id>`. Expected output: a description string built entirely through reactive composition (`.map(...)`, `.defaultIfEmpty(...)`) — the controller method returns a `Mono<String>`, and WebFlux itself subscribes to it when producing the actual HTTP response, which is what finally triggers the underlying Redis lookup to execute.

### Level 2 — Intermediate

A real admin action — "delete this session if it belongs to a specific suspicious client" — requires composing a lookup and a conditional deletion within a single reactive chain, since the deletion decision depends on the lookup's result.

```java
import org.springframework.session.ReactiveSessionRepository;
import org.springframework.session.Session;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

@RestController
public class ConditionalSessionDeletionController {

    private final ReactiveSessionRepository<? extends Session> sessionRepository;

    public ConditionalSessionDeletionController(
            ReactiveSessionRepository<? extends Session> sessionRepository) {
        this.sessionRepository = sessionRepository;
    }

    @DeleteMapping("/admin/sessions/{id}/if-flagged")
    public Mono<String> deleteIfFlagged(@PathVariable String id) {
        return sessionRepository.findById(id)
                .flatMap(session -> {
                    Boolean flagged = session.getAttribute("flaggedSuspicious");
                    if (Boolean.TRUE.equals(flagged)) {
                        return sessionRepository.deleteById(id)
                                .thenReturn("Session " + id + " was flagged and has been deleted.");
                    }
                    return Mono.just("Session " + id + " exists but is not flagged — left untouched.");
                })
                .defaultIfEmpty("No session found for ID: " + id);
    }
}
```

**How to run:** call this endpoint against a session that has `flaggedSuspicious=true` set as an attribute, and separately against one without it. Expected behavior: the flagged session is genuinely deleted from the store (verify via a subsequent lookup returning "no session found"), while the unflagged one remains present and unaffected — both outcomes correctly composed through `.flatMap(...)`, which is the operator needed here specifically because the inner operation (`deleteById`) itself returns a `Mono`, unlike `.map(...)`'s use in Level 1 for a plain, already-available value transformation.

What changed: this demonstrates the essential distinction between `.map(...)` (for transforming an already-resolved value) and `.flatMap(...)` (for chaining to *another* asynchronous operation) — getting this wrong is one of the most common sources of subtle bugs in reactive code, including code that compiles fine but produces a `Mono<Mono<T>>` instead of the intended flattened `Mono<T>`.

### Level 3 — Advanced

Code outside of a WebFlux-managed request/response cycle (a scheduled background task, for instance) must explicitly subscribe to a `Mono` for it to actually execute — this is different from a controller method, where returning the `Mono` implicitly hands subscription responsibility to the framework. Forgetting this in standalone code is a very common bug where the described operation silently never runs.

```java
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.session.ReactiveSessionRepository;
import org.springframework.session.Session;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Mono;

@Component
public class ScheduledSessionAudit {

    private final ReactiveSessionRepository<? extends Session> sessionRepository;

    public ScheduledSessionAudit(ReactiveSessionRepository<? extends Session> sessionRepository) {
        this.sessionRepository = sessionRepository;
    }

    @Scheduled(fixedRate = 3_600_000) // hourly
    public void auditKnownFlaggedSession() {
        Mono<Void> auditOperation = sessionRepository.findById("known-flagged-session-id")
                .flatMap(session -> {
                    System.out.println("Audit: session still active — " + session.getId());
                    return Mono.<Void>empty();
                })
                .switchIfEmpty(Mono.fromRunnable(() ->
                        System.out.println("Audit: flagged session no longer exists — good.")));

        // WITHOUT this explicit subscribe(), the entire operation above NEVER executes —
        // building a Mono chain describes what SHOULD happen; nothing actually happens
        // until something subscribes to it. This is the single most common reactive bug.
        auditOperation.subscribe();
    }
}
```

**How to run:** temporarily remove `.subscribe()` and observe that, despite no errors and no exceptions, the audit log lines never print — the scheduled method runs (confirmed via a separate log line at the very top of the method, for comparison), but the `Mono` chain describing the actual audit work is silently never executed. Restore `.subscribe()`: expect the audit log lines to now appear exactly as intended on the scheduled cadence.

What changed and why it's production-flavored: this is a deliberately constructed demonstration of the single most common "why isn't my reactive code doing anything" bug — code that reads as if it does something, compiles cleanly, and runs without error, but silently does nothing because nobody ever subscribed to the `Mono` describing the work; recognizing and avoiding this pattern is essential for anyone writing reactive code outside the request/response contexts where a framework handles subscription automatically.

## 6. Walkthrough

Tracing why subscription matters, using the scheduled audit task as the example, in execution order:

1. `@Scheduled` triggers `auditKnownFlaggedSession()` on its hourly cadence — this method call itself is synchronous and definitely executes.
2. Inside it, `sessionRepository.findById(...)` is called — but per the reactive contract, this doesn't actually perform any Redis I/O yet; it merely *describes* the lookup operation and returns a `Mono` representing that not-yet-executed description.
3. `.flatMap(...)` and `.switchIfEmpty(...)` further describe what should happen depending on the eventual outcome — still nothing has executed; this is all just building up a chain of instructions, like writing a recipe without yet cooking anything.
4. The fully composed chain is assigned to `auditOperation` — a `Mono<Void>` sitting inert, fully described but entirely unexecuted.
5. Only the final `.subscribe()` call actually triggers execution — this is the moment the "recipe" gets cooked: the real Redis lookup fires, and whichever branch (`flatMap`'s block, or `switchIfEmpty`'s fallback) actually applies runs based on the real result.
6. Without that `.subscribe()` call, the fully-built `auditOperation` `Mono` is simply discarded, unexecuted, the moment the method returns — Java's garbage collector eventually reclaims it, having never done anything at all, and no error is ever raised to indicate this happened, which is precisely what makes this class of bug so easy to miss.

```
@Scheduled fires -> auditKnownFlaggedSession() called (definitely runs)
   |
sessionRepository.findById(...) -> Mono created (DESCRIBES the lookup, does NOT execute it)
   |
.flatMap(...).switchIfEmpty(...) -> further describes conditional behavior (still not executed)
   |
auditOperation = <fully described but inert Mono>
   |
.subscribe() called? --NO--> chain silently discarded, nothing ever happens, no error
   |                  --YES--> NOW the real Redis lookup fires, chain actually executes
```

## 7. Gotchas & takeaways

> Building a `Mono` or `Flux` chain and never subscribing to it (directly via `.subscribe()`, or implicitly by returning it from a WebFlux controller method, which the framework subscribes to automatically) means the described operation silently never runs — no exception, no log, nothing. This is the single most common source of "my reactive code isn't working" confusion, and it's worth specifically checking for on every piece of standalone reactive code (scheduled tasks, event listeners, anything outside a framework-managed request cycle).

- Use `.map(...)` when transforming an already-available value into another plain value; use `.flatMap(...)` when the transformation itself produces another `Mono`/`Flux` that needs to be "flattened" into the outer chain rather than nested — using `.map(...)` where `.flatMap(...)` was needed produces a `Mono<Mono<T>>`, which usually surfaces as a confusing type error at compile time, a helpful signal rather than a silent bug in this specific case.
- `ReactiveSessionRepository<S extends Session>` mirrors `SessionRepository<S extends Session>` (card 0002) in its generic typing — code written against the interface, not a concrete implementation type, stays portable across different reactive store backends the same way the blocking equivalent does.
- Controller methods returning a `Mono` or `Flux` don't need an explicit `.subscribe()` call — WebFlux's request-handling machinery does that automatically as part of producing the HTTP response; adding an explicit `.subscribe()` inside a controller method is both unnecessary and often actively wrong, since it can trigger the operation before the framework's own subscription and management of it.
- Reactive session repository operations, like all reactive operations, are inherently asynchronous and potentially reordered relative to surrounding synchronous code — don't assume a `save(...)` call's effects are visible to code immediately following it in the same method unless that code is itself composed within the same reactive chain (via `.then(...)`, `.flatMap(...)`, and similar operators).
- When writing tests for reactive session repository code, use `reactor-test`'s `StepVerifier` rather than manually calling `.block()` to "make it synchronous for testing" — `StepVerifier` correctly exercises the reactive contract (including timing, cancellation, and backpressure behavior) in a way that `.block()`-based testing can mask real bugs that would only surface under genuine reactive execution.
