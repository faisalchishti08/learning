# Senior Python Backend Engineer (10 YOE) — Master Knowledge & Interview Checklist

> A complete macro → micro topic map of what a 10-year Python backend engineer / technical lead is expected to know,
> both to **clear interviews** (DSA, LLD, HLD, Python deep-dive, behavioral) and to **be** a strong senior engineer.
> Tick `[ ]` → `[x]` as you go. Rate yourself 1–5 next to each macro topic and revisit weekly.

## Legend

| Tag | Meaning |
|-----|---------|
| **P0** | Must know deeply — asked in almost every senior interview. Be able to explain, whiteboard, and code it. |
| **P1** | Should know well — commonly asked, expected at 10 YOE. |
| **P2** | Awareness — know what it is, when to use it, and the trade-offs. |
| 🎯 | Frequently asked interview questions for that area |

---

## Table of Contents

**Part A — Python Language & Runtime**
1. [Core Python Language](#1-core-python-language-p0)
2. [Python Versions & Modern Python (3.8 → 3.14)](#2-python-versions--modern-python-38--314-p0)
3. [CPython Internals, Memory & Performance Tooling](#3-cpython-internals-memory--performance-tooling-p0)
4. [Concurrency & Parallelism (GIL, threading, multiprocessing, asyncio)](#4-concurrency--parallelism-p0)
5. [Type Hints & Static Typing](#5-type-hints--static-typing-p0)

**Part B — Problem Solving**
6. [Data Structures & Algorithms in Python](#6-data-structures--algorithms-in-python-p0)
7. [OOD / LLD & Design Patterns (Pythonic)](#7-ood--lld--design-patterns-pythonic-p0)
8. [Machine Coding Round](#8-machine-coding-round-p0-for-product-companies)

**Part C — Python Backend Ecosystem**
9. [Web Fundamentals: WSGI, ASGI & App Servers](#9-web-fundamentals-wsgi-asgi--app-servers-p0)
10. [Django](#10-django-p0)
11. [Django REST Framework](#11-django-rest-framework-p0)
12. [FastAPI & Pydantic](#12-fastapi--pydantic-p0)
13. [Flask & Other Frameworks](#13-flask--other-frameworks-p1)
14. [Data Access: DB-API, SQLAlchemy, Alembic, Drivers](#14-data-access-db-api-sqlalchemy-alembic-drivers-p0)
15. [Background Jobs, Task Queues & Messaging Clients](#15-background-jobs-task-queues--messaging-clients-p0)
16. [Authentication, Authorization & Python Security](#16-authentication-authorization--python-security-p0)
17. [Testing in Python](#17-testing-in-python-p0)
18. [Packaging, Tooling, Logging & Configuration](#18-packaging-tooling-logging--configuration-p0)
19. [Python Performance Engineering](#19-python-performance-engineering-p0)
20. [Data & ML Stack Awareness for Backend Engineers](#20-data--ml-stack-awareness-p1)

**Part D — Data**
21. [SQL & Relational Databases](#21-sql--relational-databases-p0)
22. [NoSQL, Search & Storage](#22-nosql-search--storage-p0)
23. [Caching & Redis](#23-caching--redis-p0)

**Part E — Distributed Systems & Architecture**
24. [Messaging & Event Streaming](#24-messaging--event-streaming-p0)
25. [Distributed Systems Theory](#25-distributed-systems-theory-p0)
26. [Microservices, DDD & Architecture Styles](#26-microservices-ddd--architecture-styles-p0)
27. [Resilience & High Availability](#27-resilience--high-availability-p0)
28. [Rate Limiting & Throttling](#28-rate-limiting--throttling-p0)
29. [API Design (REST, gRPC, GraphQL, Real-time)](#29-api-design-p0)

**Part F — System Design (HLD)**
30. [System Design Framework & Estimation](#30-system-design-framework--estimation-p0)
31. [Building Blocks & Techniques](#31-building-blocks--techniques-p0)
32. [Classic System Design Problems](#32-classic-system-design-problems-p0)

**Part G — Infrastructure & Operations**
33. [Networking](#33-networking-p0)
34. [Linux & OS](#34-linux--os-p1)
35. [Docker & Kubernetes for Python Services](#35-docker--kubernetes-for-python-services-p0)
36. [CI/CD & IaC](#36-cicd--iac-p1)
37. [Cloud & Serverless (AWS-first)](#37-cloud--serverless-p1)
38. [Observability](#38-observability-p0)
39. [Security (Application & Infrastructure)](#39-security-p0)
40. [Production Engineering & Incidents](#40-production-engineering--incidents-p0)
41. [AI/LLM Integration for Python Backends](#41-aillm-integration-for-python-backends-p1)

**Part H — Leadership, Behavioral & Career**
42. [Technical Leadership](#42-technical-leadership-p0)
43. [Behavioral Interviews & Story Bank](#43-behavioral-interviews--story-bank-p0)
44. [Project Deep-Dive, Resume & Negotiation](#44-project-deep-dive-resume--negotiation-p0)
45. [Interview Formats](#45-interview-formats)

**Part I — Execution**
46. [Rapid-Fire Questions (Top 100)](#46-rapid-fire-questions-top-100)
47. [12-Week Preparation Plan](#47-12-week-preparation-plan)
48. [Resources](#48-resources)
49. [Final Readiness Checklist](#49-final-readiness-checklist)

---

# PART A — PYTHON LANGUAGE & RUNTIME

## 1. Core Python Language (P0)

### 1.1 Data Model & Objects
- [ ] **Everything is an object** — identity (`id`), type, value; `is` vs `==`
- [ ] **Names, binding & references** — variables are labels; assignment never copies; argument passing is "pass-by-object-reference" (call by sharing)
- [ ] **Mutable vs immutable types** — list/dict/set/bytearray vs int/str/tuple/frozenset/bytes; tuples containing mutable objects
- [ ] **Mutable default argument trap** (`def f(x=[])`) and the `None` sentinel idiom
- [ ] **Hashability** — `__hash__` + `__eq__` contract; why mutable objects aren't hashable; dataclass `frozen=True`/`unsafe_hash`
- [ ] **Truthiness** — `__bool__`, `__len__`, falsy values
- [ ] **Shallow vs deep copy** — `copy.copy`, `copy.deepcopy`, slicing, `list(x)`, `dict(x)`, `__copy__`/`__deepcopy__`
- [ ] **Interning & caching** — small int cache (−5..256), string interning, why `is` on ints/strings is unreliable
- [ ] **Dunder (magic) methods** — `__init__` vs `__new__`, `__repr__` vs `__str__`, `__eq__`/`__lt__` + `functools.total_ordering`, `__hash__`, `__len__`, `__getitem__`/`__setitem__`/`__contains__`, `__iter__`/`__next__`, `__call__`, `__enter__`/`__exit__`, `__getattr__` vs `__getattribute__`, `__setattr__`, `__del__` (and why to avoid it), arithmetic & reflected operators, `__format__`, `__class_getitem__`, `__init_subclass__`, `__set_name__`

### 1.2 Built-in Types & Operations
- [ ] **list** — dynamic array, over-allocation, O(1) append amortized, O(n) insert(0)/pop(0)
- [ ] **dict** — open-addressing hash table, insertion order preserved (3.7+), compact dict layout, key sharing dicts, view objects, `|` merge (3.9), `setdefault`, `get`, dict comprehension
- [ ] **set/frozenset** — hash set operations & complexity
- [ ] **tuple & namedtuple**, `typing.NamedTuple`
- [ ] **str** — immutable Unicode code points, `join` vs `+=` in loops, f-strings (format spec, `=` debug specifier), `str.format`, encoding/decoding, `bytes` vs `str` vs `bytearray`, `memoryview`
- [ ] **Numbers** — arbitrary-precision int, float (IEEE-754 pitfalls), `decimal.Decimal` for money (context, quantize, rounding), `fractions.Fraction`, `math.isclose`, integer division & modulo semantics with negatives
- [ ] **Slicing** — `slice` objects, negative indices, step, slice assignment
- [ ] **Unpacking** — starred assignment, `*args`/`**kwargs` unpacking in calls, nested unpacking
- [ ] **Comprehensions** — list/dict/set comprehensions, generator expressions, scope rules, nested comprehension readability
- [ ] **Walrus operator** `:=`

### 1.3 Functions
- [ ] **Parameters** — positional, keyword, default, `*args`, `**kwargs`, keyword-only (`*`), positional-only (`/`)
- [ ] **First-class functions**, higher-order functions, `lambda`, `map`/`filter`/`reduce` vs comprehensions
- [ ] **Scope — LEGB rule**, `global`, `nonlocal`, `UnboundLocalError`
- [ ] **Closures** — cell variables, late binding in loops (`lambda i=i: i` fix)
- [ ] **Decorators** — function decorators, decorators with arguments (decorator factories), class decorators, stacking order, `functools.wraps`, decorating methods, preserving signatures, real uses (retry, timing, caching, auth, registration)
- [ ] **`functools`** — `lru_cache`/`cache` (hashable args, memory, `cache_clear`), `partial`, `reduce`, `singledispatch`/`singledispatchmethod`, `cached_property`, `total_ordering`, `wraps`
- [ ] **Recursion** — default recursion limit (~1000), no tail-call optimization, iterative alternatives

### 1.4 Iterators, Generators & Context Managers
- [ ] **Iterable vs iterator protocol** — `__iter__`, `__next__`, `StopIteration`, `iter(callable, sentinel)`
- [ ] **Generators** — `yield`, lazy evaluation, memory efficiency, generator state machine, `send`, `throw`, `close`, `yield from`, generator return values
- [ ] **Generator pipelines** for streaming large files/data
- [ ] **`itertools`** — `chain`, `islice`, `groupby` (needs sorted input), `product`, `permutations`, `combinations`, `accumulate`, `count`, `cycle`, `repeat`, `tee`, `zip_longest`, `pairwise` (3.10), `batched` (3.12), `starmap`, `takewhile`/`dropwhile`
- [ ] **Context managers** — `with` protocol, exception suppression via `__exit__` return value, `contextlib.contextmanager`, `ExitStack`, `suppress`, `closing`, `nullcontext`, `redirect_stdout`, async context managers (`asynccontextmanager`)

### 1.5 Object-Oriented Python
- [ ] **Classes & instances** — class vs instance attributes (shared mutable class attribute bug), `self`, `__dict__`
- [ ] **Methods** — instance, `@classmethod` (alternate constructors), `@staticmethod`
- [ ] **Properties** — `@property`, setters/deleters, computed attributes, validation
- [ ] **Inheritance & MRO** — C3 linearization, `super()` cooperative multiple inheritance, mixins, diamond problem, `__mro__`
- [ ] **Encapsulation conventions** — `_protected`, `__private` name mangling
- [ ] **Abstract Base Classes** — `abc.ABC`, `@abstractmethod`, `collections.abc` (Iterable, Mapping, Sequence…), virtual subclasses via `register`
- [ ] **Protocols** (structural typing, `typing.Protocol`, `@runtime_checkable`) vs ABCs (nominal)
- [ ] **Duck typing**, EAFP vs LBYL
- [ ] **`__slots__`** — memory savings, no `__dict__`, inheritance caveats
- [ ] **Descriptors** — `__get__`/`__set__`/`__delete__`, data vs non-data descriptors, attribute lookup precedence; how `property`, methods (bound methods), `classmethod`, `staticmethod` and ORM fields work
- [ ] **Metaclasses** — `type` as a metaclass, `type(name, bases, dict)`, `__new__`/`__init__`/`__call__` on metaclasses, `__prepare__`; when to use (rarely — prefer `__init_subclass__`, class decorators); how Django models / SQLAlchemy declarative / Pydantic use them
- [ ] **Class creation process** end to end
- [ ] **Dataclasses** — `field(default_factory=…)`, `frozen`, `slots=True`, `kw_only`, `order`, `__post_init__`, `InitVar`, `asdict`/`replace`; dataclass vs namedtuple vs attrs vs Pydantic model vs TypedDict
- [ ] **Enums** — `Enum`, `IntEnum`, `StrEnum` (3.11), `Flag`, `auto()`, uniqueness
- [ ] **Composition over inheritance** in Python

### 1.6 Exceptions
- [ ] **Hierarchy** — `BaseException` → `Exception`; `KeyboardInterrupt`, `SystemExit`, `GeneratorExit` are not `Exception`
- [ ] `try/except/else/finally` semantics; return in `finally`
- [ ] **Exception chaining** — `raise … from err`, `raise … from None`, `__cause__` vs `__context__`
- [ ] **Custom exception hierarchies** for libraries/services
- [ ] **Exception groups & `except*`** (3.11), `add_note`
- [ ] Bare `except:` / `except Exception: pass` anti-patterns; logging with `logger.exception`
- [ ] **Warnings** module, deprecations

### 1.7 Structural Pattern Matching (3.10+)
- [ ] `match`/`case` — literal, capture, wildcard, sequence, mapping, class patterns (`__match_args__`), guards, OR patterns; when it beats if/elif

### 1.8 Modules, Packages & Imports
- [ ] Module search path (`sys.path`), `__init__.py`, namespace packages
- [ ] Absolute vs relative imports, `__all__`, `if __name__ == "__main__"`
- [ ] **Circular imports** — causes and fixes (restructure, local imports, `TYPE_CHECKING`)
- [ ] Import system internals — finders, loaders, `importlib`, module caching (`sys.modules`), `importlib.reload` caveats
- [ ] Lazy imports for startup time (PEP 810 lazy imports accepted for 3.15 — awareness)

### 1.9 Standard Library You Must Know
- [ ] **collections** — `deque`, `defaultdict`, `Counter`, `OrderedDict` (`move_to_end` → LRU), `ChainMap`, `namedtuple`
- [ ] **heapq**, **bisect**, **array**, **queue**, **weakref**
- [ ] **datetime** & **zoneinfo** (3.9) — naive vs aware datetimes, always UTC internally, DST pitfalls, `time.monotonic` vs `time.time`
- [ ] **pathlib**, **os**, **shutil**, **tempfile**, **glob**
- [ ] **json**, **csv**, **pickle** (security!), **struct**, **base64**, **hashlib**, **hmac**, **secrets**, **uuid**
- [ ] **re** — groups, named groups, non-greedy, compiled patterns, catastrophic backtracking
- [ ] **logging** (§18), **argparse**, **subprocess** (avoid `shell=True`), **signal**, **contextvars**
- [ ] **concurrent.futures**, **threading**, **multiprocessing**, **asyncio** (§4)
- [ ] **dataclasses**, **enum**, **typing**, **abc**, **functools**, **itertools**, **operator**
- [ ] **http.client**, **urllib**, **socket**, **ssl**, **email**, **sqlite3**
- [ ] **unittest/unittest.mock**, **doctest**, **timeit**, **cProfile**, **tracemalloc**, **pdb**
- [ ] **tomllib** (3.11), **graphlib** (topological sort, 3.9), **statistics**

### 1.10 Pythonic Code & Idioms
- [ ] PEP 8 style, PEP 20 (Zen of Python), PEP 257 docstrings
- [ ] EAFP, `enumerate`, `zip` (`strict=True`), `any`/`all`, `sorted(key=…)`, `dict.get`, unpacking, comprehensions, context managers, generators
- [ ] Avoiding anti-patterns — `range(len(x))`, manual index juggling, catching broad exceptions, mutable defaults, `type(x) == Y` instead of `isinstance`

### 🎯 Frequently Asked — Core Python
- Mutable default argument — what happens and why?
- Explain decorators; write a retry decorator with arguments that preserves metadata
- Generators vs lists; how do you process a 50 GB file in Python?
- What is the MRO? How does `super()` work with multiple inheritance?
- Descriptors — how does `@property` work under the hood?
- What are metaclasses and when would you actually use one?
- `__new__` vs `__init__`; `__getattr__` vs `__getattribute__`
- `is` vs `==`; shallow vs deep copy
- How is a dict implemented? Why are keys required to be hashable?
- dataclass vs Pydantic model vs TypedDict vs NamedTuple — when to use each

---

## 2. Python Versions & Modern Python (3.8 → 3.14) (P0)

| Version | Key features you should be able to explain and use |
|---------|-----------------------------------------------------|
| **3.8** | Walrus `:=`, positional-only params `/`, f-string `=` debugging, `functools.cached_property`, `typing.Protocol`/`Literal`/`Final`/`TypedDict` |
| **3.9** | Dict merge `\|`/`\|=`, generic built-ins (`list[int]`), `str.removeprefix/removesuffix`, `zoneinfo`, `graphlib`, new PEG parser |
| **3.10** | **Structural pattern matching**, `X \| Y` union types, `ParamSpec`, `TypeAlias`, better error messages, `zip(strict=True)`, `itertools.pairwise` |
| **3.11** | **10–60% faster CPython** (specializing adaptive interpreter, zero-cost exceptions), **exception groups & `except*`**, **`asyncio.TaskGroup`** & `asyncio.timeout`, `tomllib`, `Self` type, `StrEnum`, fine-grained error locations |
| **3.12** | **PEP 695 type parameter syntax** (`def f[T](x: T)`, `type Alias = …`), f-string grammar formalized (nested quotes), `@override`, per-interpreter GIL (C API), `itertools.batched`, `distutils` removed, Linux `perf` profiler support |
| **3.13** | **Free-threaded build (no-GIL, experimental, PEP 703)**, **experimental JIT** (PEP 744), new interactive REPL, `dead batteries` removed (PEP 594: `cgi`, `telnetlib`…), `copy.replace`, `warnings.deprecated`, improved error messages, iOS/Android tier-3 support |
| **3.14** | **Free-threaded build officially supported** (PEP 779), **template strings / t-strings** (PEP 750), **deferred evaluation of annotations** (PEP 649/749, `annotationlib`), **multiple interpreters in the stdlib** (`concurrent.interpreters`, PEP 734), `compression.zstd`, safe external debugger attach (PEP 768), default multiprocessing start method `forkserver` on Linux, `asyncio` introspection CLI |

- [ ] **Release cadence** — annual releases (October), ~5 years support each; know which versions are EOL (3.9 EOL Oct 2025)
- [ ] **Your upgrade story** — e.g., 3.6 → 3.11+: what broke (removed modules, asyncio API changes, dependency pins), how you tested, performance gains measured
- [ ] **Python 2 → 3 migration** knowledge (legacy codebases still exist): `unicode`/`bytes`, `print`, integer division, `six`, `2to3`
- [ ] **Free-threading implications** — C extensions must opt in, thread-safety of your own code now matters more, performance overhead on single-thread, ecosystem readiness

---

## 3. CPython Internals, Memory & Performance Tooling (P0)

### 3.1 Execution Model
- [ ] **CPython vs PyPy vs Jython vs GraalPy vs MicroPython**
- [ ] **Source → tokens → AST → bytecode (`.pyc`, `__pycache__`) → evaluation loop**; `dis` module to inspect bytecode
- [ ] **Frames & the call stack**, code objects
- [ ] **Specializing adaptive interpreter** (3.11+), quickening, inline caches
- [ ] **JIT** (copy-and-patch, experimental 3.13+) — awareness
- [ ] **Global Interpreter Lock (GIL)** — what it protects (interpreter state & refcounts), when it's released (blocking I/O, `time.sleep`, many C extensions like NumPy), switch interval (`sys.getswitchinterval`), impact on CPU-bound vs I/O-bound threads
- [ ] **Free-threaded CPython** (`python3.13t`/`3.14t`) — biased reference counting, immortal objects, per-object locks, overhead
- [ ] **Subinterpreters** — isolated interpreters with their own GIL (`concurrent.interpreters`)

### 3.2 Memory Management
- [ ] **Reference counting** — `sys.getrefcount`, immediate deallocation
- [ ] **Cyclic garbage collector** — generational collection, thresholds (`gc.get_threshold`), `gc.collect`, `gc.freeze` (pre-fork memory sharing), objects with `__del__` in cycles
- [ ] **pymalloc** — arenas, pools, blocks for small objects (≤ 512 bytes); why RSS may not shrink after freeing
- [ ] **Immortal objects** (PEP 683, 3.12)
- [ ] **`weakref`** — `WeakValueDictionary`, `WeakKeyDictionary`, `finalize`; caches without leaks
- [ ] **Object size** — `sys.getsizeof` (shallow), `__slots__` savings, `pympler`
- [ ] **Memory leaks in Python** — global caches/unbounded `lru_cache`, lingering references in closures/lists, reference cycles with `__del__`, C-extension leaks, large objects kept alive by tracebacks/exceptions, growing module-level registries, leaking Celery/Gunicorn workers → `max_requests`/`max_tasks_per_child`
- [ ] **Copy-on-write & fork** — refcount updates touching pages break CoW (why `gc.freeze` + Gunicorn `--preload` matters)

### 3.3 Diagnostic & Profiling Tools
- [ ] **CPU profiling** — `cProfile` + `pstats`/snakeviz, **py-spy** (sampling, attach to running process, flame graphs, `py-spy dump` for stack traces of stuck processes), **Scalene** (CPU + memory + GPU), `line_profiler`, **pyinstrument**, Austin, `perf` integration (3.12+)
- [ ] **Memory profiling** — `tracemalloc` (snapshots & diffs), **memray** (native allocations, flame graphs), `memory_profiler`, `objgraph` (reference graphs), `pympler`, `guppy3`
- [ ] **Debugging** — `pdb`/`breakpoint()`, `ipdb`, remote debugging (debugpy), `faulthandler` (dump tracebacks on segfault/hang), 3.14 safe remote attach
- [ ] **Benchmarking** — `timeit`, `pyperf`, `pytest-benchmark`
- [ ] **Production scenarios** — stuck worker (py-spy dump), memory growing (tracemalloc diff / memray), high CPU (py-spy top/record), slow endpoint (APM traces + profiling)

### 3.4 Speeding Up Python
- [ ] Algorithmic improvement first; built-ins & comprehensions are C-speed
- [ ] **Vectorization** — NumPy/pandas/Polars instead of Python loops
- [ ] **Native extensions** — Cython, **Rust via PyO3/maturin**, C extensions/C API, pybind11/nanobind, cffi/ctypes, **mypyc**, Numba (JIT for numeric code)
- [ ] **Alternative runtimes** — PyPy (JIT, C-extension compatibility caveats)
- [ ] **Faster libraries** — `orjson`/`msgspec` (JSON), `uvloop` (event loop), `pydantic-core` (Rust), `polars`, `httptools`

### 🎯 Frequently Asked — Internals
- What is the GIL? Why does it exist? How do you achieve parallelism despite it?
- How does Python manage memory? Reference counting vs cyclic GC
- How would you find a memory leak in a long-running Django/Celery process?
- What's changing with free-threaded Python? Would you adopt it now?
- How do you profile a slow endpoint in production without restarting it?

---

## 4. Concurrency & Parallelism (P0)

### 4.1 Choosing a Model
- [ ] **I/O-bound** → asyncio (high concurrency) or threads (simpler, blocking libraries)
- [ ] **CPU-bound** → multiprocessing / process pools, native extensions releasing the GIL, free-threaded build, or offload to workers/other services
- [ ] **Mixed** → asyncio + `run_in_executor`/`asyncio.to_thread` + process pool
- [ ] Concurrency vs parallelism; Amdahl's law; Little's law for sizing pools

### 4.2 Threading
- [ ] `threading.Thread`, daemon threads, `join`, thread-local data (`threading.local`)
- [ ] **Synchronization** — `Lock`, `RLock`, `Semaphore`/`BoundedSemaphore`, `Event`, `Condition`, `Barrier`, `Timer`
- [ ] **Which operations are atomic** under the GIL (single bytecode ops like `list.append`, `dict[k] = v`) vs not (`x += 1`, check-then-act); don't rely on GIL atomicity — especially with free-threading
- [ ] **`queue.Queue`** (thread-safe) — producer/consumer, `task_done`/`join`, `PriorityQueue`, `LifoQueue`
- [ ] **`concurrent.futures.ThreadPoolExecutor`** — `submit`, `map`, `as_completed`, `wait`, futures, exception propagation, `max_workers` sizing, shutdown
- [ ] **Deadlocks, race conditions, starvation** — detection (py-spy dump, faulthandler), lock ordering, timeouts on `acquire`

### 4.3 Multiprocessing
- [ ] `multiprocessing.Process`, `Pool` (`map`, `imap_unordered`, `apply_async`, `chunksize`), `ProcessPoolExecutor`
- [ ] **Start methods** — `fork` (fast, unsafe with threads), `spawn` (safe, slower, needs picklable targets & `if __name__ == "__main__"`), `forkserver` (default on Linux from 3.14; macOS defaults to spawn)
- [ ] **IPC** — `Queue`, `Pipe`, `Manager` (proxy objects, slow), `shared_memory` (3.8), `Value`/`Array`
- [ ] **Pickling constraints** — lambdas, local functions, large payload serialization overhead
- [ ] Memory considerations (each process has its own interpreter); `maxtasksperchild` for leaks
- [ ] **Joblib**, **Ray**, **Dask** for larger-scale parallelism (awareness)

### 4.4 asyncio Deep Dive (P0)
- [ ] **Event loop** — single-threaded cooperative multitasking, selectors (epoll/kqueue), callbacks, `asyncio.run`
- [ ] **Coroutines vs Tasks vs Futures** — `async def`, `await`, `asyncio.create_task` (keep references to avoid GC of tasks!), `asyncio.ensure_future`
- [ ] **Running concurrently** — `asyncio.gather` (`return_exceptions`), **`asyncio.TaskGroup`** (structured concurrency, cancels siblings on failure — 3.11), `asyncio.wait` (`FIRST_COMPLETED`, `FIRST_EXCEPTION`), `as_completed`
- [ ] **Timeouts** — `asyncio.timeout()` (3.11), `wait_for`
- [ ] **Cancellation** — `CancelledError` propagation (don't swallow it!), `task.cancel()`, `asyncio.shield`, cleanup in `finally`, cancellation scopes
- [ ] **Synchronization primitives** — `asyncio.Lock`, `Semaphore` (limit concurrent outbound calls), `Event`, `Condition`, `Queue` (producer/consumer, worker pools), `Barrier` (3.11)
- [ ] **Blocking the event loop** — the #1 asyncio bug: sync DB drivers, `requests`, `time.sleep`, CPU-heavy work; detection with debug mode (`PYTHONASYNCIODEBUG=1`, slow callback warnings); fixes: async libraries, `asyncio.to_thread`, `loop.run_in_executor` with process pool
- [ ] **Async iteration & context managers** — `async for`, `async with`, async generators, `aclose`
- [ ] **contextvars** — request-scoped context in async code (vs `threading.local`), copying context to tasks
- [ ] **Streams** — `asyncio.open_connection`, `start_server`; subprocesses (`create_subprocess_exec`)
- [ ] **Async ecosystem** — `httpx`/`aiohttp` (HTTP clients), `asyncpg`/`psycopg` async, SQLAlchemy async, `redis.asyncio`, `aiokafka`, `aio-pika`, `motor`; **uvloop**
- [ ] **AnyIO & Trio** — structured concurrency alternatives; FastAPI/Starlette run on AnyIO
- [ ] **Mixing sync & async** — calling async from sync (`asyncio.run`, `anyio.from_thread`), sync from async (`to_thread`), Django `sync_to_async`/`async_to_sync`
- [ ] **Graceful shutdown** — signal handlers, cancelling outstanding tasks, draining queues
- [ ] **Backpressure** — bounded queues, semaphores, rate limiting outbound calls
- [ ] **Debugging asyncio** — debug mode, task dumps (`asyncio.all_tasks`), 3.14 `python -m asyncio ps/pstree` introspection

### 4.5 Other Concurrency Models
- [ ] **Greenlets / gevent / eventlet** — monkey-patching, implicit cooperative scheduling; Gunicorn/Celery gevent workers; pitfalls (C extensions, blocking calls not patched)
- [ ] **Threads vs asyncio vs gevent** — trade-offs in readability, ecosystem, debugging, performance

### 4.6 Classic Concurrency Coding Problems (write them in Python)
- [ ] Producer–consumer with `queue.Queue` and with `asyncio.Queue`
- [ ] Bounded concurrency fetcher — fetch 10,000 URLs with max 100 in flight (`asyncio.Semaphore` + `httpx.AsyncClient`) with timeouts & retries
- [ ] Print odd/even alternately with two threads (`Condition`/`Event`)
- [ ] Thread-safe LRU cache; thread-safe singleton
- [ ] Token-bucket rate limiter (thread-safe and asyncio versions)
- [ ] Parallel CPU work with `ProcessPoolExecutor` and chunking
- [ ] Async web crawler with dedupe and depth limit
- [ ] Dining philosophers / deadlock-free bank transfer
- [ ] Implement `gather` with a concurrency limit; implement a simple async task scheduler with delays

### 🎯 Frequently Asked — Concurrency
- Threads vs processes vs asyncio — when would you use each?
- What happens if you call a blocking function inside an async endpoint?
- `gather` vs `TaskGroup` — differences in error handling
- How do you limit concurrency to a downstream API in asyncio?
- How does cancellation work in asyncio and what are common bugs?
- How do you share state between processes?

---

## 5. Type Hints & Static Typing (P0)

- [ ] **Why type hints** at scale — refactoring safety, IDE support, documentation, catching bugs in CI; gradual typing
- [ ] **Basics** — annotations for variables, params, returns; `None`, `Optional[X]` = `X | None`, `Union`, `Any` vs `object`
- [ ] **Collections** — `list[int]`, `dict[str, int]`, `tuple[int, ...]`, `collections.abc` types for params (`Iterable`, `Sequence`, `Mapping`) vs concrete return types
- [ ] **Callable**, `Literal`, `Final`, `ClassVar`, `Annotated` (metadata — used heavily by FastAPI/Pydantic), `NewType`, `TypeAlias` / `type` statement (3.12)
- [ ] **Generics** — `TypeVar` (bounds, constraints), `Generic[T]`, PEP 695 syntax (`class Box[T]:`), **variance** (covariant/contravariant/invariant — why `list[Dog]` isn't `list[Animal]`), `ParamSpec` & `Concatenate` (typing decorators), `TypeVarTuple`
- [ ] **Protocols** — structural subtyping, `@runtime_checkable`
- [ ] **TypedDict** (`Required`, `NotRequired`, `total`, `ReadOnly`), `Unpack` for `**kwargs`
- [ ] **`@overload`**, `Self`, `Never`/`NoReturn`, `TypeGuard`/`TypeIs` (narrowing), `assert_never` for exhaustiveness, `@override`, `@final`, `@deprecated`
- [ ] **Type narrowing** — `isinstance`, `is None`, literal comparisons, match statements
- [ ] **Forward references**, `from __future__ import annotations`, `TYPE_CHECKING` imports, deferred annotations in 3.14
- [ ] **Stub files** (`.pyi`), typeshed, `types-*` packages, `py.typed` marker for libraries
- [ ] **Type checkers** — **mypy** (strict mode, config, plugins for Django/Pydantic/SQLAlchemy), **pyright/basedpyright** (fast, Pylance), newer Rust-based checkers (Astral **ty**, Meta **Pyrefly**) — awareness
- [ ] **Adopting typing in a legacy codebase** — incremental strictness per module, baseline files, CI gates
- [ ] **Static typing vs runtime validation** — type hints are not enforced at runtime; Pydantic/msgspec/beartype/typeguard for runtime checks at trust boundaries

---

# PART B — PROBLEM SOLVING

## 6. Data Structures & Algorithms in Python (P0)

> Target: **250–300 quality problems** (Blind 75 → NeetCode 150 → company-tagged). Senior bar = Medium in ~25 min with clean code, edge cases and complexity.

### 6.1 Complexity & Python Cost Model
- [ ] Big-O/Θ/Ω, amortized analysis, recursion stack space, Master theorem
- [ ] **Complexity of Python built-ins** — list append O(1)*, insert/pop(0) O(n), `in` list O(n) vs set/dict O(1) avg, `sorted` O(n log n) (Timsort, stable), slicing copies O(k), string concatenation in loops O(n²), `deque` O(1) both ends, `heapq` push/pop O(log n), `heapify` O(n)
- [ ] Input-size → acceptable complexity cheat sheet

### 6.2 Python Idioms for Coding Interviews
- [ ] `collections.deque` (BFS, sliding window), `defaultdict(list)` (graphs), `Counter` (frequency, `most_common`), `OrderedDict` (LRU)
- [ ] **`heapq`** is a min-heap — negate for max-heap, tuples `(priority, counter, item)` to break ties, `nlargest`/`nsmallest`, `heappushpop`/`heapreplace`
- [ ] **`bisect`** — `bisect_left`/`bisect_right`/`insort`, `key=` param (3.10)
- [ ] `sorted(items, key=lambda x: (-x[1], x[0]))`, `functools.cmp_to_key` for custom comparators
- [ ] `@functools.cache` / `lru_cache(None)` for memoized DP; `sys.setrecursionlimit` (and when to go iterative)
- [ ] `itertools` (`combinations`, `permutations`, `product`, `accumulate`, `pairwise`, `groupby`)
- [ ] `float('inf')`, `math.inf`, integer has no overflow (but mention it for other languages)
- [ ] String building via list + `''.join`, `ord`/`chr`, `str.isalnum`, `zip(*matrix)` for transpose
- [ ] `divmod`, `//` with negatives, `pow(a, b, mod)`, `math.gcd`/`lcm`, `math.comb`
- [ ] 2D grid helpers — direction vectors, bounds checks, `visited` sets of tuples
- [ ] Note: no built-in balanced BST/TreeMap — use `bisect` on sorted list, heap + lazy deletion, or mention `sortedcontainers.SortedList`

### 6.3 Data Structures
- [ ] Arrays/strings, hash maps/sets, linked lists (dummy node), stacks, queues, deques, **monotonic stack/queue**
- [ ] Heaps/priority queues (top-K, k-way merge, two heaps for median)
- [ ] Trees — binary tree traversals (recursive & iterative), BST ops, LCA, serialization, balanced trees (concept), **B/B+ trees** (DB relevance)
- [ ] Tries; graphs (adjacency list/matrix, implicit grids); **union-find** (path compression + union by rank)
- [ ] Segment tree / Fenwick tree (P1); bit manipulation
- [ ] Design structures — LRU, LFU, min-stack, hit counter, time-based KV store, randomized set
- [ ] Probabilistic — Bloom filter, Count-Min Sketch, HyperLogLog (system-design crossover)

### 6.4 Algorithms
- [ ] Sorting (merge, quick, heap, counting, bucket, radix; Timsort is what Python uses), quickselect
- [ ] Binary search — classic, bounds, rotated arrays, search on answer space
- [ ] Recursion & backtracking (subsets, permutations, combinations, N-Queens, word search)
- [ ] Greedy (intervals, jump game, gas station, task scheduler)
- [ ] **Dynamic programming** — 1D, 2D/grid, knapsack (0/1, unbounded), LIS (with `bisect`), LCS, edit distance, interval DP, tree DP, stock state machines, bitmask DP (P2)
- [ ] **Graphs** — BFS/DFS, multi-source BFS, 0-1 BFS, topological sort (Kahn & DFS; `graphlib.TopologicalSorter`), cycle detection, Dijkstra (`heapq`), Bellman-Ford, Floyd-Warshall, MST (Kruskal/Prim), bipartite, SCC (P2)
- [ ] Strings — sliding window, KMP, Rabin-Karp rolling hash, palindromes
- [ ] Math — GCD, sieve, modular exponentiation, reservoir sampling, Fisher-Yates

### 6.5 Patterns (recognize first, then code)
- [ ] Two pointers · sliding window · fast/slow pointers · merge intervals · cyclic sort · in-place list reversal · tree BFS/DFS · two heaps · subsets/backtracking · modified binary search · top-K · k-way merge · topological sort · monotonic stack · prefix sum + hashmap · union-find · trie · matrix traversal · bitwise XOR · greedy · DP families · design data structure

### 6.6 Must-Practice Problems (LeetCode names)
- [ ] **Arrays/Hashing** — Two Sum, Group Anagrams, Top K Frequent Elements, Product of Array Except Self, Longest Consecutive Sequence, Subarray Sum Equals K, Encode/Decode Strings
- [ ] **Two Pointers / Sliding Window** — 3Sum, Container With Most Water, Trapping Rain Water, Longest Substring Without Repeating Characters, Minimum Window Substring, Sliding Window Maximum, Permutation in String
- [ ] **Stack** — Valid Parentheses, Min Stack, Daily Temperatures, Largest Rectangle in Histogram, Decode String, Basic Calculator II
- [ ] **Binary Search** — Search in Rotated Sorted Array, Koko Eating Bananas, Time Based Key-Value Store, Median of Two Sorted Arrays
- [ ] **Linked List** — Reverse, Merge K Sorted Lists, Reorder List, Copy List with Random Pointer, **LRU Cache**
- [ ] **Trees/Tries** — Max Path Sum, Serialize/Deserialize, Validate BST, LCA, Right Side View, Implement Trie, Word Search II
- [ ] **Heap** — K Closest Points, Task Scheduler, Find Median from Data Stream, Design Twitter
- [ ] **Backtracking** — Subsets, Combination Sum, Permutations, Word Search, N-Queens
- [ ] **Graphs** — Number of Islands, Clone Graph, Course Schedule I/II, Rotting Oranges, Pacific Atlantic, Word Ladder, Accounts Merge, Network Delay Time, Cheapest Flights Within K Stops, Alien Dictionary
- [ ] **DP** — Coin Change, Word Break, LIS, Partition Equal Subset Sum, LCS, Edit Distance, Decode Ways, House Robber I/II, Longest Palindromic Substring, Unique Paths
- [ ] **Intervals/Greedy** — Merge Intervals, Insert Interval, Meeting Rooms II, Non-overlapping Intervals, Jump Game, Gas Station
- [ ] **Design** — LRU Cache, LFU Cache, Logger Rate Limiter, Hit Counter, Insert Delete GetRandom O(1)

### 6.7 Interview Execution Protocol
- [ ] Clarify → examples → edge cases → brute force → optimize (name the pattern) → get buy-in → clean code with type hints → dry run → complexity → follow-ups; think aloud

---

## 7. OOD / LLD & Design Patterns (Pythonic) (P0)

### 7.1 Principles in Python
- [ ] **SOLID** with Python examples (SRP modules/classes, OCP via strategies/registries, LSP with ABCs/Protocols, ISP with small Protocols, DIP via injected dependencies)
- [ ] DRY, KISS, YAGNI, Law of Demeter, composition over inheritance, high cohesion/low coupling
- [ ] **Python-specific design** — modules as namespaces & singletons, functions as first-class strategies, duck typing, Protocols for interfaces, dataclasses for value objects, immutability via `frozen=True`

### 7.2 Design Patterns — classic intent + the Pythonic way
- [ ] **Singleton** — module-level instance (Pythonic), `__new__`-based, metaclass-based, why to avoid global state
- [ ] **Factory / Abstract Factory** — functions/dict registries, `@classmethod` constructors, plugin registries via `__init_subclass__` or entry points
- [ ] **Builder** — often replaced by keyword args/dataclasses; fluent builders for complex queries (SQLAlchemy `select()`)
- [ ] **Prototype** — `copy.deepcopy`, `dataclasses.replace`
- [ ] **Adapter, Facade, Proxy** (lazy loading, `__getattr__` delegation), **Composite**, **Flyweight** (`__slots__`, interning)
- [ ] **Decorator pattern vs Python decorators** — wrapping objects vs functions
- [ ] **Strategy** — pass a function/callable or a Protocol implementation
- [ ] **Observer / pub-sub** — callbacks, signals (Django signals, blinker), event buses
- [ ] **Command** (callables, undo stacks), **Chain of Responsibility** (middleware!), **Template Method** (ABC hooks), **State** (state classes / enums with transitions), **Iterator** (generators), **Visitor** (`functools.singledispatch`), **Mediator**, **Memento**
- [ ] **Dependency Injection** — constructor injection, FastAPI `Depends`, `dependency-injector`, `punq`/`lagom`; avoiding import-time side effects
- [ ] **Enterprise patterns** — Repository, Unit of Work (SQLAlchemy Session is one), Service layer, DTOs (Pydantic schemas vs ORM models), Specification, Domain events (Cosmic Python book)

### 7.3 LLD Problems to Practice
- [ ] Parking Lot · Elevator · Vending Machine (State) · ATM · Library Management · Splitwise · BookMyShow (seat locking) · Hotel/Meeting Room Booking · Snake & Ladder · Tic-Tac-Toe · Chess
- [ ] LRU/LFU Cache with TTL & pluggable eviction · **Rate Limiter** (pluggable algorithms) · Logger framework · In-memory Pub-Sub/Message Queue · Task Scheduler / delayed job runner · In-memory KV store with transactions · In-memory File System
- [ ] Ride sharing · Food delivery · Shopping cart & coupons · Digital wallet · Notification service · Stock order-matching engine · Circuit breaker · Workflow engine · Feature flags · URL shortener (LLD)

### 7.4 LLD Approach
- [ ] Requirements & scope → entities & relationships → state machines → interfaces/Protocols → class diagram → patterns only where they earn their place → concurrency concerns → code key flows → extensibility & tests

---

## 8. Machine Coding Round (P0 for product companies)

- [ ] 90–120 min to build a working, runnable in-memory app; evaluated on working code, modularity, extensibility, readability, edge cases, tests
- [ ] **Skeleton** — `models/` (dataclasses/enums), `services/`, `repositories/` (in-memory dicts with locks if concurrent), `strategies/`, `exceptions.py`, `main.py` driver, `tests/` with pytest
- [ ] Type hints everywhere, custom exceptions, no god classes, dependency injection for strategies
- [ ] Practice 8–10 problems under a timer (Splitwise, parking lot, snake & ladder, KV store, rate limiter, cab booking, inventory, library)

---

# PART C — PYTHON BACKEND ECOSYSTEM

## 9. Web Fundamentals: WSGI, ASGI & App Servers (P0)

- [ ] **WSGI** (PEP 3333) — synchronous callable `app(environ, start_response)`, middleware model, one request per worker thread/process
- [ ] **ASGI** — async interface `app(scope, receive, send)`, lifespan protocol, HTTP/WebSocket support; ASGI middleware
- [ ] **Servers** — **Gunicorn** (pre-fork master/worker model), **Uvicorn** (ASGI, uvloop + httptools), Hypercorn (HTTP/2, HTTP/3), **Granian** (Rust), uWSGI (legacy, in maintenance), Daphne (Channels), Waitress
- [ ] **Gunicorn worker classes** — `sync`, `gthread` (threads), `gevent`/`eventlet` (green threads), `uvicorn.workers.UvicornWorker` (ASGI; or the `uvicorn-worker` package)
- [ ] **Worker sizing** — classic `(2 × CPU) + 1` for sync; threads for I/O; in containers often 1 process per container and scale pods horizontally; memory per worker
- [ ] **Gunicorn settings** — `--workers`, `--threads`, `--timeout` (worker killed if silent), `--graceful-timeout`, `--keep-alive`, `--max-requests` + `--max-requests-jitter` (mitigate leaks), `--preload` (faster start, CoW memory sharing, but DB connections must not be shared across fork)
- [ ] **Reverse proxy** in front — Nginx (buffering slow clients, TLS, static files), ALB/Ingress; `X-Forwarded-*` headers & trusted proxies
- [ ] **Static & media files** — WhiteNoise, CDN, S3
- [ ] **Graceful shutdown** — SIGTERM handling, draining, Kubernetes preStop
- [ ] **HTTP clients** — `requests` (sync, Session for connection pooling), **`httpx`** (sync + async, HTTP/2, timeouts), `aiohttp` client; **always set timeouts**; connection pool limits; retries with `urllib3.Retry`/tenacity; `requests` default has *no* timeout
- [ ] **WebSockets & SSE** in Python — Starlette/FastAPI WebSockets, Django Channels (channel layers via Redis), `sse-starlette`; scaling with pub/sub

---

## 10. Django (P0)

### 10.1 Architecture & Request Lifecycle
- [ ] **MTV pattern** (Model-Template-View), projects vs apps, `INSTALLED_APPS`, app registry & `AppConfig.ready()`
- [ ] **Settings** — split settings per environment, `django-environ`/env vars, `DEBUG=False` in prod, `ALLOWED_HOSTS`, `SECRET_KEY` management
- [ ] **Request/response lifecycle** — WSGI/ASGI handler → middleware (request phase, top-down) → URL resolver → view → middleware (response phase, bottom-up) → response; exception middleware; `process_view`, `process_exception`, `process_template_response`
- [ ] **Middleware** — ordering in `MIDDLEWARE`, writing custom middleware (function & class style), async-capable middleware
- [ ] **URL routing** — `path`, `re_path`, converters, `include`, namespaces, `reverse`
- [ ] **Views** — function-based vs class-based (`View`, generic views: `ListView`, `DetailView`, `CreateView`…), mixins & MRO in CBVs, decorators on CBVs
- [ ] **Templates** — DTL, context processors, template inheritance, autoescaping (XSS protection), custom tags/filters (less relevant for API backends)
- [ ] **Forms & ModelForms** — validation flow (`clean_<field>`, `clean`), formsets
- [ ] **Django admin** — customization, performance (`list_select_related`, `raw_id_fields`, `autocomplete_fields`), security of admin
- [ ] **Management commands** — custom commands for ops tasks/backfills
- [ ] **Signals** — `pre_save`/`post_save`/`m2m_changed`, `transaction.on_commit`; why signals hurt traceability (prefer explicit service calls)
- [ ] **Async Django** — async views, ASGI deployment, async ORM methods (`aget`, `acreate`, `async for` over querysets — still run sync DB under the hood in many paths), `sync_to_async` (`thread_sensitive`), async-safety of the ORM
- [ ] **Django Channels** — consumers, channel layers (Redis), WebSockets, groups

### 10.2 Django ORM (P0)
- [ ] **Models** — fields, `Meta` (ordering, indexes, constraints, `db_table`, `unique_together` → `UniqueConstraint`), abstract base models, proxy models, multi-table inheritance (and its JOIN cost)
- [ ] **Relationships** — `ForeignKey` (`on_delete` options), `OneToOneField`, `ManyToManyField` (`through` models), `related_name`, reverse accessors
- [ ] **QuerySets** — laziness, chaining, caching of evaluated querysets, when querysets are evaluated (iteration, slicing with step, `len`, `list`, `bool`, repr)
- [ ] **N+1 problem** — **`select_related`** (SQL JOIN, FK/O2O) vs **`prefetch_related`** (separate query + Python join, M2M/reverse FK), `Prefetch` objects with custom querysets, detecting with django-debug-toolbar / `assertNumQueries` / nplusone / django-silk
- [ ] **`only` / `defer`**, `values` / `values_list` (dicts/tuples, skip model instantiation)
- [ ] **Query expressions** — `F()` (atomic updates, avoid race conditions: `update(stock=F('stock') - 1)`), `Q()` (complex OR/NOT lookups), `annotate`, `aggregate`, `Count`/`Sum`/`Avg` with `distinct`/`filter`, `Case`/`When`, `Subquery`/`OuterRef`/`Exists`, `Window` functions, `Coalesce`, database functions
- [ ] **Bulk operations** — `bulk_create` (`batch_size`, `ignore_conflicts`, `update_conflicts` upserts), `bulk_update`, `update()`/`delete()` on querysets (skip `save()` and signals!), `in_bulk`
- [ ] **Large datasets** — `.iterator(chunk_size=…)` (server-side cursors), keyset pagination, avoiding loading millions of objects
- [ ] **Raw SQL** — `Manager.raw`, `connection.cursor()`, parameterization (never f-strings!)
- [ ] **Managers & custom QuerySets** — `QuerySet.as_manager()`, default managers, soft-delete managers
- [ ] **Transactions** — autocommit default, **`transaction.atomic`** (decorator & context manager, nested savepoints), `ATOMIC_REQUESTS` trade-offs, **`transaction.on_commit`** (send emails/publish events only after commit), `select_for_update` (`nowait`, `skip_locked`, `of`), isolation level config, durable atomic blocks
- [ ] **Concurrency** — race conditions with `get` + `save`, optimistic locking (version field + conditional `update`), `get_or_create`/`update_or_create` race conditions & unique constraints
- [ ] **Indexes & constraints** — `Index` (partial with `condition`, functional, `GinIndex` for Postgres), `CheckConstraint`, `UniqueConstraint` (conditional); `db_index`
- [ ] **Multiple databases** — database routers, read replicas (`using()`), replica lag
- [ ] **Postgres-specific** — `JSONField`, `ArrayField`, full-text search (`SearchVector`), `contrib.postgres` indexes
- [ ] **Connection management** — `CONN_MAX_AGE` persistent connections, `CONN_HEALTH_CHECKS`, native connection pooling for Postgres (Django 5.1+ with psycopg 3 pool), PgBouncer (transaction mode caveats with server-side cursors)

### 10.3 Migrations
- [ ] `makemigrations`/`migrate`, migration graph & dependencies, `--plan`, `sqlmigrate`, `showmigrations`
- [ ] **Data migrations** (`RunPython` with historical models, reversible), `RunSQL`
- [ ] **Squashing** migrations; resolving merge conflicts in migrations
- [ ] **Zero-downtime migrations** — expand/contract, adding nullable columns first, backfilling in batches, `AddIndexConcurrently` (Postgres), avoiding table locks on large tables, separating schema and code deploys, `django-pg-zero-downtime-migrations` / `django-migration-linter`
- [ ] `SeparateDatabaseAndState` for tricky refactors

### 10.4 Auth, Security & Caching in Django
- [ ] **Auth system** — custom user model (`AbstractUser`/`AbstractBaseUser` — set it up on day one), authentication backends, permissions & groups, object-level permissions (django-guardian, django-rules), password hashers (PBKDF2 default, Argon2)
- [ ] **Sessions** — backends (DB, cache, signed cookies), session security settings
- [ ] **Built-in protections** — CSRF middleware & tokens, XSS autoescape, clickjacking (`X-Frame-Options`), SQL injection via ORM parameterization, host header validation; `SECURE_*` settings (HSTS, SSL redirect, secure cookies), `manage.py check --deploy`
- [ ] **Cache framework** — backends (Redis, Memcached, local memory), per-view cache, template fragment cache, low-level API, cache keys & versioning, `cache_page` pitfalls with auth
- [ ] **Static/media** — `collectstatic`, storages (django-storages S3), signed URLs

### 10.5 Django in Production
- [ ] Performance — query optimization, caching, `select_related`/`prefetch_related`, pagination, avoiding serializer N+1, profiling with django-silk/debug-toolbar/APM
- [ ] Deployment — Gunicorn/Uvicorn workers, Nginx, `collectstatic`, health checks, migrations in CI/CD
- [ ] Structuring large Django projects — app boundaries, service layer pattern, avoiding fat models/fat views, "Django styleguide" (HackSoft) approach, modular monolith with Django apps
- [ ] Celery integration (§15), django-celery-beat, transactional `on_commit` task enqueueing
- [ ] Ecosystem — django-filter, django-extensions, django-environ, django-storages, django-cors-headers, django-axes (brute force), django-allauth, Wagtail (CMS) awareness, Django Ninja (FastAPI-style APIs on Django)

### 🎯 Frequently Asked — Django
- Walk through the Django request lifecycle and middleware order
- `select_related` vs `prefetch_related` — how do you find and fix N+1 queries?
- How do you prevent race conditions when decrementing inventory?
- How do you run migrations on a 200M-row table with zero downtime?
- Signals — pros/cons; when would you not use them?
- How does Django protect against CSRF/XSS/SQL injection?
- How would you scale a Django monolith serving 10k RPS?

---

## 11. Django REST Framework (P0)

- [ ] **Request/Response** wrappers, parsers & renderers, content negotiation
- [ ] **Serializers** — `Serializer` vs `ModelSerializer`, field-level & object-level validation (`validate_<field>`, `validate`), `to_representation`/`to_internal_value`, read-only/write-only fields, `SerializerMethodField` (N+1 trap!), nested serializers & writable nested creates, `source=`, `context` (request), partial updates
- [ ] **Serializer performance** — DRF serialization is slow for large payloads → `values()` + plain dicts, `prefetch_related` in viewsets, lighter serializers for lists, caching, or alternative libs
- [ ] **Views** — `APIView`, generic views & mixins, **ViewSets** & `ModelViewSet`, routers, `@action` for custom endpoints, `get_queryset` vs `queryset`, `get_serializer_class` per action
- [ ] **Authentication** — Session, Basic, Token, **JWT via `djangorestframework-simplejwt`** (access/refresh, rotation, blacklist), OAuth2 (django-oauth-toolkit), custom authentication classes
- [ ] **Permissions** — `IsAuthenticated`, `IsAdminUser`, `DjangoModelPermissions`, custom `has_permission` vs `has_object_permission` (object-level — prevent IDOR), combining with `&`/`|`
- [ ] **Throttling** — `AnonRateThrottle`, `UserRateThrottle`, `ScopedRateThrottle`; cache-backed, not exact under concurrency
- [ ] **Pagination** — PageNumber, LimitOffset, **Cursor** (stable for large/real-time datasets)
- [ ] **Filtering, searching, ordering** — django-filter `FilterSet`, `SearchFilter`, `OrderingFilter`
- [ ] **Versioning** — URL path, namespace, header, query param
- [ ] **Exception handling** — custom exception handler for a consistent error contract
- [ ] **OpenAPI** — drf-spectacular schema generation, Swagger/Redoc
- [ ] **Testing** — `APIClient`, `APITestCase`, `force_authenticate`, pytest-django

---

## 12. FastAPI & Pydantic (P0)

### 12.1 FastAPI Core
- [ ] **Architecture** — built on **Starlette** (ASGI toolkit) + **Pydantic** (validation/serialization); OpenAPI generated from type hints
- [ ] **Path operations** — path, query, header, cookie, body params; `Annotated[...]` style with `Query`, `Path`, `Body`, `Header`; validation constraints
- [ ] **Request bodies & response models** — `response_model`, `response_model_exclude_unset`, separate input/output schemas (never return ORM objects with sensitive fields), status codes, `Response` subclasses (`JSONResponse`, `ORJSONResponse`, `StreamingResponse`, `FileResponse`, `RedirectResponse`)
- [ ] **`async def` vs `def` endpoints** — `def` endpoints run in a threadpool (AnyIO, default ~40 threads); `async def` runs on the event loop → **never call blocking code inside `async def`**; threadpool exhaustion
- [ ] **Dependency Injection** — `Depends`, sub-dependencies, dependency caching per request (`use_cache`), **yield dependencies** for setup/teardown (DB sessions), class-based dependencies, dependencies in routers/app (`dependencies=[...]`), overriding dependencies in tests (`app.dependency_overrides`)
- [ ] **Routers** — `APIRouter`, prefixes, tags, structuring large apps (by domain/feature), versioning
- [ ] **Middleware** — CORS, GZip, TrustedHost, custom HTTP middleware (`@app.middleware("http")`) vs pure ASGI middleware (better performance, streaming-safe)
- [ ] **Exception handling** — `HTTPException`, custom exception handlers, `RequestValidationError` (422) customization, consistent error schemas
- [ ] **Lifespan events** — `lifespan` async context manager (create/close DB pools, HTTP clients, load ML models); deprecated `on_event`
- [ ] **Background tasks** — `BackgroundTasks` (runs after response in same process — not durable; use Celery/queues for real work)
- [ ] **Security** — `OAuth2PasswordBearer`, `HTTPBearer`, API keys, JWT verification (PyJWT), OAuth2 scopes with `Security`, `SecurityScopes`
- [ ] **WebSockets**, **SSE / streaming responses**, file uploads (`UploadFile` — spooled temp file, streaming large uploads)
- [ ] **OpenAPI customization** — tags, examples, `openapi_extra`, hiding endpoints, generating clients
- [ ] **Testing** — `TestClient` (sync), `httpx.AsyncClient` with `ASGITransport` for async tests, dependency overrides, test DB per test with transactions
- [ ] **Project structure & ecosystem** — SQLModel (SQLAlchemy + Pydantic), fastapi-users, slowapi (rate limiting), `fastapi-pagination`; FastAPI CLI (`fastapi dev`/`run`)
- [ ] **Performance** — `ORJSONResponse`, avoiding double validation, Pydantic v2 speed, uvloop/httptools, multiple workers, connection pooling, async DB drivers
- [ ] **Deployment** — Uvicorn behind Gunicorn or standalone with multiple workers, `--proxy-headers`, `--forwarded-allow-ips`, container-per-process in K8s

### 12.2 Pydantic v2 (P0)
- [ ] **Models** — `BaseModel`, field types, defaults, `Field(...)` constraints (gt, max_length, pattern, alias), `Optional` vs required semantics
- [ ] **Validation** — `@field_validator` (mode before/after/wrap/plain), `@model_validator`, `Annotated` validators (`AfterValidator`, `BeforeValidator`), strict vs lax mode, coercion rules
- [ ] **Serialization** — `model_dump` (`mode="json"`, `exclude_none`, `by_alias`), `model_dump_json`, `@field_serializer`, `@computed_field`
- [ ] **Config** — `model_config = ConfigDict(from_attributes=True, extra="forbid", frozen=True, populate_by_name=True, str_strip_whitespace=True)`
- [ ] **Advanced types** — discriminated unions (`Field(discriminator=…)`), generics, `RootModel`, `TypeAdapter` (validate non-model types), `SecretStr`, `EmailStr`, `HttpUrl`, constrained types
- [ ] **pydantic-settings** — `BaseSettings` for env/.env config, nested settings, secrets directories
- [ ] **v1 → v2 migration** — renamed APIs (`dict()` → `model_dump()`, `parse_obj` → `model_validate`, `orm_mode` → `from_attributes`, validators), behavior changes, performance (pydantic-core in Rust)
- [ ] **Alternatives** — `msgspec` (very fast), `attrs` + `cattrs`, `marshmallow` (legacy), dataclasses

### 🎯 Frequently Asked — FastAPI
- What happens if you use a blocking DB driver inside an `async def` endpoint?
- How does dependency injection work? How do you manage a DB session per request?
- How do you structure a large FastAPI project?
- FastAPI vs Django/DRF vs Flask — when would you pick each?
- How do you handle background jobs reliably?
- How does Pydantic v2 validation differ from v1? How do you validate cross-field rules?

---

## 13. Flask & Other Frameworks (P1)

- [ ] **Flask** — WSGI micro-framework (Werkzeug + Jinja2), application factory pattern, **Blueprints**, application context vs request context, `g`, `current_app`, `request` proxies (context locals), `before_request`/`after_request`/`teardown_request`, error handlers, configuration, extensions (Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-JWT-Extended, Flask-Limiter, Flask-Caching, Flask-CORS), async views (limited), testing with test client
- [ ] **Quart** (async Flask), **Litestar** (ASGI, msgspec, DI), **Sanic**, **aiohttp** server, **Tornado** (legacy async), **Falcon**, **Starlette** directly, **Django Ninja**, **Robyn**/**BlackSheep** (awareness)
- [ ] **gRPC in Python** — `grpcio`, protobuf codegen (`grpcio-tools`/buf), sync & `grpc.aio` servers, interceptors, deadlines, streaming, health checks, reflection; betterproto
- [ ] **GraphQL in Python** — **Strawberry** (type-hint based, FastAPI/Django integrations), Graphene (legacy), Ariadne (schema-first); DataLoader for N+1
- [ ] **Framework selection** — Django (batteries-included, admin, ORM, large monoliths), FastAPI (async APIs, typed, microservices, ML serving), Flask (minimal, legacy), Litestar (performance + structure); team skills; ecosystem

---

## 14. Data Access: DB-API, SQLAlchemy, Alembic, Drivers (P0)

### 14.1 Drivers & Pooling
- [ ] **DB-API 2.0 (PEP 249)** — connection, cursor, `execute` with parameters (`%s` / `:name` styles — never string formatting), `executemany`, `fetchmany`, transactions (`commit`/`rollback`), autocommit
- [ ] **PostgreSQL drivers** — psycopg2 (legacy), **psycopg 3** (sync + async, server-side binding, pipeline mode, COPY support, `psycopg_pool`), **asyncpg** (fastest async, own API); COPY for bulk loads
- [ ] **MySQL drivers** — mysqlclient, PyMySQL, aiomysql/asyncmy
- [ ] **Connection pooling** — SQLAlchemy `QueuePool` (`pool_size`, `max_overflow`, `pool_timeout`, `pool_recycle`, `pool_pre_ping`), `NullPool` with PgBouncer, psycopg_pool; **total connections = pods × workers × pool size** must fit DB `max_connections`; **pools and `fork`** (dispose engine after fork / don't share connections across processes)
- [ ] **PgBouncer** modes (session/transaction/statement) and what breaks in transaction mode (prepared statements, session-level settings, advisory locks, server-side cursors)

### 14.2 SQLAlchemy 2.0 (P0)
- [ ] **Core vs ORM** — Core: `Engine`, `Connection`, `MetaData`, `Table`, `select()`/`insert()`/`update()`, SQL expression language; ORM on top
- [ ] **2.0-style** — `select(User).where(...)`, `session.execute(...).scalars()`, `session.scalars()`, typed `Mapped[...]` + `mapped_column()` declarative models, `DeclarativeBase`
- [ ] **Session** — **Unit of Work**, **identity map**, object states (transient, pending, persistent, detached, deleted), `flush` vs `commit`, autoflush, `expire_on_commit` (and its effect on async/serialization), `refresh`, `merge`, `expunge`
- [ ] **Session scoping** — one session per request/task, `sessionmaker`, `scoped_session` (thread-local, legacy), FastAPI yield-dependency pattern, never share sessions across threads/tasks
- [ ] **Relationships** — `relationship()`, `back_populates`, cascades (`all, delete-orphan`), association tables vs association objects, `lazy=` strategies
- [ ] **Loading strategies** — lazy (default; N+1 risk), `joinedload`, **`selectinload`** (best default for collections), `subqueryload`, `raiseload` (fail fast in async/APIs), `contains_eager`, `load_only`/`defer`
- [ ] **Async SQLAlchemy** — `create_async_engine`, `AsyncSession`, lazy loading not allowed (use eager loading / `AsyncAttrs`), greenlet bridge, `expire_on_commit=False`
- [ ] **Bulk operations** — ORM bulk INSERT/UPDATE with `session.execute(insert(Model), [dicts])`, `insert().on_conflict_do_update` (Postgres upsert), `yield_per` / `stream` for large reads
- [ ] **Transactions** — `session.begin()`, nested transactions/savepoints (`begin_nested`), isolation level per engine/connection, `with_for_update` (`skip_locked`, `nowait`)
- [ ] **Optimistic locking** — `version_id_col`; `StaleDataError`
- [ ] **Advanced** — hybrid properties, column properties, events (`before_flush`, `after_commit`), custom types (`TypeDecorator`), polymorphic inheritance (single/joined/concrete), multi-tenancy (schema translate map), sharding extension (awareness)
- [ ] **Debugging** — `echo=True`, logging SQL, query count assertions in tests

### 14.3 Migrations — Alembic (P0)
- [ ] `alembic init`, `env.py` (target metadata, async env), `revision --autogenerate` (and what it misses: renames, some constraint/server-default changes, enum changes)
- [ ] upgrade/downgrade, branches & merges, `alembic heads`, offline SQL mode
- [ ] **Data migrations** in Alembic (use Core, not ORM models), batched backfills
- [ ] **Zero-downtime practices** — expand/contract, `CREATE INDEX CONCURRENTLY` (outside transaction), lock timeouts, NOT NULL with default on big tables, separating migration from deploy

### 14.4 Other Data Libraries
- [ ] **Other ORMs** — Django ORM (§10), **SQLModel**, Tortoise ORM, Peewee, Pony; query builders (PyPika); "no ORM" approaches (raw SQL + dataclasses, `aiosql`)
- [ ] **Redis** — `redis-py` (sync & `redis.asyncio`), connection pools, pipelines, Lua scripts (`register_script`), pub/sub, Streams, `redis-om`, Redis Cluster client
- [ ] **MongoDB** — PyMongo (now with native async API), Motor (async, being superseded), Beanie/ODMantic (ODMs), MongoEngine
- [ ] **Elasticsearch/OpenSearch clients**, Cassandra (`cassandra-driver`), DynamoDB (`boto3` resource vs client, PynamoDB)
- [ ] **SQLite** for tests/local; why tests should use the real DB engine (Testcontainers)

### 🎯 Frequently Asked — Data Access
- Explain the SQLAlchemy Session / Unit of Work / identity map
- `joinedload` vs `selectinload` — when each?
- How do you manage DB sessions in FastAPI? In Celery tasks?
- What breaks when you use PgBouncer in transaction mode?
- How do you size connection pools across 20 pods with 4 workers each?
- What does Alembic autogenerate miss?

---

## 15. Background Jobs, Task Queues & Messaging Clients (P0)

### 15.1 Celery (P0)
- [ ] **Architecture** — producers (app), **broker** (RabbitMQ / Redis / SQS), **workers**, **result backend** (Redis, DB — often unnecessary), beat scheduler
- [ ] **Tasks** — `@shared_task`, `delay` vs `apply_async` (countdown, eta, expires, queue, priority), task signatures, `bind=True` (`self.retry`), task naming
- [ ] **Worker pools** — `prefork` (default, CPU), `threads`, `gevent`/`eventlet` (I/O), `solo`; `--concurrency`; `--autoscale`
- [ ] **Reliability settings** — `acks_late=True` + `task_reject_on_worker_lost` (at-least-once), **idempotent tasks** (required with acks_late), `worker_prefetch_multiplier=1` for long tasks, visibility timeout with Redis/SQS (long tasks re-delivered!), `task_time_limit`/`task_soft_time_limit`, `max_tasks_per_child`/`max_memory_per_child` (leaks)
- [ ] **Retries** — `autoretry_for`, `retry_backoff`, `retry_jitter`, `max_retries`, retrying only transient errors
- [ ] **Routing** — multiple queues for priorities/isolation (bulkheads), dedicated workers per queue, `task_routes`
- [ ] **Canvas** — `chain`, `group`, `chord` (needs result backend; failure semantics), `starmap`/`chunks`; when to use a workflow engine instead
- [ ] **Scheduling** — Celery beat (single instance! duplicates if scaled), django-celery-beat, RedBeat; alternatives: K8s CronJobs, APScheduler
- [ ] **Passing arguments** — pass IDs not ORM objects, JSON serializer (not pickle), payload size limits
- [ ] **Transactional enqueueing** — enqueue in `transaction.on_commit` to avoid tasks running before the row is committed; or use the outbox pattern
- [ ] **Monitoring** — Flower, Celery events, queue depth metrics, task latency/failure metrics, Prometheus exporters, alert on backlog
- [ ] **Common production issues** — tasks lost on deploy (no acks_late), duplicated tasks (visibility timeout), stuck workers, memory leaks, beat duplicates, Redis broker eviction, huge backlogs after outages, poison tasks
- [ ] **Graceful worker shutdown** — warm shutdown on SIGTERM, K8s `terminationGracePeriodSeconds` > longest task, or make tasks resumable

### 15.2 Alternatives
- [ ] **RQ** (Redis Queue, simple), **Dramatiq** (simpler/more reliable defaults), **Huey**, **arq** (asyncio + Redis), **Taskiq** (async), **SAQ**; Django's built-in Tasks framework (Django 6.0) — awareness
- [ ] **Durable workflow engines** — **Temporal** (Python SDK), Prefect, Hatchet, AWS Step Functions, Inngest — for long-running, multi-step, retryable workflows
- [ ] **Cron & scheduling** — APScheduler, `schedule`, distributed locks for single execution

### 15.3 Messaging & Streaming Clients
- [ ] **Kafka** — **confluent-kafka-python** (librdkafka; recommended for production), aiokafka (asyncio), kafka-python (legacy); producer configs (acks, idempotence, linger, compression, delivery callbacks, `flush` on shutdown), consumer configs (group.id, manual commits, `max.poll.interval.ms` with slow processing, rebalance callbacks), Schema Registry serializers (Avro/Protobuf), exactly-once transactions; FastStream (framework for Kafka/RabbitMQ/NATS/Redis)
- [ ] **RabbitMQ** — `pika` (blocking, not thread-safe), `aio-pika`, `kombu` (Celery's messaging library); acks, prefetch, DLX
- [ ] **AWS** — `boto3` SQS (long polling, visibility timeout, batch ops, DLQ), SNS, Kinesis, EventBridge; `aioboto3`
- [ ] **Redis Streams** consumer groups; **NATS** (nats-py); Google Pub/Sub client
- [ ] **Stream processing in Python** — Faust (faust-streaming fork), Bytewax, Quix Streams, PyFlink, Spark Structured Streaming (PySpark) — awareness

---

## 16. Authentication, Authorization & Python Security (P0)

### 16.1 AuthN/AuthZ Concepts
- [ ] Session/cookie vs token-based auth; stateless vs stateful trade-offs
- [ ] **JWT** — structure, claims (`iss`, `sub`, `aud`, `exp`, `iat`, `jti`), HS256 vs RS256/ES256, validation checklist (algorithm allowlist, audience, issuer, expiry, clock skew), JWKS & key rotation (`kid`), refresh token rotation & revocation strategies, storage in browsers (HttpOnly cookies vs localStorage)
- [ ] **OAuth 2.0 / 2.1 & OIDC** — Authorization Code + PKCE, Client Credentials, Device Code, refresh tokens; ID token vs access token; discovery; scopes; token introspection; token exchange
- [ ] **IdPs** — Keycloak, Auth0, Okta, Cognito, Entra ID; SAML awareness; SSO; MFA (TOTP via `pyotp`), passkeys/WebAuthn (`py_webauthn`)
- [ ] **Service-to-service auth** — mTLS, client-credentials JWTs, signed requests (HMAC)
- [ ] **Authorization models** — RBAC, ABAC, ReBAC (OpenFGA/SpiceDB/Permit), policy engines (OPA, Oso, Casbin/pycasbin); object-level authorization to prevent IDOR/BOLA; multi-tenant isolation (tenant filters on every query, Postgres RLS)

### 16.2 Python Security Libraries
- [ ] **Password hashing** — `argon2-cffi`, `bcrypt`, `passlib` (maintenance concerns), Django hashers; never `hashlib.sha256` for passwords
- [ ] **JWT/JOSE** — `PyJWT`, `joserfc`/`authlib` (python-jose is unmaintained), Authlib for OAuth2/OIDC clients & servers
- [ ] **Crypto** — `cryptography` (Fernet, AES-GCM, RSA/ECDSA, X.509), `secrets` (tokens, `compare_digest`), `hmac.compare_digest` (constant-time)
- [ ] **Never use** `random` for security tokens

### 16.3 Python-Specific Vulnerabilities (P0)
- [ ] **SQL injection** via f-strings/`%` formatting in raw queries; use parameters; ORM `extra()`/`raw()` risks
- [ ] **Command injection** — `os.system`, `subprocess(..., shell=True)` with user input → use argument lists, `shlex.quote`
- [ ] **Insecure deserialization** — `pickle`/`shelve`/`marshal` on untrusted data = RCE; `yaml.load` → `yaml.safe_load`; `jsonpickle`
- [ ] **`eval`/`exec`/`compile`** on user input; `ast.literal_eval` for literals only
- [ ] **XML attacks** (XXE, billion laughs) → `defusedxml`
- [ ] **SSRF** — validating outbound URLs, blocking internal IPs/metadata endpoints, DNS rebinding
- [ ] **Path traversal** — `os.path.join` with absolute user paths, `Path.resolve()` + prefix checks, `werkzeug.utils.secure_filename`
- [ ] **Template injection (SSTI)** — Jinja2 with user-controlled templates; sandboxing
- [ ] **ReDoS** — catastrophic regex backtracking; timeouts / `re2`
- [ ] **Mass assignment** — explicit Pydantic/DRF input schemas, `extra="forbid"`
- [ ] **Open redirects**, **CORS misconfiguration**, **CSRF** in cookie-auth APIs
- [ ] **Timing attacks** — constant-time comparisons
- [ ] **Secrets** — not in code/git; env vars/secret managers; `SecretStr`; not in logs/tracebacks/Sentry
- [ ] **Supply chain** — typosquatting on PyPI, malicious packages, dependency confusion with private indexes, hash-pinned lockfiles (`--require-hashes`, `uv.lock`), Trusted Publishing, Sigstore attestations
- [ ] **Security tooling** — **Bandit** (SAST), **pip-audit**/Safety/OSV-Scanner (dependency CVEs), Semgrep, Ruff security rules (`S`), Dependabot/Renovate, secret scanning (gitleaks, trufflehog), container scanning (Trivy)

### 🎯 Frequently Asked — Security
- How do you implement JWT auth with refresh tokens in FastAPI/DRF? How do you revoke tokens?
- Why is `pickle` dangerous? What about `yaml.load`?
- How do you prevent IDOR in a multi-tenant API?
- How do you store and rotate secrets for Python services?

---

## 17. Testing in Python (P0)

### 17.1 Strategy
- [ ] Test pyramid vs trophy; unit vs integration vs contract vs E2E; what to mock and what not to (don't mock what you don't own; prefer fakes)
- [ ] Test behavior, not implementation; FIRST principles; test naming; Arrange-Act-Assert
- [ ] TDD/BDD (pytest-bdd, behave)
- [ ] Coverage (`coverage.py`, branch coverage) and its limits; **mutation testing** (mutmut, cosmic-ray)
- [ ] Flaky tests — causes (time, ordering, shared state, network, async) and fixes; `pytest-randomly`, `pytest-rerunfailures` (as a stopgap)

### 17.2 pytest Deep Dive (P0)
- [ ] Test discovery, assert rewriting, `-k`, `-m`, `-x`, `--lf`, `-vv`, `--pdb`
- [ ] **Fixtures** — scopes (function/class/module/package/session), `yield` fixtures for teardown, `conftest.py` hierarchy, autouse, fixture factories, parametrized fixtures, `request` object, fixture dependency graph
- [ ] **`@pytest.mark.parametrize`** (ids, indirect), custom markers & `pytest.ini`/`pyproject.toml` config
- [ ] Built-in fixtures — `tmp_path`, `monkeypatch`, `capsys`/`caplog`, `recwarn`
- [ ] `pytest.raises` (`match=`), `pytest.approx`, `pytest.warns`
- [ ] **Plugins** — `pytest-xdist` (parallel), `pytest-cov`, `pytest-django`, **`pytest-asyncio`**/**anyio** plugin (async tests, event loop scope), `pytest-mock` (`mocker`), `pytest-benchmark`, `pytest-timeout`, `syrupy` (snapshots)
- [ ] Writing a simple pytest plugin / hooks (awareness)

### 17.3 Mocking (P0)
- [ ] `unittest.mock` — `Mock` vs `MagicMock` vs `AsyncMock`, `return_value`, `side_effect` (exceptions, iterables, functions), `assert_called_once_with`, `call_args_list`
- [ ] **`patch` where it's used, not where it's defined** (the #1 mocking bug), `patch.object`, `patch.dict`, as decorator/context manager
- [ ] **`autospec=True`** / `create_autospec` (catch signature mismatches)
- [ ] Over-mocking smells; prefer dependency injection and fakes

### 17.4 Test Tooling
- [ ] **Test data** — `factory_boy` (factories, SubFactory, traits), `Faker`, `model_bakery`
- [ ] **Property-based testing** — **Hypothesis** (strategies, shrinking, stateful testing)
- [ ] **HTTP mocking** — `responses` (requests), `respx` (httpx), `pytest-httpx`, `vcrpy`/`pytest-recording` (cassettes), WireMock
- [ ] **Time** — `freezegun`, `time-machine`
- [ ] **AWS** — `moto`; LocalStack
- [ ] **Real dependencies** — **testcontainers-python** (Postgres, Redis, Kafka), docker-compose in CI; transactional test isolation vs truncation
- [ ] **Django** — `TestCase` (transaction rollback) vs `TransactionTestCase`, `pytest-django` (`db` fixture, `django_assert_num_queries`), `override_settings`
- [ ] **FastAPI** — `TestClient`, `httpx.AsyncClient` + `ASGITransport`, dependency overrides
- [ ] **Celery** — `task_always_eager` (and why it hides bugs), calling task functions directly, `celery.contrib.pytest`
- [ ] **Contract testing** — Pact (pact-python), schemathesis (property-based API testing from OpenAPI)
- [ ] **Load testing** — **Locust** (Python), k6, Gatling
- [ ] **Multi-version testing** — `tox`, `nox`; CI matrix

---

## 18. Packaging, Tooling, Logging & Configuration (P0)

### 18.1 Environments & Dependencies
- [ ] **Virtual environments** — `venv`, `virtualenv`, why never install into system Python; conda/mamba (data science, non-Python deps); pyenv/`uv python` for multiple interpreters
- [ ] **pip** — requirements files, constraints files, editable installs (`-e`), `--require-hashes`, private indexes (`--index-url` vs `--extra-index-url` and dependency confusion), resolver backtracking
- [ ] **Lock files & reproducibility** — `pip-tools` (`pip-compile`), **Poetry** (`poetry.lock`), **PDM**, **Hatch**, **uv** (`uv.lock`, extremely fast resolver/installer, `uv sync`, `uv run`, `uv tool`, workspaces — now the dominant modern choice), Pipenv (legacy); PEP 751 `pylock.toml` standard lock format (awareness)
- [ ] **Direct vs transitive dependencies**, version specifiers (`~=`, `>=,<`), semantic versioning, upper-bound pinning debates for libraries vs apps
- [ ] **Dependency upgrades** — Dependabot/Renovate, upgrade cadence, deprecations

### 18.2 Packaging
- [ ] **`pyproject.toml`** (PEP 517/518/621) — `[project]` metadata, dependencies, optional-dependencies (extras), `[build-system]`, `[tool.*]` sections
- [ ] **Build backends** — setuptools, hatchling, flit-core, pdm-backend, poetry-core, maturin (Rust), scikit-build-core (C/C++), `uv_build`
- [ ] **Distributions** — sdist vs wheel, pure vs platform wheels, `manylinux`/`musllinux` tags, `cibuildwheel`, ABI3
- [ ] **Project layout** — `src/` layout vs flat, namespace packages, entry points (`[project.scripts]`, plugin entry points)
- [ ] **Publishing** — PyPI/TestPyPI, `twine`/`uv publish`, Trusted Publishing (OIDC), private registries (Artifactory, CodeArtifact, Nexus)
- [ ] **Monorepos** — uv workspaces, Pants, Bazel (rules_python) — awareness
- [ ] **Shipping apps** — Docker images, zipapps/shiv/pex, PyInstaller (desktop/CLIs)

### 18.3 Code Quality Tooling
- [ ] **Ruff** (linter + formatter; replaces flake8, isort, pyupgrade, many pylint rules, Black-compatible formatting), **Black**, isort, Pylint, flake8 plugins
- [ ] **Type checking** (§5) — mypy/pyright in CI
- [ ] **pre-commit** hooks
- [ ] Complexity & dead code — radon, vulture
- [ ] **Documentation** — docstring styles (Google/NumPy/reST), Sphinx, MkDocs + mkdocstrings, OpenAPI docs for APIs, ADRs
- [ ] **Code review standards** for Python teams; style guides (PEP 8, Google Python Style Guide)

### 18.4 Logging (P0)
- [ ] **`logging` architecture** — loggers (hierarchy, `getLogger(__name__)`, propagation), handlers, formatters, filters, levels; root logger pitfalls; `logging.config.dictConfig`
- [ ] Lazy formatting (`logger.info("x=%s", x)`), `logger.exception` in except blocks, `exc_info`, `stack_info`, `extra`
- [ ] **Structured/JSON logging** — **structlog**, `python-json-logger`, loguru (convenience); consistent fields (service, env, trace_id, request_id, user/tenant)
- [ ] **Request context** — `contextvars` + logging filters/processors to inject request IDs & trace IDs (works in asyncio)
- [ ] Performance — `QueueHandler`/`QueueListener` for non-blocking logging, avoiding expensive logs in hot paths
- [ ] Log to stdout in containers; no PII/secrets; log levels per module; third-party logger noise control
- [ ] Gunicorn/Uvicorn/Celery logging configuration integration

### 18.5 Configuration Management
- [ ] **12-factor config** — env vars; `.env` for local only (`python-dotenv`)
- [ ] **pydantic-settings** — typed, validated settings; nested; secrets files; fail fast at startup
- [ ] Dynaconf, Hydra/OmegaConf (ML), django-environ
- [ ] Secrets — AWS Secrets Manager/SSM, Vault (`hvac`), K8s Secrets; rotation; caching secrets
- [ ] Feature flags — Unleash, LaunchDarkly, Flagsmith, OpenFeature Python SDK

### 18.6 CLIs & Tooling Scripts
- [ ] `argparse`, **click**, **Typer**, rich/textual for terminal UX; packaging CLIs with entry points; `uv tool install`

---

## 19. Python Performance Engineering (P0)

- [ ] **Methodology** — define SLOs, measure (APM, profilers), find bottleneck (CPU, I/O, DB, GIL contention, serialization, memory/GC), fix, re-measure
- [ ] **Algorithmic & data-structure choices** — sets/dicts for lookups, `deque`, `heapq`, `bisect`, avoiding quadratic loops
- [ ] **Micro-optimizations that matter** — built-ins & comprehensions, local variable lookups in hot loops, `str.join`, avoiding repeated attribute lookups, `__slots__`, generators to cut memory, `functools.cache`
- [ ] **I/O-bound services** — async I/O, connection pooling (HTTP & DB), batching, concurrency limits, HTTP keep-alive, avoiding N+1 DB/HTTP calls, caching
- [ ] **CPU-bound work** — move off the request path (Celery/queues), process pools, NumPy/Polars vectorization, Rust/Cython extensions, PyPy, free-threaded builds
- [ ] **Serialization** — `orjson`/`msgspec` vs `json`; Pydantic v2 vs v1; DRF serializer overhead; response size (pagination, field selection, compression)
- [ ] **Startup time & memory** — lazy imports, `python -X importtime`, reducing dependencies, `gc.freeze` + preload for CoW
- [ ] **Web server tuning** — workers/threads, keep-alive, timeouts, uvloop/httptools, multiple processes per container vs more pods
- [ ] **Database** — query optimization, indexes, `EXPLAIN ANALYZE`, eager loading, bulk ops, COPY, read replicas, caching
- [ ] **Load testing** — Locust/k6; latency percentiles; coordinated omission; capacity planning
- [ ] **GC tuning** — `gc.set_threshold`, `gc.freeze`, disabling GC in specific hot paths (Instagram's case study) — awareness
- [ ] **Have a performance story** — "reduced p99 from X to Y by …" with numbers

---

## 20. Data & ML Stack Awareness (P1)

> Python backends often sit next to data and ML systems; senior Python engineers are expected to be fluent with the basics.

- [ ] **NumPy** — ndarrays, vectorization, broadcasting, dtypes, memory layout
- [ ] **pandas** — DataFrame/Series, indexing (`loc`/`iloc`), groupby/merge/pivot, vectorized ops vs `apply`, memory (dtypes, categoricals), chunked reading, pandas 2.x Arrow backend
- [ ] **Polars** (Rust, lazy API, much faster), **PyArrow** (columnar memory, Parquet), **DuckDB** (in-process SQL analytics on files/DataFrames)
- [ ] **Jupyter** notebooks — exploration vs production code; papermill
- [ ] **ETL in Python** — pipelines, Airflow/Dagster/Prefect orchestration, PySpark basics
- [ ] **ML model serving** — FastAPI + loaded model in lifespan, BentoML, Ray Serve, TorchServe, Triton, KServe; ONNX Runtime; batching requests; GPU vs CPU; model versioning; MLflow model registry
- [ ] **scikit-learn / PyTorch** basics — training vs inference, pickled model security (prefer safetensors/ONNX)

---

# PART D — DATA

## 21. SQL & Relational Databases (P0)

### 21.1 SQL Fluency
- [ ] Joins (inner/outer/cross/self, semi/anti-joins with `EXISTS`/`NOT EXISTS`, `NOT IN` + NULL trap), `GROUP BY`/`HAVING`, subqueries (correlated), **CTEs & recursive CTEs**, **window functions** (`ROW_NUMBER`, `RANK`, `DENSE_RANK`, `LAG`/`LEAD`, running totals, frames), `UNION` vs `UNION ALL`, NULL semantics, `CASE`, upserts (`ON CONFLICT`, `ON DUPLICATE KEY`, `MERGE`), JSON operators (Postgres `jsonb`)
- [ ] **Pagination** — OFFSET vs keyset/seek
- [ ] **Classic SQL problems** — Nth highest salary, delete duplicates, top-N per group, consecutive days (gaps & islands), running totals, median, month-over-month growth, employees earning more than managers

### 21.2 Modeling
- [ ] ER modeling, normalization (1NF–BCNF) & denormalization trade-offs, keys (surrogate vs natural; serial vs UUIDv4 vs UUIDv7/ULID and index locality), constraints, audit columns, soft delete, history/temporal tables, tree structures (adjacency list, materialized path, closure table), money as DECIMAL + currency, multi-tenant schemas

### 21.3 Indexing & Query Optimization
- [ ] **B+tree internals**, clustered (InnoDB) vs heap (Postgres) + secondary indexes, **composite index & leftmost prefix**, covering indexes (`INCLUDE`), partial & expression indexes, GIN/GiST/BRIN/hash, full-text; index killers (functions on columns, implicit casts, leading wildcards); cost of indexes on writes
- [ ] **`EXPLAIN (ANALYZE, BUFFERS)`** — seq vs index vs index-only vs bitmap scans; nested loop vs hash vs merge join; row estimates; stale statistics; `pg_stat_statements`; slow query log

### 21.4 Transactions & Concurrency
- [ ] ACID implementation (WAL, undo, MVCC, locks)
- [ ] **Isolation levels & anomalies** (dirty read, non-repeatable read, phantom, lost update, write skew); defaults (Postgres RC, MySQL RR); Postgres SSI
- [ ] **MVCC** — Postgres tuple versions, VACUUM, bloat, wraparound; InnoDB undo logs
- [ ] Row/table locks, gap/next-key locks (InnoDB), `SELECT … FOR UPDATE [SKIP LOCKED | NOWAIT]` (DB-backed job queues), advisory locks, deadlock detection & avoidance (consistent lock order, short transactions)
- [ ] **Optimistic concurrency** — version columns, conditional updates (`UPDATE … WHERE stock > 0`)

### 21.5 Scaling
- [ ] Connection limits & poolers (PgBouncer, RDS Proxy); read replicas & **read-your-writes**; replication (sync/async/semi-sync, physical vs logical); failover (Patroni, RDS Multi-AZ)
- [ ] **Partitioning** (range/list/hash, pruning, retention by dropping partitions; pg_partman), **sharding** (hash/range/directory/tenant, shard key choice, hot shards, resharding, cross-shard queries; Citus, Vitess)
- [ ] Distributed SQL (Spanner, CockroachDB, YugabyteDB, TiDB), **Aurora** architecture
- [ ] **Storage engines** — B-tree vs LSM-tree (memtables, SSTables, compaction, amplification, bloom filters)
- [ ] **Operations** — backups & PITR, online schema changes (`CREATE INDEX CONCURRENTLY`, gh-ost/pt-osc), batched backfills, monitoring (connections, replication lag, locks, bloat, cache hit ratio)
- [ ] **PostgreSQL specifics** — JSONB, extensions (PostGIS, pgvector, TimescaleDB), `LISTEN/NOTIFY`, RLS, logical replication; **MySQL** — InnoDB, binlog, gap locks

### 🎯 Frequently Asked
- How does an index work? Why isn't my composite index used?
- Explain isolation levels with an example anomaly
- How would you shard a large table and pick the shard key?
- Zero-downtime migration of a huge table from a Django/Alembic codebase
- A query got slow suddenly — walk through debugging

---

## 22. NoSQL, Search & Storage (P0)

- [ ] **SQL vs NoSQL decision** — access patterns, consistency, scale, query flexibility, transactions
- [ ] **DynamoDB** — partition/sort keys, GSI/LSI, single-table design, capacity modes, hot partitions, conditional writes, transactions, Streams, TTL, global tables; `boto3`/PynamoDB
- [ ] **MongoDB** — embedding vs referencing, indexes (ESR rule), aggregation pipeline, replica sets, write/read concerns, sharding & shard keys, transactions, change streams
- [ ] **Cassandra** — ring & consistent hashing, RF, tunable consistency (R + W > N), query-first modeling (partition key + clustering columns), write/read paths, compaction strategies, tombstones, repairs
- [ ] **Elasticsearch/OpenSearch** — inverted index, analyzers, mappings (`text` vs `keyword`), shards/replicas, NRT refresh, BM25, bool queries, aggregations, `search_after`, syncing from DB via CDC, zero-downtime reindex with aliases
- [ ] **Vector search** — embeddings, HNSW/IVF, pgvector, Qdrant/Pinecone/Weaviate/Milvus, hybrid search
- [ ] **Time-series** (TimescaleDB, InfluxDB), **graph** (Neo4j), **OLAP** (ClickHouse, Druid) — awareness
- [ ] **Object storage (S3)** — consistency, multipart uploads, **pre-signed URLs** (`boto3.generate_presigned_url/post`), lifecycle & storage classes, events, encryption; metadata in DB + blobs in S3 + CDN

---

## 23. Caching & Redis (P0)

- [ ] **Cache layers** — browser/CDN/gateway/in-process (`functools.lru_cache`, `cachetools` TTLCache)/distributed (Redis/Memcached)/DB buffer pool
- [ ] **Strategies** — cache-aside, read-through, write-through, write-behind, write-around, refresh-ahead
- [ ] **Eviction** — LRU, LFU, TTL, Redis `maxmemory-policy`
- [ ] **Invalidation & consistency** — delete-on-write, delayed double delete, versioned keys, event-driven invalidation (CDC), TTL jitter
- [ ] **Failure modes** — **stampede** (locks/single-flight, probabilistic early expiration, stale-while-revalidate), **penetration** (cache negatives, Bloom filter), **avalanche** (jittered TTLs, multi-level cache), **hot keys** (local L1, key splitting), big keys
- [ ] **Python caching tools** — `functools.cache`/`lru_cache` (per-process, unbounded risk, methods & `self` leaks), `cachetools`, `aiocache`, `django.core.cache`, `fastapi-cache2`, `dogpile.cache` (stampede protection)
- [ ] **Per-process vs shared cache** in multi-worker Gunicorn deployments (N copies, inconsistent invalidation)
- [ ] **Redis deep dive** — single-threaded execution, data types (String, Hash, List, Set, Sorted Set, Bitmap, HyperLogLog, Geo, Streams), expiration, persistence (RDB/AOF), replication, Sentinel, **Cluster** (16384 slots, hash tags), pipelining, `MULTI/EXEC/WATCH`, **Lua scripts**, distributed locks (`SET NX PX`, safe release via Lua, Redlock debate, fencing tokens; `redis-py` `Lock`, `pottery`), Pub/Sub vs Streams, `SCAN` not `KEYS`, Valkey fork
- [ ] **Use cases** — sessions, rate limiting, leaderboards, idempotency keys, dedupe, queues (Celery/RQ broker), counters, feature flags
- [ ] **HTTP caching** — `Cache-Control`, `ETag`/`If-None-Match`, `Last-Modified`, `Vary`, CDN caching & purging

### 🎯 Frequently Asked
- Cache-aside implementation in Python with stampede protection
- How do you keep cache and DB consistent?
- Why is `@lru_cache` on a method in a web app risky?
- Distributed lock in Redis — implementation and failure modes

---

# PART E — DISTRIBUTED SYSTEMS & ARCHITECTURE

## 24. Messaging & Event Streaming (P0)

- [ ] **Why async messaging** — decoupling, load leveling, fan-out, resilience
- [ ] **Queue vs pub/sub vs log (Kafka)**; push vs pull; commands vs events; event notification vs event-carried state transfer vs event sourcing
- [ ] **Delivery semantics** — at-most-once, **at-least-once** (default reality), exactly-once (idempotency + transactions); **idempotent consumers** (dedupe tables, unique constraints, Redis SETNX)
- [ ] **Ordering** — per-partition/per-key; what breaks it (retries, parallel consumers)
- [ ] **Retries, DLQs, poison messages**, backoff, parking lots, replay tooling
- [ ] **Kafka deep dive** — brokers, topics, partitions, replication, ISR, KRaft, retention & compaction, producer (`acks=all`, idempotence, batching, compression, keys → partitions), consumer groups & rebalancing (cooperative sticky, static membership), offset commits (manual after processing), lag monitoring, exactly-once transactions, Schema Registry & compatibility modes, Kafka Connect & **Debezium CDC**, partition sizing, hot partitions; Python specifics (confluent-kafka poll loop, slow processing vs `max.poll.interval.ms`, threads per consumer)
- [ ] **RabbitMQ** — exchanges (direct/topic/fanout/headers), bindings, acks, prefetch, DLX, quorum queues, publisher confirms
- [ ] **SQS/SNS/EventBridge/Kinesis**, Google Pub/Sub, NATS, Redis Streams; Kafka vs RabbitMQ vs SQS comparison
- [ ] **Patterns** — **dual-write problem**, **transactional outbox** (polling publisher or CDC), inbox, CDC, choreography vs orchestration, competing consumers, claim check (large payloads in S3), request-reply, fan-out/fan-in, event versioning & schema evolution, out-of-order handling

### 🎯 Frequently Asked
- How do you publish an event reliably after a DB commit in Django/FastAPI?
- How do you guarantee per-customer ordering while scaling consumers?
- Celery vs Kafka — when is each appropriate?
- How do you handle duplicate messages?

---

## 25. Distributed Systems Theory (P0)

- [ ] **Fallacies of distributed computing**; partial failures; timeouts can't distinguish slow vs dead
- [ ] **CAP & PACELC**; **consistency models** — linearizable, sequential, causal, read-your-writes, monotonic reads, eventual; linearizability vs serializability
- [ ] **Replication** — single-leader, multi-leader, leaderless; sync vs async; conflict resolution (LWW, version vectors, CRDTs); quorums (R + W > N), sloppy quorum, hinted handoff, read repair, Merkle-tree anti-entropy
- [ ] **Partitioning** — range vs hash, **consistent hashing + virtual nodes**, rebalancing, local vs global secondary indexes
- [ ] **Time** — clock skew, NTP, monotonic clocks, Lamport & vector clocks, hybrid logical clocks, TrueTime
- [ ] **Consensus** — Paxos (concept), **Raft** (leader election, log replication, terms), ZooKeeper/etcd; leader election; leases; **fencing tokens**; split brain; gossip & failure detection
- [ ] **Distributed transactions** — 2PC (blocking), Saga (choreography vs orchestration, compensations), TCC, outbox; workflow engines (Temporal, Step Functions)
- [ ] **Idempotency** — idempotency keys (storage, TTL, concurrent duplicates, response replay)
- [ ] **Unique IDs** — UUIDv4 vs UUIDv7/ULID, Snowflake, ticket servers
- [ ] **Probabilistic structures** — Bloom filter, Count-Min Sketch, HyperLogLog, Merkle trees
- [ ] **Queueing** — Little's law, utilization vs latency, tail latency amplification, hedged requests, backpressure
- [ ] **Landmark papers** — Dynamo, GFS, MapReduce, Bigtable, Spanner, Raft, Kafka, Chubby, Zanzibar, "The Tail at Scale"

---

## 26. Microservices, DDD & Architecture Styles (P0)

### 26.1 Microservices
- [ ] **Monolith vs modular monolith vs microservices** trade-offs; when not to split; distributed monolith anti-pattern; Conway's law & team topologies
- [ ] **Decomposition** — business capability, bounded contexts, Strangler Fig migration, anti-corruption layer
- [ ] **Communication** — sync (REST/gRPC) vs async (events); API gateway, BFF; service discovery; service mesh (Istio/Linkerd)
- [ ] **Data** — database per service, API composition, CQRS read models, sagas, event sourcing, outbox
- [ ] **Cross-cutting** — config, secrets, observability, correlation IDs, auth propagation, resilience, shared libraries (internal packages) without coupling
- [ ] **Deployment** — rolling, blue-green, canary, feature flags, backward-compatible APIs/events, expand/contract DB changes
- [ ] **Testing** — contract tests (Pact), component tests, few E2E
- [ ] **12-Factor App** — every factor, with Python examples (config via env, stateless processes, logs to stdout, disposability)

### 26.2 Domain-Driven Design (P1)
- [ ] Strategic — subdomains (core/supporting/generic), ubiquitous language, bounded contexts, context maps (ACL, shared kernel, customer-supplier, conformist, open host), event storming
- [ ] Tactical — entities, value objects (frozen dataclasses), aggregates & invariants, repositories, domain services, application services, domain events, rich vs anemic models
- [ ] **"Architecture Patterns with Python" (Cosmic Python)** — repository, unit of work, service layer, message bus, CQRS in Python

### 26.3 Architecture Styles (P1)
- [ ] Layered, **hexagonal/ports & adapters**, clean/onion architecture in Python (keeping Django/FastAPI at the edges)
- [ ] Event-driven, CQRS, event sourcing (eventsourcing library — awareness), serverless (Lambda), cell-based, multi-tenant SaaS models (silo/pool/bridge)
- [ ] **Architecture practice** — quality attributes & trade-offs, C4 model, ADRs, RFCs/design docs, fitness functions, tech debt management, build vs buy, one-way vs two-way door decisions

---

## 27. Resilience & High Availability (P0)

- [ ] **Failure modes** — cascading failures, retry storms, thundering herds, slow dependencies, resource exhaustion (workers, DB connections, file descriptors), GC/stop-the-world, poison messages, metastable failures
- [ ] **Patterns** — **timeouts everywhere** (httpx/requests/DB/Redis), **retries with exponential backoff + jitter** (`tenacity`, `backoff`, `urllib3.Retry`), retry budgets, **circuit breakers** (`pybreaker`, `aiobreaker`, `purgatory`), bulkheads (separate worker pools/queues), rate limiting, load shedding, backpressure, fallbacks/graceful degradation, health checks (liveness/readiness), idempotency, hedged requests, queue-based load leveling
- [ ] **HA & DR** — availability math (nines), SPOF elimination, multi-AZ/multi-region, active-active vs active-passive, RTO/RPO, DR strategies, failover drills
- [ ] **Chaos engineering** — Toxiproxy, Chaos Mesh, AWS FIS, game days
- [ ] **Graceful shutdown** of Gunicorn/Uvicorn/Celery/Kafka consumers

---

## 28. Rate Limiting & Throttling (P0)

- [ ] **Why & where** — abuse/DoS protection, fairness, cost, protecting downstreams; client, CDN/WAF, Nginx/Envoy, API gateway, app, outbound calls
- [ ] **Keys** — user, API key, IP, tenant, endpoint; rate limits vs quotas; concurrency limits
- [ ] **Algorithms** — **token bucket**, leaky bucket, fixed window (boundary burst), sliding window log, sliding window counter, GCRA, adaptive/AIMD — compare accuracy, memory, burst handling
- [ ] **Distributed** — Redis `INCR`+`EXPIRE`, sorted sets for sliding logs, **Lua scripts for atomicity**, local + global hybrid, fail-open vs fail-closed, multi-region, hot keys, rule management, shadow mode, metrics
- [ ] **Client contract** — 429 + `Retry-After`, `RateLimit-*` headers, 503 for shedding; client backoff
- [ ] **Python tools** — **`limits`** library (storage backends, moving window), **slowapi** (FastAPI/Starlette), **django-ratelimit**, DRF throttling, Flask-Limiter, `aiolimiter` (outbound async limiting), `pyrate-limiter`; gateway-level (Kong, Envoy, AWS API Gateway, Nginx `limit_req`)
- [ ] **Practice** — code a thread-safe token bucket & sliding window in Python; asyncio version; Redis Lua token bucket; LLD with pluggable strategies; HLD "distributed rate limiter at 1M RPS"

---

## 29. API Design (P0)

- [ ] **REST** — resources & naming, HTTP method semantics (safe/idempotent), status codes (201+Location, 202, 204, 400, 401 vs 403, 404, 409, 412, 422, 429, 5xx distinctions), RFC 9457 Problem Details errors
- [ ] **Practical design** — pagination (cursor/keyset), filtering/sorting/sparse fields, bulk ops, long-running operations (202 + polling/webhooks), **idempotency keys** for POST, optimistic concurrency (`ETag`/`If-Match`), caching headers, versioning & deprecation (`Sunset`), backward-compatible evolution, OpenAPI-first (FastAPI generates; drf-spectacular), API style guides
- [ ] **Security** — OWASP API Top 10 (BOLA, broken auth, BOPLA/mass assignment, unrestricted resource consumption, BFLA, SSRF…), input validation via Pydantic/serializers, no sensitive data in URLs
- [ ] **Webhooks** — HMAC signatures + timestamps, retries, idempotent receivers, delivery logs
- [ ] **gRPC** — protobuf schema evolution, unary/streaming, deadlines, interceptors, L7 load balancing; REST vs gRPC
- [ ] **GraphQL** — schema, resolvers, N+1 & DataLoaders, complexity limits, persisted queries, federation (Strawberry)
- [ ] **Real-time** — polling vs long polling vs SSE vs WebSockets; scaling WebSockets (sticky sessions, Redis pub/sub, Channels layers)

---

# PART F — SYSTEM DESIGN (HLD)

## 30. System Design Framework & Estimation (P0)

- [ ] **Framework** — (1) requirements (functional + NFRs: scale, latency, availability, consistency, durability, security, cost) → (2) estimation → (3) APIs → (4) data model & storage choice → (5) high-level diagram & flows → (6) deep dives (bottlenecks, hot keys, consistency, failures) → (7) monitoring, security, evolution
- [ ] **Senior signals** — drive the conversation, quantify, articulate trade-offs, cover failure modes & operations, keep it simple first
- [ ] **Estimation** — 1 day ≈ 10⁵ s; QPS = DAU × actions / 86,400; peak 2–5×; storage = writes × size × retention × replication; bandwidth; cache size (80/20); servers needed
- [ ] **Latency numbers** — memory ~100 ns, SSD read ~100 µs, same-DC RTT ~0.5 ms, disk seek ~10 ms, cross-continent ~150 ms
- [ ] **Python-specific capacity thinking** — per-worker throughput of sync vs async Python services, GIL limits per process, scaling via processes/pods, offloading CPU work

---

## 31. Building Blocks & Techniques (P0)

- [ ] DNS, CDN, load balancers (L4/L7, algorithms, health checks), reverse proxies, API gateways, stateless app tier, caches, SQL/NoSQL, search, object storage, queues/streams, workers & schedulers, ID generators, rate limiters, service discovery, config & feature flags, notification providers, observability stack, analytics pipeline
- [ ] **Scaling** — horizontal/vertical, replication, sharding, caching, async processing, denormalization & precomputation, **fan-out on write vs read** (hybrid for celebrities), batching, autoscaling, multi-region
- [ ] **Storage selection cheat sheet** — RDBMS / Cassandra-DynamoDB / MongoDB / Redis / Elasticsearch / S3 / time-series / OLAP / graph / vector / Kafka
- [ ] **Specialized techniques** — geospatial indexing (geohash, quadtree, S2, H3), inverted indexes, tries for autocomplete, top-K with count-min sketch, sharded counters, leaderboards (sorted sets), feed generation, dedupe with Bloom filters, chunking & delta sync, video transcoding & ABR streaming, OT vs CRDT, presence, seat/inventory reservation under contention, double-entry ledgers, time-bucketed schedulers

---

## 32. Classic System Design Problems (P0)

> For each: requirements → estimates → APIs → data model → HLD → 2–3 deep dives → failures → monitoring. Practice **25+** aloud with a timer.

| # | Problem | Key deep dives |
|---|---------|----------------|
| 1 | [ ] URL Shortener | ID generation (base62/KGS), redirects, caching, analytics |
| 2 | [ ] Distributed Rate Limiter | Algorithms, Redis + Lua, placement, fail-open |
| 3 | [ ] Key-Value Store | Consistent hashing, replication, quorum, conflict resolution |
| 4 | [ ] Distributed Cache | Partitioning, eviction, hot keys |
| 5 | [ ] Unique ID Generator | Snowflake, clock skew |
| 6 | [ ] Web Crawler | Frontier, politeness, dedupe, async workers (asyncio crawler) |
| 7 | [ ] Notification System | Channels, preferences, priority queues, retries, provider rate limits |
| 8 | [ ] News Feed / Timeline | Fan-out strategies, ranking, caching |
| 9 | [ ] Chat System | WebSockets, ordering, receipts, offline sync, presence |
| 10 | [ ] Typeahead / Autocomplete | Trie/top-K, caching, data pipeline |
| 11 | [ ] Video Streaming (YouTube) | Upload, transcoding pipeline (Celery/queues), CDN, ABR |
| 12 | [ ] File Sync (Dropbox) | Chunking, dedupe, metadata, conflicts |
| 13 | [ ] Ride Hailing (Uber) | Location ingestion, geo index, matching |
| 14 | [ ] Proximity Service (Yelp) | Geohash/quadtree, read-heavy caching |
| 15 | [ ] Ticket Booking (BookMyShow) | Seat holds with TTL, contention, waiting room |
| 16 | [ ] Hotel Reservation | Inventory per date, double booking prevention |
| 17 | [ ] E-commerce Checkout | Cart, inventory reservation, order saga, flash sales |
| 18 | [ ] Payment System | Idempotency, ledger, PSP integration, reconciliation, webhooks |
| 19 | [ ] Digital Wallet | Ledger consistency, saga/TCC, audit |
| 20 | [ ] Distributed Job Scheduler | Time-partitioned storage, leader election, at-least-once, idempotent jobs |
| 21 | [ ] Distributed Message Queue | Partitions, logs, replication, consumer groups |
| 22 | [ ] Metrics & Alerting System | TSDB, cardinality, downsampling, alert evaluation |
| 23 | [ ] Logging Pipeline | Agents, Kafka buffer, indexing, retention tiers |
| 24 | [ ] Ad Click Aggregation | Stream processing, windows, exactly-once, reconciliation |
| 25 | [ ] Top-K Trending | Count-min sketch, sliding windows |
| 26 | [ ] Leaderboard | Redis sorted sets, sharding |
| 27 | [ ] Collaborative Editor | OT/CRDT, WebSockets |
| 28 | [ ] Food Delivery | Order lifecycle, dispatch, tracking |
| 29 | [ ] Online Judge | Sandboxed execution, queues, worker isolation |
| 30 | [ ] Webhook Delivery Platform | Retries, per-endpoint queues, signing, DLQ |
| 31 | [ ] Feature Flag Service | SDK caching, streaming updates, targeting |
| 32 | [ ] Multi-tenant SaaS Backend | Isolation models, noisy neighbors, per-tenant limits |
| 33 | [ ] Bulk CSV/Excel Import Service | Pre-signed uploads, chunked async processing (Celery), progress, partial failures |
| 34 | [ ] Report/Export Generation Service | Async jobs, large query streaming, S3 + signed links, throttling |
| 35 | [ ] ML Model Serving Platform | Model registry, batching, GPU/CPU autoscaling, A/B models, latency SLOs |
| 36 | [ ] LLM Chat / RAG Backend | Streaming (SSE), vector retrieval, LLM gateway (rate limits, fallbacks, caching), cost control |
| 37 | [ ] Search Service for E-commerce | Indexing via CDC, relevance, facets |
| 38 | [ ] Audit Log Service | Append-only, immutability, querying, retention |

---

# PART G — INFRASTRUCTURE & OPERATIONS

## 33. Networking (P0)

- [ ] OSI vs TCP/IP layers (L4 vs L7 LBs); IP/CIDR/subnets/NAT
- [ ] **TCP** — handshake, teardown, TIME_WAIT & ephemeral port exhaustion, flow/congestion control, Nagle, keep-alive, HOL blocking; **UDP**
- [ ] **HTTP/1.1 vs HTTP/2 vs HTTP/3 (QUIC)**; headers, cookies (Secure/HttpOnly/SameSite), CORS & preflight
- [ ] **TLS 1.2/1.3** handshake, certificates & chains, SNI, mTLS, cert rotation; Python `ssl` module, `certifi` CA bundles, corporate proxies & custom CAs
- [ ] **DNS** — resolution, record types, TTLs, DNS-based failover; DNS caching in Python clients
- [ ] "What happens when you type a URL" end to end
- [ ] Proxies (forward/reverse), load balancers, CDNs/Anycast, WebSockets, SSE, long polling
- [ ] Connection pooling & keep-alive (`requests.Session`, `httpx.Client` reuse — creating a client per request is a classic perf bug)
- [ ] **Tools** — curl, dig, ss/netstat, tcpdump, Wireshark, `openssl s_client`, mtr

---

## 34. Linux & OS (P1)

- [ ] Processes vs threads, scheduling, context switches, system calls, virtual memory, page cache, file descriptors & ulimits, I/O models (blocking, non-blocking, epoll, io_uring), signals (SIGTERM vs SIGKILL vs SIGINT vs SIGHUP; Python `signal` handlers only on main thread), cgroups & namespaces, OOM killer, copy-on-write fork
- [ ] **Commands** — top/htop, ps, free, vmstat, iostat, lsof, df/du, ss, strace, perf, journalctl, grep/awk/sed/jq, tail -f, systemd basics, cron
- [ ] **Scenarios** — high CPU, memory growth, disk full (deleted-but-open files), too many open files, zombie processes, stuck process (py-spy dump)

---

## 35. Docker & Kubernetes for Python Services (P0)

### 35.1 Docker for Python
- [ ] **Base images** — `python:3.x-slim` (Debian) vs alpine (musl → slow/broken wheels, avoid for most Python), distroless, Chainguard images
- [ ] **Multi-stage builds** — build wheels/install deps in builder stage, copy virtualenv into runtime stage; `uv` in Docker (cache mounts, `uv sync --frozen --no-dev`)
- [ ] **Env settings** — `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`, `PIP_NO_CACHE_DIR`, compiled bytecode at build time for faster startup
- [ ] **Layer caching** — copy lockfile and install deps before copying source
- [ ] **Security** — non-root user, minimal packages, image scanning (Trivy/Grype), no secrets in layers (BuildKit secrets)
- [ ] **PID 1 & signals** — exec form `CMD`, `tini`/`dumb-init`, Gunicorn graceful shutdown on SIGTERM
- [ ] **Image size** — removing build deps, `.dockerignore`, wheels caching
- [ ] **Docker Compose** for local dev (app + Postgres + Redis + Celery worker)

### 35.2 Kubernetes
- [ ] Architecture (control plane, kubelet, kube-proxy, etcd); Pods, Deployments, StatefulSets, DaemonSets, Jobs/CronJobs (migrations & batch tasks), Services, Ingress/Gateway API, ConfigMaps, Secrets, PV/PVC
- [ ] **Probes** — liveness vs readiness vs startup for Django/FastAPI (don't check DB in liveness); health endpoints
- [ ] **Resources** — requests/limits, CPU throttling, OOMKilled (exit 137), QoS classes; **Python worker count vs CPU limit** (don't run 9 Gunicorn workers on a 1-CPU limit)
- [ ] **Autoscaling** — HPA (CPU/RPS/custom metrics), **KEDA** for Celery/Kafka/SQS queue-depth scaling, VPA, Karpenter/Cluster Autoscaler
- [ ] **Deployments** — rolling updates, canary (Argo Rollouts/Flagger), running DB migrations safely (Job/init container, pre-deploy step), graceful shutdown (preStop + terminationGracePeriodSeconds > Gunicorn graceful timeout / longest Celery task)
- [ ] **Scheduling** — affinity/anti-affinity, topology spread across AZs, taints/tolerations, PDBs
- [ ] **Security** — RBAC, service accounts, IRSA/Workload Identity, network policies, pod security
- [ ] Helm / Kustomize, operators, service mesh awareness
- [ ] **Troubleshooting** — CrashLoopBackOff, ImagePullBackOff, Pending, OOMKilled, failing readiness; `kubectl describe/logs --previous/exec/top/port-forward`

---

## 36. CI/CD & IaC (P1)

- [ ] **Pipeline for Python services** — lint (Ruff), type-check (mypy/pyright), tests (pytest + coverage, xdist), security (Bandit, pip-audit), build image, scan, integration tests (Testcontainers), push, deploy, smoke tests
- [ ] **Tools** — GitHub Actions (setup-python/setup-uv, caching), GitLab CI, Jenkins, CircleCI; ArgoCD/Flux (GitOps)
- [ ] **Branching** — trunk-based development, short-lived branches, feature flags
- [ ] **Release strategies** — rolling, blue-green, canary, dark launches; rollback & roll-forward; migration compatibility
- [ ] **IaC** — Terraform (state, modules, plan/apply, drift), AWS CDK (Python!), Pulumi (Python), CloudFormation
- [ ] **Supply chain** — lockfiles with hashes, SBOM (CycloneDX for Python), signed images, Trusted Publishing, OIDC to cloud (no long-lived keys)
- [ ] **DORA metrics** — deploy frequency, lead time, change failure rate, MTTR

---

## 37. Cloud & Serverless (P1)

- [ ] **AWS core** — EC2/ASG, ECS/Fargate, EKS, **Lambda**, VPC (subnets, NAT, SG vs NACL, endpoints/PrivateLink), Route 53, CloudFront, ALB/NLB, API Gateway, S3, RDS/Aurora, DynamoDB, ElastiCache, OpenSearch, SQS/SNS/EventBridge/Kinesis/MSK, Step Functions, IAM (roles, least privilege), KMS, Secrets Manager/SSM, Cognito, WAF/Shield, CloudWatch/X-Ray/CloudTrail
- [ ] **boto3** — clients vs resources, sessions, credentials chain, paginators, waiters, retries config (`botocore.config.Config`), thread-safety (clients are thread-safe, sessions are not), `aioboto3`
- [ ] **Python on Lambda** — cold starts (package size, lazy imports, provisioned concurrency, SnapStart for Python), handler design, layers, container images, **AWS Lambda Powertools for Python** (logging, tracing, metrics, idempotency, batch processing, event parsing), Mangum (ASGI on Lambda), Chalice/Zappa/Serverless Framework/SAM; timeouts & concurrency limits; partial batch failures for SQS
- [ ] **GCP/Azure equivalents** — Cloud Run, Cloud Functions, GKE, Pub/Sub, Cloud SQL, BigQuery; Azure Functions, AKS, Service Bus, Cosmos DB
- [ ] **Well-Architected Framework** (6 pillars), cost optimization (Graviton, spot, rightsizing, data transfer costs), multi-region DR strategies, shared responsibility model

---

## 38. Observability (P0)

- [ ] **Concepts** — logs, metrics, traces (+ profiles); Golden Signals; RED & USE methods
- [ ] **Logging** — structured JSON (structlog), request/trace IDs via contextvars, PII masking, aggregation (ELK/EFK, Loki, Datadog, CloudWatch), sampling & cost
- [ ] **Metrics** — counters/gauges/histograms; percentiles vs averages; cardinality; **`prometheus_client`** (multiprocess mode for Gunicorn! `PROMETHEUS_MULTIPROC_DIR`), `django-prometheus`, `prometheus-fastapi-instrumentator`, StatsD/Datadog; Celery & queue metrics; DB pool metrics; business KPIs
- [ ] **Tracing** — **OpenTelemetry Python** (SDK, auto-instrumentation `opentelemetry-instrument`, instrumentations for Django/FastAPI/Flask/requests/httpx/SQLAlchemy/psycopg/Redis/Celery/Kafka), context propagation (W3C traceparent) across HTTP & queues, sampling (head vs tail), OTel Collector, backends (Jaeger, Tempo, Datadog, Honeycomb, X-Ray)
- [ ] **Error tracking** — **Sentry** (Python SDK integrations, performance monitoring, release tracking, scrubbing PII)
- [ ] **APM** — Datadog `ddtrace`, New Relic, Elastic APM; continuous profiling (Pyroscope, Datadog profiler)
- [ ] **SRE** — SLIs/SLOs/SLAs, error budgets, burn-rate alerts, actionable alerts with runbooks, dashboards (service → dependency → infra), synthetic checks

### 🎯 Frequently Asked
- How do you expose Prometheus metrics from a multi-worker Gunicorn app?
- How do you propagate trace context from an API into a Celery task?
- p99 latency doubled after a deploy — walk through your investigation

---

## 39. Security (P0)

- [ ] **OWASP Top 10** (2021 & 2025 editions) — broken access control, cryptographic failures, injection, insecure design, misconfiguration, vulnerable/outdated components & supply chain, auth failures, integrity failures (deserialization), logging/monitoring failures, SSRF, exceptional-condition mishandling
- [ ] **OWASP API Security Top 10**
- [ ] **Cryptography basics** — hashing vs encryption vs encoding vs signing; password hashing (Argon2id/bcrypt); AES-GCM; RSA/ECC; HMAC; envelope encryption with KMS; key rotation; TLS everywhere; field-level encryption for PII
- [ ] **Secure SDLC** — threat modeling (STRIDE), SAST (Bandit, Semgrep, CodeQL), DAST (ZAP), SCA (pip-audit, Snyk, Dependabot), secret scanning, container & IaC scanning
- [ ] **Python-specific risks** (§16.3) — pickle, yaml.load, eval, shell=True, SSTI, XXE, path traversal, ReDoS
- [ ] **Infrastructure** — least privilege IAM, network segmentation, zero trust, mTLS, WAF, DDoS protection, secrets management
- [ ] **Data protection & compliance** — PII classification, masking, GDPR/DPDP/CCPA (right to erasure), PCI-DSS (tokenize card data), SOC 2, HIPAA awareness, audit logs, retention

---

## 40. Production Engineering & Incidents (P0)

- [ ] **Incident lifecycle** — detect → triage → mitigate first (rollback, feature flag, scale, shed load) → resolve → blameless postmortem → action items; severity levels; incident commander; comms
- [ ] **On-call** — runbooks, alert quality, handoffs, toil reduction
- [ ] **Debug workflow** — dashboards → logs → traces → profiles (py-spy) → DB (slow queries, locks, connections) → infra (CPU throttling, OOM, DNS)
- [ ] **Python production scenarios to have answers/stories for**:
  - [ ] Gunicorn workers timing out (`WORKER TIMEOUT`) due to slow downstream / blocking calls
  - [ ] Event loop blocked in FastAPI by a sync library → latency spike for all requests
  - [ ] Memory leak in workers → OOMKills → fixed with tracemalloc/memray + `max_requests`
  - [ ] DB connection exhaustion (too many workers × pool size, leaked sessions)
  - [ ] Celery backlog after outage, duplicate task execution, lost tasks on deploy
  - [ ] Kafka consumer rebalance loops due to long processing
  - [ ] N+1 queries introduced by a serializer change
  - [ ] Cache stampede after deploy/flush
  - [ ] Dependency upgrade breaking prod (unpinned transitive dependency)
  - [ ] Timezone/DST bug, naive vs aware datetime bug
  - [ ] Duplicate payments from retries without idempotency
  - [ ] Certificate expiry, DNS issues, clock skew breaking JWTs
- [ ] **SRE practices** — error budgets, capacity planning, load tests before peak events, production readiness reviews (§49)

---

## 41. AI/LLM Integration for Python Backends (P1)

> Python is the lingua franca of AI. Senior Python backend engineers in 2026 are routinely expected to integrate LLMs.

- [ ] **LLM fundamentals** — tokens, context windows, temperature, embeddings, hallucinations, latency & cost per token
- [ ] **SDKs** — Anthropic, OpenAI, Google GenAI Python SDKs (sync & async clients, streaming, retries, timeouts), LiteLLM (multi-provider), Instructor / structured outputs with Pydantic
- [ ] **RAG** — ingestion, chunking, embeddings, vector stores (pgvector, Qdrant, Pinecone), hybrid search, reranking, citations, evaluation (RAGAS, DeepEval)
- [ ] **Tool calling, agents & MCP** — function calling, agent loops, Model Context Protocol servers (official Python SDK / FastMCP), frameworks (LangChain/LangGraph, LlamaIndex, Pydantic AI, OpenAI Agents SDK, Claude Agent SDK)
- [ ] **Serving LLM features in FastAPI** — SSE streaming, async concurrency limits, request timeouts, background jobs for long tasks, token-based rate limiting & quotas, semantic caching, fallback models, cost tracking per tenant
- [ ] **Security** — prompt injection (direct & indirect), data leakage, output validation, PII redaction, OWASP Top 10 for LLM apps
- [ ] **Observability** — Langfuse, LangSmith, Arize Phoenix, OpenTelemetry GenAI conventions
- [ ] **Using AI coding assistants effectively** — have a clear, balanced point of view for interviews

---

# PART H — LEADERSHIP, BEHAVIORAL & CAREER

## 42. Technical Leadership (P0)

- [ ] **Technical direction** — vision & roadmaps, RFCs/design docs, ADRs, design reviews, build vs buy, tech-debt strategy (quantify & prioritize), large migrations (Python 2→3, Django upgrades, monolith → services, sync → async, Flask → FastAPI), standards (typing, linting, testing), platform thinking, managing technical risk
- [ ] **Execution** — breaking down ambiguity, milestones, estimation & uncertainty, scope negotiation, dependency management, DORA metrics, quality ownership, operational readiness
- [ ] **People** — mentoring (juniors → seniors), delegation, feedback (SBI), handling underperformance, conflict resolution, hiring & interview design, onboarding, psychological safety, knowledge sharing
- [ ] **Stakeholders & business** — partnering with product/data/ML teams, saying no with data, executive communication, cost ownership, customer impact
- [ ] **Track decision** — Staff/Principal IC vs Engineering Manager — tailor stories accordingly

---

## 43. Behavioral Interviews & Story Bank (P0)

### 43.1 Format
- [ ] STAR / STAR-L; 2–3 minutes; "I" not "we"; quantify results; show judgment & trade-offs; real failures with genuine learnings; be ready for 5 levels of follow-up

### 43.2 Story Bank (prepare 15–20 stories covering these themes)
- [ ] Most challenging technical problem · biggest project led end to end · key design decision & trade-offs · major production incident · failure/mistake · conflict with peer/manager · disagree & commit · influencing without authority · mentoring success · handling underperformer · tight deadline · ambiguity · pushing back on product · convincing stakeholders on tech debt · improving dev productivity/process · customer obsession · innovation · data-driven decision · receiving critical feedback · delivering bad news · migration story · performance optimization with numbers · security/compliance issue · calculated risk · simplifying over-engineering · learning fast · team morale · decision with incomplete data · hiring/building a team · cross-team project with ML/data teams

### 43.3 Common Questions
- [ ] **Tell me about yourself** (90–120 s: current scope → 2–3 highlights with impact → why looking → what's next)
- [ ] **Why the career break?** — intentional 2–3 months of focused upskilling; say it confidently, with what you studied and built
- [ ] Why leaving / why this company / strengths & weaknesses / greatest achievement / where in 5 years / IC vs manager / how you stay current / why hire you
- [ ] **Company frameworks** — Amazon Leadership Principles (2 stories each), Google Googleyness, Meta signals, startup ownership; map stories to each target company's values
- [ ] **Questions to ask** — success in 6/12 months, biggest technical challenges, how decisions & tech debt are handled, on-call culture, growth path to Staff/Principal

---

## 44. Project Deep-Dive, Resume & Negotiation (P0)

### 44.1 Project Deep-Dive (2–3 flagship systems)
- [ ] Business problem & impact · scale numbers (RPS, data volume, users, latency SLOs) · architecture diagram in 5 minutes · your role vs team · key decisions & alternatives (why Django vs FastAPI, Celery vs Kafka, Postgres vs Mongo) · hardest challenges · failure modes & handling · consistency/idempotency/concurrency approach · testing/deploy/monitoring · incidents · measured impact · what you'd change at 10× scale

### 44.2 Resume & Presence
- [ ] 1–2 pages, XYZ-format bullets with numbers, leadership & scale highlighted, skills aligned with target JDs (Python 3.12+, FastAPI/Django, asyncio, Postgres, Redis, Kafka/Celery, AWS, Docker/K8s, system design, LLM integration)
- [ ] LinkedIn optimized; optional GitHub project (e.g., FastAPI + SQLAlchemy async + Celery/Kafka + outbox + Redis rate limiter + OpenTelemetry + Testcontainers + Docker Compose)

### 44.3 Search & Negotiation
- [ ] Tiered target list; referrals; practice companies first; **start applying by week 4–6**; track pipeline; debrief after each interview
- [ ] Research levels & comp (levels.fyi, Glassdoor, AmbitionBox); understand base/bonus/equity/joining bonus/notice buyout; don't give the first number; negotiate level too; get it in writing; evaluate team, manager, growth

---

## 45. Interview Formats

| Company type | Typical loop for a 10 YOE Python backend engineer | Prep emphasis |
|--------------|---------------------------------------------------|---------------|
| **Big Tech** | 1–2 DSA · 1–2 HLD · behavioral/leadership · hiring manager | DSA patterns, HLD at scale, leadership stories |
| **Product unicorns / scale-ups** | DSA · machine coding · HLD · LLD · Python deep dive · HM | Machine coding in Python, LLD, async, Django/FastAPI internals |
| **Fintech / enterprises** | Python & framework deep dive · DB & transactions · coding · system design | Concurrency, ORM, transactions, security |
| **AI/data-heavy startups** | Practical coding/take-home (FastAPI service), system design, LLM integration | asyncio, FastAPI, data pipelines, LLM APIs |
| **Staff/Principal loops** | Architecture review of past work · ambiguous HLD · cross-team leadership | Strategy, influence, trade-offs |

---

# PART I — EXECUTION

## 46. Rapid-Fire Questions (Top 100)

**Python Language & Runtime**
1. [ ] Mutable default arguments — bug and fix
2. [ ] `is` vs `==`; small-int caching
3. [ ] Shallow vs deep copy
4. [ ] How is `dict` implemented? Why must keys be hashable?
5. [ ] List vs tuple vs set — complexity and use cases
6. [ ] Generators vs iterators vs iterables; `yield from`
7. [ ] Write a decorator with arguments that preserves metadata
8. [ ] Context managers — write one with a class and with `contextmanager`
9. [ ] Closures and late binding in loops
10. [ ] LEGB scope; `global` vs `nonlocal`
11. [ ] `*args`, `**kwargs`, keyword-only and positional-only params
12. [ ] MRO and `super()` with multiple inheritance
13. [ ] Descriptors — how `property` works
14. [ ] Metaclasses vs `__init_subclass__` vs class decorators
15. [ ] `__new__` vs `__init__`; `__getattr__` vs `__getattribute__`
16. [ ] `__slots__` — benefits and drawbacks
17. [ ] dataclass vs Pydantic vs attrs vs NamedTuple vs TypedDict
18. [ ] ABC vs Protocol
19. [ ] Exception chaining; exception groups & `except*`
20. [ ] Structural pattern matching use cases
21. [ ] What changed in Python 3.11, 3.12, 3.13, 3.14 that matters to you?
22. [ ] The GIL — what, why, and how to work around it
23. [ ] Reference counting vs cyclic GC; finding memory leaks
24. [ ] Free-threaded Python — implications
25. [ ] How do you profile a running production process?

**Concurrency**
26. [ ] Threads vs processes vs asyncio — decision criteria
27. [ ] Coroutine vs Task vs Future
28. [ ] `gather` vs `TaskGroup` vs `wait`
29. [ ] Blocking call inside async code — symptoms and fixes
30. [ ] Limit concurrency to 100 outbound requests in asyncio
31. [ ] Cancellation and timeouts in asyncio
32. [ ] `contextvars` vs `threading.local`
33. [ ] multiprocessing start methods and pickling issues
34. [ ] gevent monkey-patching — pros and pitfalls
35. [ ] Thread-safe rate limiter implementation

**Frameworks & Data Access**
36. [ ] WSGI vs ASGI
37. [ ] Gunicorn worker types and sizing
38. [ ] Django request lifecycle & middleware order
39. [ ] `select_related` vs `prefetch_related`; finding N+1
40. [ ] `F()` expressions and race conditions
41. [ ] `transaction.atomic` and `on_commit`
42. [ ] `select_for_update` with `skip_locked` use case
43. [ ] Zero-downtime Django/Alembic migrations
44. [ ] Django signals — when not to use them
45. [ ] DRF serializer performance problems and fixes
46. [ ] DRF permissions: `has_permission` vs `has_object_permission`
47. [ ] FastAPI `def` vs `async def` endpoints
48. [ ] FastAPI dependency injection & yield dependencies
49. [ ] Pydantic v2 validators and v1 → v2 migration
50. [ ] SQLAlchemy Session, unit of work, identity map
51. [ ] `joinedload` vs `selectinload` vs `raiseload`
52. [ ] Async SQLAlchemy pitfalls (lazy loading, `expire_on_commit`)
53. [ ] Connection pool sizing across workers & pods; PgBouncer caveats
54. [ ] Celery reliability: `acks_late`, idempotency, visibility timeout
55. [ ] Celery vs Kafka vs RQ vs Temporal
56. [ ] pytest fixtures & scopes; `patch` where it's used
57. [ ] Testing async code and FastAPI apps
58. [ ] Poetry vs uv vs pip-tools; lockfiles
59. [ ] Structured logging with request IDs in asyncio
60. [ ] Prometheus metrics with multi-process Gunicorn

**Databases & Caching**
61. [ ] B+tree indexes and composite index ordering
62. [ ] Isolation levels & anomalies
63. [ ] MVCC in Postgres; VACUUM
64. [ ] Optimistic vs pessimistic locking
65. [ ] Replication lag & read-your-writes
66. [ ] Sharding strategy & shard key
67. [ ] SQL vs NoSQL decision
68. [ ] Cache-aside & consistency
69. [ ] Cache stampede prevention
70. [ ] Redis data structures & distributed locks

**Distributed Systems, APIs & Resilience**
71. [ ] CAP & PACELC
72. [ ] Consistent hashing
73. [ ] Raft basics
74. [ ] Saga vs 2PC
75. [ ] Transactional outbox
76. [ ] Exactly-once myth; idempotent consumers
77. [ ] Kafka ordering & consumer groups
78. [ ] Idempotent POST API design
79. [ ] Rate limiting algorithms; implement token bucket
80. [ ] Circuit breakers, retries with jitter, timeouts
81. [ ] REST vs gRPC vs GraphQL
82. [ ] API versioning & backward compatibility
83. [ ] Microservice boundaries; monolith migration
84. [ ] Webhook delivery & verification
85. [ ] Unique ID generation

**System Design**
86. [ ] URL shortener
87. [ ] Notification system
88. [ ] Chat system
89. [ ] Payment system
90. [ ] Distributed job scheduler / Celery at scale

**Infra, Ops & Leadership**
91. [ ] What happens when you type a URL?
92. [ ] Dockerizing a Python app correctly (slim, multi-stage, non-root, signals)
93. [ ] Kubernetes probes and graceful shutdown for Gunicorn/Celery
94. [ ] SLOs and error budgets
95. [ ] Python-specific security risks (pickle, yaml, eval, shell=True)
96. [ ] Major incident you handled
97. [ ] How you introduced typing/linting/testing standards to a team
98. [ ] Balancing tech debt vs features
99. [ ] Mentoring and raising the bar
100. [ ] A decision that turned out wrong

---

## 47. 12-Week Preparation Plan

### Daily Template (≈ 8–9 focused hours, 6 days/week)
| Block | Time | Activity |
|-------|------|----------|
| Morning | 2.5–3 h | **DSA in Python** — 3–4 problems by pattern, timed; mistake log |
| Midday | 2 h | **System design** — one problem end-to-end or a concept deep dive |
| Afternoon | 2 h | **Python/backend core** — topic of the week; write small runnable demos |
| Evening | 1 h | **LLD/machine coding** (alternate days) or **behavioral** stories |
| End of day | 15 min | Update checklist; spaced repetition (Anki) |

### Week-by-Week
| Week | DSA | System Design / LLD | Python & Backend Core | Behavioral / Career |
|------|-----|---------------------|-----------------------|---------------------|
| **1** | Arrays, hashing, two pointers, sliding window | Framework, estimation, building blocks | Core Python data model, functions, decorators, generators (§1) | Resume & LinkedIn; intro pitch |
| **2** | Stack, binary search, linked lists | URL shortener, rate limiter | OOP, descriptors, metaclasses, versions, typing (§1.5, §2, §5) | Story candidate list |
| **3** | Trees, BST | KV store, unique IDs, notification system | CPython internals, GIL, memory, profiling (§3) | 5 STAR stories |
| **4** | Heaps, intervals, greedy | News feed, chat; LLD parking lot, elevator | Concurrency: threading, multiprocessing, **asyncio** (§4) | 5 more stories; target list; referrals |
| **5** | Graphs I | Message queue, job scheduler; LLD BookMyShow, Splitwise | Django + ORM + migrations (§10) | **Start applying** (practice tier) |
| **6** | Graphs II, tries | Uber, proximity, typeahead; machine coding mock #1 | DRF, FastAPI, Pydantic (§11–12) | Project deep-dive #1 |
| **7** | Backtracking | Ticketing, e-commerce, payments | SQLAlchemy, Alembic, drivers, pooling (§14), SQL & DB internals (§21) | Project deep-dive #2; first mocks |
| **8** | DP I | YouTube, Dropbox, collaborative editor | Celery & messaging clients (§15), Redis & caching (§23) | Apply to strong tier; 2 mocks/week |
| **9** | DP II | Metrics/logging, ad clicks, top-K | Kafka, distributed systems theory (§24–25) | Behavioral mocks |
| **10** | Mixed + company-tagged | Own-system deep dives; machine coding mock #2–3 | Microservices, resilience, rate limiting, API design (§26–29); testing & tooling (§17–18) | Apply to dream tier |
| **11** | Timed mixed sets | Mock HLDs & LLDs | Docker/K8s, cloud, observability, security, performance (§19, §33–39) | Negotiation prep |
| **12** | Revise mistake log | Revise all designs | Rapid-fire 100 (§46) | Final mocks; rest |

### Throughout
- [ ] 10+ mock interviews (DSA ×4, HLD ×4, LLD/behavioral ×2)
- [ ] Mistake log reviewed weekly; one-page summaries per topic & per design
- [ ] Optional portfolio project (weeks 6–10) for fresh talking points

---

## 48. Resources

### Books
- [ ] **Fluent Python (2nd ed.)** — Luciano Ramalho (*the* Python deep-dive book)
- [ ] **Effective Python (3rd ed.)** — Brett Slatkin
- [ ] **Python Cookbook** — Beazley & Jones; **Python Concurrency with asyncio** — Matthew Fowler
- [ ] **Architecture Patterns with Python (Cosmic Python)** — Percival & Gregory
- [ ] **High Performance Python (3rd ed.)** — Gorelick & Ozsvald
- [ ] **Robust Python** — Patrick Viafore (typing & maintainability)
- [ ] **Two Scoops of Django**; **Django for APIs**; FastAPI official docs (excellent)
- [ ] **Designing Data-Intensive Applications** — Martin Kleppmann
- [ ] **System Design Interview Vol. 1 & 2** — Alex Xu
- [ ] **Understanding Distributed Systems** — Roberto Vitillo; **Release It!** — Michael Nygard
- [ ] **Microservices Patterns** — Chris Richardson; **Building Microservices** — Sam Newman
- [ ] **Database Internals** — Alex Petrov; **SQL Performance Explained** — Markus Winand (use-the-index-luke.com)
- [ ] **Site Reliability Engineering** — Google
- [ ] **The Staff Engineer's Path** — Tanya Reilly; **Staff Engineer** — Will Larson
- [ ] **Elements of Programming Interviews in Python**; **Cracking the Coding Interview**

### Online
- [ ] Python docs (Language Reference, Data Model, asyncio, typing), PEPs, "What's New" pages for 3.11–3.14
- [ ] Real Python, Talk Python / Python Bytes podcasts, PyCon talks (Raymond Hettinger, David Beazley, Łukasz Langa)
- [ ] Django, DRF, FastAPI, SQLAlchemy, Pydantic, Celery docs; HackSoft Django Styleguide
- [ ] LeetCode/NeetCode; ByteByteGo; Hello Interview; microservices.io; Martin Fowler's blog
- [ ] Engineering blogs — Instagram (Django at scale), Dropbox (Python at scale, mypy), Reddit, Uber, Netflix, Stripe, Discord, Doordash
- [ ] Mock platforms — Pramp, interviewing.io, peers

---

## 49. Final Readiness Checklist

### Interview Readiness
- [ ] 250+ DSA problems in Python; pattern recognition in 2–3 minutes; 2 Mediums in 45 minutes
- [ ] Can explain GIL, memory management, asyncio internals, descriptors/metaclasses, and typing confidently
- [ ] Can whiteboard Django/FastAPI request lifecycles, ORM internals, and Celery reliability settings
- [ ] 25+ system designs practiced aloud with one-page notes
- [ ] 8+ machine coding problems built in Python under 2 hours
- [ ] 2–3 own-system deep dives rehearsed with numbers
- [ ] 15–20 STAR stories; confident intro and career-break narrative
- [ ] Rapid-fire 100 answered aloud; 10+ mocks completed

### Production-Ready Python Service Checklist (great interview answer too)
- [ ] **Code** — typed (mypy/pyright in CI), linted (Ruff), tested (pytest, integration with Testcontainers), dependencies locked & scanned
- [ ] **API** — validated input (Pydantic/serializers), consistent errors, idempotent writes, pagination, OpenAPI docs, auth & object-level authorization
- [ ] **Runtime** — correct worker model (sync vs async), no blocking in the event loop, timeouts on every outbound call, connection pools sized correctly, graceful shutdown
- [ ] **Data** — migrations backward-compatible, indexes reviewed, no N+1, transactions scoped tightly, backups/PITR tested
- [ ] **Async work** — durable queue, idempotent tasks, retries with backoff, DLQ, monitoring of backlog
- [ ] **Resilience** — retries with jitter, circuit breakers, rate limiting, graceful degradation
- [ ] **Observability** — structured logs with trace IDs, metrics (RED + business), OpenTelemetry traces, Sentry, dashboards, SLOs & actionable alerts
- [ ] **Security** — secrets in a manager, no pickle/yaml.load/eval on untrusted input, Bandit/pip-audit clean, least privilege, TLS
- [ ] **Deployability** — slim non-root image, health probes, CI/CD with canary & rollback, config via env
- [ ] **Scalability & cost** — load tested, autoscaling (HPA/KEDA), right-sized resources

---

> **Final advice:** At 10 YOE, interviewers probe *why* Python behaves the way it does (GIL, memory, async scheduling, ORM sessions) and whether you've operated Python at scale (workers, pools, queues, leaks, migrations). For every topic, be ready to explain **what**, **how it works internally**, **when to use / not use**, **trade-offs**, and **a real production experience**.
