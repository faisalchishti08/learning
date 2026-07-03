---
card: spring-framework
gi: 138
slug: resource-interface
title: "Resource interface"
---

## 1. What it is

`Resource` is Spring's core abstraction for any low-level resource: a classpath file, a filesystem path, a URL, a byte array, or an input stream. It provides a uniform API over `java.io.File`, `java.net.URL`, `java.io.InputStream` and the classpath. All Spring infrastructure that deals with files or URLs uses `Resource`.

```java
Resource r = new ClassPathResource("config/app.properties");
Properties props = new Properties();
props.load(r.getInputStream());
```

## 2. Why & when

- **Location-agnostic code** — a `Resource` works whether the file is on the classpath, the filesystem, or a remote URL; calling code doesn't change.
- **Testing** — swap a real file `Resource` with a `ByteArrayResource` or `InputStreamResource` without touching the file system.
- **Framework integration** — Spring MVC, `@PropertySource`, `ResourceBundleMessageSource`, Spring Batch, and others accept `Resource` or paths that Spring converts to `Resource` internally.
- **Metadata access** — `getFilename()`, `contentLength()`, `lastModified()`, `exists()`, `isReadable()`, `isOpen()` without dealing with protocol-specific APIs.

## 3. Core concept

Key `Resource` methods:

| Method | Returns |
|---|---|
| `getInputStream()` | `InputStream` — always fresh |
| `exists()` | `boolean` |
| `isReadable()` | `boolean` — readable without an open handle |
| `isOpen()` | `boolean` — true for `InputStreamResource` (single read) |
| `isFile()| `boolean` — backed by a `java.io.File` |
| `getURL()` | `URL` |
| `getURI()` | `URI` |
| `getFile()` | `File` |
| `getFilename()` | Last path component |
| `getDescription()` | Human-readable description |
| `contentLength()` | Size in bytes |
| `lastModified()` | Last-modified timestamp |
| `createRelative(path)` | Sibling resource at relative path |

`WritableResource` extends `Resource` with `getOutputStream()` for write access.

`Resource` implementations:

| Class | Backed by |
|---|---|
| `ClassPathResource` | Classpath entry |
| `FileSystemResource` | `java.io.File` / `java.nio.Path` |
| `UrlResource` | `java.net.URL` |
| `ByteArrayResource` | `byte[]` |
| `InputStreamResource` | `InputStream` (single-read) |
| `PathResource` | `java.nio.file.Path` |
| `ServletContextResource` | Web app root |

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg">
  <!-- Resource interface box -->
  <rect x="10" y="30" width="190" height="130" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="105" y="50" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">&lt;&lt;Resource&gt;&gt;</text>
  <text x="105" y="68" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">getInputStream()</text>
  <text x="105" y="82" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">exists() / isReadable()</text>
  <text x="105" y="96" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">getURL() / getURI() / getFile()</text>
  <text x="105" y="110" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">getFilename() / contentLength()</text>
  <text x="105" y="124" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">lastModified()</text>
  <text x="105" y="138" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">createRelative(path)</text>

  <!-- Implementations -->
  <rect x="255" y="18"  width="170" height="22" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="33"  fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">ClassPathResource</text>

  <rect x="255" y="45"  width="170" height="22" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="60"  fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">FileSystemResource</text>

  <rect x="255" y="72"  width="170" height="22" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="87"  fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">UrlResource</text>

  <rect x="255" y="99"  width="170" height="22" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="114" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">ByteArrayResource</text>

  <rect x="255" y="126" width="170" height="22" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="340" y="141" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">InputStreamResource</text>

  <rect x="255" y="153" width="170" height="22" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="340" y="168" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">PathResource</text>

  <!-- Arrows (inheritance lines) -->
  <line x1="202" y1="80"  x2="252" y2="80"  stroke="#6db33f" stroke-width="1" stroke-dasharray="4,3"/>
  <line x1="240" y1="80"  x2="240" y2="29"  stroke="#6db33f" stroke-width="1" stroke-dasharray="4,3"/>
  <line x1="240" y1="56"  x2="252" y2="56"  stroke="#6db33f" stroke-width="1" stroke-dasharray="4,3"/>
  <line x1="240" y1="83"  x2="252" y2="83"  stroke="#79c0ff" stroke-width="1" stroke-dasharray="4,3"/>
  <line x1="240" y1="110" x2="252" y2="110" stroke="#79c0ff" stroke-width="1" stroke-dasharray="4,3"/>
  <line x1="240" y1="137" x2="252" y2="137" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <line x1="240" y1="164" x2="252" y2="164" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <line x1="202" y1="80"  x2="240" y2="80"  stroke="#6db33f" stroke-width="1.5" stroke-dasharray="4,3"/>

  <text x="350" y="190" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Uniform API over classpath, filesystem, URL, byte array, and stream sources</text>
</svg>

`Resource` unifies access to classpath entries, files, URLs, and in-memory data under one interface.

## 5. Runnable example

### Level 1 — Basic

Read a classpath resource, check metadata, create relative sibling.

```java
// ResourceInterfaceBasic.java
import org.springframework.core.io.*;
import java.nio.file.*;
import java.util.Properties;

