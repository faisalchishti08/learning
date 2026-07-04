---
card: spring-framework
gi: 262
slug: rowmapper-resultsetextractor-rowcallbackhandler
title: RowMapper / ResultSetExtractor / RowCallbackHandler
---

## 1. What it is

Spring JDBC defines three callback interfaces for consuming a `ResultSet`. Each trades control and memory characteristics:

| Interface | Return type | Spring iterates? | Use |
|---|---|---|---|
| `RowMapper<T>` | `T` per row | yes | map each row to an object; Spring collects into `List<T>` |
| `ResultSetExtractor<T>` | `T` for whole set | no | full cursor control; build any result shape |
| `RowCallbackHandler` | void | yes | process each row (write CSV, stream, accumulate stats) without collecting |

All three receive a live `ResultSet` positioned on a row (or the full set) — you never call `rs.next()` in `RowMapper` or `RowCallbackHandler`.

## 2. Why & when

**`RowMapper<T>`** covers 90% of cases: you want a `List<Order>` or `Optional<User>`. It's composable — define it once, reuse across multiple query methods.

**`ResultSetExtractor<T>`** is for cases where the result shape cannot be expressed as a flat list:
- Multi-row aggregation into a single object.
- One-to-many joins (one `Order` has many `OrderItem`s) — you fold multiple rows into one object.
- Custom pagination or streaming where you don't want all rows materialised at once.

**`RowCallbackHandler`** is for side-effectful processing — write rows directly to an `OutputStream`, count rows without keeping objects in memory, or feed a streaming pipeline.

## 3. Core concept

`JdbcTemplate` provides overloads for all three:

```java
// RowMapper — Spring calls mapRow(rs, rowNum) for each row, collects results
List<T>  jdbc.query(sql, RowMapper<T>, args...)
T        jdbc.queryForObject(sql, RowMapper<T>, args...)  // exactly 1 row expected

// ResultSetExtractor — Spring hands you the whole ResultSet positioned before row 1
T        jdbc.query(sql, ResultSetExtractor<T>, args...)

// RowCallbackHandler — Spring calls processRow(rs) for each row; return void
void     jdbc.query(sql, RowCallbackHandler, args...)
```

Inside `JdbcTemplate.query()`, all three go through the same JDBC machinery — `DataSourceUtils.getConnection()`, prepare statement, execute, iterate — the only difference is which callback drives the loop.

`RowMapper` is wrapped in a `RowMapperResultSetExtractor` before entering `JdbcTemplate.execute()`, which explains why `ResultSetExtractor` is the lowest-level primitive.

## 4. Diagram

<svg viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- JdbcTemplate executes -->
  <rect x="10" y="95" width="140" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="80" y="116" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">JdbcTemplate</text>
  <text x="80" y="133" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">execute + ResultSet</text>

  <!-- Three callbacks -->
  <!-- RowMapper -->
  <rect x="220" y="20" width="200" height="56" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="44" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">RowMapper&lt;T&gt;</text>
  <text x="320" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">mapRow(rs, n) → T per row</text>
  <text x="320" y="72" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="monospace">returns List&lt;T&gt;</text>

  <!-- ResultSetExtractor -->
  <rect x="220" y="92" width="200" height="56" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="116" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">ResultSetExtractor&lt;T&gt;</text>
  <text x="320" y="132" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">extractData(rs) → T</text>
  <text x="320" y="144" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">full cursor control</text>

  <!-- RowCallbackHandler -->
  <rect x="220" y="164" width="200" height="56" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="188" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">RowCallbackHandler</text>
  <text x="320" y="204" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">processRow(rs) void per row</text>
  <text x="320" y="216" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">side-effects, no collection</text>

  <!-- arrows from JdbcTemplate -->
  <line x1="152" y1="105" x2="218" y2="55" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="152" y1="120" x2="218" y2="120" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="152" y1="135" x2="218" y2="185" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
</svg>

