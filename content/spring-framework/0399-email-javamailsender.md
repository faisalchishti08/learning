---
card: spring-framework
gi: 399
slug: email-javamailsender
title: "Email (JavaMailSender)"
---

## 1. What it is

`JavaMailSender` is Spring's abstraction over the JavaMail (Jakarta Mail) API for sending email. It wraps the lower-level `Session`/`Transport`/`Message` plumbing behind a small interface with `send(SimpleMailMessage)` and `send(MimeMessagePreparator)` methods, and its default implementation, `JavaMailSenderImpl`, handles SMTP connection setup from simple configuration properties.

```java
@Service
class NotificationService {
    private final JavaMailSender mailSender;
    NotificationService(JavaMailSender mailSender) { this.mailSender = mailSender; }

    void sendWelcomeEmail(String to) {
        SimpleMailMessage message = new SimpleMailMessage();
        message.setTo(to);
        message.setSubject("Welcome!");
        message.setText("Thanks for signing up.");
        mailSender.send(message);
    }
}
```

## 2. Why & when

Sending email over SMTP directly with JavaMail means constructing a `Properties` object for the SMTP session, authenticating, building a `MimeMessage` by hand, and managing `Transport` connect/send/close — verbose, easy to get wrong (especially around resource cleanup and exception translation), and awkward to unit test since it's tightly coupled to a live SMTP connection. `JavaMailSender` exists to make sending mail a one-line call from application code, with configuration (host, port, credentials) externalized to properties, and to make mail-sending code mockable in tests since `JavaMailSender` is just an interface.

Use it whenever an application needs to send transactional email: welcome messages, password resets, order confirmations, alerts. It's a small, focused abstraction — not a full email marketing or templating platform — so pair it with a template engine (Thymeleaf, FreeMarker) for anything beyond plain text, and reach for a dedicated transactional-email service (SendGrid, SES) via their own SDKs instead of raw SMTP when you need delivery tracking, bounce handling, or high-volume sending guarantees.

## 3. Core concept

```
 JavaMailSender (interface)
        |
        v
 JavaMailSenderImpl (default implementation)
        |
        | builds
        v
 jakarta.mail.Session  (SMTP host, port, auth from Spring config)
        |
        | wraps
        v
 SimpleMailMessage (plain text)  or  MimeMessage (HTML, attachments, inline images)
        |
        v
 Transport.send()  --> SMTP server --> recipient's mail server
```

`SimpleMailMessage` covers plain-text email with just to/subject/text; anything richer (HTML body, attachments, embedded images) needs a `MimeMessage`, which `JavaMailSender.createMimeMessage()` produces and `MimeMessageHelper` makes easier to populate.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Application code builds a message, JavaMailSender delivers it via SMTP to the recipient's mail server">
  <rect x="10" y="60" width="150" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="94" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">NotificationService</text>

  <rect x="230" y="60" width="150" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="305" y="94" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">JavaMailSender</text>

  <rect x="450" y="60" width="170" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="535" y="84" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">SMTP server</text>
  <text x="535" y="100" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">-&gt; recipient</text>

  <line x1="160" y1="90" x2="225" y2="90" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <line x1="380" y1="90" x2="445" y2="90" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

Application code never touches `Session`/`Transport` directly — `JavaMailSender` hides SMTP protocol details behind `.send(...)`.

## 5. Runnable example

This example uses a local test SMTP server (`GreenMail`, an in-memory mail server library) so the example is fully self-contained and actually sends and receives real SMTP traffic without needing external mail credentials or network access.

### Level 1 — Basic

Send a plain-text `SimpleMailMessage` and verify it arrived by reading it back from the embedded test server.

```java
import com.icegreen.greenmail.util.GreenMail;
import com.icegreen.greenmail.util.ServerSetup;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSenderImpl;

public class EmailBasic {

    public static void main(String[] args) throws Exception {
        GreenMail greenMail = new GreenMail(new ServerSetup(3025, null, "smtp"));
        greenMail.start();
        try {
            JavaMailSenderImpl mailSender = new JavaMailSenderImpl();
            mailSender.setHost("localhost");
            mailSender.setPort(3025);

            SimpleMailMessage message = new SimpleMailMessage();
            message.setFrom("noreply@example.com");
            message.setTo("newuser@example.com");
            message.setSubject("Welcome!");
            message.setText("Thanks for signing up.");
            mailSender.send(message);

            greenMail.waitForIncomingEmail(2000, 1);
            var received = greenMail.getReceivedMessages()[0];
            System.out.println("Subject: " + received.getSubject());
            System.out.println("Body: " + received.getContent());
        } finally {
            greenMail.stop();
        }
    }
}
```

