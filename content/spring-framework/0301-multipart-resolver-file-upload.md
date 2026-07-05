---
card: spring-framework
gi: 301
slug: multipart-resolver-file-upload
title: "Multipart resolver (file upload)"
---

## 1. What it is

A **`MultipartResolver`** is the Spring MVC strategy that parses `multipart/form-data` HTTP requests into a `MultipartHttpServletRequest`, making uploaded files accessible as `MultipartFile` objects in controller methods.

Spring MVC ships with two implementations:

| Implementation | Backed by |
|---|---|
| `StandardServletMultipartResolver` | Servlet 3.0 `Part` API (Jakarta EE) — default since Spring 5 |
| `CommonsMultipartResolver` | Apache Commons FileUpload (legacy, requires extra dependency) |

Spring Boot auto-configures `StandardServletMultipartResolver` when `spring.servlet.multipart.enabled=true` (the default).

---

## 2. Why & when

Use a `MultipartResolver` whenever a form or API client uploads binary data:

- Profile photo uploads
- Document imports (CSV, PDF, XLSX)
- Bulk-data ingestion endpoints

`StandardServletMultipartResolver` delegates parsing to the servlet container (Tomcat / Jetty) which streams the file directly to a temp directory, keeping heap usage low for large uploads.

---

## 3. Core concept

```
POST /upload
Content-Type: multipart/form-data; boundary=----FormBoundary

------FormBoundary
Content-Disposition: form-data; name="description"

My file
------FormBoundary
Content-Disposition: form-data; name="file"; filename="data.csv"
Content-Type: text/csv

id,name
1,Alice
------FormBoundary--
```

`DispatcherServlet.checkMultipart(request)` calls `MultipartResolver.isMultipart(request)` — if true, wraps the raw `HttpServletRequest` in a `StandardMultipartHttpServletRequest`.  The controller then receives `@RequestParam MultipartFile file` populated with the parsed part.

---

## 4. Diagram

<svg viewBox="0 0 740 280" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="280" fill="#0d1117"/>

  <!-- Client -->
  <rect x="10" y="110" width="100" height="40" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="60" y="134" text-anchor="middle" fill="#79c0ff">Client</text>

  <!-- arrow -->
  <line x1="110" y1="130" x2="155" y2="130" stroke="#8b949e" marker-end="url(#amr)"/>
  <text x="132" y="124" text-anchor="middle" fill="#8b949e" font-size="10">multipart POST</text>

  <!-- DispatcherServlet -->
  <rect x="155" y="100" width="155" height="60" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="232" y="120" text-anchor="middle" fill="#79c0ff">DispatcherServlet</text>
  <text x="232" y="138" text-anchor="middle" fill="#8b949e" font-size="10">checkMultipart()</text>
  <text x="232" y="152" text-anchor="middle" fill="#8b949e" font-size="10">isMultipart() → true</text>

  <!-- arrow -->
  <line x1="310" y1="130" x2="355" y2="130" stroke="#8b949e" marker-end="url(#amr)"/>

  <!-- Resolver -->
  <rect x="355" y="100" width="175" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="442" y="120" text-anchor="middle" fill="#6db33f">StandardServlet</text>
  <text x="442" y="136" text-anchor="middle" fill="#6db33f">MultipartResolver</text>
  <text x="442" y="152" text-anchor="middle" fill="#8b949e" font-size="10">wraps → MultipartHttpServletRequest</text>

  <!-- arrow -->
  <line x1="530" y1="130" x2="575" y2="130" stroke="#8b949e" marker-end="url(#amr)"/>

  <!-- Controller -->
  <rect x="575" y="100" width="155" height="60" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="652" y="120" text-anchor="middle" fill="#79c0ff">Controller</text>
  <text x="652" y="138" text-anchor="middle" fill="#8b949e" font-size="10">@RequestParam</text>
  <text x="652" y="152" text-anchor="middle" fill="#8b949e" font-size="10">MultipartFile file</text>

  <!-- Temp file arrow down -->
  <line x1="442" y1="160" x2="442" y2="210" stroke="#8b949e" stroke-dasharray="3,2" marker-end="url(#amr)"/>
  <rect x="355" y="210" width="175" height="36" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="442" y="228" text-anchor="middle" fill="#8b949e">Temp file (OS)</text>
  <text x="442" y="243" text-anchor="middle" fill="#8b949e" font-size="10">cleaned up after response</text>

  <!-- caption -->
  <text x="370" y="268" text-anchor="middle" fill="#8b949e" font-size="11">Container streams multipart body to temp disk; MultipartFile wraps it</text>

  <defs>
    <marker id="amr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*File bytes land on disk (OS temp); `MultipartFile` is a thin handle — actual bytes are not in heap.*

