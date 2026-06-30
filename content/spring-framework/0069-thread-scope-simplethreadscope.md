---
card: spring-framework
gi: 69
slug: thread-scope-simplethreadscope
title: Thread scope (SimpleThreadScope)
---

## 1. What it is

**`SimpleThreadScope`** is a built-in Spring scope (in `org.springframework.context.support`) that creates one bean instance per thread. It is the simplest custom scope implementation: the scope store is a `ThreadLocal<Map<String, Object>>`. Unlike request or session scope, `SimpleThreadScope` is **not registered by default** and **never calls destroy callbacks** — beans live until the thread's `ThreadLocal` is cleared or the thread terminates.

```java
// Register SimpleThreadScope
@Configuration
public class ThreadScopeConfig {
    @Bean
    public static CustomScopeConfigurer threadScopeConfigurer() {
        CustomScopeConfigurer configurer = new CustomScopeConfigurer();
        configurer.addScope("thread", new SimpleThreadScope());
        return configurer;
    }
}

// Use the thread scope
@Component
@Scope("thread")
public class TransactionContext {
    private String transactionId;
    private List<String> pendingOps = new ArrayList<>();
    // One per thread — each worker thread gets its own context
}
```

In one sentence: **`SimpleThreadScope` gives each thread its own instance of a bean via a `ThreadLocal`, making it useful for thread-confined state in worker-thread pools, batch jobs, or any scenario where one object per thread is the correct isolation unit.**

## 2. Why & when

Use thread scope when:

- **Thread pool workers** need per-thread scratch-pad state without `ThreadLocal` boilerplate.
- **Batch readers/writers** — each reader thread tracks its own position or buffer.
- **Per-thread transaction context** — track the current thread's open transaction.
- **Logging context** — MDC-style per-thread context enrichment.

Thread scope is conceptually simpler than request scope: request scope uses a `RequestAttributes` binding (which happens to use `ThreadLocal` internally); thread scope *is* the `ThreadLocal`.

Do NOT use thread scope when:

- You need destroy callbacks — `SimpleThreadScope` never calls `@PreDestroy`.
- Your work crosses thread boundaries (async, reactive, CompletableFuture) — `ThreadLocal` state does not propagate to child threads automatically.

## 3. Core concept

```
SimpleThreadScope implementation (simplified):
  private final ThreadLocal<Map<String, Object>> store =
      ThreadLocal.withInitial(HashMap::new);

  @Override
  public Object get(String name, ObjectFactory<?> factory) {
      Map<String, Object> map = store.get();
      return map.computeIfAbsent(name, k -> factory.getObject());
  }

  @Override
  public Object remove(String name) {
      return store.get().remove(name);
  }

  // registerDestructionCallback: no-op (Spring's warning: callbacks never called)
  // getConversationId: returns thread name (Thread.currentThread().getName())

Key properties:
  • One bean instance per Thread object.
  • State persists for the lifetime of the thread (or until remove() is called).
  • If a thread pool reuses threads, beans persist across tasks on the same thread.
  • @PreDestroy is NEVER called — SimpleThreadScope logs a warning about this.
```

## 4. Diagram

<svg viewBox="0 0 660 205" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SimpleThreadScope: each thread has its own ThreadLocal store with independent bean instances">
  <defs>
    <marker id="a69" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <rect x="5" y="5" width="650" height="193" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="330" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">SimpleThreadScope — one ThreadLocal per thread, one bean per thread</text>

  <!-- Thread 1 -->
  <rect x="15" y="35" width="195" height="140" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="112" y="52" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">worker-thread-1</text>
  <rect x="25" y="60" width="175" height="40" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="112" y="78" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">ThreadLocal store</text>
  <text x="112" y="92" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">txCtx → TransactionContext#1</text>
  <text x="112" y="114" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Task A: txCtx.open("TX-1")</text>
  <text x="112" y="127" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Task B (reuse thread): txCtx sees</text>
  <text x="112" y="140" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">"TX-1" still in context!</text>
  <text x="112" y="165" fill="#ff6b6b" font-size="7" text-anchor="middle" font-family="sans-serif">⚠ ThreadPool reuse — must clear!</text>

  <!-- Thread 2 -->
  <rect x="230" y="35" width="195" height="140" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="327" y="52" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">worker-thread-2</text>
  <rect x="240" y="60" width="175" height="40" rx="3" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="327" y="78" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">ThreadLocal store</text>
  <text x="327" y="92" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">txCtx → TransactionContext#2</text>
  <text x="327" y="114" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Task C: txCtx.open("TX-2")</text>
  <text x="327" y="127" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Completely isolated from thread-1</text>

  <!-- Thread 3 -->
  <rect x="445" y="35" width="200" height="140" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="545" y="52" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">worker-thread-3</text>
  <rect x="455" y="60" width="180" height="40" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="545" y="78" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ThreadLocal store</text>
  <text x="545" y="92" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">txCtx → TransactionContext#3</text>
  <text x="545" y="114" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Task D: own context</text>

  <text x="330" y="185" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Thread-local isolation: thread-1's TransactionContext never visible to threads 2 or 3.</text>
