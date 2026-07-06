---
card: java
gi: 290
slug: java-util-properties
title: java.util.Properties
---

## 1. What it is

`java.util.Properties` is a specialized map for storing configuration values as `String` key/value pairs, with built-in support for loading from and saving to `.properties` files (and a simple XML format). It extends `Hashtable<Object,Object>` for historical reasons, but is meant to be used only with `String` keys and values.

```java
import java.util.Properties;

public class PropertiesDemo {
    public static void main(String[] args) {
        Properties config = new Properties();
        config.setProperty("db.host", "localhost");
        config.setProperty("db.port", "5432");

        System.out.println(config.getProperty("db.host"));
        System.out.println(config.getProperty("db.timeout", "30")); // default if missing
    }
}
```

`setProperty`/`getProperty` are the `String`-safe way to work with a `Properties` object, and `getProperty(key, default)` returns a fallback value when the key isn't present — handy for optional settings.

## 2. Why & when

Before dependency-injection frameworks and YAML/JSON configuration became common, `.properties` files were *the* standard way to externalize configuration in Java — database URLs, feature flags, localized text — without recompiling code.

- **Simple, human-editable format** — a `.properties` file is just `key=value` lines, easy to hand-edit and diff in version control.
- **Built-in load/save** — `Properties` can read a file via `load(InputStream)` and write one via `store(OutputStream, comment)`, with no extra parsing code needed.
- **Defaults chaining** — a `Properties` object can be constructed with a "defaults" `Properties`, so missing keys fall back automatically.
- **Still everywhere** — `ResourceBundle` (for internationalized text), many logging frameworks, and countless legacy applications configure themselves via `.properties` files to this day.

For new projects you'll often see YAML (Spring Boot's `application.yml`) or environment variables instead, but `.properties` remains common enough — and simple enough — that it's still a reasonable default for small, standalone configuration needs.

## 3. Core concept

```java
import java.io.StringReader;
import java.util.Properties;

public class PropertiesCore {
    public static void main(String[] args) throws Exception {
        String text = "app.name=Widget\napp.version=2.1\n";
        Properties props = new Properties();
        props.load(new StringReader(text));

        System.out.println(props.getProperty("app.name") + " v" + props.getProperty("app.version"));
    }
}
```

`load` parses the given source line by line, splitting each `key=value` line at the first `=` and storing both sides as strings — the same mechanism used whether the source is a `StringReader` (as here, for demonstration) or a real `FileInputStream` reading an actual `.properties` file on disk.

## 4. Diagram

<svg viewBox="0 0 620 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A properties file on disk is loaded into a Properties object in memory, which the application reads via getProperty">
  <rect x="8" y="8" width="604" height="154" rx="8" fill="#0d1117"/>
  <rect x="30" y="55" width="150" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="105" y="80" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">app.properties</text>
  <text x="105" y="98" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">db.host=localhost</text>

  <line x1="182" y1="85" x2="270" y2="85" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>
  <text x="226" y="75" fill="#3fb950" font-size="10" text-anchor="middle">load()</text>

  <rect x="275" y="55" width="150" height="60" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="350" y="80" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">Properties</text>
  <text x="350" y="98" fill="#8b949e" font-size="9" text-anchor="middle">(in-memory map)</text>

  <line x1="427" y1="85" x2="500" y2="85" stroke="#79c0ff" stroke-width="2" marker-end="url(#a2)"/>
  <text x="463" y="75" fill="#79c0ff" font-size="10" text-anchor="middle">getProperty</text>

  <text x="555" y="90" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">App code</text>
  <defs>
    <marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="a2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

The file is read once at startup; the rest of the program only ever talks to the in-memory `Properties` object.

## 5. Runnable example

Scenario: a small application configuration loader, evolved from a hardcoded default into a file-backed configuration with fallback defaults and validation of required keys.

### Level 1 — Basic

```java
import java.util.Properties;

public class PropertiesBasic {
    public static void main(String[] args) {
        Properties config = new Properties();
        config.setProperty("greeting", "Hello");
        config.setProperty("name", "World");

        System.out.println(config.getProperty("greeting") + ", " + config.getProperty("name") + "!");
    }
}
```

**How to run:** `java PropertiesBasic.java`

Builds a tiny in-memory configuration by hand and reads two values back out — no file involved yet.

### Level 2 — Intermediate

Same configuration idea, now written to and loaded from a real file on disk, demonstrating the persistence round-trip.

```java
import java.io.FileOutputStream;
import java.io.FileInputStream;
import java.util.Properties;

public class PropertiesIntermediate {
    public static void main(String[] args) throws Exception {
        Properties toSave = new Properties();
        toSave.setProperty("greeting", "Hello");
        toSave.setProperty("name", "World");
        try (FileOutputStream out = new FileOutputStream("app.properties")) {
            toSave.store(out, "App configuration");
        }

        Properties loaded = new Properties();
        try (FileInputStream in = new FileInputStream("app.properties")) {
            loaded.load(in);
        }

        System.out.println(loaded.getProperty("greeting") + ", " + loaded.getProperty("name") + "!");
    }
}
```

