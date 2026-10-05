# Senior Data Engineer (10 YOE) — Master Knowledge & Interview Checklist

> A complete macro → micro topic map of what a 10-year data engineer / data platform lead is expected to know:
> SQL, data modeling, Spark, streaming, Airflow & orchestration, dbt, lakehouse table formats, warehouses,
> data quality & governance, cloud data platforms, data system design, and leadership.
> Tick `[ ]` → `[x]` as you go. Rate yourself 1–5 per macro topic and revisit weekly.

## Legend

| Tag | Meaning |
|-----|---------|
| **P0** | Must know deeply — asked in almost every senior interview. Be able to explain, whiteboard, and code it. |
| **P1** | Should know well — commonly asked, expected at 10 YOE. |
| **P2** | Awareness — know what it is, when to use it, and the trade-offs. |
| 🎯 | Frequently asked interview questions for that area |

---

## Table of Contents

**Part A — Foundations**
1. [The Data Engineering Lifecycle & Role](#1-the-data-engineering-lifecycle--role-p0)
2. [SQL Mastery](#2-sql-mastery-p0)
3. [Python (and JVM) for Data Engineering](#3-python-and-jvm-for-data-engineering-p0)
4. [Data Modeling](#4-data-modeling-p0)
5. [Storage: File Formats, Table Formats & Lakehouse](#5-storage-file-formats-table-formats--lakehouse-p0)

**Part B — Processing**
6. [Distributed Computing Fundamentals](#6-distributed-computing-fundamentals-p0)
7. [Apache Spark (Deep)](#7-apache-spark-deep-p0)
8. [Other Batch & Query Engines](#8-other-batch--query-engines-p1)
9. [Stream Processing (Kafka, Flink, Spark Streaming)](#9-stream-processing-p0)

**Part C — Orchestration, Transformation & Ingestion**
10. [Apache Airflow (Deep)](#10-apache-airflow-deep-p0)
11. [Other Orchestrators](#11-other-orchestrators-p1)
12. [dbt & the Transformation Layer](#12-dbt--the-transformation-layer-p0)
13. [Ingestion, Integration & CDC](#13-ingestion-integration--cdc-p0)
14. [Pipeline Design Patterns](#14-pipeline-design-patterns-p0)

**Part D — Serving & Storage Systems**
15. [Cloud Data Warehouses](#15-cloud-data-warehouses-p0)
16. [Real-Time OLAP & Serving Stores](#16-real-time-olap--serving-stores-p1)
17. [Source Databases & OLTP Knowledge](#17-source-databases--oltp-knowledge-p1)
18. [Analytics Engineering, Semantic Layer & BI](#18-analytics-engineering-semantic-layer--bi-p1)

**Part E — Quality, Governance & Operations**
19. [Data Quality & Observability](#19-data-quality--observability-p0)
20. [Data Governance, Security & Privacy](#20-data-governance-security--privacy-p0)
21. [DataOps, CI/CD & Engineering Practices](#21-dataops-cicd--engineering-practices-p0)
22. [Cost Management (FinOps for Data)](#22-cost-management-finops-for-data-p1)
23. [Cloud Data Platforms (AWS, GCP, Azure, Databricks, Snowflake)](#23-cloud-data-platforms-p0)
24. [Infrastructure: Docker, Kubernetes, IaC](#24-infrastructure-docker-kubernetes-iac-p1)
25. [ML & AI Data Engineering](#25-ml--ai-data-engineering-p1)

**Part F — Architecture & System Design**
26. [Data Architecture Patterns](#26-data-architecture-patterns-p0)
27. [Data System Design Framework & Estimation](#27-data-system-design-framework--estimation-p0)
28. [Classic Data System Design Problems](#28-classic-data-system-design-problems-p0)
29. [General Distributed Systems & Backend Knowledge](#29-general-distributed-systems--backend-knowledge-p1)

**Part G — Coding Interviews**
30. [SQL Interview Problems](#30-sql-interview-problems-p0)
31. [Python & PySpark Coding](#31-python--pyspark-coding-p0)
32. [DSA for Data Engineers](#32-dsa-for-data-engineers-p1)

**Part H — Leadership, Behavioral & Career**
33. [Technical Leadership for Data Teams](#33-technical-leadership-for-data-teams-p0)
34. [Behavioral Interviews & Story Bank](#34-behavioral-interviews--story-bank-p0)
35. [Project Deep-Dive, Resume & Negotiation](#35-project-deep-dive-resume--negotiation-p0)
36. [Interview Formats](#36-interview-formats)

**Part I — Execution**
37. [Rapid-Fire Questions (Top 100)](#37-rapid-fire-questions-top-100)
38. [12-Week Preparation Plan](#38-12-week-preparation-plan)
39. [Resources](#39-resources)
40. [Final Readiness Checklist](#40-final-readiness-checklist)

---

# PART A — FOUNDATIONS

## 1. The Data Engineering Lifecycle & Role (P0)

- [ ] **Lifecycle** — generation (sources) → ingestion → storage → transformation → serving (analytics, ML, reverse ETL)
- [ ] **Undercurrents** — security, data management, DataOps, data architecture, orchestration, software engineering
- [ ] **Roles & boundaries** — data engineer vs analytics engineer vs data analyst vs data scientist vs ML engineer vs platform engineer; what a senior/lead DE owns
- [ ] **Data platform evolution** — on-prem EDW (Teradata, Oracle) → Hadoop era → cloud warehouses → lakehouse → real-time & AI-ready platforms; "modern data stack" and its consolidation
- [ ] **Batch vs streaming vs micro-batch** — latency, cost, complexity trade-offs; when real-time is actually needed
- [ ] **ETL vs ELT** (and EtLT) — why ELT dominates with cloud warehouses; where ETL still makes sense (PII stripping, heavy transforms, streaming)
- [ ] **OLTP vs OLAP** — workloads, row vs column storage, normalization vs denormalization
- [ ] **Data consumers** — BI/dashboards, ad hoc analysis, ML features & training, operational/reverse ETL, data products & APIs, LLM/RAG applications
- [ ] **Data SLAs** — freshness, completeness, accuracy, availability; data as a product

---

## 2. SQL Mastery (P0)

> SQL is the #1 tested skill in data engineering interviews. You should be *fast* and *correct*.

### 2.1 Core SQL
- [ ] **Logical query processing order** — FROM/JOIN → WHERE → GROUP BY → HAVING → SELECT → window functions → DISTINCT → ORDER BY → LIMIT (why you can't use a SELECT alias in WHERE)
- [ ] **Joins** — inner, left/right/full outer, cross, self, **semi-joins** (`EXISTS`/`IN`), **anti-joins** (`NOT EXISTS`, `LEFT JOIN … IS NULL`, `NOT IN` NULL trap), non-equi joins, range joins, join fan-out (row explosion) detection
- [ ] **Aggregations** — `GROUP BY`, `HAVING`, `COUNT(*)` vs `COUNT(col)` vs `COUNT(DISTINCT)`, conditional aggregation (`SUM(CASE WHEN …)`, `FILTER (WHERE …)`), `GROUPING SETS`, `ROLLUP`, `CUBE`
- [ ] **Subqueries** — scalar, correlated, derived tables; **CTEs** (readability, materialization behavior differs by engine), **recursive CTEs** (hierarchies, graph traversal, date spines)
- [ ] **Window functions** (P0) — `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `NTILE`, `LAG`/`LEAD`, `FIRST_VALUE`/`LAST_VALUE` (frame gotcha), `NTH_VALUE`, aggregate windows (running totals, moving averages), **frame clauses** (`ROWS` vs `RANGE` vs `GROUPS`, `UNBOUNDED PRECEDING`), `PARTITION BY` + `ORDER BY`, `QUALIFY` (Snowflake/BigQuery/Databricks)
- [ ] **Set operations** — `UNION` vs `UNION ALL`, `INTERSECT`, `EXCEPT`
- [ ] **NULL semantics** — three-valued logic, `COALESCE`, `NULLIF`, NULLs in joins/aggregates/`NOT IN`, `IS DISTINCT FROM`
- [ ] **Data types & functions** — dates & time zones (`DATE_TRUNC`, `DATEADD`, `DATEDIFF`, timestamp vs timestamptz), strings & regex, casting pitfalls, numeric precision (DECIMAL vs FLOAT), arrays/structs/maps, **semi-structured** (JSON, `VARIANT`, `LATERAL FLATTEN`, `UNNEST`, `EXPLODE`)
- [ ] **DML** — `INSERT … SELECT`, `UPDATE … FROM`, `DELETE … USING`, **`MERGE`** (upserts, SCD2), `INSERT OVERWRITE` (partition overwrite), `CREATE TABLE AS SELECT`, idempotent DML
- [ ] **Pivoting & unpivoting** (`PIVOT`/`UNPIVOT` or conditional aggregation)
- [ ] **Sampling & approximation** — `TABLESAMPLE`, `APPROX_COUNT_DISTINCT` (HLL), approximate percentiles

### 2.2 Analytical SQL Patterns (P0)
- [ ] **Top-N per group** (ROW_NUMBER + filter / QUALIFY)
- [ ] **Deduplication** — keep latest record per key
- [ ] **Gaps & islands** — consecutive days/streaks, session detection
- [ ] **Sessionization** — new session when gap > 30 min (LAG + running SUM)
- [ ] **Running totals, moving averages, cumulative distinct counts**
- [ ] **Retention & cohort analysis**, funnel analysis, DAU/WAU/MAU, churn
- [ ] **Year-over-year / period-over-period** comparisons
- [ ] **Median & percentiles**
- [ ] **Date spines** & filling missing dates
- [ ] **SCD Type 2 queries** — point-in-time joins (`valid_from <= ts < valid_to`)
- [ ] **Event attribution** — first/last touch
- [ ] **Hierarchy traversal** with recursive CTEs
- [ ] **Overlapping intervals**, interval merging in SQL

### 2.3 Query Performance (P0)
- [ ] **Reading execution plans** — `EXPLAIN`/`EXPLAIN ANALYZE` (Postgres), Snowflake query profile, BigQuery execution details, Spark `explain()`/UI
- [ ] **OLTP indexing** — B-tree, composite & leftmost prefix, covering indexes, selectivity
- [ ] **OLAP optimization** — partition pruning, clustering/sort keys, column pruning (avoid `SELECT *`), predicate pushdown, join order & broadcast, avoiding exploding joins, pre-aggregation, materialized views, result caching, approximate functions
- [ ] **Anti-patterns** — functions on partition/filter columns, `DISTINCT` to hide bad joins, `OR` conditions defeating pruning, cross joins, correlated subqueries per row, `ORDER BY` without `LIMIT` on huge sets

### 🎯 Frequently Asked
- Second-highest salary per department; top 3 products per category
- Find users who logged in 3+ consecutive days
- Sessionize clickstream events with a 30-minute inactivity rule
- Compute 7-day rolling average and month-over-month growth
- Deduplicate a table keeping the latest record per id
- Why is my query slow? Walk through the plan

---

## 3. Python (and JVM) for Data Engineering (P0)

### 3.1 Core Python
- [ ] Data structures & complexity (list, dict, set, deque, heapq, Counter, defaultdict), comprehensions, generators/iterators for **streaming large files**, context managers, decorators, closures, exceptions, type hints, dataclasses/Pydantic, `pathlib`, `datetime`/`zoneinfo` (time zones!), `json`/`csv` modules, `itertools`/`functools`, logging
- [ ] **Concurrency** — threads for I/O (API extraction), multiprocessing for CPU, asyncio (`aiohttp`/`httpx`) for high-concurrency API ingestion, GIL implications
- [ ] **Memory-efficient processing** — chunking, generators, streaming parsers (ijson), avoiding loading whole files
- [ ] **Packaging & environments** — venv, uv/Poetry, pyproject.toml, dependency pinning, Docker images for jobs
- [ ] **Testing** — pytest (fixtures, parametrize), mocking APIs/S3 (moto), testing transformations with small DataFrames, property-based tests (Hypothesis)
- [ ] **Code quality** — Ruff, mypy, pre-commit, modular pipeline code (not giant notebooks/scripts)

### 3.2 DataFrame & Columnar Libraries
- [ ] **pandas** — indexing, `groupby`/`merge`/`pivot_table`/`melt`, vectorization vs `apply`, dtypes & memory (categoricals, nullable dtypes, Arrow-backed dtypes in pandas 2), chunked reads, time series ops; limits (single-node, memory)
- [ ] **Polars** — lazy API & query optimization, expressions, streaming engine, performance vs pandas
- [ ] **PyArrow** — columnar memory format, Arrow tables, Parquet read/write, datasets & partitioning, zero-copy interop (pandas, Polars, DuckDB, Spark)
- [ ] **DuckDB** — in-process OLAP SQL on Parquet/CSV/DataFrames/S3; great for local transforms & testing
- [ ] **Data validation** — Pandera, Pydantic, Great Expectations

### 3.3 JVM Languages (P1)
- [ ] **Scala for Spark** — case classes, Datasets, implicits/encoders, functional collections, sbt; reading Spark source/stack traces
- [ ] **Java** for Kafka clients, Flink jobs, Beam pipelines; JVM memory & GC basics (executors are JVMs!)

### 3.4 Shell & Tooling
- [ ] Bash scripting, `grep/awk/sed/jq`, `cron`, `ssh`, Git workflows, Makefiles, Linux resource inspection (`top`, `df`, `free`, `iostat`)

---

## 4. Data Modeling (P0)

### 4.1 Fundamentals
- [ ] **Conceptual → logical → physical** models; ER diagrams; cardinality
- [ ] **Normalization** (1NF–3NF, BCNF) for OLTP; **denormalization** for analytics
- [ ] **Grain** — the single most important modeling decision ("one row per …")
- [ ] **Keys** — natural vs surrogate keys, hash keys (MD5/SHA of business keys), composite keys, key management across sources

### 4.2 Dimensional Modeling — Kimball (P0)
- [ ] **Four-step process** — choose business process → declare grain → identify dimensions → identify facts
- [ ] **Fact tables** — transaction, periodic snapshot, accumulating snapshot, factless facts; additive vs semi-additive (balances) vs non-additive (ratios) measures
- [ ] **Dimension tables** — descriptive attributes, hierarchies, conformed dimensions, role-playing dimensions (order date vs ship date), junk dimensions, degenerate dimensions (order number in fact), mini-dimensions, outrigger dimensions, bridge tables (many-to-many), date dimension
- [ ] **Slowly Changing Dimensions** — Type 0 (retain original), **Type 1** (overwrite), **Type 2** (new row with `valid_from`/`valid_to`/`is_current`), Type 3 (previous value column), Type 4 (history table), Type 6 (hybrid 1+2+3); implementing SCD2 with `MERGE`, dbt snapshots, Delta/Iceberg
- [ ] **Star vs snowflake schema**; bus matrix; enterprise data warehouse bus architecture
- [ ] **Late-arriving facts & dimensions** (inferred members), early-arriving facts
- [ ] **Surrogate key pipelines**, unknown/default members (`-1` keys)

### 4.3 Other Modeling Approaches (P1)
- [ ] **Inmon** — Corporate Information Factory, normalized EDW + data marts; Kimball vs Inmon debate
- [ ] **Data Vault 2.0** — hubs (business keys), links (relationships), satellites (descriptive history), hash keys, insert-only, auditability; raw vault vs business vault; when it fits (many sources, heavy change, regulated)
- [ ] **One Big Table (OBT) / wide denormalized tables** — columnar engines make them practical; trade-offs
- [ ] **Activity Schema**, entity-centric modeling, **anchor modeling** (awareness)
- [ ] **Medallion architecture** — bronze (raw), silver (cleaned/conformed), gold (business-level aggregates/marts)
- [ ] **Event data modeling** — event tables, event schemas & tracking plans, sessionization, user stitching/identity resolution
- [ ] **Modeling for NoSQL/streaming** — access-pattern-driven, nested/repeated fields (BigQuery STRUCT/ARRAY), denormalized events
- [ ] **Metrics/semantic modeling** — measures, dimensions, entities (dbt Semantic Layer/MetricFlow, Cube, LookML)

### 🎯 Frequently Asked
- Design a dimensional model for an e-commerce/ride-sharing/subscription business
- What's the grain of your fact table and why?
- Implement SCD Type 2 — schema and MERGE logic
- Kimball vs Inmon vs Data Vault — when each?
- How do you handle late-arriving dimensions?

---

## 5. Storage: File Formats, Table Formats & Lakehouse (P0)

### 5.1 File Formats
- [ ] **Row-based** — CSV (quoting, encodings, no schema), JSON/JSONL (schema drift), **Avro** (row-based binary, schema with data, great for Kafka & schema evolution)
- [ ] **Columnar** — **Parquet** (P0): row groups → column chunks → pages; encodings (dictionary, RLE, bit-packing, delta); min/max statistics & **predicate pushdown**; column pruning; nested data (Dremel repetition/definition levels); page index & Bloom filters; ideal file sizes (128 MB–1 GB); **ORC** (stripes, indexes; Hive ecosystem)
- [ ] **Compression codecs** — Snappy (fast), Zstd (best balance), Gzip (not splittable for raw text), LZ4, Brotli; splittability
- [ ] **Arrow** (in-memory columnar, not a storage format), Arrow Flight (transport)
- [ ] **Format choice** — ingestion/landing (JSON/Avro/CSV) vs analytics (Parquet) vs streaming (Avro/Protobuf)

### 5.2 Data Lake Fundamentals
- [ ] **Object storage** — S3/GCS/ADLS Gen2: durability, consistency (S3 strong read-after-write), request rate limits per prefix, listing costs, storage classes & lifecycle policies
- [ ] **Partitioning** — Hive-style `dt=2025-01-01/`, choosing partition columns (low/medium cardinality, query filters), **over-partitioning** pitfalls
- [ ] **Bucketing** (hash) for joins
- [ ] **Small files problem** — causes (streaming, over-partitioning, many small appends), impact (metadata, task overhead), fixes (compaction, coalescing writes, optimize write)
- [ ] **Data lake problems** that table formats solve — no ACID, no schema enforcement, consistency during writes, no updates/deletes, expensive listing, "data swamp"

### 5.3 Open Table Formats (P0)
- [ ] **Why table formats** — ACID transactions on object storage, schema evolution, time travel, efficient metadata/pruning, updates/deletes/merges, concurrent writers
- [ ] **Apache Iceberg** (P0) — metadata layers (catalog pointer → metadata.json → manifest list → manifests → data files), snapshots, **hidden partitioning** (transforms: day/hour/bucket/truncate), **partition evolution**, schema evolution by column IDs, time travel & rollback, `MERGE INTO`, copy-on-write vs merge-on-read (delete files: positional/equality; deletion vectors in v3), compaction (`rewrite_data_files`), snapshot expiry & orphan file cleanup, branching & tagging (WAP), **catalogs** (REST catalog, AWS Glue, Hive Metastore, Nessie, **Apache Polaris**, Unity Catalog, S3 Tables), multi-engine support (Spark, Flink, Trino, Snowflake, BigQuery, Athena, DuckDB), Iceberg v3 spec (variant type, row lineage, deletion vectors)
- [ ] **Delta Lake** (P0) — transaction log (`_delta_log` JSON commits + Parquet checkpoints), optimistic concurrency, `OPTIMIZE` (bin-packing), **Z-ORDER** vs **Liquid Clustering**, **deletion vectors**, `VACUUM` (retention & time travel trade-off), schema enforcement & evolution (`mergeSchema`), **Change Data Feed**, time travel, `MERGE`, generated columns, constraints, **UniForm** (Iceberg/Hudi compatibility), Delta Kernel
- [ ] **Apache Hudi** — Copy-on-Write vs Merge-on-Read tables, record keys & indexes, upserts-heavy & CDC workloads, incremental queries, timeline, compaction/clustering
- [ ] **Comparisons** — Iceberg vs Delta vs Hudi: ecosystem, engine support, governance, upsert performance, streaming; industry convergence toward Iceberg interoperability; Apache XTable (format translation)
- [ ] **Table maintenance** — compaction, clustering/sorting, snapshot expiration, orphan files, manifest rewriting, statistics; scheduling maintenance jobs

### 5.4 Catalogs & Metastores
- [ ] **Hive Metastore** (legacy standard), **AWS Glue Data Catalog**, **Databricks Unity Catalog** (open-sourced), **Apache Polaris**, Nessie (git-like), **Snowflake Horizon/Open Catalog**, Gravitino; technical catalogs vs business data catalogs (§20)

### 5.5 Lake vs Warehouse vs Lakehouse
- [ ] **Data warehouse** (structured, SQL, performance, governance, proprietary storage) vs **data lake** (cheap, any data, schema-on-read, weaker governance) vs **lakehouse** (open table formats + warehouse-like features on lake storage)
- [ ] Separation of storage and compute; open formats & avoiding lock-in; multi-engine architectures

### 🎯 Frequently Asked
- Why Parquet over CSV/JSON? How does predicate pushdown work?
- What is the small files problem and how do you fix it?
- Iceberg vs Delta vs Hudi — how would you choose?
- How does Iceberg's hidden partitioning and partition evolution work?
- How does Delta Lake achieve ACID on S3?
- Z-ordering vs partitioning vs liquid clustering

---

# PART B — PROCESSING

## 6. Distributed Computing Fundamentals (P0)

- [ ] **Why distribute** — data too big for one machine, parallelism, fault tolerance
- [ ] **MapReduce model** — map, shuffle & sort, reduce; combiners; why it was slow (disk between stages)
- [ ] **HDFS** concepts — NameNode/DataNodes, blocks, replication, data locality; **YARN** (ResourceManager, NodeManager, containers)
- [ ] **Partitioning & parallelism** — partitions as units of work; partition sizing
- [ ] **Shuffles** — the most expensive operation (network + disk + serialization); how to minimize
- [ ] **Data skew** — causes (hot keys, nulls, default values), detection, mitigation (salting, broadcast, splitting hot keys, AQE)
- [ ] **Join strategies in distributed systems** — broadcast, shuffle hash, sort-merge, bucketed joins
- [ ] **Fault tolerance** — lineage-based recomputation, checkpointing, speculative execution, idempotent writes, retries
- [ ] **Exactly-once vs at-least-once** processing; idempotent sinks
- [ ] **CAP, consistency, consensus** basics (ZooKeeper/Raft) — §29
- [ ] **Scaling laws** — Amdahl's law, stragglers, coordination overhead
- [ ] **Vectorized execution & columnar processing**, code generation, MPP architectures

---

## 7. Apache Spark (Deep) (P0)

### 7.1 Architecture
- [ ] **Driver** (SparkSession/SparkContext, DAG scheduler, task scheduler) vs **executors** (JVMs running tasks, caching data) vs **cluster manager** (YARN, Kubernetes, Standalone; Mesos deprecated)
- [ ] **Deploy modes** — client vs cluster
- [ ] **Application → jobs → stages → tasks**; one task per partition; stage boundaries at shuffles
- [ ] **Lazy evaluation**; **transformations** (narrow: map/filter/union; wide: groupBy/join/distinct/repartition) vs **actions** (count, collect, write, show)
- [ ] **DAG** & lineage; recomputation on failure
- [ ] **RDD vs DataFrame vs Dataset** — why DataFrames (Catalyst, Tungsten) are preferred; when RDDs still appear
- [ ] **Spark Connect** (decoupled client-server architecture, Spark 3.4+/4.0)

### 7.2 Optimizer & Execution Engine (P0)
- [ ] **Catalyst optimizer** — parsed → analyzed → optimized logical plan → physical plans → cost model → selected physical plan; rule-based optimizations (predicate pushdown, column pruning, constant folding, filter reordering)
- [ ] **Cost-based optimization** (CBO) & table/column statistics (`ANALYZE TABLE`)
- [ ] **Tungsten** — off-heap memory, cache-aware layouts, **whole-stage code generation**
- [ ] **Adaptive Query Execution (AQE)** (default on) — dynamically coalescing shuffle partitions, converting sort-merge to broadcast joins at runtime, **skew join optimization**
- [ ] **Dynamic Partition Pruning**
- [ ] **Reading `explain()`** — `explain("formatted")`, Exchange (shuffle), BroadcastHashJoin vs SortMergeJoin, FileScan with PushedFilters/PartitionFilters
- [ ] **Photon** (Databricks native vectorized engine), Gluten/Velox, Comet (native acceleration) — awareness

### 7.3 Joins (P0)
- [ ] **Broadcast hash join** (small side < `spark.sql.autoBroadcastJoinThreshold`, default 10 MB; `broadcast()` hint), **shuffle hash join**, **sort-merge join** (default for large-large), broadcast nested loop join (non-equi), cartesian
- [ ] Join hints (`BROADCAST`, `MERGE`, `SHUFFLE_HASH`, `SHUFFLE_REPLICATE_NL`)
- [ ] **Skewed joins** — AQE skew handling, salting (add random suffix to hot keys + replicate the other side), isolating hot keys, broadcast
- [ ] **Bucketing** to avoid shuffles on repeated joins
- [ ] Join pitfalls — duplicate keys causing explosion, null keys, data type mismatches, ambiguous columns

### 7.4 Partitioning, Shuffle & Files
- [ ] **Input partitions** — `spark.sql.files.maxPartitionBytes` (128 MB), splittable formats
- [ ] **Shuffle partitions** — `spark.sql.shuffle.partitions` (default 200; tune or rely on AQE coalescing)
- [ ] **`repartition` vs `coalesce`** — full shuffle vs narrow merge; `repartitionByRange`; when to use each
- [ ] **Writing data** — `partitionBy` (directory partitioning), `bucketBy`, controlling output file count & size, `maxRecordsPerFile`, avoiding small files, dynamic partition overwrite (`spark.sql.sources.partitionOverwriteMode=dynamic`)
- [ ] **Shuffle internals** — sort-based shuffle, map output files, spill to disk, external shuffle service, push-based shuffle (awareness)

### 7.5 Memory Management & Tuning (P0)
- [ ] **Executor memory layout** — JVM heap: reserved (300 MB), **unified memory** (`spark.memory.fraction` 0.6) split into execution & storage (dynamic borrowing; `storageFraction`), user memory; **memoryOverhead** (off-heap, Python workers, native) — common cause of container kills
- [ ] **Executor sizing** — cores per executor (~4–5), memory per core, number of executors, driver sizing; fat vs thin executors; **dynamic allocation**
- [ ] **Caching/persisting** — storage levels (MEMORY_ONLY, MEMORY_AND_DISK, serialized, DISK_ONLY), when caching helps (reused DataFrames) and hurts, `unpersist`, checkpointing to cut lineage
- [ ] **Serialization** — Kryo vs Java serialization (RDDs)
- [ ] **GC tuning** basics (G1), off-heap
- [ ] **Key configs** — `spark.sql.adaptive.*`, `spark.sql.shuffle.partitions`, `spark.sql.autoBroadcastJoinThreshold`, `spark.executor.memory/cores/instances`, `spark.executor.memoryOverhead`, `spark.dynamicAllocation.*`, `spark.sql.files.maxPartitionBytes`, `spark.default.parallelism`

### 7.6 Common Failures & Debugging (P0)
- [ ] **Driver OOM** — `collect()`/`toPandas()` on big data, large broadcast, too many tasks/partitions metadata
- [ ] **Executor OOM / container killed by YARN/K8s for exceeding memory** — skewed partitions, too-large partitions, memoryOverhead (PySpark UDFs), explode/cartesian joins
- [ ] **Shuffle fetch failures**, lost executors, disk spill, long GC pauses
- [ ] **Stragglers** — skew (one task 100× longer), speculative execution
- [ ] **Spark UI** — Jobs, Stages (task duration distribution, shuffle read/write, spill), Storage, Executors (GC time, failed tasks), SQL tab (plans with metrics); Spark History Server
- [ ] **Event logs**, driver/executor logs, metrics (Prometheus sink), listeners

### 7.7 PySpark Specifics (P0)
- [ ] Architecture — Python driver ↔ JVM via **Py4J**; Python worker processes on executors
- [ ] **Python UDFs are slow** (serialization row-by-row) → prefer **built-in functions** (`pyspark.sql.functions`) → **Pandas UDFs / Arrow-optimized UDFs** (vectorized), `mapInPandas`, `applyInPandas`, Arrow-optimized Python UDFs (Spark 3.5+/4.0), Python UDTFs
- [ ] **Pandas API on Spark** (formerly Koalas)
- [ ] `toPandas()` with Arrow; avoiding driver bottlenecks
- [ ] Python data source API (Spark 4.0) — awareness
- [ ] Dependency management (zip/py-files, conda/venv packs, Docker images on K8s, Databricks libraries)

### 7.8 Spark SQL & DataFrame API Fluency
- [ ] `select`, `withColumn` (avoid long loops → `select` with list), `filter`, `groupBy().agg()`, joins, **window functions** (`Window.partitionBy().orderBy().rowsBetween()`), `explode`/`posexplode`/`inline`, `pivot`, `struct`/`array`/`map` functions, higher-order functions (`transform`, `filter`, `aggregate`), `from_json`/`to_json`/`schema_of_json`, `when/otherwise`, `coalesce`, `dropDuplicates` vs `distinct`, `approx_count_distinct`, `percentile_approx`
- [ ] **Schemas** — explicit schemas vs inference (cost & correctness), `StructType`, schema merging, `mode` for corrupt records (`PERMISSIVE`, `DROPMALFORMED`, `FAILFAST`, `_corrupt_record`)
- [ ] **Reading/writing** — Parquet, Delta, Iceberg, JDBC (partitioned reads with `partitionColumn/lowerBound/upperBound/numPartitions`, pushdown), Kafka, CSV/JSON options; save modes (append/overwrite/errorIfExists/ignore)
- [ ] **Spark 4.0 features** — ANSI SQL mode on by default, **VARIANT** type for semi-structured data, SQL scripting & pipe syntax, collation support, Spark Connect improvements, Structured Streaming state data source — awareness

### 7.9 Spark Structured Streaming (P0) — see also §9
- [ ] Micro-batch model (unbounded table), triggers (`processingTime`, `availableNow`, `once` deprecated, continuous — experimental)
- [ ] **Output modes** — append, update, complete
- [ ] **Event-time windows** & **watermarks** (late data handling, state cleanup)
- [ ] **Stateful operations** — aggregations, `dropDuplicatesWithinWatermark`, stream-stream joins (watermarks required), `flatMapGroupsWithState` → **`transformWithState`** (Spark 4.0)
- [ ] **Checkpointing** — offsets & state; recovery; changing queries & checkpoint compatibility
- [ ] **State stores** — HDFS-backed vs **RocksDB** state store
- [ ] **Exactly-once** — replayable sources + idempotent/transactional sinks; `foreachBatch` for MERGE into Delta/Iceberg & multi-sink writes
- [ ] Kafka source/sink options (`startingOffsets`, `maxOffsetsPerTrigger`, `failOnDataLoss`)
- [ ] Monitoring streaming queries (`StreamingQueryListener`, input rate vs processing rate, batch duration)

### 7.10 Testing & Development
- [ ] Unit testing transformations with local SparkSession (pytest fixtures), `chispa`/`assertDataFrameEqual` (`pyspark.testing`), small fixtures, schema assertions
- [ ] Structuring Spark code — pure transformation functions (`DataFrame → DataFrame`), `transform()` chaining, config-driven jobs, avoiding notebook-only code
- [ ] **Databricks** — clusters (all-purpose vs job), Photon, Jobs/Workflows (Lakeflow Jobs), Delta Live Tables → **Lakeflow Declarative Pipelines**, Auto Loader (`cloudFiles`), Unity Catalog, Databricks SQL warehouses, serverless compute, Asset Bundles (DABs) for CI/CD, notebooks vs repos
- [ ] **Spark on Kubernetes** — spark-submit to K8s, Spark Operator, dynamic allocation with shuffle tracking, node pools/spot instances; **EMR** (EC2/EKS/Serverless), **Dataproc**, **Synapse/Fabric Spark**, AWS Glue (Spark-based)

### 🎯 Frequently Asked — Spark
- Explain Spark architecture and what happens when you run an action
- Narrow vs wide transformations; what is a stage?
- How do you handle data skew? Explain salting
- Broadcast vs sort-merge join — when does Spark choose each?
- `repartition` vs `coalesce`
- What is AQE and what does it optimize?
- Your job fails with executor OOM — walk through debugging
- How do you size executors for a 2 TB job?
- Why are Python UDFs slow? Alternatives?
- How do you avoid small files when writing?
- `cache()` vs `persist()` vs `checkpoint()`
- How does Catalyst optimize a query?

---

## 8. Other Batch & Query Engines (P1)

- [ ] **Trino / Presto** — MPP SQL engine, coordinator/workers, connectors (federated queries across Hive/Iceberg/Postgres/Kafka), in-memory pipelined execution (vs Spark's fault-tolerant stages), fault-tolerant execution mode, Starburst; **Athena** (managed Trino/Presto), when Trino vs Spark
- [ ] **Hive** (legacy SQL-on-Hadoop, Tez/LLAP), **Impala**, Pig, Sqoop, Oozie, HBase — enough to discuss Hadoop migrations
- [ ] **DuckDB / MotherDuck** — single-node analytics often beats clusters for < 1 TB; embedded transforms
- [ ] **Polars** for single-node pipelines
- [ ] **Dask** (pandas-like parallelism), **Ray** (distributed Python, Ray Data for ML/batch inference), **Daft** (multimodal data)
- [ ] **Apache Beam** — unified batch/stream model (PCollections, transforms, windowing, triggers), runners (Dataflow, Flink, Spark); **Google Dataflow** (autoscaling, streaming engine)
- [ ] **Flink batch** mode; **Apache DataFusion** (Rust query engine, used by many new systems)
- [ ] **Choosing an engine** — data size, latency, team skills, cost, ecosystem, SQL vs code

---

## 9. Stream Processing (P0)

### 9.1 Concepts (P0)
- [ ] **Streams vs tables duality**; bounded vs unbounded data
- [ ] **Event time vs processing time vs ingestion time**
- [ ] **Windows** — tumbling, sliding/hopping, session, global; window assignment & triggers
- [ ] **Watermarks** — tracking event-time progress, late data, allowed lateness, side outputs for late events
- [ ] **Out-of-order events**, reprocessing, backfills in streaming systems
- [ ] **State** — keyed state, state size growth, TTL, state backends, checkpoints/snapshots
- [ ] **Delivery & processing guarantees** — at-most/at-least/exactly-once; end-to-end exactly-once = replayable source + deterministic processing + transactional/idempotent sink
- [ ] **Backpressure** — detection & handling
- [ ] **Streaming joins** — stream-stream (windowed), stream-table (enrichment, temporal joins), lookup joins against external stores (caching, async I/O)
- [ ] **Deduplication** in streams (keyed state with TTL)
- [ ] **Lambda vs Kappa architectures**
- [ ] **When NOT to stream** — cost and complexity vs freshness needs; micro-batch/incremental batch as a middle ground

### 9.2 Apache Kafka for Data Engineers (P0)
- [ ] Architecture — brokers, topics, partitions, replication factor, ISR, leaders, **KRaft** (ZooKeeper removed in 4.0)
- [ ] Producers — keys & partitioning, `acks`, idempotence, batching/compression, ordering guarantees
- [ ] Consumers — consumer groups, partition assignment & rebalancing, offset commits, lag, `auto.offset.reset`
- [ ] Retention (time/size), **log compaction** (changelogs, latest state per key), tiered storage
- [ ] **Schema Registry** — Avro/Protobuf/JSON Schema, compatibility modes (backward/forward/full), schema evolution rules
- [ ] **Kafka Connect** — source/sink connectors (JDBC, S3, Elasticsearch, Snowflake, BigQuery, Iceberg sink), distributed mode, SMTs, error handling & DLQ
- [ ] **Debezium CDC** (§13)
- [ ] **Kafka Streams** (KStream/KTable, joins, windowing, state stores) & **ksqlDB** — awareness
- [ ] Partition count planning, hot partitions, throughput sizing, consumer parallelism
- [ ] Exactly-once semantics (transactions, `read_committed`)
- [ ] Managed options — Confluent Cloud, Amazon MSK, Redpanda (Kafka-compatible), WarpStream/Aiven/Bufstream (S3-backed diskless Kafka) — awareness
- [ ] Alternatives — **Kinesis** (shards), **Google Pub/Sub**, **Azure Event Hubs**, **Apache Pulsar**

### 9.3 Apache Flink (P0 for streaming roles)
- [ ] Architecture — JobManager, TaskManagers, task slots, parallelism, operator chaining
- [ ] **DataStream API** — sources, transformations, keyBy, process functions, timers (event-time & processing-time), side outputs, async I/O
- [ ] **Table API & Flink SQL** — dynamic tables, continuous queries, windowing TVFs, temporal joins, changelog semantics
- [ ] **State** — keyed/operator state, state backends (HashMap vs **RocksDB**; disaggregated state in Flink 2.0), state TTL, queryable state (deprecated)
- [ ] **Checkpoints vs savepoints** — Chandy-Lamport barriers, aligned vs unaligned checkpoints, incremental checkpoints, upgrading jobs with savepoints, state schema evolution
- [ ] **Exactly-once sinks** — two-phase commit sinks (Kafka transactional), idempotent upserts
- [ ] **Watermark strategies**, idleness handling, late data
- [ ] **CEP** library (pattern detection) — awareness
- [ ] **Flink CDC** connectors (database → stream pipelines)
- [ ] Deployment — Kubernetes operator, application vs session mode, autoscaling, managed (Amazon Managed Service for Apache Flink, Confluent Flink, Ververica)
- [ ] **Flink vs Spark Structured Streaming vs Kafka Streams** — latency, state handling, operational complexity, team skills

### 9.4 Streaming Ecosystem (P1)
- [ ] **Streaming databases** — Materialize, RisingWave (incremental view maintenance with SQL)
- [ ] **Real-time OLAP sinks** — Druid, Pinot, ClickHouse (§16)
- [ ] **Streaming into lakehouses** — Iceberg/Delta streaming writes, small files & compaction, Flink → Iceberg, Kafka → Iceberg (Connect sink, Confluent Tableflow)
- [ ] **Python streaming** — Bytewax, Quix Streams, Faust, PyFlink

### 🎯 Frequently Asked — Streaming
- Event time vs processing time; how do watermarks work?
- How do you achieve exactly-once end-to-end from Kafka to a warehouse?
- How do you deduplicate events in a stream?
- How do you handle late-arriving events in a windowed aggregation?
- Checkpoints vs savepoints in Flink
- Flink vs Spark Structured Streaming — which would you choose and why?
- Design a real-time fraud detection pipeline

---

# PART C — ORCHESTRATION, TRANSFORMATION & INGESTION

## 10. Apache Airflow (Deep) (P0)

### 10.1 Architecture
- [ ] **Components** — scheduler, **API server/webserver** (UI), **metadata database** (Postgres/MySQL), executor, workers, **triggerer** (deferrable tasks), **DAG processor** (parses DAG files)
- [ ] **Airflow 3** (released 2025) — **Task Execution API / Task SDK** (workers no longer talk directly to the metadata DB), **DAG versioning**, new React-based UI, **Assets** (renamed from Datasets) & **event-driven scheduling**, scheduler-managed **backfills**, remote/edge execution, removal of legacy features (SubDAGs, SLA misses replaced by deadline alerts, some context variables) — know what changed for migrations from 2.x
- [ ] **Executors** — Sequential (dev), Local, **Celery** (worker queues), **Kubernetes** (pod per task), CeleryKubernetes/multiple executors, Edge executor; trade-offs (latency, isolation, scaling, cost)

### 10.2 DAG Authoring (P0)
- [ ] **DAG, Task, Operator, Sensor, Hook, Connection, Variable, XCom, Pool, Queue**
- [ ] **TaskFlow API** (`@dag`, `@task`, automatic XComs) vs classic operators
- [ ] **Scheduling semantics** (P0) — `start_date`, `schedule` (cron, presets, timedelta, **timetables**, assets), **logical date** (formerly execution_date) & **data interval** (`data_interval_start`/`end`) — a run processes the *previous* interval; `catchup`; backfills; `max_active_runs`; time zones & DST
- [ ] **Templating** — Jinja with macros (`{{ ds }}`, `{{ data_interval_start }}`, `{{ params }}`), templated fields, rendering in UI
- [ ] **Dependencies** — `>>`/`<<`, `chain`, cross-DAG dependencies (assets preferred over `ExternalTaskSensor`), trigger rules (`all_success`, `all_done`, `one_failed`, `none_failed_min_one_success`…), branching (`@task.branch`), short-circuiting, `depends_on_past`, `wait_for_downstream`
- [ ] **Dynamic task mapping** (`expand`, `partial`) vs dynamic DAG generation (generating many DAGs from config — parsing cost)
- [ ] **Task groups** (SubDAGs removed)
- [ ] **XComs** — small metadata only (size limits, stored in DB), custom XCom backends (S3) for larger objects
- [ ] **Sensors** — poke vs reschedule mode, timeouts, **deferrable operators/sensors** (async triggers in triggerer — free up worker slots)
- [ ] **Retries** — `retries`, `retry_delay`, `retry_exponential_backoff`, `execution_timeout`; callbacks (`on_failure_callback`, `on_success_callback`), alerts (Slack/PagerDuty)
- [ ] **Pools & priority weights**, concurrency (`max_active_tasks`, `max_active_tis_per_dag`), queues for routing to worker types
- [ ] **Params** & manual triggers with config; `dag_run.conf`
- [ ] **Providers** — AWS, GCP, Azure, Databricks, Snowflake, dbt (Cosmos), Kubernetes (`KubernetesPodOperator`), Spark (`SparkSubmitOperator`), HTTP, SQL operators

### 10.3 Best Practices (P0)
- [ ] **Airflow is an orchestrator, not a processing engine** — push compute to Spark/warehouse/K8s pods; keep workers light
- [ ] **Idempotent & deterministic tasks** — rerunnable for any data interval (partition overwrite, MERGE, `DELETE`+`INSERT` for the interval) — use `data_interval_*`, never `now()`
- [ ] **No heavy top-level code** in DAG files (DB calls, API calls, large imports) — slows parsing
- [ ] **Atomic tasks** — one logical unit per task; not too granular, not monolithic
- [ ] **Secrets** — connections & variables via secrets backends (AWS Secrets Manager, Vault, GCP Secret Manager), not hardcoded
- [ ] **Isolation of dependencies** — `KubernetesPodOperator`, `@task.virtualenv`/`@task.external_python`/`@task.docker`, avoiding dependency conflicts in the Airflow image
- [ ] **Testing DAGs** — DAG integrity tests (import errors, cycles, required tags/owners), unit tests for task logic, `dag.test()`, local dev with Astro CLI/Breeze/docker compose
- [ ] **CI/CD for DAGs** — linting (Ruff with Airflow rules), tests, deploying DAG bundles (git sync, image bake, S3 sync), versioning
- [ ] **Backfill strategy** — scheduler-managed backfills, max active runs, protecting downstream systems, reprocessing windows
- [ ] **Data-aware scheduling** — assets & asset events to trigger downstream DAGs when data lands

### 10.4 Operating Airflow at Scale
- [ ] **Scaling** — scheduler HA (multiple schedulers), parsing performance (`min_file_process_interval`, DAG bundles), worker autoscaling (KEDA for Celery), K8s executor pod startup latency
- [ ] **Metadata DB health** — cleanup (`airflow db clean`), connection pooling, indexes
- [ ] **Common issues** — zombie/undead tasks, tasks stuck in queued/scheduled, scheduler lag, DAG parsing timeouts, pool starvation, sensor deadlocks, timezone confusion, catchup storms
- [ ] **Observability** — StatsD/OpenTelemetry metrics, logs to S3/Elasticsearch, task duration trends, SLA/deadline alerts, OpenLineage integration
- [ ] **Managed Airflow** — **Amazon MWAA**, **Google Cloud Composer**, **Astronomer (Astro)**; trade-offs vs self-hosted on K8s (Helm chart)
- [ ] **Multi-tenancy** — team ownership, DAG folder structure, RBAC, separate deployments vs shared

### 🎯 Frequently Asked — Airflow
- Explain Airflow architecture; what changed in Airflow 3?
- What is the logical date/data interval? Why does a daily DAG run "a day late"?
- How do you make tasks idempotent? How do you backfill 2 years safely?
- Sensors vs deferrable operators vs assets
- Why shouldn't you process data inside Airflow workers?
- How do you pass data between tasks?
- Celery vs Kubernetes executor
- Tasks stuck in queued — how do you debug?

---

## 11. Other Orchestrators (P1)

- [ ] **Dagster** — software-defined assets, asset graph, partitions & backfills, IO managers, resources, sensors/schedules, asset checks (data quality), strong local dev & testing; asset-centric vs task-centric orchestration
- [ ] **Prefect** — flows & tasks in Python, dynamic workflows, work pools, hybrid execution
- [ ] **Others** — Luigi (legacy), Argo Workflows (K8s-native), Kestra (YAML), Mage, Flyte (ML), Temporal (durable workflows), AWS Step Functions, Azure Data Factory, Google Workflows, Databricks Workflows/Lakeflow Jobs, dbt Cloud jobs, Snowflake tasks
- [ ] **Choosing an orchestrator** — asset vs task model, team skills, ecosystem, ops burden, managed options, lineage, testing, cost

---

## 12. dbt & the Transformation Layer (P0)

### 12.1 dbt Core Concepts
- [ ] **Models** — SQL (and Python) `SELECT` statements; `ref()` builds the DAG; `source()` declares raw tables
- [ ] **Materializations** — view, table, **incremental** (strategies: append, merge, delete+insert, insert_overwrite; **microbatch** for time-based batching; `is_incremental()`, `unique_key`, `on_schema_change`, late-arriving data with lookback windows), ephemeral, materialized views
- [ ] **Snapshots** — SCD Type 2 (timestamp vs check strategy), YAML-configured snapshots
- [ ] **Seeds** (small static CSVs), **analyses**, **macros** (Jinja), **packages** (dbt_utils, dbt_expectations, dbt_date, audit_helper, codegen)
- [ ] **Jinja** — control flow, `var()`, `env_var()`, `target`, adapter dispatch, run-operations
- [ ] **Tests** — generic data tests (`unique`, `not_null`, `accepted_values`, `relationships`), custom generic tests, singular tests, **unit tests** (dbt 1.8+: mock inputs → expected outputs), test severity & thresholds, `store_failures`
- [ ] **Documentation** — descriptions, `docs` blocks, lineage graph, `dbt docs generate`
- [ ] **Model contracts** (enforced column types/constraints), **model versions**, **access** (public/protected/private), groups — for data mesh & multi-project setups (dbt Mesh)
- [ ] **Exposures** (downstream dashboards/apps), **metrics & semantic layer** (MetricFlow)
- [ ] **Hooks** — `pre-hook`/`post-hook`, `on-run-start/end` (grants, maintenance)
- [ ] **Selectors & state** — `--select` syntax (`+model`, `tag:`, `path:`), `state:modified`, **`--defer`**, **slim CI**, `dbt build` (run + test in DAG order), `dbt retry`
- [ ] **Project structure** — staging (1:1 with sources, renaming/casting) → intermediate → marts (facts/dims); naming conventions; style guides
- [ ] **dbt Core vs dbt Cloud/Platform**; **dbt Fusion engine** (Rust-based, faster parsing, SQL comprehension) — awareness
- [ ] **Orchestrating dbt** — Airflow (Cosmos), Dagster (dbt assets), dbt Cloud jobs, CI pipelines
- [ ] **Performance & cost** — incremental models, clustering/partition configs per adapter, avoiding full refreshes, model timing analysis
- [ ] **Alternatives** — **SQLMesh** (virtual environments, column-level lineage, plan/apply), Dataform (BigQuery), Coalesce, stored procedures (legacy)

### 🎯 Frequently Asked — dbt
- How do incremental models work? How do you handle late-arriving data?
- How do you implement SCD2 in dbt?
- How do you structure a dbt project for 500+ models and multiple teams?
- How does slim CI work?
- What tests do you put on a fact table?

---

## 13. Ingestion, Integration & CDC (P0)

### 13.1 Batch Ingestion
- [ ] **Full vs incremental loads** — high-water mark (updated_at/id), its pitfalls (clock skew, non-monotonic updates, deletes not captured), lookback windows
- [ ] **Database extraction** — JDBC/ODBC, read replicas, parallel partitioned reads, snapshot isolation for consistency, avoiding load on OLTP
- [ ] **API ingestion** — pagination (offset/cursor/link headers), rate limits & backoff, retries, auth (OAuth, API keys), incremental cursors, schema changes, idempotent landing, async concurrency
- [ ] **File ingestion** — SFTP/S3 drops, event-driven (S3 notifications → SQS/Lambda/Auto Loader), file manifests, checksums, duplicate file detection, archive/quarantine folders, encoding & malformed records
- [ ] **Bulk loading** — `COPY INTO` (Snowflake/Redshift), BigQuery load jobs, Snowpipe (Streaming), Databricks Auto Loader, Postgres `COPY`

### 13.2 Change Data Capture (P0)
- [ ] **CDC approaches** — query-based (timestamps — misses deletes), trigger-based, **log-based** (WAL/binlog/redo log — preferred)
- [ ] **Debezium** — connectors (Postgres logical decoding/pgoutput, MySQL binlog, SQL Server, Oracle, MongoDB), initial snapshots vs streaming, change event structure (before/after/op/ts), schema changes, ordering per key, tombstones, outbox event router, Debezium Server (non-Kafka sinks)
- [ ] **Managed CDC** — AWS DMS, Google Datastream, Fivetran/HVR, Striim, Qlik Replicate, Estuary
- [ ] **Applying CDC to the lake/warehouse** — MERGE upserts, ordering by LSN/ts, handling deletes (hard vs soft), compaction, SCD2 from CDC streams, Iceberg/Delta/Hudi upserts
- [ ] **Source-side concerns** — replication slots growing (Postgres WAL retention!), binlog retention, permissions, impact on primary

### 13.3 Integration Tools
- [ ] **ELT SaaS** — Fivetran, Airbyte (open source), Stitch, Hevo; **code-first** — dlt (dlthub), Meltano/Singer taps; build vs buy trade-offs (cost per row, connector quality, control)
- [ ] **Reverse ETL** — Hightouch, Census (syncing warehouse data to CRMs/ads/ops tools); activation use cases
- [ ] **Event collection** — Segment, RudderStack, Snowplow (event tracking, schemas), first-party event pipelines
- [ ] **Data sharing** — Snowflake data sharing, Delta Sharing, BigQuery Analytics Hub, clean rooms

### 13.4 Ingestion Challenges
- [ ] **Schema drift** — detection, evolution policies (add columns automatically, alert on breaking changes), schema registries, **data contracts** with producers
- [ ] **Late & out-of-order data**, **duplicates** (dedupe keys), **backfills/replays**, **PII at ingestion** (masking/tokenizing early)
- [ ] **Exactly-once landing** — idempotent writes, file-level tracking, ingestion metadata tables (batch IDs, row counts, checksums)

---

## 14. Pipeline Design Patterns (P0)

- [ ] **Idempotency** (P0) — rerunning a pipeline for the same input produces the same output: partition overwrite, MERGE on keys, delete-then-insert per interval, deterministic transforms, no `now()`
- [ ] **Incremental processing** — watermarks/high-water marks, CDC, change feeds (Delta CDF, Iceberg incremental reads), lookback windows for late data
- [ ] **Backfills** — parameterized by date range, isolated compute, throttling, validation before swap, communicating to consumers
- [ ] **Write-Audit-Publish (WAP)** — write to staging/branch → run quality checks → atomically publish (Iceberg branches, Nessie, Delta shallow clones, staging tables + swap)
- [ ] **Atomic swaps** — build into temp table then `ALTER TABLE … SWAP`/rename, view pointer switch, blue-green tables
- [ ] **Staging → transform → publish layers**; medallion
- [ ] **Dead-letter/quarantine** for bad records; error tables with reasons; replay
- [ ] **Checkpointing & resumability** for long jobs
- [ ] **Partitioning strategy** aligned to query patterns & retention
- [ ] **Slowly changing dimensions & snapshots**
- [ ] **Late-arriving data** handling (reprocess N days, upserts)
- [ ] **Deduplication** strategies (window ROW_NUMBER, MERGE, distinct keys)
- [ ] **Data contracts** between producers and consumers
- [ ] **Metadata-driven / config-driven pipelines** (one framework, many sources)
- [ ] **Fan-in/fan-out, dependency management, SLAs & retries with backoff**
- [ ] **Anti-patterns** — non-idempotent appends, `SELECT *` from sources into marts, business logic duplicated across pipelines, giant monolithic DAGs, silent failures (no row-count checks), notebooks in production without tests

---

# PART D — SERVING & STORAGE SYSTEMS

## 15. Cloud Data Warehouses (P0)

### 15.1 Snowflake (P0 if used)
- [ ] **Architecture** — storage layer (compressed columnar **micro-partitions**, 50–500 MB uncompressed), compute layer (**virtual warehouses**, independent scaling, multi-cluster for concurrency), cloud services layer (metadata, optimizer, security)
- [ ] **Pruning** — micro-partition metadata (min/max), **clustering keys** & automatic clustering (cost!), clustering depth, search optimization service
- [ ] **Caching** — result cache (24 h), warehouse local disk cache, metadata cache
- [ ] **Time Travel** & **Fail-safe**, **zero-copy cloning** (dev/test environments, backups), UNDROP
- [ ] **Loading** — stages, `COPY INTO`, file formats, **Snowpipe** & **Snowpipe Streaming**, Kafka connector
- [ ] **Continuous pipelines** — **Streams** (CDC on tables) + **Tasks** (scheduled SQL), **Dynamic Tables** (declarative incremental pipelines)
- [ ] **Semi-structured** — `VARIANT`, `FLATTEN`, schema detection
- [ ] **Security & governance** — RBAC (role hierarchy, functional vs access roles), row access policies, masking policies, tags, secure views, network policies
- [ ] **Cost** — credits per warehouse size, auto-suspend/resume, right-sizing, query acceleration, resource monitors, serverless feature costs (clustering, MVs, Snowpipe), storage costs (time travel retention)
- [ ] **Snowpark** (Python/Java/Scala DataFrames in Snowflake), UDFs/UDTFs, stored procedures, Cortex AI functions (awareness)
- [ ] **Iceberg tables** in Snowflake, Open Catalog (Polaris), data sharing & marketplace

### 15.2 Google BigQuery (P0 if used)
- [ ] **Architecture** — Dremel execution, Colossus storage, Capacitor columnar format, Jupiter network, **slots** (units of compute), serverless
- [ ] **Pricing** — on-demand (per TB scanned) vs capacity (editions, reservations, autoscaling slots); storage (active vs long-term, logical vs physical billing)
- [ ] **Partitioning** (ingestion-time, time-unit column, integer range) & **clustering** (up to 4 columns, automatic re-clustering); `require_partition_filter`
- [ ] **Nested & repeated fields** (STRUCT/ARRAY) for denormalization; `UNNEST`
- [ ] **Loading & streaming** — load jobs (free), Storage Write API (streaming, exactly-once), BigQuery Data Transfer Service, external tables & **BigLake** (Iceberg)
- [ ] **Performance** — avoid `SELECT *`, partition filters, approximate functions, materialized views, BI Engine, search indexes, query plan explanation
- [ ] **Features** — scheduled queries, BigQuery ML, Dataform, row-level & column-level security (policy tags), authorized views, Analytics Hub

### 15.3 Amazon Redshift (P1)
- [ ] **Architecture** — leader node + compute nodes/slices, MPP, columnar storage, zone maps; **RA3** with managed storage (separates compute & storage); **Redshift Serverless**
- [ ] **Distribution styles** — KEY, EVEN, ALL, AUTO (co-locating joins, avoiding redistribution)
- [ ] **Sort keys** — compound vs interleaved; zone map pruning
- [ ] **Maintenance** — VACUUM, ANALYZE (largely automated now), WLM/auto WLM, concurrency scaling, short query acceleration
- [ ] **Loading** — `COPY` from S3 (parallel, file splitting), `UNLOAD`; **Spectrum** (query S3), zero-ETL integrations, materialized views, data sharing

### 15.4 Databricks SQL / Lakehouse Warehousing (P1)
- [ ] SQL warehouses (serverless/pro/classic), Photon, Delta tables with liquid clustering, predictive optimization, Unity Catalog governance, materialized views & streaming tables

### 15.5 Others (P2)
- [ ] **Azure Synapse / Microsoft Fabric** (OneLake, Delta-based), **ClickHouse** (as a warehouse), **Firebolt**, **StarRocks/Doris**, **Teradata/Oracle Exadata/Netezza** (legacy migrations), Postgres as a small warehouse (and its limits)

### 15.6 Warehouse Engineering Practices
- [ ] Environments (dev/stage/prod via clones/schemas), CI with ephemeral schemas
- [ ] Workload isolation (separate warehouses/reservations for ELT, BI, data science)
- [ ] Query governance — timeouts, resource monitors, query tagging for cost attribution
- [ ] Migration projects — EDW → cloud (assessment, SQL translation, data validation/reconciliation, parallel run, cutover)

### 🎯 Frequently Asked — Warehouses
- How does Snowflake separate storage and compute? What are micro-partitions?
- Partitioning vs clustering in BigQuery — how do they reduce cost?
- Redshift distribution & sort keys — how do you choose?
- How do you control warehouse costs at scale?
- Warehouse vs lakehouse — what would you choose for a new platform?

---

## 16. Real-Time OLAP & Serving Stores (P1)

- [ ] **Real-time OLAP** — **ClickHouse** (MergeTree engines, ORDER BY/primary key sparse index, partitions, materialized views, ReplacingMergeTree for dedupe, distributed tables), **Apache Druid** (segments, rollup, real-time + historical nodes), **Apache Pinot** (user-facing analytics, star-tree index, upserts), StarRocks — sub-second queries on fresh data at high concurrency
- [ ] **Serving layers** — key-value stores for features/aggregates (Redis, DynamoDB, Cassandra, Bigtable), Elasticsearch/OpenSearch for search & log analytics, Postgres for app-facing marts, caching layers, data APIs (GraphQL/REST over the warehouse; Cube)
- [ ] **Choosing a serving store** — latency, concurrency, freshness, query flexibility, cost, update patterns
- [ ] **Time-series stores** — TimescaleDB, InfluxDB, Prometheus/Mimir (metrics), QuestDB
- [ ] **Vector stores** for AI workloads (§25)
- [ ] **Graph databases** (Neo4j, Neptune) for relationship-heavy analytics — awareness

---

## 17. Source Databases & OLTP Knowledge (P1)

- [ ] **Relational internals** — B-tree indexes, transactions & isolation levels, MVCC, locking, WAL/binlog (basis of CDC), replication (physical vs logical), read replicas for extraction
- [ ] **PostgreSQL** — logical replication slots & publications (Debezium), `pg_stat_statements`, vacuum/bloat basics, partitioning
- [ ] **MySQL** — binlog formats (ROW for CDC), GTIDs, replicas
- [ ] **SQL Server/Oracle** — CDC features, LogMiner, GoldenGate (enterprise sources)
- [ ] **NoSQL sources** — MongoDB (change streams, schema variability), DynamoDB (Streams, exports to S3), Cassandra (CDC), Elasticsearch
- [ ] **SaaS sources** — Salesforce, HubSpot, Stripe, Google Ads APIs (rate limits, incremental cursors, deleted records)
- [ ] **Protecting OLTP** — extraction off replicas, throttling, off-peak windows, CDC instead of heavy queries
- [ ] **Data modeling at the source** — how app schema design (soft deletes, updated_at columns, enums, JSON blobs) affects downstream pipelines; influencing upstream teams (data contracts)

---

## 18. Analytics Engineering, Semantic Layer & BI (P1)

- [ ] **Semantic/metrics layer** — single definition of metrics (revenue, active users), dimensions, entities; dbt Semantic Layer (MetricFlow), **Cube**, LookML, AtScale, Malloy; serving metrics to BI, notebooks, apps & LLMs
- [ ] **BI tools** — Looker (LookML, PDTs), Tableau (extracts vs live), Power BI (DAX, import vs DirectQuery, semantic models), Apache Superset, Metabase, Mode/Hex, Sigma, ThoughtSpot; embedded analytics
- [ ] **Dashboard performance** — aggregate tables, extracts, caching, materialized views, OLAP stores, avoiding row-level queries on huge facts
- [ ] **Self-serve analytics** — curated marts, documentation, certified datasets, data literacy programs
- [ ] **Product analytics & experimentation data** — event schemas, identity resolution, A/B test assignment & exposure logging, metrics computation (CUPED awareness), experimentation platforms (Statsig, Eppo, GrowthBook)
- [ ] **Metric definitions governance** — ownership, change management, metric trees/KPIs

---

# PART E — QUALITY, GOVERNANCE & OPERATIONS

## 19. Data Quality & Observability (P0)

- [ ] **Dimensions of data quality** — accuracy, completeness, consistency, timeliness/freshness, validity, uniqueness, integrity
- [ ] **Where to test** — at ingestion (schema, nulls, volumes), in transformations (business rules, referential integrity, uniqueness), at publish (reconciliation against source, metric sanity), in production (anomaly detection)
- [ ] **Testing tools** — **dbt tests** & unit tests, **Great Expectations (GX)**, **Soda** (SodaCL), **Deequ/PyDeequ** (Spark), Pandera, Dagster asset checks, Elementary (dbt-native observability), DLT/Lakeflow expectations
- [ ] **Data observability platforms** — Monte Carlo, Bigeye, Metaplane, Anomalo, Sifflet; five pillars: **freshness, volume, schema, distribution, lineage**
- [ ] **Anomaly detection** — row-count deltas, null rate changes, distribution drift, seasonality-aware thresholds
- [ ] **Circuit breakers** — block publishing bad data (WAP pattern), fail fast vs warn
- [ ] **Reconciliation** — source vs target counts/sums/checksums, financial reconciliations, audit tables
- [ ] **Data contracts** — schema + semantics + SLAs agreed with producers, enforced in CI (schema registry compatibility, contract tests), ownership; tools (Data Contract CLI, dbt contracts, Gable)
- [ ] **Data SLAs/SLOs** — freshness SLOs per dataset, alerting, status pages for data, incident management for data issues
- [ ] **Root cause analysis** — lineage-driven impact analysis (upstream cause, downstream blast radius), communicating incidents to consumers
- [ ] **Data downtime** metrics — time to detection, time to resolution

### 🎯 Frequently Asked
- How do you ensure data quality across 1,000 tables?
- A dashboard shows revenue dropped 40% overnight — walk through your investigation
- What are data contracts and how would you introduce them?
- How do you prevent bad data from reaching consumers?

---

## 20. Data Governance, Security & Privacy (P0)

### 20.1 Metadata, Catalogs & Lineage
- [ ] **Data catalogs** — DataHub, OpenMetadata, Amundsen, Atlan, Collibra, Alation, Unity Catalog, Google Dataplex, AWS Glue/DataZone, Microsoft Purview; search & discovery, ownership, glossary, certification
- [ ] **Lineage** — table- and column-level; **OpenLineage** standard (Airflow, Spark, dbt integrations), Marquez; use for impact analysis, debugging, compliance
- [ ] **Metadata types** — technical, business, operational, social

### 20.2 Governance Models
- [ ] **Data ownership & stewardship**, RACI, domain ownership
- [ ] **Data mesh** — domain-oriented ownership, data as a product, self-serve data platform, federated computational governance; challenges & when it fits (large orgs); data products (SLAs, contracts, discoverability)
- [ ] **Data classification** (public/internal/confidential/restricted, PII/PHI/PCI tags) and policy automation via tags

### 20.3 Security & Access Control
- [ ] **Access control** — RBAC, ABAC (tag-based policies), least privilege, service accounts, separation of environments
- [ ] **Fine-grained security** — row-level security, column-level security, **dynamic data masking**, secure views, policy tags (BigQuery), Lake Formation permissions, Unity Catalog grants, Ranger (Hadoop)
- [ ] **Encryption** — at rest (KMS, CMKs), in transit (TLS), client-side/field-level encryption, **tokenization** & format-preserving encryption for PII, key rotation
- [ ] **Network security** — private endpoints/PrivateLink, VPC peering, IP allowlists, no public buckets
- [ ] **Secrets management** for pipelines (Vault, Secrets Manager), credential rotation
- [ ] **Auditing** — access logs, query history, CloudTrail, who-accessed-what reports

### 20.4 Privacy & Compliance
- [ ] **Regulations** — GDPR (lawful basis, minimization, right to access/erasure, data residency), CCPA/CPRA, **India DPDP Act**, HIPAA, PCI-DSS, SOX (financial data controls), industry-specific (banking/insurance)
- [ ] **Right to be forgotten in a lake** — deleting records across raw/bronze/silver/gold, backups, time travel retention (Delta `VACUUM`, Iceberg snapshot expiry), crypto-shredding (per-user keys), deletion pipelines & audit trails
- [ ] **Anonymization vs pseudonymization**, k-anonymity, differential privacy (awareness), synthetic data
- [ ] **Data retention policies** & lifecycle management
- [ ] **Consent management** propagation into data pipelines

### 🎯 Frequently Asked
- How do you implement GDPR deletion in a Delta/Iceberg lakehouse?
- How do you mask PII for analysts but not for the fraud team?
- What's your approach to data mesh — would you recommend it here?

---

## 21. DataOps, CI/CD & Engineering Practices (P0)

- [ ] **Version control everything** — pipelines, SQL/dbt, DAGs, infrastructure, schemas
- [ ] **Environments** — dev/staging/prod data isolation, zero-copy clones, sampled data for dev, branch-based environments (lakeFS, Nessie, Iceberg branches, Databricks/Snowflake clones, SQLMesh virtual environments)
- [ ] **CI for data** — linting (SQLFluff, Ruff), unit tests (PySpark/dbt unit tests), data diff (Datafold, `data-diff` concepts), slim CI with state comparison, schema compatibility checks, DAG integrity tests
- [ ] **CD** — deploying DAGs, dbt projects, Spark jobs (artifacts/images), Databricks Asset Bundles, Terraform for infra; blue-green tables; rollbacks
- [ ] **Testing pyramid for data** — unit tests of transforms → integration tests on sample data → data quality tests in prod → reconciliation
- [ ] **Code quality** — modular reusable transformations, configuration over code duplication, code review standards for SQL & pipelines, documentation
- [ ] **Monitoring & alerting** — job failures, durations, SLA misses, data quality checks, cost anomalies; on-call for data platforms; runbooks
- [ ] **Incident management for data** — severity, communication to stakeholders, backfill & correction plans, postmortems
- [ ] **Reproducibility** — pinned dependencies, deterministic transforms, immutable raw data, recomputability from bronze

---

## 22. Cost Management (FinOps for Data) (P1)

- [ ] **Cost drivers** — compute (warehouse credits, cluster hours, slots), storage (including time travel/versions/snapshots), data transfer (cross-region/egress, NAT gateways), API/LIST requests on object storage, managed service fees (per-row ELT pricing), observability tooling
- [ ] **Compute optimization** — right-sizing warehouses/clusters, auto-suspend, autoscaling, **spot/preemptible instances** for Spark, job clusters vs all-purpose, Photon/serverless trade-offs, scheduling off-peak, eliminating unused pipelines/tables
- [ ] **Query optimization** — partition pruning, clustering, incremental models, avoiding full refreshes, materializing hot aggregates, result caching
- [ ] **Storage optimization** — compression, file compaction, lifecycle tiers (S3 IA/Glacier), retention policies, vacuuming old versions, dropping unused tables
- [ ] **Attribution & governance** — query tags, labels per team/pipeline, chargeback/showback, budgets & alerts, resource monitors, cost dashboards
- [ ] **Have a cost story** — "reduced Snowflake/Databricks spend by X% through Y"

---

## 23. Cloud Data Platforms (P0)

### 23.1 AWS
- [ ] **Storage** — S3 (partitioning layouts, prefixes, lifecycle, S3 Tables for Iceberg, event notifications), Lake Formation (permissions, governed tables)
- [ ] **Processing** — **AWS Glue** (Spark ETL jobs, crawlers, Data Catalog, DynamicFrames, job bookmarks, Glue Data Quality), **EMR** (on EC2, EKS, Serverless), **Athena** (Trino-based, per-TB pricing, CTAS, Iceberg support), Lambda (light transforms), Batch
- [ ] **Warehousing** — Redshift (provisioned/Serverless, Spectrum, zero-ETL)
- [ ] **Streaming** — Kinesis Data Streams, Amazon Data Firehose (delivery to S3/Redshift/Iceberg), MSK, Managed Service for Apache Flink
- [ ] **Orchestration** — MWAA, Step Functions, EventBridge (schedules & events)
- [ ] **Ingestion** — DMS (CDC), AppFlow, Transfer Family (SFTP), DataSync
- [ ] **Other** — QuickSight, SageMaker (Unified Studio), DataZone, IAM (roles for jobs, cross-account access), KMS, VPC endpoints, CloudWatch

### 23.2 GCP
- [ ] GCS, **BigQuery**, **Dataflow** (Beam), **Dataproc** (Spark/Hadoop, Serverless), **Pub/Sub**, **Cloud Composer** (Airflow), **Datastream** (CDC), Dataplex (governance), Dataform, Data Fusion, Bigtable, Spanner, Looker, Vertex AI

### 23.3 Azure
- [ ] ADLS Gen2 (hierarchical namespace), **Azure Data Factory** (pipelines, copy activity, mapping data flows, integration runtimes), **Azure Databricks**, **Synapse Analytics**, **Microsoft Fabric** (OneLake, lakehouse, warehouse, Data Factory, Real-Time Intelligence), Event Hubs, Stream Analytics, Purview, Cosmos DB, Power BI

### 23.4 Databricks Platform (P0 if used)
- [ ] Workspaces, clusters & policies, jobs/workflows, notebooks vs repos/Git folders, **Unity Catalog** (metastore, catalogs/schemas, grants, lineage, volumes, external locations), **Delta Lake**, Auto Loader, Lakeflow Declarative Pipelines (formerly DLT: expectations, streaming tables, materialized views), Lakeflow Connect (ingestion), Photon, serverless, SQL warehouses, Databricks Asset Bundles, MLflow, Mosaic AI, cost controls (cluster policies, tags)

### 23.5 Snowflake Platform
- [ ] (See §15.1) plus Snowpark Container Services, Openflow (ingestion), native apps, Cortex — awareness

### 23.6 Multi-Cloud & Portability
- [ ] Open formats (Parquet/Iceberg) for portability, egress costs, governance across clouds, choosing a primary platform

---

## 24. Infrastructure: Docker, Kubernetes, IaC (P1)

- [ ] **Docker** — images for pipeline jobs, multi-stage builds, dependency pinning, small images, running Spark/Python jobs in containers
- [ ] **Kubernetes for data** — Spark on K8s (Spark Operator), Flink K8s Operator, Airflow on K8s (Helm chart, KubernetesExecutor, KubernetesPodOperator), Trino on K8s; node pools (spot for batch), autoscaling (Karpenter, KEDA), resource requests/limits for JVM jobs, persistent volumes for state, namespaces & quotas
- [ ] **Infrastructure as Code** — Terraform (providers for AWS/GCP/Azure/Snowflake/Databricks), modules, state management, environments; Pulumi/CDK
- [ ] **Networking basics** — VPCs, private subnets, NAT costs, PrivateLink to SaaS (Snowflake/Databricks), DNS, firewall rules
- [ ] **Linux & JVM basics** — resource monitoring, JVM heap/GC (Spark executors, Kafka, Flink, Trino are JVMs)
- [ ] **CI/CD tooling** — GitHub Actions/GitLab CI/Jenkins, artifact registries

---

## 25. ML & AI Data Engineering (P1)

- [ ] **ML data lifecycle** — data collection, labeling, feature engineering, training datasets, validation, serving, monitoring, feedback loops
- [ ] **Feature stores** — Feast, Tecton, Databricks Feature Store, SageMaker Feature Store, Vertex Feature Store; offline vs online store, **point-in-time correct joins** (avoiding label leakage), feature freshness, training-serving skew
- [ ] **Training data pipelines** — reproducible snapshots (time travel/versioning), dataset versioning (DVC, lakeFS, Delta/Iceberg versions), sampling, splitting, class balance
- [ ] **ML orchestration & tracking** — MLflow (tracking, model registry), Kubeflow Pipelines, SageMaker Pipelines, Vertex AI Pipelines, Metaflow, Flyte
- [ ] **Batch & streaming inference pipelines** — scoring in Spark (Pandas UDFs), Ray Data batch inference, writing predictions back, monitoring drift
- [ ] **Data for GenAI/RAG** — unstructured data ingestion (PDFs, HTML, docs), parsing & chunking, **embedding pipelines** (batch & incremental refresh), vector stores (pgvector, Databricks Vector Search, OpenSearch, Pinecone), metadata & access-control propagation, freshness & deletes, evaluation datasets
- [ ] **LLMs in data engineering** — text-to-SQL over semantic layers, LLM-powered classification/extraction in pipelines (batch inference costs, caching), AI functions in warehouses (Snowflake Cortex, Databricks AI Functions, BigQuery ML.GENERATE_TEXT), using AI coding assistants for SQL/pipelines responsibly
- [ ] **Data quality for ML** — label quality, drift detection (Evidently), data validation (TFDV/GX)

---

# PART F — ARCHITECTURE & SYSTEM DESIGN

## 26. Data Architecture Patterns (P0)

- [ ] **Enterprise data warehouse** (Kimball bus / Inmon CIF)
- [ ] **Data lake** → **lakehouse** (open table formats + catalog + multiple engines)
- [ ] **Medallion architecture** (bronze/silver/gold) — responsibilities & SLAs per layer
- [ ] **Lambda architecture** (batch + speed layers, merged views; duplicate logic problem) vs **Kappa architecture** (stream-only with replay)
- [ ] **Streaming-first / real-time architectures** — Kafka as central nervous system, stream processing, real-time OLAP, materialized views
- [ ] **Data mesh** & data products (§20.2); **data fabric** (metadata-driven integration — awareness)
- [ ] **Hub-and-spoke**, **ELT-centric modern data stack** (ingestion SaaS → warehouse → dbt → BI → reverse ETL)
- [ ] **Event-driven data architecture** — CDC + outbox from microservices, event contracts
- [ ] **Operational analytics / HTAP** — real-time serving to applications, reverse ETL
- [ ] **Composable/headless data architecture** — open storage (Iceberg) with pluggable compute engines
- [ ] **AI-ready data platforms** — unified governance for structured + unstructured, vector indexes, feature stores, semantic layers for LLMs
- [ ] **Architecture decisions** — build vs buy, open source vs managed, single platform vs best-of-breed, centralized vs federated team model; documenting with ADRs and C4 diagrams
- [ ] **Migration architectures** — on-prem Hadoop/EDW → cloud lakehouse (assessment, lift-and-shift vs re-architecture, dual running, validation, cutover, decommission)

---

## 27. Data System Design Framework & Estimation (P0)

### 27.1 Framework
- [ ] **1. Requirements** — use cases & consumers (BI, ML, product features, regulators), data sources (types, volume, velocity, variety, formats), **latency/freshness SLAs** (daily, hourly, minutes, seconds), accuracy & consistency needs, retention, compliance/PII, cost constraints, scale growth
- [ ] **2. Estimation** — events/day, bytes/event, daily/annual volume, peak throughput (events/s, MB/s), storage with compression & replication, partitions count, compute sizing
- [ ] **3. Ingestion design** — batch vs streaming vs CDC, connectors, schema management, landing zone
- [ ] **4. Storage design** — raw/immutable layer, table format, partitioning & clustering, file sizes, retention & tiering
- [ ] **5. Processing design** — engines (Spark/Flink/SQL), incremental logic, late data, dedupe, idempotency, backfills
- [ ] **6. Modeling & serving** — marts/star schemas, aggregates, serving stores (warehouse, OLAP, KV, search, APIs), semantic layer
- [ ] **7. Orchestration** — dependencies, schedules vs event-driven, retries, SLAs
- [ ] **8. Quality, governance & security** — tests, contracts, lineage, access control, PII handling, auditing
- [ ] **9. Operations** — monitoring, alerting, cost controls, failure scenarios & recovery (reprocessing from raw), DR
- [ ] **10. Trade-offs & evolution** — what changes at 10× scale, simpler alternatives

### 27.2 Estimation Cheat Sheet
- [ ] 1 day ≈ 86,400 s ≈ 10⁵ s; 1 billion events/day ≈ ~12k events/s average (peak 3–5×)
- [ ] 1 KB × 1 B events = 1 TB/day raw; Parquet + compression often 5–10× smaller
- [ ] Spark rule of thumb: ~128 MB–1 GB per partition/file; tasks ≈ data size / partition size
- [ ] Kafka: partition throughput ~10 MB/s (varies); partitions ≥ peak MB/s ÷ per-partition throughput, ≥ consumer parallelism
- [ ] Warehouse scan cost: TB scanned × price; partition pruning multiplies savings

---

## 28. Classic Data System Design Problems (P0)

> Practice each end to end aloud: requirements → estimation → architecture diagram → deep dives → failures → cost → evolution.

| # | Problem | Key deep dives |
|---|---------|----------------|
| 1 | [ ] **Batch ETL platform for e-commerce analytics** (orders, users, products → daily dashboards) | Ingestion (CDC vs extracts), dimensional model, incremental loads, SCD2, orchestration, quality checks |
| 2 | [ ] **Real-time clickstream analytics** (page views → dashboards in < 1 min) | Event collection, Kafka sizing, Flink/Spark streaming, sessionization, late data, real-time OLAP (Druid/Pinot/ClickHouse) |
| 3 | [ ] **Ad click aggregation system** (billions of clicks/day, billing-grade accuracy) | Exactly-once, dedupe, windows & watermarks, reconciliation with batch, hot keys |
| 4 | [ ] **CDC pipeline from 200 microservice databases into a lakehouse** | Debezium/Kafka Connect, schema registry, ordering, deletes, MERGE into Iceberg/Delta, compaction, monitoring replication slots |
| 5 | [ ] **Data warehouse for a ride-sharing company** | Trips fact grain, driver/rider dimensions, geospatial data, surge metrics, partitioning by time & city |
| 6 | [ ] **Metrics/KPI platform (single source of truth for company metrics)** | Semantic layer, metric governance, aggregates, serving to BI/apps/LLMs |
| 7 | [ ] **Logging & observability data pipeline** (TBs/day of logs) | Agents, Kafka buffering, hot vs cold tiers, sampling, indexing costs |
| 8 | [ ] **IoT sensor ingestion** (millions of devices) | MQTT/Kinesis, time-series storage, downsampling, out-of-order data, device metadata joins |
| 9 | [ ] **Real-time fraud detection pipeline** | Feature computation in streams, low-latency lookups, rules + ML scoring, feedback loops |
| 10 | [ ] **Feature pipeline & feature store for recommendations** | Batch + streaming features, point-in-time correctness, online/offline consistency |
| 11 | [ ] **Governed data lake for a bank** | Zones, encryption, fine-grained access, lineage, audit, GDPR/regulatory deletion, retention |
| 12 | [ ] **Deduplicating events at scale** (at-least-once sources) | Idempotency keys, state TTL, Bloom filters, MERGE-based dedupe |
| 13 | [ ] **Customer 360 / identity resolution** | Matching rules, graph-based stitching, SCD history, PII handling |
| 14 | [ ] **Top-K trending items in real time** | Count-min sketch, sliding windows, heavy hitters, serving |
| 15 | [ ] **GDPR deletion system across the lake and warehouse** | Subject request intake, discovery via catalog/lineage, deletes with table formats, backups, audit |
| 16 | [ ] **Backfill 2 years of data after a logic change** | Parameterized pipelines, compute isolation, validation, swap strategy, consumer communication |
| 17 | [ ] **Hadoop → cloud lakehouse migration** | Inventory, phased migration, HiveQL translation, data validation, dual running, cost model |
| 18 | [ ] **Multi-tenant data platform for SaaS customers** | Tenant isolation, per-tenant access, cost attribution, data sharing to customers |
| 19 | [ ] **Data quality & observability platform** | Checks framework, anomaly detection, lineage-based impact, alert routing |
| 20 | [ ] **Event tracking platform** (Segment-like) | SDKs, schema validation (tracking plans), routing to destinations, replay |
| 21 | [ ] **Near real-time inventory/order analytics for operations** | CDC, streaming joins, materialized views, serving to ops dashboards |
| 22 | [ ] **Joining two massive datasets daily** (e.g., 10 TB × 2 TB) | Join strategy, bucketing, skew handling, incremental joins |
| 23 | [ ] **Reverse ETL / data activation system** | Change detection, rate-limited syncs to SaaS APIs, idempotency, error handling |
| 24 | [ ] **Embedding/RAG ingestion pipeline for enterprise documents** | Parsing, chunking, incremental embedding refresh, ACL propagation, vector store, deletes |
| 25 | [ ] **Financial reconciliation pipeline** | Exactly-once accounting, ledgers, matching, exception workflows, auditability |
| 26 | [ ] **A/B testing / experimentation data pipeline** | Assignment & exposure logs, metric computation, sample ratio mismatch checks, latency |
| 27 | [ ] **Media/unstructured data platform** (images, video, audio metadata) | Object storage, metadata catalog, processing pipelines (Ray/Spark), search |

---

## 29. General Distributed Systems & Backend Knowledge (P1)

> Senior DEs are expected to hold their own in general backend/system discussions.

- [ ] **CAP & PACELC**, consistency models (strong, eventual, read-your-writes), replication (leader-follower, leaderless, quorums), **partitioning & consistent hashing**, consensus (Raft/ZooKeeper basics), leader election, clocks (event time vs wall clock, skew)
- [ ] **Messaging semantics** — at-least-once, idempotency, ordering, outbox pattern, DLQs
- [ ] **Caching** (Redis), **rate limiting** for API ingestion & data APIs
- [ ] **API design** — REST for data services, pagination, async jobs (202 + status), data APIs over warehouses
- [ ] **Networking basics** — DNS, TCP, HTTP, TLS, load balancers, private networking to data stores
- [ ] **Backend system design classics** (awareness) — URL shortener, rate limiter, notification system, chat — enough to discuss trade-offs
- [ ] **Observability** — logs/metrics/traces, SLOs; **security** — IAM, encryption, secrets
- [ ] **Probabilistic data structures** — Bloom filters, HyperLogLog, Count-Min Sketch, t-digest

---

# PART G — CODING INTERVIEWS

## 30. SQL Interview Problems (P0)

> Practice 100+ problems (LeetCode Database, DataLemur, StrataScratch). Aim for correctness first, then readability with CTEs, then performance.

- [ ] Nth highest value overall and per group (with ties)
- [ ] Top-N per category; second most recent purchase per user
- [ ] Deduplicate keeping latest record; find duplicate rows
- [ ] Consecutive days / streaks (gaps & islands); longest streak per user
- [ ] Sessionization with inactivity threshold
- [ ] Running totals, 7-day rolling averages, cumulative distinct users
- [ ] Day-1/Day-7/Day-30 retention; monthly cohort retention matrix
- [ ] Funnel conversion between ordered events
- [ ] DAU/WAU/MAU and stickiness ratio
- [ ] Month-over-month and year-over-year growth
- [ ] Median/percentiles without built-ins
- [ ] Users who did X but never Y (anti-join)
- [ ] Customers who bought all products in a set (relational division)
- [ ] Find overlapping/merged date ranges; hotel occupancy per day
- [ ] Pivot/unpivot (daily metrics wide ↔ long)
- [ ] SCD2 point-in-time lookups; build SCD2 from a snapshot table with MERGE
- [ ] Hierarchies with recursive CTEs (org chart depth, all reports)
- [ ] Friend recommendations / mutual friends (self-joins)
- [ ] Market basket — product pairs bought together
- [ ] Histogram/bucketing of values; fill missing dates with a date spine
- [ ] First touch / last touch attribution
- [ ] Detect anomalies vs trailing average
- [ ] Query optimization discussion — rewrite a slow query, explain partition pruning & join order

---

## 31. Python & PySpark Coding (P0)

### 31.1 Python Coding
- [ ] Parse and aggregate a large log file with generators (top IPs, error rates per minute)
- [ ] Implement a mini ETL — read CSV/JSON, validate, transform, write Parquet; handle bad records
- [ ] Flatten nested JSON; unflatten; normalize semi-structured records
- [ ] Merge intervals, sessionize events, dedupe by key keeping latest
- [ ] Top-K frequent items with heaps; streaming median
- [ ] Group by & aggregate without pandas; implement a hash join and a sort-merge join
- [ ] Paginated API ingestion with retries, backoff and rate limiting (sync & asyncio)
- [ ] Topological sort of task dependencies (DAG validation, cycle detection) — orchestrator logic
- [ ] Implement an LRU cache; a simple key-value store with TTL
- [ ] Schema inference & drift detection between two JSON batches
- [ ] Write unit tests (pytest) for your transformation functions

### 31.2 PySpark Coding
- [ ] Read with explicit schemas; handle corrupt records
- [ ] Window functions — latest record per key, running totals, lag-based session splits
- [ ] Joins — broadcast hints, skew salting implementation, anti/semi joins
- [ ] `explode` arrays / parse JSON columns / flatten structs
- [ ] Pivot & aggregate; conditional aggregation with `when`
- [ ] Deduplicate with `row_number` vs `dropDuplicates`
- [ ] Incremental MERGE into Delta/Iceberg (upserts + deletes from CDC)
- [ ] SCD2 implementation in PySpark + Delta MERGE
- [ ] Structured Streaming job — Kafka source, parse JSON, watermark, windowed aggregation, `foreachBatch` MERGE sink, checkpointing
- [ ] Optimize a given slow job — identify shuffles, skew, small files, UDFs; propose fixes
- [ ] Pandas UDF vs Python UDF vs built-ins rewrite
- [ ] Write a PySpark unit test with `assertDataFrameEqual`

---

## 32. DSA for Data Engineers (P1)

> DE loops at product/big-tech companies typically include 1 DSA round (Easy–Medium). Target **100–150 problems**.

- [ ] **Core** — arrays & strings, hash maps/sets, two pointers, sliding window, sorting, binary search, stacks/queues, heaps (top-K, merge K sorted streams), intervals, linked lists (basics), trees (traversals, BST), graphs (BFS/DFS, **topological sort** — very relevant), union-find, simple DP (climbing stairs, coin change, LIS)
- [ ] **Data-flavored problems** — merge K sorted files (external sort concept), group anagrams, top K frequent words, log rate limiter, design hit counter, time-based KV store, find median from data stream, reservoir sampling, dedupe stream with limited memory (Bloom filter concept), course schedule (DAG dependencies), meeting rooms (resource scheduling)
- [ ] **Big-O reasoning for data at scale** — external sorting, hash partitioning, when data doesn't fit in memory

---

# PART H — LEADERSHIP, BEHAVIORAL & CAREER

## 33. Technical Leadership for Data Teams (P0)

- [ ] **Platform strategy** — data platform vision & roadmap, architecture decisions (lakehouse vs warehouse, batch vs streaming, build vs buy), ADRs, standards (modeling conventions, naming, testing, SLAs), golden paths/templates for pipelines, self-serve enablement
- [ ] **Data as a product** — defining owners, SLAs, contracts, documentation, discoverability; measuring adoption & trust
- [ ] **Stakeholder management** — analysts, data scientists, product, finance, compliance, executives; prioritizing a never-ending request backlog; saying no with data; translating business questions into data products
- [ ] **Execution** — scoping migrations & platform projects, estimation, phased delivery, dependency management with source-system teams, communicating data incidents
- [ ] **Quality & reliability culture** — testing, data contracts, on-call, postmortems, SLOs for data
- [ ] **Cost ownership** — budgets, chargeback, optimization programs
- [ ] **People** — mentoring (SQL → modeling → distributed systems), code review for SQL/pipelines, hiring & interview design (SQL + modeling + design exercises), team topology (platform vs embedded/domain DEs vs analytics engineers), knowledge sharing
- [ ] **Track decision** — Staff/Principal data engineer/architect vs data engineering manager

---

## 34. Behavioral Interviews & Story Bank (P0)

### 34.1 Format
- [ ] STAR / STAR-L; 2–3 minutes; "I" not "we"; quantify (pipeline runtime −70%, cost −40%, freshness 24 h → 15 min, data incidents −80%, 500 TB migrated); show trade-offs; real failures; ready for follow-ups

### 34.2 Story Bank (15–20 stories)
- [ ] Most complex pipeline/platform you built · large migration (Hadoop/EDW → cloud, warehouse → lakehouse) · architecture decision with trade-offs (batch vs streaming, Snowflake vs Databricks) · major data incident (wrong numbers in exec dashboard, data loss, duplicate events) and recovery · failure/mistake · conflict with analysts/data scientists/source-system owners · disagree & commit · influencing without authority (data contracts with upstream teams) · mentoring · underperformer · tight deadline (regulatory report) · ambiguous requirements · pushing back on unrealistic real-time demands · convincing leadership to invest in data quality/platform · cost reduction · performance optimization with numbers · governance/compliance (GDPR deletion, PII exposure) · customer/stakeholder obsession · innovation (self-serve platform, semantic layer, AI on data) · data-driven decision · receiving critical feedback · delivering bad news (data was wrong for months) · building/hiring a team · learning a new technology fast

### 34.3 Common Questions
- [ ] Tell me about yourself (90–120 s) · **why the career break** (intentional 2–3 months of upskilling — mention what you built, e.g., a lakehouse + streaming project) · why leaving · why this company · strengths/weaknesses · greatest achievement · 5-year plan · IC vs manager · how you keep up with a fast-moving ecosystem
- [ ] Company frameworks — Amazon LPs (Dive Deep, Ownership, Insist on the Highest Standards resonate for data roles), Google, Meta; map stories to values
- [ ] Questions to ask — data platform maturity, biggest data pain points, stack & roadmap, data quality culture, team structure (central vs embedded), how data work is prioritized, on-call

---

## 35. Project Deep-Dive, Resume & Negotiation (P0)

- [ ] **Deep dives (2–3 platforms/pipelines)** — business purpose & consumers, scale (TB/day, events/s, tables, users), architecture diagram (sources → ingestion → storage → processing → serving), your role, decisions & alternatives (why Iceberg vs Delta, Airflow vs Dagster, Flink vs Spark), hardest problems (skew, late data, schema drift, cost), quality & governance approach, incidents, measurable impact, what you'd change
- [ ] **Resume** — impact bullets with numbers, keywords (Spark/PySpark, Airflow, dbt, Kafka, Flink, Snowflake/BigQuery/Databricks, Iceberg/Delta, AWS/GCP/Azure, SQL, data modeling, data quality, streaming, Terraform)
- [ ] **Portfolio** (optional) — end-to-end project: Kafka/Debezium CDC → Spark/Flink → Iceberg on S3/MinIO → dbt → DuckDB/Trino → dashboard, orchestrated by Airflow, with tests & data quality checks
- [ ] **Search & negotiation** — tiered targets, referrals, apply by week 4–6, track pipeline, research comp, negotiate level & total comp

---

## 36. Interview Formats

| Company type | Typical loop for a 10 YOE data engineer | Prep emphasis |
|--------------|-----------------------------------------|---------------|
| **Big Tech** | SQL coding · Python coding (DSA-lite) · data modeling · data system design · behavioral | SQL speed, modeling, large-scale design (e.g., Meta's DE loops are SQL + Python + product sense + modeling) |
| **Product companies / scale-ups** | SQL · PySpark/Python coding · pipeline/system design · Spark/Airflow deep dive · HM | Spark tuning, streaming, Airflow, lakehouse |
| **Data platform roles** | Distributed systems & Spark/Flink internals · platform design · infra (K8s, Terraform) | Internals, platform architecture, operations |
| **Analytics engineering-leaning roles** | SQL · dbt · dimensional modeling · stakeholder scenarios | Modeling, dbt, metrics/semantic layer |
| **Consulting / enterprises** | Cloud platform (Databricks/Snowflake/Azure) depth · migration case studies · SQL | Platform features, migrations, governance |
| **Staff/Principal** | Platform strategy · architecture review · cross-team leadership | Vision, trade-offs, influence, cost |

---

# PART I — EXECUTION

## 37. Rapid-Fire Questions (Top 100)

**Foundations & Modeling**
1. [ ] ETL vs ELT; when ETL still makes sense
2. [ ] OLTP vs OLAP; row vs columnar storage
3. [ ] Batch vs streaming — how do you decide?
4. [ ] Star vs snowflake schema
5. [ ] Fact table types; additive vs semi-additive measures
6. [ ] Grain — define it and why it matters
7. [ ] SCD types 1, 2, 3 — implement Type 2
8. [ ] Conformed dimensions; role-playing dimensions
9. [ ] Kimball vs Inmon vs Data Vault
10. [ ] Medallion architecture responsibilities
11. [ ] Late-arriving dimensions
12. [ ] Surrogate vs natural keys; hash keys

**SQL**
13. [ ] Logical query execution order
14. [ ] `ROW_NUMBER` vs `RANK` vs `DENSE_RANK`
15. [ ] Window frames: `ROWS` vs `RANGE`
16. [ ] `NOT IN` with NULLs; anti-joins
17. [ ] Gaps & islands
18. [ ] Sessionization in SQL
19. [ ] MERGE for upserts & SCD2
20. [ ] Optimizing a slow warehouse query

**Storage & Formats**
21. [ ] Parquet internals; predicate pushdown
22. [ ] Avro vs Parquet vs ORC vs JSON
23. [ ] Compression codecs & splittability
24. [ ] Partitioning strategy; over-partitioning
25. [ ] Small files problem & compaction
26. [ ] Why table formats? Iceberg vs Delta vs Hudi
27. [ ] Iceberg metadata structure & hidden partitioning
28. [ ] Delta transaction log & optimistic concurrency
29. [ ] Copy-on-write vs merge-on-read
30. [ ] Time travel & retention trade-offs (VACUUM/expire snapshots)
31. [ ] Z-order vs liquid clustering vs partitioning
32. [ ] Lake vs warehouse vs lakehouse

**Spark**
33. [ ] Driver vs executors; jobs, stages, tasks
34. [ ] Narrow vs wide transformations
35. [ ] Lazy evaluation & DAG
36. [ ] Catalyst & Tungsten
37. [ ] AQE features
38. [ ] Join strategies & broadcast threshold
39. [ ] Data skew & salting
40. [ ] `repartition` vs `coalesce`
41. [ ] `cache` vs `persist` vs `checkpoint`
42. [ ] Executor memory layout & memoryOverhead
43. [ ] Executor sizing for a given cluster
44. [ ] Driver OOM causes
45. [ ] Debugging with the Spark UI
46. [ ] Python UDF vs Pandas UDF vs built-ins
47. [ ] Shuffle partitions tuning
48. [ ] Writing partitioned output without small files
49. [ ] Dynamic partition overwrite
50. [ ] Spark vs Trino vs DuckDB — when each

**Streaming**
51. [ ] Event time vs processing time
52. [ ] Watermarks & late data
53. [ ] Window types
54. [ ] Exactly-once end to end
55. [ ] Kafka partitions, consumer groups, offsets
56. [ ] Log compaction use cases
57. [ ] Schema Registry compatibility modes
58. [ ] Debezium CDC & Postgres replication slots
59. [ ] Flink checkpoints vs savepoints
60. [ ] Flink vs Spark Structured Streaming
61. [ ] Stream-stream vs stream-table joins
62. [ ] Deduplication in streams
63. [ ] Lambda vs Kappa

**Orchestration & Transformation**
64. [ ] Airflow architecture & executors
65. [ ] Airflow 3 changes
66. [ ] Logical date / data interval semantics
67. [ ] Idempotent tasks & backfills
68. [ ] Sensors vs deferrable operators vs assets
69. [ ] XComs limits
70. [ ] Dynamic task mapping
71. [ ] Airflow vs Dagster vs Prefect
72. [ ] dbt materializations & incremental strategies
73. [ ] dbt snapshots, tests, unit tests
74. [ ] dbt slim CI with state & defer
75. [ ] Structuring a large dbt project

**Ingestion, Quality, Governance**
76. [ ] Full vs incremental loads; high-water mark pitfalls
77. [ ] Log-based vs query-based CDC
78. [ ] API ingestion with pagination & rate limits
79. [ ] Handling schema drift
80. [ ] Write-Audit-Publish
81. [ ] Data quality dimensions & tools
82. [ ] Data contracts
83. [ ] Lineage (OpenLineage) & impact analysis
84. [ ] Row-level security & masking
85. [ ] GDPR deletion in a lakehouse
86. [ ] Data mesh pros & cons

**Warehouses, Cloud & Cost**
87. [ ] Snowflake architecture & micro-partitions
88. [ ] BigQuery partitioning & clustering, slots vs on-demand
89. [ ] Redshift distribution & sort keys
90. [ ] Controlling warehouse/cluster costs
91. [ ] Glue vs EMR vs Databricks
92. [ ] Feature stores & point-in-time correctness
93. [ ] Embedding pipelines for RAG

**Design & Leadership**
94. [ ] Design a clickstream analytics platform
95. [ ] Design a CDC-to-lakehouse platform
96. [ ] Design ad click aggregation with exactly-once
97. [ ] A data incident you handled end to end
98. [ ] A migration you led
99. [ ] How you prioritize competing data requests
100. [ ] A decision that turned out wrong

---

## 38. 12-Week Preparation Plan

### Daily Template (≈ 8–9 focused hours, 6 days/week)
| Block | Time | Activity |
|-------|------|----------|
| Morning | 2 h | **SQL** — 4–6 problems (timed), review patterns |
| Late morning | 1.5 h | **Python/DSA** — 2 problems or a PySpark exercise |
| Afternoon | 2.5 h | **Core topic of the week** — read, run hands-on labs (Spark/Airflow/dbt/Kafka locally via Docker), write notes |
| Evening | 1.5 h | **Data system design** (alternate with modeling exercises / behavioral) |
| End of day | 15 min | Update checklist; Anki review |

### Week-by-Week
| Week | Core Topic | Coding | Design / Behavioral |
|------|------------|--------|---------------------|
| **1** | DE lifecycle, SQL deep (§1–2) | SQL: joins, aggregation, windows | Framework (§27); resume & intro pitch |
| **2** | Data modeling — Kimball, SCD, Data Vault (§4) | SQL: gaps & islands, sessionization; Python basics | Model e-commerce & ride-sharing warehouses |
| **3** | File & table formats, lakehouse (§5) | SQL: retention, funnels; Python generators/ETL | Lakehouse design; 5 STAR stories |
| **4** | Distributed computing & Spark architecture (§6–7.4) | PySpark transformations & windows | Batch ETL platform design; target list & referrals |
| **5** | Spark tuning, memory, debugging, PySpark (§7.5–7.10) | Skew salting, MERGE/SCD2 in PySpark | Joining huge datasets design; **start applying** |
| **6** | Streaming concepts, Kafka, Flink, Structured Streaming (§9) | Streaming job (Kafka → Spark → Delta/Iceberg) | Clickstream & ad-click designs; project deep-dive #1 |
| **7** | Airflow deep + other orchestrators (§10–11) | Build DAGs with idempotent backfills | CDC-to-lakehouse design; mocks start |
| **8** | dbt, ingestion & CDC, pipeline patterns (§12–14) | dbt project with incremental + snapshots + tests | Metrics platform design; project deep-dive #2 |
| **9** | Warehouses & serving (§15–18) | SQL optimization exercises | Fraud detection & feature store designs |
| **10** | Quality, governance, DataOps, cost (§19–22) | Great Expectations/dbt tests; Python DSA | GDPR deletion & governed lake designs; apply to dream tier |
| **11** | Cloud platforms, infra, ML/AI data (§23–25), architecture patterns (§26) | Mixed timed sets | Migration & RAG ingestion designs; negotiation prep |
| **12** | Rapid-fire 100 & revision | Mock SQL/PySpark rounds | Final mocks; rest |

### Throughout
- [ ] 10+ mocks (SQL ×3, Python/PySpark ×2, data modeling ×2, system design ×3, behavioral ×1+)
- [ ] Hands-on portfolio lab (Docker Compose: Postgres + Debezium + Kafka + Spark/Flink + MinIO/Iceberg + Trino/DuckDB + dbt + Airflow) for fresh talking points

---

## 39. Resources

### Books
- [ ] **Fundamentals of Data Engineering** — Joe Reis & Matt Housley
- [ ] **Designing Data-Intensive Applications** — Martin Kleppmann (essential)
- [ ] **The Data Warehouse Toolkit (3rd ed.)** — Ralph Kimball & Margy Ross
- [ ] **Building a Scalable Data Warehouse with Data Vault 2.0** — Linstedt & Olschimke
- [ ] **Spark: The Definitive Guide** — Chambers & Zaharia; **Learning Spark (2nd ed.)**; **High Performance Spark (2nd ed.)**
- [ ] **Streaming Systems** — Akidau, Chernyak & Lax (watermarks, windows — essential for streaming)
- [ ] **Stream Processing with Apache Flink**; **Kafka: The Definitive Guide (2nd ed.)**
- [ ] **Data Pipelines Pocket Reference** — James Densmore; **Data Pipelines with Apache Airflow (2nd ed.)**
- [ ] **Apache Iceberg: The Definitive Guide**; **Delta Lake: The Definitive Guide**
- [ ] **Data Mesh** — Zhamak Dehghani; **Data Quality Fundamentals** — Moses et al.; **Data Contracts** — Andrew Jones
- [ ] **Designing Machine Learning Systems** — Chip Huyen (for ML data)
- [ ] **SQL Performance Explained** — Markus Winand; **SQL Antipatterns**
- [ ] **The Staff Engineer's Path** — Tanya Reilly

### Online
- [ ] Official docs — Spark, Airflow, dbt (Best Practices guides), Iceberg, Delta, Kafka, Flink, Snowflake, BigQuery, Databricks
- [ ] **SQL practice** — DataLemur, StrataScratch, LeetCode Database, SQLBolt, Mode SQL tutorial
- [ ] **Courses/communities** — DataExpert.io (Zach Wilson), DataTalksClub Data Engineering Zoomcamp, Databricks Academy, Snowflake/BigQuery learning paths, Seattle Data Guy, Start Data Engineering (Joseph Machado)
- [ ] **Blogs** — Netflix, Uber, Airbnb, LinkedIn, Spotify, Pinterest, Lyft, Shopify, Meta data engineering blogs; Databricks, Snowflake, Confluent, Tabular/Iceberg blogs; Benn Stancil; Chad Sanderson (data contracts); Maxime Beauchemin's essays
- [ ] **Newsletters/podcasts** — Data Engineering Weekly, Data Engineering Podcast, Joe Reis's newsletter
- [ ] **Papers** — MapReduce, GFS, Bigtable, Dremel, Spark RDD, Kafka, MillWheel, The Dataflow Model, Lakehouse (CIDR 2021), Delta Lake (VLDB 2020), Snowflake (SIGMOD 2016), Photon

---

## 40. Final Readiness Checklist

### Interview Readiness
- [ ] 100+ SQL problems; can solve window/gaps-islands/sessionization problems in < 10 minutes
- [ ] Can design a dimensional model for any business in 20 minutes with clear grain & SCD choices
- [ ] Can explain Spark internals, tuning, skew, and memory failures with real examples
- [ ] Can explain streaming semantics (event time, watermarks, exactly-once) and Kafka/Flink internals
- [ ] Can explain Airflow scheduling semantics, idempotency, and backfills confidently
- [ ] Can compare Iceberg/Delta/Hudi and warehouses (Snowflake/BigQuery/Redshift/Databricks)
- [ ] 20+ data system designs practiced aloud with estimation
- [ ] 2–3 platform deep dives rehearsed with numbers; 15–20 STAR stories
- [ ] Rapid-fire 100 answered aloud; 10+ mocks completed

### Production-Ready Pipeline Checklist (great interview answer too)
- [ ] **Correctness** — idempotent, deterministic, handles late & duplicate data, reconciled against source
- [ ] **Quality** — schema checks, business-rule tests, freshness & volume monitoring, WAP/circuit breakers, data contracts
- [ ] **Reliability** — retries with backoff, alerting, runbooks, backfill procedures, recovery from raw data
- [ ] **Performance & cost** — partitioning/clustering, file sizing & compaction, incremental processing, right-sized compute, cost tags
- [ ] **Governance & security** — documented in catalog, lineage captured, owners & SLAs defined, PII classified/masked, least-privilege access, audit logs, retention & deletion supported
- [ ] **Engineering** — version controlled, code reviewed, unit-tested transformations, CI/CD, environments, IaC

---

> **Final advice:** At 10 YOE, data engineering interviews test **fluency** (SQL, modeling) and **judgment** (batch vs streaming, build vs buy, lake vs warehouse, cost vs freshness). For every topic, be ready to explain **what**, **how it works internally**, **when to use / not use**, **trade-offs**, and **a real production experience** — especially incidents, migrations, and cost wins.
