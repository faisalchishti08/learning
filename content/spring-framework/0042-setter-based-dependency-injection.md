---
card: spring-framework
gi: 42
slug: setter-based-dependency-injection
title: Setter-based dependency injection
---

## 1. What it is

**Setter-based dependency injection** supplies a bean's collaborators by calling setter methods (or any public method) after the bean has been created with its no-arg (or minimal) constructor.

```java
@Component
public class NotificationService {

    private EmailSender emailSender;    // not final — set after construction
    private SmsSender   smsSender;      // optional — may remain null

    @Autowired
    public void setEmailSender(EmailSender emailSender) {
        this.emailSender = emailSender;
    }

    @Autowired(required = false)
    public void setSmsSender(SmsSender smsSender) {
        this.smsSender = smsSender;
    }
}
```

In XML: `<property name="emailSender" ref="emailSenderBean"/>`. In Java config, the `@Bean` method sets properties directly after calling the constructor.

In one sentence: **Setter-based DI injects dependencies after object creation by calling setter methods, enabling optional dependencies, re-injection at runtime, and wiring of classes whose constructors cannot be changed.**

## 2. Why & when

Use setter injection when:

- **The dependency is optional.** `@Autowired(required=false)` on a setter means the bean still works if the collaborator is absent.
- **The bean needs to be re-configured at runtime.** A setter can be called again to swap out a collaborator — something constructor injection does not allow.
- **You cannot change the constructor.** Third-party classes or legacy code with a fixed no-arg constructor are wired via setters.
- **Circular dependencies.** If A needs B and B needs A, at least one must use setter injection — the container creates A (incomplete), creates B (injecting the incomplete A), then sets B on A via a setter.

Prefer constructor injection for mandatory dependencies. Setter injection is the right tool for optional or replaceable collaborators.

## 3. Core concept

```
Setter DI instantiation sequence:

  1. Container calls no-arg constructor: new NotificationService()
     → bean exists, emailSender = null, smsSender = null

  2. Container calls setter for each @Autowired property:
     bean.setEmailSender(ctx.getBean(EmailSender.class))
     bean.setSmsSender(ctx.getBean(SmsSender.class))  ← skipped if required=false & no bean

  3. @PostConstruct runs (if present)
  4. Bean ready to use

Vs. constructor DI:
  Constructor DI:  new Bean(dep1, dep2) — one atomic step
  Setter DI:       new Bean() → setDep1(d1) → setDep2(d2) — three steps
```

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Setter DI: constructor called first (bean partially initialized), then setters called to inject dependencies">
  <defs>
    <marker id="a42" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b42" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Steps -->
  <rect x="10" y="20" width="155" height="50" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="88" y="43" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">1. new NotificationService()</text>
  <text x="88" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">empty bean — all fields null</text>

  <rect x="10" y="90" width="155" height="50" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="88" y="113" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">2. setEmailSender(bean)</text>
  <text x="88" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Autowired required=true</text>

  <rect x="10" y="158" width="155" height="40" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="88" y="178" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">3. setSmsSender(bean) — optional</text>

  <line x1="88" y1="70" x2="88" y2="87" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a42)"/>
  <line x1="88" y1="140" x2="88" y2="155" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a42)"/>

  <!-- Dependency beans -->
  <rect x="220" y="90" width="160" height="42" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="300" y="116" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">EmailSender bean</text>

  <rect x="220" y="155" width="160" height="42" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="300" y="181" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">SmsSender bean (opt.)</text>

  <line x1="218" y1="111" x2="168" y2="116" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a42)"/>
  <line x1="218" y1="176" x2="168" y2="178" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b42)"/>

  <!-- Final bean -->
  <rect x="460" y="75" width="200" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="560" y="98" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">NotificationService</text>
  <text x="560" y="116" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">emailSender = EmailSender ✓</text>
  <text x="560" y="132" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">smsSender   = SmsSender? (opt)</text>
  <text x="560" y="148" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ready after @PostConstruct</text>

  <line x1="175" y1="98" x2="457" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a42)"/>
</svg>

The bean is created first with an empty constructor, then each setter is called. The bean is technically usable after step 1, but its collaborators are `null` until all setters have run.

## 5. Runnable example

Scenario: a `ReportService` that requires a `DataLoader` (mandatory) but optionally uses a `PdfRenderer` (optional). Setter injection wires both.

### Level 1 — Basic

Mandatory setter + optional setter.