---

## 5. Runnable example

### Level 1 — Basic

Accept a single file upload and echo its name and size:

```java
// UploadController.java
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/upload")
public class UploadController {

    @PostMapping
    public ResponseEntity<String> upload(@RequestParam("file") MultipartFile file) {
        if (file.isEmpty()) {
            return ResponseEntity.badRequest().body("No file provided");
        }
        String info = String.format("name=%s size=%d bytes type=%s",
                file.getOriginalFilename(), file.getSize(), file.getContentType());
        return ResponseEntity.ok(info);
    }
}
```

```properties
# application.properties
spring.servlet.multipart.max-file-size=10MB
spring.servlet.multipart.max-request-size=12MB
```

**How to run:**
```bash
./mvnw spring-boot:run
curl -i -F "file=@README.md" http://localhost:8080/upload
# 200 OK
# name=README.md size=3421 bytes type=text/plain
```

`@RequestParam("file")` tells Spring to read the part named `"file"` from the `MultipartHttpServletRequest`.  `MultipartFile.getSize()` is the content-length of that part; `getOriginalFilename()` is the `filename=` attribute from the `Content-Disposition` header.

---

### Level 2 — Intermediate

Same upload scenario — now **saving the file to a target directory** and returning its storage path, plus accepting a metadata field alongside the file:

```java
// UploadController.java (extended)
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import java.io.*;
import java.nio.file.*;

@RestController
@RequestMapping("/upload")
public class UploadController {

    @Value("${upload.dir:/tmp/uploads}")
    private String uploadDir;

    @PostMapping
    public ResponseEntity<String> upload(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "description", required = false) String description) throws IOException {

        if (file.isEmpty()) return ResponseEntity.badRequest().body("Empty file");

        Path dir = Paths.get(uploadDir);
        Files.createDirectories(dir);

        // Sanitise filename to prevent path traversal
        String safeName = Paths.get(file.getOriginalFilename()).getFileName().toString();
        Path target = dir.resolve(safeName);
        file.transferTo(target);

        return ResponseEntity.ok(String.format(
                "saved=%s size=%d desc=%s", target, file.getSize(), description));
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run
curl -F "file=@data.csv" -F "description=Monthly report" http://localhost:8080/upload
# saved=/tmp/uploads/data.csv size=1024 desc=Monthly report
```

**What changed:** `MultipartFile.transferTo(Path)` streams the part directly from the container's temp file to the target — zero heap allocation for large files.  `Paths.get(name).getFileName()` strips any `../` or absolute-path prefix from the client-supplied filename (path traversal prevention).

---

### Level 3 — Advanced

Production scenario: **multiple files + virus scan before storage**, using Spring's async processing and structured error response:

