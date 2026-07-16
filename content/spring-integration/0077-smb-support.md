---
card: spring-integration
gi: 77
slug: smb-support
title: "SMB support"
---

## 1. What it is

SMB support (`Smb.inboundAdapter(...)`/`Smb.outboundAdapter(...)`/`Smb.outboundGateway(...)`, part of the extension components alongside FTP/FTPS (card 0051) and SFTP (card 0052)) connects a flow to a Windows-style shared folder over the SMB/CIFS protocol — the file-sharing protocol behind Windows network shares (`\\server\share`) and Samba. It follows the same shape as the other remote-file adapters: poll a remote directory for files, download and process them, or push files out to a share, all through the same `RemoteFileTemplate`-based abstraction FTP and SFTP support use.

## 2. Why & when

You reach for SMB support when the integration point is specifically a Windows network share rather than an FTP, SFTP, or cloud object store:

- **The data source or destination is a corporate Windows file share** — many internal systems, especially in enterprises with a strong Windows Server presence, exchange files by dropping them onto a shared drive rather than through FTP or an API; SMB support lets a flow participate in that exchange without requiring the other side to change how it works.
- **A legacy or third-party process already writes to (or reads from) a specific SMB share** — bridging a modern flow to that existing file-drop convention is often far cheaper than asking the other party to migrate to a different transfer mechanism.
- **The same polling/processing pattern as FTP or SFTP is needed, just against a different protocol** — because SMB support shares the same `RemoteFileTemplate` abstraction, a flow already built against FTP or SFTP can often be retargeted to SMB with primarily configuration changes, not a rewrite of the processing logic.

## 3. Core concept

Think of SMB as a shared filing cabinet inside an office building's own internal mail room, versus FTP or SFTP as filing cabinets reachable over the open internet through separate protocols. The three adapters — SMB, FTP, SFTP — all present essentially the same "poll a remote directory, fetch new files, process them" shape to a Spring Integration flow; the difference is which specific protocol and authentication mechanism (SMB's domain/workgroup credentials, versus FTP's plain username/password, versus SFTP's SSH keys) is used to actually reach the shared location.

```java
@Bean
public IntegrationFlow smbInboundFlow(SmbSessionFactory sessionFactory) {
    return IntegrationFlow.from(
            Smb.inboundAdapter(sessionFactory)
                .remoteDirectory("/incoming")
                .patternFilter("*.csv")
                .localDirectory(new File("/local/staging")),
            e -> e.poller(Pollers.fixedDelay(10_000)))
        .handle((File file, headers) -> batchImportService.importFile(file))
        .get();
}
```

The shape is identical to an FTP or SFTP inbound flow — the only real difference is the `SmbSessionFactory` used to connect, configured with the share's host, domain, and credentials.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SMB, FTP, and SFTP adapters all follow the same poll-download-process shape through a shared RemoteFileTemplate abstraction, differing mainly in the underlying protocol and authentication" >
  <rect x="20" y="20" width="180" height="100" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">SMB</text>
  <text x="35" y="45" fill="#e6edf3" font-size="7" font-family="monospace">\\server\share</text>
  <text x="35" y="65" fill="#8b949e" font-size="7" font-family="sans-serif">domain/user auth</text>

  <rect x="230" y="20" width="180" height="100" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">FTP/FTPS (0051)</text>
  <text x="245" y="45" fill="#e6edf3" font-size="7" font-family="monospace">ftp://host/dir</text>
  <text x="245" y="65" fill="#8b949e" font-size="7" font-family="sans-serif">username/password</text>

  <rect x="440" y="20" width="180" height="100" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="530" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">SFTP (0052)</text>
  <text x="455" y="45" fill="#e6edf3" font-size="7" font-family="monospace">sftp://host/dir</text>
  <text x="455" y="65" fill="#8b949e" font-size="7" font-family="sans-serif">SSH key auth</text>

  <text x="320" y="140" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">All three: same poll -&gt; download -&gt; process shape, different protocol underneath</text>