All three callbacks receive a live `ResultSet`. Only `RowMapper` and `RowCallbackHandler` are iterated by Spring; `ResultSetExtractor` has full control.

## 5. Runnable example

Scenario: a **book library** — query books. Progress from simple per-row mapping (`RowMapper`) through multi-row aggregation (`ResultSetExtractor`) to memory-efficient processing (`RowCallbackHandler`).

### Level 1 — Basic

`RowMapper<Book>` — map each row to a typed `Book` object.

```java
// LibraryDemo.java
import org.springframework.jdbc.core.*;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.util.List;

record Book(long id, String title, String author, String genre, int year) {}

public class LibraryDemo {

    static final RowMapper<Book> BOOK_MAPPER = (rs, n) -> new Book(
        rs.getLong("id"),
        rs.getString("title"),
        rs.getString("author"),
        rs.getString("genre"),
        rs.getInt("year"));

    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:library-schema.sql")
            .addScript("classpath:library-data.sql")
            .build();
    }

    public static void main(String[] args) {
        JdbcTemplate jdbc = new JdbcTemplate(buildDs());

        // query() with RowMapper → List<Book>
        List<Book> all = jdbc.query("SELECT * FROM books ORDER BY year", BOOK_MAPPER);
        System.out.println("All books (" + all.size() + "):");
        all.forEach(b -> System.out.printf("  [%d] %s by %s (%d)%n",
            b.id(), b.title(), b.author(), b.year()));

        // queryForObject with RowMapper — exactly one row
        Book oldest = jdbc.queryForObject(
            "SELECT * FROM books ORDER BY year LIMIT 1", BOOK_MAPPER);
        System.out.println("Oldest: " + oldest.title() + " (" + oldest.year() + ")");
    }
}
```

`library-schema.sql`: `CREATE TABLE books (id BIGINT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(200), author VARCHAR(100), genre VARCHAR(60), year INT);`

`library-data.sql`:
```sql
INSERT INTO books(title,author,genre,year) VALUES('Clean Code','Robert Martin','Tech',2008);
INSERT INTO books(title,author,genre,year) VALUES('Dune','Frank Herbert','Sci-Fi',1965);
INSERT INTO books(title,author,genre,year) VALUES('Foundation','Isaac Asimov','Sci-Fi',1951);
INSERT INTO books(title,author,genre,year) VALUES('Pragmatic Programmer','Dave Thomas','Tech',1999);
INSERT INTO books(title,author,genre,year) VALUES('Neuromancer','William Gibson','Sci-Fi',1984);
```

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. LibraryDemo.java`

`RowMapper<Book>` is called once per row by `RowMapperResultSetExtractor`. You never touch `rs.next()` — Spring does that. The lambda receives `rs` already positioned on the current row and a 1-based `rowNum`.

---

### Level 2 — Intermediate

`ResultSetExtractor<Map<String,List<Book>>>` — fold multiple rows into a genre→books map.

```java
// LibraryDemo.java
import org.springframework.jdbc.core.*;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.sql.ResultSet;
import java.util.*;

record Book(long id, String title, String author, String genre, int year) {}

public class LibraryDemo {

