---
card: spring-framework
gi: 54
slug: collections-list-set-map-props
title: Collections (List, Set, Map, Props)
---

## 1. What it is

Spring can inject Java collections — `List`, `Set`, `Map`, and `Properties` — directly into beans. In XML you use `<list>`, `<set>`, `<map>`, and `<props>` elements inside `<property>` or `<constructor-arg>`. In annotation-driven code, `@Value` can inject comma-separated strings as `List<String>`, and `@Autowired` can inject all beans of a type as a `List<T>` or `Map<String,T>`.

```java
// Annotation: inject ALL beans of type Validator as a List
@Autowired
private List<Validator> validators;   // ordered, all Validator beans injected

// Annotation: inject all Validator beans as a Map<name → instance>
@Autowired
private Map<String, Validator> validatorMap;

// @Value: comma-separated list from properties
@Value("${allowed.ips:127.0.0.1,::1}")
private List<String> allowedIps;
```

In XML this looks like:
```xml
<bean id="emailService" class="EmailService">
    <property name="allowedDomains">
        <list>
            <value>example.com</value>
            <value>partner.io</value>
        </list>
    </property>
    <property name="config">
        <map>
            <entry key="timeout" value="5000"/>
            <entry key="retries" value="3"/>
        </map>
    </property>
</bean>
```

In one sentence: **Spring's collection injection lets you wire `List`, `Set`, `Map`, and `Properties` values (scalars or bean references) into a bean's fields, enabling configuration-driven sets of values and autowiring all beans of a type as a single collection.**

## 2. Why & when

Collection injection is used when:

- **Multiple values of the same type** belong together — allowed IP ranges, environment tags, CORS origins.
- **A plugin/extension model** — all beans implementing a `Plugin` or `Validator` interface are gathered into a `List<Plugin>` automatically by Spring.
- **Key-value configuration** — a `Map<String, String>` or `Properties` holds named settings.
- **Ordered pipelines** — a `List<Filter>` or `List<HandlerInterceptor>` where order matters; annotate with `@Order` or implement `Ordered` to control sequence.

## 3. Core concept

```
Spring collection injection types:

  <list>     → java.util.List  (ordered, duplicates allowed)
  <set>      → java.util.Set   (unordered, no duplicates)
  <map>      → java.util.Map   (key-value, typed keys and values)
  <props>    → java.util.Properties (String keys, String values)

Each collection element can be:
  <value>text</value>       → String (converted to target type)
  <ref bean="beanId"/>      → reference to another bean

@Autowired on List<T>:
  Spring finds ALL beans assignable to T, orders by @Order/@Priority, injects.

@Autowired on Map<String, T>:
  Spring finds ALL beans of type T; Map key = bean name (id).
```

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring collection injection: List, Set, Map, and Properties wired into a bean">
  <defs>
    <marker id="a54" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <!-- Container -->
  <rect x="5" y="5" width="670" height="210" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="340" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Spring IoC Container — Collection Injection</text>

  <!-- List -->
  <rect x="15" y="35" width="140" height="80" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="85" y="52" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">List&lt;String&gt;</text>
  <text x="85" y="66" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">[0] example.com</text>
  <text x="85" y="79" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">[1] partner.io</text>
  <text x="85" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">[2] internal.net</text>
  <text x="85" y="108" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">ordered, duplicates ok</text>

  <!-- Set -->
  <rect x="175" y="35" width="140" height="80" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="245" y="52" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Set&lt;String&gt;</text>
  <text x="245" y="66" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">READ</text>
  <text x="245" y="79" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">WRITE</text>
  <text x="245" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">DELETE</text>
  <text x="245" y="108" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">unordered, no duplicates</text>

  <!-- Map -->
  <rect x="335" y="35" width="150" height="80" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="410" y="52" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Map&lt;String,String&gt;</text>
  <text x="410" y="66" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">timeout → 5000</text>
  <text x="410" y="79" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">retries → 3</text>
  <text x="410" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">maxSize → 100</text>
  <text x="410" y="108" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">key-value, typed</text>

  <!-- Props -->
  <rect x="505" y="35" width="155" height="80" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="582" y="52" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Properties</text>
  <text x="582" y="66" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">smtp.host=mail.io</text>
  <text x="582" y="79" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">smtp.port=587</text>
  <text x="582" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">smtp.ssl=true</text>
  <text x="582" y="108" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">String→String only</text>

  <!-- Arrows to bean -->
  <line x1="85"  y1="115" x2="290" y2="160" stroke="#6db33f" stroke-width="1.3" marker-end="url(#a54)"/>
  <line x1="245" y1="115" x2="310" y2="160" stroke="#6db33f" stroke-width="1.3" marker-end="url(#a54)"/>
  <line x1="410" y1="115" x2="370" y2="160" stroke="#6db33f" stroke-width="1.3" marker-end="url(#a54)"/>
  <line x1="582" y1="115" x2="390" y2="160" stroke="#6db33f" stroke-width="1.3" marker-end="url(#a54)"/>

  <!-- Target bean -->
  <rect x="240" y="162" width="200" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="340" y="178" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">EmailService bean</text>
  <text x="340" y="194" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">all four collections injected</text>
