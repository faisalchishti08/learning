---
card: java
gi: 791
slug: ahead-of-time-class-loading-linking
title: Ahead-of-Time class loading & linking
---

## 1. What it is

**Java 24** (JEP 483) introduces a simplified **AOT (Ahead-of-Time) cache** workflow: run your application once in a special "training" mode to record which classes it loads and how they get linked, and the JVM writes that information to a cache file. On every subsequent run, pointing the JVM at that cache file (`-XX:AOTCache=app.aot`) lets it **skip re-doing class loading and linking work** it already knows the outcome of — cutting a meaningful chunk off JVM startup time, especially for applications with large class graphs (Spring Boot apps, large enterprise applications) where class loading and linking is a real fraction of total startup.

## 2. Why & when

Class-Data Sharing (CDS) and its dynamic variant already let the JVM cache metadata about loaded classes to speed up subsequent runs, but the workflow to set it up was a multi-step process most application developers never bothered with — generate a class list, create an archive from it, then remember to pass the right flags on every future launch. JEP 483 collapses that into something much closer to "run it once with one flag, then use it": a single training run with `-XX:AOTMode=record` captures everything the previous, more manual CDS workflow required several separate steps to assemble, and the resulting cache is then simply pointed at with `-XX:AOTCache=...` on every real launch. This matters most for short-lived JVM processes where startup time is a meaningful fraction of total run time — CLI tools, serverless functions, and container-based deployments that start fresh JVM instances frequently — where shaving hundreds of milliseconds off every single startup adds up quickly across many invocations.

## 3. Core concept

```
# Step 1: training run — records classes loaded/linked while the app runs normally
java -XX:AOTCacheOutput=app.aot -XX:AOTMode=record -cp app.jar App

# Step 2: real runs — use the recorded cache to skip re-doing that work
java -XX:AOTCache=app.aot -cp app.jar App
```

The training run exercises the application's typical startup path once; every subsequent run reuses what it learned.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A training run records which classes are loaded and linked into an AOT cache file, and subsequent runs point at that cache to skip redoing the same class loading and linking work" >
  <rect x="20" y="20" width="260" height="55" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="150" y="45" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Training run</text>
  <text x="150" y="63" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">-XX:AOTMode=record -&gt; app.aot</text>

  <line x1="280" y1="47" x2="330" y2="47" stroke="#6db33f" stroke-width="2" marker-end="url(#a791)"/>
  <defs><marker id="a791" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker></defs>

  <rect x="340" y="20" width="260" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="470" y="45" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Real runs</text>
  <text x="470" y="63" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">-XX:AOTCache=app.aot -&gt; faster startup</text>

  <text x="320" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Class loading and linking already resolved by the cache are skipped, not redone</text>

  <rect x="140" y="150" width="360" height="30" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="320" y="170" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">One training run amortizes across every real launch</text>
</svg>

*A single recorded training run speeds up every subsequent launch that reuses its cache.*

## 5. Runnable example

Scenario: a small application with a modest class graph, growing from measuring plain startup time into a full record/use AOT cache workflow, then a repeated-launch comparison mimicking a short-lived-process deployment.

### Level 1 — Basic

```java
import java.util.*;

public class AotAppBasic {
    public static void main(String[] args) {
        List<String> greetings = List.of("Hello", "Hola", "Bonjour", "Ciao");
        Map<String, Integer> lengths = new HashMap<>();
        for (String g : greetings) {
            lengths.put(g, g.length());
        }
        System.out.println(lengths);
    }
}
```

**How to run:** `java AotAppBasic.java` (JDK 24+; establishes a normal baseline before introducing the AOT cache).

A small program touching a handful of common `java.base` classes (`List`, `HashMap`) — enough class loading and linking work to make a caching comparison meaningful, though not yet using any AOT flags.

### Level 2 — Intermediate

```
# Compile first, since the AOT cache workflow targets a class file / jar, not a single source file.
javac AotAppBasic.java

# Step 1: training run — records which classes AotAppBasic loads
java -XX:AOTCacheOutput=aotapp.aot -XX:AOTMode=record AotAppBasic

# Step 2: use the recorded cache on a real run
java -XX:AOTCache=aotapp.aot AotAppBasic
```

