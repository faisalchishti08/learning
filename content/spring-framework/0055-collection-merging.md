---
card: spring-framework
gi: 55
slug: collection-merging
title: Collection merging
---

## 1. What it is

**Collection merging** lets a child bean definition *inherit and extend* a collection defined on a parent bean definition. Adding `merge="true"` on a child's `<list>`, `<set>`, `<map>`, or `<props>` element tells Spring to start from the parent's collection and append/overlay the child's entries — instead of replacing the parent's collection entirely.

```xml
<!-- Parent bean: base email domains -->
<bean id="baseNotifier" class="Notifier" abstract="true">
    <property name="allowedDomains">
        <list>
            <value>example.com</value>
            <value>internal.net</value>
        </list>
    </property>
</bean>

<!-- Child bean: inherits parent + adds its own domains -->
<bean id="partnerNotifier" class="Notifier" parent="baseNotifier">
    <property name="allowedDomains">
        <list merge="true">           <!-- merge=true: parent list + child list -->
            <value>partner.io</value>
            <value>vendor.com</value>
        </list>
    </property>
    <!-- allowedDomains will be: [example.com, internal.net, partner.io, vendor.com] -->
</bean>
```

Without `merge="true"`, the child's list would replace the parent's list entirely.

In one sentence: **Collection merging (`merge="true"`) lets a child bean extend its parent's collection — the resulting collection contains the parent's entries first, followed by the child's additions.**

## 2. Why & when

Use collection merging when:

- A **base configuration** defines common values (default plugins, base CORS origins, standard validators).
- **Environment-specific or specialised** child beans need to add entries without duplicating the base set.
- A **multi-tenant** setup shares base rules across tenants but each tenant adds tenant-specific entries.
- You want a clear **parent-child config hierarchy** — base.xml defines defaults, app.xml extends them.

Without merging you'd have to duplicate the full parent list in every child, violating DRY and making base-list updates fragile.

## 3. Core concept

```
Without merge="true":   child list REPLACES parent list
  parent: [A, B]
  child:  [C, D]
  result: [C, D]          ← parent lost

With merge="true":       child list EXTENDS parent list
  parent: [A, B]
  child:  [C, D]
  result: [A, B, C, D]   ← parent preserved, child appended

For Map / Properties: child entries OVERLAY parent entries:
  parent: {timeout:5000, retries:3}
  child:  {retries:5, debug:true}   merge=true
  result: {timeout:5000, retries:5, debug:true}
  ↑ child value wins on key collision; parent-only keys are kept

For Set (merge=true):
  parent: {alpha, beta}
  child:  {beta, gamma}
  result: {alpha, beta, gamma}  ← union, duplicates removed
```

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Collection merging: parent list entries come first, child entries appended">
  <defs>
    <marker id="a55" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <!-- Background -->
  <rect x="5" y="5" width="650" height="210" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="330" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Collection Merging — parent entries first, child entries appended</text>

  <!-- Parent list -->
  <rect x="20" y="35" width="180" height="110" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="110" y="53" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Parent bean list</text>
  <rect x="30" y="62" width="160" height="22" rx="3" fill="#0d1117"/>
  <text x="110" y="77" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">[0] example.com</text>
  <rect x="30" y="88" width="160" height="22" rx="3" fill="#0d1117"/>
  <text x="110" y="103" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">[1] internal.net</text>
  <text x="110" y="135" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">2 entries (base config)</text>

  <!-- Child list -->
  <rect x="230" y="35" width="180" height="110" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="53" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Child bean list  merge="true"</text>
  <rect x="240" y="62" width="160" height="22" rx="3" fill="#0d1117"/>
  <text x="320" y="77" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">[+] partner.io</text>
  <rect x="240" y="88" width="160" height="22" rx="3" fill="#0d1117"/>
  <text x="320" y="103" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">[+] vendor.com</text>
  <text x="320" y="135" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">2 entries (additions)</text>

  <!-- Arrows -->
  <line x1="200" y1="90" x2="440" y2="140" stroke="#6db33f" stroke-width="1.3" marker-end="url(#a55)"/>
  <line x1="410" y1="90" x2="450" y2="140" stroke="#6db33f" stroke-width="1.3" marker-end="url(#a55)"/>

  <!-- Merged result -->
  <rect x="440" y="35" width="200" height="145" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="540" y="53" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Merged result</text>
  <rect x="450" y="60" width="180" height="20" rx="2" fill="#0d1117" stroke="#8b949e" stroke-width="0.8"/>
  <text x="540" y="74" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">[0] example.com  ← from parent</text>
  <rect x="450" y="84" width="180" height="20" rx="2" fill="#0d1117" stroke="#8b949e" stroke-width="0.8"/>
  <text x="540" y="98" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">[1] internal.net  ← from parent</text>
  <rect x="450" y="108" width="180" height="20" rx="2" fill="#0d1117" stroke="#6db33f" stroke-width="0.8"/>
  <text x="540" y="122" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">[2] partner.io    ← from child</text>
  <rect x="450" y="132" width="180" height="20" rx="2" fill="#0d1117" stroke="#6db33f" stroke-width="0.8"/>
  <text x="540" y="146" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">[3] vendor.com    ← from child</text>
  <text x="540" y="170" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">4 entries total</text>

  <text x="330" y="200" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Without merge="true", merged result would contain only [partner.io, vendor.com].</text>
