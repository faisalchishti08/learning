---
card: java
gi: 832
slug: properties
title: Properties
---

## 1. What it is

`Properties` is a specialized `Hashtable<Object, Object>` subclass (yes, still extending the legacy [`Hashtable`](0826-hashtable-legacy.md) class, for historical reasons dating to Java 1.0) designed specifically for string-to-string configuration data. It adds `getProperty(String key)` and `getProperty(String key, String defaultValue)` — type-safe, `String`-returning accessors layered on top of the raw `Object`-typed `Hashtable` machinery underneath — plus `setProperty(String, String)`, and crucially, `load(InputStream/Reader)`/`store(OutputStream/Writer, comments)` methods that read and write the standard `.properties` text file format directly.

## 2. Why & when

Before dedicated configuration libraries and formats like YAML or environment-variable-based config became common, `.properties` files were the standard, simple way to externalize configuration in Java applications — plain text, one `key=value` pair per line, trivially human-editable. `Properties` exists to load and save that exact format without any parsing code of your own: `load()` handles line-by-line parsing (including comments starting with `#` or `!`, and escaped characters), and `store()` writes it back out correctly formatted. It remains relevant today mainly for legacy configuration loading, JDK/library APIs that still expose configuration as `Properties` (like `System.getProperties()`), and situations needing zero-dependency, simple key-value config without pulling in a full configuration library.

## 3. Core concept

```java
Properties config = new Properties();
config.setProperty("app.name", "MyApp");
config.setProperty("app.timeout", "30");

config.getProperty("app.name");                 // "MyApp"
config.getProperty("app.missing", "default");    // "default" -- fallback for a missing key

// Loading from an actual .properties-formatted stream:
String fileContent = "app.name=MyApp\napp.timeout=30\n# a comment line\n";
config.load(new StringReader(fileContent));
```

Because `Properties` extends `Hashtable<Object, Object>`, the raw `put`/`get` methods (inherited, untyped) also technically work but return/accept `Object`, not `String` — always prefer `getProperty`/`setProperty` for actual configuration values to stay type-safe and to correctly handle the case where a key exists in a "defaults" `Properties` object chained beneath this one (which `getProperty` checks and `get` does not).

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Properties.load parses a properties-formatted text stream into key-value pairs; store writes them back out in the same format">
  <rect x="30" y="30" width="220" height="90" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="140" y="50" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace"># app config</text>
  <text x="140" y="68" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">app.name=MyApp</text>
  <text x="140" y="86" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">app.timeout=30</text>
  <text x="140" y="110" fill="#8b949e" font-size="9" text-anchor="middle">.properties text file</text>

  <line x1="250" y1="75" x2="330" y2="75" stroke="#79c0ff" stroke-width="2" marker-end="url(#a832)"/>
  <text x="290" y="65" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">load()</text>

  <rect x="340" y="30" width="260" height="90" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="470" y="60" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Properties (Hashtable&lt;Object,Object&gt;)</text>
  <text x="470" y="85" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">getProperty("app.name") -&gt; "MyApp"</text>
  <text x="470" y="103" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">getProperty("app.timeout") -&gt; "30"</text>

  <defs><marker id="a832" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

*`load()` parses a `.properties`-formatted stream directly into key-value pairs, ready for `getProperty()` access.*

## 5. Runnable example

Scenario: application configuration loaded from a `.properties`-formatted source, growing from basic in-memory get/set, to loading and saving the actual text format, to layering default values underneath user-supplied overrides.

### Level 1 — Basic

```java
import java.util.*;

public class ConfigBasic {
    public static void main(String[] args) {
        Properties config = new Properties();
        config.setProperty("app.name", "MyApp");
        config.setProperty("app.timeout", "30");

        System.out.println("app.name: " + config.getProperty("app.name"));
        System.out.println("app.missing (with default): " + config.getProperty("app.missing", "fallback"));
        System.out.println("app.missing (no default): " + config.getProperty("app.missing"));
    }
}
```

**How to run:** `java ConfigBasic.java` (JDK 17+).

Expected output:
```
app.name: MyApp
app.missing (with default): fallback
app.missing (no default): null
```

`getProperty` with a default argument never returns `null` for a missing key; the single-argument overload returns `null` exactly like `Map.get` would for an absent key.

### Level 2 — Intermediate

```java
import java.util.*;
import java.io.*;

public class ConfigLoadAndStore {
    public static void main(String[] args) throws IOException {
        String fileContent =
            "# Application configuration\n" +
            "app.name=MyApp\n" +
            "app.timeout=30\n" +
            "app.debug=false\n";

        Properties config = new Properties();
        config.load(new StringReader(fileContent)); // parse the .properties-formatted text directly

        System.out.println("loaded app.name: " + config.getProperty("app.name"));
        System.out.println("loaded app.timeout: " + config.getProperty("app.timeout"));

        // Modify and write back out in the same format.
        config.setProperty("app.debug", "true");
        StringWriter output = new StringWriter();
        config.store(output, "Updated configuration");

        System.out.println("--- stored output ---");
        System.out.println(output);
    }
}
```

**How to run:** `java ConfigLoadAndStore.java`.

Expected output shape (the exact comment-timestamp line `store()` writes will differ on your machine, since it includes the current date/time):
```
loaded app.name: MyApp
loaded app.timeout: 30
--- stored output ---
#Updated configuration
#<current date and time>
app.debug=true
app.name=MyApp
app.timeout=30
```

