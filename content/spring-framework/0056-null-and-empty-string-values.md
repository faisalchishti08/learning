---
card: spring-framework
gi: 56
slug: null-and-empty-string-values
title: Null and empty string values
---

## 1. What it is

Spring's XML configuration distinguishes between **null**, **empty string**, and an absent property. By default, omitting a `<property>` leaves the field at its Java default (`null` for objects, `0` for primitives). Setting `<value></value>` or `<value/>` injects an **empty string** `""`. Setting `<null/>` explicitly injects a **`null`** reference. In annotation-driven code, `@Value("")` injects an empty string, while `@Value("${key:#{null}}")` can inject null.

```xml
<bean id="mailer" class="Mailer">
    <property name="replyTo">
        <null/>         <!-- explicitly null — Spring knows you mean null, not "" -->
    </property>
    <property name="bccAddress">
        <value></value> <!-- empty string "" — valid non-null value -->
    </property>
    <property name="fromAddress" value="noreply@example.com"/>
</bean>
```

In annotation-driven code:
```java
@Value("${mail.replyTo:#{null}}")   // null if property absent
private String replyTo;

@Value("${mail.bcc:}")              // "" (empty string) if property absent
private String bccAddress;
```

In one sentence: **Spring's `<null/>` element injects an explicit `null` reference, `<value></value>` injects an empty `String ""`, and omitting the property leaves the Java field at its default — three distinct states you must choose deliberately.**

## 2. Why & when

Distinguishing null from empty string matters in practice:

- **Optional fields** — a `replyTo` email address of `null` means "omit the Reply-To header"; `""` might be serialised as an empty string in JSON or set a header to a blank value.
- **Database nullable columns** — `NULL` vs empty string behave differently in SQL queries and constraints.
- **Collection fields** — `null` list vs empty list (`[]`) behave differently in `for` loops (NPE vs no iterations).
- **`@NonNull` annotations** — passing an empty string where null is expected passes the null-check but may fail later; vice versa.

Use `<null/>` when the semantic is "not set / absent". Use `<value></value>` when the semantic is "blank/empty is a valid value".

## 3. Core concept

```
XML                   Java value injected    Notes
─────────────────     ───────────────────    ─────
<property omitted>    field's Java default   null for Object, 0 for int, etc.
<value></value>       ""  (empty String)     valid non-null String
<value/>              ""  (empty String)     same as above (self-closing)
<null/>               null                   explicit null injection

Annotation
─────────────────────────────────      ────────────────────────
@Value("${k:}")                        "" if key absent
@Value("${k:#{null}}")                 null if key absent
@Value("")                             "" always (literal)
@Value("#{null}")                      null always (SpEL)
field not annotated, no wiring         field keeps Java default (usually null)
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three distinct states: null, empty string, and absent — each injected differently">
  <defs>
    <marker id="a56" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <rect x="5" y="5" width="630" height="190" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="320" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">null vs empty-string vs absent</text>

  <!-- null -->
  <rect x="20" y="35" width="185" height="110" rx="5" fill="#1c2430" stroke="#ff6b6b" stroke-width="1.5"/>
  <text x="112" y="55" fill="#ff6b6b" font-size="10" text-anchor="middle" font-family="sans-serif">&lt;null/&gt;</text>
  <text x="112" y="73" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">injects Java null</text>
  <text x="112" y="89" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">field == null → true</text>
  <text x="112" y="105" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">field.isEmpty() → NullPointerException</text>
  <text x="112" y="121" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">use: "not set" / optional fields</text>
  <text x="112" y="137" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">SQL: INSERT INTO t VALUES (NULL)</text>

  <!-- empty string -->
  <rect x="225" y="35" width="185" height="110" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="317" y="55" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">&lt;value&gt;&lt;/value&gt;</text>
  <text x="317" y="73" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">injects "" (empty string)</text>
  <text x="317" y="89" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">field == null → false</text>
  <text x="317" y="105" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">field.isEmpty() → true</text>
  <text x="317" y="121" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">use: blank/empty is valid</text>
  <text x="317" y="137" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">SQL: INSERT INTO t VALUES ('')</text>

  <!-- absent -->
  <rect x="430" y="35" width="185" height="110" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="522" y="55" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(omitted)</text>
  <text x="522" y="73" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Java field default</text>
  <text x="522" y="89" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Object fields: null</text>
  <text x="522" y="105" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">int/double: 0 / 0.0</text>
  <text x="522" y="121" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">boolean: false</text>
  <text x="522" y="137" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">use: rely on field initialiser</text>

  <text x="320" y="175" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Three distinct states. Choosing wrong breaks null-checks, SQL inserts, and serialisation.</text>
</svg>

`<null/>`, `<value></value>`, and an omitted property inject three different values. All three look like "nothing" but behave very differently in code.

## 5. Runnable example

Scenario: an `EmailConfig` bean with optional fields — `replyTo` (null means omit), `bcc` (empty string means blank), `subject` (omitted uses field initialiser default).

### Level 1 — Basic

Demonstrate null vs empty string vs absent in a simple config class.

```java
// NullEmptyDemo.java — run with: java NullEmptyDemo.java

