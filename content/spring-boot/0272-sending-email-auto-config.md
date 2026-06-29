---
card: spring-boot
gi: 272
slug: sending-email-auto-config
title: Sending email auto-config
---

## 1. What it is

Spring Boot auto-configures a `JavaMailSender` bean when `spring-boot-starter-mail` is on the classpath and `spring.mail.host` is set. `JavaMailSender` wraps the Jakarta Mail (formerly JavaMail) API and provides:

- Simple text and HTML email sending.
- Multipart messages with attachments.
- Template-based email composition (Thymeleaf, Freemarker).
- Connection pooling and protocol configuration (SMTP, SMTP+TLS, SMTP+SSL).

Add with:
```xml
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-mail</artifactId>
</dependency>
```

## 2. Why & when

Email sending appears in almost every application: welcome emails, password resets, order confirmations, alerts, and notifications. Spring Boot's auto-configuration:

- Eliminates boilerplate `Session` configuration.
- Externalises SMTP credentials to `application.properties` (or environment variables) rather than hardcoding them.
- Provides `JavaMailSenderImpl` ready to use — just inject and send.

For high-volume email (transactional email at scale), a dedicated service (SendGrid, Mailgun, AWS SES) is preferred over a raw SMTP connection, but Spring Boot's `JavaMailSender` works with any SMTP endpoint including those provided by transactional email services.

## 3. Core concept

The auto-configuration reads `spring.mail.*` properties and creates a `JavaMailSenderImpl` bean:

```properties
spring.mail.host=smtp.gmail.com
spring.mail.port=587
spring.mail.username=myapp@gmail.com
spring.mail.password=${GMAIL_APP_PASSWORD}
spring.mail.properties.mail.smtp.auth=true
spring.mail.properties.mail.smtp.starttls.enable=true
```

`JavaMailSender` provides two levels of API:

1. **`SimpleMailMessage`** — for plain-text emails: `to`, `from`, `subject`, `text`.
2. **`MimeMessageHelper`** — for rich emails: HTML body, attachments, inline images, multiple recipients with names.

For templated emails, inject Thymeleaf's `TemplateEngine` alongside `JavaMailSender`:

```java
String htmlBody = templateEngine.process("welcome-email", ctx);
helper.setText(htmlBody, true); // true = HTML
```

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Email auto-configuration: JavaMailSender bean created from spring.mail properties, sends via SMTP">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Properties -->
  <rect x="10" y="80" width="160" height="70" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="90" y="105" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">spring.mail.*</text>
  <text x="90" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">host, port, user, pass</text>
  <text x="90" y="137" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">SMTP properties</text>

  <!-- JavaMailSender bean -->
  <rect x="225" y="70" width="170" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="310" y="97" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">JavaMailSenderImpl</text>
  <text x="310" y="115" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">@Bean (auto-configured)</text>
  <text x="310" y="131" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">session + transport mgmt</text>
  <text x="310" y="147" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">MimeMessage builder</text>

  <!-- Service -->
  <rect x="455" y="80" width="120" height="70" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="515" y="105" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">EmailService</text>
  <text x="515" y="122" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">@Autowired</text>
  <text x="515" y="137" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">JavaMailSender</text>

  <!-- SMTP server -->
  <rect x="590" y="80" width="100" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="640" y="105" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">SMTP Server</text>
  <text x="640" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Gmail / SES</text>
  <text x="640" y="137" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Mailgun etc.</text>

  <line x1="170" y1="115" x2="223" y2="115" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="395" y1="115" x2="453" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="575" y1="115" x2="588" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <text x="350" y="210" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">One @Bean, zero boilerplate — credentials from application.properties or env vars</text>
</svg>

Auto-configuration builds `JavaMailSenderImpl` from `spring.mail.*` properties; inject it and send.

## 5. Runnable example