</svg>

Each thread has its own `ThreadLocal` map. `TransactionContext#1`, `#2`, `#3` are entirely independent. Thread pool reuse means a thread's context persists between tasks — must be cleared explicitly.

## 5. Runnable example

Scenario: a `BatchWorkerContext` scoped per-thread — each worker thread tracks its own job segment, progress, and errors without interfering with other threads.

### Level 1 — Basic

One context per thread — demonstrate isolation and `ThreadLocal` reuse within the same thread.

```java
// ThreadScopeDemo.java — run with: java ThreadScopeDemo.java
import java.util.*;

public class ThreadScopeDemo {

    // ── per-thread bean (thread-scope equivalent) ─────────────────────
    static class WorkerContext {
        private static int count = 0;
        final int    id;
        final String threadName;
        private int  processedItems = 0;
        private int  errorCount     = 0;
        private final List<String> errors = new ArrayList<>();

        WorkerContext() {
            id         = ++count;
            threadName = Thread.currentThread().getName();
            System.out.println("  [THREAD BEAN CREATED #" + id + "] thread=" + threadName);
        }

        void process(String item) {
            if (item.startsWith("BAD")) {
                errorCount++;
                errors.add(item);
                System.out.println("  [ERROR] " + item + " thread=" + threadName + " ctx#=" + id);
            } else {
                processedItems++;
            }
        }

        String summary() {
            return String.format("WorkerContext#%d thread=%s processed=%d errors=%d",
                id, threadName, processedItems, errorCount);
        }
    }

    // ── simulated SimpleThreadScope ────────────────────────────────────
    static final ThreadLocal<WorkerContext> CONTEXT = ThreadLocal.withInitial(WorkerContext::new);

    static WorkerContext currentContext() { return CONTEXT.get(); }
    static void clearContext()            { CONTEXT.remove(); }

    // ── worker task ────────────────────────────────────────────────────
    static void processItems(List<String> items) {
        WorkerContext ctx = currentContext();
        System.out.println("[TASK] thread=" + Thread.currentThread().getName()
            + " ctx#=" + ctx.id + " items=" + items.size());
        for (String item : items) ctx.process(item);
        System.out.println("  [DONE] " + ctx.summary());
        clearContext();  // important: clear before thread is returned to pool
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Two threads, each gets its own WorkerContext ===");

        Thread t1 = new Thread(() -> processItems(
            List.of("item-1", "item-2", "BAD-item-3", "item-4")), "worker-1");
        Thread t2 = new Thread(() -> processItems(
            List.of("item-5", "BAD-item-6", "BAD-item-7")), "worker-2");

        t1.start(); t2.start();
        t1.join();  t2.join();

        System.out.println("\n[TOTAL CONTEXTS CREATED] " + WorkerContext.count);
        System.out.println("[KEY] Two contexts — one per thread, no shared mutable state.");
    }
}
```

How to run: `java ThreadScopeDemo.java`

Each thread gets its own `WorkerContext` via `ThreadLocal.withInitial(WorkerContext::new)`. Thread 1's error count is independent of thread 2's. `clearContext()` removes the `ThreadLocal` binding at task end — critical when using thread pools to avoid state leaking into the next task on the same thread.

### Level 2 — Intermediate

Thread pool reuse scenario: show that without clearing, a thread-scoped bean's state persists between tasks.