</svg>

Parent entries come first; child entries follow. For `Map`/`Properties`, parent keys are kept and child values win on collision.

## 5. Runnable example

Scenario: a `SecurityPolicy` bean with base allowed-paths (List), base roles (Set), base rate-limits (Map), and base headers (Properties). A child `AdminPolicy` extends each collection.

### Level 1 — Basic

Simple list merge: base policy has two allowed paths, admin policy adds more.

```java
// CollectionMergeDemo.java — run with: java CollectionMergeDemo.java
import java.util.*;

public class CollectionMergeDemo {

    static class SecurityPolicy {
        final List<String> allowedPaths;

        SecurityPolicy(List<String> allowedPaths) {
            this.allowedPaths = allowedPaths;
            System.out.println("[BEAN] SecurityPolicy: allowedPaths=" + allowedPaths);
        }

        boolean isAllowed(String path) {
            return allowedPaths.stream().anyMatch(path::startsWith);
        }
    }

    // ── simulate merge="true": build merged list from parent + child ───
    static SecurityPolicy buildBase() {
        List<String> basePaths = new ArrayList<>(List.of("/health", "/public"));
        return new SecurityPolicy(basePaths);
    }

    static SecurityPolicy buildAdmin() {
        // parent list + child additions (merge="true" behaviour)
        List<String> parentPaths = List.of("/health", "/public");
        List<String> childPaths  = List.of("/admin", "/metrics", "/actuator");
        List<String> merged = new ArrayList<>(parentPaths);
        merged.addAll(childPaths);
        return new SecurityPolicy(Collections.unmodifiableList(merged));
    }

    public static void main(String[] args) {
        System.out.println("=== Base policy ===");
        SecurityPolicy base = buildBase();
        System.out.println("  /health   allowed: " + base.isAllowed("/health"));
        System.out.println("  /admin    allowed: " + base.isAllowed("/admin"));

        System.out.println("\n=== Admin policy (merged) ===");
        SecurityPolicy admin = buildAdmin();
        System.out.println("  /health   allowed: " + admin.isAllowed("/health"));   // from parent
        System.out.println("  /admin    allowed: " + admin.isAllowed("/admin"));    // from child
        System.out.println("  /metrics  allowed: " + admin.isAllowed("/metrics")); // from child
    }
}
```

How to run: `java CollectionMergeDemo.java`