public class ResourceInterfaceBasic {
    public static void main(String[] args) throws Exception {
        // Create a properties file on the classpath (working directory = classpath root)
        Files.writeString(Path.of("greeting.properties"),
            "msg.hello=Hello, World!\nmsg.bye=Goodbye!\n");

        Resource resource = new ClassPathResource("greeting.properties");

        System.out.println("exists:      " + resource.exists());
        System.out.println("isReadable:  " + resource.isReadable());
        System.out.println("filename:    " + resource.getFilename());
        System.out.println("description: " + resource.getDescription());
        System.out.println("uri:         " + resource.getURI());
        System.out.println("contentLen:  " + resource.contentLength() + " bytes");

        // Read contents
        Properties props = new Properties();
        props.load(resource.getInputStream());
        System.out.println("msg.hello: " + props.getProperty("msg.hello"));
        System.out.println("msg.bye:   " + props.getProperty("msg.bye"));

        // ByteArrayResource — in-memory, no file needed
        Resource mem = new ByteArrayResource("in-memory content".getBytes());
        System.out.println("\nbyte array resource:");
        System.out.println("  isOpen:    " + mem.isOpen());
        System.out.println("  content:   " + new String(mem.getInputStream().readAllBytes()));
        System.out.println("  content:   " + new String(mem.getInputStream().readAllBytes())); // re-readable

        Files.deleteIfExists(Path.of("greeting.properties"));
    }
}
```

How to run: `java ResourceInterfaceBasic.java`

`ClassPathResource` resolves from the working directory (classpath root). `ByteArrayResource` wraps an in-memory byte array — `isOpen()` returns false, so it can be read multiple times (unlike `InputStreamResource`).

### Level 2 — Intermediate

Polymorphic method accepting `Resource`; FileSystemResource vs ClassPathResource; InputStreamResource single-read constraint.

```java
// ResourceInterfacePolymorphic.java
import org.springframework.core.io.*;
import java.io.*;
import java.nio.file.*;

public class ResourceInterfacePolymorphic {

    static String readContent(Resource r) throws IOException {
        // Generic: works for any Resource implementation
        try (var is = r.getInputStream()) {
            return new String(is.readAllBytes());
        }
    }

    static void printInfo(Resource r) throws IOException {
        System.out.printf("  [%s] exists=%b readable=%b file=%b open=%b len=%d%n",
            r.getClass().getSimpleName(),
            r.exists(), r.isReadable(), r.isFile(), r.isOpen(),
            r.exists() ? r.contentLength() : -1L);
    }

    public static void main(String[] args) throws Exception {
        // FileSystemResource
        Path tmpFile = Files.createTempFile("spring-resource-", ".txt");
        Files.writeString(tmpFile, "FileSystem content");

        Resource fs = new FileSystemResource(tmpFile.toFile());
        System.out.println("FileSystemResource:");
        printInfo(fs);
        System.out.println("  content: " + readContent(fs));
        System.out.println("  content: " + readContent(fs)); // re-readable

        // ClassPathResource
        Files.writeString(Path.of("classpath-test.txt"), "ClassPath content");
        Resource cp = new ClassPathResource("classpath-test.txt");
        System.out.println("ClassPathResource:");
        printInfo(cp);
        System.out.println("  content: " + readContent(cp));

        // ByteArrayResource
        Resource ba = new ByteArrayResource("<xml>data</xml>".getBytes(), "XML payload");
        System.out.println("ByteArrayResource:");
        printInfo(ba);
        System.out.println("  content: " + readContent(ba));

        // InputStreamResource — single-read only; isOpen() = true
        var stream = new ByteArrayInputStream("stream-only".getBytes());
        Resource isr = new InputStreamResource(stream);
        System.out.println("InputStreamResource:");
        System.out.printf("  [%s] isOpen=%b%n", isr.getClass().getSimpleName(), isr.isOpen());
        System.out.println("  content: " + readContent(isr));
        try {
            readContent(isr); // throws — already consumed
        } catch (IOException e) {
            System.out.println("  2nd read threw: " + e.getMessage());
        }

        Files.deleteIfExists(tmpFile);
        Files.deleteIfExists(Path.of("classpath-test.txt"));
    }
}
```

How to run: `java ResourceInterfacePolymorphic.java`

`readContent(Resource)` works for all implementations. `FileSystemResource` and `ClassPathResource` support multiple reads. `InputStreamResource` is single-read (`isOpen()=true`) — second call throws `IOException`.

### Level 3 — Advanced

Factory pattern for `Resource` selection; `createRelative`; `WritableResource`; content hashing.

```java
// ResourceInterfaceAdvanced.java
import org.springframework.core.io.*;
import java.io.*;
import java.nio.file.*;
import java.security.*;
import java.util.HexFormat;

