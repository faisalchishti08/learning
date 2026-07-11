---
card: spring-cloud
gi: 96
slug: function-composition-routing
title: "Function composition & routing"
---

## 1. What it is

Spring Cloud Function lets several small function beans be composed into one pipeline purely by name, using a pipe-separated function definition string (`uppercase|reverse`) instead of writing composition code — and `FunctionRouter`/`spring.cloud.function.definition` can additionally pick which function (or pipeline) to invoke at runtime based on a routing header, letting one deployed application expose many different function pipelines through a single entry point.

```properties
spring.cloud.function.definition=uppercase|reverse
```

```java
@Bean Function<String, String> uppercase() { return String::toUpperCase; }
@Bean Function<String, String> reverse() { return s -> new StringBuilder(s).reverse().toString(); }
```

```bash
curl http://localhost:8080/uppercase|reverse -d "hello"
# -> OLLEH
```

## 2. Why & when

Writing one large function that does everything (uppercase, then reverse, then validate) bundles unrelated concerns into a single unit that's hard to test or reuse in isolation — writing three small functions and composing them in Java code (`uppercase.andThen(reverse)`, as the previous card showed) is better, but still requires a new composed bean, and a new deployment, for every combination an operator might want. Configuration-driven composition solves the remaining problem: any pipe-separated combination of already-deployed function beans can be selected purely through the `spring.cloud.function.definition` property (or a per-request routing header), without writing a single new line of Java for that specific combination — the same jar can serve `uppercase`, `reverse`, or `uppercase|reverse` depending purely on configuration.

Reach for composition and routing when:

- Multiple small, independently useful functions exist, and different callers or deployments need different combinations of them chained together — configuration-driven composition avoids an explosion of hand-written composed beans, one per needed combination.
- One deployed application should serve as a multi-purpose function host, selecting which function (or pipeline) to actually invoke based on a routing header or destination on each individual request/message, rather than being locked to one fixed function per deployment.
- Keeping each function small, focused, and independently testable matters, while still being able to assemble them into larger pipelines for actual use — composition lets the small-function discipline and the need for combined behavior coexist without duplication.

## 3. Core concept

```
 individually deployed function beans:
   uppercase:  Function<String,String>
   reverse:    Function<String,String>
   validate:   Function<String,String>

 spring.cloud.function.definition=uppercase|reverse
   input --> uppercase --> intermediate --> reverse --> output
   (equivalent to uppercase.andThen(reverse), but assembled by CONFIGURATION, not Java code)

 routing header (spring.cloud.function.routing-expression or a request header):
   request A --> definition="uppercase"          --> only uppercase runs
   request B --> definition="uppercase|reverse"   --> both run, in that order
```

The pipe character in the definition string is the composition operator — each stage's output becomes the next stage's input, in left-to-right order, purely from how the string is written.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One input string flows through the uppercase function then the reverse function as configured by the pipe separated function definition producing a single combined output">
  <rect x="20" y="70" width="110" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="75" y="98" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">"hello"</text>

  <rect x="190" y="70" width="120" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="250" y="90" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">uppercase</text>
  <text x="250" y="104" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">-&gt; "HELLO"</text>

  <rect x="370" y="70" width="120" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="430" y="90" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">reverse</text>
  <text x="430" y="104" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">-&gt; "OLLEH"</text>

  <rect x="540" y="70" width="90" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="585" y="98" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">output</text>

  <defs><marker id="a96" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="130" y1="93" x2="190" y2="93" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a96)"/>
  <line x1="310" y1="93" x2="370" y2="93" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a96)"/>
  <line x1="490" y1="93" x2="540" y2="93" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a96)"/>
  <text x="325" y="35" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">definition = "uppercase|reverse"</text>
</svg>

Purely a configuration string — the two function beans themselves never reference each other.

## 5. Runnable example

The scenario: three independent text-processing functions (uppercase, reverse, exclaim), composed in different combinations purely by string-driven configuration. Start with a manual registry and a hardcoded pipe-separated definition, then generalize to routing an arbitrary definition string at call time, then add per-request routing so different requests select different pipelines against the same running registry.