</svg>

Same processing pattern across all three remote-file adapters — only the connection protocol and credentials differ.

## 5. Runnable example

The scenario: importing CSV files dropped onto a shared folder, simulated with an in-memory list of remote files standing in for an SMB share listing (no real SMB/CIFS connection needed to demonstrate the polling and processing logic), starting with a basic poll-and-import, then adding a processed-marker to avoid reimporting the same file, then handling a locked or partially-written file safely.

### Level 1 — Basic

```java
// SmbImportDemo.java
import java.util.*;

public class SmbImportDemo {
    record RemoteFile(String name, String content) {}

    static List<RemoteFile> listMatching(List<RemoteFile> share, String suffix) {
        return share.stream().filter(f -> f.name().endsWith(suffix)).toList();
    }

    static void importFile(RemoteFile f) {
        System.out.println("Imported " + f.name() + ": " + f.content());
    }

    public static void main(String[] args) {
        List<RemoteFile> share = List.of(
            new RemoteFile("customers.csv", "id,name\n1,Acme"),
            new RemoteFile("readme.txt", "not a data file"));

        for (RemoteFile f : listMatching(share, ".csv")) {
            importFile(f);
        }
    }
}
```

How to run: `java SmbImportDemo.java`. Expected output: `Imported customers.csv: id,name\n1,Acme` — only the CSV file is picked up, matching the configured pattern filter.

### Level 2 — Intermediate

```java
// SmbImportDemo.java
import java.util.*;

public class SmbImportDemo {
    record RemoteFile(String name, String content) {}

    static List<RemoteFile> listMatching(List<RemoteFile> share, String suffix) {
        return share.stream().filter(f -> f.name().endsWith(suffix)).toList();
    }

    // Real-world concern: repeated polls will see the same file again unless something tracks
    // what has already been imported -- the FTP/SFTP/SMB adapters solve this by moving or
    // renaming a processed file on the share, mirrored here with a simple processed-name set.
    static class ImportTracker {
        private final Set<String> imported = new HashSet<>();
        void poll(List<RemoteFile> share) {
            for (RemoteFile f : listMatching(share, ".csv")) {
                if (imported.contains(f.name())) {
                    System.out.println("Skipping already-imported " + f.name());
                    continue;
                }
                System.out.println("Imported " + f.name() + ": " + f.content());
                imported.add(f.name());
            }
        }
    }

    public static void main(String[] args) {
        List<RemoteFile> share = List.of(new RemoteFile("customers.csv", "id,name\n1,Acme"));
        ImportTracker tracker = new ImportTracker();

        System.out.println("-- poll 1 --");
        tracker.poll(share);
        System.out.println("-- poll 2 (file still present on share) --");
        tracker.poll(share);
    }
}
```

How to run: `java SmbImportDemo.java`. Expected output: poll 1 imports `customers.csv`; poll 2 prints `Skipping already-imported customers.csv` even though the file is still listed on the share — mirroring how a real adapter's "move to processed/" or "rename after processing" strategy prevents the same file from being imported twice.

### Level 3 — Advanced

```java
// SmbImportDemo.java
import java.util.*;

public class SmbImportDemo {
    record RemoteFile(String name, String content, boolean stillBeingWritten) {}

    static List<RemoteFile> listMatching(List<RemoteFile> share, String suffix) {
        return share.stream().filter(f -> f.name().endsWith(suffix)).toList();
    }

    // Production concern: a file can appear on the share mid-write (another process is still
    // copying it), and reading it too early yields a truncated, corrupt import. Skip files still
    // being written and retry them on a later poll, rather than importing partial data.
    static class ImportTracker {
        private final Set<String> imported = new HashSet<>();

        void poll(List<RemoteFile> share) {
            for (RemoteFile f : listMatching(share, ".csv")) {
                if (imported.contains(f.name())) continue;
                if (f.stillBeingWritten()) {
                    System.out.println("Deferring " + f.name() + ": still being written, will retry next poll");
                    continue;
                }
                System.out.println("Imported " + f.name() + ": " + f.content());
                imported.add(f.name());
            }
        }
    }

    public static void main(String[] args) {
        ImportTracker tracker = new ImportTracker();

        List<RemoteFile> shareDuringCopy = List.of(
            new RemoteFile("customers.csv", "id,name\n1,Ac", true)); // partial content, mid-write
        System.out.println("-- poll 1 (file still being copied) --");
        tracker.poll(shareDuringCopy);

        List<RemoteFile> shareAfterCopy = List.of(
            new RemoteFile("customers.csv", "id,name\n1,Acme\n2,Globex", false)); // fully written now
        System.out.println("-- poll 2 (copy finished) --");
        tracker.poll(shareAfterCopy);
    }
}
```

