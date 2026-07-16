---
card: spring-integration
gi: 69
slug: resource-inbound-adapter
title: "Resource inbound adapter"
---

## 1. What it is

The resource inbound channel adapter (`Resources.inboundAdapter(...)`, backed by Spring's `Resource` abstraction and a `ResourcePatternResolver`) polls a location expressed as a Spring `Resource` pattern — classpath, filesystem, or URL — and emits a message for each resource it finds. Unlike the file adapter (card 0050), which is specifically tied to filesystem paths, this adapter works over any location Spring's generic `Resource` abstraction can address, including classpath-packaged resources bundled inside a JAR.

## 2. Why & when

You reach for the resource inbound adapter when the input isn't necessarily a plain filesystem file, or when the same flow needs to work uniformly whether its input comes from disk, the classpath, or a URL:

- **Configuration or reference data ships inside the application's own JAR** — a set of classpath-packaged templates, schemas, or lookup files that need to be picked up as messages using the exact same flow logic regardless of where the deployment ultimately puts them.
- **The location pattern needs Ant-style wildcards across resource types** — `classpath*:rules/*.xml` finds matching files across every JAR on the classpath, not just one filesystem directory, which the file adapter alone cannot express.
- **A flow should be portable between "read from disk" and "read from classpath" with no code change** — swapping a location string between `file:/opt/app/data/*.csv` and `classpath:data/*.csv` is enough to redirect the same flow to a different resource type entirely.

## 3. Core concept

Think of the file adapter as a mail carrier who only knows how to check a specific physical mailbox on a specific street. The resource inbound adapter is more like a general dispatcher who can be told "check whichever mailbox this address pattern resolves to" — and that address might be a street (filesystem path), a shelf inside a warehouse the carrier already has a key to (classpath, even inside a packaged JAR), or a delivery slot at a remote depot (a URL) — the dispatcher doesn't need separate logic for each kind of location.

```java
@Bean
public IntegrationFlow resourcePollingFlow() {
    return IntegrationFlow.from(
            Resources.inboundAdapter().patternResolver(new PathMatchingResourcePatternResolver())
                .pattern("classpath*:rules/*.xml"),
            e -> e.poller(Pollers.fixedDelay(30_000)))
        .handle((org.springframework.core.io.Resource res, headers) -> ruleLoader.load(res))
        .get();
}
```

The `classpath*:` prefix searches every JAR and classpath directory for matching files, something a plain filesystem-only adapter has no equivalent for.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A resource inbound adapter resolves one location pattern uniformly across filesystem, classpath, and URL resource types, unlike the file adapter which is filesystem-only" >
  <rect x="20" y="20" width="280" height="110" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="160" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">File adapter (card 0050)</text>
  <text x="35" y="45" fill="#e6edf3" font-size="8" font-family="monospace">/opt/app/data/*.csv</text>
  <text x="35" y="70" fill="#8b949e" font-size="7" font-family="sans-serif">filesystem paths only</text>

  <rect x="340" y="20" width="280" height="110" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Resource inbound adapter</text>
  <text x="355" y="42" fill="#e6edf3" font-size="8" font-family="monospace">file:/opt/app/data/*.csv</text>
  <text x="355" y="62" fill="#79c0ff" font-size="8" font-family="monospace">classpath*:rules/*.xml</text>
  <text x="355" y="82" fill="#79c0ff" font-size="8" font-family="monospace">https://config-server/*.yml</text>
  <text x="355" y="105" fill="#8b949e" font-size="7" font-family="sans-serif">one adapter, any Resource type</text>
</svg>

Same polling adapter, any location a Spring `Resource` pattern can express — disk, classpath, or URL.

## 5. Runnable example

The scenario: loading rule-definition resources by pattern regardless of where they physically live, simulated with an in-memory list of resource identifiers standing in for classpath/filesystem/URL resources (no real classpath scanning needed to demonstrate the pattern-matching and loading logic), starting with a basic pattern match, then adding per-resource error isolation, then adding change detection to avoid reloading unchanged resources.

### Level 1 — Basic

```java
// ResourcePollingDemo.java
import java.util.*;

public class ResourcePollingDemo {
    // Stand-in for Resource objects a PathMatchingResourcePatternResolver would return.
    record FakeResource(String location, String content) {}

    static List<FakeResource> resolvePattern(List<FakeResource> universe, String suffix) {
        return universe.stream().filter(r -> r.location().endsWith(suffix)).toList();
    }

    public static void main(String[] args) {
        List<FakeResource> universe = List.of(
            new FakeResource("classpath:rules/discount.xml", "<rule>DISCOUNT_10</rule>"),
            new FakeResource("classpath:rules/shipping.xml", "<rule>FREE_SHIP_OVER_50</rule>"),
            new FakeResource("classpath:templates/email.html", "<html>...</html>"));

        for (FakeResource r : resolvePattern(universe, ".xml")) {
            System.out.println("Loading rule resource: " + r.location());
        }
    }
}
```

How to run: `java ResourcePollingDemo.java`. Expected output: the two `rules/*.xml` resources print as loaded, while `templates/email.html` is correctly excluded by the pattern match.

### Level 2 — Intermediate

```java
// ResourcePollingDemo.java
import java.util.*;

public class ResourcePollingDemo {
    record FakeResource(String location, String content) {}

    static List<FakeResource> resolvePattern(List<FakeResource> universe, String suffix) {
        return universe.stream().filter(r -> r.location().endsWith(suffix)).toList();
    }

    // Real-world concern: one malformed resource shouldn't stop the whole batch from loading --
    // isolate each resource's parsing so a bad file doesn't take down every other rule with it.
    static void loadRule(FakeResource r) {
        if (r.content().contains("MALFORMED")) throw new IllegalArgumentException("bad rule XML");
        System.out.println("Loaded rule from " + r.location() + ": " + r.content());
    }

    public static void main(String[] args) {
        List<FakeResource> universe = List.of(
            new FakeResource("classpath:rules/discount.xml", "<rule>DISCOUNT_10</rule>"),
            new FakeResource("classpath:rules/broken.xml", "<rule>MALFORMED"),
            new FakeResource("classpath:rules/shipping.xml", "<rule>FREE_SHIP_OVER_50</rule>"));

        for (FakeResource r : resolvePattern(universe, ".xml")) {
            try {
                loadRule(r);
            } catch (IllegalArgumentException ex) {
                System.out.println("Skipping " + r.location() + ": " + ex.getMessage());
            }
        }
    }
}
```

How to run: `java ResourcePollingDemo.java`. Expected output: `discount.xml` loads, `broken.xml` is skipped with an error message, and `shipping.xml` still loads afterward — one bad resource doesn't abort processing of the rest of the batch.

### Level 3 — Advanced

```java
// ResourcePollingDemo.java
import java.util.*;

public class ResourcePollingDemo {
    record FakeResource(String location, String content, long lastModified) {}

    static List<FakeResource> resolvePattern(List<FakeResource> universe, String suffix) {
        return universe.stream().filter(r -> r.location().endsWith(suffix)).toList();
    }

    static void loadRule(FakeResource r) {
        if (r.content().contains("MALFORMED")) throw new IllegalArgumentException("bad rule XML");
        System.out.println("Loaded rule from " + r.location() + ": " + r.content());
    }

    // Production concern: repeated polls re-scan the same pattern -- reloading every unchanged
    // resource on every poll wastes work. Track last-modified per resource and skip the unchanged.
    static class ChangeAwareLoader {
        private final Map<String, Long> lastSeenModified = new HashMap<>();

        void pollAndLoad(List<FakeResource> universe, String suffix) {
            for (FakeResource r : resolvePattern(universe, suffix)) {
                Long seen = lastSeenModified.get(r.location());
                if (seen != null && seen == r.lastModified()) {
                    System.out.println("Unchanged, skipping: " + r.location());
                    continue;
                }
                try {
                    loadRule(r);
                    lastSeenModified.put(r.location(), r.lastModified());
                } catch (IllegalArgumentException ex) {
                    System.out.println("Skipping " + r.location() + ": " + ex.getMessage());
                }
            }
        }
    }

    public static void main(String[] args) {
        List<FakeResource> universe = new ArrayList<>(List.of(
            new FakeResource("classpath:rules/discount.xml", "<rule>DISCOUNT_10</rule>", 100)));

        ChangeAwareLoader loader = new ChangeAwareLoader();
        System.out.println("-- poll 1 --");
        loader.pollAndLoad(universe, ".xml");
        System.out.println("-- poll 2 (unchanged) --");
        loader.pollAndLoad(universe, ".xml");

        universe.set(0, new FakeResource("classpath:rules/discount.xml", "<rule>DISCOUNT_15</rule>", 200));
        System.out.println("-- poll 3 (updated) --");
        loader.pollAndLoad(universe, ".xml");
    }
}
```

How to run: `java ResourcePollingDemo.java`. Expected output: poll 1 loads the resource; poll 2 prints `Unchanged, skipping: ...` since nothing changed; poll 3, after the resource's content and timestamp are updated, reloads it with the new content — the change-detection guard that keeps a repeatedly-polling resource adapter from redoing unnecessary work every cycle.

## 6. Walkthrough

Trace one poll cycle from pattern resolution to loaded rule.

1. **Poller fires**: `Resources.inboundAdapter`'s poller invokes the configured `ResourcePatternResolver` with the location pattern — `classpath*:rules/*.xml` in the example.
2. **Pattern resolution**: the resolver scans every location the pattern could refer to (every JAR and directory on the classpath, for a `classpath*:` prefix) and returns a `Resource[]` of everything matching.
3. **Message emission**: the adapter emits one message per matched `Resource`, carrying the resource itself (or its content, depending on configuration) as the payload.
4. **Downstream handling**: a `.handle(...)` step, like `ruleLoader.load(res)`, reads the resource's content and parses it — isolating any parse failure per-resource so one malformed file doesn't abort the whole poll, as in Level 2.
5. **Change tracking (optional)**: a well-behaved flow layers in its own change detection, since the adapter itself re-resolves the full pattern on every poll — comparing a resource's last-modified timestamp (or a content hash) against what was seen on the previous poll avoids redundant reprocessing, as in Level 3.
6. **Result**: whatever the loaded resource represents — a rule, a template, a schema — becomes available to the rest of the application, updated automatically the next time its underlying resource changes, without needing an application restart to pick up the change.

```
poller tick
  -> ResourcePatternResolver.getResources("classpath*:rules/*.xml")
    -> Resource[] matched
      -> Message per Resource
        -> ruleLoader.load(resource)   (isolated per-resource, change-aware)
          success -> rule registered / updated
          failure -> logged and skipped, other resources unaffected
```

## 7. Gotchas & takeaways

> **Gotcha:** `classpath:` (single asterisk-free prefix) only searches the first matching classpath location, while `classpath*:` searches every JAR and directory on the classpath for matches — using the wrong prefix silently misses resources packaged in additional JARs, a common source of "it works on my machine" when a dependency ships its own copy of a matching resource.

- The resource inbound adapter re-resolves the full pattern on every poll; for large classpaths or many matching files, add explicit change tracking (as in Level 3) rather than relying on the adapter alone to avoid redundant work.
- Because it can address URLs as well as classpath and filesystem locations, the same pattern syntax can accidentally reach out over the network if misconfigured — be deliberate about which resource types a given deployment should ever resolve.
- Prefer the file adapter (card 0050) when the input is unambiguously and permanently a plain filesystem directory — its file-specific options (like renaming after processing) don't have exact equivalents in the more generic resource adapter.
- Resources bundled inside a JAR are typically read-only at runtime; a flow expecting to move or delete a processed classpath resource (the way a file adapter might rename a processed file) needs a different strategy, since packaged resources can't be modified in place.