**How to run:** `java PropertiesIntermediate.java` (writes `app.properties` in the current directory, then reads it back)

`store` writes the comment as a leading `#` line followed by `key=value` lines; a fresh `Properties` object then reconstructs the identical key/value pairs via `load`, proving the round-trip preserves the data exactly.

### Level 3 — Advanced

Same configuration loader, now with default values via a defaults `Properties` object and validation that required keys are present after loading, throwing a clear error otherwise.

```java
import java.io.FileOutputStream;
import java.io.FileInputStream;
import java.util.Properties;

public class PropertiesAdvanced {
    static Properties loadConfig(String path, Properties defaults, String... requiredKeys) throws Exception {
        Properties config = new Properties(defaults); // fallback chain: missing keys check defaults
        try (FileInputStream in = new FileInputStream(path)) {
            config.load(in);
        }
        for (String key : requiredKeys) {
            if (config.getProperty(key) == null) {
                throw new IllegalStateException("Missing required config key: " + key);
            }
        }
        return config;
    }

    public static void main(String[] args) throws Exception {
        // Simulate a config file that is missing "timeout" but has "host"
        Properties fileContents = new Properties();
        fileContents.setProperty("host", "localhost");
        try (FileOutputStream out = new FileOutputStream("app.properties")) {
            fileContents.store(out, "Partial config");
        }

        Properties defaults = new Properties();
        defaults.setProperty("timeout", "30");
        defaults.setProperty("host", "0.0.0.0");

        Properties config = loadConfig("app.properties", defaults, "host", "timeout");

        System.out.println("host = " + config.getProperty("host"));       // from file
        System.out.println("timeout = " + config.getProperty("timeout")); // from defaults
    }
}
```

**How to run:** `java PropertiesAdvanced.java`

`new Properties(defaults)` creates a `Properties` whose `getProperty` transparently falls back to `defaults` for any key not found in the loaded file, so validation against `requiredKeys` sees `"timeout"` as present (via the fallback) even though the file itself never mentioned it.

## 6. Walkthrough

Trace `PropertiesAdvanced.main` step by step.

**File setup.** `fileContents` gets one key, `"host"`, and is stored to `app.properties` on disk — the file now literally contains `host=localhost` plus a comment line.

**Defaults setup.** `defaults` gets two keys: `"timeout"=30` and `"host"=0.0.0.0`. This object is never written to disk; it lives only in memory as a fallback source.

**`loadConfig("app.properties", defaults, "host", "timeout")` is called.** Inside, `new Properties(defaults)` constructs `config` with `defaults` wired in as its fallback chain — at this point `config` itself has zero entries of its own, but `config.getProperty("host")` would already return `"0.0.0.0"` via the fallback if asked right now.

**`config.load(in)`.** Reads `app.properties` line by line and inserts `host=localhost` directly into `config`'s own entries. Now `config` has one *own* entry (`host`), plus the fallback to `defaults` for everything else.

**Validation loop.** For `"host"`: `config.getProperty("host")` checks `config`'s own entries first, finds `"localhost"` — not null, passes. For `"timeout"`: `config`'s own entries have no `"timeout"` key, so `getProperty` falls through to `defaults`, finds `"30"` — not null, passes. Both required keys are satisfied, so no exception is thrown and `config` is returned.

**Final prints.** `config.getProperty("host")` — found directly in `config` — prints `"localhost"`. `config.getProperty("timeout")` — found only via the defaults fallback — prints `"30"`.

```
app.properties (on disk):        defaults (in memory only):
  host=localhost                   timeout=30
                                    host=0.0.0.0

config = new Properties(defaults) then config.load(file)
  config's own entries: { host=localhost }
  config.getProperty("host")    -> "localhost"   (own entry wins)
  config.getProperty("timeout") -> "30"          (falls back to defaults)
```

**Output:**
```
host = localhost
timeout = 30
```

## 7. Gotchas & takeaways

> `Properties` extends `Hashtable<Object,Object>`, which means its raw `put`/`get` methods (inherited from `Hashtable`) accept and return `Object`, not `String` — nothing stops you from accidentally calling `props.put("key", 42)` with an `Integer` value. Always use `setProperty`/`getProperty`, which are typed to `String` and are what `load`/`store` expect.

> `getProperty(key)` returns `null` for a missing key with no fallback — a very common `NullPointerException` source downstream when the returned value is used without a null check. Use `getProperty(key, defaultValue)` whenever a sensible default exists.

- `Properties` is a `String`-keyed, `String`-valued map with built-in `.properties`-file load/save support.
- Always use `setProperty`/`getProperty`, not the inherited raw `Hashtable` methods, to keep values as `String`.
- A `Properties` object can be constructed with a defaults `Properties`, letting missing keys fall back automatically without extra code.
- Modern projects often prefer YAML or environment variables, but `.properties` remains common for small, standalone configuration and for `ResourceBundle`-based internationalization.
