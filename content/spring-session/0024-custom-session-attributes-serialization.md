---
card: spring-session
gi: 24
slug: custom-session-attributes-serialization
title: "Custom session attributes & serialization"
---

## 1. What it is

Whenever a session attribute is written to an external store, it has to be serialized into bytes (or a store-native format like JSON or a MongoDB document) for storage, and deserialized back into a live Java object on read. Spring Session's stores default to different serialization strategies (Redis typically uses JSON via Jackson by default in recent versions, or Java's built-in serialization depending on configuration; JDBC stores attributes as serialized bytes in a column), and customizing this — choosing a serialization format, or controlling exactly what gets serialized — is necessary whenever the default doesn't fit an application's actual attribute types.

## 2. Why & when

The moment an object leaves a single JVM's memory (which is exactly what happens the instant it's stored in an external session store), it needs a portable, storage-appropriate representation — and that representation has real implications: Java's native serialization requires every stored class to implement `Serializable` and is notoriously brittle across class version changes (a field added or removed to a class can break deserialization of previously-stored data). JSON-based serialization avoids the version-brittleness problem and is human-readable when inspecting the store directly, but requires the stored types to be JSON-friendly (no complex object graphs with unclear ownership, no non-default constructors without help) and needs Jackson configured to trust deserializing arbitrary application classes.

Reach for custom serialization configuration when:

- Storing a domain object as a session attribute that isn't a simple, JSON-friendly type (a complex object graph, a type without a no-args constructor) — Jackson's default behavior may need explicit `@JsonCreator`/`@JsonProperty` annotations or a custom serializer/deserializer.
- Debugging deserialization failures after a class change — a classic symptom of Java-native serialization's version brittleness, where sessions created before a class change fail to deserialize after a deployment, sometimes crashing requests that touch them.
- Deciding what should even be stored in the session at all — some objects (a live database connection, a non-serializable framework object) simply can't and shouldn't be serialized, and belong in the session only as an identifier that's re-resolved on each request instead.

## 3. Core concept

Think of storing a Java object in a session as shipping a piece of furniture overseas — it needs to be disassembled into a flat-packed form (serialization) that survives the journey, with clear labeled instructions for reassembly at the destination (deserialization). Java's native serialization is like flat-packing with instructions specific to the *exact* factory blueprint used that day — if the factory changes the blueprint even slightly (the class definition changes), old flat-packed furniture may no longer reassemble correctly. JSON serialization is more like packing with universal, human-readable assembly instructions (field names and values as text) that are more forgiving of minor blueprint changes and can, in a pinch, even be manually inspected and understood by a person without needing the original blueprint at all.

```java
public class CartItem implements Serializable {
    private static final long serialVersionUID = 1L; // pins the serialization contract
    private String productId;
    private int quantity;
}
```

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Java object is serialized to a storage-appropriate format on write and deserialized back on read, on each side of the external store boundary">
  <rect x="20" y="30" width="180" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Live Java object</text>
  <text x="110" y="75" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">in this JVM's memory</text>

  <rect x="480" y="30" width="180" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="570" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Live Java object</text>
  <text x="570" y="75" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">reconstructed, another JVM</text>

  <rect x="250" y="30" width="180" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Serialized bytes / JSON</text>
  <text x="340" y="75" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">in the external store</text>

  <line x1="200" y1="60" x2="245" y2="60" stroke="#8b949e" stroke-width="1.5"/>
  <text x="222" y="45" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">serialize</text>
  <line x1="430" y1="60" x2="475" y2="60" stroke="#8b949e" stroke-width="1.5"/>
  <text x="452" y="45" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">deserialize</text>
</svg>

Every session attribute crosses this boundary on every save and every load — the format chosen for the middle box has real consequences for both compatibility and observability.

## 5. Runnable example

The scenario: storing a custom domain object (a cart) as a session attribute with Java serialization first, growing to switch to JSON serialization via a configured `RedisSerializer` and seeing the tangible readability and compatibility difference, and finally handling an actual class-evolution scenario (adding a field) safely under each serialization strategy.

### Level 1 — Basic

