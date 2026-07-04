---
card: spring-framework
gi: 269
slug: handling-lobs
title: Handling LOBs
---

## 1. What it is

**LOB (Large Object)** columns store data too large for standard column types:

- **BLOB** (`Binary Large Object`) — raw bytes: images, PDFs, audio, binary files.
- **CLOB** (`Character Large Object`) — large text: JSON documents, HTML pages, XML, long reports.

Spring JDBC handles LOBs through:
- **`LobCreator`** — creates and binds LOB values to a `PreparedStatement`.
- **`LobHandler`** — reads LOB values from a `ResultSet`.
- **`DefaultLobHandler`** — uses plain JDBC `setBytes` / `setString` / `setBinaryStream` — works with most databases including H2, PostgreSQL, MySQL.
- **`OracleLobHandler`** (legacy) — uses Oracle-specific LOB APIs for older Oracle JDBC drivers.

```java
// Write a BLOB
jdbc.update("UPDATE documents SET content=? WHERE id=?",
    ps -> {
        ps.setBytes(1, pdfBytes);
        ps.setLong(2, docId);
    });

// Read a BLOB
byte[] bytes = jdbc.queryForObject(
    "SELECT content FROM documents WHERE id=?",
    (rs, n) -> rs.getBytes("content"), docId);
```

## 2. Why & when

JDBC `setBytes()`/`getBytes()` works for small BLOBs but loads the entire content into a `byte[]` in memory. For large files (images, videos, exports) the streaming approach — `setBinaryStream` / `getBinaryStream` — is essential to avoid heap exhaustion.

Spring's `LobHandler` / `LobCreator` abstraction:
- Unifies the `setBytes` vs. `setBinaryStream` path.
- Handles transaction-scope LOB lifecycle on databases (like older Oracle) where LOB locators must not outlive their transaction.
- Provides consistent API across `DefaultLobHandler` (modern databases) and older drivers.

**Use LOBs when:**
- Storing user uploads (profile pictures, attachments) directly in the database.
- Persisting configuration blobs, serialised state, or cached processed output.
- Required by existing schema (cannot move to file-system / object-storage).

## 3. Core concept

`DefaultLobHandler` delegates to plain JDBC:

```
Writing BLOB:
  lobCreator.setBlobAsBytes(ps, column, bytes)
    → ps.setBytes(column, bytes)      [for byte[]]
    → ps.setBinaryStream(col, is, len) [for InputStream]

Writing CLOB:
  lobCreator.setClobAsString(ps, column, text)
    → ps.setString(column, text)      [for String]
    → ps.setCharacterStream(col, r, len) [for Reader]

Reading BLOB:
  lobHandler.getBlobAsBytes(rs, column) → byte[]
  lobHandler.getBlobAsBinaryStream(rs, column) → InputStream

Reading CLOB:
  lobHandler.getClobAsString(rs, column) → String
  lobHandler.getClobAsCharacterStream(rs, column) → Reader
```

`LobCreator` is `Closeable` — open it inside a `try-with-resources` so LOB resources allocated during writing are freed after the statement executes.

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="arr2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
  </defs>

  <!-- Write path -->
  <text x="10" y="25" fill="#8b949e" font-size="9" font-family="sans-serif">WRITE path</text>
  <rect x="10" y="35" width="110" height="40" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="65" y="53" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">byte[] / InputStream</text>
  <text x="65" y="68" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">String / Reader</text>

  <line x1="122" y1="55" x2="165" y2="55" stroke="#6db33f" stroke-width="1" marker-end="url(#arr)"/>

  <rect x="167" y="30" width="140" height="50" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="237" y="50" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">LobCreator</text>
  <text x="237" y="65" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">setBlob/ClobAs*(ps,col,data)</text>

  <line x1="309" y1="55" x2="352" y2="55" stroke="#6db33f" stroke-width="1" marker-end="url(#arr)"/>

  <rect x="354" y="30" width="150" height="50" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="429" y="50" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">PreparedStatement</text>
  <text x="429" y="65" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">setBytes/setBinaryStream</text>

  <line x1="506" y1="55" x2="549" y2="55" stroke="#6db33f" stroke-width="1" marker-end="url(#arr)"/>
  <rect x="551" y="35" width="80" height="40" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="591" y="58" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">DB</text>

  <!-- Read path -->
  <text x="10" y="125" fill="#8b949e" font-size="9" font-family="sans-serif">READ path</text>
  <rect x="551" y="135" width="80" height="40" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="591" y="158" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">DB</text>
  <line x1="549" y1="155" x2="506" y2="155" stroke="#79c0ff" stroke-width="1" marker-end="url(#arr2)"/>

  <rect x="354" y="130" width="150" height="50" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="429" y="150" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">ResultSet</text>
  <text x="429" y="165" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">getBytes/getBinaryStream</text>
  <line x1="352" y1="155" x2="309" y2="155" stroke="#79c0ff" stroke-width="1" marker-end="url(#arr2)"/>

  <rect x="167" y="130" width="140" height="50" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="237" y="150" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">LobHandler</text>
  <text x="237" y="165" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">getBlob/ClobAs*(rs,col)</text>
  <line x1="165" y1="155" x2="122" y2="155" stroke="#79c0ff" stroke-width="1" marker-end="url(#arr2)"/>

  <rect x="10" y="135" width="110" height="40" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="65" y="155" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">byte[] / InputStream</text>
  <text x="65" y="168" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">String / Reader</text>