```java
// UploadController.java (production)
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import java.io.*;
import java.nio.file.*;
import java.util.*;

@RestController
@RequestMapping("/upload")
public class UploadController {

    private final VirusScanService scanner;
    private final String uploadDir = System.getProperty("java.io.tmpdir") + "/uploads/";

    public UploadController(VirusScanService scanner) { this.scanner = scanner; }

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE,
                 produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<UploadResult> uploadMany(
            @RequestParam("files") List<MultipartFile> files) throws IOException {

        List<String> saved = new ArrayList<>();
        List<String> rejected = new ArrayList<>();

        Files.createDirectories(Paths.get(uploadDir));

        for (MultipartFile f : files) {
            if (f.isEmpty()) { rejected.add(f.getOriginalFilename() + ": empty"); continue; }
            if (f.getSize() > 50 * 1024 * 1024) { rejected.add(f.getOriginalFilename() + ": too large"); continue; }

            // Scan in-memory (real impl calls ClamAV over socket)
            if (scanner.isMalicious(f.getBytes())) {
                rejected.add(f.getOriginalFilename() + ": malware detected");
                continue;
            }

            String safeName = Paths.get(f.getOriginalFilename()).getFileName().toString();
            Path target = Paths.get(uploadDir).resolve(safeName);
            f.transferTo(target);
            saved.add(target.toString());
        }

        HttpStatus status = rejected.isEmpty() ? HttpStatus.OK : HttpStatus.MULTI_STATUS;
        return ResponseEntity.status(status).body(new UploadResult(saved, rejected));
    }

    record UploadResult(List<String> saved, List<String> rejected) {}
}
```

```java
// VirusScanService.java (stub — replace with real ClamAV client)
import org.springframework.stereotype.Service;
@Service
public class VirusScanService {
    public boolean isMalicious(byte[] content) {
        // Detect EICAR test string
        return new String(content).contains("X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR");
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Upload two files:
curl -F "files=@report.csv" -F "files=@photo.jpg" http://localhost:8080/upload
# {"saved":["/tmp/uploads/report.csv","/tmp/uploads/photo.jpg"],"rejected":[]}

# Upload with an oversized file (simulated):
curl -F "files=@huge.bin" http://localhost:8080/upload
# {"saved":[],"rejected":["huge.bin: too large"]}
```

**What changed and why:**
- `List<MultipartFile>` bound to a single `@RequestParam` name accepts `files[]` from HTML forms or repeated `-F "files=@x"` curl flags.
- Scanning `f.getBytes()` loads the file into heap — acceptable for virus scanning where you need a byte array.  For truly large files, stream to a temp path first, scan the path.
- `207 Multi-Status` reports partial success cleanly — caller knows which files were saved vs rejected without parsing error messages.
- `Paths.get(name).getFileName()` prevents path-traversal even for multi-file uploads.

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="190" fill="#0d1117"/>
  <rect x="10" y="30" width="100" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="60" y="50" text-anchor="middle" fill="#79c0ff">files[] parts</text>
  <line x1="110" y1="45" x2="145" y2="45" stroke="#8b949e" marker-end="url(#amv)"/>
  <rect x="145" y="30" width="120" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="205" y="50" text-anchor="middle" fill="#6db33f">size check</text>
  <line x1="265" y1="45" x2="300" y2="45" stroke="#8b949e" marker-end="url(#amv)"/>
  <rect x="300" y="30" width="120" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="360" y="50" text-anchor="middle" fill="#6db33f">virus scan</text>
  <line x1="420" y1="45" x2="455" y2="45" stroke="#8b949e" marker-end="url(#amv)"/>
  <rect x="455" y="30" width="120" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="515" y="50" text-anchor="middle" fill="#6db33f">transferTo(path)</text>
  <line x1="575" y1="45" x2="610" y2="45" stroke="#8b949e" marker-end="url(#amv)"/>
  <rect x="610" y="30" width="80" height="30" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="650" y="50" text-anchor="middle" fill="#8b949e">saved[]</text>
  <!-- reject arrows down -->
  <line x1="205" y1="60" x2="205" y2="100" stroke="#e74c3c" stroke-dasharray="3,2" marker-end="url(#amr2)"/>
  <line x1="360" y1="60" x2="360" y2="100" stroke="#e74c3c" stroke-dasharray="3,2" marker-end="url(#amr2)"/>
  <rect x="145" y="100" width="275" height="30" rx="4" fill="#1c2430" stroke="#e74c3c"/>
  <text x="282" y="120" text-anchor="middle" fill="#e74c3c">rejected[] (too large / malware)</text>
  <text x="350" y="165" text-anchor="middle" fill="#8b949e" font-size="10">207 Multi-Status returned when any files rejected, 200 when all accepted</text>
  <defs>
    <marker id="amv" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/></marker>
    <marker id="amr2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#e74c3c"/></marker>
  </defs>
