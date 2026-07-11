---
card: spring-data
gi: 182
slug: conditional-get-etag-last-modified
title: "Conditional GET (ETag/Last-Modified)"
---

## 1. What it is

Spring Data REST automatically supports conditional GET requests for entities that carry a `@Version` field: it computes an `ETag` header (derived from the version) or a `Last-Modified` header (from an `@LastModifiedDate`), and honors `If-None-Match`/`If-Modified-Since` request headers by returning a `304 Not Modified` with no body when the resource hasn't actually changed.

```java
@Entity
class Customer {
    @Id String id;
    @Version Long version; // enables automatic ETag support

    @LastModifiedDate Instant updatedAt; // enables automatic Last-Modified support
}
```

## 2. Why & when

Every GET request so far in this course has assumed the client always wants the full response body. Conditional GET is an HTTP-level optimization: the client says "give me this resource, but only if it's changed since I last saw it" — and if nothing changed, the server can skip re-serializing and re-transmitting the entire body, replying with an empty `304` instead.

Reach for conditional GET support when:

- Clients repeatedly poll the same resource (a dashboard refreshing every few seconds) and most polls find no actual change — conditional GET turns most of those into cheap, bodyless responses.
- The entity already carries `@Version` (for optimistic locking) or `@LastModifiedDate` (for auditing) — Spring Data REST derives conditional GET support from fields you likely already have for other reasons.
- Bandwidth or server-side serialization cost matters enough that avoiding redundant full responses is worth the extra request/response header bookkeeping.

## 3. Core concept

```
 First request:
   GET /customers/c1
   ->  200 OK
       ETag: "3"                       (derived from @Version)
       { "name": "Amara", ... }

 Client caches the ETag, requests again later:
   GET /customers/c1
   If-None-Match: "3"
   ->  304 Not Modified                 (no body -- version still 3, nothing changed)

 After an update (version bumps to 4):
   GET /customers/c1
   If-None-Match: "3"
   ->  200 OK
       ETag: "4"
       { "name": "Amara Okafor", ... }  (full body -- resource genuinely changed)
```

The server compares the client's cached version tag against the current one and decides, per request, whether a full body is actually needed.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client sends If-None-Match with a cached ETag, receiving either a 304 with no body or a 200 with a fresh body and new ETag">
  <rect x="20" y="20" width="270" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="155" y="47" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">GET, If-None-Match: "3"</text>

  <line x1="290" y1="42" x2="350" y2="42" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a15)"/>

  <rect x="360" y="20" width="260" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="490" y="47" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">server compares versions</text>

  <rect x="20" y="100" width="270" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="155" y="127" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">unchanged: 304, no body</text>

  <rect x="360" y="100" width="260" height="45" rx="8" fill="#79c0ff30" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="490" y="127" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">changed: 200, full body + new ETag</text>

  <line x1="490" y1="65" x2="155" y2="95" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a15)"/>
  <line x1="490" y1="65" x2="490" y2="95" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a15)"/>

  <defs><marker id="a15" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The server branches on whether the client's cached ETag still matches the current version.

## 5. Runnable example

The scenario: a client repeatedly polling a customer resource, evolving from a naive server that always returns the full body, to ETag-based conditional GET returning 304 when nothing changed, to `Last-Modified`/`If-Modified-Since` as the date-based alternative — both mechanisms working together, the way Spring Data REST supports both.

### Level 1 — Basic

Model the naive baseline: every GET returns the full body, regardless of whether the client already has the current data.

```java
import java.util.*;

public class ConditionalGetLevel1 {
    public static void main(String[] args) {
        GraphStore store = new GraphStore();
        store.save(new Customer("c1", "Amara", 1));

        System.out.println("Poll 1: " + get(store, "c1")); // full body
        System.out.println("Poll 2: " + get(store, "c1")); // full body AGAIN, even though nothing changed
        System.out.println("Poll 3: " + get(store, "c1")); // full body a THIRD time, still unchanged
    }

    static String get(GraphStore store, String id) {
        Customer c = store.findById(id);
        return "200 OK, body={ name: " + c.name + ", version: " + c.version + " }";
    }
}

class Customer {
    String id, name; long version;
    Customer(String id, String name, long version) { this.id = id; this.name = name; this.version = version; }
}

class GraphStore {
    private final Map<String, Customer> nodes = new HashMap<>();
    void save(Customer c) { nodes.put(c.id, c); }
    Customer findById(String id) { return nodes.get(id); }
}
```