```java
// SetterDIDemo.java — run with: java SetterDIDemo.java
import java.util.*;

public class SetterDIDemo {

    interface DataLoader {
        List<Map<String, Object>> load(String query);
    }

    static class DatabaseLoader implements DataLoader {
        DatabaseLoader() { System.out.println("  [BEAN] DatabaseLoader created"); }
        @Override
        public List<Map<String, Object>> load(String query) {
            System.out.println("  [DB] executing: " + query);
            return List.of(
                Map.of("id", 1, "region", "APAC", "sales", 430_000),
                Map.of("id", 2, "region", "EMEA", "sales", 610_000)
            );
        }
    }

    interface PdfRenderer {
        byte[] render(String title, List<Map<String, Object>> rows);
    }

    static class ItextPdfRenderer implements PdfRenderer {
        ItextPdfRenderer() { System.out.println("  [BEAN] ItextPdfRenderer created"); }
        @Override public byte[] render(String title, List<Map<String, Object>> rows) {
            System.out.println("  [PDF] rendering: " + title + " rows=" + rows.size());
            return ("PDF:" + title).getBytes();
        }
    }

    static class ReportService {
        private DataLoader  dataLoader;    // mandatory
        private PdfRenderer pdfRenderer;  // optional — null if not available

        ReportService() {
            System.out.println("  [BEAN] ReportService() — no-arg constructor");
        }

        // @Autowired setter — mandatory
        void setDataLoader(DataLoader dataLoader) {
            System.out.println("  [SETTER] setDataLoader → " + dataLoader.getClass().getSimpleName());
            this.dataLoader = dataLoader;
        }

        // @Autowired(required=false) setter — optional
        void setPdfRenderer(PdfRenderer pdfRenderer) {
            System.out.println("  [SETTER] setPdfRenderer → " + pdfRenderer.getClass().getSimpleName());
            this.pdfRenderer = pdfRenderer;
        }

        // @PostConstruct equivalent
        void init() {
            if (dataLoader == null) throw new IllegalStateException("dataLoader is required");
            System.out.println("  [INIT] ReportService ready. pdfRenderer present: " + (pdfRenderer != null));
        }

        String generateReport(String query) {
            var data = dataLoader.load(query);
            if (pdfRenderer != null) {
                byte[] pdf = pdfRenderer.render("Sales Report", data);
                return "PDF generated: " + new String(pdf) + " (" + data.size() + " rows)";
            }
            return "Text report: " + data.size() + " rows loaded";
        }
    }

    static class Ctx {
        private final Map<String, Object> beans = new LinkedHashMap<>();

        void register(String name, Object bean) { beans.put(name, bean); }

        // Wire setter DI: for each setter annotated-style, call it with the right bean
        ReportService wireReportService(boolean withPdf) throws Exception {
            ReportService svc = new ReportService();

            // Mandatory setter
            DataLoader loader = (DataLoader) beans.values().stream()
                .filter(b -> b instanceof DataLoader).findFirst()
                .orElseThrow(() -> new RuntimeException("No DataLoader bean"));
            svc.setDataLoader(loader);

            // Optional setter
            if (withPdf) {
                beans.values().stream()
                    .filter(b -> b instanceof PdfRenderer)
                    .map(b -> (PdfRenderer) b)
                    .findFirst()
                    .ifPresent(svc::setPdfRenderer);
            }

            svc.init();
            beans.put("reportService", svc);
            return svc;
        }
    }

    public static void main(String[] args) throws Exception {
        Ctx ctx = new Ctx();
        System.out.println("=== Container startup ===");
        ctx.register("dataLoader",   new DatabaseLoader());
        ctx.register("pdfRenderer",  new ItextPdfRenderer());
        ReportService svc = ctx.wireReportService(true);

        System.out.println("\n=== Application running (with PDF) ===");
        System.out.println("  " + svc.generateReport("SELECT * FROM sales"));

        System.out.println("\n=== Without PDF renderer ===");
        Ctx ctx2 = new Ctx();
        ctx2.register("dataLoader", new DatabaseLoader());
        ReportService svc2 = ctx2.wireReportService(false);  // no pdfRenderer
        System.out.println("  " + svc2.generateReport("SELECT * FROM sales"));
    }
}
```

How to run: `java SetterDIDemo.java`

