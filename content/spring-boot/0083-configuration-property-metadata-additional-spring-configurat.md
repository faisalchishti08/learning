---
card: spring-boot
gi: 83
slug: configuration-property-metadata-additional-spring-configurat
title: Configuration property metadata (additional-spring-configuration-metadata.json)
---

## 1. What it is

When you add `spring-boot-configuration-processor` to your build, the Java annotation processor scans every `@ConfigurationProperties` class at **compile time** and generates a file called `spring-configuration-metadata.json` inside `META-INF/`. This JSON file describes every property: its name, type, default value, description (from Javadoc), and deprecation status.

IDEs (IntelliJ IDEA, Eclipse Spring Tools, VS Code with the Spring Boot Extension Pack) read this metadata to provide:

- **Auto-complete** for property keys while you type in `application.properties` or `application.yml`.
- **Documentation pop-ups** showing the property description and type.
- **Deprecation warnings** with migration hints when a renamed or removed property is used.

For properties that cannot be derived from source code — dynamically computed properties, third-party library properties, or properties defined outside a `@ConfigurationProperties` class — you can hand-author a companion file: **`additional-spring-configuration-metadata.json`**. Spring Boot merges both files at build time.

## 2. Why & when

Auto-complete for configuration files is a quality-of-life feature that matters most in two scenarios:

1. **Your own application** — developers on your team get IDE hints for your custom properties without memorising them.
2. **Spring Boot starters / libraries** — the metadata ships inside the JAR and powers auto-complete for every consumer of your library. This is how `spring-boot-autoconfigure` itself provides hints for hundreds of `spring.*` properties.

`additional-spring-configuration-metadata.json` is needed when:

- A property is defined in a framework or library that doesn't use `@ConfigurationProperties` (e.g., a legacy `PropertySource` based approach).
- The property value is computed dynamically and cannot be inferred from source.
- You want to document a property whose description the annotation processor cannot derive (no Javadoc) without changing the source file.
- You need to mark a property as deprecated and provide a replacement hint.

## 3. Core concept

The annotation processor `spring-boot-configuration-processor` implements `javax.annotation.processing.Processor`. During compilation it:

1. Finds all classes annotated with `@ConfigurationProperties`.
2. Reads the field types, default values (from field initialisers), and Javadoc comments.
3. Writes `META-INF/spring-configuration-metadata.json` into the compiled output.

The JSON schema has three top-level arrays:

- **`groups`** — describe the owning class (the `@ConfigurationProperties` bean itself).
- **`properties`** — describe each individual property: `name`, `type`, `description`, `defaultValue`, `deprecation`.
- **`hints`** — provide value suggestions (e.g., a list of valid enum values) and value providers (e.g., a class-name completer).

`additional-spring-configuration-metadata.json` uses the **exact same schema**. At build time the processor merges the hand-authored file with the generated file. Entries in the additional file take precedence, so you can override or supplement auto-generated entries.

Both files are read-only artefacts consumed by IDEs; they have no effect at runtime.

## 4. Diagram

