---
card: java
gi: 685
slug: nashorn-removed
title: Nashorn removed
---

## 1. What it is

**Java 15 removed the Nashorn JavaScript engine** entirely from the JDK (JEP 372), along with its `jjs` command-line tool and the `javax.script` (JSR 223) bindings that let Java code embed and execute JavaScript via `ScriptEngineManager.getEngineByName("nashorn")`. Nashorn had already been marked **deprecated for removal** back in Java 11 (see [Nashorn JavaScript engine deprecated](0621-nashorn-javascript-engine-deprecated.md) in the Java 11 tutorials); Java 15 followed through on that plan and deleted the engine, its scripts APIs implementation, and `jjs` from the JDK image entirely. Code that calls `ScriptEngineManager.getEngineByName("nashorn")` on Java 15+ now receives `null` instead of a working engine, since there is nothing left to return.

## 2. Why & when

Nashorn was announced as deprecated specifically because the JDK team judged that keeping pace with the fast-moving ECMAScript specification (which was, by the mid-2010s, releasing new language features annually) was more effort than the JDK team wanted to continue committing to as part of the standard library — JavaScript engines are complex, security-sensitive, high-maintenance software, and a general-purpose ECMAScript implementation is not central to what most Java applications need. The deprecation announcement in Java 11 gave library authors and applications roughly two years' warning before the actual removal in Java 15, following the JDK's now-standard "deprecate first, remove later" policy for exactly this kind of significant API surface reduction. If your code still targets Nashorn after Java 15, migrate either to **GraalVM's JavaScript engine** (a separate, actively maintained, spec-compliant implementation available as an add-on for the standard JDK or bundled with GraalVM distributions) or, if the JavaScript execution was incidental (e.g. embedded rule expressions that could just as well be expressed differently), consider whether a Java-native alternative removes the scripting dependency altogether.

## 3. Core concept

```java
import javax.script.ScriptEngine;
import javax.script.ScriptEngineManager;

// On Java 8–14: this returns a working Nashorn engine (deprecated from Java 11)
// On Java 15+: this returns null — Nashorn no longer exists in the JDK
ScriptEngine engine = new ScriptEngineManager().getEngineByName("nashorn");

if (engine == null) {
    System.out.println("Nashorn is not available on this JDK.");
} else {
    engine.eval("print('hello from JavaScript');");
}
```

