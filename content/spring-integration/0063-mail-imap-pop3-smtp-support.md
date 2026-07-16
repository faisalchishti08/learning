---
card: spring-integration
gi: 63
slug: mail-imap-pop3-smtp-support
title: "Mail (IMAP/POP3/SMTP) support"
---

## 1. What it is

Mail support (`Mail.imapInboundAdapter(...)`/`Mail.imapIdleAdapter(...)`/`Mail.outboundAdapter(...)`) connects a flow to an email mailbox: reading incoming messages over IMAP or POP3, and sending outgoing messages over SMTP. Each retrieved email becomes a `Message` carrying the mail body as payload and headers like subject, from-address, and attachments, and each outbound send takes a message and renders it as an email over SMTP.

## 2. Why & when

You reach for mail support when email itself is the integration protocol at one end of the flow:

- **A legacy or external system's only integration point is a mailbox** — some partners, ticketing systems, or internal tools only know how to send and receive email, and adapting to that constraint is cheaper than asking them to change.
- **Notifications need to reach a human inbox** — order confirmations, alerts, and reports are naturally consumed as email by people, not as a message on a queue they'd have to check separately.
- **IMAP IDLE gives near-real-time inbound delivery** — rather than polling a mailbox on an interval, `Mail.imapIdleAdapter` uses the IMAP IDLE command so the mail server pushes a notification the moment new mail arrives, closer in spirit to an event-driven adapter than a polling one.

## 3. Core concept

Think of a mailbox as a shared physical inbox on a desk: IMAP is like being able to look at the tray, read a letter, and leave it there (or file it in a folder) without removing it, so anyone else with access sees the same tray. POP3 is like reaching in, taking the letter out, and walking away with it — once retrieved, it is (by default) gone from the tray. SMTP is the outgoing mail slot: drop a letter in, and the postal system takes it from there.

```java
@Bean
public IntegrationFlow imapInboundFlow() {
    return IntegrationFlow.from(Mail.imapInboundAdapter("imaps://user:pass@imap.example.com/INBOX")
            .shouldMarkMessagesAsRead(true)
            .javaMailProperties(p -> p.put("mail.imap.socketFactory.fallback", "false")),
            e -> e.poller(Pollers.fixedDelay(30_000)))
        .handle((jakarta.mail.internet.MimeMessage msg, headers) -> ticketService.createFrom(msg))
        .get();
}
```

Marking messages as read after processing keeps IMAP's shared-tray semantics from re-delivering the same email on the next poll.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="IMAP leaves mail on the server and syncs read state; POP3 removes mail from the server on retrieval; SMTP is the separate outbound path for sending" >
  <rect x="20" y="20" width="180" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">IMAP</text>
  <text x="110" y="60" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">mail stays on server</text>
  <text x="110" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">read/flag state synced</text>

  <rect x="230" y="20" width="180" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">POP3</text>
  <text x="320" y="60" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">mail downloaded</text>
  <text x="320" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">removed from server (default)</text>

  <rect x="440" y="20" width="180" height="60" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="530" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">SMTP</text>
  <text x="530" y="60" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">outbound send only</text>
  <text x="530" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">separate path from inbound</text>

  <text x="320" y="110" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Choose IMAP when other clients/folders must see the same mailbox state; POP3 for a single simple consumer.</text>
</svg>

IMAP mirrors a shared mailbox's state; POP3 hands you the mail and forgets it; SMTP only ever sends.

## 5. Runnable example

The scenario: a support-ticket ingestion flow that reads incoming emails and creates tickets, simulated with an in-memory mailbox (no real mail server needed to demonstrate the adapter logic), starting with reading one message, then adding read-state tracking to avoid reprocessing, then handling malformed or duplicate mail safely.

### Level 1 — Basic

```java
// MailIngestDemo.java
import java.util.*;

public class MailIngestDemo {
    record Email(String from, String subject, String body) {}

    // Stand-in for what Mail.imapInboundAdapter hands the flow: one MimeMessage per poll.
    static Email fetchNext(Queue<Email> mailbox) { return mailbox.poll(); }

    static void createTicket(Email e) {
        System.out.println("Ticket created from " + e.from() + ": " + e.subject());
    }

    public static void main(String[] args) {
        Queue<Email> mailbox = new LinkedList<>();
        mailbox.add(new Email("customer@example.com", "Login broken", "I can't log in since this morning."));

        Email e = fetchNext(mailbox);
        if (e != null) createTicket(e);
    }
}
```

How to run: `java MailIngestDemo.java`. Expected output: `Ticket created from customer@example.com: Login broken` — one email in, one ticket out.

### Level 2 — Intermediate

```java
// MailIngestDemo.java
import java.util.*;

public class MailIngestDemo {
    record Email(String id, String from, String subject, String body) {}

    // Real-world concern: IMAP polling can see the same message again before it's marked read
    // (shouldMarkMessagesAsRead ordinarily prevents this, but the adapter must track processed IDs
    // defensively in case of a crash between fetch and mark-as-read).
    static class TicketIngestor {
        private final Set<String> processedIds = new HashSet<>();

        void ingest(Email e) {
            if (!processedIds.add(e.id())) {
                System.out.println("Skipping already-processed email " + e.id());
                return;
            }
            System.out.println("Ticket created from " + e.from() + ": " + e.subject());
        }
    }

    public static void main(String[] args) {
        Queue<Email> mailbox = new LinkedList<>();
        mailbox.add(new Email("msg-1", "customer@example.com", "Login broken", "..."));
        mailbox.add(new Email("msg-1", "customer@example.com", "Login broken", "...")); // re-delivered

        TicketIngestor ingestor = new TicketIngestor();
        Email e;
        while ((e = mailbox.poll()) != null) ingestor.ingest(e);
    }
}
```

