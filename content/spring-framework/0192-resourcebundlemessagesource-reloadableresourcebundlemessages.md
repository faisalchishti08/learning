---
card: spring-framework
gi: 192
slug: resourcebundlemessagesource-reloadableresourcebundlemessages
title: "ResourceBundleMessageSource & ReloadableResourceBundleMessageSource"
---

## 1. What it is

`ResourceBundleMessageSource` and `ReloadableResourceBundleMessageSource` are Spring's two built-in `MessageSource` implementations. Both load locale-specific message bundles from `.properties` files, but differ in caching and reload behaviour.

```java
// ResourceBundleMessageSource — loads once at startup, cannot reload
@Bean
MessageSource messageSource() {
    var ms = new ResourceBundleMessageSource();
    ms.setBasenames("i18n/messages", "i18n/errors");  // multiple bundles supported
    ms.setDefaultEncoding("UTF-8");
    return ms;
}

// ReloadableResourceBundleMessageSource — can reload from disk/classpath
@Bean
MessageSource messageSource() {
    var ms = new ReloadableResourceBundleMessageSource();
    ms.setBasenames("classpath:i18n/messages");
    ms.setDefaultEncoding("UTF-8");
    ms.setCacheSeconds(10);  // reload if file changed within 10 s
    return ms;
}
```

In Spring Boot, `application.properties` configures the auto-configured `ResourceBundleMessageSource`:
```properties
spring.messages.basename=i18n/messages,i18n/errors
spring.messages.encoding=UTF-8
spring.messages.cache-duration=1m
```

## 2. Why & when

- **`ResourceBundleMessageSource`** — production default. JDK `ResourceBundle` backed; efficient startup caching; only reads classpath.
- **`ReloadableResourceBundleMessageSource`** — development or ops environments where translators update `.properties` files while the app is running; also supports non-classpath `file:` and `WEB-INF:` paths.
- **Multiple basenames** — separate bundles for app messages, validation errors, and email templates loaded together.
- **Don't use `ReloadableResourceBundleMessageSource` in memory-constrained environments** — it keeps parsed `PropertiesHolder` objects and checks `lastModified` on every cache-miss; adds file I/O overhead.

## 3. Core concept

**`ResourceBundleMessageSource`** delegates to `java.util.ResourceBundle.getBundle()`:
- Uses the JDK's bundle cache (shared across all `ResourceBundleMessageSource` instances with the same base name).
- Reads only classpath resources.
- Encoding set via `setDefaultEncoding("UTF-8")` — uses `Control.newBundle()` override to force the encoding (JDK 8 `.properties` files default to ISO-8859-1).
- No runtime reload; the JDK bundle cache persists for the JVM lifetime.

**`ReloadableResourceBundleMessageSource`** is Spring-native:
- Uses `PropertiesLoaderUtils` (not `ResourceBundle`) — supports `classpath:`, `file:`, `WEB-INF:` prefixes.
- Maintains its own `PropertiesHolder` cache with a configurable TTL (`setCacheSeconds(N)`).
- When cache expires, checks `File.lastModified()`; re-reads only if changed.
- `setCacheSeconds(-1)` → never expire (production mode).
- `setCacheSeconds(0)` → never cache (always reload, heavy I/O; avoid in production).

