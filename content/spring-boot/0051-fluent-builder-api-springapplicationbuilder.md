---
card: spring-boot
gi: 51
slug: fluent-builder-api-springapplicationbuilder
title: Fluent builder API (SpringApplicationBuilder)
---

## 1. What it is

`SpringApplicationBuilder` is a fluent (method-chaining) API that wraps `SpringApplication`, providing the same customisation options as individual setters but in a more concise, readable form. It also uniquely supports building **parent–child `ApplicationContext` hierarchies**.

```java
new SpringApplicationBuilder(MyApp.class)
    .bannerMode(Banner.Mode.OFF)
    .web(WebApplicationType.NONE)
    .lazyInitialization(true)
    .profiles("production")
    .properties("server.port=9090")
    .run(args);
```

For hierarchical contexts (used in Spring Cloud and multi-context deployments):
```java
new SpringApplicationBuilder()
    .sources(ParentConfig.class)
    .child(ChildConfig.class)
    .web(WebApplicationType.SERVLET)
    .run(args);
```

## 2. Why & when

`SpringApplicationBuilder` exists for two reasons:

1. **Ergonomics** — chaining is easier to read than multiple setter calls on a variable.
2. **Hierarchy** — `SpringApplication` has no API for parent–child context hierarchies; the builder does via `.child()` and `.sibling()`.

Use `SpringApplicationBuilder` when:
- You have three or more pre-context customisations (chaining is cleaner than setters).
- You need a parent–child application context (e.g. a shared parent context with common infrastructure beans, and a child context that provides web-layer beans).
- You are building a Spring Cloud application where the bootstrap context is the parent.

For a single customisation or two, plain `SpringApplication` setters are fine.

## 3. Core concept

`SpringApplicationBuilder` is the **builder pattern** applied to `SpringApplication`. Each method call configures one aspect and returns `this` (the builder), allowing the next method to chain. The terminal call `.run(args)` builds and starts the configured `SpringApplication`.

For hierarchical contexts:
- `.child(ChildConfig.class)` returns a **new** `SpringApplicationBuilder` scoped to the child context.
- The parent context is started first; its beans are available to the child.
- Beans from the child are not visible in the parent (downward visibility only, like Java class inheritance).
- This is how Spring Cloud Bootstrap Context works: the bootstrap context loads cloud config values first, then the application context (child) inherits those values via the parent.

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SpringApplicationBuilder fluent chain and optional parent-child context hierarchy">
  <!-- Fluent chain -->
  <rect x="20" y="20" width="400" height="120" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="220" y="44" fill="#6db33f" font-size="12" font-family="monospace" font-weight="bold" text-anchor="middle">SpringApplicationBuilder chain</text>

  <text x="36" y="66" fill="#79c0ff" font-size="11" font-family="monospace">new SpringApplicationBuilder(MyApp.class)</text>
  <text x="36" y="84" fill="#8b949e" font-size="11" font-family="monospace">    .bannerMode(OFF)</text>
  <text x="36" y="100" fill="#8b949e" font-size="11" font-family="monospace">    .web(NONE)</text>
  <text x="36" y="116" fill="#8b949e" font-size="11" font-family="monospace">    .profiles("prod")</text>
  <text x="36" y="132" fill="#6db33f" font-size="11" font-family="monospace">    .run(args);    // terminal call</text>

  <!-- Hierarchy section -->
  <rect x="20" y="160" width="620" height="70" rx="8" fill="#16202e" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="184" fill="#79c0ff" font-size="12" font-family="monospace" text-anchor="middle">Parent–child hierarchy (.child())</text>

  <!-- Parent ctx -->
  <rect x="40" y="196" width="180" height="26" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="214" fill="#6db33f" font-size="10" font-family="monospace" text-anchor="middle">Parent context (ParentConfig)</text>

  <!-- Arrow -->
  <line x1="222" y1="209" x2="258" y2="209" stroke="#79c0ff" stroke-width="2" marker-end="url(#fb)"/>
  <text x="240" y="202" fill="#79c0ff" font-size="9" font-family="sans-serif" text-anchor="middle">.child()</text>

  <!-- Child ctx -->
  <rect x="260" y="196" width="180" height="26" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="350" y="214" fill="#79c0ff" font-size="10" font-family="monospace" text-anchor="middle">Child context (ChildConfig)</text>

  <text x="460" y="214" fill="#8b949e" font-size="10" font-family="sans-serif">sees parent beans ↑</text>

  <defs>
    <marker id="fb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/>
    </marker>
  </defs>
</svg>

The fluent chain ends with `.run(args)`; `.child()` creates a parent–child context hierarchy where the child inherits beans from the parent.

## 5. Runnable example

