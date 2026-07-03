---
card: spring-framework
gi: 139
slug: urlresource-classpathresource-filesystemresource
title: "UrlResource, ClassPathResource, FileSystemResource"
---

## 1. What it is

Three of the most commonly used `Resource` implementations in Spring:

- **`ClassPathResource`** — resolves a path from the classpath. Works inside JARs. Location prefix: `classpath:`.
- **`FileSystemResource`** — resolves a `java.io.File` or `java.nio.file.Path`. Supports `WritableResource`. Location prefix: `file:`.
- **`UrlResource`** — wraps any `java.net.URL`: `http://`, `https://`, `ftp://`, `file://`, `jar:`. Location prefix: the URL scheme.

```java
Resource r1 = new ClassPathResource("data/schema.sql");
Resource r2 = new FileSystemResource("/etc/app/config.properties");
Resource r3 = new UrlResource("https://config.example.com/remote.properties");
```

## 2. Why & when

| Implementation | Choose when |
|---|---|
| `ClassPathResource` | File ships inside the JAR; needs classloader resolution |
| `FileSystemResource` | File is outside the JAR on the host filesystem; write access needed |
| `UrlResource` | File is remote (HTTP/FTP) or inside a nested JAR via `jar:` URL |

Use `ClassPathResource` for static templates, SQL scripts, and JSON fixtures bundled with the app. Use `FileSystemResource` for externalized config, log directories, and writable output. Use `UrlResource` to fetch remote config or load resources from a URL-addressable store.

## 3. Core concept

`ClassPathResource` resolution:

1. Uses `Thread.currentThread().getContextClassLoader()` by default.
2. Can accept a specific `Class` → resolves relative to that class's package.
3. Strips leading `/` to normalize paths.
4. Inside a JAR: `getFile()` throws; `getInputStream()` always works.

`FileSystemResource` resolution:

1. Wraps `java.io.File` or `java.nio.file.Path`.
2. Implements `WritableResource` → `getOutputStream()` available.
3. `getFile()` always works; `getURI()` returns a `file:` URI.

`UrlResource` resolution:

1. Opens a `java.net.URLConnection` for each read.
2. Supports basic auth via URL credentials: `http://user:pass@host/path`.
3. `getFilename()` extracts last path segment from the URL.
4. `contentLength()` requires the server to return `Content-Length`.

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg">
  <!-- Resource interface -->
  <rect x="10" y="75" width="130" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="75" y="99" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">&lt;&lt;Resource&gt;&gt;</text>

  <!-- ClassPathResource -->
  <rect x="200" y="20" width="175" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="287" y="40" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">ClassPathResource</text>
  <text x="287" y="58" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">classpath: — JAR-safe, read-only</text>

  <!-- FileSystemResource -->
  <rect x="200" y="80" width="175" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="287" y="100" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">FileSystemResource</text>
  <text x="287" y="118" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">file: — read + write, getFile() ok</text>

  <!-- UrlResource -->
  <rect x="200" y="140" width="175" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="287" y="159" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">UrlResource (http/ftp/jar)</text>

  <!-- Arrows -->
  <defs>
    <marker id="a139" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="142" y1="85" x2="197" y2="45"  stroke="#6db33f" stroke-width="1.5" marker-end="url(#a139)"/>
  <line x1="142" y1="95" x2="197" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a139)"/>
  <line x1="142" y1="108" x2="197" y2="155" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a139)"/>

  <!-- Prefixes -->
  <text x="430" y="45" fill="#6db33f" font-size="10" font-family="sans-serif">classpath:config/app.properties</text>
  <text x="430" y="105" fill="#79c0ff" font-size="10" font-family="sans-serif">file:/opt/app/config.properties</text>
  <text x="430" y="155" fill="#8b949e" font-size="10" font-family="sans-serif">https://remote/config.properties</text>

  <text x="350" y="180" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">ResourceLoader maps location prefixes to the correct Resource implementation</text>
</svg>

Location prefixes route to the correct `Resource` implementation; the `Resource` interface hides the difference.

## 5. Runnable example

### Level 1 — Basic

`ClassPathResource` reads a bundled SQL file; `FileSystemResource` reads an external config.

