# Java 11 Features (2018 LTS)

Java 11 is a Long-Term Support (LTS) release. Key additions: new String/File methods, HTTP Client, `var` in lambdas, and removal of Nashorn/JavaEE modules.

---

## 1. New String Methods

```java
public class StringJava11 {
    public static void main(String[] args) {
        // isBlank() — true if empty or all whitespace (Unicode-aware)
        System.out.println("".isBlank());        // true
        System.out.println("   ".isBlank());     // true
        System.out.println("  a  ".isBlank());   // false
        // Unlike isEmpty(): "  ".isEmpty() = false, "  ".isBlank() = true

        // strip() — Unicode-aware trim (handles   etc.)
        System.out.println("  hello  ".strip());        // "hello"
        System.out.println("  hello  ".stripLeading()); // "hello  "
        System.out.println("  hello  ".stripTrailing()); // "  hello"
        // trim() only handles ASCII whitespace (<=' ')

        // lines() — stream of lines (handles \n, \r\n, \r)
        "line1\nline2\nline3".lines()
            .forEach(System.out::println);

        // repeat(n) — repeat string
        System.out.println("ab".repeat(3));     // ababab
        System.out.println("=-".repeat(10));    // =-=-=-=-=-=-=-=-=-=-

        // String.lines() replaces split("\\n") for line splitting
        long count = "a\nb\nc".lines().count(); // 3
    }
}
```

---

## 2. New Files Methods

```java
import java.nio.file.*;
import java.nio.charset.*;

public class FilesJava11 {
    public static void main(String[] args) throws Exception {
        Path path = Path.of("/tmp/test11.txt");

        // Files.writeString [Java 11] — write String directly
        Files.writeString(path, "Hello Java 11\nLine 2", StandardCharsets.UTF_8);

        // Files.readString [Java 11] — read entire file as String
        String content = Files.readString(path, StandardCharsets.UTF_8);
        System.out.println(content);

        // With options
        Files.writeString(path, "\nappended", StandardCharsets.UTF_8,
            StandardOpenOption.APPEND);
    }
}
```

---

## 3. HTTP Client (Standard) [Java 11]

The HTTP/2 client incubating in Java 9 is now standard in `java.net.http`.

```java
import java.net.http.*;
import java.net.URI;
import java.time.Duration;
import java.util.concurrent.CompletableFuture;

public class HttpClientDemo {
    public static void main(String[] args) throws Exception {
        HttpClient client = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_2)
            .connectTimeout(Duration.ofSeconds(10))
            .build();

        // Synchronous GET
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create("https://httpbin.org/get"))
            .header("Accept", "application/json")
            .timeout(Duration.ofSeconds(5))
            .GET()
            .build();

        HttpResponse<String> response = client.send(request,
            HttpResponse.BodyHandlers.ofString());

        System.out.println("Status: " + response.statusCode()); // 200
        System.out.println("Body: " + response.body().substring(0, 50) + "...");

        // Asynchronous POST
        HttpRequest postReq = HttpRequest.newBuilder()
            .uri(URI.create("https://httpbin.org/post"))
            .POST(HttpRequest.BodyPublishers.ofString("{\"key\":\"value\"}"))
            .header("Content-Type", "application/json")
            .build();

        CompletableFuture<HttpResponse<String>> asyncResponse =
            client.sendAsync(postReq, HttpResponse.BodyHandlers.ofString());

        asyncResponse.thenAccept(resp ->
            System.out.println("Async status: " + resp.statusCode())
        ).join();
    }
}
```

---

## 4. var in Lambda Parameters [Java 11]

`var` now allowed in lambda parameters (mainly for annotation support).

```java
import java.util.function.*;

// var in lambda parameters — allows annotations
Function<String, Integer> fn = (var s) -> s.length();  // same as s -> s.length()

// Useful for applying annotations to lambda parameters (requires var, not type inference)
// (@NotNull var s) -> s.length()  — annotation on lambda param
// Without var: (@NotNull String s) -> s.length()  — equivalent

// Consistency: all params must use var if any does
BiFunction<String, Integer, String> rep = (var s, var n) -> s.repeat(n);
System.out.println(rep.apply("ab", 3)); // ababab
```

---

## 5. Running Single-File Programs

```bash
# Java 11: launch a single .java file without explicit javac step
java HelloWorld.java   # compiles in memory and runs

# Source launcher — useful for scripts
#!/usr/bin/java --source 11
public class Script {
    public static void main(String[] args) {
        System.out.println("Running as script!");
    }
}
```

---

## 6. Removed and Deprecated

```
Removed:
  Java EE modules (javax.xml.ws, javax.activation, etc.)
    → now separate Maven artifacts (jakarta.xml.ws-api, etc.)
  CORBA
  Nashorn JavaScript engine (deprecated → removed Java 15)

Deprecated:
  Thread.destroy() / stop() / suspend() / resume()
  (were deprecated since Java 1.2, removed Java 14)

Important migration note for Java 8 → 11:
  If you used javax.xml.bind (JAXB), javax.activation, etc.:
  Add to Maven/Gradle: com.sun.xml.bind:jaxb-ri (or jakarta equivalent)
```

---

## Quick Reference

```
Java 11 key features:
  String.isBlank()         empty or all whitespace
  String.strip()           Unicode-aware trim
  String.stripLeading/Trailing()
  String.lines()           stream of lines
  String.repeat(n)         "ab".repeat(3) = "ababab"
  Files.writeString(p, s)  write String to file
  Files.readString(p)      read file to String
  HttpClient               java.net.http, HTTP/1.1 + HTTP/2
  var in lambdas           (var s) -> s.length()
  Single-file launch       java MyFile.java
  Flight Recorder          production JVM profiling (free)
  Epsilon GC               no-op GC (testing/benchmarking)
  ZGC (experimental)       low-latency GC (production Java 15+)
  
LTS: yes — widely used in production
```
