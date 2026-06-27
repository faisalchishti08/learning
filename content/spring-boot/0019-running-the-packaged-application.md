---
card: spring-boot
gi: 19
slug: running-the-packaged-application
title: Running the packaged application
---

## 1. What it is

**Running the packaged application** means executing the fat JAR produced by `mvn package` or `./gradlew bootJar` using `java -jar`. This is the production runtime mode — the same command you'd use in a Docker container, on a Linux VM, or in a CI smoke test.

It is distinct from development mode (`./mvnw spring-boot:run`) which compiles and runs within the Maven/Gradle process.

Core commands:

```bash
# Build
./mvnw package

# Run (default config)
java -jar target/myapp-0.0.1-SNAPSHOT.jar

# Run with property overrides
java -jar target/myapp.jar --server.port=9090

# Run with environment variable
SERVER_PORT=9090 java -jar target/myapp.jar

# Run with active profile
java -jar target/myapp.jar --spring.profiles.active=prod

# Run with JVM tuning
java -Xmx512m -Xms256m -jar target/myapp.jar

# Run with remote debug
java -agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=5005 -jar target/myapp.jar
```

## 2. Why & when

**`./mvnw spring-boot:run` vs `java -jar`:**

| Aspect | `spring-boot:run` | `java -jar` |
|---|---|---|
| Speed | Faster (no packaging) | Slightly slower (unpack + start) |
| Classpath | Maven classpath | Nested JARs in fat JAR |
| Config | `application.properties` in `src/` | `application.properties` in JAR |
| Use in | Development only | CI, staging, production |
| Hot reload | Possible with DevTools | No |

Always use `java -jar` when:
- Running in CI/CD to test the artifact that will go to production.
- Running inside a Docker container.
- Running the app in staging or production.
- Testing that `application-prod.properties` values are correctly loaded.

The practice of running the same artifact in every environment (dev uses thin classpath, prod uses fat JAR) is a common source of "works in dev, breaks in prod" bugs. Running `java -jar` locally before deploying catches these early.

## 3. Core concept

When you run `java -jar app.jar`, Spring Boot applies the full **property source priority order**:

1. Command-line args (`--server.port=9090`) — highest priority
2. `SPRING_APPLICATION_JSON` environment variable (JSON string)
3. System environment variables (`SERVER_PORT=9090`)
4. `application.properties` / `application.yml` inside the JAR
5. `@PropertySource` annotations
6. Default values in auto-configuration — lowest priority

This means the same JAR can have completely different behaviour in each environment by injecting different environment variables — no code changes, no rebuilds.

**External `application.properties`:** Spring Boot also checks the current working directory and a `config/` sub-directory for `application.properties` or `application.yml`. A file found outside the JAR overrides the bundled one:

```
/deploy/
├── myapp.jar
└── application.properties   ← overrides the bundled one
```

Or use an explicit location:
```bash
java -jar myapp.jar --spring.config.location=file:/etc/myapp/application.properties
```

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Property source priority showing command-line args overriding env vars overriding bundled application.properties overriding defaults">
  <!-- Title -->
  <text x="330" y="22" fill="#e6edf3" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">Property Source Priority (highest wins)</text>

  <!-- Rows -->
  <!-- 1: CLI args -->
  <rect x="40" y="34" width="580" height="28" rx="5" fill="#6db33f" stroke="#6db33f" stroke-width="1"/>
  <text x="56" y="53" fill="#1c2430" font-size="11" font-weight="bold" font-family="sans-serif">1. Command-line args</text>
  <text x="440" y="53" fill="#1c2430" font-size="10" font-family="monospace">java -jar app.jar --server.port=9090</text>

  <!-- 2: Env vars -->
  <rect x="40" y="70" width="580" height="28" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="56" y="89" fill="#e6edf3" font-size="11" font-family="sans-serif">2. OS environment variables</text>
  <text x="440" y="89" fill="#8b949e" font-size="10" font-family="monospace">SERVER_PORT=9090 java -jar app.jar</text>

  <!-- 3: External config -->
  <rect x="40" y="106" width="580" height="28" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="56" y="125" fill="#e6edf3" font-size="11" font-family="sans-serif">3. External application.properties (next to JAR)</text>
  <text x="440" y="125" fill="#8b949e" font-size="10" font-family="monospace">./application.properties</text>

  <!-- 4: Bundled config -->
  <rect x="40" y="142" width="580" height="28" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="56" y="161" fill="#e6edf3" font-size="11" font-family="sans-serif">4. Bundled application.properties (inside JAR)</text>
  <text x="440" y="161" fill="#8b949e" font-size="10" font-family="monospace">src/main/resources/</text>

  <!-- 5: Defaults -->
  <rect x="40" y="178" width="580" height="28" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="56" y="197" fill="#8b949e" font-size="11" font-family="sans-serif">5. Auto-configuration defaults</text>
  <text x="440" y="197" fill="#8b949e" font-size="10" font-family="monospace">server.port=8080 (built-in)</text>
</svg>

The top entry wins. The same `app.jar` runs on `8080` by default but on any port you tell it to — no rebuild needed.

## 5. Runnable example