How to run: add `spring-context-support` (which brings `JavaMailSender`), `jakarta.mail` (or `com.sun.mail:jakarta.mail`), and `com.icegreen:greenmail` (test scope in a real project) to the classpath, then `java EmailBasic.java`.

`JavaMailSenderImpl` is configured to point at the embedded GreenMail server instead of a real SMTP provider. `mailSender.send(message)` opens an SMTP connection, transmits the message, and closes the connection — one call replaces the manual JavaMail `Session`/`Transport` sequence. Reading the message back from GreenMail proves it was genuinely delivered over SMTP, not just constructed in memory.

### Level 2 — Intermediate

Real email needs HTML content and often an attachment — `SimpleMailMessage` can't do either, so this uses `MimeMessage` via `MimeMessageHelper`.

```java
import com.icegreen.greenmail.util.GreenMail;
import com.icegreen.greenmail.util.ServerSetup;
import jakarta.mail.internet.MimeMessage;
import org.springframework.mail.javamail.JavaMailSenderImpl;
import org.springframework.mail.javamail.MimeMessageHelper;

import java.nio.charset.StandardCharsets;

public class EmailIntermediate {

    public static void main(String[] args) throws Exception {
        GreenMail greenMail = new GreenMail(new ServerSetup(3025, null, "smtp"));
        greenMail.start();
        try {
            JavaMailSenderImpl mailSender = new JavaMailSenderImpl();
            mailSender.setHost("localhost");
            mailSender.setPort(3025);

            MimeMessage mimeMessage = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(mimeMessage, true, "UTF-8");
            helper.setFrom("noreply@example.com");
            helper.setTo("newuser@example.com");
            helper.setSubject("Your order confirmation");
            helper.setText("<h1>Thanks!</h1><p>Your order <b>#42</b> shipped.</p>", true); // html=true

            byte[] receiptBytes = "Order #42\nTotal: $59.00".getBytes(StandardCharsets.UTF_8);
            helper.addAttachment("receipt.txt", new org.springframework.core.io.ByteArrayResource(receiptBytes));

            mailSender.send(mimeMessage);

            greenMail.waitForIncomingEmail(2000, 1);
            var received = greenMail.getReceivedMessages()[0];
            System.out.println("Subject: " + received.getSubject());
            System.out.println("Is multipart (has attachment): " + (received.getContent() instanceof jakarta.mail.Multipart));
        } finally {
            greenMail.stop();
        }
    }
}
```

How to run: same dependencies as Level 1, then `java EmailIntermediate.java`.

`mailSender.createMimeMessage()` produces an empty `MimeMessage` tied to this sender's `Session`; `MimeMessageHelper(mimeMessage, true, "UTF-8")` — the `true` requesting multipart support — makes it easy to set an HTML body (`setText(..., true)`) and add an attachment without manually constructing MIME parts. The resulting message is multipart, which the assertion at the end confirms.

### Level 3 — Advanced