```java
// SpringApplicationBuilderDemo.java
// How to run: java SpringApplicationBuilderDemo.java  (JDK 17+)
// Simulates SpringApplicationBuilder's fluent API and parent-child context hierarchy.

import java.util.*;

public class SpringApplicationBuilderDemo {

    enum BannerMode { CONSOLE, LOG, OFF }
    enum WebType    { SERVLET, REACTIVE, NONE }

    // ── Simulated builder ─────────────────────────────────────────
    static class SpringApplicationBuilder {
        private final String           source;
        private BannerMode             bannerMode  = BannerMode.CONSOLE;
        private WebType                webType     = WebType.SERVLET;
        private boolean                lazy        = false;
        private final List<String>     profiles    = new ArrayList<>();
        private final Map<String, String> props    = new LinkedHashMap<>();
        private Map<String, Object>    parentCtx   = null;   // simulated parent context beans

        SpringApplicationBuilder(String source) { this.source = source; }

        SpringApplicationBuilder bannerMode(BannerMode m)  { this.bannerMode = m; return this; }
        SpringApplicationBuilder web(WebType t)            { this.webType = t;   return this; }
        SpringApplicationBuilder lazyInitialization(boolean b){ this.lazy = b;   return this; }
        SpringApplicationBuilder profiles(String... p)     { profiles.addAll(Arrays.asList(p)); return this; }
        SpringApplicationBuilder properties(String... kv)  {
            for (String pair : kv) {
                String[] parts = pair.split("=", 2);
                if (parts.length == 2) props.put(parts[0].trim(), parts[1].trim());
            }
            return this;
        }

        // Creates a child builder that inherits parent bean context
        SpringApplicationBuilder child(String childSource) {
            SpringApplicationBuilder childBuilder = new SpringApplicationBuilder(childSource);
            childBuilder.parentCtx = this.run(new String[0]);  // parent is started first
            return childBuilder;
        }

        Map<String, Object> run(String[] args) {
            Map<String, Object> ctx = new LinkedHashMap<>();
            System.out.println("--- Starting context for: " + source + " ---");
            System.out.println("  banner     : " + bannerMode);
            System.out.println("  web        : " + webType);
            System.out.println("  lazy-init  : " + lazy);
            System.out.println("  profiles   : " + profiles);
            System.out.println("  properties : " + props);
            if (parentCtx != null) {
                System.out.println("  parent ctx beans visible: " + parentCtx.keySet());
                ctx.putAll(parentCtx);  // child inherits parent beans
            }
            ctx.put(source + "_bean", source + " registered");
            System.out.println("  own bean   : " + source + "_bean");
            System.out.println();
            return ctx;
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Scenario A: Fluent chain ===\n");
        new SpringApplicationBuilder("MyApp")
            .bannerMode(BannerMode.OFF)
            .web(WebType.NONE)
            .lazyInitialization(true)
            .profiles("production")
            .properties("server.port=9090", "app.name=demo")
            .run(args);

        System.out.println("=== Scenario B: Parent-child hierarchy ===\n");
        Map<String, Object> childCtx = new SpringApplicationBuilder("ParentConfig")
            .bannerMode(BannerMode.OFF)
            .child("ChildConfig")
            .web(WebType.SERVLET)
            .run(args);

        System.out.println("Final child context beans: " + childCtx.keySet());
    }
}
```

**How to run:** `java SpringApplicationBuilderDemo.java`

Expected output:
```
=== Scenario A: Fluent chain ===

--- Starting context for: MyApp ---
  banner     : OFF
  web        : NONE
  lazy-init  : true
  profiles   : [production]
  properties : {server.port=9090, app.name=demo}

=== Scenario B: Parent-child hierarchy ===

--- Starting context for: ParentConfig ---
  banner     : OFF
  web        : SERVLET
  lazy-init  : false
  profiles   : []
  properties : {}

--- Starting context for: ChildConfig ---
  banner     : CONSOLE
  web        : SERVLET
  lazy-init  : false
  profiles   : []
  properties : {}
  parent ctx beans visible: [ParentConfig_bean]
  own bean   : ChildConfig_bean

Final child context beans: [ParentConfig_bean, ChildConfig_bean]
```

## 6. Walkthrough

- Scenario A: each method returns `this`, enabling chaining. `.run(args)` terminates the chain and returns the context.
- The simulated `run()` prints the full configuration so you can see exactly what each method set.
- Scenario B: `.child("ChildConfig")` first calls `.run()` on the parent builder (creating the parent context with `ParentConfig_bean`), then constructs a child builder whose `parentCtx` is set to the parent's beans.
- When the child's `.run()` executes, it copies parent beans into the child context (`ctx.putAll(parentCtx)`), simulating context inheritance. The child can see `ParentConfig_bean`; the parent cannot see `ChildConfig_bean`.
- The final line shows both beans in the child context, confirming upward visibility.

## 7. Gotchas & takeaways

> In a parent–child hierarchy, `@Autowired` in the child context can inject beans from the parent, but `@Autowired` in the parent cannot inject beans from the child. The visibility is **one-way upward only**.

> `SpringApplicationBuilder.child()` creates a brand-new `SpringApplicationBuilder` with default settings. Profile, property, and banner settings from the parent builder are **not** automatically inherited by the child builder — you must set them again if needed.

- `SpringApplicationBuilder` returns `this` for all configuration methods (fluent interface), so you can chain as many as needed.
- The hierarchy feature is used heavily in Spring Cloud: the bootstrap context (which loads remote config) is the parent; the application context is the child.
- `.sibling(ChildConfig.class)` creates a sibling context that shares the same parent as the current builder's context (both are children of the same parent).
- For simple single-context apps with one or two customisations, `SpringApplication` setters are cleaner; use the builder when chaining three or more.