How to run: `java ConditionalGetLevel1.java`

Every one of the three polls returns the exact same full response body — the client has no way to say "skip the body if nothing changed," and the server has no way to skip the work of serializing it.

### Level 2 — Intermediate

Add ETag-based conditional GET: the server includes an `ETag` derived from `version`, and honors a simulated `If-None-Match` header by returning `304` with no body when the version matches.

```java
import java.util.*;

public class ConditionalGetLevel2 {
    public static void main(String[] args) {
        GraphStore store = new GraphStore();
        store.save(new Customer("c1", "Amara", 1));

        Response first = get(store, "c1", null); // no cached ETag yet
        System.out.println("Poll 1: " + first);

        Response second = get(store, "c1", first.etag); // client sends back the ETag it received
        System.out.println("Poll 2: " + second); // unchanged -> 304, no body

        store.save(new Customer("c1", "Amara Okafor", 2)); // entity actually changes, version bumps
        Response third = get(store, "c1", first.etag); // client still has the STALE etag
        System.out.println("Poll 3: " + third); // changed -> 200, full body, new ETag
    }

    static Response get(GraphStore store, String id, String ifNoneMatch) {
        Customer c = store.findById(id);
        String currentEtag = "\"" + c.version + "\"";
        if (currentEtag.equals(ifNoneMatch)) {
            return new Response(304, null, currentEtag); // unchanged -- no body needed
        }
        return new Response(200, "{ name: " + c.name + " }", currentEtag);
    }
}

class Response {
    int status; String body, etag;
    Response(int status, String body, String etag) { this.status = status; this.body = body; this.etag = etag; }
    public String toString() { return status + (body != null ? ", body=" + body : ", (no body)") + ", ETag=" + etag; }
}

class Customer {
    String id, name; long version;
    Customer(String id, String name, long version) { this.id = id; this.name = name; this.version = version; }
}

class GraphStore {
    private final Map<String, Customer> nodes = new HashMap<>();
    void save(Customer c) { nodes.put(c.id, c); }
    Customer findById(String id) { return nodes.get(id); }
}
```

How to run: `java ConditionalGetLevel2.java`

Poll 2 sends back the ETag it received from poll 1; since the entity's version hasn't changed, the server returns `304` with no body at all. Poll 3 uses the same stale ETag, but the entity has genuinely changed in between (version bumped to 2), so the server correctly detects the mismatch and returns the full body with a fresh ETag.

### Level 3 — Advanced

Add `Last-Modified`/`If-Modified-Since` as the date-based alternative to `ETag`/`If-None-Match`, supporting both conditional mechanisms the way Spring Data REST does — a client can use whichever header pair fits its caching strategy.