    // ResultSetExtractor has full cursor control — call rs.next() yourself
    static final ResultSetExtractor<Map<String, List<Book>>> BY_GENRE_EXTRACTOR = rs -> {
        Map<String, List<Book>> map = new LinkedHashMap<>();
        while (rs.next()) {
            String genre = rs.getString("genre");
            map.computeIfAbsent(genre, k -> new ArrayList<>()).add(new Book(
                rs.getLong("id"), rs.getString("title"),
                rs.getString("author"), genre, rs.getInt("year")));
        }
        return map;
    };

    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:library-schema.sql")
            .addScript("classpath:library-data.sql")
            .build();
    }

    public static void main(String[] args) {
        JdbcTemplate jdbc = new JdbcTemplate(buildDs());

        Map<String, List<Book>> byGenre = jdbc.query(
            "SELECT * FROM books ORDER BY genre, year", BY_GENRE_EXTRACTOR);

        byGenre.forEach((genre, books) -> {
            System.out.println(genre + ":");
            books.forEach(b -> System.out.printf("  %-40s (%d)%n", b.title(), b.year()));
        });

        // ResultSetExtractor for one-to-many join simulation
        // Find newest book per genre
        Map<String, Book> newest = jdbc.query(
            "SELECT * FROM books b1 WHERE year = (SELECT MAX(year) FROM books b2 WHERE b2.genre=b1.genre) ORDER BY genre",
            (ResultSetExtractor<Map<String,Book>>) rs -> {
                Map<String,Book> m = new LinkedHashMap<>();
                while (rs.next()) m.put(rs.getString("genre"), new Book(
                    rs.getLong("id"), rs.getString("title"),
                    rs.getString("author"), rs.getString("genre"), rs.getInt("year")));
                return m;
            });
        System.out.println("\nNewest per genre:");
        newest.forEach((g, b) -> System.out.printf("  %-10s → %s%n", g, b.title()));
    }
}
```

How to run: same classpath

`ResultSetExtractor.extractData(rs)` receives the `ResultSet` positioned before the first row — you control the loop with `while (rs.next())`. You return whatever shape you want: a `Map`, a `Tree`, a single aggregated object. This is how Spring handles one-to-many joins — one SQL query with multiple rows for the same "parent" collapses into one parent with a list of children.

---

### Level 3 — Advanced

`RowCallbackHandler` — stream books to a CSV writer without materialising the list; combine all three callbacks in one class.

```java
// LibraryDemo.java
import org.springframework.jdbc.core.*;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.sql.ResultSet;
import java.util.*;

record Book(long id, String title, String author, String genre, int year) {}

public class LibraryDemo {