public class ResourceInterfaceAdvanced {

    static Resource resolve(String location) {
        if (location.startsWith("classpath:"))
            return new ClassPathResource(location.substring("classpath:".length()));
        if (location.startsWith("file:"))
            return new FileSystemResource(location.substring("file:".length()));
        return new ClassPathResource(location);  // default: classpath
    }

    static String sha256(Resource r) throws Exception {
        var digest = MessageDigest.getInstance("SHA-256");
        try (var is = r.getInputStream()) {
            digest.update(is.readAllBytes());
        }
        return HexFormat.of().formatHex(digest.digest()).substring(0, 12);
    }

    public static void main(String[] args) throws Exception {
        // Create test files
        Path configDir = Files.createTempDirectory("spring-resource-adv-");
        Path configFile = configDir.resolve("main.properties");
        Path schemaFile = configDir.resolve("schema.json");
        Files.writeString(configFile, "app.name=Advanced\napp.version=3.0\n");
        Files.writeString(schemaFile, "{\"type\":\"object\"}");

        // Resolve via factory
        Resource mainCfg = new FileSystemResource(configFile.toFile());
        System.out.printf("Resolved: %s%n  sha256prefix=%s%n",
            mainCfg.getDescription(), sha256(mainCfg));

        // createRelative — sibling file
        Resource schema = mainCfg.createRelative("schema.json");
        System.out.printf("Relative: %s%n  exists=%b content=%s%n",
            schema.getFilename(), schema.exists(),
            new String(schema.getInputStream().readAllBytes()));

        // WritableResource — FileSystemResource implements it
        WritableResource writable = (WritableResource) mainCfg;
        try (var out = new OutputStreamWriter(writable.getOutputStream())) {
            out.write("app.name=Rewritten\napp.version=4.0\n");
        }
        // Read back
        var reread = new Properties();
        reread.load(mainCfg.getInputStream());
        System.out.println("After write: app.name=" + reread.getProperty("app.name") +
            " version=" + reread.getProperty("app.version"));

        // lastModified check
        System.out.println("lastModified: " + mainCfg.lastModified());

        // Cleanup
        Files.deleteIfExists(configFile);
        Files.deleteIfExists(schemaFile);
        Files.deleteIfExists(configDir);
    }
}
```

How to run: `java ResourceInterfaceAdvanced.java`

`createRelative` produces a sibling `Resource` without path concatenation boilerplate. `WritableResource` (implemented by `FileSystemResource` and `PathResource`) adds `getOutputStream()`. Content hashing via `sha256` demonstrates reading bytes through the uniform `getInputStream()` API.

## 6. Walkthrough

Execution for Level 3:

1. **`configDir/main.properties`** created on the filesystem.
2. **`FileSystemResource(configFile)`** wraps it — `isFile()=true`, `exists()=true`.
3. **`sha256(mainCfg)`** opens `getInputStream()`, reads all bytes, computes digest.
4. **`mainCfg.createRelative("schema.json")`** → `FileSystemResource` at `configDir/schema.json`.
5. **`schema.exists()`** → `true`. Content read via `getInputStream()`.
6. **`(WritableResource) mainCfg`** → cast succeeds (FileSystemResource implements WritableResource).
7. **`getOutputStream()`** → `FileOutputStream` to the same file; overwrites content.
8. **`mainCfg.getInputStream()`** re-opens the file → reads updated content.

## 7. Gotchas & takeaways

> `InputStreamResource` wraps an existing `InputStream` — once consumed it cannot be re-read, and `isOpen()` returns `true` as a warning. Never use it for resources that must be read more than once; use `ByteArrayResource` for in-memory data.

> `getFile()` throws `FileNotFoundException` for `ClassPathResource` entries inside a JAR — the classpath entry is not a file in the filesystem. Always use `getInputStream()` for portable reads; call `isFile()` before calling `getFile()`.

- `ClassPathResource` uses the thread context classloader by default; pass a specific `ClassLoader` or `Class` to the constructor for predictable classpath resolution in complex deployments.
- `Resource.exists()` does not guarantee `getInputStream()` succeeds (a transient I/O error can still occur). Always handle `IOException` from `getInputStream()`.
- `contentLength()` and `lastModified()` are available for `ClassPathResource` and `FileSystemResource` but throw for `InputStreamResource`.
- Spring's `ResourceLoader` (next tutorial) converts location strings like `classpath:foo.properties` or `file:/path/to/file` into `Resource` objects automatically.
