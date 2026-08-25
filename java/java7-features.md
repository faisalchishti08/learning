# Java 7 Features (2011)

Java 7 (Project Coin) added practical syntax improvements and the NIO.2 file API.

---

## 1. Diamond Operator `<>`

Infer generic type from context — no need to repeat on the right side.

```java
// Before Java 7
Map<String, List<Integer>> map = new HashMap<String, List<Integer>>();

// Java 7+
Map<String, List<Integer>> map2 = new HashMap<>(); // compiler infers type

List<String> list = new ArrayList<>();
Map<String, Map<Integer, List<String>>> complex = new HashMap<>();
```

---

## 2. try-with-resources

Automatic resource management — `AutoCloseable` resources are closed automatically.

```java
// Before Java 7 — manual close in finally
BufferedReader br = null;
try {
    br = new BufferedReader(new FileReader("file.txt"));
    String line = br.readLine();
} finally {
    if (br != null) try { br.close(); } catch (IOException e) {}
}

// Java 7+ — auto-close
try (BufferedReader br = new BufferedReader(new FileReader("file.txt"))) {
    String line = br.readLine();
} // br.close() called automatically, even if exception

// Multiple resources — closed in reverse order
try (FileInputStream fis = new FileInputStream("in.txt");
     FileOutputStream fos = new FileOutputStream("out.txt")) {
    fos.write(fis.readAllBytes()); // Java 9+ readAllBytes
}
```

---

## 3. Multi-catch

Catch multiple exception types in one catch block.

```java
// Before Java 7
try {
    riskyOp();
} catch (IOException e) {
    handle(e);
} catch (SQLException e) {
    handle(e); // same code repeated
}

// Java 7+ multi-catch
try {
    riskyOp();
} catch (IOException | SQLException e) { // one block for both
    handle(e); // e is effectively final
}
```

---

## 4. String in switch

`switch` now works with `String`.

```java
String command = "start";

switch (command) {
    case "start":
        System.out.println("Starting...");
        break;
    case "stop":
        System.out.println("Stopping...");
        break;
    default:
        System.out.println("Unknown: " + command);
}
// Implemented as hashCode + equals comparison
```

---

## 5. Numeric Literals Improvements

Underscores in numeric literals and binary literals.

```java
// Underscores for readability
int million  = 1_000_000;
long credit  = 9_999_999_999L;
double pi    = 3.14_159_265;
int hex      = 0xFF_EC_D0_12;

// Binary literals with 0b prefix
int flags    = 0b1010_1100; // 172
int mask     = 0b0000_1111; // 15
System.out.println(flags & mask); // 12
```

---

## 6. NIO.2 — Path and Files API

`java.nio.file.Path` replaces `java.io.File`. See `24-nio.md` for full coverage.

```java
import java.nio.file.*;

// Old: new File("path")
// New: Path.of("path") — more expressive

Path path = Path.of("/home/user/docs/file.txt");
System.out.println(path.getFileName());   // file.txt
System.out.println(path.getParent());     // /home/user/docs

// Files utility
Files.createDirectories(Path.of("/tmp/new/dir"));
Files.copy(Path.of("src.txt"), Path.of("dst.txt"), StandardCopyOption.REPLACE_EXISTING);
Files.move(Path.of("old.txt"), Path.of("new.txt"));
Files.delete(Path.of("temp.txt"));

// Read/write (buffered, charset-aware)
String content = new String(Files.readAllBytes(Path.of("file.txt")));
Files.write(Path.of("out.txt"), "hello".getBytes());

// WatchService for file system events
WatchService ws = FileSystems.getDefault().newWatchService();
Path dir = Path.of("/tmp");
dir.register(ws, StandardWatchEventKinds.ENTRY_CREATE);
```

---

## 7. ForkJoinPool

Work-stealing thread pool for divide-and-conquer parallel algorithms.

```java
import java.util.concurrent.*;

class SumTask extends RecursiveTask<Long> {
    private final int[] arr;
    private final int from, to;
    static final int THRESHOLD = 1000;

    SumTask(int[] arr, int from, int to) {
        this.arr = arr; this.from = from; this.to = to;
    }

    @Override protected Long compute() {
        if (to - from <= THRESHOLD) {
            long sum = 0;
            for (int i = from; i < to; i++) sum += arr[i];
            return sum;
        }
        int mid = (from + to) / 2;
        SumTask left  = new SumTask(arr, from, mid);
        SumTask right = new SumTask(arr, mid, to);
        left.fork();               // async
        return right.compute() + left.join(); // compute right, wait for left
    }
}

int[] data = new int[1_000_000];
java.util.Arrays.fill(data, 1);
ForkJoinPool pool = new ForkJoinPool();
long total = pool.invoke(new SumTask(data, 0, data.length));
System.out.println(total); // 1000000
```

---

## Quick Reference

```
Java 7 features:
  Diamond <>           infer generic type: new HashMap<>()
  try-with-resources   auto-close AutoCloseable in try(...)
  Multi-catch          catch (A | B e)
  String switch        switch("cmd") { case "start": }
  Underscore literals  1_000_000, 0b1010_1100
  Binary literals      0b prefix
  NIO.2                Path, Files, WatchService, FileSystem
  ForkJoinPool         RecursiveTask/RecursiveAction
  invokedynamic        JVM instruction (foundation for Java 8 lambdas)
```