```java
// File: RunModeDemo.java
// Shows property resolution order when running a packaged application.
// Run: java RunModeDemo.java
//   or with override: java RunModeDemo.java --server.port=9090

public class RunModeDemo {

    // Simulates Spring Boot's property resolution hierarchy
    static String resolveProperty(String key, String[] cliArgs) {
        // 1. Command-line args (highest priority)
        String cliPrefix = "--" + key + "=";
        for (String arg : cliArgs) {
            if (arg.startsWith(cliPrefix)) {
                return arg.substring(cliPrefix.length()) + " [source: CLI arg]";
            }
        }

        // 2. Environment variable (Spring Boot converts server.port → SERVER_PORT)
        String envKey = key.replace(".", "_").replace("-", "_").toUpperCase();
        String envVal = System.getenv(envKey);
        if (envVal != null) {
            return envVal + " [source: env var " + envKey + "]";
        }

        // 3. Simulate bundled application.properties
        var bundled = java.util.Map.of(
            "server.port", "8080",
            "spring.application.name", "my-app",
            "logging.level.root", "INFO"
        );
        if (bundled.containsKey(key)) {
            return bundled.get(key) + " [source: bundled application.properties]";
        }

        return "(not configured) [source: auto-configuration default]";
    }

    public static void main(String[] args) {
        System.out.println("=== Running packaged application ===");
        System.out.println("Effective configuration:\n");

        String[] keys = { "server.port", "spring.profiles.active", "spring.application.name" };
        for (String key : keys) {
            System.out.printf("  %-30s = %s%n", key, resolveProperty(key, args));
        }

        System.out.println();
        System.out.println("Run modes:");
        System.out.println("  java -jar app.jar                                → port 8080 (default)");
        System.out.println("  java -jar app.jar --server.port=9090             → port 9090 (CLI override)");
        System.out.println("  SERVER_PORT=9090 java -jar app.jar               → port 9090 (env var)");
        System.out.println("  java -jar app.jar --spring.profiles.active=prod  → loads application-prod.properties");
        System.out.println("  java -Xmx512m -jar app.jar                       → 512 MB max heap");
    }
}
```

**How to run:**
```bash
# Default behaviour
java RunModeDemo.java

# Override port via CLI arg
java RunModeDemo.java --server.port=9090
```

Expected output (default):
```
=== Running packaged application ===
Effective configuration:

  server.port                    = 8080 [source: bundled application.properties]
  spring.profiles.active         = (not configured) [source: auto-configuration default]
  spring.application.name        = my-app [source: bundled application.properties]

Run modes:
  java -jar app.jar                                → port 8080 (default)
  java -jar app.jar --server.port=9090             → port 9090 (CLI override)
  SERVER_PORT=9090 java -jar app.jar               → port 9090 (env var)
  java -jar app.jar --spring.profiles.active=prod  → loads application-prod.properties
  java -Xmx512m -jar app.jar                       → 512 MB max heap
```

Expected output (with `--server.port=9090`):
```
  server.port                    = 9090 [source: CLI arg]
```

## 6. Walkthrough

- **`cliPrefix` scan** — iterates all `args` looking for `--key=value` format. Spring Boot's real `CommandLinePropertySource` does the same. Multiple `--` args are all parsed; the last one for a given key wins.
- **`envKey` conversion** — Spring Boot's relaxed binding converts property names to env var names: `server.port` → `SERVER_PORT`, `spring.datasource.url` → `SPRING_DATASOURCE_URL`. This is called "relaxed binding." The demo shows the transformation logic.
- **`bundled` map** — represents the `src/main/resources/application.properties` embedded in the JAR. In Spring Boot's real priority order, properties from this file override auto-config defaults but lose to environment variables and CLI args.
- **No `System.getProperty`** — JVM system properties (`-Dserver.port=9090`) are also a source (between CLI args and env vars in the real Spring Boot order), but omitted here to keep the demo focused on the three most common forms.
- **Profile selection** — `--spring.profiles.active=prod` makes Spring Boot additionally load `application-prod.properties` (or `application-prod.yml`) from the same locations. Profile-specific files are merged with (and override) the base `application.properties`.

## 7. Gotchas & takeaways

> **`java -jar` vs `java -cp`:** `java -jar` honours the fat JAR's `Main-Class` manifest and ignores any `-cp` you specify. If you need to add a JAR to the classpath of a running Spring Boot fat JAR, use the `loader.path` system property instead: `java -Dloader.path=/path/to/extra.jar -jar app.jar` (only works with `PropertiesLauncher`, not the default `JarLauncher`).

> **`./target/myapp.jar` is overwritten on every `mvn package`.** If you're doing a phased rollout and keeping the previous version around, rename or copy the JAR immediately after the build: `cp target/myapp.jar /deploy/myapp-$(date +%Y%m%d).jar`.

- `java -jar app.jar` is the only command you need to run the packaged Spring Boot application.
- Override any property at runtime via `--key=value` or environment variable — no rebuild.
- `--spring.profiles.active=prod` loads `application-prod.properties` from inside the JAR, merging with `application.properties`.
- An `application.properties` file placed next to the JAR on disk overrides the bundled one — useful for ops-managed configuration.
- For production JVM tuning, `-Xmx` is almost always the first flag to set: `java -Xmx1g -jar app.jar`.
