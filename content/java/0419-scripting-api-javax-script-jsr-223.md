---
card: java
gi: 419
slug: scripting-api-javax-script-jsr-223
title: Scripting API javax.script (JSR 223)
---

## 1. What it is

`javax.script` (JSR 223), added in Java 6, is a standard API for embedding and invoking **scripting engines** from Java code, independent of which scripting language they implement. The central classes are `ScriptEngineManager` (discovers and creates engines, and lets you register custom ones), `ScriptEngine` (the engine itself — `eval(String)` runs script text and returns a result), and `Bindings` (a `Map<String, Object>` of variables shared between Java and the script, so each side can read and write the other's data).

## 2. Why & when

Before JSR 223, embedding a scripting language in a Java application meant writing directly against that specific engine's proprietary API — code written for one scripting engine wouldn't work with another, and swapping engines meant rewriting the integration. JSR 223 standardizes the *contract*: any compliant engine (JavaScript via Nashorn historically, Groovy, Python via Jython, or a custom domain-specific language you write yourself) can be plugged in and driven through the exact same `ScriptEngineManager`/`ScriptEngine`/`Bindings` API, without the calling code needing to know which engine it's actually talking to.

You reach for this whenever an application needs to run **user-supplied or dynamically-loaded logic** without recompiling — a rules engine where business analysts write simple conditions, a plugin system, or a calculator/formula feature where end users type expressions to be evaluated at runtime. The engine can be swapped later (a faster implementation, a different language) without touching the calling code.

## 3. Core concept

```java
import javax.script.*;

ScriptEngineManager manager = new ScriptEngineManager();

// Real engines are discovered automatically via ServiceLoader if present on the classpath.
// You can ALSO register one explicitly at runtime -- this is what makes JSR 223 genuinely pluggable.
manager.registerEngineName("my-engine", myCustomFactory);

ScriptEngine engine = manager.getEngineByName("my-engine");
engine.put("x", 10);                      // Java -> script: bind a variable
Object result = engine.eval("x + 5");     // script runs, sees "x" as 10
System.out.println(result);               // whatever the engine decided "x + 5" means
```

Because no scripting language ships bundled with a stock JDK (Nashorn, the JavaScript engine once bundled with Java 8–14, was removed from the JDK in Java 15), the runnable examples below build a tiny custom engine to demonstrate the *real* mechanism — `ScriptEngineManager.registerEngineName()` — rather than depending on an external engine dependency.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Java code obtains a named ScriptEngine from ScriptEngineManager, then passes variables in via Bindings, evaluates script text, and gets a result back">
  <rect x="8" y="8" width="624" height="164" rx="8" fill="#0d1117"/>
  <rect x="30" y="40" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="120" y="65" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">ScriptEngineManager</text>

  <rect x="250" y="40" width="160" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="330" y="65" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">ScriptEngine</text>

  <rect x="450" y="40" width="160" height="40" rx="6" fill="#1c2430" stroke="#e6edf3"/>
  <text x="530" y="65" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Bindings (vars)</text>

  <line x1="210" y1="60" x2="245" y2="60" stroke="#8b949e" marker-end="url(#ay1)"/>
  <text x="228" y="52" fill="#8b949e" font-size="8" text-anchor="middle">getEngineByName</text>
  <line x1="330" y1="80" x2="330" y2="110" stroke="#8b949e"/>
  <text x="330" y="128" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">eval(scriptText) reads/writes Bindings, returns a result</text>

  <defs><marker id="ay1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The manager hands out engines by name; the engine's `eval()` is where script text actually runs against shared variable bindings.

## 5. Runnable example

Scenario: a tiny rules engine that evaluates simple `variable = number (+ number)*` scripts written by non-programmers — the same custom engine, evolved from evaluating a single expression, through passing variables in and out via `Bindings`, to correctly scoping engine-local versus globally-shared bindings.

### Level 1 — Basic

```java
import javax.script.*;
import java.util.*;

public class MiniScriptEngine extends AbstractScriptEngine {
    @Override
    public Object eval(String script, ScriptContext context) throws ScriptException {
        // Extremely small "language": one line, e.g. "3 + 4 + 5" -- sum whitespace-separated numbers/plus signs
        String[] tokens = script.trim().split("\\s+");
        double result = 0;
        for (String token : tokens) {
            if (!token.equals("+")) {
                try {
                    result += Double.parseDouble(token);
                } catch (NumberFormatException e) {
                    throw new ScriptException("Not a number: " + token);
                }
            }
        }
        return result;
    }

    @Override public Object eval(java.io.Reader reader, ScriptContext context) throws ScriptException {
        return eval(new Scanner(reader).useDelimiter("\\A").next(), context);
    }
    @Override public Bindings createBindings() { return new SimpleBindings(); }
    @Override public ScriptEngineFactory getFactory() { return new MiniScriptEngineFactory(); }

    public static void main(String[] args) throws ScriptException {
        ScriptEngineManager manager = new ScriptEngineManager();
        manager.registerEngineName("mini", new MiniScriptEngineFactory());

        ScriptEngine engine = manager.getEngineByName("mini");
        Object result = engine.eval("10 + 20 + 5");
        System.out.println("Result: " + result);
    }
}

class MiniScriptEngineFactory implements ScriptEngineFactory {
    public String getEngineName() { return "MiniScriptEngine"; }
    public String getEngineVersion() { return "1.0"; }
    public java.util.List<String> getExtensions() { return List.of("mini"); }
    public java.util.List<String> getMimeTypes() { return List.of(); }
    public java.util.List<String> getNames() { return List.of("mini"); }
    public String getLanguageName() { return "MiniScript"; }
    public String getLanguageVersion() { return "1.0"; }
    public Object getParameter(String key) { return null; }
    public String getMethodCallSyntax(String obj, String m, String... args) { return null; }
    public String getOutputStatement(String toDisplay) { return null; }
    public String getProgram(String... statements) { return String.join(";", statements); }
    public ScriptEngine getScriptEngine() { return new MiniScriptEngine(); }
}
```

**How to run:** `java MiniScriptEngine.java`

`registerEngineName("mini", ...)` is the real, standard JSR 223 pluggability mechanism — any code that later calls `manager.getEngineByName("mini")` gets this engine back without knowing anything about `MiniScriptEngine`'s implementation, exactly as it would for a real third-party engine like Groovy's.

### Level 2 — Intermediate

```java
import javax.script.*;
import java.util.*;

public class MiniScriptWithVariables {
    public static void main(String[] args) throws ScriptException {
        ScriptEngineManager manager = new ScriptEngineManager();
        manager.registerEngineName("mini", new MiniScriptEngineFactory());
        ScriptEngine engine = manager.getEngineByName("mini");

        engine.put("basePrice", 100);   // Java -> script
        engine.put("tax", 8);

        // Our tiny language only sums numbers, so we resolve variables to numbers before eval --
        // a real engine (Nashorn, Groovy) would resolve identifiers like "basePrice" itself.
        int basePrice = (Integer) engine.get("basePrice");
        int tax = (Integer) engine.get("tax");
        Object result = engine.eval(basePrice + " + " + tax);

        engine.put("total", result); // script result -> back into Bindings for later use
        System.out.println("Total stored in bindings: " + engine.get("total"));
    }
}

// Same tiny engine from Level 1, reused here unchanged.
class MiniScriptEngine extends AbstractScriptEngine {
    @Override
    public Object eval(String script, ScriptContext context) throws ScriptException {
        String[] tokens = script.trim().split("\\s+");
        double result = 0;
        for (String token : tokens) {
            if (!token.equals("+")) {
                try {
                    result += Double.parseDouble(token);
                } catch (NumberFormatException e) {
                    throw new ScriptException("Not a number: " + token);
                }
            }
        }
        return result;
    }
    @Override public Object eval(java.io.Reader reader, ScriptContext context) throws ScriptException {
        return eval(new Scanner(reader).useDelimiter("\\A").next(), context);
    }
    @Override public Bindings createBindings() { return new SimpleBindings(); }
    @Override public ScriptEngineFactory getFactory() { return new MiniScriptEngineFactory(); }
}

class MiniScriptEngineFactory implements ScriptEngineFactory {
    public String getEngineName() { return "MiniScriptEngine"; }
    public String getEngineVersion() { return "1.0"; }
    public List<String> getExtensions() { return List.of("mini"); }
    public List<String> getMimeTypes() { return List.of(); }
    public List<String> getNames() { return List.of("mini"); }
    public String getLanguageName() { return "MiniScript"; }
    public String getLanguageVersion() { return "1.0"; }
    public Object getParameter(String key) { return null; }
    public String getMethodCallSyntax(String obj, String m, String... args) { return null; }
    public String getOutputStatement(String toDisplay) { return null; }
    public String getProgram(String... statements) { return String.join(";", statements); }
    public ScriptEngine getScriptEngine() { return new MiniScriptEngine(); }
}
```

**How to run:** `java MiniScriptWithVariables.java`

`engine.put(...)`/`engine.get(...)` read and write the engine's `Bindings` — a shared `Map<String,Object>` that both Java and the script can see. Storing the computed `result` back via `engine.put("total", result)` demonstrates the two-way data flow: values can move from Java into the script's world and back out again.

### Level 3 — Advanced

```java
import javax.script.*;

public class MiniScriptEngineScopes {
    public static void main(String[] args) throws ScriptException {
        ScriptEngineManager manager = new ScriptEngineManager();
        manager.registerEngineName("mini", new MiniScriptEngineFactory());
        ScriptEngine engine = manager.getEngineByName("mini");

        // GLOBAL_SCOPE bindings are visible to every engine the manager creates; ENGINE_SCOPE
        // bindings belong only to this one engine instance and take precedence over global ones.
        Bindings globalBindings = manager.getBindings();
        globalBindings.put("discount", 0.0);

        Bindings engineBindings = engine.createBindings();
        engineBindings.put("discount", 5.0); // shadows the global "discount" for THIS engine only
        engine.setBindings(engineBindings, ScriptContext.ENGINE_SCOPE);
        engine.setBindings(globalBindings, ScriptContext.GLOBAL_SCOPE);

        double effectiveDiscount = (Double) engine.get("discount"); // resolves ENGINE_SCOPE first
        System.out.println("Effective discount seen by this engine: " + effectiveDiscount);
        System.out.println("Global discount (unaffected): " + globalBindings.get("discount"));
    }
}

// Same tiny engine from Level 1, reused here unchanged.
class MiniScriptEngine extends AbstractScriptEngine {
    @Override
    public Object eval(String script, ScriptContext context) throws ScriptException {
        String[] tokens = script.trim().split("\\s+");
        double result = 0;
        for (String token : tokens) {
            if (!token.equals("+")) {
                try {
                    result += Double.parseDouble(token);
                } catch (NumberFormatException e) {
                    throw new ScriptException("Not a number: " + token);
                }
            }
        }
        return result;
    }
    @Override public Object eval(java.io.Reader reader, ScriptContext context) throws ScriptException {
        return eval(new java.util.Scanner(reader).useDelimiter("\\A").next(), context);
    }
    @Override public Bindings createBindings() { return new SimpleBindings(); }
    @Override public ScriptEngineFactory getFactory() { return new MiniScriptEngineFactory(); }
}

class MiniScriptEngineFactory implements ScriptEngineFactory {
    public String getEngineName() { return "MiniScriptEngine"; }
    public String getEngineVersion() { return "1.0"; }
    public java.util.List<String> getExtensions() { return java.util.List.of("mini"); }
    public java.util.List<String> getMimeTypes() { return java.util.List.of(); }
    public java.util.List<String> getNames() { return java.util.List.of("mini"); }
    public String getLanguageName() { return "MiniScript"; }
    public String getLanguageVersion() { return "1.0"; }
    public Object getParameter(String key) { return null; }
    public String getMethodCallSyntax(String obj, String m, String... args) { return null; }
    public String getOutputStatement(String toDisplay) { return null; }
    public String getProgram(String... statements) { return String.join(";", statements); }
    public ScriptEngine getScriptEngine() { return new MiniScriptEngine(); }
}
```

**How to run:** `java MiniScriptEngineScopes.java`

`ScriptContext.ENGINE_SCOPE` bindings are private to one engine instance and take precedence over `ScriptContext.GLOBAL_SCOPE` bindings (shared across every engine the manager creates) when both define the same variable name — this scoping mechanism matters in real applications hosting multiple engine instances that should share some, but not all, state.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `manager.registerEngineName("mini", ...)` registers the custom factory; `engine` is obtained by name.

`manager.getBindings()` retrieves the manager's shared `GLOBAL_SCOPE` `Bindings` map (initially empty of custom keys); `globalBindings.put("discount", 0.0)` sets a global default discount of `0.0`.

`engine.createBindings()` creates a fresh, empty `Bindings` map specific to this engine — `engineBindings.put("discount", 5.0)` sets a *different* value, `5.0`, in this engine-local map. `engine.setBindings(engineBindings, ScriptContext.ENGINE_SCOPE)` installs this as the engine's own scope, and `engine.setBindings(globalBindings, ScriptContext.GLOBAL_SCOPE)` installs the shared map as the global scope for this engine's context.

`engine.get("discount")` looks up `"discount"` by checking `ENGINE_SCOPE` first (since it has higher precedence), finds `5.0` there, and returns it immediately without ever consulting `GLOBAL_SCOPE` — this is printed as `"Effective discount seen by this engine: 5.0"`.

`globalBindings.get("discount")` bypasses the engine's scope resolution entirely and reads directly from the global map, correctly returning the untouched `0.0` — demonstrating that the engine-scope value shadowed, but did not modify, the global one.

Expected output:
```
Effective discount seen by this engine: 5.0
Global discount (unaffected): 0.0
```

## 7. Gotchas & takeaways

> Modern JDKs (15 and later) ship **no built-in scripting engine at all** — Nashorn (the JavaScript engine bundled from Java 8 through 14) was removed in JEP 372. `ScriptEngineManager().getEngineByName("javascript")` returns `null` on a stock JDK 17 unless you explicitly add an engine dependency (such as GraalJS) to the classpath. Don't assume any particular language engine is available without checking `getEngineFactories()` first or shipping one yourself.

- `ScriptEngineManager` discovers engines automatically via `ServiceLoader` from the classpath, and also lets you register one explicitly at runtime with `registerEngineName`/`registerEngineExtension`/`registerEngineMimeType`.
- `Bindings` is a `Map<String, Object>` shared between Java and the running script — `engine.put`/`engine.get` are shorthand for accessing the engine's default (`ENGINE_SCOPE`) bindings.
- `ENGINE_SCOPE` bindings are private to one engine instance and take precedence over `GLOBAL_SCOPE` bindings, which are shared across every engine a given `ScriptEngineManager` creates.
- The API itself is language-agnostic — the same `ScriptEngine`/`Bindings`/`eval()` contract works whether the underlying engine runs JavaScript, Groovy, Python, or a tiny custom DSL like the one built here.
- Because no engine ships with the JDK by default since Java 15, real-world use requires adding a specific engine's dependency (and understanding that engine's own language semantics) — the JSR 223 API only standardizes *how you talk to* whichever engine you choose.