    static final RowMapper<Book> BOOK_MAPPER = (rs, n) -> new Book(
        rs.getLong("id"), rs.getString("title"),
        rs.getString("author"), rs.getString("genre"), rs.getInt("year"));

    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:library-schema.sql")
            .addScript("classpath:library-data.sql")
            .build();
    }

    public static void main(String[] args) {
        JdbcTemplate jdbc = new JdbcTemplate(buildDs());

        // RowCallbackHandler — side-effectful, no collection returned
        // Great for: streaming export, writing to OutputStream, accumulating stats
        int[] stats = {0, 0};   // [count, totalYear]
        StringBuilder csv = new StringBuilder("id,title,author,genre,year\n");

        jdbc.query("SELECT * FROM books ORDER BY year", (RowCallbackHandler) rs -> {
            stats[0]++;
            stats[1] += rs.getInt("year");
            csv.append(rs.getLong("id")).append(',')
               .append('"').append(rs.getString("title")).append('"').append(',')
               .append(rs.getString("author")).append(',')
               .append(rs.getString("genre")).append(',')
               .append(rs.getInt("year")).append('\n');
        });

        System.out.println("Books processed: " + stats[0]);
        System.out.printf("Average publication year: %.0f%n", (double) stats[1] / stats[0]);
        System.out.println("\nCSV output:");
        System.out.print(csv);

        // BeanPropertyRowMapper — convention-based, zero lambda code
        List<Book> byMapper = jdbc.query(
            "SELECT * FROM books WHERE genre=?",
            BeanPropertyRowMapper.newInstance(Book.class), "Sci-Fi");
        System.out.println("\nSci-Fi via BeanPropertyRowMapper: " + byMapper.size() + " books");

        // ColumnMapRowMapper — Map<String,Object> per row; useful for dynamic/unknown schemas
        List<Map<String,Object>> raw = jdbc.query(
            "SELECT title, year FROM books ORDER BY year DESC LIMIT 2",
            new ColumnMapRowMapper());
        System.out.println("Top 2 recent (raw map): " + raw);
    }
}
```

How to run: same classpath

`RowCallbackHandler` processes each row as a side effect — here we build a CSV string and compute statistics in one pass without creating a `List<Book>` in memory. For very large result sets this avoids GC pressure. `BeanPropertyRowMapper` handles the conventional case: column `AUTHOR` maps to setter `setAuthor()` / accessor `author()`. `ColumnMapRowMapper` returns `Map<String,Object>` keyed by uppercase column name — handy for reporting queries where the schema is dynamic.

## 6. Walkthrough

**Level 2 — `ResultSetExtractor` for genre grouping (execution order):**

1. **`jdbc.query(sql, BY_GENRE_EXTRACTOR)`**: `JdbcTemplate` opens a connection via `DataSourceUtils.getConnection(ds)`.
2. **PreparedStatement**: `con.prepareStatement("SELECT * FROM books ORDER BY genre, year")` — no params to bind.
3. **Execute**: `ps.executeQuery()` — H2 returns a `ResultSet` with 5 rows, sorted `Sci-Fi` first (1951, 1965, 1984) then `Tech` (1999, 2008).
4. **`ResultSetExtractor.extractData(rs)` called once** — the extractor receives `rs` positioned *before* row 1.
5. **Extractor loop**:
   - `rs.next()` → row 1: genre=`Sci-Fi`, title=`Foundation`, year=1951 → `map["Sci-Fi"] = [Foundation]`
   - `rs.next()` → row 2: genre=`Sci-Fi`, title=`Dune`, year=1965 → `map["Sci-Fi"].add(Dune)`
   - `rs.next()` → row 3: genre=`Sci-Fi`, title=`Neuromancer`, year=1984 → `map["Sci-Fi"].add(Neuromancer)`
   - `rs.next()` → row 4: genre=`Tech`, title=`Pragmatic Programmer`, year=1999 → `map["Tech"] = [PP]`
   - `rs.next()` → row 5: genre=`Tech`, title=`Clean Code`, year=2008 → `map["Tech"].add(Clean Code)`
   - `rs.next()` → false → loop ends
6. **Return** `Map{Sci-Fi=[Foundation,Dune,Neuromancer], Tech=[PP,Clean Code]}`.
7. **Cleanup**: `rs.close()`, `ps.close()`, `DataSourceUtils.releaseConnection(con, ds)`.

```
SQL:      SELECT * FROM books ORDER BY genre, year
DB rows:  [Foundation/Sci-Fi/1951, Dune/Sci-Fi/1965, Neuromancer/Sci-Fi/1984,
           Pragmatic Programmer/Tech/1999, Clean Code/Tech/2008]
After extractor:
  Map {
    "Sci-Fi" → [Foundation, Dune, Neuromancer]
    "Tech"   → [Pragmatic Programmer, Clean Code]
  }
```

## 7. Gotchas & takeaways

> **Never call `rs.next()` inside a `RowMapper` or `RowCallbackHandler`.** Spring has already advanced the cursor; calling it again skips a row silently. Only `ResultSetExtractor` owns the cursor.

> **`queryForObject` with `RowMapper` throws `EmptyResultDataAccessException` on zero rows** — not `null`. Wrap in try/catch or use `query()` and check `isEmpty()` if the row might not exist.

> **`BeanPropertyRowMapper` is reflective and slow under heavy load.** For high-throughput paths define an explicit lambda `RowMapper` — it's faster and checked at compile time.

- `RowMapper<T>` — simplest: map row → object; Spring collects into `List<T>`.
- `ResultSetExtractor<T>` — full cursor control; fold multiple rows into any result type (maps, trees, one-to-many).
- `RowCallbackHandler` — side effects per row; no collection; good for streaming large result sets.
- `BeanPropertyRowMapper` — convention-based; maps `COLUMN_NAME` → `setColumnName()`; slow for hot paths.
- `ColumnMapRowMapper` — returns `Map<String,Object>` per row; handy for dynamic/reporting queries.