**`setAlwaysUseMessageFormat(boolean)`:** when `false` (default), messages with NO arguments bypass `MessageFormat` parsing (performance win for the common case). Set to `true` if your messages use `'` or `{` literally and must always be processed through `MessageFormat`.

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="rbmsa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Two implementations side by side -->
  <rect x="5" y="15" width="295" height="140" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="152" y="35" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">ResourceBundleMessageSource</text>
  <text x="152" y="52" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Delegates to JDK ResourceBundle.getBundle()</text>
  <text x="152" y="66" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Classpath-only</text>
  <text x="152" y="80" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">JDK bundle cache — loaded once at startup</text>
  <text x="152" y="94" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">No runtime reload</text>
  <text x="152" y="108" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">setDefaultEncoding("UTF-8")</text>
  <text x="152" y="122" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">setBasenames(...) — multiple bundles</text>
  <text x="152" y="136" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Best for: production</text>

  <rect x="400" y="15" width="295" height="140" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="547" y="35" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">ReloadableResourceBundleMessageSource</text>
  <text x="547" y="52" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Spring-native PropertiesLoaderUtils</text>
  <text x="547" y="66" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">classpath: / file: / WEB-INF: paths</text>
  <text x="547" y="80" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">TTL cache — checks lastModified on expiry</text>
  <text x="547" y="94" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">setCacheSeconds(N) — reload after N seconds</text>
  <text x="547" y="108" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">setCacheSeconds(-1) — never reload</text>
  <text x="547" y="122" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">setCacheSeconds(0) — always reload (dev only)</text>
  <text x="547" y="136" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Best for: dev, ops live-reload, file: resources</text>

  <!-- Common interface -->
  <rect x="250" y="70" width="105" height="25" rx="4" fill="#6db33f" opacity="0.15" stroke="#6db33f" stroke-width="1"/>
  <text x="302" y="85" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">MessageSource (interface)</text>
  <line x1="305" y1="95" x2="303" y2="88" stroke="#6db33f" stroke-width="1.5" marker-end="url(#rbmsa)"/>
  <line x1="302" y1="70" x2="270" y2="55" stroke="#6db33f" stroke-width="1" marker-end="url(#rbmsa)"/>
  <line x1="302" y1="70" x2="440" y2="55" stroke="#79c0ff" stroke-width="1" marker-end="url(#rbmsa)"/>

  <text x="350" y="168" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Spring Boot auto-configures ResourceBundleMessageSource; swap bean to switch</text>
</svg>

Both implement `MessageSource`; `ReloadableResourceBundleMessageSource` adds TTL-based file-watch reload and `file:` path support.

## 5. Runnable example

Scenario: **product catalogue service** — messages for product labels and validation errors.

### Level 1 — Basic

`ResourceBundleMessageSource` with multiple base names.

```java
// RbmsBasic.java
import org.springframework.context.support.ResourceBundleMessageSource;
import java.util.Locale;

public class RbmsBasic {
    public static void main(String[] args) throws Exception {
        // Write temporary properties files
        writeFile("msgs/products.properties",
            "product.title=Product Catalogue\nproduct.item={0} — {1}");
        writeFile("msgs/products_fr.properties",
            "product.title=Catalogue de produits\nproduct.item={0} — {1}");
        writeFile("msgs/errors.properties",
            "error.notfound=Product {0} not found\nerror.outofstock={0} is out of stock");
        writeFile("msgs/errors_fr.properties",
            "error.notfound=Produit {0} introuvable\nerror.outofstock={0} est en rupture de stock");

        var ms = new ResourceBundleMessageSource();
        ms.setBasenames("msgs/products", "msgs/errors"); // two separate bundles loaded together
        ms.setDefaultEncoding("UTF-8");
        ms.setFallbackToSystemLocale(false);

        for (Locale locale : new Locale[]{Locale.ENGLISH, Locale.FRENCH}) {
            System.out.printf("[%s] title=%s%n",
                locale.getLanguage(),
                ms.getMessage("product.title", null, locale));
            System.out.printf("[%s] item=%s%n",
                locale.getLanguage(),
                ms.getMessage("product.item", new Object[]{"SKU-001", "Laptop"}, locale));
            System.out.printf("[%s] err=%s%n",
                locale.getLanguage(),
                ms.getMessage("error.notfound", new Object[]{"SKU-XYZ"}, locale));
        }
        cleanup("msgs");
    }
    static void writeFile(String path, String content) throws Exception {
        var f = new java.io.File(path); f.getParentFile().mkdirs();
        java.nio.file.Files.writeString(f.toPath(), content);
    }
    static void cleanup(String dir) {
        java.util.Arrays.stream(new java.io.File(dir).listFiles()).forEach(java.io.File::delete);
        new java.io.File(dir).delete();
    }
}
```