public class NullEmptyDemo {

    static class EmailConfig {
        String fromAddress;   // will be set
        String replyTo;       // null  — "not set"
        String bcc;           // ""   — explicitly empty
        String subject = "No Subject";  // field initialiser — omitted property

        void print() {
            System.out.println("  fromAddress : [" + fromAddress + "]");
            System.out.println("  replyTo     : " + (replyTo == null ? "null (not set)" : "[" + replyTo + "]"));
            System.out.println("  bcc         : " + (bcc == null ? "null" : "[" + bcc + "] (empty=" + bcc.isEmpty() + ")"));
            System.out.println("  subject     : [" + subject + "] (default)");
        }

        void buildMimeHeaders() {
            System.out.println("\n  Building MIME headers:");
            System.out.println("  From: " + fromAddress);
            if (replyTo != null) {                    // only add if set
                System.out.println("  Reply-To: " + replyTo);
            }
            if (bcc != null && !bcc.isEmpty()) {      // only add if non-blank
                System.out.println("  Bcc: " + bcc);
            } else if (bcc != null) {
                System.out.println("  Bcc: (blank — header omitted)");
            }
        }
    }

    // ── simulate Spring injection ──────────────────────────────────────
    static EmailConfig buildBean() {
        EmailConfig cfg = new EmailConfig();
        cfg.fromAddress = "noreply@example.com";   // <value>noreply@example.com</value>
        cfg.replyTo     = null;                    // <null/>
        cfg.bcc         = "";                      // <value></value>
        // subject: omitted — stays "No Subject"
        return cfg;
    }

    public static void main(String[] args) {
        EmailConfig cfg = buildBean();
        System.out.println("[BEAN] EmailConfig injected fields:");
        cfg.print();
        cfg.buildMimeHeaders();

        System.out.println("\n[NULL CHECKS]");
        System.out.println("  replyTo == null  : " + (cfg.replyTo == null));
        System.out.println("  bcc     == null  : " + (cfg.bcc == null));
        System.out.println("  bcc.isEmpty()    : " + cfg.bcc.isEmpty());
        System.out.println("  subject omitted? : " + ("No Subject".equals(cfg.subject)));
    }
}
```

How to run: `java NullEmptyDemo.java`

`replyTo = null` → the Reply-To header is omitted from the email. `bcc = ""` → a BCC header exists but its value is blank (no recipients). `subject` was never injected — it stays at its Java field initialiser value `"No Subject"`. All three are different: one is absent, one is null, one is empty-string.

### Level 2 — Intermediate

Real-world database record where `null` vs `""` changes SQL INSERT and query behaviour.

```java
// NullEmptyDemo2.java — run with: java NullEmptyDemo2.java
import java.util.*;

public class NullEmptyDemo2 {

    record UserProfile(String userId, String displayName, String bio, String website) {
        // bio=null  → not provided; bio="" → provided but blank
        // website=null → not set; website="" → set to empty (bad data)
    }

    static class UserProfileRepository {

        void insert(UserProfile p) {
            System.out.println("[INSERT] user_profiles:");
            System.out.println("  user_id      = '" + p.userId() + "'");
            // NULL vs '' makes a real difference in SQL
            System.out.println("  display_name = " + sqlLiteral(p.displayName()));
            System.out.println("  bio          = " + sqlLiteral(p.bio()));
            System.out.println("  website      = " + sqlLiteral(p.website()));
        }

        void findByBioStatus(List<UserProfile> profiles) {
            System.out.println("\n[QUERY] users by bio status:");
            for (UserProfile p : profiles) {
                String status;
                if (p.bio() == null)        status = "bio NOT PROVIDED (IS NULL)";
                else if (p.bio().isBlank()) status = "bio PROVIDED BUT BLANK";
                else                         status = "bio SET: " + p.bio();
                System.out.println("  " + p.userId() + " → " + status);
            }
        }

