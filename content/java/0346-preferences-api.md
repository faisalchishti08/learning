---
card: java
gi: 346
slug: preferences-api
title: Preferences API
---

## 1. What it is

The `java.util.prefs.Preferences` API provides a small, hierarchical, persistent key-value store built into the JDK, intended for storing lightweight application settings — window positions, user options, last-used file paths — without requiring you to manage your own configuration file format or location. Preferences come in two flavors: **user** preferences (`Preferences.userNodeForPackage(...)` or `Preferences.userRoot()`), scoped to the current OS user, and **system** preferences, shared across all users on the machine; both are organized into a tree of named nodes, typically mirroring your package structure.

```java
import java.util.prefs.Preferences;

public class PreferencesDemo {
    public static void main(String[] args) {
        Preferences prefs = Preferences.userNodeForPackage(PreferencesDemo.class);
        prefs.put("username", "ada");
        prefs.putInt("windowWidth", 1024);

        System.out.println("username: " + prefs.get("username", "unknown"));
        System.out.println("windowWidth: " + prefs.getInt("windowWidth", 800));
    }
}
```

`prefs.put`/`prefs.get` store and retrieve string values; every getter takes a default value as its second argument, returned if the key was never set — there is no `NullPointerException` or missing-key exception to handle, by design.

## 2. Why & when