`buildAdmin()` simulates `merge="true"`: it starts with the parent list `["/health", "/public"]` and appends `["/admin", "/metrics", "/actuator"]`. The base policy has only 2 paths; the admin policy has 5. The base entries appear first.

### Level 2 — Intermediate

Merge all four collection types: List, Set, Map, Properties — each with the parent-first merge rule.

```java
// CollectionMergeDemo2.java — run with: java CollectionMergeDemo2.java
import java.util.*;

public class CollectionMergeDemo2 {

    static class AppConfig {
        final List<String>         plugins;      // ordered: base first, then extras
        final Set<String>          features;     // union of base and override sets
        final Map<String, Integer> limits;       // parent keys kept, child wins on collision
        final Properties           headers;      // same override semantics as Map

        AppConfig(List<String> plugins, Set<String> features,
                  Map<String, Integer> limits, Properties headers) {
            this.plugins  = plugins;
            this.features = features;
            this.limits   = limits;
            this.headers  = headers;
        }

        void print(String label) {
            System.out.println("[" + label + "]");
            System.out.println("  plugins="  + plugins);
            System.out.println("  features=" + features);
            System.out.println("  limits="   + limits);
            System.out.println("  headers="  + headers);
        }
    }

    // ── parent definition ─────────────────────────────────────────────
    static AppConfig buildParent() {
        return new AppConfig(
            new ArrayList<>(List.of("core-plugin", "audit-plugin")),
            new LinkedHashSet<>(List.of("BASIC_AUTH", "LOGGING")),
            new LinkedHashMap<>(Map.of("requestsPerMin", 100, "maxPayloadKb", 64)),
            propsOf("X-Frame-Options", "DENY", "X-Content-Type", "nosniff")
        );
    }

    // ── child definition: merge each collection ────────────────────────
    static AppConfig buildChild() {
        AppConfig parent = buildParent();

        // List merge: parent first, child appended
        List<String> mergedPlugins = new ArrayList<>(parent.plugins);
        mergedPlugins.addAll(List.of("analytics-plugin", "billing-plugin"));

        // Set merge: union
        Set<String> mergedFeatures = new LinkedHashSet<>(parent.features);
        mergedFeatures.addAll(List.of("RATE_LIMITING", "2FA", "LOGGING")); // LOGGING duplicate removed

        // Map merge: parent keys kept, child values override on collision
        Map<String, Integer> mergedLimits = new LinkedHashMap<>(parent.limits);
        mergedLimits.put("requestsPerMin", 500);   // override parent value
        mergedLimits.put("burstCapacity",  1000);  // new key

        // Properties merge: same as Map
        Properties mergedHeaders = new Properties(parent.headers);
        mergedHeaders.setProperty("X-Frame-Options", "SAMEORIGIN");  // override
        mergedHeaders.setProperty("Content-Security-Policy", "default-src 'self'"); // new

        return new AppConfig(mergedPlugins, mergedFeatures, mergedLimits, mergedHeaders);
    }

    static Properties propsOf(String... kv) {
        Properties p = new Properties();
        for (int i = 0; i < kv.length; i += 2) p.setProperty(kv[i], kv[i+1]);
        return p;
    }

    public static void main(String[] args) {
        System.out.println("=== Parent (base) config ===");
        buildParent().print("PARENT");

        System.out.println("\n=== Child (merged) config ===");
        buildChild().print("CHILD-MERGED");

        System.out.println("\n--- Merge analysis ---");
        AppConfig p = buildParent(), c = buildChild();
        System.out.println("  plugins:  parent=" + p.plugins.size() + " child=" + c.plugins.size()
            + " → child entries=" + c.plugins.subList(p.plugins.size(), c.plugins.size()));
        System.out.println("  features: parent=" + p.features.size() + " child=" + c.features.size()
            + " (LOGGING duplicate removed)");
        System.out.println("  limits:   requestsPerMin overridden: "
            + p.limits.get("requestsPerMin") + " → " + c.limits.get("requestsPerMin"));
    }
}
```