</svg>

`LobCreator` and `LobHandler` abstract the JDBC LOB API — write via `LobCreator`, read via `LobHandler`.

## 5. Runnable example

Scenario: a **document archive** — store and retrieve documents with BLOB (binary content) and CLOB (text summary), progressing from `setBytes`/`getBytes` through streaming to the full `LobHandler` API.

### Level 1 — Basic

Store and retrieve a small binary file and text using `setBytes` / `getBytes` directly.

```java
// LobDemo.java
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.nio.charset.StandardCharsets;

public class LobDemo {

    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:document-schema.sql")
            .build();
    }

    public static void main(String[] args) {
        JdbcTemplate jdbc = new JdbcTemplate(buildDs());

        // Simulate a PDF as a byte array
        byte[] fakeBytes = "FAKE PDF CONTENT — binary data here".getBytes(StandardCharsets.UTF_8);
        String summary   = "Annual report for fiscal year 2024. Contains financial statements.";

        // INSERT: bind byte[] and String directly — fine for small LOBs
        jdbc.update("INSERT INTO documents(title,content,summary) VALUES(?,?,?)",
            "Annual Report 2024", fakeBytes, summary);

        // SELECT: retrieve as byte[] and String
        jdbc.query("SELECT id,title,content,summary FROM documents", rs -> {
            byte[] content = rs.getBytes("content");
            String txt     = rs.getString("summary");
            System.out.printf("Doc[%d] %s%n", rs.getLong("id"), rs.getString("title"));
            System.out.printf("  BLOB size: %d bytes%n", content.length);
            System.out.printf("  CLOB: %s%n", txt);
        });
    }
}
```

`document-schema.sql`:
```sql
CREATE TABLE documents (
  id      BIGINT AUTO_INCREMENT PRIMARY KEY,
  title   VARCHAR(200),
  content BLOB,
  summary CLOB
);
```

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. LobDemo.java`

`ps.setBytes(1, fakeBytes)` sends the full byte array in memory — fine for small files (up to a few MB). `rs.getBytes("content")` loads the full BLOB into a `byte[]`. For files under ~1 MB, this approach is simple and correct.

---

### Level 2 — Intermediate

`DefaultLobHandler` + `LobCreator` with streaming insert + streaming read.

```java
// LobDemo.java
import org.springframework.jdbc.core.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.jdbc.support.lob.*;
import javax.sql.DataSource;
import java.io.*;
import java.nio.charset.StandardCharsets;

