---
card: spring-integration
gi: 30
slug: claim-check-in-out
title: "Claim check (in/out)"
---

## 1. What it is

Claim check is a pattern implemented by a pair of endpoints — a claim-check-in transformer, which stores a message's (often large) payload somewhere external and replaces it with a small reference/ID, and a claim-check-out transformer, which later retrieves the original payload using that reference. It's named after a coat-check ticket: you hand over your coat (the large payload), receive a small numbered ticket (the claim check ID) that's easy to carry around, and later exchange that ticket for the original coat.

## 2. Why & when

You reach for claim check specifically when a large payload is inconvenient to carry through every step of a flow, but is still needed eventually:

- **A message's actual payload is large** (a full document, an image, a big JSON blob) **but intermediate flow steps only need to route, filter, or inspect metadata**, not the full content — carrying the entire large payload through every channel, interceptor, and endpoint wastes memory and bandwidth on data most steps don't touch.
- **A flow's messages need to travel across a slower or size-limited transport** (some messaging middleware has payload size limits) **for part of their journey** — checking the payload in before that leg and retrieving it after keeps the message itself small for the constrained portion.
- **Multiple recipients need to reference the same large payload without each holding their own full copy** — a claim check reference can be handed to several downstream consumers, each retrieving the shared stored payload only if and when they actually need it, rather than everyone carrying a redundant copy.

## 3. Core concept