The real-world concern added: actually parsing (`load`) and re-serializing (`store`) the standard `.properties` text format — no manual string-splitting or parsing code needed. Note that key order in the stored output isn't guaranteed to match the original file's order, since `Properties` (being `Hashtable`-based underneath) doesn't preserve insertion order.

### Level 3 — Advanced

```java
import java.util.*;
import java.io.*;

public class ConfigWithDefaults {
    public static void main(String[] args) throws IOException {
        // A "defaults" Properties object -- the built-in Properties(Properties defaults) constructor
        // chains lookups: if a key is missing from the main map, it falls back to the defaults.
        Properties defaults = new Properties();
        defaults.setProperty("app.name", "DefaultAppName");
        defaults.setProperty("app.timeout", "10");
        defaults.setProperty("app.debug", "false");

        Properties userConfig = new Properties(defaults);
        String userSuppliedContent = "app.timeout=60\n"; // user only overrides ONE setting
        userConfig.load(new StringReader(userSuppliedContent));

        // getProperty automatically falls through to "defaults" for keys the user didn't override.
        System.out.println("app.name (falls back to default): " + userConfig.getProperty("app.name"));
        System.out.println("app.timeout (user override): " + userConfig.getProperty("app.timeout"));
        System.out.println("app.debug (falls back to default): " + userConfig.getProperty("app.debug"));

        // Gotcha: containsKey() and the raw Hashtable methods do NOT see defaults -- only getProperty does.
        System.out.println("userConfig.containsKey(\"app.name\") [does NOT check defaults]: " + userConfig.containsKey("app.name"));
        System.out.println("but getProperty(\"app.name\") still works: " + userConfig.getProperty("app.name"));
    }
}
```

**How to run:** `java ConfigWithDefaults.java`.

Expected output:
```
app.name (falls back to default): DefaultAppName
app.timeout (user override): 60
app.debug (falls back to default): false
userConfig.containsKey("app.name") [does NOT check defaults]: false
but getProperty("app.name") still works: true
```

This adds the production-flavored hard case: the built-in **defaults-chaining** constructor, `Properties(Properties defaults)`. `getProperty` correctly checks the main properties object first, then falls back to `defaults` if the key isn't found there — a clean way to express "these are the base settings, only override what you need to change." The counterintuitive trap: `containsKey()` (inherited directly from `Hashtable`, operating on the raw untyped storage) does **not** consult the defaults chain at all — only `getProperty()` (and the `String`-typed accessor methods generally) implement that fallback logic, which is easy to forget since both methods look like they should behave consistently.

## 6. Walkthrough

Tracing `ConfigWithDefaults.main`:

1. `defaults` is populated with three baseline settings: `app.name`, `app.timeout`, `app.debug`.
2. `userConfig = new Properties(defaults)` constructs a new `Properties` object with `defaults` registered as its fallback chain — `userConfig` itself starts completely empty of its own entries.
3. `userConfig.load(new StringReader("app.timeout=60\n"))` parses the single-line input and adds exactly one entry directly to `userConfig`: `app.timeout` = `"60"`. `userConfig`'s own storage now has one entry; `defaults` still has its original three, untouched.
4. `userConfig.getProperty("app.name")` first checks `userConfig`'s own entries — not found — then falls back to `defaults`, finding `"DefaultAppName"` there, and returns it.
5. `userConfig.getProperty("app.timeout")` finds the entry directly in `userConfig` itself (`"60"`, from the loaded content) and returns that, **without** consulting `defaults` at all — the user's explicit override takes precedence simply because it's found first, in the object closer to where the lookup started.
6. `userConfig.getProperty("app.debug")` again finds nothing in `userConfig`'s own storage, falls back to `defaults`, and returns `"false"`.
7. `userConfig.containsKey("app.name")` calls the inherited `Hashtable.containsKey`, which only ever inspects `userConfig`'s own internal storage — since `app.name` was never actually added to `userConfig` (only to `defaults`), this returns `false`, even though `getProperty("app.name")` on the very next line successfully returns a value, demonstrating the asymmetry between the two method families.

## 7. Gotchas & takeaways

> **Gotcha:** the defaults-chaining behavior is implemented **only** in `getProperty`/`propertyNames`/`stringPropertyNames` — the raw `Hashtable`-inherited methods (`get`, `containsKey`, `keySet`, `entrySet`, and a plain for-each loop over the map) only ever see the object's own directly-stored entries, completely bypassing the defaults chain. Always use `getProperty` (never `get`) when defaults-chaining behavior matters, and be aware that iterating a `Properties` object directly will miss any keys that only exist in its defaults.

- `Properties` extends [`Hashtable`](0826-hashtable-legacy.md)`<Object, Object>`, specialized for `String`-to-`String` configuration data via `getProperty`/`setProperty`.
- `load(InputStream/Reader)` and `store(OutputStream/Writer, comment)` read and write the standard `.properties` text file format directly, without manual parsing code.
- The `Properties(Properties defaults)` constructor enables a fallback chain: `getProperty` checks the object's own entries first, then falls back to `defaults` if not found there.
- The defaults-chaining behavior only applies to the `String`-typed accessor methods (`getProperty` and related) — raw `Hashtable`-inherited methods like `get`/`containsKey` never consult the defaults chain.
- `Properties`, being `Hashtable`-based, disallows `null` keys and values, and gives no iteration-order guarantee — the same caveats that apply to `Hashtable` generally apply here too.
