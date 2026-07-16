---
card: spring-integration
gi: 79
slug: codec-kryo
title: "Codec (Kryo)"
---

## 1. What it is

Codec support (`CodecMessageConverter`, backed by the `Codec` interface with a `PojoCodec`/`KryoCodec` implementation using the Kryo library) provides a fast, compact binary serialization mechanism for message payloads, as an alternative to Java's built-in serialization or a text format like JSON. It's most commonly used where messages cross a network boundary — over TCP (card 0053) between Spring Integration nodes, for instance — and both ends are Java processes that can share the same codec.

## 2. Why & when

You reach for a Kryo-based codec when serialization speed and payload size matter more than human readability or cross-language interoperability:

- **Two Java processes exchange a high volume of messages over TCP or another raw transport** — the TCP/UDP adapter (card 0053) needs some way to turn an object into bytes and back; Kryo's binary encoding is typically both faster to produce and smaller in size than Java's built-in serialization or a JSON-based transformer (card 0078) for the same object graph.
- **Standard Java serialization's overhead or fragility is a problem** — Java's default serialization embeds a lot of class metadata per object and is notoriously brittle across class version changes; Kryo, configured with registered classes, produces denser output and can be tuned for the specific object graphs a flow uses.
- **Do not reach for Kryo when a non-Java consumer needs to read the message** — like RMI (card 0068), a Kryo-based codec is a Java-to-Java optimization; a message destined for a non-Java consumer needs a portable format like JSON, XML, or Avro (card 0078) instead.

## 3. Core concept

Think of Java's built-in serialization as shipping furniture by including a full, verbose assembly manual with every single shipment, even when the receiving warehouse already has a copy on file. Kryo is like pre-registering the assembly manual once with the receiving warehouse, so every subsequent shipment just needs a short reference number (a registered class ID) plus the actual parts — smaller, faster to pack and unpack, but only works because both warehouses agreed on the same manual numbering scheme ahead of time.

```java
@Bean
public Codec kryoCodec() {
    PojoCodec codec = new PojoCodec();
    return codec; // registers common types automatically; explicit registration improves density further
}

@Bean
public IntegrationFlow tcpOutboundFlow(AbstractClientConnectionFactory connectionFactory, Codec kryoCodec) {
    return IntegrationFlow.from("outboundOrders")
        .transform(Transformers.objectToBuffer()) // conceptually similar surface; real setups wire the codec into the connection factory's serializer
        .handle(Tcp.outboundAdapter(connectionFactory))
        .get();
}
```

Once both sides of a TCP connection share the same codec configuration, every message is serialized to a compact binary form instead of a bulkier, self-describing one.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Java serialization ships full class metadata with every object; Kryo pre-registers class information once and ships only a compact reference plus field data thereafter" >
  <rect x="20" y="20" width="280" height="110" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="160" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Java serialization</text>
  <text x="35" y="45" fill="#e6edf3" font-size="7" font-family="monospace">[full class descriptor]</text>
  <text x="35" y="65" fill="#e6edf3" font-size="7" font-family="monospace">[field names + types]</text>
  <text x="35" y="85" fill="#e6edf3" font-size="7" font-family="monospace">[field values]</text>
  <text x="35" y="110" fill="#8b949e" font-size="7" font-family="sans-serif">repeated on every message</text>

  <rect x="340" y="20" width="280" height="110" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Kryo codec</text>
  <text x="355" y="45" fill="#79c0ff" font-size="7" font-family="monospace">registered once: class ID 7 = Order</text>
  <text x="355" y="70" fill="#e6edf3" font-size="7" font-family="monospace">wire: [7][field values]</text>
  <text x="355" y="110" fill="#8b949e" font-size="7" font-family="sans-serif">smaller, faster, per message</text>
</svg>

Pre-registering class identity once trades a small setup cost for a much smaller, faster per-message payload thereafter.

## 5. Runnable example

The scenario: sending order objects between two Java processes over a socket-like connection, simulated with a plain in-memory byte-array encoding standing in for Kryo's binary format (no real Kryo dependency needed to demonstrate the registration and encoding-density concept), starting with a naive verbose encoding, then adding class registration to shrink the payload, then measuring the size difference across many messages to show why it matters at volume.

### Level 1 — Basic

```java
// KryoStyleCodecDemo.java
import java.util.*;

public class KryoStyleCodecDemo {
    record Order(String id, double amount) {}

    // Stand-in for Java's built-in serialization: every message repeats the full "schema".
    static String verboseEncode(Order order) {
        return "{\"__class\":\"com.example.Order\",\"fields\":[\"id\",\"amount\"],\"id\":\""
            + order.id() + "\",\"amount\":" + order.amount() + "}";
    }

    public static void main(String[] args) {
        Order order = new Order("ORD-1", 42.50);
        String encoded = verboseEncode(order);
        System.out.println("Verbose encoding (" + encoded.length() + " bytes): " + encoded);
    }
}
```

How to run: `java KryoStyleCodecDemo.java`. Expected output: a fairly long encoded string with class name and field names repeated inline — the overhead a schema-carrying format pays on every single message.

### Level 2 — Intermediate