<svg viewBox="0 0 700 340" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Build-time metadata pipeline: annotation processor reads @ConfigurationProperties source, merges with additional metadata, writes spring-configuration-metadata.json for IDE consumption">
  <rect x="10" y="10" width="680" height="320" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="350" y="36" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Configuration Metadata Pipeline (Build Time)</text>

  <!-- Source files -->
  <rect x="25" y="55" width="155" height="70" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="103" y="76" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Java Source</text>
  <text x="103" y="94" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">@ConfigurationProperties</text>
  <text x="103" y="110" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">+ Javadoc comments</text>

  <!-- Additional file -->
  <rect x="25" y="145" width="155" height="60" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="103" y="164" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">additional-spring-</text>
  <text x="103" y="180" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">configuration-metadata</text>
  <text x="103" y="196" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">.json (hand-authored)</text>

  <!-- Arrows to processor -->
  <line x1="181" y1="88" x2="238" y2="130" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ma1)"/>
  <line x1="181" y1="172" x2="238" y2="150" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ma1)"/>
  <defs>
    <marker id="ma1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ma2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ma3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Annotation Processor -->
  <rect x="240" y="105" width="170" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="325" y="130" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Annotation Processor</text>
  <text x="325" y="148" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">spring-boot-configuration</text>
  <text x="325" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">-processor</text>

  <!-- Arrow to output -->
  <line x1="412" y1="135" x2="460" y2="135" stroke="#6db33f" stroke-width="2" marker-end="url(#ma2)"/>

  <!-- Generated metadata -->
  <rect x="462" y="95" width="208" height="80" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="566" y="116" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">META-INF/</text>
  <text x="566" y="132" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">spring-configuration-</text>
  <text x="566" y="148" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">metadata.json</text>
  <text x="566" y="166" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(merged, shipped in JAR)</text>

  <!-- Arrow to IDE -->
  <line x1="566" y1="177" x2="566" y2="220" stroke="#79c0ff" stroke-width="2" marker-end="url(#ma3)"/>

  <!-- IDE box -->
  <rect x="440" y="222" width="260" height="70" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="570" y="244" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">IDE</text>
  <text x="570" y="262" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">auto-complete • docs • deprecation</text>
  <text x="570" y="278" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">hints in application.properties/yml</text>

  <!-- Note: runtime irrelevant -->
  <rect x="25" y="230" width="390" height="40" rx="6" fill="#0d1117" stroke="#30363d" stroke-width="1"/>
  <text x="220" y="246" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">The JSON file is a build artefact.</text>
  <text x="220" y="261" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">It has no effect at runtime — only IDEs read it.</text>
</svg>

The annotation processor is a pure build-time tool. The JSON it produces ships inside the JAR so that anyone depending on your library also gets IDE support.

## 5. Runnable example

**Step 1 — add the processor to your build**

```xml
<!-- pom.xml — annotationProcessorPaths keeps it off the compile classpath -->
<build>
  <plugins>
    <plugin>
      <groupId>org.apache.maven.plugins</groupId>
      <artifactId>maven-compiler-plugin</artifactId>
      <configuration>
        <annotationProcessorPaths>
          <path>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-configuration-processor</artifactId>
          </path>
        </annotationProcessorPaths>
      </configuration>
    </plugin>
  </plugins>
</build>
```

For Gradle:

```groovy
// build.gradle
dependencies {
    annotationProcessor 'org.springframework.boot:spring-boot-configuration-processor'
}
```

**Step 2 — write a `@ConfigurationProperties` class with Javadoc**

```java
// src/main/java/com/example/demo/MailProperties.java
package com.example.demo;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * Mail sender configuration for the demo application.
 */
@Component
@ConfigurationProperties(prefix = "demo.mail")
public class MailProperties {

    /** SMTP host to connect to. */
    private String host = "localhost";

    /** SMTP port number. */
    private int port = 25;

    /** Whether to require authentication. */
    private boolean auth = false;

    public String getHost()          { return host; }
    public void setHost(String h)    { this.host = h; }
    public int getPort()             { return port; }
    public void setPort(int p)       { this.port = p; }
    public boolean isAuth()          { return auth; }
    public void setAuth(boolean a)   { this.auth = a; }
}
```

**Step 3 — hand-author additional metadata** for a property that isn't in `MailProperties` source (e.g., a legacy property you want to document and deprecate):

