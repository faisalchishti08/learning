---
card: spring-integration
gi: 51
slug: ftp-ftps-adapters
title: "FTP / FTPS adapters"
---

## 1. What it is

Spring Integration's FTP support mirrors the file-support adapters from card 0050, but for a remote FTP (or FTPS, its TLS-secured variant) server instead of the local file system: `FtpInboundFileSynchronizingMessageSource` polls a remote directory, downloads new files to a local staging directory, and emits a `Message<File>` for each; `FtpMessageHandler` is the outbound adapter that uploads a message's payload to a remote FTP directory. Both are built on a shared `SessionFactory<FTPFile>` abstraction that manages the actual FTP connection and authentication.

## 2. Why & when

You reach for the FTP adapters specifically when the external system a flow integrates with is a remote FTP server, a common integration point with older systems, batch-file-exchange partners, and many enterprise data pipelines:

- **A trading partner or legacy system drops files onto a remote FTP server for you to pick up** — `FtpInboundFileSynchronizingMessageSource` polls that remote directory on a schedule (the same polling-consumer mechanics from card 0035) and synchronizes new files down to a local directory, from which they can then be read exactly like any local file (card 0050).
- **A flow's output needs to be delivered to a remote FTP server**, such as a nightly export a downstream partner expects to retrieve from a specific FTP directory — `FtpMessageHandler` performs that upload as its outbound side effect.
- **Security requirements mandate encrypted file transfer** — FTPS (`FTPS` session factories) wraps the same FTP protocol semantics in TLS, used identically to plain FTP from the flow's perspective, just configured with different `SessionFactory` implementation and security settings.

## 3. Core concept

Think of the FTP adapters like a courier service that regularly checks a remote partner's drop-off box (a directory on their FTP server), physically retrieves anything new, brings it back to your own local mail room (the local staging directory) for actual processing, and later, on the outbound side, delivers your own finished packages to the partner's designated pickup location on that same remote server. The courier's job is entirely about the physical transport between two systems' file locations — your own internal processing (transformers, service activators) never has to deal with FTP protocol details directly, only the plain local files the courier already brought back.

```java
@Bean
public SessionFactory<FTPFile> ftpSessionFactory() {
    DefaultFtpSessionFactory factory = new DefaultFtpSessionFactory();
    factory.setHost("ftp.partner.example.com");
    factory.setUsername("integration-user");
    factory.setPassword("secret");
    return factory;
}

@Bean
@InboundChannelAdapter(value = "incomingFtpFiles", poller = @Poller(fixedDelay = "5000"))
public FtpInboundFileSynchronizingMessageSource ftpInbound(SessionFactory<FTPFile> sessionFactory) {
    FtpInboundFileSynchronizingMessageSource source = new FtpInboundFileSynchronizingMessageSource(
        new FtpInboundFileSynchronizer(sessionFactory));
    source.setLocalDirectory(new File("/local/staging"));
    return source;
}
```

The `SessionFactory` handles connecting, authenticating, and the actual FTP protocol exchange; the message source's job is orchestrating the poll-synchronize-emit cycle around it, using that session.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="FtpInboundFileSynchronizingMessageSource polls a remote FTP directory, downloads new files to a local staging directory, and emits a message per file; FtpMessageHandler uploads outbound payloads to a remote FTP directory">
  <rect x="20" y="20" width="150" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="95" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">remote FTP dir</text>

  <line x1="170" y1="40" x2="230" y2="40" stroke="#6db33f" stroke-width="2" marker-end="url(#ftp1)"/>
  <text x="200" y="27" fill="#6db33f" font-size="6" text-anchor="middle" font-family="sans-serif">sync/download</text>

  <rect x="240" y="20" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="315" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">local staging dir</text>

  <line x1="390" y1="40" x2="450" y2="40" stroke="#79c0ff" stroke-width="2" marker-end="url(#ftp2)"/>

  <rect x="460" y="20" width="150" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="535" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">flow's channel</text>

  <rect x="20" y="120" width="150" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="144" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">flow's channel</text>

  <line x1="170" y1="140" x2="450" y2="140" stroke="#79c0ff" stroke-width="2" marker-end="url(#ftp2)"/>
  <text x="310" y="127" fill="#79c0ff" font-size="6" text-anchor="middle" font-family="sans-serif">upload</text>

  <rect x="460" y="120" width="150" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="535" y="144" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">remote FTP dir</text>

  <defs>
    <marker id="ftp1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ftp2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

FTP files are synchronized to a local staging directory before entering the flow — internal processing sees only plain local files, never FTP protocol details.