</svg>

All four collection types are injected into one bean. Each has a different Java type: `List` (ordered), `Set` (unique), `Map` (key→value), `Properties` (String→String only).

## 5. Runnable example

Scenario: a `NotificationHub` that holds a list of allowed channels, a set of blocked domains, a map of per-channel configs, and a `Properties` object for SMTP settings.

### Level 1 — Basic

Inject and use a `List`, `Set`, `Map`, and `Properties` — all pre-configured at construction time.

```java
// CollectionsDemo.java — run with: java CollectionsDemo.java
import java.util.*;

public class CollectionsDemo {

    static class NotificationHub {
        final List<String>        channels;        // List: ordered
        final Set<String>         blockedDomains;  // Set: unique, fast lookup
        final Map<String, String> channelConfig;   // Map: key → value
        final Properties          smtpProps;       // Properties: String→String

        NotificationHub(List<String> channels,
                         Set<String>  blockedDomains,
                         Map<String, String> channelConfig,
                         Properties smtpProps) {
            this.channels       = channels;
            this.blockedDomains = blockedDomains;
            this.channelConfig  = channelConfig;
            this.smtpProps      = smtpProps;
            System.out.println("[BEAN] NotificationHub created");
            System.out.println("  channels="       + channels);
            System.out.println("  blocked="        + blockedDomains);
            System.out.println("  channelConfig="  + channelConfig);
            System.out.println("  smtp.host="      + smtpProps.getProperty("smtp.host"));
        }

        void send(String channel, String recipientEmail, String message) {
            String domain = recipientEmail.contains("@")
                ? recipientEmail.split("@")[1] : "";
            if (blockedDomains.contains(domain)) {
                System.out.println("[BLOCK] " + recipientEmail + " (domain blocked)");
                return;
            }
            if (!channels.contains(channel)) {
                System.out.println("[SKIP]  Unknown channel: " + channel);
                return;
            }
            String rate = channelConfig.getOrDefault("rateLimit." + channel, "100/min");
            System.out.println("[SEND]  channel=" + channel
                + " to=" + recipientEmail + " rate=" + rate + " msg=" + message);
        }
    }

    public static void main(String[] args) {
        List<String> channels = List.of("email", "sms", "push");

        Set<String> blocked = new LinkedHashSet<>(List.of(
            "spam.com", "disposable.io", "throwaway.net"
        ));

        Map<String, String> config = new LinkedHashMap<>(Map.of(
            "rateLimit.email", "50/min",
            "rateLimit.sms",   "10/min",
            "rateLimit.push",  "200/min"
        ));

        Properties smtp = new Properties();
        smtp.setProperty("smtp.host",    "smtp.sendgrid.net");
        smtp.setProperty("smtp.port",    "587");
        smtp.setProperty("smtp.ssl",     "true");
        smtp.setProperty("smtp.timeout", "5000");

        NotificationHub hub = new NotificationHub(channels, blocked, config, smtp);
        System.out.println();
        hub.send("email", "alice@example.com",   "Your order shipped");
        hub.send("email", "bob@spam.com",         "Your order shipped");
        hub.send("sms",   "carol@example.com",   "Verification code: 123456");
        hub.send("fax",   "dave@example.com",    "Document ready");
    }
}
```

