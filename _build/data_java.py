# -*- coding: utf-8 -*-
"""Java SE knowledge area — topics extracted from the hand-maintained java.html.
Used only to drive the tutorial pipeline; java.html itself stays hand-maintained."""

JAVA = {
    "file": "java.html",
    "title": "Java SE",
    "logo": "J",
    "cat": "Language Foundation",
    "subtitle": "Every Java micro-topic by release — the language Spring runs on.",
    "sections": [
{
"name": "0. Foundations & Environment",
"tag": "foundations",
"groups": [
{
"g": "What Java Is",
"items": [
"History & timeline of Java (Oak → Java, Sun → Oracle)",
"Write-once-run-anywhere (WORA) philosophy",
"Platform independence & how it is achieved",
"Java SE (Standard Edition)",
"Jakarta EE / Java EE (Enterprise Edition)",
"Java ME (Micro Edition)",
"JavaFX & client-side Java",
"Java language vs Java platform vs Java API",
"OpenJDK (reference implementation)",
"Oracle JDK",
"Eclipse Temurin (Adoptium)",
"Amazon Corretto",
"Azul Zulu",
"GraalVM",
"Release cadence (6-month feature releases)",
"Long-Term Support (LTS) releases",
"Preview features & enabling them (--enable-preview)",
"Incubator modules",
"Java SE specification (JSR) & JCP process"
]
},
{
"g": "JVM / JRE / JDK",
"items": [
"JVM (Java Virtual Machine) — what it is",
"JRE (Java Runtime Environment) — what it includes",
"JDK (Java Development Kit) — what it includes",
"Relationship JDK ⊃ JRE ⊃ JVM",
"Bytecode & the .class file format",
"Just-In-Time (JIT) compilation overview",
"Ahead-Of-Time (AOT) compilation overview"
]
},
{
"g": "Toolchain (each tool)",
"items": [
"javac — the compiler",
"java — the launcher",
"Single-file source-code launch (java Hello.java)",
"jar — archive tool",
"MANIFEST.MF & executable JARs",
"javadoc — documentation generator",
"jshell — the REPL",
"javap — class file disassembler",
"jdeps — dependency analyzer",
"jlink — custom runtime image linker",
"jpackage — native installer packager",
"jcmd — diagnostic command tool",
"jstack — thread dump tool",
"jmap — heap map / dump tool",
"jstat — JVM statistics",
"jconsole / VisualVM — monitoring",
"keytool — key & certificate management"
]
},
{
"g": "Program Structure & Setup",
"items": [
"Installing the JDK",
"Setting JAVA_HOME",
"Setting PATH for java/javac",
"Anatomy of a class",
"The main() method signature",
"Command-line arguments (String[] args)",
"Compilation lifecycle (source → bytecode → execution)",
"Packages & the package statement",
"import statements",
"Static imports (import static)",
"Wildcard imports (import java.util.*)",
"Source file naming rules (public class = file name)",
"Classpath (-cp / CLASSPATH)",
"Module path (--module-path)",
"Line comments (//)",
"Block comments (/* */)",
"Javadoc comments (/** */)"
]
}
]
},
{
"name": "1. Core Language (Java 1.0–1.4)",
"tag": "1.0-1.4",
"groups": [
{
"g": "Lexical Structure",
"items": [
"Identifiers & naming rules",
"Naming conventions (camelCase, PascalCase, UPPER_SNAKE)",
"Reserved keywords (full list)",
"Reserved literals: true, false, null",
"Unicode source & \\u escapes",
"Whitespace & line terminators",
"Separators ( ) { } [ ] ; , . )"
]
},
{
"g": "Primitive Types (each)",
"items": [
"boolean (true/false)",
"byte (8-bit, -128..127)",
"short (16-bit, -32768..32767)",
"int (32-bit signed)",
"long (64-bit signed)",
"char (16-bit unsigned UTF-16 code unit)",
"float (32-bit IEEE-754)",
"double (64-bit IEEE-754)",
"Default values of each primitive",
"Sizes & ranges of each primitive"
]
},
{
"g": "Literals",
"items": [
"Decimal integer literals",
"Octal integer literals (0…)",
"Hexadecimal integer literals (0x…)",
"long literals (suffix L)",
"float literals (suffix f) & double literals (suffix d)",
"Scientific notation (1.5e3)",
"char literals & escape sequences (\\n \\t \\\\ \\' \\\" \\uXXXX)",
"boolean literals",
"String literals",
"null literal"
]
},
{
"g": "Variables",
"items": [
"Variable declaration & initialization",
"Local variables",
"Instance variables (fields)",
"Static (class) variables",
"Variable scope & lifetime",
"final variables (constants)",
"Definite assignment rules",
"Shadowing of variables"
]
},
{
"g": "Type Conversion",
"items": [
"Implicit widening conversions",
"Explicit narrowing conversions (casting)",
"Numeric promotion in expressions",
"char ↔ int conversions",
"Integer overflow / underflow behavior",
"Floating-point special values (NaN, Infinity, -0.0)",
"Loss of precision in conversions"
]
},
{
"g": "Operators (each)",
"items": [
"Addition + (and String concatenation)",
"Subtraction -",
"Multiplication *",
"Division / (integer vs float)",
"Modulo %",
"Unary plus/minus (+ -)",
"Pre/post increment ++ ",
"Pre/post decrement --",
"Simple assignment =",
"Compound assignment (+= -= *= /= %= &= |= ^= <<= >>= >>>=)",
"Equality == and inequality !=",
"Relational < > <= >=",
"Logical AND && (short-circuit)",
"Logical OR || (short-circuit)",
"Logical NOT !",
"Bitwise AND &",
"Bitwise OR |",
"Bitwise XOR ^",
"Bitwise complement ~",
"Left shift <<",
"Signed right shift >>",
"Unsigned right shift >>>",
"Ternary conditional ?:",
"instanceof operator",
"Operator precedence & associativity"
]
},
{
"g": "Control Flow (each)",
"items": [
"if statement",
"if-else statement",
"else-if chains",
"switch statement (int/char/byte/short)",
"switch fall-through & break",
"default case",
"while loop",
"do-while loop",
"for loop (init; condition; update)",
"Infinite loops & loop termination",
"break statement",
"continue statement",
"Labeled break & continue",
"return statement",
"Empty statement & block statement"
]
},
{
"g": "Strings (micro)",
"items": [
"String immutability",
"String literal pool & interning",
"String concatenation with +",
"new String() vs literal",
"length()",
"charAt(int)",
"substring(int) / substring(int,int)",
"indexOf / lastIndexOf",
"equals() & equalsIgnoreCase()",
"compareTo() & compareToIgnoreCase()",
"toUpperCase() / toLowerCase()",
"trim()",
"replace()",
"split(String regex)",
"startsWith() / endsWith()",
"contains() (1.5)",
"concat()",
"toCharArray() & getChars()",
"valueOf() static overloads",
"intern()",
"String.format() (1.5)",
"StringBuffer (synchronized, mutable)",
"StringBuffer append/insert/delete/reverse"
]
},
{
"g": "Arrays (micro)",
"items": [
"Array declaration syntax (int[] vs int x[])",
"Array creation with new",
"Array initializer { }",
"Accessing & modifying elements",
"array.length field",
"ArrayIndexOutOfBoundsException",
"Iterating arrays with for",
"Multi-dimensional arrays",
"Jagged (ragged) arrays",
"Arrays of objects (default null)",
"java.util.Arrays.sort()",
"java.util.Arrays.binarySearch()",
"java.util.Arrays.fill()",
"java.util.Arrays.equals()",
"java.util.Arrays.copyOf() / copyOfRange()",
"java.util.Arrays.toString() / deepToString()",
"System.arraycopy()",
"Covariance of arrays & ArrayStoreException"
]
},
{
"g": "Classes & Objects",
"items": [
"Defining a class",
"Creating objects with new",
"Fields (instance variables)",
"Methods & method signatures",
"Parameters & return types",
"The 'this' reference",
"Constructors",
"Default (no-arg) constructor",
"Constructor overloading",
"Constructor chaining with this()",
"Method overloading & resolution",
"Pass-by-value semantics (primitives & references)",
"Object lifecycle & creation order",
"Garbage collection basics",
"finalize() (deprecated later)",
"Object identity vs equality"
]
},
{
"g": "Static & Initialization",
"items": [
"static fields",
"static methods",
"Static initializer blocks",
"Instance initializer blocks",
"Field initialization order",
"Constants (static final)",
"Utility classes pattern"
]
},
{
"g": "Access & Modifiers",
"items": [
"public modifier",
"protected modifier",
"default (package-private) access",
"private modifier",
"final modifier (fields/methods/classes)",
"abstract modifier",
"static modifier",
"Encapsulation principle",
"Getters & setters"
]
},
{
"g": "Inheritance & Polymorphism",
"items": [
"extends keyword & single inheritance",
"Inheriting fields & methods",
"Method overriding rules",
"@Override semantics",
"super keyword (fields)",
"super(...) constructor call",
"super.method() invocation",
"Upcasting (subtype → supertype)",
"Downcasting & ClassCastException",
"Dynamic method dispatch (virtual methods)",
"Static vs dynamic binding",
"Covariant return types (1.5)",
"Final methods (prevent override)",
"Final classes (prevent extension)",
"Object class & inheritance root"
]
},
{
"g": "Object class methods",
"items": [
"toString()",
"equals(Object)",
"hashCode()",
"equals/hashCode contract",
"getClass()",
"clone() & Cloneable",
"Shallow vs deep clone",
"wait() / notify() / notifyAll()",
"finalize()"
]
},
{
"g": "Abstract & Interfaces",
"items": [
"Abstract classes",
"Abstract methods",
"When to use abstract vs interface",
"Interface declaration",
"implements keyword",
"Implementing multiple interfaces",
"Interface constants (implicitly public static final)",
"Interface method signatures (implicitly public abstract)",
"Interface inheritance (extends)",
"Marker interfaces (e.g. Serializable, Cloneable)"
]
},
{
"g": "Nested & Inner Classes",
"items": [
"Static nested classes",
"Inner (non-static) classes",
"Accessing outer instance (Outer.this)",
"Local classes (inside methods)",
"Anonymous classes",
"Capturing local variables (final/effectively-final)",
"Nested class compilation ($ class files)"
]
},
{
"g": "Exceptions (micro)",
"items": [
"Throwable hierarchy",
"Error vs Exception",
"RuntimeException (unchecked)",
"Checked exceptions",
"try block",
"catch block",
"finally block",
"try-finally without catch",
"Multiple catch blocks & ordering",
"throw statement",
"throws clause",
"Custom exception classes",
"Exception chaining (initCause / cause constructor)",
"getMessage() / printStackTrace() / getStackTrace()",
"Common exceptions (NPE, AIOOBE, CCE, NumberFormat, Arithmetic)",
"Resource cleanup before try-with-resources",
"assert statement & -ea flag (1.4)"
]
},
{
"g": "Core Library APIs",
"items": [
"Wrapper classes (Integer, Long, Double, Boolean, Character, etc.)",
"Boxing/unboxing manually (pre-1.5)",
"parseInt / parseDouble / valueOf",
"Integer.MAX_VALUE / MIN_VALUE constants",
"Number abstract class",
"Math class (abs, max, min, pow, sqrt, round, floor, ceil, random)",
"System.out / System.err / System.in",
"System.getProperty / setProperty",
"System.currentTimeMillis()",
"System.exit() / System.gc()",
"Runtime class",
"java.util.Date (legacy)",
"java.util.Calendar (legacy)",
"java.text.SimpleDateFormat (legacy)",
"java.util.Random",
"java.util.StringTokenizer",
"java.util.Properties",
"java.util.BitSet"
]
},
{
"g": "Legacy Collections",
"items": [
"Vector",
"Stack",
"Hashtable",
"Enumeration interface",
"Dictionary (abstract)"
]
},
{
"g": "I/O (java.io)",
"items": [
"InputStream / OutputStream (byte streams)",
"Reader / Writer (character streams)",
"FileInputStream / FileOutputStream",
"FileReader / FileWriter",
"BufferedReader / BufferedWriter",
"BufferedInputStream / BufferedOutputStream",
"DataInputStream / DataOutputStream",
"PrintStream / PrintWriter",
"InputStreamReader / OutputStreamWriter (bridge)",
"File class (paths, exists, mkdirs, listFiles)",
"RandomAccessFile",
"Serialization (Serializable)",
"transient keyword",
"ObjectOutputStream / ObjectInputStream",
"serialVersionUID",
"Externalizable interface"
]
},
{
"g": "Threads (legacy)",
"items": [
"Thread class",
"Runnable interface",
"Starting threads (start vs run)",
"Thread.sleep()",
"Thread.join()",
"Thread priorities",
"Daemon threads",
"synchronized keyword (methods)",
"synchronized blocks",
"wait / notify / notifyAll coordination",
"Thread states & lifecycle",
"volatile keyword",
"Thread interruption (interrupt/isInterrupted)",
"Race conditions & deadlocks (intro)"
]
},
{
"g": "Networking (java.net)",
"items": [
"InetAddress",
"Socket (TCP client)",
"ServerSocket (TCP server)",
"DatagramSocket / DatagramPacket (UDP)",
"URL & URLConnection",
"HttpURLConnection"
]
},
{
"g": "Reflection (java.lang.reflect)",
"items": [
"Class object & getClass() / .class",
"Class.forName()",
"Field reflection",
"Method reflection & invoke()",
"Constructor reflection & newInstance()",
"Modifier inspection",
"setAccessible() & access control"
]
},
{
"g": "Added in 1.4",
"items": [
"Regular expressions (java.util.regex: Pattern, Matcher)",
"java.nio buffers (ByteBuffer, CharBuffer)",
"java.nio channels (FileChannel, SocketChannel)",
"Selectors & non-blocking I/O",
"java.util.logging (Logger, Level, Handler)",
"assert keyword & assertions",
"Preferences API",
"Chained exceptions (getCause)",
"Exception chaining constructors"
]
}
]
},
{
"name": "2. Java 5 (J2SE 5.0 'Tiger')",
"tag": "5",
"groups": [
{
"g": "Generics",
"items": [
"Generic class declaration <T>",
"Generic interface declaration",
"Generic methods <T> return",
"Type parameter naming conventions (T, E, K, V, N, ?)",
"Bounded type parameters (T extends Number)",
"Multiple bounds (T extends A & B)",
"Wildcard ?",
"Upper-bounded wildcard (? extends T)",
"Lower-bounded wildcard (? super T)",
"PECS (Producer Extends, Consumer Super)",
"Type erasure",
"Raw types & warnings",
"Cannot create generic arrays",
"Cannot use primitives as type args",
"Bridge methods (compiler-generated)"
]
},
{
"g": "Enums",
"items": [
"Basic enum declaration",
"Enum constants",
"values() & valueOf()",
"ordinal() & name()",
"Enums with fields & constructors",
"Enums with methods",
"Constant-specific method bodies",
"Enums implementing interfaces",
"EnumSet",
"EnumMap",
"Enums in switch statements"
]
},
{
"g": "Annotations",
"items": [
"Annotation syntax @Name",
"@Override",
"@Deprecated",
"@SuppressWarnings",
"Declaring custom annotations",
"Annotation elements & default values",
"Meta-annotation @Retention (SOURCE/CLASS/RUNTIME)",
"Meta-annotation @Target",
"Meta-annotation @Documented",
"Meta-annotation @Inherited",
"Marker & single-value annotations",
"Reading annotations via reflection"
]
},
{
"g": "Other Language Features",
"items": [
"Autoboxing (primitive → wrapper)",
"Auto-unboxing (wrapper → primitive)",
"Autoboxing pitfalls (NPE, == identity, caching -128..127)",
"Enhanced for-each loop",
"Varargs (Type... args)",
"Varargs & ambiguity / array passing",
"Static imports",
"Covariant return types",
"Formatted output printf/format"
]
},
{
"g": "java.util.concurrent (new)",
"items": [
"Executor & ExecutorService",
"Executors factory (fixed/cached/single/scheduled)",
"Callable & Future",
"ThreadPoolExecutor",
"ScheduledExecutorService",
"BlockingQueue (ArrayBlockingQueue, LinkedBlockingQueue)",
"ConcurrentHashMap",
"CopyOnWriteArrayList / CopyOnWriteArraySet",
"ConcurrentLinkedQueue",
"ReentrantLock",
"ReentrantReadWriteLock",
"Condition objects",
"Semaphore",
"CountDownLatch",
"CyclicBarrier",
"Exchanger",
"Atomic types (AtomicInteger, AtomicLong, AtomicReference)",
"TimeUnit enum"
]
},
{
"g": "Other Library Additions",
"items": [
"Scanner class",
"StringBuilder (non-synchronized)",
"Queue interface",
"java.util.Formatter",
"Arrays.deepToString / deepEquals"
]
}
]
},
{
"name": "3. Java 6 (Java SE 6 'Mustang')",
"tag": "6",
"groups": [
{
"g": "APIs & Platform",
"items": [
"Scripting API javax.script (JSR 223)",
"Compiler API javax.tools (in-memory compilation)",
"Pluggable annotation processing (JSR 269, javax.annotation.processing)",
"JDBC 4.0 (auto driver loading)",
"JAXB bundled (XML binding)",
"JAX-WS bundled (web services)",
"StAX streaming XML",
"NavigableMap interface",
"NavigableSet interface",
"ConcurrentSkipListMap / ConcurrentSkipListSet",
"Deque interface & ArrayDeque",
"java.io.Console",
"Arrays.copyOf / copyOfRange (from 6)",
"ServiceLoader (java.util.ServiceLoader)"
]
}
]
},
{
"name": "4. Java 7 (Java SE 7 'Dolphin')",
"tag": "7",
"groups": [
{
"g": "Project Coin (language)",
"items": [
"Strings in switch",
"Binary literals (0b1010)",
"Underscores in numeric literals (1_000_000)",
"Diamond operator <> for generics",
"Try-with-resources",
"AutoCloseable / Closeable interfaces",
"Multi-catch (catch A | B e)",
"More precise rethrow",
"Suppressed exceptions (getSuppressed)"
]
},
{
"g": "NIO.2 (java.nio.file)",
"items": [
"Path interface & Paths factory",
"Files utility class",
"Files.copy / move / delete",
"Files.readAllLines / readAllBytes / write",
"Files.walkFileTree & FileVisitor",
"DirectoryStream",
"WatchService (file change events)",
"FileSystem & FileSystems",
"Symbolic links handling",
"File attributes (BasicFileAttributes, PosixFilePermissions)"
]
},
{
"g": "Concurrency & Platform",
"items": [
"Fork/Join framework (ForkJoinPool)",
"RecursiveTask / RecursiveAction",
"ThreadLocalRandom",
"Phaser",
"invokedynamic bytecode (JSR 292)",
"java.lang.invoke (MethodHandle, MethodType)",
"Objects utility class (requireNonNull, equals, hash, toString)",
"Improved exception messages"
]
}
]
},
{
"name": "5. Java 8 (LTS)",
"tag": "8",
"groups": [
{
"g": "Lambda Expressions",
"items": [
"Lambda syntax (params) -> body",
"Single-expression vs block-body lambdas",
"Parameter type inference",
"Capturing variables (effectively final)",
"Lambda vs anonymous class differences",
"this in lambdas (enclosing instance)",
"Target typing of lambdas"
]
},
{
"g": "Functional Interfaces",
"items": [
"@FunctionalInterface annotation",
"Function<T,R>",
"BiFunction<T,U,R>",
"Consumer<T> / BiConsumer",
"Supplier<T>",
"Predicate<T> / BiPredicate",
"UnaryOperator<T> / BinaryOperator<T>",
"Primitive specializations (IntFunction, ToIntFunction, IntPredicate, etc.)",
"Default methods on functional interfaces (andThen, compose, negate, and, or)"
]
},
{
"g": "Method & Constructor References",
"items": [
"Static method reference (Class::staticMethod)",
"Instance method of particular object (obj::method)",
"Instance method of arbitrary object (Class::instanceMethod)",
"Constructor reference (Class::new)",
"Array constructor reference (Type[]::new)"
]
},
{
"g": "Streams — creation",
"items": [
"Collection.stream() / parallelStream()",
"Arrays.stream()",
"Stream.of()",
"Stream.iterate()",
"Stream.generate()",
"Stream.empty()",
"IntStream.range / rangeClosed",
"Files.lines() / BufferedReader.lines()",
"Stream.concat()"
]
},
{
"g": "Streams — intermediate ops",
"items": [
"filter()",
"map()",
"mapToInt / mapToLong / mapToDouble / mapToObj",
"flatMap()",
"distinct()",
"sorted() / sorted(Comparator)",
"peek()",
"limit()",
"skip()",
"boxed()"
]
},
{
"g": "Streams — terminal ops",
"items": [
"forEach() / forEachOrdered()",
"toArray()",
"reduce() (3 forms)",
"collect()",
"min() / max()",
"count()",
"anyMatch / allMatch / noneMatch",
"findFirst() / findAny()",
"sum / average / summaryStatistics (primitive streams)"
]
},
{
"g": "Collectors",
"items": [
"toList() / toSet()",
"toCollection()",
"toMap()",
"joining()",
"groupingBy()",
"groupingBy with downstream",
"partitioningBy()",
"counting()",
"summingInt / averagingInt",
"mapping()",
"reducing()",
"collectingAndThen()",
"minBy / maxBy"
]
},
{
"g": "Streams — concepts",
"items": [
"Lazy evaluation",
"Short-circuiting operations",
"Stateless vs stateful operations",
"Ordered vs unordered streams",
"Parallel streams & spliterators",
"Stream cannot be reused",
"Side-effects & purity rules"
]
},
{
"g": "Interfaces",
"items": [
"Default methods",
"Static methods on interfaces",
"Diamond problem resolution",
"Functional interface inheritance"
]
},
{
"g": "Optional",
"items": [
"Optional.of / ofNullable / empty",
"isPresent() / get()",
"ifPresent()",
"orElse() / orElseGet() / orElseThrow()",
"map() / flatMap() / filter()",
"Optional anti-patterns"
]
},
{
"g": "Date/Time API (java.time)",
"items": [
"LocalDate",
"LocalTime",
"LocalDateTime",
"Instant",
"Duration",
"Period",
"ZoneId & ZoneOffset",
"ZonedDateTime",
"OffsetDateTime",
"DateTimeFormatter",
"Parsing & formatting",
"TemporalAdjusters",
"ChronoUnit & ChronoField",
"Conversion to/from legacy Date/Calendar"
]
},
{
"g": "Other Additions",
"items": [
"Repeating annotations (@Repeatable)",
"Type annotations (ElementType.TYPE_USE)",
"Parameter reflection (Method.getParameters, -parameters)",
"StringJoiner",
"String.join()",
"java.util.Base64",
"Arrays.parallelSort()",
"Comparator improvements (comparing, thenComparing, reversed)",
"Map default methods (getOrDefault, putIfAbsent, computeIfAbsent, computeIfPresent, compute, merge, forEach, replaceAll)",
"Iterable.forEach() / Collection.removeIf()",
"CompletableFuture",
"StampedLock",
"LongAdder / DoubleAdder / LongAccumulator",
"Nashorn JavaScript engine",
"PermGen removed → Metaspace"
]
}
]
},
{
"name": "6. Java 9",
"tag": "9",
"groups": [
{
"g": "Module System (JPMS / Jigsaw)",
"items": [
"Module concept & motivation",
"module-info.java",
"requires directive",
"requires transitive",
"requires static",
"exports directive",
"exports … to (qualified)",
"opens directive (reflection)",
"uses directive",
"provides … with directive",
"Module path vs classpath",
"Automatic modules",
"Unnamed module",
"Strong encapsulation",
"jlink custom runtime images",
"jdeps for module migration"
]
},
{
"g": "Language Changes",
"items": [
"Private methods in interfaces",
"Private static methods in interfaces",
"Try-with-resources on effectively-final vars",
"Diamond with anonymous classes",
"@SafeVarargs on private methods",
"Underscore '_' banned as identifier"
]
},
{
"g": "API Additions",
"items": [
"List.of / Set.of / Map.of / Map.ofEntries",
"Stream.takeWhile",
"Stream.dropWhile",
"Stream.ofNullable",
"Stream.iterate with predicate",
"Optional.ifPresentOrElse",
"Optional.or",
"Optional.stream",
"Reactive Streams Flow API (Publisher/Subscriber/Processor/Subscription)",
"Process API (ProcessHandle, ProcessHandle.Info)",
"StackWalker API",
"Multi-release JAR files",
"Compact Strings (byte[] backing)",
"Indified string concatenation",
"Collectors.flatMapping / filtering (9)",
"Enhanced @Deprecated (forRemoval, since)"
]
},
{
"g": "Tooling",
"items": [
"JShell REPL",
"JLink",
"Improved Javadoc (search, HTML5)",
"Unified JVM logging",
"G1 as default GC (from 9)"
]
}
]
},
{
"name": "7. Java 10",
"tag": "10",
"groups": [
{
"g": "Features",
"items": [
"Local-variable type inference: var",
"var rules & where it is allowed",
"var limitations (no fields, no method params, no null init)",
"List.copyOf / Set.copyOf / Map.copyOf",
"Collectors.toUnmodifiableList/Set/Map",
"Optional.orElseThrow() (no-arg)",
"Application Class-Data Sharing (AppCDS)",
"Parallel Full GC for G1",
"Time-based release versioning ($FEATURE.$INTERIM.$UPDATE)",
"Graal experimental JIT (on Linux)"
]
}
]
},
{
"name": "8. Java 11 (LTS)",
"tag": "11",
"groups": [
{
"g": "Language",
"items": [
"var in lambda parameters"
]
},
{
"g": "String / Files API",
"items": [
"String.isBlank()",
"String.lines()",
"String.strip() / stripLeading() / stripTrailing()",
"String.repeat(int)",
"Files.readString()",
"Files.writeString()",
"Path.of()",
"Collection.toArray(IntFunction)",
"Optional.isEmpty()",
"Predicate.not()"
]
},
{
"g": "Platform",
"items": [
"HTTP Client standardized (java.net.http.HttpClient)",
"HttpRequest / HttpResponse",
"BodyHandlers / BodyPublishers",
"Synchronous & asynchronous (sendAsync) requests",
"HTTP/2 support",
"WebSocket support",
"Launch single-file source programs",
"Epsilon GC (no-op)",
"ZGC (experimental)",
"Flight Recorder open-sourced",
"Mission Control",
"TLS 1.3",
"Removed Java EE & CORBA modules",
"Nashorn deprecated",
"Removed JavaFX from JDK (separate)"
]
}
]
},
{
"name": "9. Java 12",
"tag": "12",
"groups": [
{
"g": "Features",
"items": [
"Switch expressions (preview)",
"String.indent(int)",
"String.transform(Function)",
"Files.mismatch()",
"Collectors.teeing()",
"Compact Number Formatting (NumberFormat.getCompactNumberInstance)",
"Shenandoah GC (experimental)",
"G1 abortable mixed collections",
"G1 promptly return unused memory",
"JVM Constants API (java.lang.constant)",
"Microbenchmark suite (JMH) added to JDK"
]
}
]
},
{
"name": "10. Java 13",
"tag": "13",
"groups": [
{
"g": "Features",
"items": [
"Text blocks (preview)",
"Switch expressions yield (2nd preview)",
"Reimplemented legacy Socket API",
"Dynamic CDS archives",
"ZGC uncommit unused memory",
"FileSystems.newFileSystem additions"
]
}
]
},
{
"name": "11. Java 14",
"tag": "14",
"groups": [
{
"g": "Features",
"items": [
"Switch expressions — standardized",
"Switch arrow labels (case x ->)",
"yield in switch",
"Records (preview)",
"Pattern matching for instanceof (preview)",
"Helpful NullPointerExceptions",
"Text blocks (2nd preview)",
"Foreign-Memory Access API (incubator)",
"jpackage (incubator)",
"ZGC on macOS & Windows",
"CMS GC removed",
"ParallelScavenge + SerialOld deprecation",
"G1 NUMA-aware allocation"
]
}
]
},
{
"name": "12. Java 15",
"tag": "15",
"groups": [
{
"g": "Features",
"items": [
"Text blocks — standardized",
"Sealed classes (preview)",
"Records (2nd preview)",
"Pattern matching for instanceof (2nd preview)",
"Hidden classes",
"EdDSA signatures",
"ZGC production-ready",
"Shenandoah production-ready",
"Nashorn removed",
"Disable & deprecate biased locking"
]
}
]
},
{
"name": "13. Java 16",
"tag": "16",
"groups": [
{
"g": "Features",
"items": [
"Records — standardized",
"Pattern matching for instanceof — standardized",
"Sealed classes (2nd preview)",
"Stream.toList()",
"Stream.mapMulti (later) / Vector API (incubator)",
"Day Period support in DateTimeFormatter",
"Foreign Linker API (incubator)",
"Foreign-Memory Access API (3rd incubator)",
"Unix-domain socket channels",
"Strong encapsulation of JDK internals by default",
"Elastic Metaspace",
"ZGC concurrent thread-stack processing",
"Migrate JDK source to Git/GitHub",
"Enable C++14 in JDK source"
]
}
]
},
{
"name": "14. Java 17 (LTS)",
"tag": "17",
"groups": [
{
"g": "Language",
"items": [
"Sealed classes & interfaces — standardized",
"sealed / permits / non-sealed keywords",
"Pattern matching for switch (preview)",
"Restore always-strict floating point (strictfp default)"
]
},
{
"g": "Platform & API",
"items": [
"Enhanced pseudo-random generators (RandomGenerator API)",
"RandomGeneratorFactory",
"New macOS rendering pipeline (Metal)",
"macOS AArch64 (Apple Silicon) port",
"Foreign Function & Memory API (incubator)",
"Vector API (2nd incubator)",
"Context-specific deserialization filters",
"Deprecate Security Manager for removal",
"Remove RMI Activation",
"Remove experimental AOT/JIT (Graal) compiler",
"Strongly encapsulated internals (no illegal-access)",
"Remove Applet API (deprecated)"
]
}
]
},
{
"name": "15. Java 18",
"tag": "18",
"groups": [
{
"g": "Features",
"items": [
"UTF-8 as default charset",
"Simple Web Server (jwebserver)",
"Code snippets in Javadoc (@snippet)",
"Pattern matching for switch (2nd preview)",
"Foreign Function & Memory API (2nd incubator)",
"Vector API (3rd incubator)",
"Internet-Address Resolution SPI",
"Deprecate finalization for removal"
]
}
]
},
{
"name": "16. Java 19",
"tag": "19",
"groups": [
{
"g": "Project Loom & Amber",
"items": [
"Virtual threads (preview)",
"Structured concurrency (incubator)",
"Record patterns (preview)",
"Pattern matching for switch (3rd preview)",
"Foreign Function & Memory API (preview)",
"Vector API (4th incubator)",
"Linux/RISC-V port"
]
}
]
},
{
"name": "17. Java 20",
"tag": "20",
"groups": [
{
"g": "Features (continued previews)",
"items": [
"Scoped values (incubator)",
"Record patterns (2nd preview)",
"Pattern matching for switch (4th preview)",
"Virtual threads (2nd preview)",
"Structured concurrency (2nd incubator)",
"Foreign Function & Memory API (2nd preview)",
"Vector API (5th incubator)"
]
}
]
},
{
"name": "18. Java 21 (LTS)",
"tag": "21",
"groups": [
{
"g": "Standardized Features",
"items": [
"Virtual threads — standardized",
"Record patterns — standardized",
"Record deconstruction patterns",
"Pattern matching for switch — standardized",
"Guarded patterns (when clauses)",
"Null handling in switch (case null)",
"Exhaustiveness checking in switch",
"Sequenced collections (SequencedCollection)",
"SequencedSet / SequencedMap",
"getFirst/getLast/reversed methods",
"Generational ZGC"
]
},
{
"g": "Preview / Incubator",
"items": [
"String templates (preview)",
"Unnamed patterns & variables (preview)",
"Unnamed classes & instance main methods (preview)",
"Scoped values (preview)",
"Structured concurrency (preview)",
"Foreign Function & Memory API (3rd preview)",
"Vector API (6th incubator)",
"Key Encapsulation Mechanism API",
"Deprecate 32-bit x86 port"
]
}
]
},
{
"name": "19. Java 22",
"tag": "22",
"groups": [
{
"g": "Features",
"items": [
"Foreign Function & Memory API — standardized",
"Unnamed variables & patterns — standardized",
"Statements before super(...) (preview)",
"Stream gatherers (preview)",
"Structured concurrency (2nd preview)",
"Scoped values (2nd preview)",
"String templates (2nd preview)",
"Implicitly declared classes & instance main (2nd preview)",
"Class-File API (preview)",
"Region pinning for G1",
"Launch multi-file source-code programs",
"Vector API (7th incubator)"
]
}
]
},
{
"name": "20. Java 23",
"tag": "23",
"groups": [
{
"g": "Features",
"items": [
"Primitive types in patterns/instanceof/switch (preview)",
"Markdown documentation comments",
"Flexible constructor bodies (2nd preview)",
"Module import declarations (preview)",
"Implicitly declared classes & instance main (3rd preview)",
"Stream gatherers (2nd preview)",
"Structured concurrency (3rd preview)",
"Scoped values (3rd preview)",
"Class-File API (2nd preview)",
"Vector API (8th incubator)",
"ZGC generational by default",
"Deprecate memory-access methods in sun.misc.Unsafe"
]
}
]
},
{
"name": "21. Java 24",
"tag": "24",
"groups": [
{
"g": "Features",
"items": [
"Stream gatherers — standardized",
"Class-File API — standardized",
"Flexible constructor bodies — standardized",
"Scoped values (4th preview)",
"Structured concurrency (4th preview)",
"Module import declarations (2nd preview)",
"Simple source files & instance main methods (4th preview)",
"Primitive types in patterns (2nd preview)",
"Ahead-of-Time class loading & linking",
"Generational Shenandoah (experimental)",
"Compact object headers (experimental)",
"ML-KEM (quantum-resistant key encapsulation)",
"ML-DSA (quantum-resistant signatures)",
"Permanently disable Security Manager",
"Warn on sun.misc.Unsafe memory access",
"Late barrier expansion for G1",
"Remove 32-bit x86 port"
]
}
]
},
{
"name": "22. Collections Framework (deep)",
"tag": "collections",
"groups": [
{
"g": "Interfaces",
"items": [
"Iterable",
"Collection",
"List",
"Set",
"SortedSet / NavigableSet",
"Queue",
"Deque",
"Map",
"SortedMap / NavigableMap",
"Iterator",
"ListIterator",
"Spliterator"
]
},
{
"g": "List implementations",
"items": [
"ArrayList (internals, resizing)",
"LinkedList (doubly-linked)",
"Vector (legacy, synchronized)",
"CopyOnWriteArrayList",
"List operations Big-O comparison"
]
},
{
"g": "Set implementations",
"items": [
"HashSet",
"LinkedHashSet",
"TreeSet",
"EnumSet",
"CopyOnWriteArraySet",
"ConcurrentSkipListSet"
]
},
{
"g": "Map implementations",
"items": [
"HashMap internals (buckets, hashing, load factor, treeify)",
"LinkedHashMap (insertion & access order, LRU)",
"TreeMap (red-black tree)",
"Hashtable (legacy)",
"EnumMap",
"WeakHashMap",
"IdentityHashMap",
"ConcurrentHashMap internals",
"ConcurrentSkipListMap",
"Properties"
]
},
{
"g": "Queue / Deque implementations",
"items": [
"PriorityQueue (binary heap)",
"ArrayDeque",
"LinkedList as Queue/Deque",
"BlockingQueue family (Array/Linked/Priority/Delay/Synchronous)",
"ConcurrentLinkedQueue / Deque"
]
},
{
"g": "Ordering & Utilities",
"items": [
"Comparable & compareTo",
"Comparator & compare",
"Comparator.comparing / thenComparing / reversed / nullsFirst",
"natural ordering vs custom",
"Collections.sort / reverse / shuffle / binarySearch",
"Collections.unmodifiable* views",
"Collections.synchronized* wrappers",
"Collections.emptyList/Set/Map & singleton*",
"Collections.min / max / frequency / disjoint",
"Fail-fast iterators & ConcurrentModificationException",
"Fail-safe iterators",
"Choosing the right collection (trade-offs)"
]
}
]
},
{
"name": "23. Concurrency (deep)",
"tag": "concurrency",
"groups": [
{
"g": "Fundamentals",
"items": [
"Process vs thread",
"Thread lifecycle & states (NEW, RUNNABLE, BLOCKED, WAITING, TIMED_WAITING, TERMINATED)",
"Creating threads (Thread vs Runnable vs Callable)",
"Thread scheduling & priorities",
"Daemon vs user threads",
"Thread.sleep / yield / join",
"Interruption model"
]
},
{
"g": "Java Memory Model",
"items": [
"Happens-before relationship",
"volatile semantics",
"Atomicity vs visibility vs ordering",
"Data races",
"Safe publication",
"final field semantics",
"Double-checked locking"
]
},
{
"g": "Locking",
"items": [
"synchronized methods",
"synchronized blocks & monitor objects",
"Intrinsic locks & reentrancy",
"ReentrantLock & fairness",
"ReadWriteLock",
"StampedLock (optimistic reads)",
"Condition variables",
"Deadlock (causes & prevention)",
"Livelock & starvation",
"Lock ordering & avoidance"
]
},
{
"g": "Executors & Tasks",
"items": [
"Executor / ExecutorService / ScheduledExecutorService",
"ThreadPoolExecutor configuration (core/max/queue/rejection)",
"Thread pool sizing strategies",
"Future & Callable",
"CompletionService",
"CompletableFuture creation (supplyAsync/runAsync)",
"CompletableFuture chaining (thenApply/thenAccept/thenCompose)",
"CompletableFuture combining (thenCombine/allOf/anyOf)",
"CompletableFuture exception handling (exceptionally/handle/whenComplete)",
"ForkJoinPool & work-stealing",
"RecursiveTask / RecursiveAction",
"Common pool"
]
},
{
"g": "Synchronizers & Atomics",
"items": [
"CountDownLatch",
"CyclicBarrier",
"Semaphore",
"Phaser",
"Exchanger",
"CAS (compare-and-swap)",
"AtomicInteger / AtomicLong / AtomicReference",
"AtomicIntegerArray etc.",
"AtomicFieldUpdater",
"LongAdder / LongAccumulator",
"ABA problem & AtomicStampedReference"
]
},
{
"g": "Thread-local & Loom",
"items": [
"ThreadLocal",
"InheritableThreadLocal",
"ThreadLocal memory leaks",
"Virtual threads model (Loom)",
"Platform vs virtual threads",
"Carrier threads & pinning",
"Structured concurrency",
"Scoped values"
]
}
]
},
{
"name": "24. JVM Internals",
"tag": "jvm",
"groups": [
{
"g": "Class Loading",
"items": [
"Loading, linking (verify/prepare/resolve), initialization",
"ClassLoader hierarchy (bootstrap/platform/application)",
"Parent delegation model",
"Custom class loaders",
"Class initialization triggers & order",
"Class unloading"
]
},
{
"g": "Runtime Data Areas",
"items": [
"Heap",
"Method area / Metaspace",
"JVM stacks & stack frames",
"Program Counter (PC) register",
"Native method stacks",
"Runtime constant pool",
"String pool"
]
},
{
"g": "Execution Engine",
"items": [
"Bytecode interpretation",
"JIT compilation (C1 client, C2 server)",
"Tiered compilation",
"Method inlining",
"Escape analysis & scalar replacement",
"On-stack replacement (OSR)",
"Deoptimization"
]
},
{
"g": "Garbage Collection",
"items": [
"Generational hypothesis (young/old/eden/survivor)",
"Reachability & GC roots",
"Reference types (strong/soft/weak/phantom)",
"Mark-sweep / mark-compact / copying",
"Serial GC",
"Parallel GC",
"CMS (removed)",
"G1 GC",
"ZGC",
"Shenandoah",
"Epsilon GC",
"Stop-the-world pauses",
"GC tuning flags & ergonomics",
"Memory leaks in managed memory"
]
},
{
"g": "Diagnostics & Tuning",
"items": [
"JVM flags (-Xms/-Xmx/-Xss)",
"Heap dumps & analysis",
"Thread dumps",
"Java Flight Recorder (JFR)",
"Java Mission Control (JMC)",
"GC logging",
"Profiling (VisualVM, async-profiler, JMH)",
"OutOfMemoryError types"
]
}
]
},
{
"name": "25. Advanced Language & APIs",
"tag": "advanced",
"groups": [
{
"g": "Generics (advanced)",
"items": [
"Generic method type inference",
"Recursive type bounds (T extends Comparable<T>)",
"Wildcard capture",
"Super type tokens (TypeReference pattern)",
"Heap pollution",
"Reifiable vs non-reifiable types",
"Generics & arrays interplay"
]
},
{
"g": "Records (deep)",
"items": [
"Record components & canonical constructor",
"Compact canonical constructor",
"Auto-generated equals/hashCode/toString/accessors",
"Records implementing interfaces",
"Records & immutability",
"Local records",
"Record patterns / deconstruction"
]
},
{
"g": "Sealed types (deep)",
"items": [
"sealed / permits clauses",
"non-sealed subclasses",
"Sealed + records + pattern matching synergy",
"Exhaustiveness in switch"
]
},
{
"g": "Pattern matching (deep)",
"items": [
"instanceof pattern binding",
"switch type patterns",
"Guarded patterns (when)",
"Record deconstruction patterns",
"Nested patterns",
"Unnamed patterns (_)"
]
},
{
"g": "Functional / Reactive",
"items": [
"Pure functions & immutability",
"Function composition & currying",
"Higher-order functions",
"Reactive Streams spec (Flow API)",
"Backpressure"
]
},
{
"g": "NIO & Serialization (advanced)",
"items": [
"Memory-mapped files (MappedByteBuffer)",
"Direct vs heap ByteBuffers",
"Selectors & event loops",
"Charset encoding/decoding pitfalls",
"Serialization vulnerabilities & filters",
"Alternatives to Java serialization (JSON, protobuf)",
"Externalizable vs Serializable"
]
},
{
"g": "Reflection & Metaprogramming",
"items": [
"Reflection API deep dive",
"MethodHandles & VarHandles",
"Dynamic proxies (java.lang.reflect.Proxy)",
"Annotation processing (APT)",
"Instrumentation API & java agents",
"ServiceLoader & SPI"
]
}
]
},
{
"name": "26. Best Practices, Patterns & Tooling",
"tag": "practices",
"groups": [
{
"g": "Principles",
"items": [
"SOLID — Single Responsibility",
"SOLID — Open/Closed",
"SOLID — Liskov Substitution",
"SOLID — Interface Segregation",
"SOLID — Dependency Inversion",
"DRY / KISS / YAGNI",
"Composition over inheritance",
"Law of Demeter"
]
},
{
"g": "Design Patterns",
"items": [
"Singleton",
"Factory Method",
"Abstract Factory",
"Builder",
"Prototype",
"Adapter",
"Decorator",
"Facade",
"Proxy",
"Composite",
"Strategy",
"Observer",
"Template Method",
"Command",
"Iterator",
"State",
"Chain of Responsibility",
"Dependency Injection"
]
},
{
"g": "Effective Java idioms",
"items": [
"equals/hashCode contract & implementation",
"Immutability & defensive copies",
"Builder for many parameters",
"Static factory methods",
"Prefer composition",
"Minimize mutability & accessibility",
"Avoid finalizers/cleaners",
"Prefer enums & EnumSet",
"Favor generics & avoid raw types",
"Optional usage guidelines",
"Exception handling best practices"
]
},
{
"g": "Testing",
"items": [
"JUnit 5 lifecycle (@BeforeEach/@AfterEach/@BeforeAll/@AfterAll)",
"Assertions (assertEquals, assertThrows, assertAll)",
"Parameterized tests",
"Nested & dynamic tests",
"Mockito (mock/when/verify)",
"Test doubles (stub/mock/spy/fake)",
"AssertJ / Hamcrest matchers",
"Test coverage (JaCoCo)",
"TDD basics"
]
},
{
"g": "Build & Tooling",
"items": [
"Maven lifecycle & POM",
"Maven dependencies & scopes",
"Gradle build scripts & tasks",
"Semantic versioning",
"Dependency management & conflicts",
"Static analysis (SpotBugs, PMD, Checkstyle, SonarQube)",
"Code formatting (google-java-format, Spotless)",
"Debugging (IDE debugger, jdb, breakpoints)",
"Benchmarking with JMH"
]
},
{
"g": "Ecosystem (beyond core)",
"items": [
"JDBC & connection pooling",
"JPA / Hibernate ORM",
"Spring Core & DI container",
"Spring Boot",
"Jakarta EE overview",
"Logging (SLF4J + Logback / Log4j2)",
"JSON (Jackson, Gson)",
"REST APIs (JAX-RS, Spring MVC)",
"GraalVM native images",
"Microservices basics"
]
}
]
}
],
}

PROJECTS = [JAVA]