```java
// Cart.java (must implement Serializable for Java-native serialization to work at all)
import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;

public class Cart implements Serializable {
    private static final long serialVersionUID = 1L;

    private List<String> items = new ArrayList<>();

    public void addItem(String item) { items.add(item); }
    public List<String> getItems() { return items; }
}
```

```java
// CartController.java
import jakarta.servlet.http.HttpSession;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class CartController {

    @GetMapping("/cart/add")
    public String add(HttpSession session, String item) {
        Cart cart = (Cart) session.getAttribute("cart");
        if (cart == null) {
            cart = new Cart();
        }
        cart.addItem(item);
        session.setAttribute("cart", cart);
        return "Cart: " + cart.getItems();
    }
}
```

**How to run:** with the default Redis session configuration (which, depending on Spring Session version, may default to Java serialization for arbitrary attribute values), add items via `GET /cart/add?item=book`. Inspect the raw stored value with `redis-cli --no-raw HGETALL "spring:session:sessions:<id>"`. Expected observation: the `cart` attribute's stored value is unreadable binary data — Java's native serialization format, opaque to direct human inspection.

### Level 2 — Intermediate

Switching to JSON serialization makes the same data directly human-readable in Redis — useful for debugging, and avoids the `Serializable` requirement and Java-serialization-specific version brittleness for these particular objects.

```java
// JsonSessionSerializationConfig.java
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.session.data.redis.config.ConfigureRedisAction;
import org.springframework.session.data.redis.config.annotation.web.http.EnableRedisHttpSession;

@Configuration
@EnableRedisHttpSession
public class JsonSessionSerializationConfig {

    @Bean
    public GenericJackson2JsonRedisSerializer springSessionDefaultRedisSerializer() {
        // Spring Session looks up a bean with exactly this name to use for
        // serializing session attribute values, if present.
        return new GenericJackson2JsonRedisSerializer(new ObjectMapper());
    }
}
```

```java
// Cart no longer needs to implement Serializable for JSON-based serialization —
// Jackson works from the object's fields/getters directly, not Java's serialization mechanism.
public class Cart {
    private java.util.List<String> items = new java.util.ArrayList<>();
    public void addItem(String item) { items.add(item); }
    public java.util.List<String> getItems() { return items; }
}
```

**How to run:** add this configuration, restart, repeat the `/cart/add` sequence, then inspect Redis again. Expected observation: the stored `cart` attribute value is now readable JSON text (including a `@class` type hint Jackson embeds by default for polymorphic deserialization) — directly inspectable and understandable without deserializing it in application code first, a genuine debugging and operability improvement.

What changed: session data went from opaque binary to human-readable JSON purely through configuration, with no change to how application code reads or writes the `cart` attribute — the serialization strategy is entirely orthogonal to the application-facing session API.

### Level 3 — Advanced

Adding a field to `Cart` after sessions already exist in the store is a real, common scenario during ongoing development — Java serialization handles this poorly by default (a `serialVersionUID` mismatch, or missing-field issues depending on exact changes), while JSON serialization via Jackson handles it gracefully by default (new fields simply get their default value on deserialization of old data).

```java
// Cart.java — evolved, with a new field added after sessions already exist in production
public class Cart {
    private java.util.List<String> items = new java.util.ArrayList<>();
    private String promoCode; // NEW field, added after some sessions already exist without it

    public void addItem(String item) { items.add(item); }
    public java.util.List<String> getItems() { return items; }
    public String getPromoCode() { return promoCode; }
    public void setPromoCode(String promoCode) { this.promoCode = promoCode; }
}
```

```java
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;

public class SafeJsonSerializerConfig {

    public ObjectMapper resilientObjectMapper() {
        ObjectMapper mapper = new ObjectMapper();
        // Explicit, even though it's Jackson's default: old JSON missing this new field
        // deserializes successfully, with promoCode simply left null, rather than failing outright.
        mapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
        return mapper;
    }
}
```

