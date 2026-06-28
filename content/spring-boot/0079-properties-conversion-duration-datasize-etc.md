---
card: spring-boot
gi: 79
slug: properties-conversion-duration-datasize-etc
title: Properties conversion (Duration, DataSize, etc.)
---

## 1. What it is

Spring Boot automatically converts property strings to rich Java types when binding `@ConfigurationProperties` or injecting with `@Value`. Rather than forcing you to parse `"10s"` into a `Duration` by hand, the framework does it for you through its `ConversionService`.

The main types covered out of the box:

- **`java.time.Duration`** — time spans: `"10s"`, `"5m"`, `"2h"`, `"1d"`, or ISO-8601 like `"PT2H30M"`.
- **`org.springframework.util.unit.DataSize`** — byte quantities: `"10MB"`, `"512KiB"`, `"1GB"`.
- **`java.time.Period`** — calendar periods: `"3d"`, `"2w"`, `"1y"` or ISO-8601 like `"P1Y2M"`.
- **Any custom type** that you expose via a `Converter<String, T>` bean.

The `@DurationUnit` and `@DataSizeUnit` annotations control what unit Spring assumes when a value has **no suffix** — so `"10"` can mean ten seconds, ten minutes, or ten megabytes depending on the annotation you place on the field.

## 2. Why & when

Hard-coding `TimeUnit.SECONDS.toMillis(30)` scattered through configuration code is fragile and hard to read. Storing `"30000"` in a properties file is worse — anyone reading it has to know the implicit unit. Human-readable suffixes solve both problems.

Use this feature whenever a configuration property represents:

- A **timeout** or **TTL** (cache expiry, connection idle time, session duration).
- A **file size limit** (upload cap, buffer size, log rotation threshold).
- A **calendar period** (retention window, subscription length).
- Any quantity where the unit matters and should be explicit.

It's particularly valuable for library authors publishing Spring Boot starters: end-users can write `mylib.timeout=30s` instead of memorising that the value is in milliseconds.

## 3. Core concept

Spring Boot registers a set of built-in converters with its `ApplicationConversionService`. When `@ConfigurationProperties` binding encounters a property string destined for a `Duration` field it delegates to `DurationConverter`, which understands two formats:

1. **Simple Spring format** — a number followed by a suffix: `ns`, `us`, `ms`, `s`, `m`, `h`, `d`.
2. **ISO-8601 duration** — the standard `PT…` / `P…` notation that `java.time.Duration.parse` accepts.

`DataSize` works identically but with data suffixes: `B`, `KB`, `MB`, `GB`, `TB` (SI, base-10) and `KiB`, `MiB`, `GiB`, `TiB` (IEC, base-2).

`Period` accepts Spring shorthand `nd`/`nw`/`ny` plus ISO-8601 `P…` notation.

**`@DurationUnit(ChronoUnit.SECONDS)`** placed on a field means: when the incoming string is a plain number with no suffix, treat it as seconds. Without the annotation, a bare number causes a binding error — Spring refuses to guess the unit.

The same principle applies to `@DataSizeUnit(DataUnit.MEGABYTES)`.

## 4. Diagram

