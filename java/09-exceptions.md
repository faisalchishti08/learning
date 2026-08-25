# Java Exceptions

Java's exception mechanism separates normal code flow from error handling. An exception is an event that disrupts normal program execution. The JVM creates an exception object, which travels up the call stack until something catches it or the program terminates.

---

## 1. Exception Hierarchy

Every throwable thing in Java extends `Throwable`. Two direct children: `Error` and `Exception`.

```
Throwable
├── Error  (JVM-level problems — do NOT catch these)
│   ├── OutOfMemoryError        (heap exhausted)
│   ├── StackOverflowError      (infinite recursion)
│   ├── AssertionError          (assert statement failed)
│   ├── VirtualMachineError
│   └── LinkageError
│
└── Exception
    ├── RuntimeException  (UNCHECKED — compiler doesn't force you to handle)
    │   ├── NullPointerException
    │   ├── ArrayIndexOutOfBoundsException
    │   ├── ClassCastException
    │   ├── IllegalArgumentException
    │   ├── IllegalStateException
    │   ├── NumberFormatException
    │   ├── UnsupportedOperationException
    │   └── ConcurrentModificationException
    │
    └── (everything else = CHECKED — compiler forces handling)
        ├── IOException
        │   └── FileNotFoundException
        ├── SQLException
        ├── ClassNotFoundException
        ├── InterruptedException
        └── ParseException
```

**Checked exceptions** — declared in `throws` clause or caught. Compiler refuses to compile if you ignore them. Designed for conditions that are outside the programmer's control but might be recoverable (file missing, network down, DB timeout).

**Unchecked exceptions** — extend `RuntimeException` or `Error`. Compiler is silent. These signal programming bugs (null dereference, bad array index) — you should fix the code, not catch the exception.

**Errors** — JVM-level catastrophes. Catching `OutOfMemoryError` is almost never correct: the JVM state is unreliable after heap exhaustion.

```java
// Full hierarchy in code form
public class HierarchyDemo {
    public static void main(String[] args) {
        // All of these are true:
        System.out.println(new NullPointerException()      instanceof RuntimeException); // true
        System.out.println(new NullPointerException()      instanceof Exception);        // true
        System.out.println(new NullPointerException()      instanceof Throwable);        // true
        System.out.println(new IOException()               instanceof Exception);        // true
        System.out.println(new IOException()               instanceof RuntimeException); // false
        System.out.println(new OutOfMemoryError()          instanceof Error);            // true
        System.out.println(new OutOfMemoryError()          instanceof RuntimeException); // false
    }
}
```

**What this does:** confirms inheritance relationships. `NullPointerException` is-a `RuntimeException` is-a `Exception` is-a `Throwable`. `IOException` is-a `Exception` but NOT a `RuntimeException`.

---

## 2. Checked vs Unchecked

### Checked Exceptions

