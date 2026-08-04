---
card: system-design
gi: 26
slug: webhooks-server-push-callbacks
title: "Webhooks (server-push callbacks)"
---

## 1. What it is

A **webhook** is a way for one server (Server A) to notify a different server (Server B) the instant an event happens, by having Server A send an HTTP request — usually `POST` — directly to a URL Server B registered in advance, called a **callback URL**. Instead of Server B repeatedly asking "did anything happen yet?", Server A pushes the notification the moment it occurs.

## 2. Why & when

Webhooks solve the same "how does one system learn about an event on another system" problem that polling solves, but between two *servers* (not a browser client and a server, which is what WebSocket/SSE/polling usually connect). A payment processor notifying your server that a payment succeeded, or a CI system notifying your server that a build finished, are classic webhook use cases. You choose webhooks over polling between two backend systems because polling a third-party API repeatedly wastes both sides' resources and adds latency; webhooks let the event source push the notification instantly, once.

## 3. Core concept

**The registration and delivery flow:**

1. Server B (the receiver) registers a callback URL with Server A ("when a payment completes, `POST` to `https://myapp.com/webhooks/payment`").
2. When the event happens, Server A sends an HTTP `POST` request to that URL, with the event data in the body.
3. Server B's endpoint receives the request, processes the event, and responds with a `2xx` status code to acknowledge receipt.

**Key design concerns that come up in an interview:**

- **Retries on failure.** If Server B's endpoint is down or returns an error, Server A should retry the delivery, usually with **exponential backoff** (waiting progressively longer between each retry), since a single failed attempt should not mean the notification is lost forever.
- **Idempotency on the receiving end.** Because of retries, Server B might receive the *same* webhook event more than once. The receiving endpoint should be able to safely process the same event twice without a bad effect — typically by tracking a unique event ID and ignoring duplicates it has already processed.
- **Verifying authenticity.** Since a webhook endpoint is a public URL that accepts incoming requests, anyone could send a fake request to it. Real systems verify the request actually came from the trusted sender, commonly by checking a cryptographic **signature** included in a request header, computed from a shared secret both sides know.
- **Fast acknowledgment.** The receiving endpoint should do minimal work (like just queuing the event for later processing) before returning a `2xx` response quickly, rather than doing slow work inline, since a slow response can cause the sender to time out and retry unnecessarily.

## 4. Diagram

```
 Server B (receiver)                        Server A (event source)
   |--register callback URL--------------->|
   |                                         |
   |                    (later, event happens on Server A)
   |<--POST /webhooks/payment {event data}--|
   |--200 OK (ack, fast)-------------------->|
   |
   | (if B was down or returned an error, A retries with backoff)
```
*Caption: the receiver registers a URL once; the sender pushes each event to it as it happens, retrying on failure.*

## 5. Runnable example

### Artifact: a Java simulation of webhook delivery with retry-with-backoff and idempotent event handling

```java
import java.util.*;

public class WebhookSim {

    static final Set<String> processedEventIds = new HashSet<>();

    // Simulates the receiving endpoint; returns true if it "accepted" the request.
    static boolean deliverWebhook(String eventId, boolean receiverIsUp) {
        if (!receiverIsUp) return false; // receiver down, delivery fails this attempt

        if (processedEventIds.contains(eventId)) {
            System.out.println("  Receiver: duplicate event " + eventId + ", already processed, ack anyway");
            return true; // idempotent: safely re-acknowledge without reprocessing
        }
        processedEventIds.add(eventId);
        System.out.println("  Receiver: processed NEW event " + eventId);
        return true;
    }

    static void sendWithRetry(String eventId, boolean[] receiverUpOnAttempt) {
        int maxAttempts = receiverUpOnAttempt.length;
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            System.out.println("Attempt " + attempt + " to deliver event " + eventId + ":");
            boolean delivered = deliverWebhook(eventId, receiverUpOnAttempt[attempt - 1]);
            if (delivered) {
                System.out.println("  Delivered and acknowledged.");
                return;
            }
            int backoffSeconds = (int) Math.pow(2, attempt); // exponential backoff: 2s, 4s, 8s...
            System.out.println("  Failed, retrying in " + backoffSeconds + "s");
        }
        System.out.println("  Giving up after " + maxAttempts + " attempts.");
    }

    public static void main(String[] args) {
        // Receiver is down on the first attempt, up on the second (a retry succeeds).
        sendWithRetry("evt_123", new boolean[]{ false, true });

        // Simulate the sender accidentally re-delivering the SAME event again later.
        System.out.println("Sender re-delivers evt_123 again (e.g. due to its own retry confusion):");
        deliverWebhook("evt_123", true);
    }
}
```

**How to run:** save as `WebhookSim.java`, run `java WebhookSim.java` (JDK 17+).

## 6. Walkthrough

1. `processedEventIds` tracks every event ID the receiver has already handled, which is what makes duplicate delivery safe — this is the idempotency mechanism described above.
2. `deliverWebhook` simulates one delivery attempt: if the receiver is "down", it fails; if the event ID was already processed, it acknowledges without reprocessing; otherwise it processes the event as new.
3. `sendWithRetry` loops through a sequence of attempts, each with a simulated up/down state for the receiver, doubling the backoff delay after every failure (`2^attempt` seconds), matching real exponential-backoff retry logic.
4. `main` first sends `evt_123` where the receiver is down on attempt 1 and up on attempt 2, showing a successful retry. It then manually re-delivers the exact same event ID again, showing the idempotent duplicate-handling path.
5. Output:
```
Attempt 1 to deliver event evt_123:
  Failed, retrying in 2s
Attempt 2 to deliver event evt_123:
  Receiver: processed NEW event evt_123
  Delivered and acknowledged.
Sender re-delivers evt_123 again (e.g. due to its own retry confusion):
  Receiver: duplicate event evt_123, already processed, ack anyway
```
6. The final line proves the design goal: receiving the same event twice never causes double-processing — it is simply acknowledged the second time, exactly the safety property a webhook receiver needs given that retries can cause duplicate deliveries.

## 7. Gotchas & takeaways

> **Gotcha:** building a webhook receiver that is not idempotent. Because the sender may legitimately retry a delivery (it cannot always know for certain whether its previous attempt succeeded), a non-idempotent receiver can end up double-charging a payment or double-sending a notification from a single real event.

- Webhooks push events from one server to another instantly, avoiding the waste of one server polling another repeatedly.
- Always design the receiving endpoint to be idempotent, tracking event IDs to safely ignore duplicates.
- Verify the sender's signature on incoming webhook requests; a public callback URL is otherwise open to forged requests.