```java
// EmailAutoConfigDemo.java — run with: java EmailAutoConfigDemo.java
// Demonstrates email sending patterns and required configuration
// for Spring Boot's JavaMailSender auto-config.

import java.util.Properties;
import jakarta.mail.*;
import jakarta.mail.internet.*;

public class EmailAutoConfigDemo {

    public static void main(String[] args) throws Exception {
        System.out.println("=== Sending Email Auto-config Demo ===\n");
        printConfig();
        printServiceExample();
        printTemplateExample();
        demonstrateRawJakartaMail();
    }

    static void printConfig() {
        System.out.println("--- application.properties ---");
        System.out.println("""
            # Gmail via SMTP (use App Password, not account password):
            spring.mail.host=smtp.gmail.com
            spring.mail.port=587
            spring.mail.username=myapp@gmail.com
            spring.mail.password=${GMAIL_APP_PASSWORD}
            spring.mail.properties.mail.smtp.auth=true
            spring.mail.properties.mail.smtp.starttls.enable=true
            spring.mail.properties.mail.smtp.starttls.required=true

            # AWS SES SMTP:
            # spring.mail.host=email-smtp.us-east-1.amazonaws.com
            # spring.mail.port=587
            # spring.mail.username=${SES_SMTP_USER}
            # spring.mail.password=${SES_SMTP_PASSWORD}

            # Test mode (GreenMail / MailHog for local dev):
            # spring.mail.host=localhost
            # spring.mail.port=1025
            # spring.mail.properties.mail.smtp.auth=false
            """);
    }

    static void printServiceExample() {
        System.out.println("--- EmailService using JavaMailSender ---");
        System.out.println("""
            @Service
            public class EmailService {
                private final JavaMailSender mailSender;

                // Simple text email:
                public void sendWelcome(String to, String name) {
                    SimpleMailMessage msg = new SimpleMailMessage();
                    msg.setFrom("noreply@myapp.com");
                    msg.setTo(to);
                    msg.setSubject("Welcome to MyApp!");
                    msg.setText("Hi " + name + ", welcome aboard!");
                    mailSender.send(msg);
                }

                // HTML email with attachment:
                public void sendReport(String to, byte[] pdf) throws MessagingException {
                    MimeMessage mime = mailSender.createMimeMessage();
                    MimeMessageHelper helper = new MimeMessageHelper(mime, true, "UTF-8");
                    helper.setFrom("reports@myapp.com");
                    helper.setTo(to);
                    helper.setSubject("Monthly Report");
                    helper.setText("<h1>Report Ready</h1><p>See attachment.</p>", true);
                    helper.addAttachment("report.pdf",
                        new ByteArrayResource(pdf), "application/pdf");
                    mailSender.send(mime);
                }
            }
            """);
    }

    static void printTemplateExample() {
        System.out.println("--- Thymeleaf HTML email template ---");
        System.out.println("""
            // templates/email/welcome.html:
            // <!DOCTYPE html>
            // <html xmlns:th="http://www.thymeleaf.org">
            // <body>
            //   <h1 th:text="'Welcome, ' + ${name} + '!'">Welcome!</h1>
            //   <p>Click <a th:href="${activationUrl}">here</a> to activate.</p>
            // </body></html>

            // In EmailService (inject TemplateEngine):
            @Autowired TemplateEngine templateEngine;

            public void sendActivation(String to, String name, String token)
                    throws MessagingException {
                Context ctx = new Context(Locale.ENGLISH);
                ctx.setVariable("name", name);
                ctx.setVariable("activationUrl",
                    "https://myapp.com/activate?token=" + token);
                String html = templateEngine.process("email/welcome", ctx);

                MimeMessage mime = mailSender.createMimeMessage();
                MimeMessageHelper h = new MimeMessageHelper(mime, false, "UTF-8");
                h.setTo(to);
                h.setSubject("Activate your account");
                h.setText(html, true);
                mailSender.send(mime);
            }
            """);
    }

    static void demonstrateRawJakartaMail() throws Exception {
        System.out.println("--- Raw Jakarta Mail (what Spring abstracts) ---");

        // This is what Spring Boot's auto-config replaces with clean properties:
        Properties props = new Properties();
        props.put("mail.smtp.auth", "true");
        props.put("mail.smtp.starttls.enable", "true");
        props.put("mail.smtp.host", "smtp.gmail.com");
        props.put("mail.smtp.port", "587");

        System.out.println("  Raw Jakarta Mail Session properties:");
        props.forEach((k, v) -> System.out.println("    " + k + "=" + v));
        System.out.println();
        System.out.println("  With Spring Boot: replace all of the above with spring.mail.*");
        System.out.println("  Spring creates the Session and Transport automatically.");
        System.out.println();
        System.out.println("--- Testing without a real SMTP server ---");
        System.out.println("""
            # Option 1: GreenMail (embedded SMTP for tests):
            @Bean GreenMail greenMail() {
                GreenMail gm = new GreenMail(new ServerSetup(1025, null, "smtp"));
                gm.start();
                return gm;
            }
            // Check sent messages: greenMail.getReceivedMessages()

            # Option 2: MailHog (Docker):
            # docker run -p 1025:1025 -p 8025:8025 mailhog/mailhog
            # spring.mail.host=localhost spring.mail.port=1025
            # View emails at http://localhost:8025

            # Option 3: Mock JavaMailSender in @SpringBootTest:
            @MockBean JavaMailSender mailSender;
            // verify(mailSender).send(any(MimeMessage.class));
            """);
    }
}
```