<svg viewBox="0 0 680 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Property string conversion pipeline: raw string goes through ConversionService to typed Java value">
  <!-- Background panels -->
  <rect x="10" y="10" width="660" height="280" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>

  <!-- Stage 1: raw string -->
  <rect x="30" y="80" width="150" height="140" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="105" y="105" fill="#8b949e" font-size="11" text-anchor="middle" font-family="monospace">application.properties</text>
  <text x="105" y="128" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">"30s"</text>
  <text x="105" y="148" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">"512MiB"</text>
  <text x="105" y="168" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">"P1Y2M"</text>
  <text x="105" y="188" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">"10"</text>
  <text x="105" y="58" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Raw String</text>

  <!-- Arrow 1 -->
  <line x1="182" y1="150" x2="248" y2="150" stroke="#6db33f" stroke-width="2" marker-end="url(#arr1)"/>
  <defs>
    <marker id="arr1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arr2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Stage 2: ConversionService -->
  <rect x="250" y="60" width="180" height="180" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="88" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">ConversionService</text>
  <text x="340" y="110" fill="#8b949e" font-size="11" text-anchor="middle" font-family="monospace">DurationConverter</text>
  <text x="340" y="128" fill="#8b949e" font-size="11" text-anchor="middle" font-family="monospace">DataSizeConverter</text>
  <text x="340" y="146" fill="#8b949e" font-size="11" text-anchor="middle" font-family="monospace">PeriodConverter</text>
  <rect x="270" y="160" width="140" height="34" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="340" y="182" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">@DurationUnit</text>
  <text x="340" y="218" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(default-unit hint)</text>

  <!-- Arrow 2 -->
  <line x1="432" y1="150" x2="498" y2="150" stroke="#6db33f" stroke-width="2" marker-end="url(#arr2)"/>

  <!-- Stage 3: typed value -->
  <rect x="500" y="80" width="150" height="140" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="575" y="105" fill="#8b949e" font-size="11" text-anchor="middle" font-family="monospace">Java field</text>
  <text x="575" y="128" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">Duration(30s)</text>
  <text x="575" y="148" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">DataSize(512MiB)</text>
  <text x="575" y="168" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">Period(1y 2m)</text>
  <text x="575" y="188" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">Duration(10s)*</text>
  <text x="575" y="58" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Typed Value</text>

  <text x="340" y="270" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">* bare "10" → 10 s only when @DurationUnit(SECONDS) is present</text>
</svg>

A raw property string enters Spring's `ConversionService`, which dispatches to the appropriate converter. The `@DurationUnit` / `@DataSizeUnit` annotation provides the default unit that the converter uses for bare numbers.

## 5. Runnable example

```java
// src/main/java/com/example/demo/CacheProperties.java
package com.example.demo;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.convert.DataSizeUnit;
import org.springframework.boot.convert.DurationUnit;
import org.springframework.stereotype.Component;
import org.springframework.util.unit.DataSize;
import org.springframework.util.unit.DataUnit;

import java.time.Duration;
import java.time.Period;
import java.time.temporal.ChronoUnit;

@Component
@ConfigurationProperties(prefix = "demo.cache")
public class CacheProperties {

    /**
     * Full-suffix values — no annotation needed; Spring reads the suffix.
     * Set via: demo.cache.ttl=10m  (or "PT10M", or "600s")
     */
    private Duration ttl = Duration.ofMinutes(5);

    /**
     * Bare number: without @DurationUnit Spring refuses to guess the unit.
     * Set via: demo.cache.warmup-delay=3   → interpreted as 3 seconds
     */
    @DurationUnit(ChronoUnit.SECONDS)
    private Duration warmupDelay = Duration.ofSeconds(0);

    /**
     * DataSize with suffix: demo.cache.max-entry-size=512KiB
     */
    private DataSize maxEntrySize = DataSize.ofKilobytes(256);

    /**
     * Bare number treated as megabytes when no suffix present.
     * Set via: demo.cache.max-heap=128   → 128 MB
     */
    @DataSizeUnit(DataUnit.MEGABYTES)
    private DataSize maxHeap = DataSize.ofMegabytes(64);

    /**
     * Calendar period — demo.cache.retention-period=30d (or "P1M")
     */
    private Period retentionPeriod = Period.ofDays(7);

    // --- getters and setters ---
    public Duration getTtl()                    { return ttl; }
    public void setTtl(Duration ttl)            { this.ttl = ttl; }
    public Duration getWarmupDelay()            { return warmupDelay; }
    public void setWarmupDelay(Duration d)      { this.warmupDelay = d; }
    public DataSize getMaxEntrySize()           { return maxEntrySize; }
    public void setMaxEntrySize(DataSize s)     { this.maxEntrySize = s; }
    public DataSize getMaxHeap()                { return maxHeap; }
    public void setMaxHeap(DataSize s)          { this.maxHeap = s; }
    public Period getRetentionPeriod()          { return retentionPeriod; }
    public void setRetentionPeriod(Period p)    { this.retentionPeriod = p; }
}

// -----------------------------------------------------------------------
// src/main/java/com/example/demo/DemoApplication.java
package com.example.demo;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class DemoApplication implements CommandLineRunner {

    @Autowired CacheProperties cache;

    public static void main(String[] args) {
        SpringApplication.run(DemoApplication.class, args);
    }

    @Override
    public void run(String... args) {
        System.out.println("TTL           : " + cache.getTtl());
        System.out.println("Warmup delay  : " + cache.getWarmupDelay());
        System.out.println("Max entry size: " + cache.getMaxEntrySize().toKilobytes() + " KiB");
        System.out.println("Max heap      : " + cache.getMaxHeap().toMegabytes() + " MB");
        System.out.println("Retention     : " + cache.getRetentionPeriod());
    }
}
```

