---
card: spring-data
gi: 109
slug: gridfs-support
title: "GridFS support"
---

## 1. What it is

GridFS is MongoDB's mechanism for storing files larger than the 16MB document size limit — it splits a file into smaller chunks stored as ordinary documents in a `fs.chunks` collection, with metadata tracked in a paired `fs.files` collection, and Spring Data MongoDB's `GridFsTemplate` provides `store`/`find`/`getResource` operations that hide the chunking mechanics behind a simple stream-in, stream-out API.

```java
@Autowired GridFsTemplate gridFsTemplate;

ObjectId fileId = gridFsTemplate.store(inputStream, "invoice-2024.pdf", "application/pdf");
GridFSFile file = gridFsTemplate.findOne(Query.query(Criteria.where("_id").is(fileId)));
GridFsResource resource = gridFsTemplate.getResource(file);
```

## 2. Why & when

Every entity mapped in the earlier document-mapping card fits comfortably within a normal document's size limits — but binary files (PDFs, images, videos) routinely exceed MongoDB's 16MB single-document limit, and even well under that limit, storing large binary blobs directly inside ordinary documents bloats query results and working-set memory usage unnecessarily. GridFS solves this by storing large files as a stream of chunks, retrievable without loading the whole file into memory at once.

Reach for GridFS specifically when:

- Storing files that might exceed (or even just approach) MongoDB's 16MB document size limit — GridFS has no such limit, since files are split into many small chunks.
- You want to stream a large file's contents in and out without loading the entire file into application memory at once — `GridFsTemplate`'s stream-based API supports this directly.
- You need file metadata (filename, content type, upload date, custom metadata) queryable alongside the file content itself — `fs.files` documents support arbitrary additional metadata fields, queryable like any other collection.

## 3. Core concept

```
 gridFsTemplate.store(inputStream, "invoice.pdf", "application/pdf")
   -- file is split into N chunks (default 255KB each), stored in fs.chunks
   -- ONE metadata document stored in fs.files: {filename, contentType, length, chunkSize, uploadDate, ...}

 gridFsTemplate.findOne(query) -> GridFSFile   -- metadata only, no chunk data loaded yet
 gridFsTemplate.getResource(file) -> GridFsResource  -- a STREAM over the reassembled chunks

 Reading the file: streams chunks back in order, reassembling the original content
                    WITHOUT ever loading the entire file into memory at once
```

Files are split into chunks on write and reassembled as a stream on read — the application never needs to hold the whole file in memory at either end.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="A large file is split into chunks stored in fs.chunks, with metadata tracked separately in fs.files, and streamed back on read">
  <rect x="20" y="20" width="180" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">invoice.pdf (5MB)</text>

  <rect x="250" y="15" width="200" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="35" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">fs.chunks</text>
  <text x="350" y="52" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">~20 chunks of 255KB each</text>
  <text x="350" y="65" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ordered by chunk index</text>

  <rect x="480" y="15" width="140" height="55" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="550" y="35" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">fs.files</text>
  <text x="550" y="52" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">filename, contentType,</text>
  <text x="550" y="65" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">length, uploadDate</text>

  <rect x="150" y="110" width="340" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="320" y="135" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">getResource(file) -&gt; stream reassembles chunks in order</text>

  <line x1="200" y1="42" x2="245" y2="42" stroke="#8b949e" stroke-width="1.3" marker-end="url(#gf)"/>
  <line x1="200" y1="42" x2="475" y2="42" stroke="#8b949e" stroke-width="1.3" marker-end="url(#gf)"/>
  <defs><marker id="gf" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

One file becomes many small chunks plus one metadata document; reading it back reassembles the chunks in order as a stream.

## 5. Runnable example

The scenario: storing and retrieving a file, evolving from a naive whole-file-in-memory model showing the size-limit problem, to a chunked storage model matching GridFS's actual mechanics, to querying stored files by metadata without touching their content.

### Level 1 — Basic

Show the problem GridFS solves: storing an entire large file as one unit runs into the document size limit.

```java
import java.util.*;

class FileTooLargeException extends RuntimeException { FileTooLargeException(String msg) { super(msg); } }

public class GridFsLevel1 {
    static final int MONGODB_DOCUMENT_LIMIT_BYTES = 16 * 1024 * 1024; // 16MB

    // Simulates storing an entire file as ONE document -- fails if it exceeds MongoDB's document size limit.
    static void storeAsOneDocument(byte[] fileContent) {
        if (fileContent.length > MONGODB_DOCUMENT_LIMIT_BYTES) {
            throw new FileTooLargeException("File is " + fileContent.length + " bytes, exceeds the "
                + MONGODB_DOCUMENT_LIMIT_BYTES + "-byte document limit");
        }
        System.out.println("Stored " + fileContent.length + " bytes as a single document.");
    }

    public static void main(String[] args) {
        byte[] smallFile = new byte[1024]; // 1KB, fine
        storeAsOneDocument(smallFile);

        byte[] hugeFile = new byte[20 * 1024 * 1024]; // 20MB, exceeds the limit
        try {
            storeAsOneDocument(hugeFile);
        } catch (FileTooLargeException e) {
            System.out.println("Failed: " + e.getMessage());
        }
    }
}
```

