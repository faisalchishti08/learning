---
card: spring-boot
gi: 275
slug: quartz-scheduler
title: Quartz Scheduler
---

## 1. What it is

**Quartz** is a full-featured, open-source job scheduling library. Spring Boot auto-configures it when `spring-boot-starter-quartz` is on the classpath.

Key concepts:
- **Job** — a class implementing `Job` that contains the work to do.
- **JobDetail** — describes a Job: class, name, group, data.
- **Trigger** — when and how often to fire a Job (cron expression, simple interval, calendar).
- **Scheduler** — the central Quartz engine; holds Jobs and Triggers and fires them.

Quartz is more powerful than Spring's built-in `@Scheduled`:
- **Persisted schedules** — Jobs and Triggers stored in a database survive application restarts.
- **Cluster support** — multiple instances run the same scheduler; only one fires each trigger (cluster mode).
- **Misfire handling** — defines what happens when a trigger fires while the app was down.
- **Job data** — pass arbitrary data to Jobs via `JobDataMap`.

## 2. Why & when

Use Quartz when:

- You need schedules to **survive restarts** — `@Scheduled` runs only while the JVM is up. If the app is down at 2 AM when the nightly report should run, it doesn't run. Quartz with JDBC job store fires missed jobs when the app comes back up (depending on misfire policy).
- You need **cluster-safe scheduling** — in a multi-pod Kubernetes deployment, `@Scheduled` runs on every pod. Quartz cluster mode ensures each job runs on exactly one pod.
- You need **dynamic scheduling** — create, update, or delete jobs and triggers at runtime via the `Scheduler` API (e.g., a user schedules a custom report via a UI).
- You need **job history and monitoring** — the JDBC job store's tables provide a persistent record.

Use `@Scheduled` for simple, stateless, always-on jobs that don't need cluster coordination.

## 3. Core concept

Spring Boot's `QuartzAutoConfiguration` creates:

1. A `Scheduler` bean from `QuartzProperties` (`spring.quartz.*`).
2. A `SchedulerFactoryBean` that wires Spring-managed beans into Quartz Jobs (so Jobs can `@Autowired` services).
3. JDBC job store configuration if `spring.quartz.job-store-type=jdbc`.

The Job store types:

| Type | Persistence | Cluster | Use case |
|---|---|---|---|
| `MEMORY` (default) | No | No | Dev, simple cases |
| `JDBC` | Yes (database) | Yes | Production, clustered |

With `JDBC`, Quartz creates ~11 tables in your database (`QRTZ_JOB_DETAILS`, `QRTZ_TRIGGERS`, etc.). Spring Boot can create them automatically via `spring.quartz.jdbc.initialize-schema=always`.

## 4. Diagram

<svg viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Quartz Scheduler components: Job, JobDetail, Trigger, Scheduler, and JDBC cluster mode">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Scheduler -->
  <rect x="250" y="80" width="200" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="108" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif">Quartz Scheduler</text>
  <text x="350" y="126" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">fires triggers, runs jobs</text>
  <text x="350" y="142" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">spring.quartz.*</text>

  <!-- Trigger -->
  <rect x="10" y="50" width="160" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="72" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">CronTrigger</text>
  <text x="90" y="90" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">0 0 2 * * ? (2 AM daily)</text>

  <!-- JobDetail -->
  <rect x="10" y="130" width="160" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="152" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">JobDetail</text>
  <text x="90" y="170" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">ReportJob.class + data</text>

  <!-- JDBC Store -->
  <rect x="530" y="80" width="160" height="80" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="610" y="108" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">JDBC Job Store</text>
  <text x="610" y="126" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">QRTZ_* tables</text>
  <text x="610" y="142" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">persists schedules</text>

  <line x1="170" y1="75" x2="248" y2="105" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="170" y1="155" x2="248" y2="135" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="450" y1="120" x2="528" y2="120" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <text x="350" y="220" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">JDBC mode: multiple pods share one scheduler — cluster lock ensures only one fires each trigger</text>