Think of claim check exactly like an actual coat check at a theater. On arrival, you hand your coat to an attendant (claim-check-in), who stores it and gives you a small numbered ticket — from that point on, you carry only the lightweight ticket through the rest of the evening, not the bulky coat. When you're ready to leave, you present the ticket to the attendant (claim-check-out), who retrieves your exact original coat using the number. The theater's aisles and seating (the messaging system's channels) never had to accommodate a room full of coats — only tickets.

```java
// Claim-check-in: store the large payload, replace the message with a small reference
@Transformer(inputChannel = "documents", outputChannel = "documentReferences")
public String checkIn(byte[] largeDocument) {
    String claimCheckId = UUID.randomUUID().toString();
    payloadStore.put(claimCheckId, largeDocument); // external store: could be Redis, a DB, a file system
    return claimCheckId; // the message now carries only this small String
}

// Claim-check-out: retrieve the original large payload using the reference
@Transformer(inputChannel = "documentReferences", outputChannel = "processedDocuments")
public byte[] checkOut(String claimCheckId) {
    return payloadStore.get(claimCheckId); // the ORIGINAL large payload, retrieved back
}
```

Between check-in and check-out, only the small `claimCheckId` string travels through the flow's channels — the large `byte[]` sits safely in external storage the entire time.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Claim-check-in stores a large payload and replaces it with a small ID; the ID travels through the flow; claim-check-out retrieves the original payload using that ID">
  <rect x="20" y="60" width="100" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="70" y="87" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">large payload</text>

  <line x1="120" y1="82" x2="170" y2="82" stroke="#6db33f" stroke-width="2" marker-end="url(#cc1)"/>

  <rect x="180" y="60" width="110" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="235" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">claim-check-in</text>
  <text x="235" y="97" fill="#8b949e" font-size="6" text-anchor="middle" font-family="sans-serif">store, return ID</text>

  <line x1="290" y1="82" x2="340" y2="82" stroke="#79c0ff" stroke-width="2" marker-end="url(#cc2)"/>

  <rect x="350" y="65" width="90" height="35" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="395" y="87" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">small ID</text>

  <line x1="440" y1="82" x2="480" y2="82" stroke="#79c0ff" stroke-width="2" marker-end="url(#cc2)"/>

  <rect x="490" y="60" width="110" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="545" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">claim-check-out</text>
  <text x="545" y="97" fill="#8b949e" font-size="6" text-anchor="middle" font-family="sans-serif">retrieve by ID</text>

  <line x1="235" y1="105" x2="545" y2="105" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,2"/>
  <text x="390" y="120" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">external store holds the actual payload the whole time</text>

  <defs>
    <marker id="cc1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="cc2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Only the small ID travels through intermediate channels; the large payload sits in external storage, retrieved only where it's actually needed.

## 5. Runnable example

The scenario: a document-processing pipeline where an approval step only needs metadata, not the full document, starting with basic check-in/check-out, then intermediate routing on the small reference alone, and finally cleanup of the external store after the payload is no longer needed.

### Level 1 — Basic

```java
// BasicClaimCheckDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.util.*;

public class BasicClaimCheckDemo {
    static final Map<String, byte[]> STORE = new HashMap<>(); // stand-in for Redis/DB/file storage

    public static void main(String[] args) {
        DirectChannel documents = new DirectChannel();
        DirectChannel references = new DirectChannel();
        DirectChannel processed = new DirectChannel();

        processed.subscribe(m -> System.out.println("Processed original payload, size=" + ((byte[]) m.getPayload()).length + " bytes"));

        // claim-check-out
        references.subscribe(m -> {
            String claimCheckId = (String) m.getPayload();
            byte[] original = STORE.get(claimCheckId);
            processed.send(MessageBuilder.withPayload(original).build());
        });

        // claim-check-in
        documents.subscribe(m -> {
            byte[] largeDocument = (byte[]) m.getPayload();
            String claimCheckId = UUID.randomUUID().toString();
            STORE.put(claimCheckId, largeDocument);
            System.out.println("Checked in, ID=" + claimCheckId + " (channel now carries " + claimCheckId.length() + " chars, not " + largeDocument.length + " bytes)");
            references.send(MessageBuilder.withPayload(claimCheckId).build());
        });

        byte[] fakeLargeDocument = new byte[10_000]; // simulate a large payload
        documents.send(MessageBuilder.withPayload(fakeLargeDocument).build());
    }
}
```

How to run: `java BasicClaimCheckDemo.java`. Expected output: `Checked in, ID=... (channel now carries 36 chars, not 10000 bytes)` followed by `Processed original payload, size=10000 bytes` — the intermediate `references` channel only ever carried a 36-character UUID string, while the full 10,000-byte payload was safely retrieved intact at the end.

### Level 2 — Intermediate

An intermediate approval step operates purely on the small claim-check reference (plus header metadata attached at check-in time), never touching or needing the large payload at all — exactly the scenario claim check is designed for.

```java
// MetadataOnlyRoutingDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.util.*;

public class MetadataOnlyRoutingDemo {
    static final Map<String, byte[]> STORE = new HashMap<>();

    public static void main(String[] args) {
        DirectChannel documents = new DirectChannel();
        DirectChannel forApproval = new DirectChannel();
        DirectChannel processed = new DirectChannel();

        processed.subscribe(m -> System.out.println("Final processing, retrieved size=" + ((byte[]) m.getPayload()).length));

        // approval step: works ONLY with metadata (filename, size header) and the small ID — never the payload
        forApproval.subscribe(m -> {
            String claimCheckId = (String) m.getPayload();
            String filename = (String) m.getHeaders().get("filename");
            int sizeHint = (Integer) m.getHeaders().get("sizeHint");
            System.out.println("Approval step reviewing '" + filename + "' (" + sizeHint + " bytes) via ID=" + claimCheckId + " — no payload loaded");
            boolean approved = sizeHint < 50_000; // decision made purely from metadata
            if (approved) {
                byte[] original = STORE.get(claimCheckId); // ONLY retrieved here, once actually needed
                processed.send(MessageBuilder.withPayload(original).build());
            } else {
                System.out.println("REJECTED by approval step, too large — payload never even retrieved");
            }
        });

        documents.subscribe(m -> {
            byte[] largeDocument = (byte[]) m.getPayload();
            String claimCheckId = UUID.randomUUID().toString();
            STORE.put(claimCheckId, largeDocument);
            forApproval.send(MessageBuilder.withPayload(claimCheckId)
                .setHeader("filename", "report.pdf")
                .setHeader("sizeHint", largeDocument.length)
                .build());
        });

        documents.send(MessageBuilder.withPayload(new byte[10_000]).build()); // small enough, approved
    }
}
```

How to run: `java MetadataOnlyRoutingDemo.java`. Expected output: `Approval step reviewing 'report.pdf' (10000 bytes) via ID=... — no payload loaded` then `Final processing, retrieved size=10000` — the approval decision was made entirely from header metadata and the small ID; the actual large payload was only pulled from the store after approval passed.

### Level 3 — Advanced

A production claim-check flow needs cleanup: once the payload has been retrieved for its final use, the external store entry should typically be removed to avoid an ever-growing store of payloads nobody will ever check out again — shown here with explicit removal after retrieval.

```java
// CleanupClaimCheckDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.util.*;

public class CleanupClaimCheckDemo {
    static final Map<String, byte[]> STORE = new HashMap<>();

    public static void main(String[] args) {
        DirectChannel documents = new DirectChannel();
        DirectChannel references = new DirectChannel();
        DirectChannel processed = new DirectChannel();

        processed.subscribe(m -> System.out.println("Processed, store size now=" + STORE.size()));

        // claim-check-out WITH cleanup: remove from the store once retrieved
        references.subscribe(m -> {
            String claimCheckId = (String) m.getPayload();
            byte[] original = STORE.remove(claimCheckId); // remove, not just get — frees the store
            System.out.println("Checked out and REMOVED from store, ID=" + claimCheckId);
            processed.send(MessageBuilder.withPayload(original).build());
        });

        documents.subscribe(m -> {
            byte[] doc = (byte[]) m.getPayload();
            String id = UUID.randomUUID().toString();
            STORE.put(id, doc);
            System.out.println("Store size after check-in: " + STORE.size());
            references.send(MessageBuilder.withPayload(id).build());
        });

        documents.send(MessageBuilder.withPayload(new byte[5_000]).build());
        documents.send(MessageBuilder.withPayload(new byte[3_000]).build());
    }
}
```

How to run: `java CleanupClaimCheckDemo.java`. Expected output shows the store size growing to `1` then processing/removal bringing it back to `0`, then growing to `1` again for the second document and back to `0` after its own processing — the store never accumulates entries for payloads that have already completed their round trip, avoiding an unbounded memory leak.

## 6. Walkthrough

Tracing `CleanupClaimCheckDemo` for one document in execution order:

1. `documents.send(new byte[5000])` triggers the claim-check-in subscriber, which generates a UUID, stores the 5,000-byte array in `STORE` under that UUID, and prints the store's size (now `1`).
2. The claim-check-in subscriber sends a new message carrying only the UUID string (not the large array) to `references`.
3. The claim-check-out subscriber on `references` receives that small message, extracts the UUID, and calls `STORE.remove(claimCheckId)` — this both retrieves the original 5,000-byte array *and* deletes it from the store in one operation.
4. The retrieved original payload is wrapped into a new message and sent to `processed`.
5. `processed`'s subscriber receives the full original payload and prints the store's current size — now back to `0`, since the entry was removed in step 3.
6. The exact same sequence repeats independently for the second document (3,000 bytes): the store briefly holds one entry, then returns to empty once that document's own check-out completes — at no point does the store accumulate entries for documents whose round trip has already finished.

```
documents.send(doc1, 5000 bytes)
  -> check-in: STORE={id1: doc1}  (size=1)
  -> references.send(id1)
  -> check-out: STORE.remove(id1) -> doc1 retrieved, STORE={} (size=0)
  -> processed.send(doc1)
```

## 7. Gotchas & takeaways

> If claim-check-out never happens for some messages (a flow branch that drops a message via a `Filter`, card 0022, before it reaches check-out, or a crashed consumer), the corresponding entry in the external store is never cleaned up — this is a real memory/storage leak risk distinct from the flow's own message handling. Pair claim check with either explicit cleanup on every path (including failure paths) or a TTL/expiry policy on the external store itself, so orphaned entries eventually age out even if a check-out is missed.

- Claim check replaces a large payload with a small reference (an ID) for the portion of a flow that doesn't need the full content, storing the actual payload externally and retrieving it later via claim-check-out.
- Use it when intermediate steps only need metadata or a lightweight handle, not the full payload — keeping channels, interceptors, and routing logic fast and memory-light for the parts of the journey that don't need the bulk data.
- Routing and approval decisions can be made entirely from headers and the small reference, deferring the actual (potentially expensive) payload retrieval until it's genuinely needed.
- Always clean up the external store once a payload's claim check is no longer needed, or configure a TTL/expiry — orphaned entries from messages that never reach check-out are a real leak risk.
- Claim check trades a small amount of added complexity (an external store, ID generation, retrieval logic) for significantly reduced payload weight moving through the messaging system itself — worth it specifically when payloads are large and not every step needs them.