public class LobDemo {

    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:document-schema.sql")
            .build();
    }

    public static void main(String[] args) throws Exception {
        JdbcTemplate jdbc = new JdbcTemplate(buildDs());
        DefaultLobHandler lobHandler = new DefaultLobHandler();

        // Simulate a "large" binary payload via InputStream
        byte[] bigBytes = ("PDF BINARY CONTENT — ".repeat(100)).getBytes(StandardCharsets.UTF_8);
        InputStream binaryStream = new ByteArrayInputStream(bigBytes);

        String longSummary = "This is a very detailed summary. " .repeat(50);
        Reader textReader  = new StringReader(longSummary);

        // Write via LobCreator (try-with-resources ensures cleanup)
        try (LobCreator lobCreator = lobHandler.getLobCreator()) {
            jdbc.update(
                "INSERT INTO documents(title,content,summary) VALUES(?,?,?)",
                ps -> {
                    ps.setString(1, "Technical Manual");
                    lobCreator.setBlobAsBinaryStream(ps, 2, binaryStream, bigBytes.length);
                    lobCreator.setClobAsCharacterStream(ps, 3, textReader, longSummary.length());
                }
            );
        }

        // Read via LobHandler — streaming
        jdbc.query("SELECT id,title,content,summary FROM documents", rs -> {
            String title = rs.getString("title");
            // Read BLOB as stream — don't buffer entire thing
            try (InputStream is = lobHandler.getBlobAsBinaryStream(rs, "content")) {
                int size = is.readAllBytes().length;
                System.out.printf("BLOB '%s': %d bytes%n", title, size);
            } catch (IOException e) { e.printStackTrace(); }
            // Read CLOB as String
            String summary = lobHandler.getClobAsString(rs, "summary");
            System.out.printf("CLOB length: %d chars%n", summary.length());
        });
    }
}
```

How to run: same classpath

`lobHandler.getLobCreator()` returns a `LobCreator` that must be closed after the `update()` — wrap in `try-with-resources`. `setBlobAsBinaryStream(ps, col, stream, length)` calls `ps.setBinaryStream(col, stream, length)` — the JDBC driver reads from the stream during execution without loading all bytes into a single `byte[]`. `getBlobAsBinaryStream(rs, col)` similarly returns an `InputStream` — read it and close it before moving off the row.

---

### Level 3 — Advanced

Multiple documents with LOBs, `RowMapper`-based extraction, and bulk insert.

```java
// LobDemo.java
import org.springframework.jdbc.core.*;
import org.springframework.jdbc.core.namedparam.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.jdbc.support.lob.*;
import javax.sql.DataSource;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

record Document(long id, String title, int contentSize, String summaryPreview) {}

