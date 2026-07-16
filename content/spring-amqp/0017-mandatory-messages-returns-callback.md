---
card: spring-amqp
gi: 17
slug: mandatory-messages-returns-callback
title: "Mandatory messages & returns callback"
---

## 1. What it is

The `mandatory` flag, set via `RabbitTemplate.setMandatory(true)` (or per-message via a `MessagePostProcessor`), tells the broker that a message failing to route to any queue should be returned to the publisher rather than silently dropped — the specific mechanism that makes the "return" half of card 0014's confirms-and-returns pair actually fire. Without `mandatory=true`, an unroutable message vanishes with no notification at all, regardless of whether a returns callback is registered.

## 2. Why & when

You set `mandatory=true` specifically whenever silently dropping an unroutable message would be an unacceptable, invisible failure:

- **A routing key or binding configuration mistake needs to be caught immediately, not discovered later** — publishing to `order.exchange` with a routing key that doesn't match any current binding (a typo, or a binding that was removed but the producer wasn't updated) is exactly the kind of mistake `mandatory=true` surfaces loudly instead of silently.
- **Business messages where "this absolutely must reach a queue" is a real requirement** — for critical events, knowing immediately that a message had nowhere to go is far more valuable than the message just disappearing without a trace, discovered only when someone later notices expected data never arrived.
- **Debugging routing configuration during development or after a topology change** — temporarily enabling `mandatory=true` with a returns callback that logs loudly is a practical way to catch routing misconfigurations early, before they cause a harder-to-diagnose production issue.

## 3. Core concept

Think of `mandatory=true` as writing "return to sender if undeliverable" on the outside of a physical envelope — without that instruction, a piece of mail that can't be delivered to its address (no matching binding) is simply discarded by the postal service with no further action and no way for the sender to ever know. With that instruction, an undeliverable piece of mail comes back to the original sender, letting them notice something went wrong and investigate why the address was invalid in the first place.

```java
rabbitTemplate.setMandatory(true);

rabbitTemplate.setReturnsCallback(returned -> {
    System.err.println("UNROUTABLE MESSAGE: exchange=" + returned.getExchange()
        + " routingKey=" + returned.getRoutingKey()
        + " replyCode=" + returned.getReplyCode()
        + " replyText=" + returned.getReplyText());
    alertingService.notifyRoutingFailure(returned);
});

rabbitTemplate.convertAndSend("order.exchange", "order.status.unknown", order); // typo'd routing key
```

If `order.status.unknown` matches no binding on `order.exchange`, the returns callback fires with the details needed to diagnose exactly what went wrong.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Without mandatory=true, an unroutable message is silently dropped with no notification; with mandatory=true and a returns callback registered, the same unroutable message triggers an explicit, actionable return event" >
  <text x="160" y="14" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">mandatory=false (default)</text>
  <rect x="20" y="30" width="280" height="35" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="160" y="52" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">unroutable message -&gt; silently dropped</text>
  <text x="160" y="85" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">no notification, no trace, ever</text>

  <text x="480" y="14" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">mandatory=true + returns callback</text>
  <rect x="340" y="30" width="280" height="35" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="52" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">unroutable message -&gt; returned to publisher</text>
  <text x="480" y="85" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">returns callback fires -&gt; explicit, actionable</text>
</svg>

The single flag flips a silent failure into an observable, actionable one.

## 5. Runnable example

The scenario: publishing order events where a routing configuration mistake causes some messages to be unroutable, simulated with a plain in-memory model standing in for the broker's mandatory-flag-aware routing decision (no real RabbitMQ broker needed to demonstrate the silent-drop-versus-explicit-return contrast), starting with the default silent-drop behavior, then adding the mandatory flag with a returns callback to surface the same failure explicitly, then adding an alerting/logging action triggered specifically by the returns callback.

### Level 1 — Basic