        private String sqlLiteral(String val) {
            return val == null ? "NULL" : "'" + val + "'";
        }
    }

    static List<UserProfile> buildProfiles() {
        return List.of(
            new UserProfile("u001", "Alice",  "Java developer",   "https://alice.dev"),   // all set
            new UserProfile("u002", "Bob",    null,               null),                   // bio+website: null
            new UserProfile("u003", "Carol",  "",                 ""),                     // bio+website: empty
            new UserProfile("u004", null,     "Anonymous writer", null)                    // displayName: null
        );
    }

    public static void main(String[] args) {
        UserProfileRepository repo = new UserProfileRepository();
        List<UserProfile> profiles = buildProfiles();

        for (UserProfile p : profiles) {
            repo.insert(p);
            System.out.println();
        }

        repo.findByBioStatus(profiles);

        System.out.println("\n[NULL SAFETY DEMO]");
        for (UserProfile p : profiles) {
            // Safe null handling
            String safeDisplay = p.displayName() != null ? p.displayName() : "(anonymous)";
            String safeBio     = p.bio() != null
                ? (p.bio().isBlank() ? "(blank bio)" : p.bio())
                : "(not set)";
            System.out.printf("  %-5s display=%-15s bio=%s%n",
                p.userId(), safeDisplay, safeBio);
        }
    }
}
```

How to run: `java NullEmptyDemo2.java`

Bob's `bio=null` → SQL `NULL` → query `WHERE bio IS NULL` finds Bob. Carol's `bio=""` → SQL `''` → `WHERE bio IS NULL` misses Carol; `WHERE bio = ''` finds her. These are entirely different rows. Spring's `<null/>` vs `<value></value>` produces these different SQL outcomes.

### Level 3 — Advanced

JSON serialisation, validation, and API contract: `null` vs `""` vs absent produce different JSON payloads and trigger different validation errors.

```java
// NullEmptyDemo3.java — run with: java NullEmptyDemo3.java
import java.util.*;
import java.util.stream.Collectors;

public class NullEmptyDemo3 {

    // ── request model with explicit null / empty / absent semantics ────
    static class UpdateProfileRequest {
        final Optional<String> displayName;  // Optional.empty = not provided at all
        final String           bio;          // null="explicitly clear", ""="blank"
        final String           website;      // null="remove", ""="invalid but submitted"

        UpdateProfileRequest(Optional<String> displayName, String bio, String website) {
            this.displayName = displayName;
            this.bio         = bio;
            this.website     = website;
        }
    }

    // ── validator ─────────────────────────────────────────────────────
    static class ProfileValidator {
        List<String> validate(UpdateProfileRequest req) {
            List<String> errors = new ArrayList<>();

            // displayName: if provided, must not be blank
            req.displayName.ifPresent(name -> {
                if (name.isBlank()) errors.add("displayName: provided but blank");
                else if (name.length() > 50) errors.add("displayName: max 50 chars");
            });

            // bio: null is ok (clear it); "" is technically ok but worth flagging
            if ("".equals(req.bio)) errors.add("bio: empty string submitted (use null to clear)");

            // website: null = remove (ok); "" = invalid URL
            if ("".equals(req.website)) errors.add("website: empty string is not a valid URL");
            if (req.website != null && !req.website.isBlank()
                    && !req.website.startsWith("http"))
                errors.add("website: must start with http:// or https://");

            return errors;
        }
    }

    // ── service that processes the request ────────────────────────────
    static class ProfileService {
        private final ProfileValidator validator = new ProfileValidator();

        // Returns serialised JSON-like patch document
        Map<String, Object> processUpdate(String userId, UpdateProfileRequest req) {
            System.out.println("[UPDATE] userId=" + userId);

            List<String> errors = validator.validate(req);
            if (!errors.isEmpty()) {
                System.out.println("  [VALIDATION FAILED] " + errors);
                return Map.of("error", errors);
            }

            // Build the SQL SET clause
            Map<String, Object> patch = new LinkedHashMap<>();
            req.displayName.ifPresent(n -> patch.put("display_name", n));  // present: update
            // displayName absent: do NOT include (partial update, not null out)

            if (req.bio == null) patch.put("bio", null);                   // null: set to SQL NULL
            else                  patch.put("bio", req.bio);               // "" or value: set to that

            if (req.website == null) patch.put("website", null);           // null: set to SQL NULL
            else                     patch.put("website", req.website);

            System.out.println("  [SQL PATCH] " + patchToSql("user_profiles", userId, patch));
            return patch;
        }

