---
card: spring-boot
gi: 201
slug: auditing-auditeventrepository
title: Auditing (AuditEventRepository)
---

## 1. What it is

Spring Boot Actuator provides a lightweight **audit event** subsystem: any component can publish an `AuditApplicationEvent` to record security or business events. The events are stored in an `AuditEventRepository`. Spring Security auto-publishes common events (login success, login failure, access denied). The `/actuator/auditevents` endpoint exposes the stored events for querying.

## 2. Why & when

Use audit events when you need a tamper-evident activity trail without a full audit-logging framework:
- Who logged in, when, and from where.
- Which secured endpoint was accessed denied.
- Custom business events ("payment-approved", "user-deleted").

The built-in `InMemoryAuditEventRepository` fits development and short-lived debugging. Production systems typically replace it with a persistent implementation (database, log aggregator).

## 3. Core concept

**Publishing an event** (anywhere in your app):
```java
@Autowired ApplicationEventPublisher publisher;

publisher.publishEvent(new AuditApplicationEvent(
    "admin@example.com",     // principal
    "USER_DELETED",          // event type
    Map.of("userId", "42")   // data
));
```

**Spring Security auto-publishes** `AUTHENTICATION_SUCCESS`, `AUTHENTICATION_FAILURE`, `AUTHORIZATION_FAILURE` events — no code needed once an `AuditEventRepository` bean exists.

**Enable the repository** (required — not auto-configured):
```java
@Bean
public AuditEventRepository auditEventRepository() {
    return new InMemoryAuditEventRepository(1000); // keep last 1000 events
}
```

**Query via endpoint:**
```
GET /actuator/auditevents
GET /actuator/auditevents?principal=admin@example.com
GET /actuator/auditevents?type=AUTHENTICATION_FAILURE
GET /actuator/auditevents?after=2024-04-01T00:00:00Z
```

## 4. Diagram

<svg viewBox="0 0 680 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Security and custom code publish AuditApplicationEvents; ApplicationEventMulticaster routes them to AuditListener which stores in AuditEventRepository; /actuator/auditevents queries the repository">
  <!-- Sources -->
  <rect x="10" y="30" width="155" height="42" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="87" y="48" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">Spring Security</text>
  <text x="87" y="64" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">AUTHN_SUCCESS / FAILURE</text>

  <rect x="10" y="82" width="155" height="42" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="87" y="100" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">Your Code</text>
  <text x="87" y="116" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">publisher.publishEvent(...)</text>

  <!-- Arrows to multicaster -->
  <line x1="167" y1="52" x2="230" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#aua)"/>
  <line x1="167" y1="103" x2="230" y2="103" stroke="#8b949e" stroke-width="1.5" marker-end="url(#aua)"/>

  <!-- EventMulticaster -->
  <rect x="235" y="70" width="155" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="312" y="91" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">AuditListener</text>
  <text x="312" y="107" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">converts to AuditEvent</text>
  <text x="312" y="120" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">adds timestamp</text>

  <!-- Arrow to repository -->
  <line x1="392" y1="97" x2="450" y2="97" stroke="#6db33f" stroke-width="1.5" marker-end="url(#aub)"/>

  <!-- Repository -->
  <rect x="455" y="65" width="175" height="65" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="542" y="84" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">AuditEventRepository</text>
  <text x="542" y="100" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">InMemory (1000 capacity)</text>
  <text x="542" y="114" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">or custom (DB, Elasticsearch)</text>
  <text x="542" y="128" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">stores: principal, type, timestamp, data</text>

  <!-- Actuator reads -->
  <line x1="542" y1="133" x2="542" y2="160" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="4,2" marker-end="url(#auc)"/>
  <rect x="410" y="163" width="265" height="20" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="542" y="178" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">GET /actuator/auditevents?principal=x&amp;type=y</text>

  <defs>
    <marker id="aua" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="aub" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="auc" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

`AuditListener` bridges Spring's event bus to the repository; Spring Security emits events automatically when a repository bean exists.

## 5. Runnable example

