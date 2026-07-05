---
card: spring-framework
gi: 323
slug: multipart-requestpart-multipartfile
title: "Multipart (@RequestPart, MultipartFile)"
---

## 1. What it is

When a client sends `Content-Type: multipart/form-data`, each form part is a named section with its own content type. Spring MVC provides two annotations to bind individual parts:

**`@RequestParam`** — binds a multipart text field or file by name:
```java
@PostMapping("/upload")
public String upload(@RequestParam MultipartFile file) { ... }
```

**`@RequestPart`** — binds a multipart part by name and deserializes it via `HttpMessageConverter` if the part's content type is not `text/plain`:
```java
@PostMapping("/products")
public String create(
    @RequestPart("metadata") ProductMetadata metadata,   // JSON part → Jackson
    @RequestPart("photo")    MultipartFile photo) { ... } // binary part
```

`MultipartFile` exposes the file's original name, content type, size, and an `InputStream` or byte array.

---

## 2. Why & when

Use `@RequestParam MultipartFile` for:
- Simple single-file uploads with no accompanying structured data.
- Form submissions where file fields mix with text fields.

Use `@RequestPart` when:
- One part of the multipart request is a JSON/XML document (metadata), another is binary (file).
- The part must be deserialized by `HttpMessageConverter` — `@RequestParam` treats parts as `String` or `MultipartFile` only.
- You want to `@Valid`-validate the JSON part.

Both require a `MultipartResolver` bean — `StandardServletMultipartResolver` is auto-configured by Spring Boot.

---

## 3. Core concept

```
POST /products
Content-Type: multipart/form-data; boundary=----Boundary

------Boundary
Content-Disposition: form-data; name="metadata"
Content-Type: application/json

{"name":"Drill","price":29.99}
------Boundary
Content-Disposition: form-data; name="photo"; filename="drill.jpg"
Content-Type: image/jpeg

[binary JPEG data]
------Boundary--

@RequestPart("metadata") ProductMetadata metadata
  → Content-Type of this part = application/json
  → MappingJackson2HttpMessageConverter.read(ProductMetadata, part.getInputStream())
  → ProductMetadata{name="Drill", price=29.99}

@RequestPart("photo") MultipartFile photo
  → photo.getOriginalFilename() = "drill.jpg"
  → photo.getContentType()      = "image/jpeg"
  → photo.getSize()             = [bytes]
  → photo.transferTo(Path)
```

---

## 4. Diagram