```java
import java.util.*;
import java.time.*;

public class ConditionalGetLevel3 {
    public static void main(String[] args) {
        GraphStore store = new GraphStore();
        Instant t1 = Instant.parse("2026-07-01T10:00:00Z");
        store.save(new Customer("c1", "Amara", 1, t1));

        // Client using ETag-based caching:
        Response viaEtag = get(store, "c1", "\"1\"", null);
        System.out.println("ETag-based poll (unchanged): " + viaEtag);

        // Client using Last-Modified-based caching, checking against the SAME unchanged resource:
        Response viaDate = get(store, "c1", null, t1);
        System.out.println("Date-based poll (unchanged): " + viaDate);

        // Resource changes:
        Instant t2 = Instant.parse("2026-07-01T10:05:00Z");
        store.save(new Customer("c1", "Amara Okafor", 2, t2));

        Response viaEtagAfterChange = get(store, "c1", "\"1\"", null);
        System.out.println("ETag-based poll (changed): " + viaEtagAfterChange);

        Response viaDateAfterChange = get(store, "c1", null, t1);
        System.out.println("Date-based poll (changed): " + viaDateAfterChange);
    }

    static Response get(GraphStore store, String id, String ifNoneMatch, Instant ifModifiedSince) {
        Customer c = store.findById(id);
        String currentEtag = "\"" + c.version + "\"";
        boolean etagMatches = currentEtag.equals(ifNoneMatch);
        boolean notModifiedSince = ifModifiedSince != null && !c.updatedAt.isAfter(ifModifiedSince);

        if (etagMatches || notModifiedSince) {
            return new Response(304, null, currentEtag, c.updatedAt);
        }
        return new Response(200, "{ name: " + c.name + " }", currentEtag, c.updatedAt);
    }
}

class Response {
    int status; String body, etag; Instant lastModified;
    Response(int status, String body, String etag, Instant lastModified) {
        this.status = status; this.body = body; this.etag = etag; this.lastModified = lastModified;
    }
    public String toString() { return status + (body != null ? ", body=" + body : ", (no body)") + ", Last-Modified=" + lastModified; }
}

class Customer {
    String id, name; long version; Instant updatedAt;
    Customer(String id, String name, long version, Instant updatedAt) {
        this.id = id; this.name = name; this.version = version; this.updatedAt = updatedAt;
    }
}

class GraphStore {
    private final Map<String, Customer> nodes = new HashMap<>();
    void save(Customer c) { nodes.put(c.id, c); }
    Customer findById(String id) { return nodes.get(id); }
}
```

How to run: `java ConditionalGetLevel3.java`

Both the ETag-based and date-based checks agree in every case here, because both are derived from the same underlying change — this is intentional: `ETag`/`If-None-Match` and `Last-Modified`/`If-Modified-Since` are two independent HTTP mechanisms answering the same question ("has this changed since I last saw it"), and a well-behaved server keeps both consistent with the entity's actual state.

## 6. Walkthrough

Execution starts in `main` for Level 3. A customer is saved at `version=1`, `updatedAt=10:00:00Z`. Two polls check the *same unchanged* resource, one using each mechanism:

```
ETag-based poll (unchanged): 304, (no body), Last-Modified=2026-07-01T10:00:00Z
Date-based poll (unchanged): 304, (no body), Last-Modified=2026-07-01T10:00:00Z
```

The entity is then updated (`version=2`, `updatedAt=10:05:00Z`), and the same two stale client-side values (`"1"` and `10:00:00Z`) are checked again — both now correctly detect the change:

```
ETag-based poll (changed): 200, body={ name: Amara Okafor }, Last-Modified=2026-07-01T10:05:00Z
Date-based poll (changed): 200, body={ name: Amara Okafor }, Last-Modified=2026-07-01T10:05:00Z
```

In a real Spring Data REST application, this logic runs automatically inside the framework's response-building path — no controller code checks `If-None-Match` or `If-Modified-Since` by hand, as long as the entity carries `@Version` and/or `@LastModifiedDate`. The framework compares the incoming conditional headers against the entity's current state and short-circuits to a bodyless `304` before serialization ever runs, saving both the server the work of building the response and the client the bandwidth of receiving it.

## 7. Gotchas & takeaways

> Gotcha: conditional GET support is derived automatically from `@Version`/`@LastModifiedDate` — an entity with neither field gets no automatic `ETag`/`Last-Modified` support at all, and every `GET` against it always returns a full `200` body, silently missing out on the optimization with no error or warning.

> Gotcha: a client that caches an `ETag` but never actually sends `If-None-Match` on subsequent requests gets no benefit either — conditional GET is a two-sided contract; the server supporting it is necessary but not sufficient, the client has to participate by round-tripping the header back.

- Conditional GET lets a client ask "only send the body if this has actually changed," turning unchanged polls into cheap `304 Not Modified` responses with no body.
- Spring Data REST derives `ETag` support from `@Version` and `Last-Modified` support from `@LastModifiedDate` automatically — no extra configuration beyond having those fields for their original purposes.
- `ETag`/`If-None-Match` and `Last-Modified`/`If-Modified-Since` are two independent mechanisms answering the same question; a well-implemented server keeps them consistent with each other.
- Both the client and server need to participate — a server offering conditional GET support does nothing if the client never sends the conditional headers back.