How to run: `java RbmsBasic.java`

`setBasenames("msgs/products", "msgs/errors")` registers two bundles; resolution checks bundles in order. `setFallbackToSystemLocale(false)` ensures the JVM locale doesn't interfere with missing-locale fallback — always falls to the base bundle.

### Level 2 — Intermediate

`ReloadableResourceBundleMessageSource` with `setCacheSeconds(5)`; demonstrates cache TTL reload.

```java
// RbmsIntermediate.java
import org.springframework.context.support.ReloadableResourceBundleMessageSource;
import java.nio.file.*;
import java.util.Locale;

public class RbmsIntermediate {
    public static void main(String[] args) throws Exception {
        Path propsFile = Path.of("msgs2/app.properties");
        Files.createDirectories(propsFile.getParent());
        Files.writeString(propsFile, "status.msg=Service is UP (v1)\n");

        var ms = new ReloadableResourceBundleMessageSource();
        ms.setBasenames("msgs2/app");   // no classpath: prefix → reads relative to working dir
        ms.setDefaultEncoding("UTF-8");
        ms.setCacheSeconds(2);          // re-check file every 2 seconds

        System.out.println("Read 1: " + ms.getMessage("status.msg", null, Locale.ENGLISH));

        // Update the file AFTER cache TTL
        Thread.sleep(2200);
        Files.writeString(propsFile, "status.msg=Service is UP (v2 — reloaded)\n");

        System.out.println("Read 2: " + ms.getMessage("status.msg", null, Locale.ENGLISH));

        Files.delete(propsFile);
        Files.delete(propsFile.getParent());
    }
}
```

How to run: `java RbmsIntermediate.java`

After `cacheSeconds=2` elapses and the file changes, the next `getMessage` call re-reads from disk. `ResourceBundleMessageSource` cannot do this — it relies on the JDK bundle cache which is never invalidated at runtime. Use `file:msgs2/app` prefix to force absolute path loading; without prefix, Spring resolves relative to the classpath/working directory.

### Level 3 — Advanced

Spring context; `ReloadableResourceBundleMessageSource`; `setCacheMillis(-1)` in production; custom `Control` equivalent via `setFileEncodings`; multiple basenames with hierarchy.

```java
// RbmsAdvanced.java
import org.springframework.context.MessageSource;
import org.springframework.context.annotation.*;
import org.springframework.context.support.*;
import java.nio.file.*;
import java.util.*;

@Configuration
class MsAdvancedConfig {
    // Parent: shared global messages
    @Bean
    MessageSource parentMessageSource() throws Exception {
        Path f = Path.of("msgs3/global.properties");
        Files.createDirectories(f.getParent());
        Files.writeString(f, "app.version=3.1.0\napp.name=My App\n");
        var parent = new ReloadableResourceBundleMessageSource();
        parent.setBasenames("msgs3/global");
        parent.setDefaultEncoding("UTF-8");
        parent.setCacheSeconds(-1); // never expire — production mode
        return parent;
    }

    // Child: module-specific messages, delegates to parent for missing keys
    @Bean
    MessageSource messageSource() throws Exception {
        writeProps("msgs3/module.properties",
            "module.greeting=Welcome to {0}!\nmodule.error=Error code {0}: {1}\n");
        writeProps("msgs3/module_es.properties",
            "module.greeting=¡Bienvenido a {0}!\nmodule.error=Error {0}: {1}\n");

        var child = new ReloadableResourceBundleMessageSource();
        child.setBasenames("msgs3/module");
        child.setDefaultEncoding("UTF-8");
        child.setCacheSeconds(30);
        child.setParentMessageSource(parentMessageSource());  // fallback chain
        return child;
    }

    static void writeProps(String path, String content) throws Exception {
        var f = new java.io.File(path); f.getParentFile().mkdirs();
        java.nio.file.Files.writeString(f.toPath(), content);
    }
}

public class RbmsAdvanced {
    public static void main(String[] args) throws Exception {
        var ctx = new AnnotationConfigApplicationContext(MsAdvancedConfig.class);
        var ms = ctx.getBean(MessageSource.class);

        // Module-specific keys
        for (Locale locale : new Locale[]{Locale.ENGLISH, new Locale("es")}) {
            System.out.printf("[%s] greeting: %s%n",
                locale.getLanguage(),
                ms.getMessage("module.greeting", new Object[]{"Spring"}, locale));
        }

        // Parent key — not in module bundle, resolved via parent
        System.out.println("version: " + ms.getMessage("app.version", null, Locale.ENGLISH));
        System.out.println("name:    " + ms.getMessage("app.name",    null, Locale.ENGLISH));

        ctx.close();
        // Cleanup
        Path dir = Path.of("msgs3");
        Files.walk(dir).sorted(Comparator.reverseOrder()).map(Path::toFile).forEach(java.io.File::delete);
    }
}
```