How to run: `java SmbImportDemo.java`. Expected output: poll 1 prints `Deferring customers.csv: still being written, will retry next poll` and imports nothing; poll 2, once the file is fully written, imports the complete content — avoiding the truncated-read problem that comes from processing a file while another process is still actively copying it onto the share.

## 6. Walkthrough

Trace a file import cycle from share to processed data, including the partial-write edge case.

1. **Poller fires**: `Smb.inboundAdapter`'s poller lists the configured remote directory on the share, filtering by the configured pattern (`*.csv`).
2. **Staleness/completeness check**: a well-configured adapter avoids picking up files still being written — commonly by requiring a file's size or modified timestamp to be stable across two consecutive polls, or by having the writing process use an atomic rename (write as `.tmp`, then rename to `.csv` only once complete) so the adapter never sees a partial file matching its pattern at all.
3. **Download**: for each qualifying file, the adapter downloads it to a configured local staging directory over the SMB connection.
4. **Processing**: a `.handle(...)` step, like `batchImportService.importFile(file)`, reads the local copy and performs the actual import.
5. **Mark processed**: after successful processing, the adapter (depending on configuration) can rename or move the source file on the share to a "processed" location, or delete it, so the next poll's directory listing no longer includes it — the same idempotency guarantee the JDBC (card 0064) and mail (card 0063) adapters achieve through their own respective mechanisms.
6. **Failure isolation**: if one file fails to import (malformed content, a lock held by another process), that failure is handled per-file so the rest of the batch from the same poll still gets processed, rather than one bad file blocking every other file waiting on the share.

```
poller tick
  -> list remote directory, filter by pattern
    -> for each file: stable size/timestamp across polls? (not mid-write)
         no  -> defer to next poll
         yes -> download to local staging
                  -> batchImportService.importFile(file)
                    success -> mark processed (rename/move/delete on share)
                    failure -> isolate, other files still processed
```

## 7. Gotchas & takeaways

> **Gotcha:** a naive poller that immediately processes any file matching its pattern the instant it appears in a directory listing can read a file mid-copy from a slow writer, producing a truncated or corrupted import — always require some form of stability check (unchanged size/timestamp across polls, or an atomic rename convention agreed with the writer) before treating a newly-seen file as ready.

- SMB authentication (domain, username, password, or increasingly Kerberos-based) differs meaningfully from FTP's plain credentials or SFTP's SSH keys — the connection setup is the main place SMB support diverges from its FTP/SFTP siblings, not the flow logic built on top of it.
- Because SMB support shares the same `RemoteFileTemplate` abstraction as FTP and SFTP, migrating an existing FTP-based flow to SMB (or vice versa) is often mostly a configuration change — swap the session factory, keep the processing logic.
- Network shares can be slower or less reliable than a dedicated file-transfer protocol under high latency or across a WAN link; for high-volume or latency-sensitive transfers, weigh whether SFTP or a dedicated transfer tool might serve better than an SMB share designed primarily for local-network file access.
- Always mark files as processed on the share itself (rename, move, or delete) rather than relying solely on in-memory tracking in the application — an application restart with only in-memory state would otherwise reprocess every file still sitting in the source directory.