How to run: `java CollectionsDemo.java`

`channels` is a `List` — order matters (email is first priority). `blocked` is a `Set` — O(1) domain lookup, no duplicates. `channelConfig` maps channel names to rate limits. `smtp` is a `Properties` object holding String→String SMTP config. Spring injects all four with `<list>`, `<set>`, `<map>`, `<props>` elements in XML.

### Level 2 — Intermediate

`@Autowired` collection injection: Spring gathers ALL beans of type `MessageSender` into a `List<MessageSender>`, ordered by `@Order`.

```java
// CollectionsDemo2.java — run with: java CollectionsDemo2.java
import java.util.*;

public class CollectionsDemo2 {

    // ── sender interface ───────────────────────────────────────────────
    interface MessageSender {
        String channel();
        boolean send(String to, String msg);
    }

    // ── implementations with order annotation ─────────────────────────
    static class EmailSender implements MessageSender {
        private final int order;
        EmailSender(int order) { this.order = order; }
        @Override public String channel() { return "email"; }
        @Override public boolean send(String to, String msg) {
            System.out.println("  [EMAIL:" + order + "] to=" + to + " msg=" + msg);
            return true;
        }
    }

    static class SmsSender implements MessageSender {
        private final int order;
        SmsSender(int order) { this.order = order; }
        @Override public String channel() { return "sms"; }
        @Override public boolean send(String to, String msg) {
            System.out.println("  [SMS:" + order + "] to=" + to + " msg=" + msg.substring(0, Math.min(msg.length(), 20)));
            return msg.length() <= 160;
        }
    }

    static class PushSender implements MessageSender {
        private final int order;
        PushSender(int order) { this.order = order; }
        @Override public String channel() { return "push"; }
        @Override public boolean send(String to, String msg) {
            System.out.println("  [PUSH:" + order + "] to=" + to + " title=" + msg.substring(0, Math.min(msg.length(), 30)));
            return true;
        }
    }

    // ── hub receives ALL senders as List (simulating @Autowired List<T>) ─
    static class NotificationHub {
        private final List<MessageSender>        senders;      // @Autowired List<MessageSender>
        private final Map<String, MessageSender> senderMap;   // @Autowired Map<String, T>

        NotificationHub(List<MessageSender> senders) {
            this.senders   = senders;
            this.senderMap = new LinkedHashMap<>();
            for (MessageSender s : senders) senderMap.put(s.channel(), s);
            System.out.println("[BEAN] NotificationHub: senders=" + senderMap.keySet());
        }

        // Try all senders in order (fanout)
        void broadcast(String to, String msg) {
            System.out.println("[BROADCAST] to=" + to);
            senders.forEach(s -> s.send(to, msg));
        }

        // Send via specific channel
        void send(String channel, String to, String msg) {
            MessageSender s = senderMap.get(channel);
            if (s == null) { System.out.println("[ERROR] unknown channel: " + channel); return; }
            System.out.println("[SEND] channel=" + channel + " to=" + to);
            s.send(to, msg);
        }
    }

    static NotificationHub buildContainer() {
        // Spring would autowire all MessageSender beans ordered by @Order
        List<MessageSender> senders = List.of(
            new EmailSender(1),   // @Order(1) — first in list
            new SmsSender(2),     // @Order(2)
            new PushSender(3)     // @Order(3)
        );
        return new NotificationHub(senders);
    }

    public static void main(String[] args) {
        NotificationHub hub = buildContainer();
        System.out.println();
        hub.broadcast("alice@example.com", "Your password was changed");
        System.out.println();
        hub.send("sms", "+15551234567", "Verification code: 987654");
    }
}
```