How to run: `java MailIngestDemo.java`. Expected output: `Ticket created from customer@example.com: Login broken` once, then `Skipping already-processed email msg-1` — the idempotency guard doing the job that `shouldMarkMessagesAsRead` plus a processed-ID cache does together in production.

### Level 3 — Advanced

```java
// MailIngestDemo.java
import java.util.*;

public class MailIngestDemo {
    record Email(String id, String from, String subject, String body) {}

    static class MalformedMailException extends RuntimeException {
        MalformedMailException(String msg) { super(msg); }
    }

    static class TicketIngestor {
        private final Set<String> processedIds = new HashSet<>();
        private final List<Email> deadLetter = new ArrayList<>();

        void ingest(Email e) {
            if (!processedIds.add(e.id())) {
                System.out.println("Skipping already-processed email " + e.id());
                return;
            }
            try {
                validate(e);
                System.out.println("Ticket created from " + e.from() + ": " + e.subject());
            } catch (MalformedMailException ex) {
                // Production concern: don't let one bad email (missing subject, spoofed sender,
                // encoding garbage) stop the whole poll -- quarantine it and keep going.
                System.out.println("Quarantining malformed email " + e.id() + ": " + ex.getMessage());
                deadLetter.add(e);
            }
        }

        private void validate(Email e) {
            if (e.from() == null || e.from().isBlank()) throw new MalformedMailException("missing sender");
            if (e.subject() == null || e.subject().isBlank()) throw new MalformedMailException("missing subject");
        }
    }

    public static void main(String[] args) {
        Queue<Email> mailbox = new LinkedList<>();
        mailbox.add(new Email("msg-1", "customer@example.com", "Login broken", "..."));
        mailbox.add(new Email("msg-2", "", "No sender", "..."));            // malformed
        mailbox.add(new Email("msg-1", "customer@example.com", "Login broken", "...")); // duplicate

        TicketIngestor ingestor = new TicketIngestor();
        Email e;
        while ((e = mailbox.poll()) != null) ingestor.ingest(e);

        System.out.println("Dead-lettered: " + ingestor.deadLetter.size());
    }
}
```

How to run: `java MailIngestDemo.java`. Expected output: `msg-1` creates a ticket, `msg-2` is quarantined with a validation error, the repeated `msg-1` is skipped as a duplicate, and `Dead-lettered: 1` confirms the malformed email was isolated rather than crashing the poll.

## 6. Walkthrough

Trace a support email from arrival to ticket creation.

1. **Poll or IDLE fires**: the `Mail.imapInboundAdapter`'s poller (or an IDLE-based adapter's push notification) checks the configured folder for new messages matching the search filter (commonly "unseen").
2. **Fetch**: the adapter retrieves the raw `MimeMessage` — headers (from, subject, date), body (text or HTML), and any attachments.
3. **Wrap as Message**: the adapter builds a Spring Integration `Message` with the `MimeMessage` (or its extracted text) as payload, and mail-specific headers (`MailHeaders.SUBJECT`, `MailHeaders.FROM`) attached.
4. **Flow processing**: the message flows through whatever handler chain follows — in the example, a `.handle(...)` step that extracts sender and subject and calls `ticketService.createFrom(msg)`, which validates the fields and either creates a ticket or dead-letters the malformed input.
5. **Mark as read**: if `shouldMarkMessagesAsRead(true)` is set, the adapter flags the message as seen on the server so the next poll's "unseen" search does not return it again — mirroring the idempotency guard the example adds defensively in Java.
6. **Outbound (separate path)**: a reply or notification uses `Mail.outboundAdapter(...)` on a different flow, taking a message and rendering it as a `MimeMessage` sent over SMTP — this path never touches the inbound mailbox at all.

```
IMAP poll (unseen search)
    -> fetch MimeMessage
        -> wrap as Message{payload, MailHeaders}
            -> ticketService.createFrom(msg)   // validate, create or dead-letter
                -> mark as read (IMAP only)
```

## 7. Gotchas & takeaways

> **Gotcha:** POP3's default behavior removes mail from the server on retrieval, so a crash between fetch and downstream processing loses the message permanently — IMAP's "mark as read after processing" model, plus an idempotency guard for the rare re-delivery, is the safer default for anything where losing a message matters.

- IMAP IDLE reduces the poll-interval latency of ordinary polling adapters to near-real-time, but not every mail server or provider supports it — check before relying on it.
- Email is not designed as a reliable message queue: no guaranteed ordering, no transactional delivery, and providers can silently rate-limit or throttle. Treat it as best-effort, not a replacement for a proper broker.
- Attachments and HTML bodies need explicit MIME-part handling; a naive `getContent()` call on a multipart message returns a `Multipart` object, not a plain string.
- Outbound SMTP sending has nothing to do with the inbound adapter's mailbox — they are separate flows, often against separate accounts (a "no-reply" sender vs. a monitored support inbox).
