---
card: spring-integration
gi: 89
slug: message-history-wire-tap
title: "Message history & wire tap"
---

## 1. What it is

Message history (`@EnableMessageHistory`, `MessageHistory` header) automatically records the sequence of channels and components a message has passed through, embedding that trace directly in the message's own headers as it travels. Wire tap (`WireTap`, a `ChannelInterceptor` that copies a message to a secondary channel without altering its path through the main flow) lets an observer inspect messages flowing through a channel non-invasively, without changing the message or the flow's actual routing. Together, they're the primary built-in tools for understanding what actually happened to a message after the fact.

## 2. Why & when

You reach for message history and wire taps specifically for observability — understanding a flow's actual behavior — rather than for changing that behavior:

- **Debugging a message that ended up somewhere unexpected** — message history shows the exact sequence of channels and endpoints a specific message traversed, turning "why did this end up here?" from a guessing exercise into reading a recorded trail.
- **Auditing or logging every message through a channel without touching the main flow** — a wire tap on a sensitive channel (say, payment requests) can copy every message to a logging or audit channel, leaving the original processing path completely undisturbed.
- **Live monitoring or debugging in a running system without redeploying** — a wire tap can be added or removed to inspect traffic on a channel temporarily, which is far less invasive than modifying and redeploying the flow itself just to add a println-style trace.

## 3. Core concept

Think of message history as a passport getting a stamp at every border crossing — by the time the traveler (the message) reaches its final destination, anyone can look at the passport and see exactly which countries (channels and components) it passed through, in order, without needing to have watched the journey happen live. A wire tap is more like a security camera pointed at one specific checkpoint — it doesn't affect the traveler's actual route at all, it just gives an observer a copy of what passed through that one point, for review, without the traveler ever knowing the camera was there.

```java
@Configuration
@EnableMessageHistory
public class HistoryConfig {}

@Bean
public IntegrationFlow auditedPaymentFlow() {
    return IntegrationFlow.from("paymentRequests")
        .wireTap("auditLogChannel") // copies every message here, untouched, for auditing
        .handle(paymentGateway::charge)
        .get();
}

@Bean
public IntegrationFlow auditLogFlow() {
    return IntegrationFlow.from("auditLogChannel")
        .handle((Message<?> msg, headers) -> auditLogger.record(msg))
        .get();
}
```

Every message on `paymentRequests` continues to `paymentGateway::charge` exactly as before; a copy also silently flows to `auditLogChannel` for logging, with the message's full channel history available in its headers if `@EnableMessageHistory` is active.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A wire tap copies a message to a secondary observation channel while the original continues unchanged along its main path; message history records every channel a message passed through as a header" >
  <rect x="20" y="20" width="180" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">paymentRequests</text>

  <line x1="200" y1="42" x2="290" y2="42" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a6)"/>
  <rect x="290" y="20" width="180" height="45" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="380" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">paymentGateway.charge()</text>

  <line x1="110" y1="65" x2="110" y2="100" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#a6)"/>
  <text x="150" y="90" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">wire tap copy</text>
  <rect x="20" y="100" width="180" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="127" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">auditLogChannel</text>

  <text x="450" y="90" fill="#8b949e" font-size="7" font-family="monospace">MessageHistory header:</text>
  <text x="450" y="105" fill="#8b949e" font-size="7" font-family="monospace">[paymentRequests, chargeHandler]</text>

  <defs><marker id="a6" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker></defs>
</svg>

The main path is undisturbed by the tap; the history header accumulates as the message travels regardless.

## 5. Runnable example

The scenario: auditing payment messages without altering the main processing path, then using the accumulated channel history to debug an unexpected routing outcome, simulated with a plain in-memory message wrapper standing in for `Message<?>` and its `MessageHistory` header (no real Spring Integration context needed to demonstrate the tap-and-trace pattern), starting with a basic wire tap copying to a second destination, then adding history tracking across multiple channels, then using that history to diagnose a message that ended up somewhere unexpected.

### Level 1 — Basic

```java
// WireTapDemo.java
import java.util.*;
import java.util.function.*;

public class WireTapDemo {
    record Msg(String payload) {}

    // Stand-in for a WireTap ChannelInterceptor: forwards a copy without altering the main path.
    static void sendWithTap(Msg msg, Consumer<Msg> mainHandler, Consumer<Msg> tapHandler) {
        tapHandler.accept(msg); // observation copy, doesn't affect what follows
        mainHandler.accept(msg); // main path continues exactly as it would without the tap
    }

    public static void main(String[] args) {
        Msg payment = new Msg("charge:$50.00");
        sendWithTap(payment,
            m -> System.out.println("Main path processed: " + m.payload()),
            m -> System.out.println("Audit log recorded: " + m.payload()));
    }
}
```

How to run: `java WireTapDemo.java`. Expected output: `Audit log recorded: charge:$50.00` then `Main path processed: charge:$50.00` — both the audit copy and the main processing happen, with the main path's behavior unaffected by the tap's presence.

### Level 2 — Intermediate

```java
// WireTapDemo.java
import java.util.*;

public class WireTapDemo {
    // Real-world concern: message history should accumulate as the message crosses each
    // channel/component, so the full path is reconstructable later without having observed
    // the journey live.
    static class Msg {
        final String payload;
        final List<String> history = new ArrayList<>();
        Msg(String payload) { this.payload = payload; }
        Msg passedThrough(String componentName) {
            history.add(componentName);
            return this;
        }
    }

    public static void main(String[] args) {
        Msg payment = new Msg("charge:$50.00");
        payment = payment.passedThrough("paymentRequests");
        payment = payment.passedThrough("validationFilter");
        payment = payment.passedThrough("chargeHandler");

        System.out.println("Final payload: " + payment.payload);
        System.out.println("Message history: " + payment.history);
    }
}
```

