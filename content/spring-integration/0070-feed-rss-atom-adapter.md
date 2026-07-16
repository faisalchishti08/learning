---
card: spring-integration
gi: 70
slug: feed-rss-atom-adapter
title: "Feed (RSS/Atom) adapter"
---

## 1. What it is

The feed inbound channel adapter (`Feed.inboundAdapter(...)`) polls an RSS or Atom feed URL and emits a message for each new entry found since the last poll, using Rome (the underlying feed-parsing library) to handle both formats transparently. It tracks which entries have already been seen so a repeated poll of the same feed doesn't re-deliver entries already processed.

## 2. Why & when

You reach for the feed adapter when the integration point is a syndication feed rather than a bespoke API:

- **A third party only publishes updates as RSS/Atom** — many news sources, blogs, and changelogs expose no API beyond a feed; the feed adapter is the natural way to turn "new posts" into messages a flow can act on.
- **Aggregating multiple external sources into one internal pipeline** — several feed adapters, each pointed at a different source, can funnel into the same downstream processing (deduplication, tagging, storage) so the rest of the flow doesn't need to know how many sources exist.
- **Polling cadence matters more than instant delivery** — feeds are inherently a polling-based protocol (no feed publisher pushes to subscribers), so the feed adapter fits naturally where "check every few minutes" is an acceptable trade-off, unlike a use case demanding sub-second delivery.

## 3. Core concept

Think of an RSS/Atom feed as a public bulletin board that a publisher pins new notices to over time, in order, without ever removing old ones from the board (usually). Each visitor who checks the board must remember which notices they've already read (by publication date or a unique entry ID) so they don't re-report a notice they already reacted to on a previous visit — that's exactly what the feed adapter's internal "last entry seen" tracking does, so a five-minute poll cycle only surfaces what's genuinely new since the last check.

```java
@Bean
public IntegrationFlow feedPollingFlow() {
    return IntegrationFlow.from(
            Feed.inboundAdapter(new URL("https://blog.example.com/feed.atom"), "exampleBlog"),
            e -> e.poller(Pollers.fixedDelay(300_000)))
        .handle((com.rometools.rome.feed.synd.SyndEntry entry, headers) ->
            notificationService.notifyNewPost(entry.getTitle(), entry.getLink()))
        .get();
}
```

Every five minutes, only entries published since the last successful poll are emitted — the adapter's internal metadata store remembers where it left off.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A feed adapter polls a feed URL, compares entries against what it has already seen, and emits messages only for genuinely new entries since the last poll" >
  <rect x="20" y="20" width="600" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="35" y="45" fill="#e6edf3" font-size="8" font-family="monospace">Feed: [entry-1 (old)] [entry-2 (old)] [entry-3 (new)] [entry-4 (new)]</text>

  <rect x="20" y="90" width="600" height="45" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="35" y="115" fill="#8b949e" font-size="8" font-family="monospace">last seen: entry-2</text>
  <text x="250" y="115" fill="#6db33f" font-size="8" font-family="monospace">-&gt; emits Message(entry-3), Message(entry-4)</text>

  <text x="320" y="14" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Only entries after the last-seen marker become messages</text>
</svg>

Tracking the last-seen entry turns a repeatedly-scanned bulletin board into a stream of only what's genuinely new.

## 5. Runnable example

The scenario: aggregating new blog posts from a feed into notification messages, simulated with an in-memory list of feed entries standing in for a Rome-parsed feed (no real network fetch needed to demonstrate the last-seen tracking and deduplication logic), starting with a basic new-entry check, then adding persistent last-seen tracking across polls, then handling a feed that unexpectedly reorders or removes old entries.

### Level 1 — Basic

```java
// FeedPollingDemo.java
import java.util.*;

public class FeedPollingDemo {
    record Entry(String id, String title, long publishedAt) {}

    public static void main(String[] args) {
        List<Entry> feed = List.of(
            new Entry("e1", "Launch announcement", 100),
            new Entry("e2", "Follow-up post", 200));

        for (Entry e : feed) {
            System.out.println("New post: " + e.title());
        }
    }
}
```

How to run: `java FeedPollingDemo.java`. Expected output: both entries print as new posts — a first poll with no history yet, so everything currently on the feed counts as new.

### Level 2 — Intermediate

```java
// FeedPollingDemo.java
import java.util.*;

public class FeedPollingDemo {
    record Entry(String id, String title, long publishedAt) {}

    // Real-world concern: a repeated poll must not re-report entries already seen. The adapter
    // tracks the newest publishedAt timestamp (or entry ID) it has already delivered.
    static class FeedTracker {
        private long lastSeenPublishedAt = Long.MIN_VALUE;

        List<Entry> pollNew(List<Entry> feed) {
            List<Entry> fresh = feed.stream()
                .filter(e -> e.publishedAt() > lastSeenPublishedAt)
                .sorted(Comparator.comparingLong(Entry::publishedAt))
                .toList();
            if (!fresh.isEmpty()) {
                lastSeenPublishedAt = fresh.get(fresh.size() - 1).publishedAt();
            }
            return fresh;
        }
    }

    public static void main(String[] args) {
        FeedTracker tracker = new FeedTracker();
        List<Entry> feedAtPollOne = List.of(new Entry("e1", "Launch announcement", 100));
        List<Entry> feedAtPollTwo = List.of(
            new Entry("e1", "Launch announcement", 100),
            new Entry("e2", "Follow-up post", 200));

        System.out.println("-- poll 1 --");
        tracker.pollNew(feedAtPollOne).forEach(e -> System.out.println("New post: " + e.title()));
        System.out.println("-- poll 2 --");
        tracker.pollNew(feedAtPollTwo).forEach(e -> System.out.println("New post: " + e.title()));
    }
}
```