public class LobDemo {

    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:document-schema.sql")
            .build();
    }

    static byte[] fakePdf(String label, int size) {
        byte[] base = ("PDF:" + label + " ").getBytes(StandardCharsets.UTF_8);
        byte[] buf  = new byte[size];
        for (int i = 0; i < size; i++) buf[i] = base[i % base.length];
        return buf;
    }

    public static void main(String[] args) throws Exception {
        JdbcTemplate jdbc = new JdbcTemplate(buildDs());
        DefaultLobHandler lob = new DefaultLobHandler();

        // Insert multiple documents with LOBs
        List<String> titles = List.of("Invoice","Contract","Report","Manual");
        for (int i = 0; i < titles.size(); i++) {
            String title = titles.get(i);
            byte[] pdf   = fakePdf(title, 1024 * (i + 1));  // 1–4 KB
            String summary = "Summary for " + title + ". " .repeat(20);
            final InputStream is = new ByteArrayInputStream(pdf);
            final Reader r  = new StringReader(summary);
            final int pdfLen = pdf.length, sumLen = summary.length();

            try (LobCreator lc = lob.getLobCreator()) {
                jdbc.update(
                    "INSERT INTO documents(title,content,summary) VALUES(?,?,?)",
                    ps -> {
                        ps.setString(1, title);
                        lc.setBlobAsBinaryStream(ps, 2, is, pdfLen);
                        lc.setClobAsCharacterStream(ps, 3, r, sumLen);
                    }
                );
            }
        }

        // RowMapper that reads LOB metadata without buffering full content
        RowMapper<Document> docMapper = (rs, n) -> {
            long   id     = rs.getLong("id");
            String title  = rs.getString("title");
            byte[] bytes  = lob.getBlobAsBytes(rs, "content");   // full bytes — OK for small LOBs
            String sum    = lob.getClobAsString(rs, "summary");
            return new Document(id, title, bytes.length, sum.substring(0, Math.min(30, sum.length())));
        };

        List<Document> docs = jdbc.query(
            "SELECT id,title,content,summary FROM documents ORDER BY id", docMapper);
        System.out.println("Documents:");
        docs.forEach(d -> System.out.printf(
            "  [%d] %-12s BLOB=%,d bytes  CLOB preview='%s...'%n",
            d.id(), d.title(), d.contentSize(), d.summaryPreview()));

        // Update one document's BLOB
        byte[] updated = fakePdf("InvoiceV2", 2048);
        try (LobCreator lc = lob.getLobCreator();
             InputStream is = new ByteArrayInputStream(updated)) {
            jdbc.update(
                "UPDATE documents SET content=? WHERE title=?",
                ps -> {
                    lc.setBlobAsBinaryStream(ps, 1, is, updated.length);
                    ps.setString(2, "Invoice");
                }
            );
        }
        Integer newSize = jdbc.queryForObject(
            "SELECT LENGTH(content) FROM documents WHERE title=?", Integer.class, "Invoice");
        System.out.println("Updated Invoice BLOB size: " + newSize + " bytes");
    }
}
```

How to run: same classpath

`lob.getBlobAsBytes(rs, "content")` is appropriate for small LOBs (under ~10 MB) — it loads the full content into `byte[]`. For larger blobs use `getBlobAsBinaryStream()` and process the stream without accumulating bytes. Each `LobCreator` wraps one or more `ps.setXxx` calls and must be closed after the `update()` executes.

## 6. Walkthrough

**Level 2 — streaming BLOB insert and read (execution order):**

1. **`lobHandler.getLobCreator()`**: `DefaultLobHandler.getLobCreator()` returns a `DefaultLobCreator` — a thin wrapper, no DB interaction yet.
2. **`jdbc.update(sql, pss)` call**: `JdbcTemplate` acquires a connection, calls `con.prepareStatement("INSERT INTO documents(title,content,summary) VALUES(?,?,?)")`.
3. **Parameter binding** (inside the lambda):
   - `ps.setString(1, "Technical Manual")` — binds the title.
   - `lobCreator.setBlobAsBinaryStream(ps, 2, binaryStream, bigBytes.length)` → calls `ps.setBinaryStream(2, binaryStream, bigBytes.length)` — the JDBC driver registers the stream; it will read it during `executeUpdate()`.
   - `lobCreator.setClobAsCharacterStream(ps, 3, textReader, longSummary.length())` → `ps.setCharacterStream(3, textReader, len)`.
4. **`ps.executeUpdate()`**: JDBC driver reads from `binaryStream` and `textReader`, sends bytes to H2. H2 stores them in the BLOB and CLOB columns.
5. **`lobCreator.close()`**: `DefaultLobCreator.close()` is a no-op for H2 (Oracle LobCreator would release temporary LOBs here). `try-with-resources` ensures this always runs.
6. **Read** `lobHandler.getBlobAsBinaryStream(rs, "content")`: calls `rs.getBinaryStream("content")` — H2 returns a stream backed by the stored bytes. Caller reads all bytes, gets the size.

```
Write:
  ps.setBinaryStream(2, stream, 2000)  → H2 stores 2000 bytes as BLOB
  ps.setCharacterStream(3, reader, 1650) → H2 stores 1650 chars as CLOB

Read:
  rs.getBinaryStream("content") → InputStream over stored 2000 bytes
  rs.getString("summary") → full CLOB as String
```

## 7. Gotchas & takeaways

> **`LobCreator` MUST be closed after the update.** Even with `DefaultLobHandler` (where `close()` is a no-op), always use `try-with-resources` — if you ever switch to an Oracle or other driver that allocates temporary LOBs, the close becomes essential and you won't need to change the code.

> **Don't call `rs.getBinaryStream()` after moving off the row.** JDBC `InputStream`s from `ResultSet` are invalidated when you call `rs.next()`. Read or buffer the content before advancing the cursor — or use `getBytes()` for small blobs to materialise the data immediately.

> **H2 `BLOB` columns accept `setBytes()` and `setBinaryStream()` equally.** Production databases (PostgreSQL, MySQL, Oracle) have specific rules — PostgreSQL uses `bytea` for small blobs or the `lo` extension for large ones; Oracle requires Oracle-specific LOB locators for > 4 KB. Test against the actual database type before deploying LOB code.

- `LobCreator.setBlobAsBytes` / `setBlobAsBinaryStream` — write LOBs; use streaming for large data.
- `LobHandler.getBlobAsBytes` / `getBlobAsBinaryStream` — read LOBs; use streaming to avoid heap pressure.
- `DefaultLobHandler` — works for H2, PostgreSQL, MySQL; use for most modern databases.
- Always `try-with-resources` around `LobCreator` — essential for Oracle-style LOB locators.
- `rs.getBinaryStream()` is invalidated on `rs.next()` — read it before advancing the cursor.