The `javax.script` (JSR 223) API itself is unaffected — only the specific `"nashorn"` engine registration was removed; other JSR 223-compliant engines (like GraalVM's) can still be plugged into the same generic API.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Nashorn timeline: introduced in Java 8, deprecated in Java 11, fully removed in Java 15">
  <line x1="40" y1="100" x2="600" y2="100" stroke="#8b949e" stroke-width="2"/>

  <circle cx="100" cy="100" r="8" fill="#6db33f"/>
  <text x="100" y="70" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Java 8</text>
  <text x="100" y="130" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Nashorn introduced</text>

  <circle cx="340" cy="100" r="8" fill="#f0883e"/>
  <text x="340" y="70" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">Java 11</text>
  <text x="340" y="130" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">deprecated for removal</text>

  <circle cx="560" cy="100" r="8" fill="#f85149"/>
  <text x="560" y="70" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">Java 15</text>
  <text x="560" y="130" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">fully removed</text>
</svg>

Roughly two years and several JDK releases separated the deprecation warning from the actual removal, giving users time to migrate.

## 5. Runnable example

Scenario: code that depends on Nashorn — first a naive version that assumes it's always available, then a defensive version that checks for `null` and falls back gracefully, then a version that migrates the same functionality away from an embedded scripting engine entirely by expressing the "script" as a plain Java `Predicate`, illustrating one common Nashorn-removal migration path.

### Level 1 — Basic

```java
// File: NaiveScriptUse.java
import javax.script.ScriptEngine;
import javax.script.ScriptEngineManager;

public class NaiveScriptUse {
    public static void main(String[] args) throws Exception {
        ScriptEngine engine = new ScriptEngineManager().getEngineByName("nashorn");
        // On Java 15+, "engine" is null here — calling eval on it throws NPE.
        Object result = engine.eval("2 + 2");
        System.out.println("Result: " + result);
    }
}
```

**How to run on Java 15+:**
```
java NaiveScriptUse.java
```

Expected output (Nashorn no longer exists, so this fails; the exact local-variable label depends on whether debug info was compiled in — it may read "engine" or a generic "<local1>"):
```
Exception in thread "main" java.lang.NullPointerException: Cannot invoke "javax.script.ScriptEngine.eval(String)" because "<local1>" is null
	at NaiveScriptUse.main(NaiveScriptUse.java:7)
```

### Level 2 — Intermediate

```java
// File: DefensiveScriptUse.java
import javax.script.ScriptEngine;
import javax.script.ScriptEngineManager;

public class DefensiveScriptUse {
    public static void main(String[] args) throws Exception {
        ScriptEngine engine = new ScriptEngineManager().getEngineByName("nashorn");

        if (engine == null) {
            System.out.println("Nashorn engine not found on this JDK (removed since Java 15).");
            System.out.println("Falling back to a hard-coded Java implementation.");
            System.out.println("Result: " + (2 + 2));
            return;
        }

        Object result = engine.eval("2 + 2");
        System.out.println("Result: " + result);
    }
}
```

**How to run on Java 15+:**
```
java DefensiveScriptUse.java
```

Expected output:
```
Nashorn engine not found on this JDK (removed since Java 15).
Falling back to a hard-coded Java implementation.
Result: 4
```

This is the minimum safe pattern for any code that used to assume Nashorn was always present: check for `null` before calling any method on the returned `ScriptEngine`, since `getEngineByName` simply returns `null` for an unregistered engine name rather than throwing.

### Level 3 — Advanced

```java
// File: RuleMigration.java
import java.util.List;
import java.util.function.Predicate;
import java.util.Map;

public class RuleMigration {
    // Before (Nashorn-era): a rule was a JavaScript expression string,
    // evaluated per record via engine.eval() with bound variables, e.g.
    //   engine.put("age", record.get("age"));
    //   boolean matches = (boolean) engine.eval("age >= 18");
    //
    // After (Nashorn removed): the same rule expressed as a plain Java
    // Predicate — no embedded scripting engine required at all.
    static Predicate<Map<String, Object>> ageAtLeast(int minAge) {
        return record -> ((Integer) record.get("age")) >= minAge;
    }

    public static void main(String[] args) {
        List<Map<String, Object>> records = List.of(
                Map.of("name", "Alice", "age", 30),
                Map.of("name", "Bob", "age", 15),
                Map.of("name", "Carol", "age", 18)
        );

        Predicate<Map<String, Object>> rule = ageAtLeast(18);

        for (Map<String, Object> record : records) {
            boolean matches = rule.test(record);
            System.out.println(record.get("name") + " (age " + record.get("age") + "): "
                    + (matches ? "eligible" : "not eligible"));
        }
    }
}
```

**How to run:**
```
java RuleMigration.java
```

Expected output:
```
Alice (age 30): eligible
Bob (age 15): not eligible
Carol (age 18): eligible
```

Level 3 shows the migration path many teams actually took: business rules that were originally expressed as small embedded JavaScript snippets (evaluated per record with Nashorn) were rewritten as plain Java `Predicate`s or small interpreter classes, eliminating the dependency on any embedded scripting engine entirely rather than replacing Nashorn with a different one — appropriate whenever the "scripting" need was really just a handful of simple, evaluable conditions rather than genuinely dynamic, user-authored JavaScript.

## 6. Walkthrough

1. In `NaiveScriptUse`, `new ScriptEngineManager().getEngineByName("nashorn")` asks the JSR 223 script-engine registry (a service-provider mechanism scanned at JVM startup) for an engine registered under the name `"nashorn"`. On Java 8 through 14, this registry would find Nashorn's provider and return a working `ScriptEngine`; on Java 15+, no such provider exists anywhere on the module path or classpath, so the method returns `null` — this is standard JSR 223 behavior for an unrecognized engine name, not a special case introduced by Nashorn's removal.
2. Calling `engine.eval("2 + 2")` on a `null` reference immediately throws `NullPointerException` — and, since Java 14's [helpful NullPointerExceptions](0669-helpful-nullpointerexceptions.md) feature, the exception message names the exact method call that failed (`ScriptEngine.eval(String)`) because its target reference was null, making this specific failure mode easy to diagnose even without prior knowledge of Nashorn's removal.
3. `DefensiveScriptUse` performs the same lookup but checks `if (engine == null)` immediately afterward. Taking that branch, it prints an explanatory message and computes the same `2 + 2` result directly in Java — demonstrating the simplest possible migration: detect the missing engine, and fall back rather than crash.
4. `RuleMigration` goes further: instead of merely falling back to a hard-coded calculation, it re-expresses what would have been a dynamically-evaluated JavaScript rule (something like the string `"age >= 18"`, evaluated per record with `age` bound as a script variable) as a genuine Java `Predicate<Map<String, Object>>` returned by the `ageAtLeast(int minAge)` factory method.
5. `main` builds a `List` of three record-like `Map`s, each with `"name"` and `"age"` entries, then obtains one concrete rule via `ageAtLeast(18)`.
6. For each record, `rule.test(record)` extracts the `"age"` entry, casts it to `Integer`, and compares it against the captured `minAge` (18, from the closure) — this is exactly the same conditional logic a JavaScript rule string would have expressed, just written directly in Java and requiring no script parsing or evaluation step at runtime at all.
7. The loop prints each record's eligibility: Alice (30) and Carol (18, satisfying `>= 18`) are eligible; Bob (15) is not — the same business outcome the old Nashorn-based rule engine would have produced, but now computed without any embedded scripting dependency, no per-call script-parsing overhead, and full type-checking of the rule logic at compile time.

```
getEngineByName("nashorn")
        │
   Java ≤14: returns working ScriptEngine
   Java 15+: returns null
        │
        ▼
  null-check ──► fallback: hard-coded Java logic (Level 2)
        │            or
        └──────► fully re-modeled as Predicate<T> (Level 3, no scripting at all)
```

## 7. Gotchas & takeaways

> `ScriptEngineManager.getEngineByName("nashorn")` returning `null` on Java 15+ is **not an error condition the JSR 223 API reports specially** — it's the same, ordinary "no engine registered under this name" behavior that would occur for any misspelled or unavailable engine name. Any code that skipped the `null` check (assuming Nashorn was always present) will fail with a plain `NullPointerException` at the first `eval` call, not with any Nashorn-specific error message.

- Nashorn's full timeline: introduced in Java 8, deprecated for removal in Java 11, fully removed in Java 15 — roughly a four-release, multi-year deprecation cycle typical of significant JDK API removals.
- The `javax.script` (JSR 223) API itself was **not** removed — only the `"nashorn"` engine registration and the `jjs` command-line tool. Other JSR 223-compliant engines (such as GraalVM's JavaScript engine) can still be added as a dependency and used through the same generic scripting API.
- If genuine, actively-maintained JavaScript execution is still required (not just simple rule evaluation), **GraalVM's JavaScript engine** is the JDK team's recommended, spec-compliant successor — it can be added to a standard JDK via Maven/Gradle dependencies rather than requiring the full GraalVM distribution.
- Search your codebase for `getEngineByName("nashorn")`, `jjs`, and any Maven/Gradle dependency on `org.openjdk.nashorn` before upgrading to Java 15+ — these are the concrete signals that migration work is needed.
- Removing an embedded scripting dependency entirely (as in Level 3's `Predicate`-based migration) is often the *better* long-term outcome, not just a workaround — it usually means less runtime overhead, full compile-time type checking, and one fewer moving part in the deployed application, at the cost of losing runtime-configurable/user-authored rule text.