### Level 1 — Basic

A registry of function beans by name, and a hardcoded pipe-separated definition composed manually.

```java
import java.util.*;
import java.util.function.Function;

public class FunctionCompositionLevel1 {
    public static void main(String[] args) {
        Map<String, Function<String, String>> registry = new HashMap<>();
        registry.put("uppercase", String::toUpperCase);
        registry.put("reverse", s -> new StringBuilder(s).reverse().toString());
        registry.put("exclaim", s -> s + "!");

        String definition = "uppercase|reverse"; // mirrors spring.cloud.function.definition
        String[] stages = definition.split("\\|");

        Function<String, String> pipeline = registry.get(stages[0]);
        for (int i = 1; i < stages.length; i++) {
            pipeline = pipeline.andThen(registry.get(stages[i])); // chain each named stage onto the previous
        }

        System.out.println(pipeline.apply("hello"));
    }
}
```

How to run: `java FunctionCompositionLevel1.java`

Splitting `"uppercase|reverse"` on `|` and chaining each named lookup with `andThen` is exactly the mechanism Spring Cloud Function's `FunctionCatalog` uses internally — the pipeline is assembled entirely from the definition string, not from any Java code that names `uppercase` or `reverse` directly.

### Level 2 — Intermediate

Generalize into a reusable `compose(definition)` method that can build any pipeline from any pipe-separated string, not just one hardcoded at the top of `main`.

```java
import java.util.*;
import java.util.function.Function;

public class FunctionCompositionLevel2 {
    static Map<String, Function<String, String>> registry = new HashMap<>();

    static Function<String, String> compose(String definition) {
        String[] stages = definition.split("\\|");
        Function<String, String> pipeline = registry.get(stages[0]);
        if (pipeline == null) throw new IllegalArgumentException("unknown function: " + stages[0]);
        for (int i = 1; i < stages.length; i++) {
            Function<String, String> next = registry.get(stages[i]);
            if (next == null) throw new IllegalArgumentException("unknown function: " + stages[i]);
            pipeline = pipeline.andThen(next);
        }
        return pipeline;
    }

    public static void main(String[] args) {
        registry.put("uppercase", String::toUpperCase);
        registry.put("reverse", s -> new StringBuilder(s).reverse().toString());
        registry.put("exclaim", s -> s + "!");

        // three different definitions, all resolved from the SAME registry, no new Java code per combination
        System.out.println(compose("uppercase").apply("hello"));
        System.out.println(compose("uppercase|reverse").apply("hello"));
        System.out.println(compose("reverse|exclaim").apply("hello"));
    }
}
```

How to run: `java FunctionCompositionLevel2.java`

Three entirely different pipelines are produced from three different definition strings against one shared registry — adding a fourth combination requires only a new string, never a new Java method, which is the practical payoff of configuration-driven composition over hand-written `andThen` chains for every needed combination.

### Level 3 — Advanced

Add request-level routing: incoming "requests" each carry their own routing header selecting which definition to run, against the same running registry, plus handling for an unknown function name in a definition without crashing the whole request loop.

```java
import java.util.*;
import java.util.function.Function;

public class FunctionCompositionLevel3 {
    static Map<String, Function<String, String>> registry = new HashMap<>();

    record Request(String routingHeader, String body) {}

    static Function<String, String> compose(String definition) {
        String[] stages = definition.split("\\|");
        Function<String, String> pipeline = registry.get(stages[0]);
        if (pipeline == null) throw new IllegalArgumentException("unknown function: " + stages[0]);
        for (int i = 1; i < stages.length; i++) {
            Function<String, String> next = registry.get(stages[i]);
            if (next == null) throw new IllegalArgumentException("unknown function: " + stages[i]);
            pipeline = pipeline.andThen(next);
        }
        return pipeline;
    }

    static String handle(Request req) {
        try {
            // spring.cloud.function.routing-expression models exactly this: pick the definition per-request
            Function<String, String> pipeline = compose(req.routingHeader());
            return pipeline.apply(req.body());
        } catch (IllegalArgumentException e) {
            return "ERROR: " + e.getMessage();
        }
    }

    public static void main(String[] args) {
        registry.put("uppercase", String::toUpperCase);
        registry.put("reverse", s -> new StringBuilder(s).reverse().toString());
        registry.put("exclaim", s -> s + "!");

        List<Request> incoming = List.of(
                new Request("uppercase|exclaim", "hello"),
                new Request("reverse", "world"),
                new Request("uppercase|typo|exclaim", "oops") // "typo" doesn't exist in the registry
        );

        for (Request req : incoming) {
            System.out.println(req.routingHeader() + " -> " + handle(req));
        }
    }
}
```