How to run: `java WireTapDemo.java`. Expected output: `Final payload: charge:$50.00` then `Message history: [paymentRequests, validationFilter, chargeHandler]` — the accumulated trail showing exactly which channels and components the message passed through, in order, available entirely from the message itself.

### Level 3 — Advanced

```java
// WireTapDemo.java
import java.util.*;

public class WireTapDemo {
    static class Msg {
        final String payload;
        final List<String> history = new ArrayList<>();
        Msg(String payload) { this.payload = payload; }
        Msg passedThrough(String componentName) { history.add(componentName); return this; }
    }

    // Production concern: use the recorded history to DIAGNOSE why a specific message ended up
    // somewhere unexpected -- e.g. a payment that should have gone through fraud review but
    // didn't, reconstructable purely from the trail left in its own headers.
    static void diagnoseUnexpectedRouting(Msg msg, String expectedComponent) {
        if (!msg.history.contains(expectedComponent)) {
            System.out.println("ANOMALY: message never passed through '" + expectedComponent + "'");
            System.out.println("Actual path taken: " + msg.history);
            int lastRouterIndex = msg.history.indexOf("priorityRouter");
            if (lastRouterIndex >= 0 && lastRouterIndex + 1 < msg.history.size()) {
                System.out.println("Diverged at 'priorityRouter', went to: " + msg.history.get(lastRouterIndex + 1));
            }
        } else {
            System.out.println("Path confirmed correct: " + msg.history);
        }
    }

    public static void main(String[] args) {
        Msg suspiciousPayment = new Msg("charge:$5000.00");
        suspiciousPayment = suspiciousPayment.passedThrough("paymentRequests");
        suspiciousPayment = suspiciousPayment.passedThrough("priorityRouter");
        suspiciousPayment = suspiciousPayment.passedThrough("fastTrackHandler"); // should've been fraudReviewHandler!
        suspiciousPayment = suspiciousPayment.passedThrough("chargeHandler");

        diagnoseUnexpectedRouting(suspiciousPayment, "fraudReviewHandler");
    }
}
```

How to run: `java WireTapDemo.java`. Expected output: `ANOMALY: message never passed through 'fraudReviewHandler'`, followed by the full actual path and `Diverged at 'priorityRouter', went to: fastTrackHandler` — pinpointing exactly where the message's routing went wrong (a large payment incorrectly sent to the fast-track path instead of fraud review) purely by reading its recorded history, without needing to have observed the message live as it happened.

## 6. Walkthrough

Trace a message being tapped for audit while its history accumulates, then used to diagnose a routing anomaly.

1. **Message enters the flow**: a payment request arrives on `paymentRequests`, and (if `@EnableMessageHistory` is active) its `MessageHistory` header begins recording this first channel.
2. **Wire tap fires**: before the message continues to its next handler, the configured wire tap sends an unaltered copy to `auditLogChannel` — this happens transparently, and the original message's journey through the main flow is completely unaffected by the tap's existence.
3. **Main path continues**: the original message proceeds to whatever handler or router comes next (a validation filter, a priority router), with each hop appending itself to the accumulating history header.
4. **Routing decision recorded**: if the flow includes a router (a priority router, in the example), the history captures not just that the message passed through the router, but — by recording the very next component — implicitly which branch it took, since that's simply the next entry in the recorded sequence.
5. **Later investigation**: if a message later turns up somewhere unexpected (a large payment that should have gone to fraud review instead reaching a fast-track handler), an investigator reads the message's own `MessageHistory` header to see its exact path, pinpointing precisely where it diverged from the expected route — no need to have been watching the flow live when the anomaly occurred.
6. **Audit trail independently available**: separately, the wire-tapped copy sitting in `auditLogChannel` provides its own independent record of every message that passed through the tapped point, useful for compliance or bulk analysis even when no specific anomaly is being investigated.

```
message enters paymentRequests -> history: [paymentRequests]
  -> wire tap copies message (untouched) to auditLogChannel
  -> continues to validationFilter -> history: [..., validationFilter]
    -> priorityRouter -> history: [..., priorityRouter]
      -> (should route to fraudReviewHandler, but actually goes to) fastTrackHandler
        -> history: [..., fastTrackHandler]  <- anomaly visible here on inspection
```

## 7. Gotchas & takeaways

> **Gotcha:** message history and wire taps are observability tools, not control-flow tools — a wire tap's secondary channel receives a copy of the message but has no way to affect or halt the original message's progress through the main flow; using a wire tap where the intent is actually to intercept or block a message is the wrong tool, since blocking requires an actual filter or router in the main path instead.

- Enable message history selectively for flows where post-hoc debugging genuinely matters — the header overhead is generally modest, but it does add to every message's payload size and there's little reason to enable it universally for extremely high-volume flows where it isn't needed.
- Wire taps are a clean way to add logging, auditing, or monitoring to a channel without modifying the channel's existing handlers — prefer this over inserting logging code directly into a handler that otherwise has no reason to know about logging concerns.
- A wire tap's target channel should itself be handled asynchronously (or otherwise decoupled) where possible, so that a slow or failing audit/logging consumer doesn't inadvertently add latency to the tapped message's main-path processing — check how the tap is configured with respect to synchronous versus asynchronous dispatch.
- Message history is most valuable specifically for diagnosing "how did this message end up here" questions after the fact; for live, real-time visibility into what's happening in a flow right now, combine it with the JMX support (card 0067) or dedicated observability tooling rather than relying on history inspection alone.
