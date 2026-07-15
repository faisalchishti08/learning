---
card: spring-integration
gi: 50
slug: file-support-read-write-tail
title: "File support (read/write/tail)"
---

## 1. What it is

Spring Integration's file support provides ready-made channel adapters (card 0018/0033) for the file system: `FileReadingMessageSource` (an inbound adapter that polls a directory and emits a `Message<File>` for each new file it finds), `FileWritingMessageHandler` (an outbound adapter that writes a message's payload to disk as a file), and `FileTailingMessageProducer` (an event-driven inbound adapter that continuously watches a growing file — like a log file — and emits a message for each new line appended, similar to the Unix `tail -f` command).

## 2. Why & when

You reach for these specific adapters whenever a flow's external boundary is the local (or a mounted network) file system:

- **New files periodically appear in a directory and need to be picked up for processing** — an incoming-orders folder, a batch-upload landing zone — `FileReadingMessageSource` polls that directory on a schedule (using the polling-consumer mechanics from card 0035) and turns each discovered file into a message.
- **A flow's final output needs to be written to disk** — a generated report, a processed data export — `FileWritingMessageHandler` is the outbound adapter that performs that write as its side effect, taking a payload (bytes, a `String`, or an existing `File`) and producing a file on disk.
- **A continuously-growing file needs to be monitored for new content as it's appended**, rather than read once — `FileTailingMessageProducer` is purpose-built for exactly this: watching a log file and emitting a message per new line, event-driven rather than polling the whole file repeatedly.

## 3. Core concept

Think of `FileReadingMessageSource` like a mail clerk who checks an inbox tray on a schedule and picks up whatever new envelopes have arrived since the last check; `FileWritingMessageHandler` like a clerk who takes a finished document and physically files it into an outbox folder; and `FileTailingMessageProducer` like someone standing at a ticker-tape machine, reacting to each new line the moment it's printed, rather than periodically checking the whole tape from the start.

```java
@Bean
@InboundChannelAdapter(value = "incomingFiles", poller = @Poller(fixedDelay = "1000"))
public FileReadingMessageSource fileReader() {
    FileReadingMessageSource source = new FileReadingMessageSource();
    source.setDirectory(new File("/incoming"));
    return source;
}

@ServiceActivator(inputChannel = "processedContent")
@Bean
public FileWritingMessageHandler fileWriter() {
    FileWritingMessageHandler handler = new FileWritingMessageHandler(new File("/processed"));
    handler.setFileNameGenerator(message -> "processed-" + message.getHeaders().getId() + ".txt");
    return handler;
}
```

Both adapters bridge the file system boundary described generically in card 0018, using file-system-specific logic (directory polling, file naming, write strategies) so the rest of the flow never has to deal with `java.io.File` mechanics directly.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="FileReadingMessageSource polls a directory and emits a message per new file; FileWritingMessageHandler writes a message's payload to disk; FileTailingMessageProducer watches a growing file and emits a message per new appended line" >
  <rect x="20" y="20" width="140" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="90" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">/incoming directory</text>

  <line x1="160" y1="40" x2="220" y2="40" stroke="#6db33f" stroke-width="2" marker-end="url(#fs1)"/>
  <text x="190" y="27" fill="#6db33f" font-size="6" text-anchor="middle" font-family="sans-serif">poll (new files)</text>

  <rect x="230" y="20" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="305" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">flow's channel</text>

  <line x1="380" y1="40" x2="440" y2="40" stroke="#79c0ff" stroke-width="2" marker-end="url(#fs2)"/>

  <rect x="450" y="20" width="140" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="520" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">/processed (written)</text>

  <rect x="20" y="120" width="220" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="130" y="140" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">growing log file (appended to)</text>

  <line x1="240" y1="142" x2="300" y2="142" stroke="#6db33f" stroke-width="2" marker-end="url(#fs1)"/>
  <text x="270" y="128" fill="#6db33f" font-size="6" text-anchor="middle" font-family="sans-serif">tail -f style</text>

  <rect x="310" y="120" width="150" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="385" y="140" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">message per new line</text>

  <defs>
    <marker id="fs1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="fs2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Three distinct file-system adapter roles: poll-and-read, write, and continuously-tail — each suited to a different file-system interaction shape.