Production email sending needs to be asynchronous (so a slow SMTP provider doesn't block a web request), needs retry on transient failures, and typically renders content from a template rather than string-concatenating HTML.

```java
import com.icegreen.greenmail.util.GreenMail;
import com.icegreen.greenmail.util.ServerSetup;
import jakarta.mail.internet.MimeMessage;
import org.springframework.mail.MailSendException;
import org.springframework.mail.javamail.JavaMailSenderImpl;
import org.springframework.mail.javamail.MimeMessageHelper;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executors;

public class EmailAdvanced {

    record OrderConfirmation(String to, String orderId, double total) {}

    static String renderHtml(OrderConfirmation order) {
        // In a real app, this would delegate to Thymeleaf/FreeMarker instead of string building.
        return "<h1>Order confirmed</h1><p>Order <b>%s</b> — total $%.2f</p>"
                .formatted(order.orderId(), order.total());
    }

    static void sendWithRetry(JavaMailSenderImpl mailSender, OrderConfirmation order, int maxAttempts) {
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                MimeMessage mimeMessage = mailSender.createMimeMessage();
                MimeMessageHelper helper = new MimeMessageHelper(mimeMessage, "UTF-8");
                helper.setFrom("noreply@example.com");
                helper.setTo(order.to());
                helper.setSubject("Order " + order.orderId() + " confirmed");
                helper.setText(renderHtml(order), true);
                mailSender.send(mimeMessage);
                System.out.println("Sent to " + order.to() + " on attempt " + attempt);
                return;
            } catch (MailSendException | jakarta.mail.MessagingException e) {
                System.out.println("Attempt " + attempt + " failed: " + e.getMessage());
                if (attempt == maxAttempts) throw new RuntimeException("Giving up after " + maxAttempts + " attempts", e);
            }
        }
    }

    public static void main(String[] args) throws Exception {
        GreenMail greenMail = new GreenMail(new ServerSetup(3025, null, "smtp"));
        greenMail.start();
        var executor = Executors.newFixedThreadPool(2);
        try {
            JavaMailSenderImpl mailSender = new JavaMailSenderImpl();
            mailSender.setHost("localhost");
            mailSender.setPort(3025);

            var order = new OrderConfirmation("customer@example.com", "order-42", 59.00);

            CompletableFuture<Void> future = CompletableFuture.runAsync(
                    () -> sendWithRetry(mailSender, order, 3), executor);
            future.join(); // demo-only: real callers would not block on this

            greenMail.waitForIncomingEmail(2000, 1);
            System.out.println("Confirmed delivered: " + greenMail.getReceivedMessages()[0].getSubject());
        } finally {
            executor.shutdown();
            greenMail.stop();
        }
    }
}
```

How to run: same dependencies as Level 1, then `java EmailAdvanced.java`.

`CompletableFuture.runAsync(..., executor)` moves the actual SMTP send off the caller's thread — in a web application, this is what keeps a slow mail provider from adding latency to an HTTP request that triggers a confirmation email. `sendWithRetry` retries transient `MailSendException`s (connection drops, temporary SMTP errors) up to `maxAttempts` times before giving up, which matters because SMTP relays occasionally reject or time out connections transiently.

## 6. Walkthrough

Trace `EmailAdvanced.main` end to end:

1. **Infrastructure starts.** The embedded GreenMail SMTP server starts listening on port 3025; a small thread pool is created to run the send asynchronously.
2. **Async submission.** `CompletableFuture.runAsync(() -> sendWithRetry(...), executor)` schedules `sendWithRetry` to run on a pool thread and returns immediately — `main`'s thread does not block here (the `future.join()` afterward is only there so this demo program doesn't exit before the async work finishes).
3. **Template rendering.** On the pool thread, `renderHtml(order)` builds the HTML body string from the `OrderConfirmation` data — in a production app this call would instead be `templateEngine.process("order-confirmation", context)` against a Thymeleaf template.
4. **Message construction.** `mailSender.createMimeMessage()` creates an empty message on this sender's mail `Session`; `MimeMessageHelper` populates from/to/subject and sets the HTML body.
5. **Send attempt 1.** `mailSender.send(mimeMessage)` opens an SMTP connection to `localhost:3025` and transmits:

   ```
   SMTP conversation (simplified):
     C: EHLO client
     C: MAIL FROM:<noreply@example.com>
     C: RCPT TO:<customer@example.com>
     C: DATA
     C: Subject: Order order-42 confirmed
        Content-Type: text/html
        <h1>Order confirmed</h1><p>Order <b>order-42</b> — total $59.00</p>
     C: .
     S: 250 OK
   ```

   Since GreenMail is healthy and accepts the message, this succeeds on the first attempt — the `catch` block and retry loop never execute in this run.
6. **Success logged.** `"Sent to customer@example.com on attempt 1"` prints from the pool thread; `sendWithRetry` returns, completing the `CompletableFuture`.
7. **Join and verify.** `future.join()` on the main thread unblocks once the async work finishes; `main` then asks GreenMail for the received message and prints its subject, confirming the round trip completed correctly end to end.

```
main thread:  runAsync(sendWithRetry) --> [returns immediately] --> future.join() waits
pool thread:  render HTML -> build MimeMessage -> SMTP send -> success -> complete future
main thread:  (unblocked) -> read GreenMail inbox -> print confirmation
```

## 7. Gotchas & takeaways

> Gotcha: `JavaMailSenderImpl.send(...)` is a blocking, synchronous SMTP call — invoking it directly inside a web request handler (without an async boundary like the `CompletableFuture`/executor shown in Level 3, or `@Async`) means a slow or unresponsive mail server adds its full latency directly to that HTTP response, and a down mail server can make the request hang or fail entirely.

- `JavaMailSender` is an interface specifically so mail-sending code is trivially mockable in unit tests — inject it and verify `send(...)` was called with the expected message, rather than needing a real (or even embedded) SMTP server for every test.
- Use `SimpleMailMessage` only for plain text; reach for `MimeMessage`/`MimeMessageHelper` the moment you need HTML, attachments, or inline images.
- Always send email asynchronously from request-handling code (`@Async`, a dedicated executor, or a message queue) — never let a mail provider's latency or downtime block a user-facing request.
- For anything beyond a handful of transactional emails, pair `JavaMailSender` with a template engine for the body and consider a dedicated transactional-email provider's SDK for delivery tracking, bounce handling, and reputation management that raw SMTP doesn't give you.