**How to run:** create a session with the *old* `Cart` class (no `promoCode` field), deploy the *new* class with the added field, then make a request touching that pre-existing session. Under JSON serialization: expect the old session to deserialize successfully, with `getPromoCode()` simply returning `null` for that pre-existing cart. Repeat the same scenario under plain Java serialization (Level 1's approach) instead: expect this to be noticeably more fragile — depending on exactly how `serialVersionUID` is managed, this can throw `InvalidClassException` outright, effectively corrupting every pre-existing session holding the old class shape.

What changed and why it's production-flavored: this is the exact real-world scenario ("we shipped a new field, now what happens to sessions created before the deploy") that makes the serialization strategy choice matter far beyond initial setup — JSON's graceful handling of additive schema changes is a genuine operational advantage for any application under active development where session-stored classes will inevitably evolve over time.

## 6. Walkthrough

Tracing a session read spanning a class-schema evolution, in execution order:

1. Before a deployment, a user's session was saved with a `cart` attribute serialized (via JSON, per Level 2) from the *old* `Cart` class shape — `{"items": ["book"], "@class": "com.example.Cart"}`, with no `promoCode` field, since it didn't exist yet.
2. A new version of the application deploys, including the evolved `Cart` class with the added `promoCode` field — but the user's existing session in Redis is untouched by the deployment; it still holds the old JSON exactly as it was written.
3. The user makes a request; `SessionRepositoryFilter` (card 0004) resolves their session, and reading the `cart` attribute triggers deserialization — Jackson (configured per Level 3, though this is its default behavior) attempts to construct a `Cart` object from the stored JSON.
4. Since the stored JSON simply has no `promoCode` field, Jackson leaves that field at its default value (`null`, for an object reference) on the reconstructed `Cart` instance, rather than failing the deserialization outright — the object is successfully rebuilt, just missing data that genuinely never existed for this particular pre-existing session.
5. Application code calling `cart.getPromoCode()` on this reconstructed object correctly receives `null`, and — assuming the application handles a `null` promo code sensibly elsewhere, which is a normal, expected state regardless of session serialization concerns — the request proceeds without error.
6. Contrast this with Java-native serialization's typically stricter behavior around class shape changes — depending on `serialVersionUID` management, the equivalent old-session read could throw an exception during deserialization, potentially breaking every request that happens to touch a session created before the class change, until those specific sessions eventually expire and are replaced by freshly created ones under the new class shape.

```
Before deploy: session saved with OLD Cart JSON {"items": [...]}  (no promoCode field)
   |
Deploy: NEW Cart class adds promoCode field
   |
User's next request: read cart attribute -> deserialize stored (OLD-shape) JSON
   |
JSON: promoCode field missing -> Jackson leaves it null on the NEW Cart object -> succeeds
   |
(vs. Java serialization: potentially throws InvalidClassException on the same scenario)
```

## 7. Gotchas & takeaways

> Java's native serialization is fragile across class-shape changes in a way that directly affects session data continuity across deployments — a class change that would be entirely harmless in a single-instance, restart-loses-everything world (card 0001's original problem) becomes a real, user-visible failure mode once sessions are expected to survive a deployment, since old, still-valid sessions may hold data serialized under the pre-change class shape.

- Prefer JSON-based serialization (Level 2, via `GenericJackson2JsonRedisSerializer` or equivalent) for new applications specifically because of its more graceful handling of additive class changes (Level 3) — this matters more, not less, the longer an application is expected to be actively developed and deployed while real user sessions remain live.
- Human-readable JSON in the store is also a genuine operational advantage independent of the schema-evolution question — being able to `redis-cli HGETALL` a session and actually read what's in it, without writing custom deserialization tooling, meaningfully speeds up debugging production issues.
- Not every object belongs directly in the session — anything inherently non-serializable (a live network connection, certain framework-internal objects) should be stored as an identifier or key instead, with the actual object re-resolved fresh on each request that needs it, rather than attempting to force it through serialization at all.
- `serialVersionUID` explicitly declared on any `Serializable` class used in sessions (Level 1) is a minimum hygiene practice if Java serialization is used at all — omitting it lets the JVM compute one automatically based on the class's exact structure, meaning *any* structural change (even one that wouldn't otherwise be breaking) silently changes the computed UID and breaks deserialization of prior instances.
- When debugging a deserialization failure in production after a deployment, check first whether it correlates with a recent change to a class stored in the session — this is one of the most common and most avoidable classes of post-deployment incident in applications using external session storage, and choosing JSON serialization upfront (Level 2-3) substantially reduces its likelihood.