## 5. Runnable example

The scenario: a file-processing pipeline reading incoming files, writing processed output, and tailing a growing log, starting with basic directory polling, then writing output files, and finally tailing a file for new lines.

### Level 1 — Basic

```java
// FileReadingDemo.java
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class FileReadingDemo {
    public static void main(String[] args) throws IOException {
        Path incomingDir = Files.createTempDirectory("incoming-demo");
        Files.writeString(incomingDir.resolve("order-1.txt"), "ORD-1,199.99");
        Files.writeString(incomingDir.resolve("order-2.txt"), "ORD-2,25.00");

        // what FileReadingMessageSource's poll does for you: list new files, emit one Message<File> each
        File[] discoveredFiles = incomingDir.toFile().listFiles((dir, name) -> name.endsWith(".txt"));
        Arrays.sort(discoveredFiles, Comparator.comparing(File::getName));

        for (File file : discoveredFiles) {
            String content = Files.readString(file.toPath());
            System.out.println("Discovered file: " + file.getName() + " -> content: " + content);
        }
    }
}
```

How to run: `java FileReadingDemo.java`. Expected output: `Discovered file: order-1.txt -> content: ORD-1,199.99` then `Discovered file: order-2.txt -> content: ORD-2,25.00` — a directory listing turned each discovered file into something processable, exactly what a real `FileReadingMessageSource` does on each poll cycle, just without the polling schedule itself.

### Level 2 — Intermediate

Writing processed output to disk, with a generated file name derived from message content — mirroring `FileWritingMessageHandler`'s `FileNameGenerator` configuration.

```java
// FileWritingDemo.java
import java.io.*;
import java.nio.file.*;

public class FileWritingDemo {
    record ProcessedOrder(String id, double discountedAmount) {}

    public static void main(String[] args) throws IOException {
        Path outputDir = Files.createTempDirectory("processed-demo");

        ProcessedOrder order = new ProcessedOrder("ORD-1", 179.99);

        // what FileWritingMessageHandler does for you: generate a name, write the payload
        String fileName = "processed-" + order.id() + ".txt";
        Path outputFile = outputDir.resolve(fileName);
        Files.writeString(outputFile, "Order " + order.id() + " processed, final amount: " + order.discountedAmount());

        System.out.println("Written: " + outputFile.getFileName());
        System.out.println("Content: " + Files.readString(outputFile));
    }
}
```

How to run: `java FileWritingDemo.java`. Expected output: `Written: processed-ORD-1.txt` then `Content: Order ORD-1 processed, final amount: 179.99` — a message's payload was turned into an actual file on disk, with a name generated from the message's own content, exactly what a real `FileWritingMessageHandler` would do as an outbound adapter.

### Level 3 — Advanced

Tailing a growing log file, reacting to each new line as it's appended — modeled with a background writer thread appending lines while a tailing thread watches and reports each new line, mirroring `FileTailingMessageProducer`'s event-driven behavior.

```java
// FileTailingDemo.java
import java.io.*;
import java.nio.file.*;
import java.util.concurrent.CountDownLatch;

public class FileTailingDemo {
    public static void main(String[] args) throws Exception {
        Path logFile = Files.createTempFile("app", ".log");
        CountDownLatch linesToWatch = new CountDownLatch(3);

        // what FileTailingMessageProducer does: watch a file, emit ONE message per new line appended
        Thread tailer = new Thread(() -> {
            try (RandomAccessFile raf = new RandomAccessFile(logFile.toFile(), "r")) {
                long filePointer = 0;
                while (linesToWatch.getCount() > 0) {
                    long fileLength = raf.length();
                    if (fileLength > filePointer) {
                        raf.seek(filePointer);
                        String line;
                        while ((line = raf.readLine()) != null) {
                            System.out.println("[tail] new line: " + line);
                            linesToWatch.countDown();
                        }
                        filePointer = raf.getFilePointer();
                    }
                    Thread.sleep(50);
                }
            } catch (Exception ignored) {}
        });
        tailer.start();

        // writer: appends new lines to the log, simulating a running application logging events
        Thread.sleep(100);
        Files.writeString(logFile, "INFO: order ORD-1 received\n", StandardOpenOption.APPEND);
        Thread.sleep(100);
        Files.writeString(logFile, "INFO: order ORD-1 shipped\n", StandardOpenOption.APPEND);
        Thread.sleep(100);
        Files.writeString(logFile, "WARN: order ORD-2 delayed\n", StandardOpenOption.APPEND);

        linesToWatch.await();
        tailer.interrupt();
    }
}
```