```json
// src/main/resources/META-INF/additional-spring-configuration-metadata.json
{
  "properties": [
    {
      "name": "demo.mail.legacy-server",
      "type": "java.lang.String",
      "description": "Deprecated SMTP server address. Use demo.mail.host instead.",
      "deprecation": {
        "replacement": "demo.mail.host",
        "level": "warning"
      }
    },
    {
      "name": "demo.mail.from",
      "type": "java.lang.String",
      "description": "Default sender address used for all outgoing mail.",
      "defaultValue": "noreply@example.com"
    }
  ],
  "hints": [
    {
      "name": "demo.mail.host",
      "values": [
        { "value": "localhost", "description": "Local mail server (development)" },
        { "value": "smtp.mailgun.org", "description": "Mailgun SMTP relay" },
        { "value": "smtp.sendgrid.net", "description": "SendGrid SMTP relay" }
      ]
    }
  ]
}
```

**Step 4 — build and inspect**

```bash
./mvnw compile
# The processor writes:
# target/classes/META-INF/spring-configuration-metadata.json
cat target/classes/META-INF/spring-configuration-metadata.json
```

**How to run:** After `./mvnw compile`, open `application.properties` in IntelliJ IDEA and type `demo.mail.` — you should see auto-complete for `host`, `port`, `auth`, `from`, and `legacy-server`, with `legacy-server` shown as deprecated.

## 6. Walkthrough

- **`spring-boot-configuration-processor`** is declared as an annotation processor, not a regular dependency. This keeps it off the runtime classpath — it runs only during `javac` (or the Gradle/Maven equivalent) and produces the JSON as a side-effect of compilation.
- **Javadoc on `host`, `port`, `auth`** — the processor reads the Javadoc comment on each field and writes it into the `description` field of the generated JSON. That description appears in IDE tooltip pop-ups. Without Javadoc the description is absent.
- **Default values** — the field initialisers (`"localhost"`, `25`, `false`) are captured and written as `defaultValue` in the JSON. IDEs show this so developers know what value they'll get if they omit the property.
- **`additional-spring-configuration-metadata.json`** lives in `src/main/resources/META-INF/`. The processor detects it during compilation and merges it with the generated content into the single output file.
- **`demo.mail.legacy-server` deprecation entry** — the `"level": "warning"` and `"replacement": "demo.mail.host"` fields cause IntelliJ to show a strikethrough on `demo.mail.legacy-server` in `application.properties` with a tooltip pointing to the replacement.
- **`hints` for `demo.mail.host`** — the `hints` array tells the IDE to offer `localhost`, `smtp.mailgun.org`, and `smtp.sendgrid.net` as suggested completions when the cursor is positioned after `demo.mail.host=`.
- The **merged output** in `target/classes/META-INF/spring-configuration-metadata.json` is what gets packaged into the JAR. Consumers of the JAR (other Spring Boot applications that depend on it) also benefit from the auto-complete.

## 7. Gotchas & takeaways

> **The annotation processor runs at compile time, not at runtime.** If you add or rename a property and want the IDE to reflect the change, you must recompile (or trigger a build). The JSON in the JAR is a snapshot from the last compilation — stale metadata causes IDE hints to lag behind your source.

> **Inner classes and Java records require no extra setup.** The processor recurses into nested types automatically, generating metadata for every property in the object graph, including deeply nested fields.

- Place `additional-spring-configuration-metadata.json` in `src/main/resources/META-INF/` — not in `src/test/resources/` and not in the project root. The processor only reads it from the resource root.
- The `deprecation.level` field accepts `"warning"` (property still works, IDE shows a hint) or `"error"` (property is removed, IDE shows an error). Use `"warning"` when you have a migration window; use `"error"` after removal.
- If you use Lombok, the processor cannot see the field types from `@Data`-generated getters in all configurations. Prefer explicit getters/setters or use the `spring-boot-configuration-processor` in combination with Lombok's `@ConfigurationProperties` support.
- For `hints`, the `providers` array (not shown in the example) can reference a class-name completer (`"spring-bean-reference"`) or a logger-name completer — useful for properties that should name a Spring bean or a logger.
- The processor is optional — without it the application works perfectly. Its only purpose is improving the developer experience in IDEs.