```java
// ResourceTypesBasic.java
import org.springframework.core.io.*;
import java.nio.file.*;

public class ResourceTypesBasic {
    public static void main(String[] args) throws Exception {
        // ClassPathResource — bundle a SQL script alongside the class
        Files.writeString(Path.of("schema.sql"),
            "CREATE TABLE orders (id INT PRIMARY KEY, amount DECIMAL(10,2));\n");

        ClassPathResource sql = new ClassPathResource("schema.sql");
        System.out.println("ClassPathResource:");
        System.out.println("  filename: " + sql.getFilename());
        System.out.println("  exists:   " + sql.exists());
        System.out.println("  isFile:   " + sql.isFile());
        System.out.println("  content:  " +
            new String(sql.getInputStream().readAllBytes()).trim());

        // FileSystemResource — external config file
        Path ext = Files.createTempFile("ext-cfg-", ".properties");
        Files.writeString(ext, "ext.key=external-value\next.count=42\n");

        FileSystemResource fs = new FileSystemResource(ext.toFile());
        System.out.println("\nFileSystemResource:");
        System.out.println("  filename: " + fs.getFilename());
        System.out.println("  exists:   " + fs.exists());
        System.out.println("  isFile:   " + fs.isFile());
        System.out.println("  uri:      " + fs.getURI());

        var props = new java.util.Properties();
        props.load(fs.getInputStream());
        System.out.println("  ext.key:  " + props.getProperty("ext.key"));

        Files.deleteIfExists(Path.of("schema.sql"));
        Files.deleteIfExists(ext);
    }
}
```

How to run: `java ResourceTypesBasic.java`

`ClassPathResource` works when the SQL file is on the classpath (working directory). `FileSystemResource` wraps a `File` directly. Both expose the same `getInputStream()` API.

### Level 2 — Intermediate

`FileSystemResource` as `WritableResource`; `UrlResource` loading a remote JSON; class-relative `ClassPathResource`.

```java
// ResourceTypesWrite.java
import org.springframework.core.io.*;
import java.io.*;
import java.nio.file.*;

public class ResourceTypesWrite {
    public static void main(String[] args) throws Exception {
        // 1. FileSystemResource as WritableResource
        Path tmpFile = Files.createTempFile("spring-writable-", ".log");
        FileSystemResource writable = new FileSystemResource(tmpFile.toFile());

        System.out.println("WritableResource:");
        System.out.println("  isWritable: " + (writable instanceof WritableResource));
        try (var writer = new OutputStreamWriter(
                ((WritableResource) writable).getOutputStream())) {
            writer.write("line1: start\n");
            writer.write("line2: middle\n");
            writer.write("line3: end\n");
        }
        System.out.println("  written bytes: " + writable.contentLength());
        System.out.println("  content: " +
            new String(writable.getInputStream().readAllBytes()));

        // 2. Class-relative ClassPathResource
        // Resolves relative to the package of the passed Class
        Files.createDirectories(Path.of("data"));
        Files.writeString(Path.of("data/seed.json"), "{\"seed\":true}");
        // Normally you'd pass YourClass.class; here we simulate with Object.class
        ClassPathResource relative = new ClassPathResource("data/seed.json");
        System.out.println("\nClassPathResource (data/seed.json):");
        System.out.println("  exists: " + relative.exists());
        System.out.println("  content: " +
            new String(relative.getInputStream().readAllBytes()));

        // 3. UrlResource — file: URL (works without network)
        UrlResource fileUrl = new UrlResource(tmpFile.toUri().toURL());
        System.out.println("\nUrlResource (file: URL):");
        System.out.println("  filename:    " + fileUrl.getFilename());
        System.out.println("  contentLength: " + fileUrl.contentLength());
        System.out.println("  content lines: " +
            new String(fileUrl.getInputStream().readAllBytes()).lines().count());

        Files.deleteIfExists(tmpFile);
        Files.deleteIfExists(Path.of("data/seed.json"));
        Files.deleteIfExists(Path.of("data"));
    }
}
```

How to run: `java ResourceTypesWrite.java`

`FileSystemResource` implements `WritableResource` — cast to write. A `file:` URL wraps a filesystem path inside `UrlResource` for uniform URL-based access. Both `ClassPathResource` and `UrlResource` support `contentLength()`.

### Level 3 — Advanced

`createRelative`, `PathResource` (NIO path), metadata comparison across resource types, resource selection factory.