How to run: `java FunctionCompositionLevel3.java`

The first two requests route to valid pipelines and produce `"HELLO!"` and `"dlrow"` respectively; the third request's routing header names a stage (`"typo"`) that was never registered, so `compose` throws `IllegalArgumentException`, which `handle`'s `catch` block converts into an `"ERROR: unknown function: typo"` response instead of crashing the whole request-processing loop — one malformed routing header doesn't take down processing of the other, valid requests.

## 6. Walkthrough

Trace the third request in Level 3.

1. `handle(new Request("uppercase|typo|exclaim", "oops"))` is called, entering the `try` block.
2. `compose("uppercase|typo|exclaim")` splits the definition into `["uppercase", "typo", "exclaim"]`.
3. `registry.get("uppercase")` succeeds, returning the uppercase function, assigned to `pipeline`.
4. The loop's first iteration (`i=1`) calls `registry.get("typo")`, which returns `null` because no such entry was ever put into `registry` — the `if (next == null)` check catches this and throws `IllegalArgumentException("unknown function: typo")` immediately, before any chaining or execution happens.
5. Back in `handle`, the `catch (IllegalArgumentException e)` block catches this exception and returns `"ERROR: unknown function: typo"` as the response body — the exception never escapes `handle`, so the surrounding `for` loop in `main` continues normally to process any further requests.
6. `main`'s `println` prints `"uppercase|typo|exclaim -> ERROR: unknown function: typo"`, giving a caller-visible, specific explanation of what went wrong, rather than an unhandled crash.

```
request: routingHeader="uppercase|typo|exclaim", body="oops"
  compose splits into [uppercase, typo, exclaim]
  registry.get("uppercase") -> found, pipeline starts
  registry.get("typo")      -> NOT FOUND -> throw IllegalArgumentException
  handle() catches it       -> returns "ERROR: unknown function: typo"
  main's loop continues normally to the NEXT request
```

## 7. Gotchas & takeaways

> **Gotcha:** stage order in the definition string is significant and easy to get backwards — `"uppercase|reverse"` and `"reverse|uppercase"` produce different results whenever the two operations don't commute (as here: reversing an uppercased string versus uppercasing a reversed one happens to look identical for pure-case operations, but composed operations with real side effects, like `validate|persist` versus `persist|validate`, absolutely do not commute). Always read a pipe-separated definition left to right as literal execution order, the same way `andThen` chains execute left to right.

- Configuration-driven composition (`spring.cloud.function.definition=a|b|c`) achieves the same result as manually chaining `a.andThen(b).andThen(c)` in Java, but the combination is selected by a string, letting one deployed jar serve many different pipelines without new code per combination.
- Per-request routing (via `spring.cloud.function.routing-expression` or an equivalent routing header) extends this further: the same running application can dispatch different requests to different pipelines dynamically, rather than being fixed to one pipeline for its entire lifetime.
- An invalid or misspelled stage name in a definition string is a runtime failure, not a compile-time one — validating definition strings against the actual function catalog at startup (or handling the lookup failure gracefully per-request, as Level 3 does) prevents one bad routing header from becoming an unhandled exception.
- Keeping individual functions small and independently meaningful (as opposed to one large function doing several unrelated things) is what makes composition actually valuable — composing two already-monolithic functions gains little, since neither one is independently reusable in a different combination anyway.
