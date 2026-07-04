---
card: spring-framework
gi: 199
slug: cron-expressions
title: Cron expressions
---

## 1. What it is

A **cron expression** is a compact string that describes a repeating calendar schedule — "every weekday at 08:30", "first day of every month at midnight", "every 15 minutes between 9 AM and 5 PM". Spring's `@Scheduled(cron = "…")` accepts these strings directly, turning human time descriptions into precise trigger rules.

Spring uses **six fields** (unlike Unix cron's five): `second minute hour day-of-month month day-of-week`. Values can be numbers, ranges (`1-5`), step values (`*/15`), lists (`MON,WED,FRI`), or special wildcards (`?`, `L`, `W`, `#`).

## 2. Why & when

`fixedRate`/`fixedDelay` are good for "every N milliseconds" but useless for "every Sunday at 3 AM". Calendar-aware schedules come up constantly:

- Nightly database backups at a low-traffic hour.
- Monthly invoices on the first of the month.
- Business-hours-only polling ("every 10 minutes, Mon–Fri, 8–18").
- Year-end reports on 31 December.

Cron expressions encode all of this in a single string that operations teams can read and adjust in config, without touching Java code.

## 3. Core concept

Think of cron as six dials on a safe — each dial must align for the trigger to fire. Spring evaluates the expression against the current time every second and fires when all six fields match.

```
"0 30 8 * * MON-FRI"
 |  |  | |  | └─ day-of-week: Monday–Friday
 |  |  | |  └─── month: every month
 |  |  | └────── day-of-month: any day (overridden by day-of-week)
 |  |  └──────── hour: 8
 |  └─────────── minute: 30
 └────────────── second: 0
```

Special characters:
| Symbol | Meaning | Example |
|--------|---------|---------|
| `*` | every value | `* * * * * *` — every second |
| `?` | no specific value (day-of-month or day-of-week only) | use when the other day field is specified |
| `-` | range | `1-5` = 1,2,3,4,5 |
| `,` | list | `MON,WED,FRI` |
| `/` | step | `*/15` in minutes = every 15 min |
| `L` | last | `L` in day-of-month = last day of month |
| `W` | nearest weekday | `15W` = nearest weekday to 15th |
| `#` | nth weekday | `2#3` = third Tuesday |

Spring also accepts **macro aliases**: `@yearly`, `@monthly`, `@weekly`, `@daily`, `@midnight`, `@hourly`.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg">
  <!-- Six boxes for fields -->
  <rect x="15" y="60" width="80" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="55" y="81" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">0</text>
  <text x="55" y="98" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">second</text>

  <rect x="105" y="60" width="80" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="145" y="81" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">30</text>
  <text x="145" y="98" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">minute</text>

  <rect x="195" y="60" width="80" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="235" y="81" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">8</text>
  <text x="235" y="98" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">hour</text>

  <rect x="285" y="60" width="80" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="325" y="81" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">?</text>
  <text x="325" y="98" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">day-of-month</text>

  <rect x="375" y="60" width="80" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="415" y="81" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">*</text>
  <text x="415" y="98" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">month</text>

  <rect x="465" y="60" width="120" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="525" y="81" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">MON-FRI</text>
  <text x="525" y="98" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">day-of-week</text>

  <!-- Label -->
  <text x="320" y="145" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">"0 30 8 ? * MON-FRI"  →  08:30 every weekday</text>
</svg>

All six fields must simultaneously match for the trigger to fire. `?` in day-of-month means "don't constrain this" because day-of-week already constrains the day.

## 5. Runnable example

Scenario: a **report generator** that runs on different schedules — first just every 5 seconds for demo, then business-hours-only, then a full production-grade monthly schedule with time zone.

### Level 1 — Basic

Fire a report every 5 seconds (demo pace) using a simple cron expression.

```java
// CronDemo.java
import org.springframework.context.annotation.*;
import org.springframework.scheduling.annotation.*;

@Configuration
@EnableScheduling
@ComponentScan
public class CronDemo {
    public static void main(String[] args) throws InterruptedException {
        var ctx = new AnnotationConfigApplicationContext(CronDemo.class);
        Thread.sleep(16000); // watch ~3 fires
        ctx.close();
    }
}

@org.springframework.stereotype.Component
class ReportTask {
    private int runs = 0;

    @Scheduled(cron = "*/5 * * * * *")  // every 5 seconds
    public void generate() {
        System.out.printf("Report #%d generated at %s%n",
            ++runs, java.time.LocalTime.now());
    }
}
```

How to run: `java -cp spring-context.jar:. CronDemo.java`

`*/5` in the seconds field means "every value divisible by 5": 0, 5, 10, 15 … The expression fires at the *next* clock second that matches, so the first fire is at most 5 s away.

---

### Level 2 — Intermediate

Business-hours-only concern: generate reports only during working hours (Mon–Fri, 09:00–17:00), every 30 minutes.

```java
// CronDemo.java
import org.springframework.context.annotation.*;
import org.springframework.scheduling.annotation.*;

@Configuration
@EnableScheduling
@ComponentScan
public class CronDemo {
    public static void main(String[] args) throws InterruptedException {
        var ctx = new AnnotationConfigApplicationContext(CronDemo.class);
        Thread.sleep(10000);
        ctx.close();
    }
}

@org.springframework.stereotype.Component
class ReportTask {
    private int runs = 0;

    // Every 30 min, Mon-Fri, hours 9-17
    @Scheduled(cron = "0 */30 9-17 ? * MON-FRI")
    public void businessHoursReport() {
        System.out.printf("Business report #%d at %s%n",
            ++runs, java.time.LocalDateTime.now());
    }

    // Demo: fires every 4 seconds so we can see output quickly
    @Scheduled(cron = "*/4 * * * * *")
    public void demoHeartbeat() {
        System.out.printf("  [demo] tick — next business report at %s%n",
            java.time.LocalTime.now());
    }
}
```

How to run: same as Level 1

`9-17` in the hour field restricts firing to 09:xx–17:xx. `?` in day-of-month defers to `MON-FRI` in day-of-week. The `demoHeartbeat` fires quickly so we can verify the scheduler is alive even when the business cron is dormant.

---

### Level 3 — Advanced

Production concern: use an explicit time zone and the `L` (last-day) special character to run a month-end summary; also read the cron string from a property so ops can change it without a redeploy.

```java
// CronDemo.java
import org.springframework.context.annotation.*;
import org.springframework.scheduling.annotation.*;
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.support.*;

@Configuration
@EnableScheduling
@ComponentScan
@PropertySource("classpath:schedule.properties")
public class CronDemo {
    public static void main(String[] args) throws InterruptedException {
        // Simulate property source with a system property
        System.setProperty("report.cron", "*/3 * * * * *"); // fast for demo
        System.setProperty("report.zone", "Europe/London");
        var ctx = new AnnotationConfigApplicationContext(CronDemo.class);
        ctx.getEnvironment().getSystemProperties(); // already loaded
        Thread.sleep(12000);
        ctx.close();
    }
}

@org.springframework.stereotype.Component
class ReportTask {
    private int runs = 0;

    // Production value: "0 0 23 L * ?" — 23:00 on last day of every month
    // Demo value injected from system property via @Scheduled SpEL property binding
    @Scheduled(cron = "${report.cron:0 0 23 L * ?}", zone = "${report.zone:UTC}")
    public void monthEndReport() {
        System.out.printf("Month-end report #%d at %s (zone=%s)%n",
            ++runs,
            java.time.ZonedDateTime.now(
                java.time.ZoneId.of(
                    System.getProperty("report.zone", "UTC"))),
            System.getProperty("report.zone", "UTC"));
    }
}
```

How to run: `java -cp spring-context.jar:spring-beans.jar:. CronDemo.java`

`${report.cron:0 0 23 L * ?}` reads the cron string from a property with a fallback. The `zone` attribute on `@Scheduled` ensures the trigger fires at the correct wall-clock time regardless of the JVM's default time zone — critical for servers hosted in UTC while the business is in London.

## 6. Walkthrough

**Expression parsing:** When Spring processes `@Scheduled(cron = "*/3 * * * * *")`, `CronExpression.parse()` tokenises each of the six fields. `*/3` in seconds computes the set `{0, 3, 6, 9, …, 57}`.

**Next-execution calculation:** The `CronTrigger.nextExecutionTime(context)` method takes the *last scheduled time* (or now if first run) and advances second-by-second through the expression until all six fields match. For `*/3 * * * * *` and last run at `12:00:00`, next run is `12:00:03`.

**Property value resolution:** `${report.cron:0 0 23 L * ?}` is resolved by Spring's `PropertySourcesPropertyResolver` before `CronExpression.parse()` is called. The fallback after `:` is used when the property is absent.

**`zone` attribute:** Spring wraps the resolved `ZoneId` around the trigger. Instead of comparing against the JVM's default `ZoneId.systemDefault()`, the scheduler converts the current instant to the configured zone before matching the expression. This means "23:00 London time" fires at 23:00 BST (UTC+1) in summer and 23:00 GMT in winter.

**`L` in day-of-month:** When day-of-month is `L`, `CronExpression` computes `YearMonth.of(year,month).lengthOfMonth()` dynamically so it handles February correctly (28 or 29 days).

**`?` interaction:** You cannot specify both day-of-month and day-of-week as non-`?` values — Spring throws `IllegalArgumentException`. Use `?` on whichever field should be ignored.

**Expected output (demo pace):**
```
Month-end report #1 at 2025-11-03T14:22:03Z[Europe/London] (zone=Europe/London)
Month-end report #2 at 2025-11-03T14:22:06Z[Europe/London] (zone=Europe/London)
```

## 7. Gotchas & takeaways

> **Day-of-month and day-of-week cannot both be set.** One must be `?`. Spring (via Quartz-influenced CronExpression) requires exactly one to be `?`. Setting both throws `IllegalArgumentException: "Support for specifying both a day-of-week and a day-of-month parameter is not implemented"`.

> **Seconds are field 1, not an extension.** Unix cron has 5 fields (no seconds). Spring cron has 6 (seconds first). Pasting a 5-field Unix cron directly silently misfires.

- `*/N` means "every N-th value starting at 0", not "every N seconds from last run" — for gaps from last run use `fixedDelay`.
- `zone` attribute accepts any `ZoneId` string; omit it to use the JVM default — but set it explicitly in production.
- `@Scheduled(cron = "@midnight")` is equivalent to `"0 0 0 * * *"` — Spring's macro aliases improve readability.
- To test cron expressions without running code, use [crontab.guru](https://crontab.guru) (remembering Spring adds seconds as field 1).
- Externalise cron strings to properties so ops can adjust schedules without rebuilding the artifact.