</svg>

---

## 6. Walkthrough

**Startup:**

1. Spring Boot detects `spring.servlet.multipart.enabled=true`, registers `StandardServletMultipartResolver` bean named `multipartResolver`.
2. Tomcat's `DefaultServlet` is configured with `max-file-size` and `max-request-size` limits from `application.properties`.

**Per-request flow:**

3. `POST /upload` with `Content-Type: multipart/form-data` arrives at `DispatcherServlet`.
4. `checkMultipart(request)` calls `resolver.isMultipart(request)` — checks `Content-Type` starts with `multipart/`.  Returns `true`.
5. `resolver.resolveMultipart(request)` wraps the raw request in `StandardMultipartHttpServletRequest`; Tomcat parses the multipart body into `Part` objects and streams bytes to OS temp files.
6. `DispatcherServlet.doDispatch()` proceeds with the wrapped request.
7. `RequestMappingHandlerAdapter` resolves method arguments:
   - `@RequestParam("files") List<MultipartFile>` — `RequestParamMethodArgumentResolver` reads all parts named `"files"` from `MultipartHttpServletRequest.getFiles("files")`, wraps each in `StandardMultipartFile`.
8. Controller iterates `files`, checks size, calls `scanner.isMalicious(f.getBytes())`.
9. For accepted files: `f.transferTo(target)` calls `Part.write(target.toString())` — the container moves the temp file (or copies if cross-device), zero additional heap allocation.
10. After the request, `DispatcherServlet.cleanupMultipart(request)` deletes any remaining temp files.

**Request / Response state at each layer:**

| Layer | State |
|---|---|
| Raw request | `Content-Type: multipart/form-data` bytes on socket |
| After `resolveMultipart()` | Parts on OS temp disk; `MultipartFile` handles in memory |
| `getBytes()` call | part bytes loaded into heap for scan |
| `transferTo()` | bytes moved from temp → target path |
| `cleanupMultipart()` | temp files deleted |
| Response | `{"saved":[...],"rejected":[...]}` |

---

## 7. Gotchas & takeaways

> **`MultipartFile.getBytes()` loads the whole file into heap.**  For files larger than a few MB, stream through `getInputStream()` instead, or use `transferTo(Path)` which avoids heap entirely.

> **Temp files are cleaned up by `DispatcherServlet` after the response is committed.**  If you `transferTo()` the multipart file to another path, the original temp file is still cleaned up — that's fine.  If you try to read `getInputStream()` after the response is committed (e.g. in a background thread), the temp file is gone and you get `IOException`.

> **The default bean name `multipartResolver` is required.**  `DispatcherServlet` looks up the resolver by this exact name.  If you name the bean differently, multipart parsing silently falls back to raw `HttpServletRequest`.

- Spring Boot auto-configures `StandardServletMultipartResolver` — no explicit bean needed unless customising.
- `max-file-size` and `max-request-size` are enforced by the servlet container, not Spring — `MaxUploadSizeExceededException` is thrown before the controller runs.
- Always sanitise `getOriginalFilename()` — it is whatever the client sends and can contain `../` path traversal sequences.
- `transferTo(Path)` is the preferred method for saving files — it uses the container's native temp file, avoiding heap allocation.