How to run: `java CollectionsDemo2.java`

`List<MessageSender>` collects all three senders in `@Order` sequence. `Map<String, MessageSender>` is built from that list with `channel()` as the key — in real Spring, `@Autowired Map<String, T>` uses the bean name as the key automatically. Adding a new `SlackSender` bean requires no change to `NotificationHub`.

### Level 3 — Advanced

Typed `Map<String, List<String>>` groupings, `Properties` as a config overlay, and a `Set<String>` for deduplication of processed event IDs.

```java
// CollectionsDemo3.java — run with: java CollectionsDemo3.java
import java.util.*;
import java.util.stream.Collectors;

public class CollectionsDemo3 {

    // ── complex collection-driven routing engine ───────────────────────
    static class EventRouter {
        // channel → list of subscriber email addresses
        final Map<String, List<String>> subscriptions;
        // processed event IDs (deduplication)
        final Set<String>               processed;
        // overrides: channel.key → value
        final Properties                channelProps;

        EventRouter(Map<String, List<String>> subscriptions,
                    Set<String>               processed,
                    Properties                channelProps) {
            this.subscriptions = subscriptions;
            this.processed     = processed;
            this.channelProps  = channelProps;
            System.out.println("[BEAN] EventRouter");
            System.out.println("  subscriptions: " + subscriptions.keySet());
            System.out.println("  pre-processed: " + processed);
        }

        void dispatch(String eventId, String channel, String payload) {
            System.out.println("[EVENT] id=" + eventId + " channel=" + channel);
            if (processed.contains(eventId)) {
                System.out.println("  [SKIP] duplicate event");
                return;
            }
            processed.add(eventId);

            List<String> subscribers = subscriptions.getOrDefault(channel, List.of());
            if (subscribers.isEmpty()) {
                System.out.println("  [NO SUBS] no subscribers for " + channel);
                return;
            }

            boolean enabled = Boolean.parseBoolean(
                channelProps.getProperty(channel + ".enabled", "true")
            );
            int maxPayload = Integer.parseInt(
                channelProps.getProperty(channel + ".maxPayloadBytes", "1024")
            );

            if (!enabled) { System.out.println("  [DISABLED] channel=" + channel); return; }
            if (payload.length() > maxPayload) {
                System.out.println("  [TRUNCATED] payload too large: "
                    + payload.length() + " > " + maxPayload);
                payload = payload.substring(0, maxPayload) + "...[truncated]";
            }

            for (String sub : subscribers) {
                System.out.println("  [DELIVER] to=" + sub + " payload=" + payload);
            }
            System.out.println("  [DONE] dispatched to " + subscribers.size() + " subscribers");
        }

        String stats() {
            return "EventRouter{channels=" + subscriptions.size()
                + " subscribers=" + subscriptions.values().stream()
                    .mapToInt(List::size).sum()
                + " processedCount=" + processed.size() + "}";
        }
    }

    static EventRouter buildContainer() {
        Map<String, List<String>> subs = new LinkedHashMap<>();
        subs.put("orders",   List.of("alice@example.com", "ops@example.com"));
        subs.put("payments", List.of("finance@example.com", "cfo@example.com", "alice@example.com"));
        subs.put("alerts",   List.of("oncall@example.com"));

        // Set pre-seeded with already-processed IDs (prevents replay)
        Set<String> alreadyProcessed = new LinkedHashSet<>(List.of("evt-0001", "evt-0002"));

        Properties props = new Properties();
        props.setProperty("orders.enabled",           "true");
        props.setProperty("orders.maxPayloadBytes",   "512");
        props.setProperty("payments.enabled",         "true");
        props.setProperty("payments.maxPayloadBytes", "256");
        props.setProperty("alerts.enabled",           "false");  // alerts channel disabled

        return new EventRouter(subs, alreadyProcessed, props);
    }

    public static void main(String[] args) {
        EventRouter router = buildContainer();
        System.out.println();
        router.dispatch("evt-0003", "orders",   "{\"orderId\":\"ORD-42\",\"status\":\"shipped\"}");
        System.out.println();
        router.dispatch("evt-0001", "payments", "{\"amount\":99.99}");  // duplicate → skip
        System.out.println();
        router.dispatch("evt-0004", "alerts",   "{\"severity\":\"critical\"}");  // disabled
        System.out.println();
        router.dispatch("evt-0005", "payments", "x".repeat(300));  // payload too large
        System.out.println();
        System.out.println("[STATS] " + router.stats());
    }
}
```