How to run: `java GridFsLevel1.java`

The 20MB file fails outright — this is exactly the problem GridFS exists to solve: a single document (even one holding just raw binary data) cannot exceed MongoDB's 16MB limit, no matter how the data is encoded.

### Level 2 — Intermediate

Model GridFS's chunking mechanism: split the same large file into fixed-size chunks, each individually well under the document limit, and store them alongside one metadata document.

```java
import java.util.*;

record FileChunk(int index, byte[] data) {}
record FileMetadata(String id, String filename, String contentType, long length, int chunkSize) {}

public class GridFsLevel2 {
    static final int CHUNK_SIZE = 255 * 1024; // GridFS's default chunk size: 255KB

    // Simulates gridFsTemplate.store(inputStream, filename, contentType)
    static FileMetadata storeChunked(byte[] fileContent, String filename, String contentType, List<FileChunk> chunksOut) {
        int chunkCount = (int) Math.ceil((double) fileContent.length / CHUNK_SIZE);
        for (int i = 0; i < chunkCount; i++) {
            int start = i * CHUNK_SIZE;
            int end = Math.min(start + CHUNK_SIZE, fileContent.length);
            chunksOut.add(new FileChunk(i, Arrays.copyOfRange(fileContent, start, end)));
        }
        return new FileMetadata(UUID.randomUUID().toString(), filename, contentType, fileContent.length, CHUNK_SIZE);
    }

    public static void main(String[] args) {
        byte[] hugeFile = new byte[20 * 1024 * 1024]; // 20MB -- would have failed in Level 1
        List<FileChunk> chunks = new ArrayList<>();

        FileMetadata metadata = storeChunked(hugeFile, "large-report.pdf", "application/pdf", chunks);

        System.out.println("Stored as metadata: " + metadata);
        System.out.println("Split into " + chunks.size() + " chunks of up to " + metadata.chunkSize() + " bytes each");
        System.out.println("Largest single chunk is WELL under the 16MB document limit.");
    }
}
```

How to run: `java GridFsLevel2.java`

The same 20MB file that failed in Level 1 now succeeds — split into roughly 82 chunks of 255KB each, each individually a tiny fraction of the 16MB document limit, plus one small `FileMetadata` document. This is exactly the mechanism `gridFsTemplate.store(...)` performs internally against real `fs.chunks`/`fs.files` collections.

### Level 3 — Advanced

Add reading the file back — reassembling chunks in order into a stream — and a metadata-only query that finds a file by its filename without touching any chunk data at all.

```java
import java.util.*;
import java.util.stream.*;

record FileChunk(int index, byte[] data) {}
record FileMetadata(String id, String filename, String contentType, long length) {}

public class GridFsLevel3 {
    static final int CHUNK_SIZE = 255 * 1024;

    static FileMetadata storeChunked(byte[] fileContent, String filename, String contentType,
                                       Map<String, List<FileChunk>> chunkStore, Map<String, FileMetadata> metadataStore) {
        List<FileChunk> chunks = new ArrayList<>();
        int chunkCount = (int) Math.ceil((double) fileContent.length / CHUNK_SIZE);
        for (int i = 0; i < chunkCount; i++) {
            int start = i * CHUNK_SIZE;
            int end = Math.min(start + CHUNK_SIZE, fileContent.length);
            chunks.add(new FileChunk(i, Arrays.copyOfRange(fileContent, start, end)));
        }
        String id = UUID.randomUUID().toString();
        FileMetadata metadata = new FileMetadata(id, filename, contentType, fileContent.length);
        chunkStore.put(id, chunks);
        metadataStore.put(id, metadata);
        return metadata;
    }

    // gridFsTemplate.getResource(file) -- reassembles chunks IN ORDER into the original byte stream.
    static byte[] readAsStream(String fileId, Map<String, List<FileChunk>> chunkStore) {
        List<FileChunk> chunks = chunkStore.get(fileId);
        chunks.sort(Comparator.comparingInt(FileChunk::index)); // MUST reassemble in order
        int totalLength = chunks.stream().mapToInt(c -> c.data().length).sum();
        byte[] result = new byte[totalLength];
        int offset = 0;
        for (FileChunk chunk : chunks) {
            System.arraycopy(chunk.data(), 0, result, offset, chunk.data().length);
            offset += chunk.data().length;
        }
        return result;
    }

    // gridFsTemplate.findOne(Query.query(Criteria.where("filename").is(name))) -- metadata query, NO chunk data touched.
    static Optional<FileMetadata> findByFilename(Map<String, FileMetadata> metadataStore, String filename) {
        return metadataStore.values().stream().filter(m -> m.filename().equals(filename)).findFirst();
    }

    public static void main(String[] args) {
        Map<String, List<FileChunk>> chunkStore = new HashMap<>();
        Map<String, FileMetadata> metadataStore = new HashMap<>();

        byte[] original = new byte[1024 * 1024]; // 1MB
        new Random(42).nextBytes(original); // fill with deterministic "content"

        FileMetadata stored = storeChunked(original, "report.pdf", "application/pdf", chunkStore, metadataStore);
        System.out.println("Stored '" + stored.filename() + "' as " + chunkStore.get(stored.id()).size() + " chunks");

        // Find by metadata WITHOUT touching any chunk data.
        FileMetadata found = findByFilename(metadataStore, "report.pdf").orElseThrow();
        System.out.println("Found by filename: length=" + found.length() + " bytes (no chunks read yet)");

        // NOW read the actual content, reassembling chunks in order.
        byte[] reassembled = readAsStream(found.id(), chunkStore);
        System.out.println("Reassembled length: " + reassembled.length + " bytes");
        System.out.println("Content matches original? " + Arrays.equals(original, reassembled));
    }
}
```