**How to run:** `java EmailAutoConfigDemo.java` (requires `jakarta.mail` on classpath)

## 6. Walkthrough

- **`spring.mail.properties.mail.smtp.starttls.enable=true`** — STARTTLS upgrades a plain connection to TLS after the initial handshake. Port 587 + STARTTLS is the modern standard for SMTP. Port 465 + `ssl.enable=true` is the older SSL-first approach; some providers still require it.
- **`SimpleMailMessage`** — the simplest approach: set fields and call `send()`. No HTML, no attachments. Good for internal system alerts or developer notifications.
- **`MimeMessageHelper(mime, true, "UTF-8")`** — the `true` argument enables multipart mode (required for attachments). `"UTF-8"` sets encoding for the subject and body. Always use UTF-8 to handle international characters in names and subjects.
- **Thymeleaf `Context`** — for email templates, create a Thymeleaf `Context` (not the Spring MVC one) and populate variables. `templateEngine.process("email/welcome", ctx)` renders the template to an HTML string without any HTTP context.
- **GreenMail** — an in-process SMTP server for testing. `greenMail.getReceivedMessages()` returns the `MimeMessage[]` actually sent during the test. More reliable than `@MockBean JavaMailSender` because it tests the actual email composition logic.

## 7. Gotchas & takeaways

> **Send email asynchronously in production.** `mailSender.send()` makes a network call that can take 1–5 seconds or time out. Calling it synchronously in an HTTP request thread makes the user wait. Wrap it in `@Async` or publish an event and handle email in a listener.

> **Never store SMTP passwords in `application.properties` committed to source control.** Use `${SMTP_PASSWORD}` with the value injected as an environment variable or from a secrets manager. Gmail accounts should use an "App Password" (2FA must be enabled), not the account password.

- Use GreenMail or MailHog for local and CI email testing — no real SMTP server needed.
- `MimeMessageHelper.addInline("img", resource, "image/png")` adds inline images; reference them in HTML with `<img src="cid:img">`.
- Set `spring.mail.test-connection=true` to verify SMTP connectivity at startup (fails fast if credentials are wrong).
- For bulk email, use SendGrid/Mailgun REST APIs directly (via `RestClient`) rather than SMTP — they're faster, more reliable, and provide delivery analytics.
- HTML emails should include a plain-text fallback: `helper.setText(plainText, htmlText)` — the client shows whichever is appropriate.