How to run: `java CollectionMergeDemo2.java`

Four collection types merged simultaneously: List appends child entries; Set takes the union (duplicate `LOGGING` appears once); Map keeps parent `maxPayloadKb=64` and overrides `requestsPerMin` from 100 → 500; Properties overrides `X-Frame-Options` and adds `Content-Security-Policy`. Parent-only keys are always preserved.

### Level 3 — Advanced

A three-level hierarchy (grandparent → parent → child) demonstrating cumulative collection merging across multiple inheritance levels.

```java
// CollectionMergeDemo3.java — run with: java CollectionMergeDemo3.java
import java.util.*;
import java.util.stream.Collectors;

public class CollectionMergeDemo3 {

    record PolicyDef(List<String> rules, Map<String, Integer> thresholds, Set<String> flags) {}

    // ── simulate three-level XML bean hierarchy ────────────────────────
    static PolicyDef grandparent() {
        return new PolicyDef(
            new ArrayList<>(List.of("block-sql-injection", "block-xss")),
            new LinkedHashMap<>(Map.of("maxRetries", 3, "sessionTimeoutSec", 1800)),
            new LinkedHashSet<>(List.of("AUDIT_LOG"))
        );
    }

    static PolicyDef parent(PolicyDef gp) {
        // merge from grandparent
        List<String>         rules      = new ArrayList<>(gp.rules());
        Map<String, Integer> thresholds = new LinkedHashMap<>(gp.thresholds());
        Set<String>          flags      = new LinkedHashSet<>(gp.flags());

        rules.addAll(List.of("rate-limit-ips", "block-tor-exit-nodes"));
        thresholds.put("maxRetries",          5);       // override gp
        thresholds.put("rateLimitPerMin",     200);     // new
        flags.addAll(List.of("TWO_FACTOR", "AUDIT_LOG")); // AUDIT_LOG deduped

        return new PolicyDef(rules, thresholds, flags);
    }

    static PolicyDef child(PolicyDef p) {
        // merge from parent (which already merged grandparent)
        List<String>         rules      = new ArrayList<>(p.rules());
        Map<String, Integer> thresholds = new LinkedHashMap<>(p.thresholds());
        Set<String>          flags      = new LinkedHashSet<>(p.flags());

        rules.addAll(List.of("require-mfa-for-admin", "block-non-eu-ips"));
        thresholds.put("rateLimitPerMin",  50);    // more restrictive for this tenant
        thresholds.put("maxPayloadKb",     128);   // new
        flags.addAll(List.of("GDPR_MODE", "TWO_FACTOR")); // TWO_FACTOR deduped

        return new PolicyDef(rules, thresholds, flags);
    }

    static void printPolicy(String label, PolicyDef pd) {
        System.out.println("[" + label + "]");
        System.out.println("  rules="      + pd.rules());
        System.out.println("  thresholds=" + pd.thresholds());
        System.out.println("  flags="      + pd.flags());
    }

    static void diff(String a, PolicyDef pa, String b, PolicyDef pb) {
        System.out.println("--- diff " + a + " → " + b + " ---");
        List<String> addedRules = new ArrayList<>(pb.rules());
        addedRules.removeAll(pa.rules());
        System.out.println("  added rules: " + addedRules);

        Map<String,Integer> overrides = new LinkedHashMap<>();
        pb.thresholds().forEach((k,v) -> {
            if (!pa.thresholds().containsKey(k)) overrides.put(k + " (new)", v);
            else if (!pa.thresholds().get(k).equals(v))
                overrides.put(k + " (" + pa.thresholds().get(k) + "→" + v + ")", v);
        });
        System.out.println("  threshold changes: " + overrides);
        Set<String> addedFlags = new LinkedHashSet<>(pb.flags());
        addedFlags.removeAll(pa.flags());
        System.out.println("  added flags: " + addedFlags);
    }

    public static void main(String[] args) {
        PolicyDef gp = grandparent();
        PolicyDef par = parent(gp);
        PolicyDef ch  = child(par);

        printPolicy("GRANDPARENT", gp);
        System.out.println();
        printPolicy("PARENT (merged from grandparent)", par);
        System.out.println();
        printPolicy("CHILD  (merged from parent+grandparent)", ch);
        System.out.println();
        diff("grandparent", gp, "parent", par);
        System.out.println();
        diff("parent", par, "child", ch);
    }
}
```