The compiler enforces a "handle or declare" rule. If method `A` calls method `B` which throws a checked exception, then `A` must either:
- catch it with `try/catch`, or
- declare `throws CheckedException` in its own signature (pushing the obligation to A's callers)

**When to create checked exceptions:** recoverable conditions caused by external factors. Caller can meaningfully handle them.

```java
// Checked: compiler forces the caller to deal with it
import java.io.*;

public class CheckedDemo {

    // readFile MUST declare throws IOException because FileReader/BufferedReader throw it
    public static String readFile(String path) throws IOException {
        BufferedReader reader = new BufferedReader(new FileReader(path));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            sb.append(line).append("\n");
        }
        reader.close();
        return sb.toString();
    }

    public static void main(String[] args) {
        // Option 1: catch here
        try {
            String content = readFile("config.txt");
            System.out.println(content);
        } catch (IOException e) {
            System.out.println("File not found or unreadable: " + e.getMessage());
            // fallback logic here — we can recover
        }

        // Option 2 would be: declare throws IOException on main — pushes to JVM
    }
}
```

**What this does:** `readFile` is forced to declare `throws IOException`. The caller (`main`) is forced to catch or re-declare. This compile-time obligation ensures developers think about error handling for recoverable conditions.

### Unchecked Exceptions

No compiler obligation. These should indicate bugs that must be fixed, not handled.

```java
public class UncheckedDemo {

    // No throws declaration needed — RuntimeException is unchecked
    public static int divide(int a, int b) {
        if (b == 0) {
            throw new IllegalArgumentException("Divisor cannot be zero");
        }
        return a / b;
    }

    public static String getLength(String s) {
        // NullPointerException if s is null — fix the caller, don't catch NPE
        return "Length: " + s.length();
    }

    public static void main(String[] args) {
        System.out.println(divide(10, 2));   // 5
        System.out.println(divide(10, 0));   // throws IllegalArgumentException — fix the caller
    }
}
```

**What this does:** `IllegalArgumentException` is unchecked so no `throws` needed. The contract is enforced at design time, not compile time. `getLength` shows a common NPE scenario — the fix is to validate the argument, not catch NPE inside the method.

### Custom Exception Decision

```java
// Checked custom: recoverable, caller should handle
class InsufficientFundsException extends Exception {
    public InsufficientFundsException(String message) { super(message); }
}

// Unchecked custom: programming error / invariant violation
class InvalidAccountStateException extends RuntimeException {
    public InvalidAccountStateException(String message) { super(message); }
}

class BankAccount {
    private double balance;

    public BankAccount(double balance) { this.balance = balance; }

    // Caller can recover: show error to user, ask for smaller amount
    public void withdraw(double amount) throws InsufficientFundsException {
        if (amount > balance) {
            throw new InsufficientFundsException(
                "Requested: " + amount + ", Available: " + balance);
        }
        balance -= amount;
    }

    // Programming bug: account should never be in this state
    public void close() {
        if (balance != 0) {
            throw new InvalidAccountStateException(
                "Cannot close account with non-zero balance: " + balance);
        }
    }
}
```

**What this does:** `InsufficientFundsException` is checked because the caller (UI layer, service layer) can meaningfully handle it — show a message, suggest a lower amount. `InvalidAccountStateException` is unchecked because reaching `close()` with a non-zero balance means there is a bug in the calling code.

> ⚠️ **Pitfall:** Overusing checked exceptions. Every checked exception in a public API is a burden on every caller. Many modern frameworks (Spring, Hibernate) wrap checked exceptions in unchecked ones to avoid forced handling everywhere. Use checked only when the caller genuinely can recover.

---

## 3. try / catch / finally

### Structure

```
try block
    │
    ├── no exception ──────────────────────────────► continue after finally
    │
    └── exception thrown
          │
          ├── catch (MostSpecificException e) ──► handle, then finally
          ├── catch (MiddleException e)        ──► handle, then finally
          └── catch (BroadException e)         ──► handle, then finally
                                                         │
                                                    finally block
                                                    (ALWAYS runs)
```

**Multiple catch blocks must go most-specific to least-specific.** If a parent class appears before a child class in the catch chain, the child catch is unreachable — the compiler flags this as a compile error.

**finally always runs:** even if there's a `return` inside try, even if an exception is thrown, even if a catch block throws. The only exceptions: `System.exit()` and a JVM crash.

```java
// Example 1: basic flow
public class TryCatchDemo {

    static int riskyOperation(int x) {
        if (x < 0) throw new IllegalArgumentException("Negative: " + x);
        if (x == 0) throw new ArithmeticException("Zero not allowed");
        return 100 / x;
    }

    public static void main(String[] args) {
        for (int x : new int[]{5, 0, -1}) {
            try {
                int result = riskyOperation(x);
                System.out.println("Result: " + result);
            } catch (ArithmeticException e) {
                System.out.println("Arithmetic: " + e.getMessage());
            } catch (IllegalArgumentException e) {
                System.out.println("Illegal arg: " + e.getMessage());
            } finally {
                System.out.println("Finally ran for x=" + x);
            }
        }
    }
}
```

**What this does:** iterates three inputs. For x=5 no exception, prints result then finally. For x=0 catches `ArithmeticException`, then finally. For x=-1 catches `IllegalArgumentException`, then finally. Notice `finally` prints after every iteration regardless of the path.

**Dry run — tracing execution paths:**

| x  | try line executed        | exception?               | catch block hit          | finally? | output                                      |
|----|--------------------------|--------------------------|--------------------------|----------|---------------------------------------------|
| 5  | `100/5 = 20`             | none                     | none                     | yes      | "Result: 20", "Finally ran for x=5"         |
| 0  | `throw ArithmeticEx`     | ArithmeticException      | ArithmeticException      | yes      | "Arithmetic: Zero not allowed", "Finally…0" |
| -1 | `throw IllegalArgEx`     | IllegalArgumentException | IllegalArgumentException | yes      | "Illegal arg: Negative: -1", "Finally…-1"  |

```java
// Example 2: wrong order causes compile error
public class WrongOrderDemo {
    public static void main(String[] args) {
        try {
            throw new FileNotFoundException("file.txt");
        } catch (IOException e) {           // parent first
            System.out.println("IOException");
        // } catch (FileNotFoundException e) { // COMPILE ERROR: already caught by IOException above
        //     System.out.println("FileNotFoundException");
        // }
        }
    }
}
```

**What this does:** demonstrates that `FileNotFoundException extends IOException`. If `IOException` catch appears first it swallows `FileNotFoundException` too, making the specific handler unreachable. Compiler rejects this.

```java
// Example 3: finally with return — finally wins
public class FinallyReturnDemo {

    static String test() {
        try {
            System.out.println("try block");
            return "from try";      // <-- this return is prepared
        } finally {
            System.out.println("finally block");
            // return "from finally"; // if uncommented, OVERRIDES the try return
        }
    }

    public static void main(String[] args) {
        System.out.println(test());
    }
    // Output:
    // try block
    // finally block
    // from try
}
```

**What this does:** the `return "from try"` value is prepared and saved, then `finally` runs. Because the finally block has no `return` statement, the saved return value from try is used. If finally had its own `return`, it would override the try's return — the try return is silently discarded.

> ⚠️ **Pitfall:** Never put a `return` in `finally`. It silently swallows the try/catch return value and can also suppress exceptions. This is a well-known Java bug pattern.

```java
// Example 4: finally runs even when exception is uncaught
public class FinallyUncaughtDemo {

    static void doWork() {
        try {
            System.out.println("working...");
            throw new RuntimeException("oops");
        } finally {
            System.out.println("cleanup in finally");  // still runs
        }
    }

    public static void main(String[] args) {
        try {
            doWork();
        } catch (RuntimeException e) {
            System.out.println("caught in main: " + e.getMessage());
        }
    }
    // Output:
    // working...
    // cleanup in finally
    // caught in main: oops
}
```

**What this does:** `doWork` has no catch block but has `finally`. When `RuntimeException` is thrown, `finally` still runs before the exception propagates up to `main`'s catch.

---

## 4. try-with-resources [Java 7+]

### Problem try-with-resources Solves

Before Java 7, closing resources (files, connections, streams) required verbose finally blocks. If both the try body and the finally block threw exceptions, the body exception was silently lost.

```
Resource acquisition order:  A, B, C
Close order (reverse):        C, B, A

         open A ──► open B ──► open C
                                  │
                          body executes
                                  │
                          close C (reverse order)
                          close B
                          close A
```

### Old Style vs New Style

```java
import java.io.*;

// OLD STYLE — before Java 7
public class OldResourceHandling {

    public static void copyFile(String src, String dst) throws IOException {
        BufferedReader reader = null;
        BufferedWriter writer = null;
        try {
            reader = new BufferedReader(new FileReader(src));
            writer = new BufferedWriter(new FileWriter(dst));
            String line;
            while ((line = reader.readLine()) != null) {
                writer.write(line);
                writer.newLine();
            }
        } finally {
            // Must manually null-check AND handle close() throwing
            if (reader != null) {
                try { reader.close(); } catch (IOException e) { /* lost! */ }
            }
            if (writer != null) {
                try { writer.close(); } catch (IOException e) { /* lost! */ }
            }
        }
    }
}
```

**What this does:** the old pattern is error-prone. Two manual null checks. Nested try/catch inside finally to prevent close exceptions from propagating. If reader.close() throws, writer.close() never runs. The close exception silently replaces any body exception.

```java
import java.io.*;

// NEW STYLE — Java 7+ try-with-resources
public class NewResourceHandling {

    public static void copyFile(String src, String dst) throws IOException {
        // Both resources declared in try(...); closed automatically in reverse order
        try (BufferedReader reader = new BufferedReader(new FileReader(src));
             BufferedWriter writer = new BufferedWriter(new FileWriter(dst))) {

            String line;
            while ((line = reader.readLine()) != null) {
                writer.write(line);
                writer.newLine();
            }
        }
        // writer.close() called first, then reader.close()
        // close() called even if exception thrown in body
    }
}
```

**What this does:** `BufferedReader` and `BufferedWriter` both implement `AutoCloseable`. The compiler generates the finally block automatically. Close order is reverse of declaration: `writer` closes first, then `reader`. If body throws, the close still happens.

### AutoCloseable Interface

```java
// Implementing AutoCloseable for custom resources
public class DatabaseConnection implements AutoCloseable {

    private final String url;
    private boolean open;

    public DatabaseConnection(String url) {
        this.url = url;
        this.open = true;
        System.out.println("Connection opened: " + url);
    }

    public void query(String sql) {
        if (!open) throw new IllegalStateException("Connection is closed");
        System.out.println("Executing: " + sql);
    }

    @Override
    public void close() {
        if (open) {
            open = false;
            System.out.println("Connection closed: " + url);
        }
    }

    public static void main(String[] args) {
        try (DatabaseConnection conn = new DatabaseConnection("jdbc://localhost/db")) {
            conn.query("SELECT * FROM users");
            conn.query("SELECT * FROM orders");
        }
        // close() automatically called here
    }
    // Output:
    // Connection opened: jdbc://localhost/db
    // Executing: SELECT * FROM users
    // Executing: SELECT * FROM orders
    // Connection closed: jdbc://localhost/db
}
```

**What this does:** custom class implements `AutoCloseable` with a `close()` method. When used in try-with-resources, `close()` is guaranteed to run after the try body regardless of success or exception.

### Suppressed Exceptions [Java 7+]

When both the body and `close()` throw, the body exception is the **primary** exception. The close exception is **suppressed** — attached to the primary via `addSuppressed()`. Both are preserved; nothing is lost.

```java
public class SuppressedExceptionDemo {

    static class BrokenResource implements AutoCloseable {
        private final String name;

        BrokenResource(String name) {
            System.out.println("Opening " + name);
        }

        void doWork() throws Exception {
            throw new Exception("Body exception from work");
        }

        @Override
        public void close() throws Exception {
            throw new Exception("Close exception from " + name);
        }
    }

    public static void main(String[] args) {
        try (BrokenResource r = new BrokenResource("R1")) {
            r.doWork();  // throws body exception
        } catch (Exception e) {
            System.out.println("Primary: " + e.getMessage());
            for (Throwable suppressed : e.getSuppressed()) {
                System.out.println("Suppressed: " + suppressed.getMessage());
            }
        }
    }
    // Output:
    // Opening R1
    // Primary: Body exception from work
    // Suppressed: Close exception from R1
}
```

**What this does:** `doWork()` throws, then close() also throws. The JVM attaches the close exception as a suppressed exception on the body exception. `e.getSuppressed()` returns an array of all suppressed exceptions. Nothing is silently lost.

**Dry run — two-resource suppression:**

| Step | Action                  | Exception state                                    |
|------|-------------------------|----------------------------------------------------|
| 1    | open R1                 | none                                               |
| 2    | open R2                 | none                                               |
| 3    | body throws E_body      | primary = E_body                                   |
| 4    | close R2 throws E_r2    | E_r2 suppressed on E_body                         |
| 5    | close R1 throws E_r1    | E_r1 also suppressed on E_body                    |
| 6    | catch receives E_body   | E_body.getSuppressed() = [E_r2, E_r1]             |

> ⚠️ **Pitfall:** If you declare a resource outside try-with-resources (as a variable before the try), it is NOT automatically closed. Only resources declared inside `try(...)` get the automatic close treatment.

---

## 5. Multi-catch [Java 7+]

Before Java 7, catching two unrelated exception types required duplicated catch blocks or catching a common parent (losing specificity). Multi-catch uses `|` to handle multiple types in one block.

```java
import java.io.*;
import java.sql.*;

public class MultiCatchDemo {

    // Before Java 7 — duplicated handling
    static void oldWay(String input) {
        try {
            processInput(input);
        } catch (IOException e) {
            logAndAlert(e);   // same code
        } catch (SQLException e) {
            logAndAlert(e);   // duplicated
        }
    }

    // Java 7+ multi-catch
    static void newWay(String input) {
        try {
            processInput(input);
        } catch (IOException | SQLException e) {
            // e is effectively final here — cannot reassign
            logAndAlert(e);
        }
    }

    static void processInput(String s) throws IOException, SQLException {
        if (s == null)  throw new IOException("null input");
        if (s.isEmpty()) throw new SQLException("empty query");
    }

    static void logAndAlert(Exception e) {
        System.out.println("Logged: " + e.getMessage());
    }
}
```

**What this does:** `IOException | SQLException` handles both types in one block. The variable `e` gets the type `IOException | SQLException` — effectively `Exception`. The `|` reads as "or", not "and".

```java
// Multi-catch with different exception types showing effectively-final rule
public class MultiCatchFinalDemo {

    public static void main(String[] args) {
        try {
            String s = null;
            s.length();  // NPE
        } catch (NullPointerException | ArrayIndexOutOfBoundsException e) {
            System.out.println("Caught: " + e.getClass().getSimpleName());

            // e = new RuntimeException("x");  // COMPILE ERROR: e is effectively final
            // Cannot reassign e in a multi-catch block

            throw e;  // re-throwing is fine
        }
    }
}
```

**What this does:** demonstrates the effectively-final constraint. `e` cannot be reassigned inside the multi-catch block. Re-throwing `e` is allowed. This restriction exists because the compiler generates bytecode that handles both types through a single variable — reassigning would break type safety.

```java
// ILLEGAL: catching related exceptions in multi-catch
public class MultiCatchRelatedDemo {

    public static void main(String[] args) {
        try {
            throw new FileNotFoundException("oops");
        // } catch (IOException | FileNotFoundException e) {  // COMPILE ERROR
        //     // FileNotFoundException IS-A IOException — redundant, compiler rejects
        } catch (IOException e) {
            System.out.println("caught: " + e.getMessage());
        }
    }
}
```

**What this does:** `IOException | FileNotFoundException` is illegal because `FileNotFoundException extends IOException`. The `IOException` already covers `FileNotFoundException`. The compiler rejects this as redundant and confusing.

> ⚠️ **Pitfall:** Multi-catch variable `e` has the union type of all caught exceptions. Its type is inferred as their common parent. Call only methods available on the common parent (usually `Exception`).

---

## 6. Custom Exceptions

### Why Custom Exceptions

Standard exceptions (`IOException`, `IllegalArgumentException`) are generic. Custom exceptions convey domain-specific meaning, carry extra fields (error codes, context), and let callers catch precisely what they care about.

```java
// Basic custom checked exception
public class OrderNotFoundException extends Exception {

    private final long orderId;

    public OrderNotFoundException(long orderId) {
        super("Order not found: " + orderId);
        this.orderId = orderId;
    }

    public OrderNotFoundException(long orderId, Throwable cause) {
        super("Order not found: " + orderId, cause);
        this.orderId = orderId;
    }

    public long getOrderId() { return orderId; }
}

// Usage
class OrderService {
    public Order findOrder(long id) throws OrderNotFoundException {
        Order o = database.find(id);  // hypothetical
        if (o == null) {
            throw new OrderNotFoundException(id);
        }
        return o;
    }
}
```

**What this does:** `OrderNotFoundException` is a checked exception (extends `Exception`) because the caller might want to show "order not found" in the UI. The `orderId` field gives callers structured access to context without parsing the message string.

```java
// Custom unchecked exception with error code
public class PaymentProcessingException extends RuntimeException {

    public enum ErrorCode { CARD_DECLINED, NETWORK_TIMEOUT, INVALID_CARD, FRAUD_DETECTED }

    private final ErrorCode errorCode;
    private final String transactionId;

    public PaymentProcessingException(ErrorCode code, String transactionId) {
        super("Payment failed [" + code + "] txn=" + transactionId);
        this.errorCode = code;
        this.transactionId = transactionId;
    }

    public PaymentProcessingException(ErrorCode code, String transactionId, Throwable cause) {
        super("Payment failed [" + code + "] txn=" + transactionId, cause);
        this.errorCode = code;
        this.transactionId = transactionId;
    }

    public ErrorCode getErrorCode()    { return errorCode; }
    public String getTransactionId()   { return transactionId; }
}

// Usage: caller can switch on error code
class PaymentController {
    void processPayment(PaymentRequest req) {
        try {
            paymentService.charge(req);
        } catch (PaymentProcessingException e) {
            switch (e.getErrorCode()) {
                case CARD_DECLINED:  showMessage("Card declined"); break;
                case NETWORK_TIMEOUT: retryLater(req);            break;
                case FRAUD_DETECTED: alertFraudTeam(req);         break;
                default:             showGenericError();
            }
        }
    }
}
```

**What this does:** the enum `ErrorCode` lets callers react to the specific failure reason without string parsing. The `transactionId` is a structured field for logging. The cause constructor (taking `Throwable`) enables exception chaining.

```java
// Exception hierarchy for a domain
public class AppException extends RuntimeException {
    public AppException(String message)             { super(message); }
    public AppException(String message, Throwable c){ super(message, c); }
}

public class ValidationException extends AppException {
    private final String field;
    public ValidationException(String field, String message) {
        super("Validation failed on '" + field + "': " + message);
        this.field = field;
    }
    public String getField() { return field; }
}

public class DatabaseException extends AppException {
    public DatabaseException(String message, Throwable cause) {
        super(message, cause);
    }
}
```

**What this does:** creates a domain exception hierarchy. Callers can catch `AppException` to handle all app errors, or catch `ValidationException` / `DatabaseException` specifically. This is how Spring organizes its `DataAccessException` hierarchy.

> ⚠️ **Pitfall:** Don't create a new exception class for every error condition. A small hierarchy with an enum for subtypes (like `PaymentProcessingException.ErrorCode`) is often cleaner than 20 exception classes.

---

## 7. Re-throwing and finally Interaction

### Re-throwing Patterns

Three patterns for re-throwing:

1. **Re-throw same exception** — same object propagates, original stack trace preserved
2. **Wrap with cause** — new higher-level exception with original as cause (exception chaining)
3. **Translate** — convert one exception type to another at layer boundary

```java
import java.sql.*;
import java.io.*;

public class RethrowDemo {

    // Pattern 1: re-throw same exception
    static void pattern1() throws IOException {
        try {
            readFile("data.txt");
        } catch (IOException e) {
            System.out.println("Logging: " + e.getMessage());
            throw e;   // same object, same stack trace
        }
    }

    // Pattern 2: wrap with cause (exception chaining)
    static void pattern2() {
        try {
            queryDatabase();
        } catch (SQLException e) {
            // Translate checked SQL exception to unchecked domain exception
            // Original SQL exception preserved as cause
            throw new RuntimeException("Failed to load user data", e);
        }
    }

    // Pattern 3: layer translation
    static void pattern3() throws IOException {
        try {
            queryDatabase();
        } catch (SQLException e) {
            throw new IOException("Database read failed: " + e.getMessage(), e);
        }
    }

    static void readFile(String f)  throws IOException  { /* ... */ }
    static void queryDatabase()     throws SQLException { /* ... */ }
}
```

**What this does:** pattern 1 preserves the original exception — same object, same `toString()`, same stack trace in logs. Pattern 2 wraps in an unchecked exception, useful at service boundaries to avoid propagating checked exceptions through many layers. Pattern 3 translates between checked types.

```java
// Exception chaining: getCause() traversal
public class ExceptionChainDemo {

    public static void main(String[] args) {
        try {
            level3();
        } catch (Exception e) {
            System.out.println("Top: " + e.getMessage());
            System.out.println("Cause: " + e.getCause().getMessage());
            System.out.println("Root: " + e.getCause().getCause().getMessage());
        }
    }

    static void level3() {
        try {
            level2();
        } catch (Exception e) {
            throw new RuntimeException("Level3 failed", e);
        }
    }

    static void level2() throws Exception {
        try {
            level1();
        } catch (Exception e) {
            throw new Exception("Level2 failed", e);
        }
    }

    static void level1() throws Exception {
        throw new Exception("Root cause: DB connection refused");
    }
}
```

**What this does:** each layer catches the lower-level exception and wraps it. `getCause()` traverses the chain. `e.getCause().getCause()` reaches the original root cause. In logs, `printStackTrace()` prints the full chain automatically.

### finally Overriding Return — Dry Run

```java
public class FinallyOverrideReturn {

    static int getValue() {
        int x = 1;
        try {
            x = 2;
            return x;        // return value 2 is "saved"
        } finally {
            x = 3;           // x local var changes to 3, but saved return is still 2
            // return x;     // DANGEROUS: uncomment to return 3, swallowing the try return
        }
    }

    static int getDangerousValue() {
        try {
            return 1;         // saved: return 1
        } finally {
            return 2;         // overrides! return 2 wins, no warning from compiler
        }
    }

    public static void main(String[] args) {
        System.out.println(getValue());           // 2
        System.out.println(getDangerousValue());  // 2
    }
}
```

**Dry run — `getValue()`:**

| Step | Code executed     | Local `x` | Saved return value | Notes                              |
|------|-------------------|-----------|--------------------|-------------------------------------|
| 1    | `x = 1`           | 1         | —                  | initialization                      |
| 2    | `x = 2`           | 2         | —                  |                                     |
| 3    | `return x`        | 2         | **2** saved        | return value copied, not yet sent   |
| 4    | `x = 3` (finally) | 3         | **2** unchanged    | changing x doesn't affect saved val |
| 5    | finally exits     | 3         | 2                  | no return in finally, send saved 2  |
| 6    | caller receives 2 |           |                    |                                     |

```java
// finally exception replaces original exception
public class FinallyExceptionDemo {

    static void dangerousFinally() throws Exception {
        try {
            throw new Exception("original exception");
        } finally {
            throw new Exception("finally exception");  // replaces original!
        }
    }

    public static void main(String[] args) {
        try {
            dangerousFinally();
        } catch (Exception e) {
            // "original exception" is LOST — never seen
            System.out.println("Caught: " + e.getMessage());  // "finally exception"
        }
    }
}
```

**What this does:** when `finally` throws its own exception, it completely replaces the original exception. The "original exception" is silently lost — no suppressed chain, no cause. This is the old-style (pre-Java 7) problem. Try-with-resources fixes this by using the suppressed mechanism.

> ⚠️ **Pitfall:** Never throw from `finally`. If `finally` must close something that can throw, wrap it in another try/catch. The exception-from-finally silently discards the original exception.

---

## 8. Suppressed Exceptions Deep Dive

### How try-with-resources Attaches Suppressed Exceptions

The compiler desugars try-with-resources into roughly this structure:

```java
// What the compiler generates from try-with-resources
// try (Resource r = new Resource()) { body; }
// becomes approximately:

Resource r = new Resource();
Throwable primaryException = null;
try {
    body();
} catch (Throwable t) {
    primaryException = t;
    throw t;
} finally {
    if (primaryException != null) {
        try {
            r.close();
        } catch (Throwable closeEx) {
            primaryException.addSuppressed(closeEx);  // attach, don't replace
        }
    } else {
        r.close();  // no body exception: close normally, let close exception propagate
    }
}
```

**What this does:** the key insight is `addSuppressed()`. If body threw, close exceptions are attached. If body succeeded, close exception propagates normally. This is why try-with-resources is strictly better than manual finally.

```java
// getSuppressed() access pattern
public class GetSuppressedDemo {

    static class LeakyResource implements AutoCloseable {
        final String name;
        LeakyResource(String n) { this.name = n; }

        void work() throws Exception {
            throw new Exception("body error");
        }

        @Override
        public void close() throws Exception {
            throw new Exception("close error from " + name);
        }
    }

    public static void main(String[] args) {
        try (LeakyResource a = new LeakyResource("A");
             LeakyResource b = new LeakyResource("B")) {
            a.work();
        } catch (Exception e) {
            System.out.println("Primary: " + e.getMessage());

            Throwable[] suppressed = e.getSuppressed();
            System.out.println("Suppressed count: " + suppressed.length);

            for (Throwable s : suppressed) {
                System.out.println("  Suppressed: " + s.getMessage());
            }
        }
    }
    // Output:
    // Primary: body error
    // Suppressed count: 2
    //   Suppressed: close error from B
    //   Suppressed: close error from A
}
```

**What this does:** two resources A and B are opened. `a.work()` throws. Then B closes (throws, suppressed), then A closes (throws, suppressed). The primary exception carries both suppressed exceptions. Close order is reverse of open order: B before A.

**Dry run — two resources, both close throw:**

| Step | Action              | Primary exception | Suppressed list       |
|------|---------------------|-------------------|-----------------------|
| 1    | open A              | none              | []                    |
| 2    | open B              | none              | []                    |
| 3    | `a.work()` throws   | body error        | []                    |
| 4    | close B (throws)    | body error        | [close error from B]  |
| 5    | close A (throws)    | body error        | [close error from B, close error from A] |
| 6    | catch receives it   | body error        | 2 suppressed          |

### Manual addSuppressed

```java
// Using addSuppressed manually for multi-step cleanup
public class ManualSuppressedDemo {

    static void multiStepCleanup() throws Exception {
        Exception primary = null;
        try {
            throw new Exception("main operation failed");
        } catch (Exception e) {
            primary = e;
        }

        // Multiple cleanup steps, each might fail
        try {
            cleanupA();
        } catch (Exception e) {
            if (primary != null) primary.addSuppressed(e);
            else primary = e;
        }

        try {
            cleanupB();
        } catch (Exception e) {
            if (primary != null) primary.addSuppressed(e);
            else primary = e;
        }

        if (primary != null) throw primary;
    }

    static void cleanupA() throws Exception { throw new Exception("cleanup A failed"); }
    static void cleanupB() throws Exception { throw new Exception("cleanup B failed"); }

    public static void main(String[] args) {
        try {
            multiStepCleanup();
        } catch (Exception e) {
            System.out.println("Primary: " + e.getMessage());
            for (Throwable s : e.getSuppressed()) {
                System.out.println("  Suppressed: " + s.getMessage());
            }
        }
    }
}
```

**What this does:** manual use of `addSuppressed()` for cases where you can't use try-with-resources (e.g., multiple cleanup steps not fitting the `AutoCloseable` pattern). The pattern: save primary exception, run cleanups in try/catch, attach their exceptions as suppressed, re-throw primary.

> ⚠️ **Pitfall:** An exception cannot suppress itself — `e.addSuppressed(e)` throws `IllegalArgumentException`. Also, a null argument throws `NullPointerException`. Always check for null and for self-reference when calling `addSuppressed` manually.