```java
// ThreadScopeDemo2.java — run with: java ThreadScopeDemo2.java
import java.util.*;
import java.util.concurrent.*;

public class ThreadScopeDemo2 {

    static class TaskContext {
        private static int count = 0;
        final int    id;
        final String threadName;
        private int  runCount = 0;
        private final List<String> processedIds = new ArrayList<>();

        TaskContext() {
            id = ++count;
            threadName = Thread.currentThread().getName();
            System.out.println("    [CONTEXT CREATED #" + id + "] thread=" + threadName);
        }

        void run(String taskId) {
            runCount++;
            processedIds.add(taskId);
            System.out.printf("    [CTX#%d] task=%s runCount=%d processedIds=%s%n",
                id, taskId, runCount, processedIds);
        }
    }

    static final ThreadLocal<TaskContext> CTX = ThreadLocal.withInitial(TaskContext::new);

    // ── demo WITHOUT clear — shows stale state bleed ───────────────────
    static void runWithoutClear(ExecutorService pool, String taskId) throws Exception {
        pool.submit(() -> {
            CTX.get().run(taskId);
            // NOT clearing — state persists in thread's ThreadLocal for next task
        }).get();
    }

    // ── demo WITH clear — correct pattern ──────────────────────────────
    static void runWithClear(ExecutorService pool, String taskId) throws Exception {
        pool.submit(() -> {
            try { CTX.get().run(taskId); }
            finally { CTX.remove(); }  // always clear, even on exception
        }).get();
    }

    public static void main(String[] args) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(1);  // single thread to demo reuse

        System.out.println("=== WITHOUT clearing (state bleeds across tasks) ===");
        runWithoutClear(pool, "task-A");
        runWithoutClear(pool, "task-B");  // same thread → same context → runCount=2!
        runWithoutClear(pool, "task-C");  // runCount=3 — all three leaked into same context

        System.out.println();
        System.out.println("=== After clearing, reset: WITH clearing (correct) ===");
        CTX.remove();  // clean start for demo
        runWithClear(pool, "task-D");    // new context (runCount=1)
        runWithClear(pool, "task-E");    // new context (runCount=1) — fresh each time
        runWithClear(pool, "task-F");    // new context (runCount=1)

        pool.shutdown();
        System.out.println("\n[TOTAL CONTEXTS CREATED] " + TaskContext.count);
        System.out.println("[KEY] Without clear: 1 context reused 3 times.");
        System.out.println("[KEY] With clear:    3 fresh contexts created.");
    }
}
```

How to run: `java ThreadScopeDemo2.java`

A single-threaded pool reuses the same thread for all tasks. Without `CTX.remove()`, tasks D–F would reuse the same context (runCount increments to 3). With `CTX.remove()` in `finally`, each task creates a fresh context (runCount always 1). This is the critical gotcha: `SimpleThreadScope` does not clear state — the caller must.

### Level 3 — Advanced

Parallel batch processing with thread-scoped accumulators, then a final aggregation step that collects all thread results.

```java
// ThreadScopeDemo3.java — run with: java ThreadScopeDemo3.java
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import java.util.stream.*;

public class ThreadScopeDemo3 {

    // ── thread-scoped batch accumulator ───────────────────────────────
    static class BatchAccumulator {
        private static final AtomicInteger seq = new AtomicInteger();
        final int    id;
        final String threadName;
        int    itemsRead    = 0;
        int    itemsWritten = 0;
        int    errors       = 0;
        long   totalValue   = 0;
        final List<String> errorItems = new ArrayList<>();

        BatchAccumulator() {
            id         = seq.incrementAndGet();
            threadName = Thread.currentThread().getName();
        }

        void recordRead()                 { itemsRead++; }
        void recordWrite(long value)      { itemsWritten++; totalValue += value; }
        void recordError(String itemId)   { errors++; errorItems.add(itemId); }

        Map<String, Object> toMap() {
            return Map.of(
                "threadName", threadName, "id", id,
                "read",       itemsRead,  "written", itemsWritten,
                "errors",     errors,     "totalValue", totalValue,
                "errorItems", errorItems
            );
        }

        @Override public String toString() {
            return String.format("Acc#%d[%s] read=%d written=%d errors=%d total=%d",
                id, threadName, itemsRead, itemsWritten, errors, totalValue);
        }
    }

    static final ThreadLocal<BatchAccumulator> ACC = ThreadLocal.withInitial(BatchAccumulator::new);
    static final CopyOnWriteArrayList<Map<String,Object>> RESULTS = new CopyOnWriteArrayList<>();

    static void processChunk(List<String[]> records) {
        BatchAccumulator acc = ACC.get();
        try {
            System.out.printf("[CHUNK] thread=%s acc#=%d records=%d%n",
                Thread.currentThread().getName(), acc.id, records.size());
            for (String[] rec : records) {
                acc.recordRead();
                try {
                    long value = Long.parseLong(rec[1]);
                    if (value < 0) throw new IllegalArgumentException("Negative value");
                    acc.recordWrite(value);
                } catch (Exception e) {
                    acc.recordError(rec[0]);
                }
            }
            System.out.println("  [CHUNK DONE] " + acc);
        } finally {
            RESULTS.add(acc.toMap());  // collect before removing
            ACC.remove();              // clear ThreadLocal
        }
    }

    // Build simulated batch records
    static List<String[]> buildRecords(int start, int count, boolean includeErrors) {
        List<String[]> list = new ArrayList<>();
        for (int i = start; i < start + count; i++) {
            String val = includeErrors && i % 5 == 0 ? "INVALID" : String.valueOf(i * 100L);
            list.add(new String[]{"record-" + i, val});
        }
        return list;
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Parallel batch processing (4 worker threads) ===");
        ExecutorService pool = Executors.newFixedThreadPool(4);
        List<Future<?>> futures = new ArrayList<>();

        // Split 100 records into 4 chunks of 25 — each processed by a worker thread
        futures.add(pool.submit(() -> processChunk(buildRecords(  0, 25, false))));
        futures.add(pool.submit(() -> processChunk(buildRecords( 25, 25, true ))));
        futures.add(pool.submit(() -> processChunk(buildRecords( 50, 25, false))));
        futures.add(pool.submit(() -> processChunk(buildRecords( 75, 25, true ))));

        for (Future<?> f : futures) f.get();
        pool.shutdown();

        System.out.println("\n=== Aggregating thread-local results ===");
        long totalRead    = RESULTS.stream().mapToLong(m -> (int) m.get("read"))   .sum();
        long totalWritten = RESULTS.stream().mapToLong(m -> (int) m.get("written")).sum();
        long totalErrors  = RESULTS.stream().mapToLong(m -> (int) m.get("errors")) .sum();
        long totalValue   = RESULTS.stream().mapToLong(m -> (long) m.get("totalValue")).sum();
        List<String> allErrors = RESULTS.stream()
            .flatMap(m -> ((List<String>) m.get("errorItems")).stream())
            .collect(Collectors.toList());

        System.out.printf("  Total read:    %d%n", totalRead);
        System.out.printf("  Total written: %d%n", totalWritten);
        System.out.printf("  Total errors:  %d  items=%s%n", totalErrors, allErrors);
        System.out.printf("  Total value:   %d%n", totalValue);
        System.out.println("  Thread accumulators: " + BatchAccumulator.seq.get());
    }
}
```