How to run: `java CollectionMergeDemo3.java`

Three levels: grandparent defines base security rules; parent extends with rate-limiting; child extends with tenant-specific constraints. At each level the collection grows cumulatively — the child's final `rules` list contains all 6 rules from all three levels. `maxRetries` is overridden at the parent level (3→5) and the child inherits `5`. `rateLimitPerMin` is introduced at the parent (200) and tightened at the child (50). The diff output shows exactly what each level adds.

## 6. Walkthrough

**Three-level merge of `thresholds` Map:**

```
Grandparent:
  {maxRetries: 3, sessionTimeoutSec: 1800}

Parent merges grandparent:
  start with copy: {maxRetries:3, sessionTimeoutSec:1800}
  put("maxRetries", 5)        → override: {maxRetries:5, sessionTimeoutSec:1800}
  put("rateLimitPerMin", 200) → new key:  {maxRetries:5, sessionTimeoutSec:1800, rateLimitPerMin:200}

Child merges parent:
  start with copy: {maxRetries:5, sessionTimeoutSec:1800, rateLimitPerMin:200}
  put("rateLimitPerMin", 50)  → override: {maxRetries:5, sessionTimeoutSec:1800, rateLimitPerMin:50}
  put("maxPayloadKb", 128)    → new key:  {maxRetries:5, sessionTimeoutSec:1800, rateLimitPerMin:50, maxPayloadKb:128}

Final child thresholds: {maxRetries:5, sessionTimeoutSec:1800, rateLimitPerMin:50, maxPayloadKb:128}
  Parent-only key "sessionTimeoutSec" preserved through both merges.
  Child wins on "rateLimitPerMin" collision (50 beats parent's 200).
```

**Rules List — cumulative append:**

```
Grandparent: [block-sql-injection, block-xss]                         (2 rules)
Parent:      [block-sql-injection, block-xss, rate-limit-ips,
              block-tor-exit-nodes]                                    (4 rules)
Child:       [block-sql-injection, block-xss, rate-limit-ips,
              block-tor-exit-nodes, require-mfa-for-admin,
              block-non-eu-ips]                                        (6 rules)
```

**Flags Set — union with deduplication:**

```
Grandparent: {AUDIT_LOG}
Parent:      {AUDIT_LOG, TWO_FACTOR}      (AUDIT_LOG already present → 1 copy)
Child:       {AUDIT_LOG, TWO_FACTOR, GDPR_MODE}  (TWO_FACTOR already present → 1 copy)
```

## 7. Gotchas & takeaways

> **`merge="true"` is only valid on a child bean definition.** If you put it on a top-level non-child bean, Spring silently ignores it (no error). You must have `parent="parentBeanId"` on the bean for merging to apply.

> **Map and Properties child values WIN on key collision.** The parent value is replaced — not kept alongside the child value. If you need both, use different keys or a `List<Entry>`.

- Merging only works in XML bean definitions. There is no annotation-driven equivalent of `merge="true"`. In Java config (`@Configuration`), achieve the same by calling a `baseList()` method and appending to it.
- `<list>` merge always appends child entries after parent entries — you cannot insert in the middle or change order of parent entries.
- `<set>` merge deduplicates — if the same value appears in both parent and child, it appears only once in the merged set.
- Parent collections that are `null` are treated as empty — the child's entries are the full result.