**How to run:** run the three commands above in order (JDK 24+). The training run behaves exactly like a normal run (it still prints the program's output) while also writing `aotapp.aot`; the third command reuses that cache.

The real-world concern added: the actual **two-step workflow** — one training run producing a reusable cache file, then subsequent runs pointing at it — this is the concrete mechanism JEP 483 simplifies down from the older, more manual CDS archive-creation process.

### Level 3 — Advanced

```
# Training run against a representative startup path
java -XX:AOTCacheOutput=aotapp.aot -XX:AOTMode=record AotAppBasic

# Compare repeated startup timing with and without the cache —
# simulating a short-lived-process deployment launching the same JVM many times.
for i in 1 2 3 4 5; do
  /usr/bin/time -p java AotAppBasic > /dev/null
done

echo "--- now with AOT cache ---"

for i in 1 2 3 4 5; do
  /usr/bin/time -p java -XX:AOTCache=aotapp.aot AotAppBasic > /dev/null
done
```

**How to run:** run this shell workflow after compiling `AotAppBasic.java` (JDK 24+; `/usr/bin/time -p` prints wall-clock time per run — on some systems, use `time` as a shell builtin instead if `/usr/bin/time` isn't available).

This adds the production-flavored hard case: **repeated launches**, timed, with and without the AOT cache — the scenario where AOT caching actually pays off is exactly this one, many short-lived JVM startups of the same application, where the training run's one-time cost is amortized across every subsequent launch, and the `real`/`user` time reported by `time -p` becomes the concrete, measurable evidence of the improvement.

## 6. Walkthrough

Tracing the full three-command workflow from Level 2:

1. `javac AotAppBasic.java` compiles the source into `AotAppBasic.class`, since the AOT cache workflow operates on compiled classes, not raw source files.
2. `java -XX:AOTCacheOutput=aotapp.aot -XX:AOTMode=record AotAppBasic` starts the JVM in **recording mode**: it runs the program completely normally — loading `AotAppBasic`, `List`, `Map`, `HashMap`, and every class transitively needed to execute `main` — while also tracking, class by class, the loading and linking decisions the JVM made along the way. The program's own output (the printed map) appears exactly as it would in a normal run; the difference is entirely in what happens alongside it. Once `main` returns, the JVM writes everything it recorded to `aotapp.aot`.
3. `java -XX:AOTCache=aotapp.aot AotAppBasic` starts a **fresh** JVM process, but this time it reads `aotapp.aot` first. For every class the cache has recorded loading/linking information about, the JVM can reuse that recorded work directly instead of repeating the class-loading and linking steps from scratch — the program still runs the same `main` method and produces the same output, but with less redundant JVM-internal work happening before it gets there.
4. The observable difference isn't in the program's printed output — which is identical across all three runs — it's in **how long the JVM takes to get to the point of running `main` at all**, which is what the Level 3 timing comparison is designed to surface.

Expected program output (identical for every run, cached or not):
```
{Hola=4, Bonjour=7, Ciao=4, Hello=5}
```

Expected timing shape from the Level 3 comparison (exact numbers vary heavily by machine, JDK build, and application size — larger, more class-heavy applications typically show a bigger proportional improvement than this small example):
```
--- now with AOT cache ---
real         0.04
real         0.03
...
```

## 7. Gotchas & takeaways

> **Gotcha:** an AOT cache is tied to the exact classes and JVM configuration present during the training run — adding new dependencies, changing the classpath, or running against a different JDK build than the one that created the cache can invalidate it (the JVM detects the mismatch and falls back to normal startup rather than using stale cached data, but you lose the speedup silently unless you check for a warning). Regenerate the cache whenever the application's class graph or deployment JDK changes meaningfully.

- Java 24 (JEP 483) simplifies AOT/CDS caching into a two-step workflow: `-XX:AOTMode=record` to train, `-XX:AOTCache=...` to use the resulting cache on real runs.
- Speeds up JVM startup by skipping already-resolved class loading and linking work, not by changing anything about how the application itself executes.
- The improvement is most valuable for short-lived JVM processes launched repeatedly — CLI tools, serverless functions, containers restarting frequently — where startup time is a meaningful fraction of total run time.
- The cache must be regenerated if the application's classes or the JVM configuration it was trained against change significantly, or the JVM silently falls back to uncached startup.
- Builds on the JDK's existing Class-Data Sharing foundations, but collapses what used to be a multi-step manual archive-creation process into a single training run plus a single cache-pointing flag.
