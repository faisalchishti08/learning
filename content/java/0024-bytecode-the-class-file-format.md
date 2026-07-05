---
card: java
gi: 24
slug: bytecode-the-class-file-format
title: Bytecode & the .class file format
---

## 1. What it is

**Java bytecode** is the instruction set of the Java Virtual Machine — a compact, platform-neutral binary format stored in `.class` files. Every Java source file compiles to one or more `.class` files. Each `.class` file has a precisely defined binary structure called the **class file format**, specified in Chapter 4 of the Java Virtual Machine Specification (JVMS).

Bytecode is *not* native machine code. It is instructions for an imaginary machine (the JVM) that the JVM then translates to native code via interpretation or JIT compilation at runtime.

## 2. Why & when

Understanding bytecode matters for:
- **Debugging `ClassNotFoundException`, `NoSuchMethodError`, `UnsupportedClassVersionError`** — all caused by class file format issues.
- **Writing bytecode manipulation tools** (Byte Buddy, ASM, cglib) used by frameworks like Spring (AOP proxies), Mockito (mock generation), and JPA implementations.
- **Security auditing** — malicious class files can be injected; the bytecode verifier is the first line of defence.
- **Performance analysis** — understanding what `javac` compiles to helps explain JIT behaviour.
- **`javap -c`** — the built-in tool to disassemble class files to readable bytecode.

## 3. Core concept

Every `.class` file is a structured binary file with this layout:

```
ClassFile {
  u4             magic;              // always 0xCAFEBABE
  u2             minor_version;      // 0 (or 65535 for preview features)
  u2             major_version;      // 45=Java1, 52=Java8, 61=Java17, 65=Java21
  u2             constant_pool_count;
  cp_info        constant_pool[];    // strings, class refs, method refs
  u2             access_flags;       // public, final, abstract, interface, etc.
  u2             this_class;         // index into constant_pool
  u2             super_class;        // index into constant_pool
  u2             interfaces_count;
  u2             interfaces[];
  u2             fields_count;
  field_info     fields[];
  u2             methods_count;
  method_info    methods[];          // bytecode lives in method attributes
  u2             attributes_count;
  attribute_info attributes[];       // SourceFile, LineNumberTable, etc.
}
```

Key parts:
- **Magic** `0xCAFEBABE` — the first 4 bytes of every `.class` file. The JVM rejects files that don't start with this.
- **Version** — `major_version` maps to a Java release. `65` = Java 21. The JVM rejects class files with a major version higher than it supports.
- **Constant pool** — a table of strings, class names, method signatures. Bytecode instructions reference the pool by index rather than embedding strings directly.
- **Code attribute** — inside each method, the bytecode instructions are stored in a `Code` attribute.

**JVM instruction set (opcodes):** 200+ opcodes organised by type:
- `iload_1`, `aload_2` — load local variable onto stack
- `iadd`, `imul`, `idiv` — integer arithmetic
- `invokevirtual`, `invokeinterface`, `invokestatic` — method calls
- `getfield`, `putfield` — object field access
- `new`, `newarray` — object allocation
- `return`, `ireturn`, `areturn` — method return

## 4. Diagram