```java
// AuditingDemo.java — simulates AuditEventRepository, event publishing, and endpoint queries
// How to run: java AuditingDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: register InMemoryAuditEventRepository @Bean; expose auditevents endpoint

import java.time.*;
import java.util.*;
import java.util.stream.Collectors;

public class AuditingDemo {

    record AuditEvent(Instant timestamp, String principal, String type, Map<String, Object> data) {
        @Override public String toString() {
            return String.format("[%s] %s  principal=%s  data=%s",
                    timestamp.toString().substring(0, 19), type, principal, data);
        }
    }

    // Simulates InMemoryAuditEventRepository
    static class AuditEventRepository {
        private final int capacity;
        private final Deque<AuditEvent> store;

        AuditEventRepository(int capacity) {
            this.capacity = capacity;
            this.store    = new ArrayDeque<>(capacity);
        }

        void add(String principal, String type, Map<String, Object> data) {
            if (store.size() >= capacity) store.pollFirst();
            store.addLast(new AuditEvent(Instant.now(), principal, type, data));
        }

        // GET /actuator/auditevents?principal=X&type=Y&after=Z
        List<AuditEvent> find(String principal, String type, Instant after) {
            return store.stream()
                .filter(e -> principal == null || principal.equals(e.principal()))
                .filter(e -> type      == null || type.equals(e.type()))
                .filter(e -> after     == null || e.timestamp().isAfter(after))
                .collect(Collectors.toList());
        }
    }

    // Simulates Spring Security publishing events
    static void springSecurityEvents(AuditEventRepository repo) {
        repo.add("alice@example.com", "AUTHENTICATION_SUCCESS", Map.of("remoteAddress","10.0.0.1"));
        repo.add("bob@example.com",   "AUTHENTICATION_FAILURE",
                Map.of("remoteAddress","10.0.0.2","reason","BadCredentials"));
        repo.add("alice@example.com", "AUTHORIZATION_FAILURE",
                Map.of("requestUrl","/admin/delete","role","ROLE_USER"));
        repo.add("charlie@example.com","AUTHENTICATION_SUCCESS",Map.of("remoteAddress","10.0.0.3"));
    }

    // Custom business events
    static void customBusinessEvents(AuditEventRepository repo) {
        repo.add("alice@example.com", "USER_DELETED",
                Map.of("deletedUserId","99","reason","account closure"));
        repo.add("charlie@example.com","PAYMENT_APPROVED",
                Map.of("orderId","ORD-500","amount","199.99"));
        repo.add("admin@example.com", "CONFIG_CHANGED",
                Map.of("property","feature.flag.x","newValue","true"));
    }

    static void printQuery(AuditEventRepository repo, String principal, String type, Instant after) {
        List<AuditEvent> results = repo.find(principal, type, after);
        String q = "GET /actuator/auditevents" +
                (principal != null ? "?principal=" + principal : "") +
                (type      != null ? (principal != null ? "&" : "?") + "type=" + type : "");
        System.out.println("\n" + q);
        System.out.println("  => " + results.size() + " event(s):");
        results.forEach(e -> System.out.println("     " + e));
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("=== Auditing / AuditEventRepository Demo ===\n");

        AuditEventRepository repo = new AuditEventRepository(1000);

        System.out.println("--- Publishing events (Spring Security + custom) ---");
        springSecurityEvents(repo);
        customBusinessEvents(repo);

        System.out.println("Total stored: " + repo.find(null, null, null).size() + " events\n");
        System.out.println("All events:");
        repo.find(null, null, null).forEach(e -> System.out.println("  " + e));

        // Query examples
        printQuery(repo, "alice@example.com", null, null);
        printQuery(repo, null, "AUTHENTICATION_FAILURE", null);
        printQuery(repo, null, "AUTHENTICATION_SUCCESS", null);

        System.out.println("\n--- Spring Boot configuration ---");
        System.out.println("@Bean AuditEventRepository auditEventRepository() {");
        System.out.println("    return new InMemoryAuditEventRepository(1000);");
        System.out.println("}");
        System.out.println("# expose endpoint:");
        System.out.println("management.endpoints.web.exposure.include=auditevents");
        System.out.println();
        System.out.println("# Publish custom event from service:");
        System.out.println("publisher.publishEvent(new AuditApplicationEvent(principal, \"USER_DELETED\", data));");
    }
}
```

**How to run:** `java AuditingDemo.java`

## 6. Walkthrough

- **`AuditEventRepository` with capacity 1000**: a rolling buffer matching `InMemoryAuditEventRepository(1000)`. Oldest events evicted when full.
- **`springSecurityEvents`**: simulates what Spring Security publishes automatically — `AUTHENTICATION_SUCCESS`, `AUTHENTICATION_FAILURE`, `AUTHORIZATION_FAILURE`. These appear the moment a repository bean exists; no configuration in `SecurityFilterChain` required.
- **`customBusinessEvents`**: your code calls `publisher.publishEvent(new AuditApplicationEvent(...))`. The payload is a `Map<String, Object>` of any contextual data.
- **`find` with filters**: mirrors `GET /actuator/auditevents?principal=alice@example.com` — filters by principal, type, and/or `after` timestamp. All filters are optional and combined.
- The final snippet shows the exact Spring Boot `@Bean` and publish call.

## 7. Gotchas & takeaways

> `AuditEventRepository` is **not auto-configured**. If you add `starter-actuator` and Spring Security but forget the `@Bean`, no events are stored — Spring Security events are silently discarded and `/actuator/auditevents` returns 404.

> `InMemoryAuditEventRepository` is **not persistent** — events are lost on restart. For compliance or production auditing, implement `AuditEventRepository` backed by a database or forward events to a log aggregation system.

- Default capacity of `InMemoryAuditEventRepository` is 1000.
- Expose: `management.endpoints.web.exposure.include=auditevents`.
- Secure the endpoint — it contains authentication attempt details and business events.
- The `/actuator/auditevents` response includes `timestamp`, `principal`, `type`, and `data` fields.
- To test: in a Spring Boot app with Spring Security, log in with wrong credentials — the `AUTHENTICATION_FAILURE` event appears immediately in `/actuator/auditevents`.