`application.properties` to exercise every field:

```properties
demo.cache.ttl=10m
demo.cache.warmup-delay=3
demo.cache.max-entry-size=512KiB
demo.cache.max-heap=128
demo.cache.retention-period=30d
```

**How to run:** `./mvnw spring-boot:run` (or `./gradlew bootRun`). You should see all five values printed with their correct Java representations.

## 6. Walkthrough

- **`demo.cache.ttl=10m`** — the string `"10m"` hits `DurationConverter`. The suffix `m` maps to `ChronoUnit.MINUTES`, so the field receives `Duration.ofMinutes(10)`. Alternatively `"PT10M"` (ISO-8601) or `"600s"` would work equally well.
- **`@DurationUnit(ChronoUnit.SECONDS)` + `demo.cache.warmup-delay=3`** — the bare `"3"` has no suffix; the annotation tells the converter to treat it as 3 seconds. Without the annotation, Spring throws a `ConversionFailedException` at startup.
- **`demo.cache.max-entry-size=512KiB`** — `DataSizeConverter` recognises `KiB` as an IEC unit (1 KiB = 1024 bytes), so the field holds 524 288 bytes. `512KB` (no `i`) would use SI (1 KB = 1000 bytes) — a meaningful difference.
- **`@DataSizeUnit(DataUnit.MEGABYTES)` + `demo.cache.max-heap=128`** — the bare `"128"` is treated as megabytes because of the annotation.
- **`demo.cache.retention-period=30d`** — `PeriodConverter` maps the Spring shorthand `d` to `ChronoUnit.DAYS` and returns `Period.ofDays(30)`. The ISO-8601 equivalent `"P30D"` also works.
- Default values are defined in the Java field initialisers (`Duration.ofMinutes(5)` etc.) so the app still starts correctly if a property is absent from the file.

## 7. Gotchas & takeaways

> **`KB` and `KiB` are not the same.** `KB` is 1 000 bytes (SI); `KiB` is 1 024 bytes (IEC). For network throughput SI is conventional; for JVM heap sizes IEC is more accurate. Pick deliberately, and document your choice.

> **A bare number without `@DurationUnit` / `@DataSizeUnit` is a startup error, not a silent default.** Spring Boot intentionally refuses to assume a unit — the failure is your cue to add the annotation or the suffix.

- Supported `Duration` suffixes: `ns` (nanoseconds), `us` (microseconds), `ms` (milliseconds), `s` (seconds), `m` (minutes), `h` (hours), `d` (days); plus any ISO-8601 `PT…` string.
- Supported `DataSize` suffixes: `B`, `KB`, `MB`, `GB`, `TB` (SI) and `KiB`, `MiB`, `GiB`, `TiB` (IEC).
- Supported `Period` shorthand: `nd` (days), `nw` (weeks), `ny` (years); ISO-8601 `P…` also accepted.
- `@DurationUnit` and `@DataSizeUnit` only affect the fallback for bare numbers — they do not override an explicit suffix in the property value.
- Custom types that aren't `Duration`/`DataSize`/`Period` require a `Converter<String, MyType>` bean; see tutorial gi:84.