<svg viewBox="0 0 680 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Class file binary structure: magic, version, constant pool, methods with bytecode">
  <!-- file -->
  <rect x="20" y="20" width="280" height="200" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="160" y="44" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">HelloWorld.class (binary)</text>

  <!-- sections -->
  <rect x="30" y="52" width="260" height="28" rx="4" fill="#0d1117" stroke="#f0883e" stroke-width="1.5"/>
  <text x="160" y="68" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">CA FE BA BE  (magic 0xCAFEBABE)</text>

  <rect x="30" y="84" width="260" height="22" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="160" y="99" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">00 00  00 41  (minor=0, major=65 → Java 21)</text>

  <rect x="30" y="110" width="260" height="40" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="126" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Constant Pool</text>
  <text x="160" y="141" fill="#8b949e" font-size="8"  text-anchor="middle" font-family="sans-serif">"HelloWorld"  "java/lang/Object"  "main"  "[Ljava/lang/String;"</text>

  <rect x="30" y="154" width="260" height="22" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="160" y="169" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Access flags · this_class · super_class · interfaces</text>

  <rect x="30" y="180" width="260" height="32" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="195" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">methods[] → Code attribute</text>
  <text x="160" y="207" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">B2 00 02 12 03 B6 00 04 B1  (bytecode opcodes)</text>

  <!-- Bytecode decode -->
  <text x="360" y="40"  fill="#8b949e" font-size="11" font-family="sans-serif">Decoded bytecode (javap -c):</text>
  <text x="360" y="60"  fill="#8b949e" font-size="9"  font-family="monospace">getstatic    #2  // System.out</text>
  <text x="360" y="76"  fill="#8b949e" font-size="9"  font-family="monospace">ldc          #3  // "Hello"</text>
  <text x="360" y="92"  fill="#8b949e" font-size="9"  font-family="monospace">invokevirtual #4 // PrintStream.println</text>
  <text x="360" y="108" fill="#8b949e" font-size="9"  font-family="monospace">return</text>
  <text x="360" y="140" fill="#6db33f" font-size="9"  font-family="sans-serif">opcodes are 1 byte + operands</text>
  <text x="360" y="156" fill="#8b949e" font-size="9"  font-family="sans-serif">B2 = getstatic (opcode 0xB2)</text>
  <text x="360" y="170" fill="#8b949e" font-size="9"  font-family="sans-serif">12 = ldc (opcode 0x12)</text>
  <text x="360" y="184" fill="#8b949e" font-size="9"  font-family="sans-serif">B6 = invokevirtual (opcode 0xB6)</text>
  <text x="360" y="198" fill="#8b949e" font-size="9"  font-family="sans-serif">B1 = return (opcode 0xB1)</text>
</svg>

Binary class file structure: magic bytes → version → constant pool → methods with bytecode instructions.

## 5. Runnable example

Scenario: read and parse the class file of a real class to understand its structure — growing from reading magic bytes to fully disassembling bytecode.

### Level 1 — Basic

```java
// ClassFileMagic.java
import java.io.*;
import java.nio.file.*;

public class ClassFileMagic {
    public static void main(String[] args) throws Exception {
        // Find our own class file (only works when explicitly compiled + run, not source-launch)
        // For source-launch mode, we compile a temp class and read it

        // Compile a trivial class to a temp file and read its header
        Path tmpDir = Files.createTempDirectory("bytecode-demo");
        Path src = tmpDir.resolve("Probe.java");
        Files.writeString(src, "public class Probe { public void hello() { System.out.println(\"hi\"); } }");

        new ProcessBuilder("javac", src.toString())
            .directory(tmpDir.toFile())
            .redirectErrorStream(true)
            .start().waitFor();

        byte[] bytes = Files.readAllBytes(tmpDir.resolve("Probe.class"));

        // Magic bytes
        System.out.printf("Magic   : %02X %02X %02X %02X  (%s)%n",
            bytes[0]&0xFF, bytes[1]&0xFF, bytes[2]&0xFF, bytes[3]&0xFF,
            (bytes[0]==(byte)0xCA && bytes[1]==(byte)0xFE) ? "valid class file" : "INVALID");

        // Version
        int minor = ((bytes[4]&0xFF)<<8) | (bytes[5]&0xFF);
        int major = ((bytes[6]&0xFF)<<8) | (bytes[7]&0xFF);
        System.out.printf("Version : major=%d minor=%d  → JDK %d%s%n",
            major, minor, major-44, minor==65535 ? " (preview)" : "");

        System.out.println("Total size: " + bytes.length + " bytes");

        Files.delete(tmpDir.resolve("Probe.class"));
        Files.delete(src);
        Files.delete(tmpDir);
    }
}
```

**How to run:** `java ClassFileMagic.java`

`major - 44 = JDK version` (45 = JDK 1, 52 = JDK 8, 65 = JDK 21). `minor = 65535 = 0xFFFF` signals a preview-features class file.