        private String patchToSql(String table, String id, Map<String, Object> patch) {
            if (patch.isEmpty()) return "(no changes)";
            String sets = patch.entrySet().stream()
                .map(e -> e.getKey() + " = " + (e.getValue() == null ? "NULL" : "'" + e.getValue() + "'"))
                .collect(Collectors.joining(", "));
            return "UPDATE " + table + " SET " + sets + " WHERE id = '" + id + "'";
        }
    }

    public static void main(String[] args) {
        ProfileService svc = new ProfileService();

        System.out.println("=== Request 1: partial update (displayName not sent) ===");
        svc.processUpdate("u001", new UpdateProfileRequest(
            Optional.empty(),                     // displayName: absent — don't touch
            "Updated bio text",                   // bio: non-empty string
            "https://alice.dev"                   // website: valid
        ));

        System.out.println("\n=== Request 2: clear bio and website ===");
        svc.processUpdate("u002", new UpdateProfileRequest(
            Optional.of("Bob Smith"),             // displayName: present — update
            null,                                 // bio: null → set to SQL NULL (clear)
            null                                  // website: null → set to SQL NULL (clear)
        ));

        System.out.println("\n=== Request 3: validation failures ===");
        svc.processUpdate("u003", new UpdateProfileRequest(
            Optional.of(""),                      // displayName: blank → validation error
            "",                                   // bio: empty string → validation error
            ""                                    // website: empty → validation error
        ));
    }
}
```

How to run: `java NullEmptyDemo3.java`

Request 1: `displayName=absent` → not included in the SQL patch (no column touched). Request 2: `bio=null` and `website=null` → SQL `SET bio = NULL, website = NULL` (clear them). Request 3: empty strings fail validation because `""` ≠ `null` ≠ absent — each has different contract semantics. The service produces different SQL for null vs empty vs absent in every case.

## 6. Walkthrough

**Request 2 — `processUpdate("u002", ...)` step by step:**

```
Input:
  displayName = Optional.of("Bob Smith")
  bio         = null
  website     = null

validator.validate(req):
  req.displayName.ifPresent("Bob Smith"):
    "Bob Smith".isBlank()     → false
    "Bob Smith".length() = 9  ≤ 50 ✓
  "".equals(req.bio)          → false (bio is null, not "")
  "".equals(req.website)      → false (website is null)
  req.website != null         → false → skip URL check
  → errors = []  (validation passes)

processUpdate builds patch:
  req.displayName.ifPresent → present → patch.put("display_name", "Bob Smith")
  req.bio == null           → patch.put("bio", null)
  req.website == null       → patch.put("website", null)

patchToSql(patch):
  "display_name = 'Bob Smith', bio = NULL, website = NULL"

SQL output:
  UPDATE user_profiles
  SET display_name = 'Bob Smith', bio = NULL, website = NULL
  WHERE id = 'u002'
```

State change: `display_name` is updated to `"Bob Smith"`; `bio` and `website` columns are set to SQL `NULL`. An empty string `""` would have set them to an empty-string column value — entirely different SQL semantics.

## 7. Gotchas & takeaways

> **`<value></value>` and `<value/>` both inject the empty `String ""`, not `null`.** Developers often assume an empty XML element means "no value" — in Spring XML it explicitly injects `""`. Use `<null/>` if you want a null reference.

> **`@Value("${key:}")` injects `""` when the key is absent; `@Value("${key:#{null}}")` injects `null`.** The colon-default syntax always produces a string, so the `#{null}` SpEL expression is required for a null default.

- `@NotNull` passes for `""` (empty string is not null). `@NotBlank` catches both null and blank. Use `@NotBlank` when "not empty" is the real constraint.
- In SQL, `WHERE col = ''` and `WHERE col IS NULL` are not interchangeable — they target different rows. Spring's `<null/>` produces SQL `NULL`; `<value></value>` produces SQL `''`.
- `Optional<String>` is a better model for "field may not be present in the request" than using `null` — it makes the three-state distinction (absent / null / value) explicit in the type.
- Primitive fields (`int`, `boolean`) cannot be null in Java — Spring will throw a `TypeMismatchException` if you try to inject `<null/>` into an `int` field. Use the wrapper type (`Integer`, `Boolean`) if null must be possible.