Writing and parsing a custom configuration file (properties, JSON, or otherwise) for simple application settings is real, repeated boilerplate — the Preferences API exists specifically to remove that boilerplate for lightweight, per-user or per-machine settings, backed by whatever storage mechanism the platform naturally provides (the Windows Registry, a set of files under the user's home directory on Unix-like systems, or similar).

- **Remembering user preferences across application runs** — window size and position, selected theme, recently opened files, or any small setting that should persist without the user needing to reconfigure it every launch.
- **Storing settings without managing file paths or formats yourself** — the API abstracts away exactly where and how the data is stored, which varies by platform, so your code doesn't need to know or care.
- **Organizing settings hierarchically** — nodes can be nested (e.g., one node per feature or module), keeping related settings grouped without needing a single flat namespace.

The Preferences API is meant for small amounts of configuration data, not large datasets or anything performance-critical — it is explicitly documented as unsuitable for large amounts of data, and each individual value has documented size limits (keys and string values are capped at a fixed maximum length); for real application data storage, a proper database or file format remains the right tool.

## 3. Core concept

```java
import java.util.prefs.Preferences;

public class PreferencesCore {
    public static void main(String[] args) {
        Preferences prefs = Preferences.userNodeForPackage(PreferencesCore.class);

        System.out.println("Before setting, theme = " + prefs.get("theme", "light")); // uses default
        prefs.put("theme", "dark");
        System.out.println("After setting, theme = " + prefs.get("theme", "light")); // uses stored value

        prefs.remove("theme"); // clean up so repeated runs of this demo behave consistently
    }
}
```

**How to run:** `java PreferencesCore.java` (run it twice to see that without the final `remove`, the value would persist between runs)

Every `get` call requires a default value as its second argument — there's no way to ask for a key without also specifying what to return if it was never set, which is a deliberate design choice that avoids null-handling entirely.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Preferences nodes form a hierarchical tree, typically one node per package, each holding simple key-value pairs persisted by the platform">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="180" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="50" fill="#79c0ff" font-size="9" text-anchor="middle">userRoot()</text>

  <rect x="230" y="30" width="180" height="30" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="50" fill="#8b949e" font-size="9" text-anchor="middle">com/example/myapp node</text>

  <rect x="440" y="30" width="140" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="510" y="50" fill="#6db33f" font-size="9" text-anchor="middle">theme=dark</text>

  <text x="20" y="100" fill="#8b949e" font-size="9">Nodes typically mirror package structure; each node holds its own key-value pairs.</text>
</svg>

## 5. Runnable example

Scenario: a small application settings manager, evolved from storing one plain string setting, into one handling typed values with sensible defaults, into a production-style settings manager exporting/importing preferences and cleanly resetting to defaults.

### Level 1 — Basic

```java
import java.util.prefs.Preferences;

public class SettingsBasic {
    public static void main(String[] args) {
        Preferences prefs = Preferences.userNodeForPackage(SettingsBasic.class);
        prefs.put("lastOpenedFile", "/home/user/report.txt");
        System.out.println("Last opened: " + prefs.get("lastOpenedFile", "none"));
        prefs.remove("lastOpenedFile"); // cleanup for repeatable demo runs
    }
}
```

**How to run:** `java SettingsBasic.java`

This stores and retrieves exactly one plain string setting — a fine starting point, but any real settings manager needs multiple typed values (numbers, booleans) and a coherent way to reset them, neither of which this demonstrates yet.

### Level 2 — Intermediate

```java
import java.util.prefs.Preferences;

public class SettingsIntermediate {
    static final String KEY_THEME = "theme";
    static final String KEY_FONT_SIZE = "fontSize";
    static final String KEY_AUTOSAVE = "autosaveEnabled";

    public static void main(String[] args) {
        Preferences prefs = Preferences.userNodeForPackage(SettingsIntermediate.class);

        prefs.put(KEY_THEME, "dark");
        prefs.putInt(KEY_FONT_SIZE, 14);
        prefs.putBoolean(KEY_AUTOSAVE, true);

        System.out.println("Theme: " + prefs.get(KEY_THEME, "light"));
        System.out.println("Font size: " + prefs.getInt(KEY_FONT_SIZE, 12));
        System.out.println("Autosave: " + prefs.getBoolean(KEY_AUTOSAVE, false));

        prefs.remove(KEY_THEME);
        prefs.remove(KEY_FONT_SIZE);
        prefs.remove(KEY_AUTOSAVE);
    }
}
```

**How to run:** `java SettingsIntermediate.java`

Named constants for each key avoid typo-prone string literals scattered through the code, and each setting uses its natural type (`put`/`get` for strings, `putInt`/`getInt`, `putBoolean`/`getBoolean`) rather than manually converting everything to and from strings.

### Level 3 — Advanced

```java
import java.util.prefs.BackingStoreException;
import java.util.prefs.Preferences;

public class SettingsAdvanced {
    static final String KEY_THEME = "theme";
    static final String KEY_FONT_SIZE = "fontSize";
    static final String DEFAULT_THEME = "light";
    static final int DEFAULT_FONT_SIZE = 12;

    public static void main(String[] args) throws BackingStoreException {
        Preferences prefs = Preferences.userNodeForPackage(SettingsAdvanced.class);

        applySettings(prefs); // reads whatever is currently stored (defaults, initially)

        prefs.put(KEY_THEME, "dark");
        prefs.putInt(KEY_FONT_SIZE, 18);
        applySettings(prefs); // reflects the newly stored values

        resetToDefaults(prefs);
        applySettings(prefs); // back to defaults after reset

        prefs.flush(); // force settings to be written to persistent storage now
    }

    static void applySettings(Preferences prefs) {
        String theme = prefs.get(KEY_THEME, DEFAULT_THEME);
        int fontSize = prefs.getInt(KEY_FONT_SIZE, DEFAULT_FONT_SIZE);
        System.out.println("Applying settings: theme=" + theme + ", fontSize=" + fontSize);
    }

    static void resetToDefaults(Preferences prefs) throws BackingStoreException {
        prefs.clear(); // removes ALL keys under this node
    }
}
```

**How to run:** `java SettingsAdvanced.java`

`prefs.clear()` (which can throw the checked `BackingStoreException` if the underlying storage is unavailable) removes every key under this node at once, cleanly resetting to defaults, and `prefs.flush()` forces any pending changes to be written to the platform's persistent backing store immediately rather than at some unspecified later time.

## 6. Walkthrough

Execution starts in `main`, which obtains the `prefs` node for this package and calls `applySettings(prefs)` first, before anything has been stored in this run.

Inside `applySettings`, `prefs.get(KEY_THEME, DEFAULT_THEME)` looks for a stored value under `"theme"`; assuming no leftover value from a previous run, none is found, so the default `"light"` is returned. Similarly, `prefs.getInt(KEY_FONT_SIZE, DEFAULT_FONT_SIZE)` returns the default `12`. The method prints `Applying settings: theme=light, fontSize=12`.

Back in `main`, `prefs.put(KEY_THEME, "dark")` and `prefs.putInt(KEY_FONT_SIZE, 18)` write new values into the preferences node (held in memory immediately, and eventually persisted to the platform's backing store). `applySettings(prefs)` is called again: this time, `prefs.get(KEY_THEME, DEFAULT_THEME)` finds the just-stored `"dark"` and returns it instead of the default, and `getInt` similarly returns `18`. The method prints `Applying settings: theme=dark, fontSize=18`.

`main` then calls `resetToDefaults(prefs)`, which calls `prefs.clear()` — this removes both the `"theme"` and `"fontSize"` keys (and any other keys) from this node entirely. `applySettings(prefs)` is called a third time: with no stored values left, both `get` calls fall back to their defaults again, printing `Applying settings: theme=light, fontSize=12`, identical to the very first call.

Finally, `prefs.flush()` ensures the cleared (empty) state is written through to persistent storage immediately, rather than leaving it pending.

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="settings are read as defaults initially, then reflect newly stored values after put calls, then return to defaults after clear removes all keys">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#8b949e" font-size="10">1st applySettings: no stored keys -&gt; get()/getInt() return defaults -&gt; theme=light, fontSize=12</text>
  <text x="20" y="55" fill="#79c0ff" font-size="10">put(theme,"dark"), putInt(fontSize,18) -&gt; values now stored under this node</text>
  <text x="20" y="80" fill="#79c0ff" font-size="10">2nd applySettings: stored values found -&gt; theme=dark, fontSize=18</text>
  <text x="20" y="105" fill="#f85149" font-size="10">clear() removes ALL keys -&gt; 3rd applySettings: back to defaults -&gt; theme=light, fontSize=12</text>
</svg>

## 7. Gotchas & takeaways

> Preferences are not a general-purpose data store — string values and keys have platform-enforced maximum lengths (documented as a fixed cap), and the API is explicitly meant for small amounts of configuration, not application data or large user content.

- Every getter (`get`, `getInt`, `getBoolean`, etc.) requires a default value argument, returned when the key was never set — there's no missing-key exception to catch.
- `userNodeForPackage`/`systemNodeForPackage` conventionally scope preferences by package, keeping different applications' or modules' settings naturally separated.
- Changes may not be immediately persisted to the underlying backing store — call `flush()` to force persistence at a specific point, such as before the application exits.
- `clear()` removes all keys under a node at once; both it and `flush()` can throw the checked `BackingStoreException` if the underlying storage mechanism is unavailable.
- Preferences are stored per-user (or per-machine, for system preferences) by the platform itself — they are not portable application data and shouldn't be relied on for anything that needs to move between machines or be backed up as part of the application's own data.