How to run: `java GridFsLevel3.java`

`findByFilename` locates the file purely from its metadata document, never touching `chunkStore` at all — matching how a real `gridFsTemplate.findOne(...)` query only reads `fs.files`. Only `readAsStream` actually reassembles the chunks, sorting by `index` to guarantee correct byte order before concatenating — and `Arrays.equals(original, reassembled)` confirms the reassembled bytes exactly match what was originally stored, proving the chunk-split-and-reassemble round trip preserves the file's content perfectly.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `original` is filled with 1MB of deterministic pseudo-random bytes (seeded, so the exact same bytes would be generated again if needed for verification). `storeChunked(original, "report.pdf", ...)` runs: it splits `original` into chunks of up to `CHUNK_SIZE` (255KB) each — for a 1MB file, this produces 5 chunks (four full 255KB chunks and one smaller final chunk) — stores them in `chunkStore` keyed by a generated file ID, and stores a `FileMetadata` record (filename, content type, total length) in `metadataStore` under the same ID.

`findByFilename(metadataStore, "report.pdf")` runs next: it searches only `metadataStore` for a matching filename, finding `stored`'s metadata without ever looking at `chunkStore` — this mirrors exactly how a real GridFS metadata query (`gridFsTemplate.findOne(...)`) never touches the potentially much larger `fs.chunks` collection just to answer "does a file with this name exist, and how big is it."

Finally, `readAsStream(found.id(), chunkStore)` runs: it retrieves the list of chunks for that file ID, sorts them by `index` (critical, since chunks might not be stored or retrieved in original order), computes the total reassembled length, and copies each chunk's bytes into the correct position of a new `result` array using `System.arraycopy`, advancing `offset` by each chunk's length as it goes.

The final comparison, `Arrays.equals(original, reassembled)`, confirms `true` — every byte of the original 1MB file was correctly preserved through the split-into-chunks-then-reassemble round trip.

```
storeChunked(1MB file):  splits into 5 chunks (255KB x4 + smaller remainder), stores metadata separately

findByFilename("report.pdf"):  metadata-only lookup, chunkStore never touched

readAsStream(fileId):  sort chunks by index -> concatenate in order -> reassembled == original (byte-for-byte)
```

In a real Spring Data MongoDB application, `gridFsTemplate.store(inputStream, "report.pdf", "application/pdf")` streams the file's bytes directly from the `InputStream` into MongoDB, chunking as it goes (never buffering the whole file in application memory), while `gridFsTemplate.getResource(file)` returns a `GridFsResource` that streams the reassembled content back out on demand — a controller serving a large file download can stream it directly to the HTTP response without ever holding the entire file in memory on the application server, regardless of whether the file is 1MB or 1GB.

## 7. Gotchas & takeaways

> Gotcha: deleting a GridFS file requires removing *both* its `fs.files` metadata document and all of its associated `fs.chunks` documents — `gridFsTemplate.delete(query)` handles this correctly when used properly, but manually deleting only the metadata document (e.g., via a raw `mongoTemplate.remove(...)` against `fs.files` directly) leaves orphaned chunk data behind, silently consuming storage indefinitely.

- GridFS splits files exceeding (or approaching) MongoDB's 16MB document size limit into many small chunks, tracked alongside one metadata document per file.
- `GridFsTemplate` provides a stream-based API (`store`/`getResource`) that hides the chunking mechanics, letting files be written and read without loading the entire file into application memory at once.
- Metadata queries (finding a file by name, content type, or custom metadata) never need to touch the potentially much larger chunk data.
- Always delete both the metadata document and its chunks together — use `GridFsTemplate`'s own delete operation rather than manually removing only the metadata document.