## 5. Runnable example

The scenario: a nightly file exchange with a trading partner over FTP, starting with a basic simulated inbound sync, then local processing of synchronized files, and finally an outbound upload with a duplicate-prevention check across sync cycles.

### Level 1 — Basic

```java
// SimulatedFtpInboundSyncDemo.java
// Simulates the FTP synchronization step using local directories standing in for "remote" and
// "local staging" file systems, since actually connecting to an FTP server requires a real server.
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class SimulatedFtpInboundSyncDemo {
    public static void main(String[] args) throws IOException {
        Path remoteFtpDir = Files.createTempDirectory("remote-ftp-demo"); // stands in for the remote server
        Path localStagingDir = Files.createTempDirectory("local-staging-demo");

        Files.writeString(remoteFtpDir.resolve("export-1.csv"), "ORD-1,199.99");
        Files.writeString(remoteFtpDir.resolve("export-2.csv"), "ORD-2,25.00");

        // what FtpInboundFileSynchronizer does for you: download each remote file to local staging
        for (File remoteFile : Objects.requireNonNull(remoteFtpDir.toFile().listFiles())) {
            Path localCopy = localStagingDir.resolve(remoteFile.getName());
            Files.copy(remoteFile.toPath(), localCopy, StandardCopyOption.REPLACE_EXISTING);
            System.out.println("Synchronized: " + remoteFile.getName() + " -> local staging");
        }

        System.out.println("Local staging now contains: " + Arrays.toString(localStagingDir.toFile().list()));
    }
}
```

How to run: `java SimulatedFtpInboundSyncDemo.java`. Expected output: `Synchronized: export-1.csv -> local staging` and `Synchronized: export-2.csv -> local staging` (order may vary), then `Local staging now contains: [export-1.csv, export-2.csv]` (or similar) — the remote files were downloaded into a local directory, exactly the synchronization step `FtpInboundFileSynchronizer` performs before a `FileReadingMessageSource` (card 0050) picks up the local copies.

### Level 2 — Intermediate

Once files are synchronized locally, the rest of the flow processes them exactly like any local file — reusing the same `FileReadingMessageSource`-style logic from card 0050, since the FTP-specific work is entirely confined to the synchronization step itself.

```java
// ProcessSynchronizedFilesDemo.java
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class ProcessSynchronizedFilesDemo {
    record Order(String id, double amount) {}

    public static void main(String[] args) throws IOException {
        Path localStagingDir = Files.createTempDirectory("local-staging-demo");
        Files.writeString(localStagingDir.resolve("export-1.csv"), "ORD-1,199.99");

        // downstream processing has NO idea this file originated from a remote FTP server
        File[] files = localStagingDir.toFile().listFiles();
        for (File file : Objects.requireNonNull(files)) {
            String[] parts = Files.readString(file.toPath()).split(",");
            Order order = new Order(parts[0], Double.parseDouble(parts[1]));
            System.out.println("Processing (FTP origin is irrelevant now): " + order);
        }
    }
}
```

How to run: `java ProcessSynchronizedFilesDemo.java`. Expected output: `Processing (FTP origin is irrelevant now): Order[id=ORD-1, amount=199.99]` — confirming that once synchronization has happened, the rest of the flow works with plain local files, completely decoupled from the fact that they originated on a remote FTP server, exactly the adapter-boundary separation described generically in card 0018.

### Level 3 — Advanced

