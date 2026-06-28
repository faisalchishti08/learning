---
card: spring-boot
gi: 63
slug: command-line-properties
title: Command-line properties
---

## 1. What it is

When you launch a Spring Boot application with `java -jar app.jar`, any argument that starts with `--` and contains `=` is treated as a **command-line property** and injected into the `Environment` at the highest production-time priority:

```bash
java -jar app.jar --server.port=9090 --spring.datasource.url=jdbc:mysql://prod-db/shop
```

Those two arguments set `server.port` and `spring.datasource.url` for that one run — no file is edited, no environment variable is set, no rebuild is needed.

Command-line properties are the topmost source in the precedence stack (position #11 in the full list, above env vars and config files, but below test-only sources like `@TestPropertySource`).

## 2. Why & when

Command-line properties shine in three scenarios:

- **Ad-hoc local testing.** "I want to start on port 9091 right now so I can run two instances simultaneously." One flag, no file change, no git diff.
- **CI/CD pipelines.** A pipeline script passes `--spring.profiles.active=staging` without needing a shell-level environment variable — especially useful when the pipeline tool has easier access to positional arguments than to env var injection.
- **Controlled overrides in scripts.** A start script can pass `--logging.level.root=DEBUG` for a diagnostic run, then remove it for normal operation — the change is visible and auditable in the script.

Avoid command-line properties when:

- The value must persist across restarts (use `application.properties` or an env var instead).
- The value contains secrets that would appear in process-listing tools like `ps aux` — use env vars or a secrets manager.

## 3. Core concept

Think of `--key=value` CLI args like **sticky notes on a whiteboard**. The whiteboard already has instructions (your config files), but a sticky note placed on top covers any instruction beneath it. When you're done with the sticky note you just remove it — the underlying instruction is unchanged.

Spring Boot's `SpringApplication` parses every argument string of the form `--key=value` using a special `SimpleCommandLinePropertySource` and places it at the top of the `Environment`'s source list. The parsing rules are:

- `--key=value` → property `key` with value `value`.
- `--flag` (no `=`) → property `flag` with value `"true"`.
- Arguments not starting with `--` are passed through as non-option args (accessible via `ApplicationArguments`), not added as properties.

Multiple values for the same key are supported by repeating the flag: `--my.list=a --my.list=b` produces a list `[a, b]`.

You can also **disable** command-line property parsing entirely — useful when running tests that pass args for other purposes:

```java
SpringApplication app = new SpringApplication(MyApp.class);
app.setAddCommandLineProperties(false);
app.run(args);
```

## 4. Diagram

<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Command-line arguments parsed into the highest-priority property source">
  <defs>
    <marker id="arr63" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/>
    </marker>
    <marker id="arr63b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/>
    </marker>
  </defs>

  <!-- Terminal box -->
  <rect x="20" y="30" width="280" height="70" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="36" y="55" fill="#6db33f" font-size="12" font-family="monospace">$ java -jar app.jar \</text>
  <text x="36" y="73" fill="#6db33f" font-size="12" font-family="monospace">    --server.port=9090 \</text>
  <text x="36" y="91" fill="#6db33f" font-size="12" font-family="monospace">    --app.feature=true</text>

  <!-- Arrow: terminal -> parser -->
  <line x1="304" y1="65" x2="370" y2="65" stroke="#6db33f" stroke-width="2" marker-end="url(#arr63)"/>

  <!-- Parser box -->
  <rect x="374" y="40" width="200" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="474" y="62" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">SimpleCommandLine</text>
  <text x="474" y="80" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">PropertySource</text>

  <!-- Property source stack -->
  <rect x="130" y="150" width="420" height="30" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="340" y="170" fill="#6db33f" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">CLI args  ← WINS (highest priority)</text>

  <rect x="130" y="185" width="420" height="25" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="340" y="202" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">OS env vars</text>

  <rect x="130" y="215" width="420" height="25" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="340" y="232" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">application.properties</text>

  <!-- Arrow: parser -> stack -->
  <line x1="474" y1="94" x2="340" y2="146" stroke="#79c0ff" stroke-width="2" marker-end="url(#arr63b)"/>
  <text x="440" y="128" fill="#79c0ff" font-size="11" font-family="sans-serif">placed at top</text>
</svg>

*`SimpleCommandLinePropertySource` sits at the very top of the production-time source stack. Any key it defines shadows the same key in env vars or config files.*

## 5. Runnable example

```java
// CliPropsDemo.java — Spring Boot 3.x project
// Shows which source won for server.port and a custom property

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
@RestController
public class CliPropsDemo {

    @Value("${server.port}")
    private int port;

    @Value("${app.mode:normal}")
    private String mode;

    @GetMapping("/info")
    public String info() {
        return "port=" + port + "  mode=" + mode;
    }

    public static void main(String[] args) {
        SpringApplication.run(CliPropsDemo.class, args);
    }
}
```

`src/main/resources/application.properties`:
```properties
server.port=8080
app.mode=normal
```

**How to run:**

```bash
# 1. Default — file values apply
./mvnw spring-boot:run
# http://localhost:8080/info => port=8080  mode=normal

# 2. Override port via CLI arg
./mvnw spring-boot:run \
  -Dspring-boot.run.arguments="--server.port=9090"
# http://localhost:9090/info => port=9090  mode=normal

# 3. Override both
./mvnw spring-boot:run \
  -Dspring-boot.run.arguments="--server.port=9091 --app.mode=debug"
# http://localhost:9091/info => port=9091  mode=debug

# 4. With a packaged JAR
./mvnw package -q
java -jar target/*.jar --server.port=9092 --app.mode=perf
# http://localhost:9092/info => port=9092  mode=perf
```

## 6. Walkthrough

1. `application.properties` sets `server.port=8080` and `app.mode=normal` — the baseline committed defaults.
2. In run 2, `--server.port=9090` is parsed by `SimpleCommandLinePropertySource`. The `Environment` now has two definitions of `server.port`; CLI is at a higher position in the source list, so `9090` wins.
3. `app.mode` has no CLI arg in run 2, so the file's `normal` fills in unchallenged.
4. In run 4 (fat JAR), the same `--key=value` syntax works identically. The JAR's embedded `application.properties` is source #3; CLI args are source #11. Source #11 wins.
5. `@Value("${app.mode:normal}")` — the `:normal` inline default is a fallback of last resort. It only applies if *zero* property sources define `app.mode`. Since the file defines it, the inline default is never reached in these runs.

## 7. Gotchas & takeaways

> Anything passed as `--key=value` shows up in `ps aux` or any process inspector. Never pass passwords or tokens this way — use environment variables set via a secrets manager or a Kubernetes secret instead.

> When running with `./mvnw spring-boot:run`, args must be passed via `-Dspring-boot.run.arguments=` rather than appended directly, because Maven consumes the top-level args before Spring Boot sees them. With a packaged JAR (`java -jar app.jar --key=val`) the args reach Spring Boot directly.

- `--flag` (no `=`) is a boolean shorthand: it sets `flag=true`.
- Multiple values: `--my.list=a --my.list=b` produces a list; repeat the flag for each element.
- To stop Spring Boot from consuming `--` args at all, call `app.setAddCommandLineProperties(false)` — useful when test harnesses pass custom `--` flags for their own purposes.
- CLI args are ideal for single-run overrides; if you need the value on every restart, put it in an env var or the config file instead.
- CLI args have the highest priority of any production-time source, beating env vars and all config files.