How to run: `java CollectionsDemo3.java`

`subscriptions` is a `Map<String, List<String>>` — a map where each value is itself a list. `processed` is a `Set<String>` that grows at runtime (deduplication). `channelProps` is a `Properties` object used to look up per-channel settings. Event `evt-0001` is pre-loaded in `processed`, so it is silently deduplicated. The `alerts` channel is disabled via `Properties`. The large payment payload is truncated to `maxPayloadBytes=256`.

## 6. Walkthrough

**Container startup:**

```
buildContainer()
  → subscriptions Map created:
      orders   → [alice@example.com, ops@example.com]
      payments → [finance@example.com, cfo@example.com, alice@example.com]
      alerts   → [oncall@example.com]
  → processed Set seeded: {evt-0001, evt-0002}
  → channelProps loaded: 6 entries
  → EventRouter constructor: prints channels + pre-processed
```

**`dispatch("evt-0003", "orders", "...")` — data through each layer:**

```
Step 1: processed.contains("evt-0003") → false → continue
Step 2: processed.add("evt-0003")  → processed = {evt-0001, evt-0002, evt-0003}
Step 3: subscriptions.get("orders") → [alice@example.com, ops@example.com]
Step 4: channelProps.getProperty("orders.enabled") → "true"
Step 5: channelProps.getProperty("orders.maxPayloadBytes") → "512"
Step 6: payload.length()=44 ≤ 512 → no truncation
Step 7: for each subscriber → [DELIVER] x2
Output:
  [DELIVER] to=alice@example.com payload={"orderId":"ORD-42","status":"shipped"}
  [DELIVER] to=ops@example.com   payload={"orderId":"ORD-42","status":"shipped"}
  [DONE] dispatched to 2 subscribers
```

**`dispatch("evt-0001", "payments", "...")` — duplicate:**

```
Step 1: processed.contains("evt-0001") → TRUE
  → [SKIP] duplicate event
  → return immediately
```

**`dispatch("evt-0005", "payments", "xxx...300chars")` — payload truncated:**

```
Step 3: subscriptions.get("payments") → [finance, cfo, alice]
Step 5: maxPayloadBytes = 256
Step 6: payload.length()=300 > 256
  → payload = payload[0..256] + "...[truncated]"
Step 7: deliver truncated payload to 3 subscribers
```

## 7. Gotchas & takeaways

> **`@Autowired List<T>` injects ALL beans of type `T` in the application context.** If you add a new implementation of the interface, it automatically appears in the list. Order is determined by `@Order`/`Ordered` — without it, order is undefined.

> **`Properties` only holds `String→String` entries.** Using `Map<String, Object>` when you need typed values is fine, but `<props>` in XML is strictly string-keyed, string-valued. Use `<map>` with `value-type` for typed values.

- In XML, `<list>` can contain both `<value>` (scalars) and `<ref bean="..."/>` (bean references) — they can be mixed in the same list.
- `@Value("${key}")` on a `List<String>` field uses a comma as the delimiter by default: `"a,b,c"` → `["a","b","c"]`. Custom delimiters need a `ConversionService` customisation.
- `@Autowired Map<String, T>` uses the **bean name** as the key — not the return value of any method. Name your beans clearly if the key matters.
- Spring's injected collections are unmodifiable by default when using annotation injection. If you need a mutable copy, assign to a `new ArrayList<>(injectedList)`.