### Level 2 — Intermediate

Same class file parser extended to read the constant pool size and list the string constants — the most human-readable part of the binary.

```java
// ClassFileParser.java
import java.io.*;
import java.nio.file.*;

public class ClassFileParser {
    public static void main(String[] args) throws Exception {
        // Compile a class with interesting constants
        Path tmpDir = Files.createTempDirectory("cf-parse");
        Path src = tmpDir.resolve("Sample.java");
        Files.writeString(src,
            "public class Sample {\n" +
            "    static final String MSG = \"Hello bytecode!\";\n" +
            "    public void greet(String name) {\n" +
            "        System.out.println(MSG + \", \" + name);\n" +
            "    }\n" +
            "}\n");
        new ProcessBuilder("javac", src.toString()).redirectErrorStream(true).start().waitFor();
        byte[] b = Files.readAllBytes(tmpDir.resolve("Sample.class"));

        try (DataInputStream dis = new DataInputStream(new ByteArrayInputStream(b))) {
            int magic = dis.readInt();
            System.out.printf("Magic   : 0x%08X  (%s)%n", magic, magic == 0xCAFEBABE ? "OK" : "INVALID");

            int minor = dis.readUnsignedShort();
            int major = dis.readUnsignedShort();
            System.out.printf("Version : %d.%d  (JDK %d)%n", major, minor, major - 44);

            int cpCount = dis.readUnsignedShort();
            System.out.printf("Constant pool count: %d entries%n%n", cpCount - 1);

            // Read and display string-like constants
            System.out.println("String constants in constant pool:");
            for (int i = 1; i < cpCount; i++) {
                int tag = dis.readUnsignedByte();
                switch (tag) {
                    case 1 -> {  // CONSTANT_Utf8
                        int len = dis.readUnsignedShort();
                        byte[] strBytes = dis.readNBytes(len);
                        String s = new String(strBytes);
                        if (!s.contains("(") && !s.startsWith("L") && s.length() < 50) {
                            System.out.printf("  #%-3d Utf8: \"%s\"%n", i, s);
                        }
                    }
                    case 7  -> dis.readUnsignedShort();  // CONSTANT_Class: name_index
                    case 8  -> dis.readUnsignedShort();  // CONSTANT_String: string_index
                    case 9,10,11 -> { dis.readUnsignedShort(); dis.readUnsignedShort(); } // ref tags
                    case 12 -> { dis.readUnsignedShort(); dis.readUnsignedShort(); } // NameAndType
                    case 3,4 -> dis.readInt();           // Integer/Float
                    case 5,6 -> { dis.readLong(); i++; } // Long/Double (occupy two slots)
                    case 15 -> { dis.readByte(); dis.readUnsignedShort(); } // MethodHandle
                    case 16 -> dis.readUnsignedShort();  // MethodType
                    case 18 -> { dis.readUnsignedShort(); dis.readUnsignedShort(); } // InvokeDynamic
                    default -> { /* unknown tag, stop */ return; }
                }
            }
        }

        Files.delete(tmpDir.resolve("Sample.class")); Files.delete(src); Files.delete(tmpDir);
    }
}
```

**How to run:** `java ClassFileParser.java`

The output shows `"Hello bytecode!"`, `"Sample"`, `"java/lang/System"`, etc. from the constant pool. Every string that appears in the source code ends up as a `CONSTANT_Utf8` entry — this is where string constants live.

### Level 3 — Advanced