How to run: `java RbmsAdvanced.java`

`setParentMessageSource()` chains two `MessageSource` instances — if the child doesn't have a key, it delegates to the parent. This is a `HierarchicalMessageSource` feature both implementations support. Common pattern: global shared messages (parent) + module-specific messages (child).

## 6. Walkthrough

Tracing `ms.getMessage("app.version", null, Locale.ENGLISH)` (key only in parent):

**Step 1 — Child `ReloadableResourceBundleMessageSource` checks its cache for `msgs3/module.properties`.**
- Found in cache, not expired.
- Looks up key `app.version` → not found.

**Step 2 — Child checks `msgs3/module_en.properties`** — not found (no locale-specific file for English).

**Step 3 — Child delegates to parent** (`parentMessageSource()`).

**Step 4 — Parent checks `msgs3/global.properties`** → found: `"3.1.0"`.

**Step 5 — Returns `"3.1.0"`** to the caller.

Tracing `ms.getMessage("app.version", null, Locale.ENGLISH)` after the parent's file is updated and `cacheSeconds=-1`:
- Parent never reloads; still returns the old value.
- Use `clearCache()` on the parent to force reload, or restart the application.

## 7. Gotchas & takeaways

> **`setCacheSeconds(0)` reloads on EVERY request.** This is a development shortcut, not a production setting — it adds file I/O to every message resolution call. Use `setCacheSeconds(30)` or `-1` in production.

> **`ResourceBundleMessageSource` uses the JDK bundle cache — you cannot clear it.** If you update a classpath `.properties` file at runtime (e.g., in a fat JAR), the change is invisible until the JVM restarts. For live-reload, you must use `ReloadableResourceBundleMessageSource`.

- **Encoding trap:** JDK `ResourceBundle` prior to Java 9 defaults to ISO-8859-1. Call `ms.setDefaultEncoding("UTF-8")` always — otherwise accented characters (`é`, `ü`, `ñ`) become garbage. Since Java 9, `.properties` files default to UTF-8, but Spring's `setDefaultEncoding` call is still the safest explicit override.
- **Spring Boot:** set `spring.messages.use-code-as-default-message=true` to return the key itself when no translation is found, instead of throwing `NoSuchMessageException`. Useful during development.
- **`alwaysUseMessageFormat=false` (default):** messages with no arguments skip `MessageFormat` entirely. A message containing `{` without corresponding `getMessage(..., args, ...)` call works fine. Setting to `true` causes `MessageFormat` to parse ALL messages, breaking messages with raw `{` characters.
- **Testing:** use `StaticMessageSource` or `ReloadableResourceBundleMessageSource` with `setCacheSeconds(0)` + test-scoped property files for fast locale tests without classpath setup.