`setDataLoader` is called unconditionally (mandatory). `setPdfRenderer` is only called when the bean exists (optional). With `required=false` semantics, `svc2` has `pdfRenderer=null` and gracefully falls back to text output.

### Level 2 — Intermediate

Re-injection via setter: swap out a collaborator at runtime.

```java
// SetterDIDemo2.java — run with: java SetterDIDemo2.java
import java.util.*;

public class SetterDIDemo2 {

    interface PaymentProcessor {
        String process(String orderId, double amount);
        String providerName();
    }

    static class StripeProcessor implements PaymentProcessor {
        StripeProcessor() { System.out.println("  [BEAN] StripeProcessor created"); }
        @Override public String process(String id, double amt) {
            return "STRIPE:" + id + " charged $" + String.format("%.2f", amt);
        }
        @Override public String providerName() { return "Stripe"; }
    }

    static class BraintreeProcessor implements PaymentProcessor {
        BraintreeProcessor() { System.out.println("  [BEAN] BraintreeProcessor created"); }
        @Override public String process(String id, double amt) {
            return "BRAINTREE:" + id + " charged $" + String.format("%.2f", amt);
        }
        @Override public String providerName() { return "Braintree"; }
    }

    static class CheckoutService {
        private PaymentProcessor processor;

        CheckoutService() { System.out.println("  [BEAN] CheckoutService() created"); }

        void setPaymentProcessor(PaymentProcessor p) {
            System.out.println("  [SETTER] setPaymentProcessor → " + p.providerName());
            this.processor = p;
        }

        String checkout(String orderId, double total) {
            if (processor == null) throw new IllegalStateException("No payment processor injected");
            return processor.process(orderId, total);
        }

        String currentProvider() { return processor == null ? "none" : processor.providerName(); }
    }

    public static void main(String[] args) {
        System.out.println("=== Initial wiring ===");
        CheckoutService svc = new CheckoutService();
        svc.setPaymentProcessor(new StripeProcessor());
        System.out.println("  provider: " + svc.currentProvider());
        System.out.println("  " + svc.checkout("ORD-001", 199.99));

        System.out.println("\n=== Runtime re-injection (migration to Braintree) ===");
        svc.setPaymentProcessor(new BraintreeProcessor());
        System.out.println("  provider: " + svc.currentProvider());
        System.out.println("  " + svc.checkout("ORD-002", 59.90));

        System.out.println("\n=== Contrast with constructor DI ===");
        System.out.println("  Constructor DI: final PaymentProcessor — cannot be changed after creation");
        System.out.println("  Setter DI:      non-final field — swap processor by calling setter again");
    }
}
```

How to run: `java SetterDIDemo2.java`

Setter injection allows `processor` to be swapped at runtime. First `StripeProcessor` is injected, then `BraintreeProcessor` is re-injected via the same setter. This is impossible with constructor injection where the field is `final`.

### Level 3 — Advanced

Setter DI breaking a circular dependency: A injects B by setter so B can be created with A already in the container.