```java
// KryoStyleCodecDemo.java
import java.util.*;

public class KryoStyleCodecDemo {
    record Order(String id, double amount) {}

    // Real-world concern: repeating full class/field metadata on every message wastes bytes and
    // CPU. Kryo instead registers a class once, assigning it a small numeric ID both sides share.
    static class ClassRegistry {
        private final Map<Class<?>, Integer> idsByClass = new HashMap<>();
        private final Map<Integer, Class<?>> classesById = new HashMap<>();
        void register(Class<?> clazz, int id) { idsByClass.put(clazz, id); classesById.put(id, clazz); }
        int idFor(Class<?> clazz) { return idsByClass.get(clazz); }
    }

    static String compactEncode(Order order, ClassRegistry registry) {
        int classId = registry.idFor(Order.class);
        return classId + "|" + order.id() + "|" + order.amount();
    }

    public static void main(String[] args) {
        ClassRegistry registry = new ClassRegistry();
        registry.register(Order.class, 7); // agreed once, out of band, by both ends of the connection

        Order order = new Order("ORD-1", 42.50);
        String encoded = compactEncode(order, registry);
        System.out.println("Compact encoding (" + encoded.length() + " bytes): " + encoded);
    }
}
```

How to run: `java KryoStyleCodecDemo.java`. Expected output: `Compact encoding (12 bytes): 7|ORD-1|42.5` — noticeably shorter than the verbose form, since only a numeric class ID and the field values themselves are sent, the actual field names and class name having already been agreed upon in the registry.

### Level 3 — Advanced

```java
// KryoStyleCodecDemo.java
import java.util.*;

public class KryoStyleCodecDemo {
    record Order(String id, double amount) {}

    static class ClassRegistry {
        private final Map<Class<?>, Integer> idsByClass = new HashMap<>();
        void register(Class<?> clazz, int id) { idsByClass.put(clazz, id); }
        int idFor(Class<?> clazz) { return idsByClass.get(clazz); }
    }

    static String verboseEncode(Order order) {
        return "{\"__class\":\"com.example.Order\",\"fields\":[\"id\",\"amount\"],\"id\":\""
            + order.id() + "\",\"amount\":" + order.amount() + "}";
    }

    static String compactEncode(Order order, ClassRegistry registry) {
        return registry.idFor(Order.class) + "|" + order.id() + "|" + order.amount();
    }

    // Production concern: the real payoff of a compact codec shows up at volume, not on a
    // single message -- measure the cumulative byte savings across a realistic batch.
    public static void main(String[] args) {
        ClassRegistry registry = new ClassRegistry();
        registry.register(Order.class, 7);

        int messageCount = 10_000;
        long verboseTotalBytes = 0;
        long compactTotalBytes = 0;

        for (int i = 0; i < messageCount; i++) {
            Order order = new Order("ORD-" + i, 10.0 + i);
            verboseTotalBytes += verboseEncode(order).length();
            compactTotalBytes += compactEncode(order, registry).length();
        }

        System.out.println("Verbose total bytes: " + verboseTotalBytes);
        System.out.println("Compact total bytes: " + compactTotalBytes);
        System.out.printf("Savings: %.1f%%%n", 100.0 * (verboseTotalBytes - compactTotalBytes) / verboseTotalBytes);
    }
}
```

How to run: `java KryoStyleCodecDemo.java`. Expected output: two total-byte counts followed by a `Savings: NN.N%` line, typically showing the compact encoding using well under half the bytes of the verbose one across 10,000 messages — the cumulative effect that makes a registered, compact codec worth adopting for high-volume, Java-to-Java transports, even though the saving on any single message looks modest.

## 6. Walkthrough

Trace a message from object to wire and back using a registered codec.

1. **Class registration (startup)**: both the sending and receiving application register the same set of classes with the same IDs when they start up — this is a one-time, out-of-band agreement, not something negotiated per message.
2. **Encode**: when a message needs to go out over a raw transport like TCP (card 0053), the codec looks up the payload's class in the registry, writes the compact numeric ID instead of the full class name, then writes the object's field values in a dense binary layout — no field names, no redundant class metadata.
3. **Transmit**: the resulting compact byte sequence goes out over the wire, smaller and faster to produce than an equivalent Java-serialized or JSON-encoded payload would have been.
4. **Decode**: the receiving side reads the numeric class ID first, looks it up in its own copy of the same registry to determine which class to reconstruct, then reads the field values in the agreed order to rebuild the object.
5. **Downstream use**: the reconstructed object flows into the receiving application's logic exactly as if it had arrived through any other transformer — the compactness of the wire format is invisible past this point.
6. **Failure mode**: if the two sides' registries ever disagree (a class registered under a different ID on one side, or a class present on one side but not the other), decoding fails outright — unlike JSON, where an unexpected field can often be ignored gracefully, a mismatched registry is a hard error, since the compact format has no field names to fall back on for graceful degradation.

```
Order object
  -> registry lookup: Order -> id 7
    -> encode: [7][id field][amount field]  (compact binary)
      -> transmit over TCP
        -> decode: read id 7 -> registry lookup: 7 -> Order
          -> reconstruct Order object -> downstream logic
```

## 7. Gotchas & takeaways

> **Gotcha:** because the compact wire format carries no field names or class names, both ends of the connection must have identical, synchronized class registrations — deploying a class registry change to only one side of a connection (a rolling deployment that updates senders before receivers, for instance) can cause silent decoding corruption or hard failures until both sides match again.

- Kryo-based codecs are a Java-to-Java optimization, like RMI (card 0068) — they don't help, and shouldn't be used, when a message needs to be read by a non-Java consumer or inspected as readable text for debugging.
- The byte-size and speed advantage matters most at high message volume or over bandwidth-constrained links; for low-volume flows, the operational complexity of keeping class registries synchronized across deployments may outweigh the savings.
- Unlike JSON or XML, a compact registered-class format isn't self-describing — logging or inspecting a raw Kryo-encoded payload directly (say, in a network capture) requires the same registry and decoder to make any sense of it, unlike a JSON payload a human can read directly.
- Reserve this codec approach for internal, high-throughput Java-to-Java links; default to a format transformer (card 0078) producing JSON, XML, or Avro for anything crossing a language boundary or needing straightforward debuggability.