```java
// MandatoryMessagesDemo.java
import java.util.*;

public class MandatoryMessagesDemo {
    static Set<String> boundRoutingKeys = Set.of("order.created", "order.shipped");

    // Default behavior: unroutable messages are silently dropped, no notification at all.
    static void publishDefault(String routingKey, String payload) {
        if (boundRoutingKeys.contains(routingKey)) {
            System.out.println("Delivered to matching queue: " + payload);
        }
        // else: silently dropped -- nothing prints, nothing is logged, no trace whatsoever
    }

    public static void main(String[] args) {
        publishDefault("order.created", "{\"orderId\":\"ORD-1\"}");
        publishDefault("order.status.unknown", "{\"orderId\":\"ORD-2\"}"); // typo'd routing key
        System.out.println("(ORD-2's message vanished above with zero indication anything went wrong)");
    }
}
```

How to run: `java MandatoryMessagesDemo.java`. Expected output: only `Delivered to matching queue: {"orderId":"ORD-1"}` prints — `ORD-2`'s message is silently lost, with the final line the only hint anything was even amiss, exactly the invisible-failure problem `mandatory=true` exists to solve.

### Level 2 — Intermediate

```java
// MandatoryMessagesDemo.java
import java.util.*;
import java.util.function.*;

public class MandatoryMessagesDemo {
    static Set<String> boundRoutingKeys = Set.of("order.created", "order.shipped");

    // Real-world concern: mandatory=true plus a returns callback turns the same silent failure
    // into an explicit, observable event the moment it happens.
    static void publishMandatory(String routingKey, String payload, Consumer<String> returnsCallback) {
        if (boundRoutingKeys.contains(routingKey)) {
            System.out.println("Delivered to matching queue: " + payload);
        } else {
            returnsCallback.accept("UNROUTABLE: routingKey='" + routingKey + "' matched no binding, payload=" + payload);
        }
    }

    public static void main(String[] args) {
        Consumer<String> returnsCallback = reason -> System.err.println("RETURNED MESSAGE: " + reason);

        publishMandatory("order.created", "{\"orderId\":\"ORD-1\"}", returnsCallback);
        publishMandatory("order.status.unknown", "{\"orderId\":\"ORD-2\"}", returnsCallback);
    }
}
```

How to run: `java MandatoryMessagesDemo.java`. Expected output: `Delivered to matching queue: {"orderId":"ORD-1"}` followed by `RETURNED MESSAGE: UNROUTABLE: routingKey='order.status.unknown' matched no binding, payload={"orderId":"ORD-2"}` — the exact same routing mistake as Level 1, now surfaced explicitly and immediately instead of vanishing silently.

### Level 3 — Advanced

```java
// MandatoryMessagesDemo.java
import java.util.*;
import java.util.function.*;

public class MandatoryMessagesDemo {
    static Set<String> boundRoutingKeys = Set.of("order.created", "order.shipped");

    record ReturnedMessage(String exchange, String routingKey, String payload, String reason) {}

    // Production concern: a returns callback should drive a genuine remediation path -- logging
    // loudly, alerting an operator, AND capturing enough detail (exchange, routing key, payload)
    // to actually diagnose and fix the underlying routing/binding misconfiguration.
    static class ReturnsHandler {
        List<ReturnedMessage> returnedMessages = new ArrayList<>();

        void handle(ReturnedMessage returned) {
            returnedMessages.add(returned);
            System.err.println("ALERT: message returned as unroutable");
            System.err.println("  exchange=" + returned.exchange() + " routingKey=" + returned.routingKey());
            System.err.println("  payload=" + returned.payload());
            System.err.println("  likely cause: no binding exists for this routing key on this exchange");
        }
    }

    static void publishMandatory(String exchange, String routingKey, String payload, ReturnsHandler returnsHandler) {
        if (boundRoutingKeys.contains(routingKey)) {
            System.out.println("Delivered to matching queue: " + payload);
        } else {
            returnsHandler.handle(new ReturnedMessage(exchange, routingKey, payload, "NO_ROUTE"));
        }
    }

    public static void main(String[] args) {
        ReturnsHandler returnsHandler = new ReturnsHandler();

        publishMandatory("order.exchange", "order.created", "{\"orderId\":\"ORD-1\"}", returnsHandler);
        publishMandatory("order.exchange", "order.status.unknown", "{\"orderId\":\"ORD-2\"}", returnsHandler);
        publishMandatory("order.exchange", "order.cancelled.typo", "{\"orderId\":\"ORD-3\"}", returnsHandler);

        System.out.println("Total messages requiring investigation: " + returnsHandler.returnedMessages.size());
    }
}
```