How to run: `java FileTailingDemo.java`. Expected output: `[tail] new line: INFO: order ORD-1 received`, `[tail] new line: INFO: order ORD-1 shipped`, `[tail] new line: WARN: order ORD-2 delayed` — each line appeared as its own event the moment it was appended to the file, exactly the incremental, event-driven behavior `FileTailingMessageProducer` provides, rather than repeatedly re-reading the entire file from the start.

## 6. Walkthrough

Tracing `FileTailingDemo` in execution order:

1. The `tailer` thread starts immediately, opens the log file for reading, and begins its loop with `filePointer = 0` — tracking exactly how much of the file it has already read.
2. Initially, `raf.length()` (the file's current size) equals `filePointer` (`0`), since nothing has been written yet — the loop finds no new content and sleeps briefly before checking again.
3. After the main thread's `Thread.sleep(100)`, the first `Files.writeString(..., APPEND)` call appends a line to the log file — the file's length on disk grows.
4. On the tailer's next check, `raf.length()` is now greater than `filePointer`; it seeks to `filePointer` (skipping content it's already read), reads the new line with `raf.readLine()`, prints it, and updates `filePointer` to the new current position — crucially, it never re-reads from the beginning of the file, only the newly-appended portion.
5. This same seek-read-print-advance cycle repeats for the second and third appended lines, each detected independently as the writer thread appends them roughly 100ms apart.
6. Once `linesToWatch` reaches zero (all three expected lines have been seen), the main thread's `await()` unblocks, and the tailer thread is interrupted — in a real `FileTailingMessageProducer`, this same seek-based incremental reading is what lets it efficiently watch even very large, continuously-growing log files without repeatedly re-scanning content it has already emitted as messages.

```
t=0ms:    tailer starts, filePointer=0, file is empty
t=100ms:  writer appends "INFO: order ORD-1 received\n" -> file grows
t=~100ms: tailer detects growth, seeks to filePointer, reads NEW line, advances filePointer
t=200ms:  writer appends "INFO: order ORD-1 shipped\n" -> file grows further
t=~200ms: tailer detects growth again, reads ONLY the new line, advances filePointer
... repeats for the third line ...
```

## 7. Gotchas & takeaways

> `FileReadingMessageSource`'s directory polling, by default, can re-discover the same file on a subsequent poll if it hasn't been explicitly marked as processed (via a `FileListFilter` like `AcceptOnceFileListFilter`), leading to duplicate processing — a file-system analogue of the at-least-once delivery problem the idempotent receiver pattern (card 0047) addresses for messaging transports generally. Always configure an appropriate filter (accept-once, a "processed" marker file, or moving/renaming processed files) rather than assuming a file is automatically only ever picked up once.

- Spring Integration provides dedicated file-system adapters: `FileReadingMessageSource` (inbound, polls a directory), `FileWritingMessageHandler` (outbound, writes a payload to disk), and `FileTailingMessageProducer` (inbound, event-driven, watches a growing file for new lines).
- Use directory-polling for batch-style file intake, file writing for producing output artifacts, and tailing specifically for continuously-growing files (like logs) where reacting to each new line as it appears matters more than periodic full re-reads.
- Tailing is efficient specifically because it tracks a file position and reads only newly-appended content, never re-scanning what it has already processed — the same principle a real log-monitoring tool relies on.
- Always configure explicit duplicate-prevention for directory polling (an accept-once filter, moving processed files elsewhere) to avoid the same file being picked up and processed more than once across multiple poll cycles.
- These adapters are concrete instances of the general inbound/outbound adapter roles from cards 0018 and 0033, specialized specifically for file-system interaction — the same one-way, no-reply-expected semantics from those cards apply here as well.