```java
// ResourceTypesAdvanced.java
import org.springframework.core.io.*;
import java.nio.file.*;
import java.time.*;
import java.util.*;

public class ResourceTypesAdvanced {

    sealed interface ResourceKind permits ResourceKind.Classpath, ResourceKind.Filesystem, ResourceKind.Remote {
        record Classpath(String path) implements ResourceKind {}
        record Filesystem(String path) implements ResourceKind {}
        record Remote(String url) implements ResourceKind {}
    }

    static Resource from(ResourceKind kind) throws Exception {
        return switch (kind) {
            case ResourceKind.Classpath c -> new ClassPathResource(c.path());
            case ResourceKind.Filesystem f -> new FileSystemResource(f.path());
            case ResourceKind.Remote r -> new UrlResource(r.url());
        };
    }

    static void describe(Resource r) throws Exception {
        System.out.printf("  [%s] exists=%b readable=%b file=%b open=%b%n",
            r.getClass().getSimpleName(), r.exists(), r.isReadable(), r.isFile(), r.isOpen());
        if (r.exists()) {
            System.out.printf("  filename=%s len=%d%n", r.getFilename(), r.contentLength());
        }
    }

    public static void main(String[] args) throws Exception {
        // Setup
        Path dir = Files.createTempDirectory("spring-res-adv-");
        Path main  = dir.resolve("main.txt");
        Path extra = dir.resolve("extra.txt");
        Files.writeString(main, "main content");
        Files.writeString(extra, "extra content");
        Files.writeString(Path.of("classpath-res.txt"), "classpath content");

        var kinds = List.of(
            new ResourceKind.Classpath("classpath-res.txt"),
            new ResourceKind.Filesystem(main.toString()),
            new ResourceKind.Remote(extra.toUri().toURL().toString())
        );

        for (var kind : kinds) {
            System.out.println("=== " + kind.getClass().getSimpleName() + " ===");
            Resource r = from(kind);
            describe(r);
        }

        // createRelative from FileSystemResource
        Resource mainRes = new FileSystemResource(main.toFile());
        Resource extraRes = mainRes.createRelative("extra.txt");
        System.out.println("\n=== createRelative ===");
        System.out.println("extra.txt via createRelative:");
        System.out.println("  filename: " + extraRes.getFilename());
        System.out.println("  content:  " + new String(extraRes.getInputStream().readAllBytes()));

        // PathResource (NIO path-based)
        Resource pathRes = new PathResource(main);
        System.out.println("\n=== PathResource ===");
        describe(pathRes);
        System.out.println("  path type: " + pathRes.getClass().getSimpleName());

        // lastModified comparison
        Instant modMain  = Instant.ofEpochMilli(new FileSystemResource(main.toFile()).lastModified());
        Instant modExtra = Instant.ofEpochMilli(new FileSystemResource(extra.toFile()).lastModified());
        System.out.println("\nmain modified:  " + modMain);
        System.out.println("extra modified: " + modExtra);

        Files.deleteIfExists(main);
        Files.deleteIfExists(extra);
        Files.deleteIfExists(dir);
        Files.deleteIfExists(Path.of("classpath-res.txt"));
    }
}
```

How to run: `java ResourceTypesAdvanced.java`

The sealed-interface factory dispatches to the correct `Resource` type. `createRelative` navigates to sibling files. `PathResource` wraps `java.nio.file.Path` directly and also implements `WritableResource`. `lastModified()` provides timestamps for cache validation.

## 6. Walkthrough

Execution for Level 3 `createRelative`:

1. **`mainRes = new FileSystemResource(main.toFile())`** → wraps `/tmp/.../main.txt`.
2. **`mainRes.createRelative("extra.txt")`** → `FileSystemResource` delegates to `File.getParentFile()` → `/tmp/.../extra.txt`.
3. **`extraRes.exists()`** → `true`.
4. **`extraRes.getInputStream()`** → `FileInputStream` on `/tmp/.../extra.txt`.
5. **`readAllBytes()`** → `"extra content"`.

## 7. Gotchas & takeaways

> `ClassPathResource.getFile()` throws `FileNotFoundException` when the resource is inside a JAR — the path has no backing filesystem file. Always use `getInputStream()` for portable reads across all deployment scenarios (exploded WAR, fat JAR, native image).

> `UrlResource` opens a new `URLConnection` on each `getInputStream()` call — with no connection pooling or timeouts by default. For HTTP resources in production, use a dedicated HTTP client rather than `UrlResource`.

- `FileSystemResource` vs `PathResource`: `PathResource` wraps `java.nio.file.Path` and handles `Path.toFile()` failures gracefully on non-default filesystems (e.g., in-memory FS). Prefer `PathResource` for NIO-first code.
- Both `FileSystemResource` and `PathResource` implement `WritableResource` — but `ClassPathResource` and `UrlResource` do not.
- `ClassPathResource` with a leading `/` strips it: `new ClassPathResource("/config/app.properties")` is the same as `new ClassPathResource("config/app.properties")`.
- `UrlResource` accepts `file:`, `http:`, `https:`, `ftp:`, and `jar:` URLs — and any custom protocol registered with `java.net.URL`.