How to run: `java MandatoryMessagesDemo.java`. Expected output: `ORD-1` delivers normally; `ORD-2` and `ORD-3` each trigger a detailed alert block identifying the exchange, routing key, and payload involved, and the final line reports `Total messages requiring investigation: 2` — giving an operator or developer everything needed to diagnose and fix the two routing misconfigurations, rather than discovering the missing data days later with no clue why.

## 6. Walkthrough

Trace a message through the mandatory-flag decision at the broker.

1. **Publish with mandatory flag set**: application code publishes a message with `mandatory=true` configured on the template (globally, or per-message via a post-processor), attaching the exchange and routing key as usual.
2. **Broker attempts routing**: the broker evaluates the message's routing key against the target exchange's bindings, exactly as it would for any other message — the mandatory flag itself doesn't change the routing logic, only what happens if routing fails.
3. **Routing succeeds**: if at least one binding matches, the message is delivered to the matching queue(s) normally, and the mandatory flag has no further effect — everything proceeds exactly as an ordinary, non-mandatory publish would.
4. **Routing fails**: if no binding matches the routing key, the broker — because `mandatory=true` was set — sends the message back to the publishing connection instead of silently discarding it, including details like a reply code and reply text explaining why.
5. **Returns callback fires**: `RabbitTemplate`'s registered returns callback (via `setReturnsCallback(...)`) receives this returned message, giving the application an explicit, actionable notification containing the original exchange, routing key, and payload.
6. **Application responds**: the returns callback can log the failure loudly, alert an operator, and (in a well-built system) capture enough detail to diagnose the underlying routing misconfiguration — turning what would otherwise be an invisible, silent data-loss event into a visible, addressable one.

```
convertAndSend(exchange, routingKey, payload) [mandatory=true]
  -> broker attempts routing against bindings
       matches a binding -> delivered normally, mandatory flag has no further effect
       no matching binding -> message returned to publisher
                                -> returns callback fires with exchange/routingKey/payload/reason
                                   -> application logs/alerts/investigates
```

## 7. Gotchas & takeaways

> **Gotcha:** setting `mandatory=true` without also registering a returns callback accomplishes nothing useful — the broker still returns the message, but with no callback registered to receive it, the returned message is effectively discarded on the client side anyway, just with slightly different internal handling; the flag and the callback must be configured together to actually get the intended visibility.

- `mandatory=true` alone doesn't prevent message loss for an unroutable message — it converts a silent, invisible loss into a visible, notified one; the application still needs a returns callback (and a defined response to it) to actually act on that visibility.
- Reserve `mandatory=true` for publish paths where routing failures genuinely need immediate, explicit surfacing — enabling it blanket-wide for every message adds overhead and callback-handling complexity that isn't always warranted for lower-stakes, best-effort messages.
- A returns callback firing frequently in production is a strong signal of a routing or binding configuration problem that needs fixing — treat it as an operational alert worth investigating promptly, not a routine event to just log and ignore.
- Combined with publisher confirms (card 0014), mandatory messages and returns give a publisher two independent, complementary signals: confirms verify the broker accepted the message at all, and returns verify it could actually be routed somewhere useful once accepted.
