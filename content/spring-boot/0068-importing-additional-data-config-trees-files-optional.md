---
card: spring-boot
gi: 68
slug: importing-additional-data-config-trees-files-optional
title: Importing additional data (config trees, files, optional)
---

## 1. What it is

`spring.config.import` supports three main source types beyond plain property files:

- **`file:`** — loads a single `.properties` or `.yml` file from the filesystem.
- **`configtree:`** — reads an entire directory where **each filename is a property key** and the file's contents are the value. This maps perfectly to how Kubernetes mounts Secrets and ConfigMaps.
- **`optional:`** — a prefix you attach to any source to suppress startup failure when the source is absent.

Together these three patterns cover the realistic range of "how config reaches a running container."

## 2. Why & when

**Config trees** exist because Kubernetes does not inject secrets as environment variables by default (that's considered less secure). Instead it mounts a `Secret` or `ConfigMap` as a directory. You end up with something like:

```
/run/secrets/
  db.password        ← file, content is "s3cr3t"
  db.username        ← file, content is "admin"
```

Before config-tree support you had to write custom code to read those files. Now a single `spring.config.import=configtree:/run/secrets/` maps them straight into Spring's Environment as `db.password` and `db.username`.

**`optional:`** matters for local development: you don't want a developer to create `/run/secrets/` on their laptop. Mark it optional and the app starts normally without it; in production the directory is always present, so the properties are always loaded.

## 3. Core concept

Analogy: think of a config tree as a **filing cabinet** where the drawer label is the property key and the paper inside is the value. A plain `file:` import is one document you hand to Spring. A `configtree:` import is handing Spring the entire cabinet — it reads every drawer automatically.

How Spring processes a config tree:

1. It scans the directory recursively.
2. Each file path **relative to the tree root** becomes the property key, with `/` replaced by `.` (so `db/password` → `db.password`).
3. The file's contents (trimmed of trailing whitespace) become the value.
4. Files beginning with `..` (Kubernetes metadata files) are ignored automatically.

The `optional:` prefix applies to any scheme: `optional:file:`, `optional:configtree:`, `optional:classpath:`, etc. Without `optional:`, a missing source throws `ConfigDataLocationNotFoundException` and stops the JVM.

## 4. Diagram

<svg viewBox="0 0 700 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Config tree: directory files mapped to Spring Environment properties">
  <rect width="700" height="280" rx="10" fill="#0d1117"/>

  <!-- Kubernetes Secret / directory -->
  <rect x="20" y="30" width="220" height="175" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="56" fill="#79c0ff" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">Mounted directory</text>
  <text x="130" y="73" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">/run/secrets/</text>

  <!-- files -->
  <rect x="40" y="85" width="180" height="28" rx="4" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="55" y="104" fill="#6db33f" font-size="11" font-family="monospace">db/password</text>
  <text x="195" y="104" fill="#e6edf3" font-size="10" text-anchor="end" font-family="monospace">s3cr3t</text>

  <rect x="40" y="120" width="180" height="28" rx="4" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="55" y="139" fill="#6db33f" font-size="11" font-family="monospace">db/username</text>
  <text x="195" y="139" fill="#e6edf3" font-size="10" text-anchor="end" font-family="monospace">admin</text>

  <rect x="40" y="155" width="180" height="28" rx="4" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="55" y="174" fill="#6db33f" font-size="11" font-family="monospace">api.key</text>
  <text x="195" y="174" fill="#e6edf3" font-size="10" text-anchor="end" font-family="monospace">abc123</text>

  <!-- Arrow: configtree: import -->
  <line x1="245" y1="118" x2="330" y2="118" stroke="#6db33f" stroke-width="2" marker-end="url(#hga)"/>
  <text x="287" y="112" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">configtree:</text>

  <!-- Spring Environment -->
  <rect x="335" y="50" width="225" height="155" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="448" y="76" fill="#6db33f" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">Spring Environment</text>

  <rect x="355" y="88" width="185" height="28" rx="4" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="370" y="107" fill="#79c0ff" font-size="11" font-family="monospace">db.password=s3cr3t</text>

  <rect x="355" y="122" width="185" height="28" rx="4" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="370" y="141" fill="#79c0ff" font-size="11" font-family="monospace">db.username=admin</text>

  <rect x="355" y="156" width="185" height="28" rx="4" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="370" y="175" fill="#79c0ff" font-size="11" font-family="monospace">api.key=abc123</text>

  <!-- optional label at bottom -->
  <rect x="20" y="225" width="220" height="36" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="130" y="247" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">optional: → skip if missing</text>

  <!-- note -->
  <text x="350" y="250" fill="#8b949e" font-size="10" font-family="sans-serif">/ in filename → . in property key</text>

  <defs>
    <marker id="hga" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Each file inside the mounted directory becomes a Spring property. Subdirectory separators (`/`) are converted to dots (`.`), so `db/password` maps to `db.password`. Files prefixed with `..` (Kubernetes internal metadata) are silently skipped.

## 5. Runnable example

```java
// File: ConfigTreeDemo.java
// Spring Boot app — run with: ./gradlew bootRun  OR  mvn spring-boot:run
//
// Before running, create the simulated config tree:
//   mkdir -p /tmp/demo-secrets/db
//   echo -n "s3cr3t"  > /tmp/demo-secrets/db/password
//   echo -n "admin"   > /tmp/demo-secrets/db/username
//   echo -n "abc123"  > /tmp/demo-secrets/api.key
//
// src/main/resources/application.properties:
//   spring.config.import=optional:configtree:/tmp/demo-secrets/,optional:file:/tmp/overrides.properties

package com.example;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class ConfigTreeDemo implements CommandLineRunner {

    // Keys derived from configtree: /tmp/demo-secrets/db/password
    @Value("${db.password:NOT_SET}")
    private String dbPassword;

    @Value("${db.username:NOT_SET}")
    private String dbUsername;

    // Key derived from configtree: /tmp/demo-secrets/api.key
    @Value("${api.key:NOT_SET}")
    private String apiKey;

    // Key from the optional file: import — won't exist unless you create /tmp/overrides.properties
    @Value("${app.override:no-override}")
    private String override;

    public static void main(String[] args) {
        SpringApplication.run(ConfigTreeDemo.class, args);
    }

    @Override
    public void run(String... args) {
        System.out.println("db.username : " + dbUsername);
        System.out.println("db.password : " + dbPassword);
        System.out.println("api.key     : " + apiKey);
        System.out.println("app.override: " + override);
    }
}
```

**How to run:**
1. Create the config tree files with the `mkdir` / `echo` commands above.
2. Add the `spring.config.import` line to `application.properties`.
3. Run `./gradlew bootRun`. All four values print.
4. Remove `/tmp/demo-secrets/` and rerun — `optional:` prevents a crash; all values show `NOT_SET`.

## 6. Walkthrough

- **`mkdir -p /tmp/demo-secrets/db`** — creates a two-level directory. The `db/` subdirectory becomes a key prefix, so `db/password` → `db.password` in the Environment.
- **`echo -n "s3cr3t" > /tmp/demo-secrets/db/password`** — the `-n` flag suppresses a trailing newline; Spring trims trailing whitespace anyway, but `-n` is the safest habit to match what Kubernetes Secret mounts produce.
- **`spring.config.import=optional:configtree:/tmp/demo-secrets/`** — the trailing `/` signals a directory. Without it, Spring tries to treat the path as a file and fails. The `optional:` prefix makes the import survive a missing directory.
- **`optional:file:/tmp/overrides.properties`** — a plain file import, also optional. Demonstrates that you can mix `configtree:` and `file:` imports in a single comma-separated list.
- **`@Value("${db.password:NOT_SET}")`** — the `NOT_SET` default fires when the property is absent (config tree directory missing). In production the Kubernetes Secret mount ensures the property is always present.
- **Key naming** — Spring replaces each `/` in the relative path with `.`. Kubernetes Secret key names use `-` by default (e.g., `db-password`); if you use dashes, the property key becomes `db-password`, not `db.password`. Design your Secret keys accordingly or use Spring's relaxed binding.

## 7. Gotchas & takeaways

> Always end the `configtree:` path with a **trailing slash** (`configtree:/run/secrets/`). Without it, Spring Boot cannot determine that you are specifying a directory and will throw a confusing error at startup.

> Kubernetes mounts Secret files **without execute bits** and with contents that look like plain text — no equals signs, no colons. Spring reads the raw content of the file as the value; nothing is interpreted or parsed. This is different from a `.properties` file import and trips people up when they expect `key=value` format inside the tree files.

- `configtree:` is the idiomatic Spring Boot integration point for Kubernetes Secrets and ConfigMaps mounted as volumes.
- Files prefixed with `..` (e.g., `..data`, `..2024_01_01`) are metadata symlinks created by Kubernetes and are automatically ignored by Spring Boot.
- `optional:` is not "hide errors" — it is a deliberate contract that the source is legitimately absent in some environments (typically local dev). Never add it just to silence a broken production path.
- Multiple imports are comma-separated in one `spring.config.import` value, or you can list them on separate lines in YAML with the list syntax (`- file:...`).
- Config tree properties participate in relaxed binding and profile activation like any other property source.