<svg viewBox="0 0 740 260" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="260" fill="#0d1117"/>

  <!-- multipart request -->
  <rect x="10" y="30" width="200" height="120" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="48" text-anchor="middle" fill="#79c0ff">multipart/form-data</text>
  <rect x="20" y="55" width="180" height="38" rx="3" fill="#0d1117" stroke="#6db33f"/>
  <text x="110" y="68" text-anchor="middle" fill="#6db33f" font-size="10">part: metadata</text>
  <text x="110" y="82" text-anchor="middle" fill="#8b949e" font-size="10">Content-Type: application/json</text>
  <rect x="20" y="100" width="180" height="38" rx="3" fill="#0d1117" stroke="#79c0ff"/>
  <text x="110" y="113" text-anchor="middle" fill="#79c0ff" font-size="10">part: photo</text>
  <text x="110" y="127" text-anchor="middle" fill="#8b949e" font-size="10">Content-Type: image/jpeg</text>

  <line x1="210" y1="90" x2="245" y2="90" stroke="#8b949e" marker-end="url(#armp)"/>

  <!-- resolver -->
  <rect x="245" y="30" width="220" height="120" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="355" y="50" text-anchor="middle" fill="#6db33f">MultipartResolver</text>
  <text x="355" y="65" text-anchor="middle" fill="#6db33f">+ RequestPart resolver</text>
  <text x="255" y="85" fill="#8b949e" font-size="10">metadata part: Content-Type=JSON</text>
  <text x="255" y="99" fill="#8b949e" font-size="10">  → Jackson deserializes</text>
  <text x="255" y="113" fill="#8b949e" font-size="10">photo part: Content-Type=image/*</text>
  <text x="255" y="127" fill="#8b949e" font-size="10">  → MultipartFile wrapper</text>

  <line x1="465" y1="90" x2="500" y2="90" stroke="#8b949e" marker-end="url(#armp)"/>

  <!-- handler params -->
  <rect x="500" y="30" width="220" height="120" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="610" y="50" text-anchor="middle" fill="#6db33f">Handler parameters</text>
  <text x="510" y="68" fill="#e6edf3" font-size="11">ProductMetadata metadata</text>
  <text x="510" y="83" fill="#8b949e" font-size="10">  .name()  = "Drill"</text>
  <text x="510" y="97" fill="#8b949e" font-size="10">  .price() = 29.99</text>
  <text x="510" y="112" fill="#e6edf3" font-size="11">MultipartFile photo</text>
  <text x="510" y="127" fill="#8b949e" font-size="10">  .getOriginalFilename()</text>
  <text x="510" y="141" fill="#8b949e" font-size="10">  .transferTo(Path)</text>

  <!-- path traversal note -->
  <rect x="245" y="180" width="360" height="45" rx="5" fill="#1c2430" stroke="#e74c3c" stroke-dasharray="3,2"/>
  <text x="425" y="198" text-anchor="middle" fill="#e74c3c">Security: path traversal</text>
  <text x="425" y="213" text-anchor="middle" fill="#8b949e" font-size="10">NEVER use getOriginalFilename() directly as a path</text>
  <text x="425" y="226" text-anchor="middle" fill="#8b949e" font-size="10">Paths.get(name).getFileName() → safe basename only</text>

  <text x="370" y="255" text-anchor="middle" fill="#8b949e" font-size="11">@RequestPart runs HttpMessageConverter on the part; @RequestParam treats parts as String/bytes</text>

  <defs>
    <marker id="armp" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*`@RequestPart` deserializes structured parts via `HttpMessageConverter`; `MultipartFile` wraps binary parts.*

---

## 5. Runnable example

### Level 1 — Basic

A file upload endpoint using `@RequestParam MultipartFile`:

```java
// UploadController.java
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import java.io.IOException;
import java.nio.file.*;

@RestController
@RequestMapping("/upload")
public class UploadController {

    private static final Path UPLOAD_DIR = Path.of("/tmp/uploads");

    @PostMapping
    public ResponseEntity<String> upload(@RequestParam("file") MultipartFile file)
            throws IOException {

        if (file.isEmpty()) {
            return ResponseEntity.badRequest().body("No file provided");
        }

        // Path traversal prevention: take only the filename, strip any directory prefix
        String safeName = Paths.get(file.getOriginalFilename()).getFileName().toString();
        if (safeName.isBlank()) {
            return ResponseEntity.badRequest().body("Invalid filename");
        }

        Files.createDirectories(UPLOAD_DIR);
        Path dest = UPLOAD_DIR.resolve(safeName);
        file.transferTo(dest);

        return ResponseEntity.ok("Saved: " + safeName + " (" + file.getSize() + " bytes)");
    }
}
```

`application.properties`:
```properties
spring.servlet.multipart.max-file-size=10MB
spring.servlet.multipart.max-request-size=10MB
```

**How to run:**
```bash
./mvnw spring-boot:run

echo "hello" > /tmp/test.txt
curl -X POST http://localhost:8080/upload \
     -F "file=@/tmp/test.txt"
# Saved: test.txt (6 bytes)

# Path traversal attempt — blocked
curl -X POST http://localhost:8080/upload \
     -F "file=@/tmp/test.txt;filename=../../etc/passwd"
# Saved: passwd (6 bytes)  ← only the basename is used
```

`file.getOriginalFilename()` returns the browser-supplied name — untrusted. `Paths.get(name).getFileName()` strips any `../` prefix by returning only the last path component.

---

### Level 2 — Intermediate

Product creation with a JSON metadata part and a photo file part using `@RequestPart`:

```java
// ProductController.java
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import java.io.IOException;
import java.nio.file.*;
import java.util.*;

@RestController
@RequestMapping("/products")
public class ProductController {

    record ProductMetadata(
            @NotBlank String name,
            @Positive double price,
            String description) {}

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<Map<String, Object>> create(
            @RequestPart("metadata") @Valid ProductMetadata metadata,
            @RequestPart(value = "photo", required = false) MultipartFile photo)
            throws IOException {

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("id", System.currentTimeMillis() % 100000);
        result.put("name", metadata.name());
        result.put("price", metadata.price());

        if (photo != null && !photo.isEmpty()) {
            String safeName = Paths.get(photo.getOriginalFilename()).getFileName().toString();
            String contentType = photo.getContentType();

            if (!contentType.startsWith("image/")) {
                return ResponseEntity.badRequest()
                        .body(Map.of("error", "Only image files allowed"));
            }

            Path dest = Path.of("/tmp/uploads").resolve(safeName);
            Files.createDirectories(dest.getParent());
            photo.transferTo(dest);
            result.put("photo", safeName);
            result.put("photoSize", photo.getSize());
        }

        return ResponseEntity.status(HttpStatus.CREATED).body(result);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# With both parts
curl -X POST http://localhost:8080/products \
     -F 'metadata={"name":"Drill","price":29.99,"description":"Cordless"};type=application/json' \
     -F "photo=@/tmp/drill.jpg"
# {"id":54321,"name":"Drill","price":29.99,"photo":"drill.jpg","photoSize":12345}

# Without photo (optional)
curl -X POST http://localhost:8080/products \
     -F 'metadata={"name":"Hammer","price":14.99};type=application/json'
# {"id":54322,"name":"Hammer","price":14.99}

# Invalid JSON metadata → 400 from @Valid
curl -X POST http://localhost:8080/products \
     -F 'metadata={"name":"","price":-1};type=application/json'
# MethodArgumentNotValidException → 400
```

**What changed:** `@RequestPart("metadata")` deserializes the JSON part via Jackson (part's `Content-Type: application/json`). `@Valid` validates the deserialized object. The `photo` part is `required = false` — missing photo is allowed. Content type check prevents non-image uploads.

---

### Level 3 — Advanced

Production scenario: batch file upload with per-file metadata, virus scan gate, and chunked transfer for large files:

```java
// BatchUploadController.java
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.stream.*;

@RestController
@RequestMapping("/files")
public class BatchUploadController {

    private static final long MAX_SINGLE_FILE_BYTES = 50L * 1024 * 1024; // 50 MB
    private static final Path UPLOAD_DIR = Path.of("/tmp/uploads");
    private static final Set<String> ALLOWED_TYPES = Set.of(
            "image/jpeg", "image/png", "application/pdf");

    record UploadResult(String name, long bytes, String status, String error) {}

    @PostMapping(value = "/batch",
                 consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<List<UploadResult>> batchUpload(
            @RequestParam("files") List<MultipartFile> files,
            @RequestParam(value = "folder", defaultValue = "default") String folder)
            throws IOException {

        // Prevent path traversal in folder name
        String safeFolder = Paths.get(folder).getFileName().toString();
        if (safeFolder.isBlank()) safeFolder = "default";

        Path dest = UPLOAD_DIR.resolve(safeFolder);
        Files.createDirectories(dest);

        List<UploadResult> results = new ArrayList<>();

        for (MultipartFile file : files) {
            String safeName = Paths.get(
                    Objects.requireNonNullElse(file.getOriginalFilename(), "unnamed"))
                    .getFileName().toString();

            // Validate size
            if (file.getSize() > MAX_SINGLE_FILE_BYTES) {
                results.add(new UploadResult(safeName, file.getSize(), "REJECTED",
                        "Exceeds 50 MB limit"));
                continue;
            }

            // Validate content type
            String ct = file.getContentType();
            if (!ALLOWED_TYPES.contains(ct)) {
                results.add(new UploadResult(safeName, file.getSize(), "REJECTED",
                        "Type not allowed: " + ct));
                continue;
            }

            // Read first 8 bytes for magic number check
            byte[] header = new byte[8];
            try (InputStream is = file.getInputStream()) {
                int read = is.read(header);
                if (!isMagicValid(ct, header, read)) {
                    results.add(new UploadResult(safeName, file.getSize(), "REJECTED",
                            "Content-type/magic mismatch"));
                    continue;
                }
            }

            // Save (transferTo streams internally — no full in-memory buffer needed)
            Path filePath = dest.resolve(safeName);
            file.transferTo(filePath);
            results.add(new UploadResult(safeName, file.getSize(), "SAVED", null));
        }

        boolean anyFailed = results.stream().anyMatch(r -> "REJECTED".equals(r.status()));
        HttpStatus status = anyFailed ? HttpStatus.MULTI_STATUS : HttpStatus.OK;
        return ResponseEntity.status(status).body(results);
    }

    private boolean isMagicValid(String ct, byte[] header, int read) {
        if (read < 4) return false;
        return switch (ct) {
            case "image/jpeg" -> header[0] == (byte)0xFF && header[1] == (byte)0xD8;
            case "image/png"  -> header[0] == (byte)0x89 && header[1] == 'P';
            case "application/pdf" -> header[0] == '%' && header[1] == 'P';
            default -> false;
        };
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Batch upload
curl -X POST "http://localhost:8080/files/batch?folder=products" \
     -F "files=@/tmp/drill.jpg" \
     -F "files=@/tmp/manual.pdf" \
     -F "files=@/tmp/script.sh"
# [
#   {"name":"drill.jpg","bytes":12345,"status":"SAVED","error":null},
#   {"name":"manual.pdf","bytes":54321,"status":"SAVED","error":null},
#   {"name":"script.sh","bytes":123,"status":"REJECTED","error":"Type not allowed: text/x-sh"}
# ]
# HTTP/1.1 207 Multi-Status (some rejected)
```

**What changed and why:**
- `List<MultipartFile> files` binds multiple files from the same part name — the client sends multiple `-F "files=@..."` entries.
- Magic number check (`isMagicValid`) verifies the file's actual binary signature against the claimed `Content-Type` — prevents MIME spoofing (renaming `script.sh` to `image.jpg` is detected).
- `file.transferTo(path)` streams the upload to disk without loading the full file into memory — critical for large files.
- Per-file results allow partial success — the `207 Multi-Status` response tells the client which files succeeded and which failed.

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="190" fill="#0d1117"/>
  <text x="350" y="20" text-anchor="middle" fill="#8b949e">Batch upload validation pipeline per file</text>

  <rect x="10" y="35" width="100" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="60" y="54" text-anchor="middle" fill="#79c0ff">MultipartFile</text>
  <line x1="110" y1="50" x2="135" y2="50" stroke="#8b949e" marker-end="url(#armp2)"/>

  <rect x="135" y="35" width="110" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="190" y="54" text-anchor="middle" fill="#6db33f">size ≤ 50 MB?</text>
  <line x1="245" y1="50" x2="270" y2="50" stroke="#8b949e" marker-end="url(#armp2)"/>

  <rect x="270" y="35" width="130" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="335" y="54" text-anchor="middle" fill="#6db33f">content-type allowed?</text>
  <line x1="400" y1="50" x2="425" y2="50" stroke="#8b949e" marker-end="url(#armp2)"/>

  <rect x="425" y="35" width="120" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="485" y="54" text-anchor="middle" fill="#6db33f">magic number match?</text>
  <line x1="545" y1="50" x2="570" y2="50" stroke="#8b949e" marker-end="url(#armp2)"/>

  <rect x="570" y="35" width="110" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="625" y="54" text-anchor="middle" fill="#6db33f">transferTo(path)</text>

  <!-- reject paths -->
  <line x1="190" y1="65" x2="190" y2="100" stroke="#e74c3c" stroke-dasharray="2,2"/>
  <line x1="335" y1="65" x2="335" y2="100" stroke="#e74c3c" stroke-dasharray="2,2"/>
  <line x1="485" y1="65" x2="485" y2="100" stroke="#e74c3c" stroke-dasharray="2,2"/>
  <rect x="100" y="100" width="480" height="24" rx="3" fill="#1c2430" stroke="#e74c3c"/>
  <text x="340" y="116" text-anchor="middle" fill="#e74c3c" font-size="10">REJECTED with reason → included in 207 Multi-Status response</text>

  <text x="350" y="152" text-anchor="middle" fill="#8b949e" font-size="10">getOriginalFilename() is untrusted — always use Paths.get(name).getFileName().toString()</text>
  <text x="350" y="170" text-anchor="middle" fill="#8b949e" font-size="10">transferTo() streams to disk — no full in-memory buffer; safe for large files</text>
  <defs><marker id="armp2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/></marker></defs>
</svg>

---

## 6. Walkthrough

**Per-request: `POST /files/batch` with 2 files:**

1. `StandardServletMultipartResolver` parses `multipart/form-data` → `MultipartHttpServletRequest`.
2. `@RequestParam("files") List<MultipartFile> files` → resolver collects all parts named `"files"` into a list.
3. `@RequestParam("folder") String folder` → `"products"`.
4. Safe folder: `Paths.get("products").getFileName()` → `"products"`.
5. `Files.createDirectories(/tmp/uploads/products)`.
6. **File 1** (`drill.jpg`): size=12345 (≤50 MB), content-type=`image/jpeg` (allowed), magic=`FF D8` (JPEG) → `transferTo(/tmp/uploads/products/drill.jpg)` → `SAVED`.
7. **File 2** (`script.sh`): content-type=`text/x-sh` (not in `ALLOWED_TYPES`) → `REJECTED`, magic check skipped.
8. `anyFailed = true` → `207 Multi-Status`.
9. Response: JSON array with per-file results.

**State at each layer:**

| Layer | Data |
|---|---|
| Multipart body | 2 parts named `files`, 1 param `folder=products` |
| `files` param | `List<MultipartFile>[drill.jpg, script.sh]` |
| Validation loop | drill.jpg passes all checks; script.sh fails content-type |
| Disk | `/tmp/uploads/products/drill.jpg` written |
| Response | `207 Multi-Status`, JSON with per-file status |

---

## 7. Gotchas & takeaways

> **`getOriginalFilename()` is controlled by the client.** It can contain `../../../etc/passwd`. Always call `Paths.get(name).getFileName().toString()` to strip directory components before using the name as a path segment.

> **`@RequestPart` requires the part to have a `Content-Type` header for JSON deserialization.** When sending from `curl`, use `;type=application/json` on the `-F` flag. Without it, the part is treated as `text/plain` and Jackson cannot deserialize it.

> **`MultipartFile.getSize()` returns the declared size from the multipart header, not the actual file size.** In practice they match, but use `Files.size(savedPath)` for authoritative size after saving.

- `@RequestParam MultipartFile` — simple file; `@RequestPart` — JSON/XML + binary mix.
- `transferTo(Path)` streams to disk without buffering the entire file in memory.
- Validate: safe filename (`getFileName()`), content type allowlist, magic number check for MIME spoofing.
- `List<MultipartFile>` binds multiple files from the same form field name.
- `spring.servlet.multipart.max-file-size` and `max-request-size` set the upload limit; `MaxUploadSizeExceededException` is thrown on violation.