</svg>

The Scheduler fires Triggers that execute Jobs; JDBC job store enables cluster-safe, persistent scheduling.

## 5. Runnable example

```java
// QuartzSchedulerDemo.java — run with: java QuartzSchedulerDemo.java
// Demonstrates Quartz Job, JobDetail, Trigger, and Scheduler setup
// equivalent to what Spring Boot auto-configures via spring-boot-starter-quartz.

public class QuartzSchedulerDemo {

    public static void main(String[] args) {
        System.out.println("=== Quartz Scheduler Demo ===\n");
        printDependency();
        printJobExample();
        printConfigurationExample();
        printApplicationPropertiesExample();
        printDynamicScheduling();
    }

    static void printDependency() {
        System.out.println("--- pom.xml ---");
        System.out.println("""
            <dependency>
              <groupId>org.springframework.boot</groupId>
              <artifactId>spring-boot-starter-quartz</artifactId>
            </dependency>
            """);
    }

    static void printJobExample() {
        System.out.println("--- Defining a Job ---");
        System.out.println("""
            // Quartz Job — Spring beans can be @Autowired:
            @Component
            public class DailyReportJob implements Job {
                // Spring Boot's auto-config wires this via SpringBeanJobFactory:
                @Autowired private ReportService reportService;
                @Autowired private EmailService emailService;

                @Override
                public void execute(JobExecutionContext ctx) throws JobExecutionException {
                    // Read data passed via JobDataMap:
                    String format = ctx.getMergedJobDataMap().getString("format");

                    try {
                        byte[] pdf = reportService.generateDailyReport(format);
                        emailService.sendReport("reports@example.com", pdf);
                        System.out.println("Daily report sent: format=" + format);
                    } catch (Exception e) {
                        throw new JobExecutionException("Report generation failed", e);
                    }
                }
            }
            """);
    }

    static void printConfigurationExample() {
        System.out.println("--- Registering Job + Trigger as Spring @Beans ---");
        System.out.println("""
            @Configuration
            public class QuartzConfig {

                @Bean
                public JobDetail dailyReportJobDetail() {
                    return JobBuilder.newJob(DailyReportJob.class)
                        .withIdentity("dailyReport", "reports")
                        .withDescription("Generate and email daily report")
                        .usingJobData("format", "PDF")
                        .storeDurably()  // keep job even when no trigger references it
                        .build();
                }

                @Bean
                public CronTrigger dailyReportTrigger(JobDetail dailyReportJobDetail) {
                    return TriggerBuilder.newTrigger()
                        .forJob(dailyReportJobDetail)
                        .withIdentity("dailyReportTrigger", "reports")
                        .withSchedule(CronScheduleBuilder
                            .cronSchedule("0 0 2 * * ?")    // 2 AM daily (6 fields: s m h d M wd)
                            .withMisfireHandlingInstructionFireAndProceed()) // catch up on misfire
                        .build();
                }

                // Simple interval trigger example:
                @Bean
                public SimpleTrigger cleanupTrigger(JobDetail cleanupJobDetail) {
                    return TriggerBuilder.newTrigger()
                        .forJob(cleanupJobDetail)
                        .withSchedule(SimpleScheduleBuilder
                            .simpleSchedule()
                            .withIntervalInHours(6)
                            .repeatForever())
                        .build();
                }
            }
            """);
    }

    static void printApplicationPropertiesExample() {
        System.out.println("--- application.properties ---");
        System.out.println("""
            # Job store type:
            spring.quartz.job-store-type=jdbc     # or MEMORY (default)

            # Auto-create QRTZ_* tables:
            spring.quartz.jdbc.initialize-schema=always

            # Cluster mode (requires JDBC store):
            spring.quartz.properties.org.quartz.jobStore.isClustered=true
            spring.quartz.properties.org.quartz.scheduler.instanceId=AUTO
            spring.quartz.properties.org.quartz.jobStore.clusterCheckinInterval=15000

            # Thread pool:
            spring.quartz.properties.org.quartz.threadPool.threadCount=5

            # Overwrite existing job definitions on startup:
            spring.quartz.overwrite-existing-jobs=true
            """);
    }

    static void printDynamicScheduling() {
        System.out.println("--- Dynamic scheduling at runtime ---");
        System.out.println("""
            // Inject and use Scheduler directly:
            @Service
            public class SchedulingService {
                @Autowired private Scheduler scheduler;

                // Create a job at runtime (e.g., user books a meeting reminder):
                public void scheduleReminder(String userId, LocalDateTime at) throws SchedulerException {
                    JobDetail job = JobBuilder.newJob(ReminderJob.class)
                        .withIdentity("reminder-" + userId)
                        .usingJobData("userId", userId)
                        .build();

                    Trigger trigger = TriggerBuilder.newTrigger()
                        .withSchedule(CronScheduleBuilder.cronSchedule(
                            toCron(at)))  // convert LocalDateTime to cron
                        .build();

                    scheduler.scheduleJob(job, trigger);
                }

                // Cancel a job:
                public void cancelReminder(String userId) throws SchedulerException {
                    scheduler.deleteJob(JobKey.jobKey("reminder-" + userId));
                }

                // List all running jobs:
                public List<JobKey> listJobs() throws SchedulerException {
                    return new ArrayList<>(scheduler.getJobKeys(GroupMatcher.anyGroup()));
                }
            }
            """);
    }
}
```

