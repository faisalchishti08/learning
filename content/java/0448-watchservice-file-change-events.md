---
card: java
gi: 448
slug: watchservice-file-change-events
title: WatchService (file change events)
---

## 1. What it is

`WatchService`, added in Java 7 as part of `java.nio.file`, lets a program subscribe to file system change notifications for a directory — creations, modifications, and deletions of entries within it — without repeatedly polling and comparing directory listings by hand. You register a directory (`path.register(watcher, ENTRY_CREATE, ENTRY_MODIFY, ENTRY_DELETE)`), then call `watcher.poll(...)` or `watcher.take()` to retrieve a `WatchKey` carrying any events that occurred, each described by a `WatchEvent` with a *kind* (create/modify/delete) and a *context* (the affected file's name).

## 2. Why & when

Before `WatchService`, detecting file system changes meant writing your own polling loop: periodically list a directory's contents, compare against the previous listing, and infer what changed — tedious, easy to get subtly wrong (missed rapid changes between polls, or races), and wasteful if implemented with a tight polling loop. `WatchService` provides a standard API for this exact need, letting the underlying platform (where possible, using native OS file-change notification facilities) do the actual watching efficiently.

You reach for `WatchService` any time your application needs to react to file system changes it doesn't control directly — a configuration-reload feature that picks up edits to a config file, a build tool watching source files for changes to trigger a rebuild, or a simple file-drop processing pipeline that reacts as new files arrive in a directory.

## 3. Core concept

```java
import java.nio.file.*;
import static java.nio.file.StandardWatchEventKinds.*;

WatchService watcher = FileSystems.getDefault().newWatchService();
Path dir = Paths.get("/some/directory");
dir.register(watcher, ENTRY_CREATE, ENTRY_MODIFY, ENTRY_DELETE);

WatchKey key = watcher.take(); // blocks until at least one event is available (poll() has a timed variant)
for (WatchEvent<?> event : key.pollEvents()) {
    System.out.println(event.kind() + " on " + event.context()); // context() is the affected file's NAME
}
key.reset(); // MUST call this to keep receiving future events for this key
```

`event.context()` gives only the affected entry's *file name* — not its full path — since the same `WatchKey` may represent multiple watched directories worth of underlying identity in more advanced setups; you must combine it with the directory you know it belongs to, to get a full, usable path.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Registering a directory with a WatchService produces a WatchKey; file system changes queue WatchEvents on that key, retrieved via poll or take, and the key must be reset to continue receiving further events">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="150" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/><text x="105" y="52" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">dir.register(watcher, ...)</text>
  <rect x="230" y="30" width="150" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="305" y="52" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">WatchKey</text>
  <rect x="430" y="30" width="180" height="34" rx="6" fill="#1c2430" stroke="#e6edf3"/><text x="520" y="52" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">poll()/take() -&gt; events</text>

  <line x1="180" y1="47" x2="225" y2="47" stroke="#8b949e" marker-end="url(aws1)"/>
  <line x1="380" y1="47" x2="425" y2="47" stroke="#8b949e" marker-end="url(aws1)"/>

  <text x="320" y="100" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">key.reset() after processing -- forgetting this silently stops future events for that key</text>
  <defs><marker id="aws1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Registering produces a key; events queue on that key over time; resetting the key is what keeps the subscription alive.

## 5. Runnable example

Scenario: watching a directory for file changes — the same watch setup, evolved from detecting a single file creation, through observing a full create/modify/delete lifecycle for one file, to correctly distinguishing events across two separately-watched directories.

### Level 1 — Basic

```java
import java.nio.file.*;
import static java.nio.file.StandardWatchEventKinds.*;

public class WatchBasic {
    public static void main(String[] args) throws Exception {
        Path dir = Files.createTempDirectory("watch-demo");

        WatchService watcher = FileSystems.getDefault().newWatchService();
        dir.register(watcher, ENTRY_CREATE, ENTRY_MODIFY, ENTRY_DELETE);

        Path newFile = dir.resolve("new.txt");
        Files.write(newFile, "hello".getBytes());

        WatchKey key = watcher.poll(15, java.util.concurrent.TimeUnit.SECONDS);
        if (key != null) {
            for (WatchEvent<?> event : key.pollEvents()) {
                System.out.println("Event: " + event.kind() + " on " + event.context());
            }
            key.reset();
        } else {
            System.out.println("No event received within timeout");
        }

        watcher.close();
        Files.delete(newFile);
        Files.delete(dir);
    }
}
```

**How to run:** `java WatchBasic.java`

Creating `new.txt` after registering the watch triggers an `ENTRY_CREATE` event; `watcher.poll(15, TimeUnit.SECONDS)` waits (typically just a couple of seconds in practice, since the platform's watch implementation checks periodically) until that event becomes available, then `key.pollEvents()` retrieves it.

### Level 2 — Intermediate

```java
import java.nio.file.*;
import java.util.concurrent.TimeUnit;
import static java.nio.file.StandardWatchEventKinds.*;

public class WatchMultipleEvents {
    public static void main(String[] args) throws Exception {
        Path dir = Files.createTempDirectory("watch-demo2");
        WatchService watcher = FileSystems.getDefault().newWatchService();
        dir.register(watcher, ENTRY_CREATE, ENTRY_MODIFY, ENTRY_DELETE);

        Path file = dir.resolve("data.txt");

        Files.write(file, "v1".getBytes());   // triggers ENTRY_CREATE
        Thread.sleep(2500); // give the watch service's polling cycle time to observe this change separately
        Files.write(file, "v2".getBytes());   // triggers ENTRY_MODIFY
        Thread.sleep(2500);
        Files.delete(file);                    // triggers ENTRY_DELETE
        Thread.sleep(2500);

        int eventsSeen = 0;
        while (eventsSeen < 3) {
            WatchKey key = watcher.poll(5, TimeUnit.SECONDS);
            if (key == null) break;
            for (WatchEvent<?> event : key.pollEvents()) {
                System.out.println(event.kind() + " -> " + event.context());
                eventsSeen++;
            }
            key.reset();
        }
        System.out.println("Total events observed: " + eventsSeen);

        watcher.close();
        Files.delete(dir);
    }
}
```

**How to run:** `java WatchMultipleEvents.java`

Each file operation (`write` for create, `write` again for modify, `delete`) is spaced out with a short sleep, so the underlying watch implementation's periodic check observes each change as a separate event rather than several rapid changes collapsing into fewer observable events. All three event kinds — `ENTRY_CREATE`, `ENTRY_MODIFY`, `ENTRY_DELETE` — are correctly observed in order.

### Level 3 — Advanced

```java
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.TimeUnit;
import static java.nio.file.StandardWatchEventKinds.*;

public class WatchMultipleDirs {
    public static void main(String[] args) throws Exception {
        Path dirA = Files.createTempDirectory("watch-a");
        Path dirB = Files.createTempDirectory("watch-b");

        WatchService watcher = FileSystems.getDefault().newWatchService();

        // Track WHICH directory each WatchKey belongs to -- event.context() only gives a FILE NAME,
        // not which watched directory it happened in, so this mapping is essential with multiple directories.
        Map<WatchKey, Path> keyToDir = new HashMap<>();
        keyToDir.put(dirA.register(watcher, ENTRY_CREATE), dirA);
        keyToDir.put(dirB.register(watcher, ENTRY_CREATE), dirB);

        Files.write(dirA.resolve("a-file.txt"), "in A".getBytes());
        Thread.sleep(2500);
        Files.write(dirB.resolve("b-file.txt"), "in B".getBytes());
        Thread.sleep(2500);

        int eventsSeen = 0;
        while (eventsSeen < 2) {
            WatchKey key = watcher.poll(5, TimeUnit.SECONDS);
            if (key == null) break;
            Path watchedDir = keyToDir.get(key); // resolve WHICH directory this key belongs to
            for (WatchEvent<?> event : key.pollEvents()) {
                Path fullPath = watchedDir.resolve((Path) event.context());
                System.out.println(event.kind() + " -> " + fullPath.getFileName() + " (in " + watchedDir.getFileName() + ")");
                eventsSeen++;
            }
            key.reset();
        }

        watcher.close();
        Files.delete(dirA.resolve("a-file.txt"));
        Files.delete(dirB.resolve("b-file.txt"));
        Files.delete(dirA);
        Files.delete(dirB);
    }
}
```

**How to run:** `java WatchMultipleDirs.java`

Since one `WatchService` can watch multiple directories simultaneously, and `event.context()` only ever gives a bare file name (not which directory it happened in), `keyToDir` maps each returned `WatchKey` back to the directory it was registered for — essential for correctly attributing each event once more than one directory is being watched at once.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. Two separate temporary directories, `dirA` and `dirB`, are created and each registered with the same `watcher` for `ENTRY_CREATE` events. `keyToDir` records that the `WatchKey` returned from registering `dirA` maps back to `dirA`, and likewise for `dirB`.

`Files.write(dirA.resolve("a-file.txt"), ...)` creates a new file inside `dirA`. After a short pause (letting the platform's watch mechanism observe this as its own distinct change), `Files.write(dirB.resolve("b-file.txt"), ...)` creates a file inside `dirB`.

The polling loop calls `watcher.poll(5, TimeUnit.SECONDS)` repeatedly. The first call returns the `WatchKey` corresponding to whichever directory's change was detected first (typically `dirA`, since its file was created first) — `keyToDir.get(key)` resolves this back to `dirA`. `key.pollEvents()` yields the `ENTRY_CREATE` event for `"a-file.txt"`; `watchedDir.resolve((Path) event.context())` combines the directory (`dirA`) with the bare file name from `event.context()` to reconstruct the full path, and the event is printed identifying both the file and which directory it occurred in. `key.reset()` re-arms this key so it can report future events too.

The loop continues and, on a subsequent call, `watcher.poll` returns the `WatchKey` for `dirB`'s change — the same process repeats, correctly attributing `"b-file.txt"`'s creation to `dirB` rather than `dirA`, purely because of the `keyToDir` lookup.

Expected output (the exact temporary directory names will vary each run, since `createTempDirectory` generates unique names):
```
ENTRY_CREATE -> a-file.txt (in watch-a<random-suffix>)
ENTRY_CREATE -> b-file.txt (in watch-b<random-suffix>)
```

## 7. Gotchas & takeaways

> Forgetting to call `key.reset()` after processing a `WatchKey`'s events silently stops that key from ever reporting further events — no exception is thrown, the key simply becomes permanently inactive from that point on. Always call `key.reset()` once you've finished processing a key's events for that round, inside your polling loop, or your watch will quietly stop working after its first batch of events.

- `WatchService` provides file system change notifications (create, modify, delete) for a registered directory, avoiding the need to manually poll and diff directory listings.
- `event.context()` gives only the affected entry's file **name**, not a full path — combine it with the directory the key was registered for to get a complete, usable path.
- Always call `key.reset()` after processing a key's events, or that key will stop delivering any further notifications.
- Watch notification latency depends on the underlying platform's implementation — expect delays on the order of a couple of seconds for changes to actually be observed, not instantaneous notification, and design accordingly (avoid assuming sub-second responsiveness).
- With multiple registered directories sharing one `WatchService`, track which `WatchKey` corresponds to which directory (a `Map<WatchKey, Path>`, as shown above) — this is essential for correctly attributing events once more than one directory is involved.