Same class file parsing grown to use `javap -c -p -verbose` (the JDK's built-in disassembler) to display full bytecode including the stack operations — and explain each instruction.

```java
// BytecodeDisassembler.java
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class BytecodeDisassembler {

    // Sample class to disassemble — keep it small and interesting
    static final String SOURCE =
        "public class Target {\n" +
        "    private String name;\n" +
        "    public Target(String name) { this.name = name; }\n" +
        "    public int nameLength() { return name.length(); }\n" +
        "    public String greet() {\n" +
        "        return \"Hello, \" + name + \"!\";\n" +
        "    }\n" +
        "}\n";

    // Opcode → mnemonic for a selection of common opcodes
    static final Map<Integer, String> OPCODES = Map.ofEntries(
        Map.entry(0x00, "nop"),
        Map.entry(0x01, "aconst_null"),
        Map.entry(0x03, "iconst_0"),    Map.entry(0x04, "iconst_1"),
        Map.entry(0x12, "ldc"),         Map.entry(0x15, "iload"),
        Map.entry(0x19, "aload"),       Map.entry(0x1A, "iload_0"),
        Map.entry(0x2A, "aload_0"),     Map.entry(0x2B, "aload_1"),
        Map.entry(0x3A, "astore"),      Map.entry(0x3C, "istore_1"),
        Map.entry(0x4C, "astore_1"),    Map.entry(0x60, "iadd"),
        Map.entry(0xAC, "ireturn"),     Map.entry(0xB0, "areturn"),
        Map.entry(0xB1, "return"),      Map.entry(0xB2, "getstatic"),
        Map.entry(0xB4, "getfield"),    Map.entry(0xB5, "putfield"),
        Map.entry(0xB6, "invokevirtual"), Map.entry(0xB7, "invokespecial"),
        Map.entry(0xB8, "invokestatic"), Map.entry(0xBB, "new"),
        Map.entry(0x59, "dup"),         Map.entry(0x57, "pop")
    );

    public static void main(String[] args) throws Exception {
        Path tmpDir = Files.createTempDirectory("bytecode-adv");
        Path src = tmpDir.resolve("Target.java");
        Files.writeString(src, SOURCE);

        // Compile
        Process compile = new ProcessBuilder("javac", src.toString())
            .directory(tmpDir.toFile()).redirectErrorStream(true).start();
        String compileOut = new String(compile.getInputStream().readAllBytes());
        compile.waitFor();
        if (!compileOut.isBlank()) System.out.println("Compile: " + compileOut);

        // Read raw class file header
        byte[] classBytes = Files.readAllBytes(tmpDir.resolve("Target.class"));
        System.out.println("╔═══════════════════════════════════════════════╗");
        System.out.println("║         Bytecode Disassembly: Target.class    ║");
        System.out.println("╚═══════════════════════════════════════════════╝\n");

        System.out.printf("File size : %d bytes%n", classBytes.length);
        System.out.printf("Magic     : %02X%02X%02X%02X%n",
            classBytes[0]&0xFF, classBytes[1]&0xFF, classBytes[2]&0xFF, classBytes[3]&0xFF);
        int major = ((classBytes[6]&0xFF)<<8)|(classBytes[7]&0xFF);
        System.out.printf("Version   : %d (JDK %d)%n", major, major-44);

        // Use javap -c -verbose if available
        Path javap = tmpDir.resolve("../../bin/javap").normalize();
        Path javaHome = Path.of(System.getProperty("java.home"));
        Path javapBin = javaHome.resolve("bin/javap");
        boolean hasJavap = Files.exists(javapBin) || Files.exists(Path.of(javapBin + ".exe"));

        if (hasJavap) {
            System.out.println("\n[ javap -c output (method bytecode) ]");
            Process javapProc = new ProcessBuilder(
                hasJavap ? javapBin.toString() : "javap",
                "-c", tmpDir.resolve("Target.class").toString())
                .redirectErrorStream(true).start();
            String javapOut = new String(javapProc.getInputStream().readAllBytes());
            javapProc.waitFor();

            // Filter and annotate with opcode meanings
            for (String line : javapOut.split("\n")) {
                System.out.println("  " + line);
                // Annotate opcode lines
                line = line.trim();
                if (line.matches("\\d+:.*")) {
                    String opcode = line.replaceAll("^\\d+:\\s*(\\w+).*", "$1").toLowerCase();
                    addOpcodeNote(opcode);
                }
            }
        } else {
            System.out.println("\njavap not found (JRE-only image). Install JDK for bytecode disassembly.");
            System.out.println("Use: javap -c Target.class");
        }

        // Cleanup
        Files.delete(tmpDir.resolve("Target.class")); Files.delete(src); Files.delete(tmpDir);
    }

    static void addOpcodeNote(String opcode) {
        String note = switch (opcode) {
            case "aload_0"       -> "  // push 'this' reference onto stack";
            case "getfield"      -> "  // pop ref, push field value";
            case "invokevirtual" -> "  // pop args + receiver, call virtual method";
            case "invokespecial" -> "  // call constructor or private method";
            case "new"           -> "  // allocate new object on heap";
            case "dup"           -> "  // duplicate top stack value";
            case "putfield"      -> "  // pop value + ref, store to field";
            case "areturn"       -> "  // return object reference";
            case "return"        -> "  // return void";
            default -> "";
        };
        if (!note.isEmpty()) System.out.println(note);
    }
}
```

**How to run:** `java BytecodeDisassembler.java`

`javap -c Target.class` is the standard JDK tool for bytecode inspection. The program adds inline annotations explaining what each opcode category does.

## 6. Walkthrough

Execution in `BytecodeDisassembler.main`:

1. **Source generation** — `Files.writeString(src, SOURCE)` writes the `Target` class to a temp file. `ProcessBuilder("javac", ...)` invokes the compiler in a subprocess. This is exactly what build tools (Maven, Gradle) do internally.

2. **Class file header parse** — `classBytes[0..3]` = `0xCAFEBABE` (the JVM rejects files lacking this). `major` = bytes 6–7 big-endian: `(bytes[6]&0xFF)<<8 | (bytes[7]&0xFF)`. Java uses big-endian in class files regardless of the host CPU's byte order.

3. **`javap -c` subprocess** — `javap` is a JDK tool (not in JRE). It reads the class file, decodes the constant pool, and prints method bytecode in a human-readable format:
   ```
   public int nameLength();
     Code:
        0: aload_0          // push this
        1: getfield #7      // push this.name
        4: invokevirtual #13 // String.length()
        7: ireturn           // return int
   ```

4. **Opcode annotation** — the `addOpcodeNote` method pattern-matches the opcode mnemonic and adds a comment explaining the stack operation. This is how frameworks like ASM describe bytecode: each instruction pops and pushes typed values from/to the operand stack.

Key bytecode for `nameLength()`:
```
Method entry: operand stack = []
aload_0     → stack = [this]
getfield #7 → stack = [this.name (String)]
invokevirtual #13 → stack = [name.length() result (int)]
ireturn     → return the int, stack = []
```

The operand stack is a key concept: bytecode instructions operate by pushing and popping values from this thread-local stack. `aload_0` pushes the `this` reference; `getfield` consumes the reference and pushes the field value; `invokevirtual` consumes the receiver and arguments, pushes the return value.

## 7. Gotchas & takeaways

> **`UnsupportedClassVersionError: class compiled for JDK N, JVM only supports up to M`** — this is the class file major version mismatch. The JVM reads bytes 6–7 and rejects the file if `major > max_supported_major`. Fix: recompile with `--release M` or upgrade the JVM.

> **`java.class.version` system property is `"65.0"` for Java 21 class files.** The `65` is the major version number. `65 - 44 = 21`. This mapping: 45=Java1, 46=Java2, …, 52=Java8, 61=Java17, 65=Java21, 69=Java25.

- Every `.class` file starts with `0xCAFEBABE` — the JVM's first structural check.
- Class file `major_version` = `44 + JDK_version` (52 = Java8, 65 = Java21).
- `javap -c ClassName.class` disassembles bytecode to human-readable form.
- The constant pool is where all strings, class references, and method signatures live; bytecode instructions reference it by index.
- The operand stack is the core execution model: instructions push/pop typed values.
- Bytecode manipulation libraries (ASM, Byte Buddy) generate or modify `.class` bytecode directly — used by Spring AOP, Mockito, JPA implementations.