```java
// SetterDIDemo3.java — run with: java SetterDIDemo3.java
import java.util.*;

public class SetterDIDemo3 {

    // Circular: AuthService uses SessionStore for session lookups;
    // SessionStore uses AuthService to validate tokens before storing.
    // Solution: SessionStore injects AuthService via setter (after SessionStore is created).

    interface TokenValidator {
        boolean validate(String token);
    }

    static class AuthService implements TokenValidator {
        private SessionStore sessionStore;   // setter — resolves circular

        AuthService() { System.out.println("  [BEAN] AuthService() created (no-arg)"); }

        // Setter called after SessionStore is created
        void setSessionStore(SessionStore sessionStore) {
            System.out.println("  [SETTER] AuthService.setSessionStore → " + sessionStore.getClass().getSimpleName());
            this.sessionStore = sessionStore;
        }

        @Override
        public boolean validate(String token) {
            System.out.println("  [AUTH] validating token: " + token.substring(0, 8) + "...");
            return token.startsWith("valid-");
        }

        String login(String user, String password) {
            if (!password.equals("secret")) return "LOGIN FAILED";
            String token = "valid-" + UUID.randomUUID().toString().replace("-", "").substring(0, 16);
            sessionStore.store(user, token);
            return token;
        }

        String whoAmI(String token) {
            return sessionStore.lookup(token).orElse("unknown");
        }
    }

    static class SessionStore {
        private TokenValidator validator;    // setter — resolves circular
        private final Map<String, String> sessions    = new HashMap<>();   // token → user
        private final Map<String, String> userTokens  = new HashMap<>();   // user → token

        SessionStore() { System.out.println("  [BEAN] SessionStore() created (no-arg)"); }

        // Setter: injected after AuthService is created
        void setTokenValidator(TokenValidator validator) {
            System.out.println("  [SETTER] SessionStore.setTokenValidator → " + validator.getClass().getSimpleName());
            this.validator = validator;
        }

        void store(String user, String token) {
            sessions.put(token, user);
            userTokens.put(user, token);
            System.out.println("  [SESSION] stored session for " + user);
        }

        Optional<String> lookup(String token) {
            if (validator != null && !validator.validate(token)) {
                System.out.println("  [SESSION] invalid token — not in store");
                return Optional.empty();
            }
            return Optional.ofNullable(sessions.get(token));
        }

        boolean hasSession(String user) { return userTokens.containsKey(user); }
    }

    public static void main(String[] args) {
        System.out.println("=== Container resolving circular dependency via setter DI ===");

        // Step 1: Create AuthService (no deps yet)
        AuthService auth = new AuthService();

        // Step 2: Create SessionStore (no deps yet)
        SessionStore sessions = new SessionStore();

        // Step 3: Inject via setters — circular resolved
        auth.setSessionStore(sessions);
        sessions.setTokenValidator(auth);

        System.out.println("\n=== Application running ===");
        String tokenAlice = auth.login("alice", "secret");
        System.out.println("  alice token: " + tokenAlice.substring(0, 14) + "...");

        String user = auth.whoAmI(tokenAlice);
        System.out.println("  whoAmI: " + user);

        System.out.println("  alice has session: " + sessions.hasSession("alice"));
        System.out.println("  bob has session: "   + sessions.hasSession("bob"));

        System.out.println("\n=== Failed login ===");
        String failToken = auth.login("bob", "wrong");
        System.out.println("  bob login result: " + failToken);

        System.out.println("\n=== Why this works but constructor DI cannot ===");
        System.out.println("  AuthService(SessionStore) requires SessionStore to exist first");
        System.out.println("  SessionStore(TokenValidator) requires AuthService to exist first");
        System.out.println("  → Deadlock. Setter DI creates both empty, then cross-injects.");
    }
}
```

How to run: `java SetterDIDemo3.java`

`AuthService` and `SessionStore` have a circular dependency. The container creates both with no-arg constructors (step 1 and 2), then calls `setSessionStore` and `setTokenValidator` to cross-wire them (step 3). Spring does exactly this internally for singleton beans: creates `A` first, puts the incomplete `A` in an "early singleton" cache, creates `B` injecting the early `A`, then calls `A.setB(b)`.

## 6. Walkthrough

**Level 3 — circular resolution order:**

```
Step 1: new AuthService()
  → auth.sessionStore = null

Step 2: new SessionStore()
  → sessions.validator = null

Step 3: auth.setSessionStore(sessions)
  → auth.sessionStore = SessionStore ✓

Step 4: sessions.setTokenValidator(auth)
  → sessions.validator = AuthService ✓

auth.login("alice", "secret"):
  → validates password
  → token = "valid-..." generated
  → sessions.store("alice", token)
      → sessions[token] = "alice"
      → userTokens["alice"] = token

auth.whoAmI(token):
  → sessions.lookup(token)
      → sessions.validator.validate(token) = true (starts with "valid-")
      → return sessions["valid-..."] = "alice"
```

## 7. Gotchas & takeaways

> **Setter-injected fields can be null if the setter is never called.** Unlike constructor injection, a missing `@Autowired` setter does not fail at startup when `required=false`. Always call `Objects.requireNonNull()` in `@PostConstruct` for fields that are truly mandatory.

> **Thread-safety.** Setter injection modifies fields after construction. If the bean is used in multiple threads during startup (rare but possible), a volatile field or synchronized setter may be needed.

- Constructor injection guarantees the object is fully initialized at the end of the constructor. Setter injection has a window where the object exists but is partially wired.
- Setter injection is the standard solution for circular dependencies between singleton beans.
- Spring's XML `<property name="X" ref="Y"/>` is equivalent to calling `setX(Y)`. The property name `X` maps to a setter named `setX`.
- `@Autowired` on a setter is functionally equivalent to `@Autowired` on the field — both inject the same dependency — but the setter form allows the `required=false` attribute to suppress injection failures.