Simulating outbound upload with duplicate-prevention across multiple sync cycles — tracking which local files have already been uploaded (mirroring `FtpMessageHandler`'s typical usage alongside a marker or a processed-files registry) so a re-run doesn't re-upload the same file.

```java
// OutboundUploadWithDedupeDemo.java
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class OutboundUploadWithDedupeDemo {
    static Set<String> alreadyUploaded = new HashSet<>(); // stands in for a metadata store (card 0047)

    static void uploadIfNew(Path localFile, Path remoteFtpDir) throws IOException {
        String fileName = localFile.getFileName().toString();
        if (alreadyUploaded.contains(fileName)) {
            System.out.println("SKIPPED (already uploaded): " + fileName);
            return;
        }
        Files.copy(localFile, remoteFtpDir.resolve(fileName), StandardCopyOption.REPLACE_EXISTING);
        alreadyUploaded.add(fileName);
        System.out.println("Uploaded: " + fileName);
    }

    public static void main(String[] args) throws IOException {
        Path outputDir = Files.createTempDirectory("local-output-demo");
        Path remoteFtpDir = Files.createTempDirectory("remote-ftp-demo");
        Path reportFile = outputDir.resolve("nightly-report.csv");
        Files.writeString(reportFile, "ORD-1,SHIPPED\nORD-2,SHIPPED");

        System.out.println("--- Sync cycle 1 ---");
        uploadIfNew(reportFile, remoteFtpDir);

        System.out.println("--- Sync cycle 2 (report NOT regenerated, same file) ---");
        uploadIfNew(reportFile, remoteFtpDir); // should be skipped

        System.out.println("Remote FTP dir contents: " + Arrays.toString(remoteFtpDir.toFile().list()));
    }
}
```

How to run: `java OutboundUploadWithDedupeDemo.java`. Expected output: `--- Sync cycle 1 ---`, `Uploaded: nightly-report.csv`, `--- Sync cycle 2 ---`, `SKIPPED (already uploaded): nightly-report.csv`, then `Remote FTP dir contents: [nightly-report.csv]` — the file was only actually uploaded once, even though the upload logic ran twice, avoiding redundant remote uploads across repeated poll/sync cycles.

## 6. Walkthrough

Tracing `OutboundUploadWithDedupeDemo` in execution order:

1. The first `uploadIfNew(reportFile, remoteFtpDir)` call checks `alreadyUploaded.contains("nightly-report.csv")` — false, since nothing has been uploaded yet — so it proceeds to `Files.copy(...)`, physically copying the file into the simulated remote FTP directory, then adds the file name to `alreadyUploaded` and prints confirmation.
2. In a real system, this step is where `FtpMessageHandler` would actually connect to the remote FTP server (via its `SessionFactory`) and perform the upload over the network, rather than a local file copy — the local-copy simulation stands in for that network operation while preserving the same decision logic.
3. The second call to `uploadIfNew` with the *same* `reportFile` path checks `alreadyUploaded.contains("nightly-report.csv")` again — this time `true`, since the first call added it — so the method returns immediately via the early `return`, printing a "SKIPPED" message instead of performing another upload.
4. This mirrors a realistic scenario: an outbound flow re-triggered (perhaps by a retry, or a scheduled job running again before new content exists) shouldn't re-upload identical content unnecessarily, wasting network bandwidth and potentially confusing the receiving partner with duplicate files.
5. The final check of `remoteFtpDir.toFile().list()` confirms only one file exists in the "remote" directory — proof that the second upload attempt genuinely had no effect, rather than silently overwriting the same file a second time (which, while harmless for identical content, would be wasteful for a large file over a slow connection).
6. A real production system would typically base this dedupe decision on file content hashes or explicit "already sent" tracking (similar to the `MetadataStore`-backed idempotent receiver pattern from card 0047), rather than the local-only, in-memory `Set` used here for simulation purposes.

```
cycle 1: uploadIfNew(nightly-report.csv) -> not in alreadyUploaded -> UPLOAD -> mark as uploaded
cycle 2: uploadIfNew(nightly-report.csv) -> ALREADY in alreadyUploaded -> SKIP, no re-upload
```

## 7. Gotchas & takeaways

> Plain FTP (unlike FTPS) transmits credentials and file contents in cleartext over the network — a significant security exposure for any integration handling sensitive data. Always prefer FTPS (or SFTP, card 0052, which is a different protocol entirely, built on SSH rather than FTP+TLS) for any real production file exchange involving credentials or sensitive content; reach for plain FTP only when integrating with a legacy partner system that genuinely offers no more secure alternative, and treat that as a risk to flag rather than a default choice.

- FTP support mirrors the local file adapters from card 0050, but for a remote FTP/FTPS server: `FtpInboundFileSynchronizingMessageSource` polls and downloads new remote files to a local staging directory; `FtpMessageHandler` uploads outbound payloads to a remote directory.
- The FTP-specific protocol work (connecting, authenticating, transferring) is confined entirely to the synchronization/upload step — once a file is synchronized locally, the rest of the flow processes it exactly like any local file, with no FTP awareness needed downstream.
- FTPS (TLS-secured FTP) should be preferred over plain FTP for any production use involving credentials or sensitive content; plain FTP transmits everything, including credentials, in cleartext.
- Duplicate-prevention across repeated sync/upload cycles (avoiding re-downloading or re-uploading the same file) is a real, common concern — track already-processed files explicitly, similar to the metadata-store-backed idempotent receiver pattern from card 0047.
- These adapters are concrete, protocol-specific instances of the general inbound/outbound adapter roles from cards 0018 and 0033 — understanding that general pattern makes the FTP-specific configuration mostly about connection details, not new conceptual ground.