**How to run:** `java QuartzSchedulerDemo.java`

## 6. Walkthrough

- **`SpringBeanJobFactory`** — Spring Boot's auto-config replaces Quartz's default `JobFactory` with a Spring-aware one. This factory creates Job instances as Spring beans, enabling `@Autowired` inside Jobs. Without it, Quartz creates Jobs via reflection and Spring beans are not injected.
- **`storeDurably()`** — tells Quartz to keep the `JobDetail` in the store even if no trigger currently references it. Required if you want to delete a trigger (unschedule) without also deleting the Job definition.
- **`withMisfireHandlingInstructionFireAndProceed()`** — when the app was down and a trigger was missed, this instruction fires the job immediately when the scheduler comes back up and then continues the normal schedule. The alternative `DoNothing` simply skips missed firings.
- **`spring.quartz.jdbc.initialize-schema=always`** — drops and recreates Quartz tables on startup. Use `never` in production (run migrations manually) and `always` only in dev/test.
- **`instanceId=AUTO`** — in cluster mode, each Quartz instance needs a unique ID. `AUTO` generates one from the hostname + random number. The cluster lock (`QRTZ_LOCKS` table) ensures only one instance fires each trigger per interval.

## 7. Gotchas & takeaways

> **Quartz cron has 6 fields, not 5.** The standard Unix cron format is `minute hour day month weekday`. Quartz cron adds a `second` field at the start: `second minute hour day month weekday`. `"0 0 2 * * ?"` means "at 00 seconds, 00 minutes, 02:00 AM, every day, every month, any weekday". The `?` in the weekday position means "don't care" — required when day-of-month is specified.

> **`spring.quartz.overwrite-existing-jobs=true`** prevents startup errors when Job/Trigger names conflict between code and the database. In JDBC mode, triggers from a previous deployment are still in the DB; the new deployment's triggers have the same names. Without `overwrite-existing-jobs=true`, Quartz throws on startup.

- In JDBC mode with `initialize-schema=always`, use Flyway/Liquibase instead to control table creation — set `spring.quartz.jdbc.initialize-schema=never` and add Quartz's SQL scripts to your migration files.
- `scheduler.getTriggerState(triggerKey)` returns `NORMAL`, `PAUSED`, `COMPLETE`, `ERROR`, or `BLOCKED` — useful for monitoring dashboards.
- Quartz Job classes must have a no-arg constructor (Spring's factory handles dependency injection post-construction).
- For a UI: Quartz Monitor (open source) provides a web dashboard for inspecting and managing jobs.