How to run: `java FeedPollingDemo.java`. Expected output: poll 1 reports `Launch announcement`; poll 2, even though `e1` is still present in the feed, reports only `Follow-up post` — the last-seen timestamp guard preventing `e1` from being reported twice.

### Level 3 — Advanced

```java
// FeedPollingDemo.java
import java.util.*;

public class FeedPollingDemo {
    record Entry(String id, String title, long publishedAt) {}

    static class FeedTracker {
        private long lastSeenPublishedAt = Long.MIN_VALUE;
        private final Set<String> seenIds = new HashSet<>();

        // Production concern: some feeds republish an entry with an updated timestamp (an edit),
        // or reorder entries unexpectedly -- relying on timestamp alone can either miss a
        // legitimately-edited repost or, worse, silently skip it forever. Track seen IDs too,
        // and treat "seen ID, newer timestamp" as an update rather than a brand-new entry.
        List<Entry> pollNew(List<Entry> feed) {
            List<Entry> fresh = new ArrayList<>();
            for (Entry e : feed.stream().sorted(Comparator.comparingLong(Entry::publishedAt)).toList()) {
                boolean idSeenBefore = seenIds.contains(e.id());
                boolean isNewerThanLastSeen = e.publishedAt() > lastSeenPublishedAt;
                if (!idSeenBefore) {
                    fresh.add(e);
                    seenIds.add(e.id());
                } else if (isNewerThanLastSeen) {
                    System.out.println("Detected edit to already-seen entry: " + e.id());
                }
            }
            if (!feed.isEmpty()) {
                lastSeenPublishedAt = feed.stream().mapToLong(Entry::publishedAt).max().orElse(lastSeenPublishedAt);
            }
            return fresh;
        }
    }

    public static void main(String[] args) {
        FeedTracker tracker = new FeedTracker();

        List<Entry> pollOne = List.of(new Entry("e1", "Launch announcement", 100));
        List<Entry> pollTwo = List.of(
            new Entry("e2", "Follow-up post", 200),
            new Entry("e1", "Launch announcement (corrected)", 250)); // same ID, edited, later timestamp

        System.out.println("-- poll 1 --");
        tracker.pollNew(pollOne).forEach(e -> System.out.println("New post: " + e.title()));
        System.out.println("-- poll 2 --");
        tracker.pollNew(pollTwo).forEach(e -> System.out.println("New post: " + e.title()));
    }
}
```

How to run: `java FeedPollingDemo.java`. Expected output: poll 1 reports `Launch announcement`; poll 2 reports `Follow-up post` as new and prints `Detected edit to already-seen entry: e1` for the edited repost, rather than either silently dropping it or wrongly re-announcing it as a brand-new post.

## 6. Walkthrough

Trace one feed-poll cycle from fetch to notification.

1. **Poller fires**: `Feed.inboundAdapter`'s poller fetches the feed URL and parses it with Rome into a list of `SyndEntry` objects, regardless of whether the underlying document is RSS or Atom — Rome normalizes both formats to the same object model.
2. **Last-seen comparison**: the adapter compares each parsed entry against its stored last-seen marker (by publish date, typically), keeping only entries newer than what was already delivered on a previous poll.
3. **Message emission**: each genuinely new entry becomes the payload of one outbound message, carrying the entry's title, link, and publish date.
4. **Downstream handling**: a `.handle(...)` step acts on each new entry — in the example, calling `notificationService.notifyNewPost(...)` — with any per-entry failure isolated so one malformed or unusual entry doesn't block the rest of the batch.
5. **Marker update**: after a successful poll, the adapter updates its stored last-seen marker so the next poll only looks for entries newer still — this state typically persists across restarts via a metadata store (card 0046) so a restart doesn't cause a flood of "new" entries that were actually already processed.
6. **Edge case handling**: a well-built flow layered on top of the raw adapter (as in Level 3) also accounts for feeds that edit or reorder existing entries, distinguishing a genuine new entry from an update to one already seen.

```
poller tick
  -> fetch + parse feed (Rome, RSS or Atom transparently)
    -> filter: entry.publishedAt > lastSeenMarker
      -> Message per new entry
        -> notificationService.notifyNewPost(entry)
          -> update lastSeenMarker (persisted via metadata store)
```

## 7. Gotchas & takeaways

> **Gotcha:** the feed adapter's last-seen tracking is only as reliable as the feed's own publish-date and entry-ID discipline — a poorly-behaved feed that reuses IDs, omits dates, or silently edits old entries in place can cause missed or duplicate deliveries no matter how carefully the adapter's own logic is written; treat downstream processing as needing to tolerate the occasional duplicate.

- Persist the last-seen marker in a durable metadata store (card 0046), not just in memory — otherwise a restart re-treats the entire current feed content as new, flooding downstream with duplicates.
- Feeds are pull-based by nature; there is no equivalent of IMAP IDLE (card 0063) for instant push notification of a new post, so polling frequency is a direct trade-off between freshness and load on the feed's host.
- Rome's unified object model means the same flow code handles both RSS and Atom feeds without branching on format, but format-specific fields (some feeds put extra data in custom XML namespaces) still need explicit handling if a flow depends on them.
- A feed adapter is a convenient way to bridge an external, publisher-controlled data source into an internal flow, but it's a one-way, read-only integration — there's no equivalent outbound feed-publishing adapter, since a flow producing its own feed is normally done by exposing an HTTP endpoint that serves RSS/Atom XML directly.
