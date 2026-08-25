# Java 18 Features (2022)

Java 18 introduced UTF-8 as the default charset, a simple web server, and code snippets in Javadoc.

---

## 1. UTF-8 as Default Charset [Java 18]

`java.nio.charset.Charset.defaultCharset()` now always returns UTF-8, regardless of OS locale.

```java
import java.nio.charset.*;

// Before Java 18: default charset was platform-dependent
// On Windows: windows-1252 or GBK
// On macOS/Linux: UTF-8 (usually)

// Java 18: always UTF-8
System.out.println(Charset.defaultCharset()); // UTF-8

// APIs affected (now always use UTF-8 by default):
//   new FileReader("file.txt")           — was platform charset
//   new FileWriter("file.txt")           — was platform charset
//   new PrintStream(System.out)          — was platform charset
//   new String(bytes) / str.getBytes()   — was platform charset

// BEST PRACTICE (still): always specify charset explicitly
byte[] bytes = "hello".getBytes(StandardCharsets.UTF_8);
String str = new String(bytes, StandardCharsets.UTF_8);
```

---

## 2. Simple Web Server [Java 18]

Built-in HTTP file server for development/testing.

```bash
# Command-line: serve current directory on port 8000
jwebserver

# Specify directory and port
jwebserver -p 9090 -d /path/to/dir

# Output:
# Binding to loopback by default. For all interfaces use "-b 0.0.0.0" or "-b ::".
# Serving /path/to/dir and subdirectories on 127.0.0.1 port 9090
# URL: http://127.0.0.1:9090/
```

```java
import com.sun.net.httpserver.*;
import java.net.*;
import java.io.*;
import java.nio.file.*;

// Programmatic API
InetSocketAddress addr = new InetSocketAddress(8080);
HttpServer server = SimpleFileServer.createFileServer(
    addr, Path.of("/tmp"), SimpleFileServer.OutputLevel.VERBOSE);
server.start();
```

---

## 3. Code Snippets in Javadoc [Java 18]

`@snippet` tag replaces `{@code}` for embedding verified code examples.

```java
/**
 * Creates a greeting message.
 *
 * {@snippet lang="java" :
 *     Greeter g = new Greeter("Alice");
 *     String msg = g.greet();           // @highlight substring="greet"
 *     System.out.println(msg);          // Prints: Hello, Alice
 * }
 *
 * External snippet from a file:
 * {@snippet file="GreeterUsage.java" region="example"}
 */
public class Greeter {
    private final String name;
    public Greeter(String name) { this.name = name; }
    public String greet() { return "Hello, " + name; }
}
```

---

## 4. Pattern Matching for switch (2nd Preview) [Java 18]

Refinements to the preview from Java 17 — guarded patterns, improvements.

```java
// 2nd preview — closer to final form
static String format(Object obj) {
    return switch (obj) {
        case Integer i when i > 0 -> "positive: " + i; // guarded pattern (when)
        case Integer i            -> "non-positive: " + i;
        case String s             -> "string: " + s;
        default                   -> "other";
    };
}
```

---

## 5. Vector API (3rd Incubator) [Java 18]

Continued refinement of SIMD API.

---

## Quick Reference

```
Java 18 key features:
  UTF-8 default charset    Charset.defaultCharset() → UTF-8 always
  Simple web server        jwebserver CLI + SimpleFileServer API
  @snippet Javadoc         verified code snippets in documentation
  Pattern switch (2nd prev) guarded patterns (when clause)
  Vector API (3rd incubat.) SIMD improvements
  Internet-Address Resolution SPI  pluggable DNS resolution
  Foreign Function + Memory (2nd incubat.) native interop
  Deprecated: Object.finalize()   use Cleaner instead
```