How to run: `java ThreadScopeDemo3.java`

Four worker threads each get their own `BatchAccumulator` via `ThreadLocal`. Each thread processes 25 records independently and appends its result to `RESULTS` before clearing its `ThreadLocal`. The main thread aggregates results from all four accumulators. This pattern (parallel per-thread accumulation → single aggregation) is exactly how Spring Batch uses thread-scoped beans in multi-threaded step execution.

## 6. Walkthrough

**`processChunk(records-25..49-with-errors)` on worker-thread-2:**

```
ACC.get() → ThreadLocal → no entry yet → new BatchAccumulator()
  [THREAD BEAN CREATED #2] thread=pool-1-thread-2
try:
  for each of 25 records (indices 25..49):
    acc.recordRead()   → itemsRead++
    index 25: "record-25", "2500" → parseLong(2500) → acc.recordWrite(2500)
    index 30: "record-30", "INVALID" → NumberFormatException → acc.recordError("record-30")
    index 35: "record-35", "INVALID" → acc.recordError("record-35")
    ... (5 errors total at indices 30,35,40,45)
  end of loop:
    itemsRead=25, itemsWritten=20, errors=5, totalValue=sum of valid values
  [CHUNK DONE] Acc#2[pool-1-thread-2] read=25 written=20 errors=5 total=...
finally:
  RESULTS.add(acc.toMap())   → save result
  ACC.remove()               → ThreadLocal cleared (no state leaks)
```

**Aggregation:**

```
RESULTS = [chunk-0-result, chunk-25-result, chunk-50-result, chunk-75-result]
totalRead    = 25+25+25+25 = 100
totalErrors  = 0+5+0+5     = 10
totalWritten = 100 - 10    = 90
allErrors    = [record-30, record-35, record-40, record-45, record-75, record-80, ...]
```

## 7. Gotchas & takeaways

> **`SimpleThreadScope` never calls `@PreDestroy` or `DisposableBean.destroy()`.** Spring logs a warning about this. If your thread-scoped bean holds resources (connections, file handles), you must close them manually — the thread-scope container does not manage bean teardown.

> **Thread pool reuse means thread-local state survives between tasks.** Unless you explicitly call `ThreadLocal.remove()` (or `SimpleThreadScope.remove()`) at the end of each task, the next task on the same thread sees the previous task's stale context. Always clear in a `finally` block.

- `SimpleThreadScope` is NOT registered by default. Registering it with `CustomScopeConfigurer` or directly via `beanFactory.registerScope("thread", new SimpleThreadScope())` in a `BeanFactoryPostProcessor` is required.
- `SimpleThreadScope.getConversationId()` returns `Thread.currentThread().getName()` — useful for debug logging.
- For reactive/virtual-thread applications, `ThreadLocal` is not propagated across suspension points (Reactor, Kotlin Coroutines). Use `ReactorContext` or `CoroutineContext` instead — `SimpleThreadScope` is not appropriate for reactive code.
- Spring Batch's `@JobScope` and `@StepScope` are more sophisticated custom scopes: they DO call destroy callbacks and manage lifecycle properly. Prefer them over raw `SimpleThreadScope` for batch jobs.
