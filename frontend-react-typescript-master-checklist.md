# Senior Frontend / Full-Stack Engineer (10 YOE, React + TypeScript) — Master Knowledge & Interview Checklist

> A complete macro → micro topic map of what a 10-year frontend / full-stack engineer is expected to know,
> with **React and TypeScript as the primary focus**, plus the web platform (HTML, CSS, JavaScript), performance,
> accessibility, security, tooling, frontend system design, Node.js full-stack, and leadership.
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

**Part A — Web Platform Foundations**
1. [How the Web & Browsers Work](#1-how-the-web--browsers-work-p0)
2. [HTML](#2-html-p0)
3. [CSS](#3-css-p0)
4. [JavaScript (Deep)](#4-javascript-deep-p0)
5. [TypeScript (Deep)](#5-typescript-deep-p0)

**Part B — React**
6. [React Fundamentals & Rendering Model](#6-react-fundamentals--rendering-model-p0)
7. [Hooks (Deep)](#7-hooks-deep-p0)
8. [React Performance](#8-react-performance-p0)
9. [React 18/19, Concurrent Features & Server Components](#9-react-1819-concurrent-features--server-components-p0)
10. [State Management](#10-state-management-p0)
11. [Data Fetching & Server State](#11-data-fetching--server-state-p0)
12. [Forms](#12-forms-p1)
13. [Routing](#13-routing-p1)
14. [Meta-Frameworks & Rendering Strategies (Next.js et al.)](#14-meta-frameworks--rendering-strategies-p0)
15. [Styling & Design Systems](#15-styling--design-systems-p0)
16. [Component Architecture & Patterns](#16-component-architecture--patterns-p0)
17. [TypeScript with React](#17-typescript-with-react-p0)

**Part C — Engineering Quality**
18. [Build Tooling, Package Management & Monorepos](#18-build-tooling-package-management--monorepos-p0)
19. [Testing](#19-testing-p0)
20. [Web Performance & Core Web Vitals](#20-web-performance--core-web-vitals-p0)
21. [Accessibility (a11y)](#21-accessibility-p0)
22. [Frontend Security](#22-frontend-security-p0)
23. [Browser APIs, PWAs & Advanced Web](#23-browser-apis-pwas--advanced-web-p1)
24. [Internationalization](#24-internationalization-p1)

**Part D — Architecture & System Design**
25. [Frontend Architecture at Scale](#25-frontend-architecture-at-scale-p0)
26. [Frontend System Design](#26-frontend-system-design-p0)
27. [UI Machine Coding Round](#27-ui-machine-coding-round-p0)

**Part E — Full-Stack**
28. [Node.js (Deep)](#28-nodejs-deep-p0)
29. [Backend for Frontend Engineers](#29-backend-for-frontend-engineers-p0)
30. [Backend System Design Essentials](#30-backend-system-design-essentials-p1)
31. [DevOps, Deployment & Observability for Frontend](#31-devops-deployment--observability-p1)
32. [Mobile & Cross-Platform](#32-mobile--cross-platform-p2)
33. [AI in Frontend Engineering](#33-ai-in-frontend-engineering-p1)

**Part F — Problem Solving**
34. [DSA in JavaScript/TypeScript](#34-dsa-in-javascripttypescript-p0)
35. [JavaScript Coding Questions (Implement from Scratch)](#35-javascript-coding-questions-p0)

**Part G — Leadership, Behavioral & Career**
36. [Technical Leadership](#36-technical-leadership-p0)
37. [Behavioral Interviews & Story Bank](#37-behavioral-interviews--story-bank-p0)
38. [Project Deep-Dive, Resume & Negotiation](#38-project-deep-dive-resume--negotiation-p0)
39. [Interview Formats](#39-interview-formats)

**Part H — Execution**
40. [Rapid-Fire Questions (Top 100)](#40-rapid-fire-questions-top-100)
41. [12-Week Preparation Plan](#41-12-week-preparation-plan)
42. [Resources](#42-resources)
43. [Final Readiness Checklist](#43-final-readiness-checklist)

---

# PART A — WEB PLATFORM FOUNDATIONS

## 1. How the Web & Browsers Work (P0)

### 1.1 Networking for Frontend
- [ ] **"What happens when you type a URL"** — DNS → TCP/QUIC → TLS → HTTP request → server/CDN → response → parsing → rendering → interactivity
- [ ] **HTTP/1.1 vs HTTP/2 vs HTTP/3** — connection limits (6 per origin in HTTP/1.1), multiplexing, header compression, HOL blocking, QUIC; why domain sharding/sprite sheets/bundling-everything are outdated under HTTP/2+
- [ ] **HTTP caching** — `Cache-Control` (`max-age`, `s-maxage`, `no-cache` vs `no-store`, `immutable`, `stale-while-revalidate`), `ETag`/`If-None-Match`, `Last-Modified`, `Vary`, 304; content-hashed filenames for long-term caching
- [ ] **CDNs** — edge caching, cache keys, purging, edge functions
- [ ] **Cookies** — `Secure`, `HttpOnly`, `SameSite` (Lax/Strict/None), `Domain`/`Path`, partitioned cookies (CHIPS), third-party cookie phase-out/privacy changes
- [ ] **Same-origin policy & CORS** — simple vs preflighted requests, `Access-Control-Allow-*`, credentials mode
- [ ] **Compression** — gzip vs Brotli vs zstd
- [ ] **TLS basics**, HSTS, mixed content

### 1.2 Browser Architecture
- [ ] **Multi-process model** — browser, renderer (per site — site isolation), GPU, network processes
- [ ] **Rendering engine** (Blink, WebKit, Gecko) & **JS engine** (V8, JavaScriptCore, SpiderMonkey)
- [ ] **V8 internals (awareness)** — parser, Ignition interpreter, TurboFan/Maglev JIT, hidden classes/shapes, inline caches, deoptimization, generational GC (Scavenger/Orinoco)

### 1.3 Critical Rendering Path (P0)
- [ ] HTML parsing → **DOM**; CSS parsing → **CSSOM**; render tree; **layout (reflow)**; **paint**; **composite** (layers, GPU)
- [ ] **Render-blocking** CSS, **parser-blocking** scripts; `async` vs `defer` vs `type="module"`; preload scanner
- [ ] **Reflow vs repaint vs composite-only** changes; **layout thrashing** (interleaved reads/writes, forced synchronous layout)
- [ ] **Compositing layers** — `transform`/`opacity` animations on the compositor, `will-change`, layer explosion
- [ ] Frame budget — 60 fps ≈ 16.7 ms per frame; 120 Hz displays

### 1.4 Event Loop (P0)
- [ ] Call stack, heap, **task (macrotask) queue**, **microtask queue** (Promises, `queueMicrotask`, MutationObserver), **rendering steps** (`requestAnimationFrame` → style → layout → paint), `requestIdleCallback`
- [ ] Ordering puzzles — `setTimeout` vs `Promise.then` vs `async/await` vs `rAF`
- [ ] **Long tasks** (> 50 ms) and their effect on responsiveness (INP); yielding (`scheduler.yield()`, `setTimeout(0)`, `scheduler.postTask`)
- [ ] Node.js event loop differences (§28)

### 🎯 Frequently Asked
- What happens when you type a URL into the browser?
- Explain the critical rendering path; how do you make a page render faster?
- Reflow vs repaint; what triggers layout thrashing?
- Output-ordering puzzle with `setTimeout`, promises, and `async/await`

---

## 2. HTML (P0)

- [ ] **Semantic HTML** — `header`, `nav`, `main`, `article`, `section`, `aside`, `footer`, headings hierarchy, landmarks; why semantics matter (a11y, SEO, maintainability)
- [ ] **Document structure** — doctype, `lang`, charset, viewport meta, `<head>` contents
- [ ] **Forms** — input types (email, number, date, tel, range, file…), `label`/`for`, `fieldset`/`legend`, `autocomplete` tokens, `inputmode`, `enterkeyhint`, **Constraint Validation API** (`required`, `pattern`, `setCustomValidity`, `:invalid`/`:user-invalid`), form submission semantics, `FormData`, buttons default to `type="submit"`
- [ ] **Images & media** — `alt`, `srcset` + `sizes`, `<picture>` (art direction, AVIF/WebP fallbacks), `loading="lazy"`, `decoding="async"`, `fetchpriority="high"` for LCP image, explicit `width`/`height` (CLS), `<video>`/`<audio>`, captions (`<track>`)
- [ ] **Resource hints** — `preload` (with `as`), `prefetch`, `preconnect`, `dns-prefetch`, `modulepreload`; Speculation Rules API (prerender/prefetch)
- [ ] **Script loading** — classic vs module scripts, `async`, `defer`, `nomodule`, import maps
- [ ] **Modern elements** — `<dialog>` (modal, `showModal`, focus handling), `<details>/<summary>`, **Popover API** (`popover` attribute), `<template>`, `<slot>`, `inert` attribute, `<search>`
- [ ] **iframes** — `sandbox`, `allow`, `loading="lazy"`, `postMessage` with origin checks
- [ ] **SEO & sharing** — `<title>`, meta description, canonical, robots, Open Graph/Twitter cards, structured data (JSON-LD), sitemap, hreflang
- [ ] **Web Components** — Custom Elements (lifecycle callbacks), Shadow DOM (encapsulation, `::part`, slots), declarative shadow DOM, interop with React (React 19 supports custom elements properly)
- [ ] `data-*` attributes, global attributes, content editable

---

## 3. CSS (P0)

### 3.1 Fundamentals
- [ ] **Cascade** — origin, importance, **`@layer`** cascade layers, specificity (inline > id > class/attr/pseudo-class > element), order; inheritance; `initial`/`inherit`/`unset`/`revert`/`revert-layer`
- [ ] **Box model** — content/padding/border/margin, `box-sizing: border-box`, margin collapsing
- [ ] **Display & formatting contexts** — block, inline, inline-block, flow-root, **Block Formatting Context** (BFC), stacking contexts
- [ ] **Positioning** — static, relative, absolute (containing block), fixed, sticky (gotchas with overflow)
- [ ] **Stacking context & z-index** — what creates a stacking context (`position`+`z-index`, `opacity < 1`, `transform`, `filter`, `isolation`, `will-change`…); the "z-index: 9999 doesn't work" problem
- [ ] **Units** — `px`, `em`, `rem`, `%`, `vw`/`vh`, **`dvh`/`svh`/`lvh`** (mobile viewports), `ch`, `ex`, container query units (`cqw`, `cqi`)
- [ ] **Functions** — `calc()`, `clamp()` (fluid typography), `min()`, `max()`, `var()`, `env()` (safe areas), `color-mix()`
- [ ] **Overflow**, text overflow & ellipsis, line clamping, `object-fit`, `aspect-ratio`

### 3.2 Layout (P0)
- [ ] **Flexbox** — main/cross axes, `flex-grow`/`shrink`/`basis`, `flex: 1` meaning, alignment (`justify-content`, `align-items`, `align-self`, `align-content`), `gap`, wrapping, `min-width: 0` gotcha
- [ ] **CSS Grid** — tracks, `fr`, `repeat(auto-fill/auto-fit, minmax())`, named areas, implicit vs explicit grid, `grid-auto-flow: dense`, **subgrid**, alignment
- [ ] **Flexbox vs Grid** — 1D vs 2D; content-out vs layout-in
- [ ] Classic layouts — centering (every method), holy grail, sticky footer, sidebar layouts, masonry (and native CSS masonry status)
- [ ] **Multi-column layout** (awareness)

### 3.3 Responsive & Modern CSS
- [ ] **Mobile-first** media queries, breakpoints strategy, `prefers-color-scheme`, `prefers-reduced-motion`, `prefers-contrast`, `hover`/`pointer` media features
- [ ] **Container queries** (`container-type`, `@container`) & style queries — component-driven responsiveness
- [ ] **Modern selectors** — `:has()` (parent selector), `:is()`, `:where()` (zero specificity), `:not()`, `:focus-visible`, `:focus-within`, `:user-invalid`, `::marker`, `::backdrop`
- [ ] **Native CSS nesting**, custom properties (runtime theming, `@property` typed properties)
- [ ] **Logical properties** (`margin-inline`, `padding-block`) for RTL
- [ ] **Newer features** — View Transitions API, scroll-driven animations, anchor positioning, `@starting-style`, `text-wrap: balance/pretty`, `field-sizing`, `light-dark()`, relative color syntax, OKLCH/`color()` wide-gamut colors, `@scope`
- [ ] **Browser support strategy** — Baseline (Widely available/Newly available), progressive enhancement, `@supports`, Autoprefixer/PostCSS/Lightning CSS

### 3.4 Animations & Visual Effects
- [ ] Transitions vs keyframe animations, timing functions, `transform`/`opacity` for 60 fps, `will-change` cautiously, FLIP technique, Web Animations API, reduced-motion handling
- [ ] Filters, blend modes, masks, clip-path, gradients, shadows (performance cost)

### 3.5 Typography & Assets
- [ ] Web fonts — `@font-face`, `font-display` (swap/optional), preloading fonts, subsetting, variable fonts, `size-adjust` & fallback metric overrides (avoid CLS), system font stacks
- [ ] SVG inline vs `<img>` vs sprite vs icon fonts (avoid); `currentColor`

### 3.6 CSS Architecture at Scale (P0)
- [ ] **Methodologies** — BEM, OOCSS, SMACSS, ITCSS, utility-first
- [ ] **Scoping strategies** — CSS Modules, Shadow DOM, `@scope`, CSS-in-JS
- [ ] **CSS-in-JS** — runtime (styled-components, Emotion: runtime cost, SSR complexity, poor fit with React Server Components) vs **zero-runtime** (vanilla-extract, Linaria, Panda CSS, StyleX, Pigment CSS)
- [ ] **Tailwind CSS** (v4: CSS-first config, Oxide engine) — pros/cons, `@apply`, design tokens, class sorting, `clsx`/`cva`/`tailwind-merge`
- [ ] **Preprocessors/postprocessors** — Sass (mixins, functions, modules), PostCSS, Lightning CSS
- [ ] **Design tokens** — primitives → semantic → component tokens, theming (light/dark, brand), Style Dictionary
- [ ] Dead CSS removal, critical CSS, CSS bundle size, specificity wars prevention

### 🎯 Frequently Asked
- Explain specificity and the cascade; what are cascade layers for?
- Flexbox vs Grid — when each? Center a div 5 ways
- What creates a stacking context? Why isn't my z-index working?
- How do you approach responsive design today (container queries vs media queries)?
- CSS-in-JS vs CSS Modules vs Tailwind for a large team

---

## 4. JavaScript (Deep) (P0)

### 4.1 Language Fundamentals
- [ ] **Types** — 7 primitives (string, number, bigint, boolean, undefined, symbol, null) + objects; `typeof` quirks (`typeof null === "object"`)
- [ ] **Type coercion** — `==` vs `===`, truthy/falsy, `Object.is` (NaN, ±0), `+` operator rules, `ToPrimitive`
- [ ] **Declarations** — `var` vs `let` vs `const`, **hoisting**, **temporal dead zone**, block scope, function hoisting
- [ ] **Scope & closures** — lexical scope, closure use cases (data privacy, factories, memoization), closure memory leaks, the loop + `var` + `setTimeout` puzzle
- [ ] **`this` binding rules** — default, implicit, explicit (`call`/`apply`/`bind`), `new`, arrow functions (lexical `this`), class methods losing `this`, priority order
- [ ] **Functions** — declarations vs expressions, IIFE, arrow functions (no `arguments`, no `new`), default/rest params, higher-order functions, currying, pure functions
- [ ] **Prototypes** — `[[Prototype]]`, `__proto__` vs `prototype`, prototype chain lookups, `Object.create`, `new` operator steps, inheritance via prototypes
- [ ] **Classes** — syntactic sugar over prototypes, `extends`/`super`, **private fields `#x`**, static members & static blocks, getters/setters, `instanceof`
- [ ] **Objects** — property descriptors (`writable`, `enumerable`, `configurable`), `Object.defineProperty`, `freeze` vs `seal` vs `preventExtensions`, shallow vs deep copy (`structuredClone`), spread vs `Object.assign`, property order, computed keys, getters
- [ ] **Equality & immutability** — reference vs value; immutable update patterns (spread, `toSorted`, `toSpliced`, `with`)
- [ ] **Numbers** — IEEE-754 (`0.1 + 0.2`), `Number.EPSILON`, safe integers, `BigInt`, `NaN` handling, `parseInt` radix
- [ ] **Strings** — immutability, template literals, tagged templates, Unicode & grapheme clusters (`Intl.Segmenter`), `localeCompare`
- [ ] **Symbols** — unique keys, well-known symbols (`Symbol.iterator`, `Symbol.asyncIterator`, `Symbol.toPrimitive`)
- [ ] **Iterators & generators** — iteration protocol, `for...of` vs `for...in`, generators (`function*`, `yield`), async generators, `for await...of`; **Iterator helpers** (`.map`, `.filter`, `.take` on iterators)
- [ ] **Collections** — `Map` vs object, `Set` (and new Set methods: `union`, `intersection`, `difference`), `WeakMap`/`WeakSet` (private data, caches without leaks), `WeakRef`/`FinalizationRegistry`
- [ ] **Arrays** — mutating vs non-mutating methods, `map`/`filter`/`reduce`/`flatMap`/`find`/`findLast`/`some`/`every`/`at`, `Array.from`, sparse arrays, sorting stability & comparator pitfalls, `Object.groupBy`/`Map.groupBy`
- [ ] **Destructuring, spread/rest, optional chaining `?.`, nullish coalescing `??`, logical assignment (`||=`, `&&=`, `??=`)**
- [ ] **Error handling** — `Error` types, custom errors, `cause`, `AggregateError`, `try/catch/finally`, global handlers (`window.onerror`, `unhandledrejection`)
- [ ] **Regular expressions** — groups, named groups, lookahead/lookbehind, flags (`g`, `u`, `v`, `y`, `s`, `d`), `matchAll`, ReDoS
- [ ] **Proxy & Reflect** — traps, use cases (validation, reactivity systems like Vue/MobX), meta-programming
- [ ] **Strict mode** differences
- [ ] **Explicit resource management** (`using`/`await using`, `Symbol.dispose`) — awareness

### 4.2 Asynchronous JavaScript (P0)
- [ ] Callbacks & callback hell
- [ ] **Promises** — states, chaining, error propagation, `then` returning promises, `Promise.resolve/reject`, **`all` vs `allSettled` vs `race` vs `any`**, `Promise.withResolvers`, unhandled rejections
- [ ] **async/await** — sugar over promises, sequential vs parallel awaits, error handling with try/catch, top-level await, `await` in loops (`for...of` vs `forEach` pitfall)
- [ ] **Cancellation** — `AbortController`/`AbortSignal` (`AbortSignal.timeout`, `AbortSignal.any`), aborting fetch, cancelling stale requests (race conditions in UIs)
- [ ] **Concurrency control** — limit parallel promises, retries with exponential backoff, timeouts via `Promise.race`
- [ ] Event loop interplay (§1.4)

### 4.3 Modules
- [ ] **ES Modules vs CommonJS** — static vs dynamic, live bindings vs copies, `import`/`export` forms, default vs named exports (prefer named), circular dependencies, `require` of ESM, dual packages
- [ ] **Dynamic `import()`** — code splitting
- [ ] Tree shaking requirements (static ESM, `sideEffects`)
- [ ] Import maps, `import.meta`, JSON modules/import attributes

### 4.4 DOM & Events
- [ ] DOM traversal & manipulation APIs, `DocumentFragment`, `textContent` vs `innerHTML` (XSS)
- [ ] **Events** — capturing vs bubbling vs target phases, `stopPropagation` vs `preventDefault`, **event delegation**, passive listeners (scroll perf), `once`, custom events, `composedPath` with Shadow DOM
- [ ] **Observers** — `IntersectionObserver` (lazy loading, infinite scroll), `ResizeObserver`, `MutationObserver`, `PerformanceObserver`
- [ ] `requestAnimationFrame`, `requestIdleCallback`
- [ ] **Storage** — `localStorage`/`sessionStorage` (sync, 5 MB, strings), cookies, IndexedDB (async, large), Cache Storage; quotas & eviction
- [ ] **Network APIs** — `fetch` (doesn't reject on HTTP errors!, `credentials`, `mode`, `keepalive`), streams (`ReadableStream`, response streaming), `XMLHttpRequest` (upload progress), `navigator.sendBeacon`, WebSocket, EventSource (SSE)

### 4.5 Memory & Performance in JS
- [ ] Garbage collection (mark-and-sweep, generational), reachability
- [ ] **Memory leaks** — forgotten event listeners, timers, detached DOM nodes, closures over large objects, global caches, unsubscribed observables/subscriptions
- [ ] Chrome DevTools Memory panel — heap snapshots, allocation timelines, comparing snapshots, retainers
- [ ] **Debounce vs throttle**, memoization, avoiding work on the main thread (Web Workers)

### 4.6 ECMAScript Versions (know what you use)
- [ ] ES2015 (classes, modules, arrow functions, let/const, promises, Map/Set, destructuring, generators) → ES2017 (async/await) → ES2018 (rest/spread objects, async iteration) → ES2019 (`flat`, `Object.fromEntries`) → ES2020 (`?.`, `??`, BigInt, `Promise.allSettled`, dynamic import) → ES2021 (logical assignment, `replaceAll`, `Promise.any`, WeakRef) → ES2022 (class fields & private methods, top-level await, `at`, `Error.cause`, `Object.hasOwn`) → ES2023 (`findLast`, `toSorted`/`toReversed`/`with`, hashbang) → ES2024 (`Object.groupBy`, `Promise.withResolvers`, `v` flag, resizable ArrayBuffer) → ES2025 (Iterator helpers, Set methods, `RegExp.escape`, import attributes, `Promise.try`, Float16Array)
- [ ] **Temporal API** (modern date/time) — shipping in browsers; why `Date` is broken; date-fns/Day.js/Luxon today
- [ ] **TC39 process** stages (0–4); notable proposals (decorators, signals, pipeline operator) — awareness

### 🎯 Frequently Asked
- Explain closures with a practical example; the classic loop/setTimeout puzzle
- How does `this` work? Arrow vs regular functions
- Prototypal inheritance — how does `new` work?
- Promise.all vs allSettled vs race vs any; implement Promise.all
- Event delegation — why and how?
- Debounce vs throttle — implement both
- How do you find and fix a memory leak in a SPA?
- ESM vs CommonJS

---

## 5. TypeScript (Deep) (P0)

### 5.1 Type System Fundamentals
- [ ] **Structural typing** (vs nominal), excess property checks on object literals
- [ ] **Type inference**, contextual typing, widening (`let` vs `const`), **literal types**, `as const`
- [ ] **Top & bottom types** — `any` (opt out) vs **`unknown`** (safe top type) vs **`never`** (bottom; exhaustiveness) vs `void` vs `undefined` vs `null`; `object` vs `Object` vs `{}`
- [ ] **Interfaces vs type aliases** — declaration merging, extends vs intersections, performance, when to use which
- [ ] **Unions & intersections**; **discriminated (tagged) unions** + exhaustive `switch` with `never` check (`assertNever`)
- [ ] **Type narrowing** — `typeof`, `instanceof`, `in`, equality, truthiness, discriminant checks, control-flow analysis, **user-defined type guards** (`x is T`), **assertion functions** (`asserts x is T`), inferred type predicates (TS 5.5)
- [ ] **Type assertions** (`as`), non-null assertion (`!`) — and why to minimize them
- [ ] **`satisfies` operator** — validate without widening
- [ ] **Optional properties** vs `| undefined` (`exactOptionalPropertyTypes`), readonly properties & `ReadonlyArray`, index signatures, `Record`
- [ ] **Tuples** — labeled, optional, variadic tuple types, `readonly` tuples
- [ ] **Enums** — numeric vs string enums, reverse mapping, `const enum` pitfalls (isolatedModules), and why **union of string literals / `as const` objects** are often preferred

### 5.2 Generics & Type-Level Programming (P0)
- [ ] **Generics** — functions, interfaces, classes; **constraints** (`T extends …`), defaults, inference from arguments, `const` type parameters (TS 5.0), `NoInfer<T>` (TS 5.4)
- [ ] **`keyof`**, **`typeof`** (type query), **indexed access types** (`T["key"]`, `T[number]`)
- [ ] **Mapped types** — `{ [K in keyof T]: … }`, modifiers (`readonly`, `?`, `-readonly`, `-?`), **key remapping with `as`**
- [ ] **Conditional types** — `T extends U ? X : Y`, **`infer`**, **distributive conditional types** (and how to disable with `[T]`)
- [ ] **Template literal types** — string manipulation types (`Uppercase`, `Capitalize`), typed event names/route params
- [ ] **Recursive types** — deep partial/readonly, JSON types, path types (`"a.b.c"`)
- [ ] **Built-in utility types** — `Partial`, `Required`, `Readonly`, `Pick`, `Omit`, `Record`, `Exclude`, `Extract`, `NonNullable`, `ReturnType`, `Parameters`, `ConstructorParameters`, `InstanceType`, `Awaited`, `ThisParameterType`, `NoInfer`
- [ ] **Implement utility types from scratch** (common interview task): `MyPick`, `MyOmit`, `DeepPartial`, `DeepReadonly`, `UnionToIntersection`, `TupleToUnion`, `First<T>`, `Last<T>`, `Awaited`, `PathValue`
- [ ] **Variance** — covariance/contravariance, method vs function property bivariance (`strictFunctionTypes`), variance annotations (`in`/`out`)
- [ ] **Branded/nominal types** (`type UserId = string & { __brand: "UserId" }`)
- [ ] **Function overloads**, `this` parameters, generic call signatures, construct signatures
- [ ] **Type-challenges** practice (easy/medium level)

### 5.3 Classes, Modules & Declarations
- [ ] Access modifiers (`public`/`private`/`protected`) vs JS `#private`, `readonly`, parameter properties, abstract classes, `implements`, `override` keyword
- [ ] **Decorators** — TC39 stage 3 decorators (TS 5.0) vs legacy `experimentalDecorators` (Angular/NestJS)
- [ ] **Declaration files (`.d.ts`)** — ambient declarations, `declare module`, **module augmentation** (extending library types, e.g., theme types), global augmentation, triple-slash directives, DefinitelyTyped (`@types/*`), shipping types in libraries (`types`/`exports` conditions)
- [ ] **Namespaces** (legacy) vs modules

### 5.4 tsconfig & Compiler (P0)
- [ ] **`strict`** family — `strictNullChecks`, `noImplicitAny`, `strictFunctionTypes`, `strictBindCallApply`, `useUnknownInCatchVariables`…
- [ ] Extra safety — **`noUncheckedIndexedAccess`**, `exactOptionalPropertyTypes`, `noImplicitOverride`, `noFallthroughCasesInSwitch`, `noPropertyAccessFromIndexSignature`
- [ ] **Module settings** — `module` & `moduleResolution` (`bundler` vs `NodeNext`/`node16`), `target`, `lib`, `jsx` (`react-jsx`), `esModuleInterop`, `allowJs`/`checkJs`, `resolveJsonModule`
- [ ] **`isolatedModules`**, **`verbatimModuleSyntax`** (`import type`), `erasableSyntaxOnly` (for Node's native type stripping)
- [ ] `paths`/`baseUrl` aliases, **project references** & `composite` for monorepos, `incremental`, `skipLibCheck`, `declaration`/`declarationMap`, `noEmit` with bundlers
- [ ] **Type-checking vs transpiling** — Babel/SWC/esbuild strip types (no type checking) → run `tsc --noEmit` in CI
- [ ] **Performance** — slow type checking diagnosis (`--extendedDiagnostics`, `--generateTrace`), avoiding huge unions/deep recursion, interfaces over intersections
- [ ] **TypeScript 5.x highlights** & the **native Go port (TypeScript 7 / `tsgo`)** for ~10× faster builds — awareness
- [ ] **Running TS natively** — Node.js type stripping, Deno, Bun, `tsx`

### 5.5 TypeScript in Practice
- [ ] **Runtime validation at boundaries** — types vanish at runtime; validate API responses/forms/env with **Zod** (v4), Valibot, ArkType, Yup; infer TS types from schemas (`z.infer`)
- [ ] **End-to-end type safety** — tRPC, OpenAPI → TS codegen (openapi-typescript, orval), GraphQL Codegen, shared types in monorepos, Prisma/Drizzle generated types
- [ ] **Migrating JS → TS** incrementally — `allowJs`, JSDoc types, `// @ts-check`, strictness ratchet, `@ts-expect-error` over `@ts-ignore`
- [ ] **Typing third-party JS**, writing `.d.ts` for untyped modules
- [ ] **Error handling types** — `unknown` in catch, Result/Either patterns, typed errors
- [ ] **Linting** — typescript-eslint (type-aware rules: `no-floating-promises`, `no-misused-promises`, `strict-boolean-expressions`)

### 🎯 Frequently Asked
- `any` vs `unknown` vs `never`; `interface` vs `type`
- Explain discriminated unions and exhaustive checking
- Implement `Pick`, `Omit`, `DeepPartial`, `ReturnType` yourself
- What does `infer` do? Explain distributive conditional types
- `satisfies` vs type annotation vs `as`
- How do you guarantee type safety for API responses at runtime?
- Which tsconfig flags do you enable on a new project and why?

---

# PART B — REACT

## 6. React Fundamentals & Rendering Model (P0)

- [ ] **JSX** — transform (`react/jsx-runtime`), expressions, elements are plain objects, `key`, fragments, conditional rendering patterns (`&&` with `0` gotcha), lists
- [ ] **Elements vs components vs instances**; function components (class components legacy — know lifecycle mapping: `componentDidMount`/`DidUpdate`/`WillUnmount` ↔ effects, `shouldComponentUpdate` ↔ `memo`, `getDerivedStateFromError`/`componentDidCatch` for error boundaries)
- [ ] **Props vs state**, one-way data flow, lifting state up, derived state (compute during render — don't sync into state)
- [ ] **Render vs commit phases** — rendering = calling components (must be pure, no side effects), commit = applying DOM changes, then effects run
- [ ] **What triggers a re-render** — state update, parent re-render, context value change (props changing is *not* itself the trigger)
- [ ] **Reconciliation & diffing heuristics** — different element type → remount; same type → update; **keys** for lists (why index keys break state/inputs; using `key` to reset component state)
- [ ] **Virtual DOM** — what it is, what it isn't (not inherently "faster than DOM")
- [ ] **Fiber architecture** — units of work, interruptible rendering, double buffering (current vs work-in-progress tree), **lanes**/priorities, scheduler
- [ ] **Batching** — automatic batching in React 18 (including promises/timeouts), `flushSync`
- [ ] **State as a snapshot** — state values are fixed per render; updater functions (`setCount(c => c + 1)`); queueing multiple updates
- [ ] **Controlled vs uncontrolled** components (inputs, and the general pattern)
- [ ] **Composition** — `children`, slots via props, component injection, composition over inheritance
- [ ] **Portals** (modals, tooltips — event bubbling follows React tree)
- [ ] **Error boundaries** — what they catch (render errors) and don't (event handlers, async, SSR), `react-error-boundary`, recovery/reset strategies
- [ ] **StrictMode** — double-invoking renders & effects in dev to surface impurity and missing cleanups
- [ ] **Suspense** — for code splitting (`lazy`), data fetching (framework/`use`), streaming SSR; fallback boundaries placement
- [ ] **Synthetic events** — event delegation at root, event pooling removed (17+), differences from native events
- [ ] **Refs** — DOM access, mutable instance values, callback refs, ref cleanup functions (React 19)

---

## 7. Hooks (Deep) (P0)

- [ ] **Rules of hooks** & why — hooks stored as an ordered list on the fiber; ESLint `react-hooks` plugin
- [ ] **`useState`** — lazy initializer, functional updates, object/array immutability, batching, bail-out on `Object.is` equality
- [ ] **`useReducer`** — when over `useState` (complex transitions, related state), reducer purity, typing actions as discriminated unions, dispatch stability
- [ ] **`useEffect`** — synchronizing with *external* systems; dependency array semantics; **cleanup** (subscriptions, timers, abort fetches); runs after paint; **race conditions** in data fetching (ignore flag / AbortController); effects running twice in StrictMode
- [ ] **"You Might Not Need an Effect"** — derive during render, handle in event handlers, `key` to reset state, avoid chains of effects, don't fetch in effects when a framework/query library is available
- [ ] **`useLayoutEffect`** (measure DOM before paint, avoid flicker; SSR warnings) vs **`useInsertionEffect`** (CSS-in-JS libs)
- [ ] **`useRef`** — DOM refs, mutable values that don't trigger re-renders, storing previous values, avoiding stale closures, ref as prop (React 19, `forwardRef` no longer needed)
- [ ] **`useMemo` / `useCallback`** — referential equality for memoized children/effect deps, expensive calculations; when they're wasted; **React Compiler** makes most manual memoization unnecessary
- [ ] **`useContext`** — every consumer re-renders on value change; memoizing provider values; splitting contexts (state vs dispatch); context is not a state manager
- [ ] **`useId`** (SSR-safe IDs for a11y), **`useImperativeHandle`**, **`useDebugValue`**
- [ ] **`useSyncExternalStore`** — subscribing to external stores safely in concurrent rendering (tearing); basis of Redux/Zustand bindings
- [ ] **`useTransition`** & **`useDeferredValue`** — non-urgent updates, keeping UI responsive
- [ ] **React 19 hooks** — **`use()`** (read promises & context, conditionally), **`useActionState`**, **`useFormStatus`**, **`useOptimistic`**; **`useEffectEvent`** (19.2 — non-reactive logic inside effects)
- [ ] **Stale closures** — causes & fixes (functional updates, refs, correct deps, `useEffectEvent`)
- [ ] **Custom hooks** — extracting reusable stateful logic, naming, returning tuples vs objects, composing hooks, testing with `renderHook`; examples: `useDebounce`, `useFetch`, `useLocalStorage`, `usePrevious`, `useIntersectionObserver`, `useMediaQuery`, `useEventListener`, `useInterval`, `useOnClickOutside`
- [ ] **React Compiler (1.0)** — automatic memoization at build time, requirements (pure components, rules of React), opting out, impact on `memo`/`useMemo`/`useCallback` advice

### 🎯 Frequently Asked
- Why can't hooks be called conditionally?
- `useEffect` vs `useLayoutEffect`; when does each run?
- How do you avoid race conditions when fetching in an effect?
- When are `useMemo`/`useCallback` actually useful? What does React Compiler change?
- What's a stale closure? Show a bug and the fix
- Build `useDebounce`, `usePrevious`, `useFetch` with cancellation

---

## 8. React Performance (P0)

- [ ] **Measure first** — React DevTools Profiler (flamegraph, "why did this render"), Chrome Performance panel, `<Profiler>` API, why-did-you-render
- [ ] **Avoiding unnecessary renders** — state colocation (move state down), lift content up (`children` as props trick), split components, `React.memo` with stable props, memoized context values, splitting contexts, context selectors (use-context-selector) or external stores with selectors
- [ ] **Expensive renders** — `useMemo`, moving work out of render, Web Workers for heavy computation
- [ ] **Large lists** — **virtualization/windowing** (TanStack Virtual, react-window, react-virtuoso), pagination, infinite scroll
- [ ] **Code splitting** — `React.lazy` + `Suspense`, route-based splitting, component-level splitting, prefetching on hover/viewport
- [ ] **Concurrent rendering** — `useTransition`/`useDeferredValue` for responsive input on heavy updates
- [ ] **Bundle size** — tree shaking, avoiding heavy deps (moment → date-fns), analyzing bundles, dynamic imports
- [ ] **Hydration cost** — less client JS via Server Components, partial/selective hydration, islands
- [ ] **Images & assets** — responsive images, lazy loading, `next/image`
- [ ] **Effects performance** — avoid layout thrashing in `useLayoutEffect`, debounce resize/scroll handlers, passive listeners
- [ ] **Keys & reconciliation** — stable keys; avoid remounting large subtrees
- [ ] **State management impact** — selector-based subscriptions (Redux/Zustand), normalized state, avoiding global re-renders
- [ ] **Memory leaks in React** — missing effect cleanups, subscriptions, intervals, stale references in closures

### 🎯 Frequently Asked
- A page with a 10,000-row table is slow to type into — how do you fix it?
- How do you find out why a component re-renders?
- Context causes the whole app to re-render — what are your options?

---

## 9. React 18/19, Concurrent Features & Server Components (P0)

### 9.1 Concurrent React (18)
- [ ] `createRoot`, automatic batching, transitions (`startTransition`), `useDeferredValue`, Suspense improvements, `useId`, `useSyncExternalStore`, streaming SSR with `renderToPipeableStream`/`renderToReadableStream`, selective hydration
- [ ] **Interruptible rendering** and why components must be pure; tearing with external stores

### 9.2 React 19 / 19.x
- [ ] **Actions** — async functions in transitions, pending states, error handling, optimistic updates
- [ ] **Form actions** — `<form action={fn}>`, `useActionState`, `useFormStatus`, `useOptimistic`
- [ ] **`use()`** API; **ref as a prop**; ref cleanup functions; `<Context>` as provider
- [ ] **Document metadata** (`<title>`, `<meta>`, `<link>` rendered anywhere and hoisted), stylesheet precedence, async scripts, **resource preloading APIs** (`preload`, `preinit`, `prefetchDNS`, `preconnect`)
- [ ] Better hydration error messages; custom elements support
- [ ] **19.2** — `<Activity>` (hide/show UI while preserving state, pre-rendering), `useEffectEvent`, partial pre-rendering primitives, Performance Tracks in DevTools
- [ ] Removed/deprecated APIs — `propTypes`, `defaultProps` on function components, string refs, legacy context, `ReactDOM.render`; migration path

### 9.3 React Server Components (RSC) (P0)
- [ ] **Mental model** — Server Components render on the server (or at build time), send a serialized tree (RSC payload) to the client; **zero client JS** for server components; Client Components hydrate
- [ ] **`'use client'` boundary** — marks the entry into client code; everything imported below becomes client code; pass Server Components as `children`/props to Client Components
- [ ] **`'use server'`** — **Server Functions/Actions**, callable from the client; they are **public HTTP endpoints** (validate input, authorize!)
- [ ] **Serialization constraints** — props crossing the boundary must be serializable (no functions except server actions, no class instances)
- [ ] **Data fetching in RSC** — async components, direct DB/service access, avoiding waterfalls (parallel fetching, preload pattern), caching/dedup (`cache()`)
- [ ] **What can't be in RSC** — state, effects, browser APIs, event handlers, context consumers
- [ ] **Streaming with Suspense** — progressive rendering, loading states
- [ ] **Trade-offs** — infra complexity, framework coupling, caching complexity, mental overhead, debugging; when a SPA is still the right answer
- [ ] **Security incidents & hygiene** — server-only modules (`server-only` package), not leaking secrets to client bundles, taint APIs; keep React/Next patched (critical RSC vulnerabilities were disclosed in late 2025)

### 🎯 Frequently Asked
- Explain Server Components vs Client Components vs SSR — how are they different?
- What can and can't you do in a Server Component?
- How do Server Actions work and what are their security implications?
- What problems do transitions solve?

---

## 10. State Management (P0)

- [ ] **Classify state first** — local UI state, shared/global client state, **server state (cache)**, **URL state**, form state, derived state; most "global state" is actually server state
- [ ] **Built-ins** — `useState`, `useReducer`, Context (+ reducer), lifting state, composition
- [ ] **Redux Toolkit** (P0 for enterprise) — store, slices (`createSlice`), Immer-powered immutable updates, `createAsyncThunk`, middleware, **RTK Query** (server state, caching, invalidation tags), `createEntityAdapter` (normalization), memoized selectors (`createSelector`/Reselect), Redux DevTools, when Redux is overkill; legacy Redux (connect, sagas, thunks) for migrations
- [ ] **Zustand** — minimal store, selectors to limit re-renders, middleware (persist, devtools, immer), slices pattern, outside-React access
- [ ] **Jotai** (atomic), **Valtio** (proxy), **MobX** (observables/reactivity), **XState** (state machines & statecharts for complex flows — wizards, checkout, media players), **Recoil** (archived — migration awareness)
- [ ] **Signals** — Preact Signals, Solid/Angular/Vue reactivity, TC39 signals proposal; fine-grained reactivity vs React's re-render model
- [ ] **URL as state** — search params for filters/pagination/sorting (shareable, back-button friendly), `nuqs`, router APIs
- [ ] **Persistence** — localStorage/IndexedDB, hydration mismatches with persisted state, versioning/migrations of persisted state
- [ ] **Choosing** — decision matrix by team size, app complexity, server-state share, devtools, performance, learning curve

### 🎯 Frequently Asked
- How do you decide where state lives?
- Redux vs Zustand vs Context vs React Query — when each?
- Why is "server state" different from client state?

---

## 11. Data Fetching & Server State (P0)

- [ ] **Fetching approaches** — effects (and their problems), framework loaders (React Router, Next.js RSC), query libraries, Suspense-enabled fetching
- [ ] **TanStack Query** (P0) — query keys (structure & factories), `staleTime` vs `gcTime`, background refetching (focus/reconnect/interval), deduplication, retries, dependent & parallel queries, pagination & **infinite queries**, **mutations** & invalidation, **optimistic updates** with rollback, prefetching (hover, SSR/hydration), `select` for derived data, suspense mode, offline/persisters, DevTools
- [ ] **SWR** — stale-while-revalidate model
- [ ] **GraphQL clients** — Apollo Client (normalized cache, type policies, fragments, cache updates after mutations), urql, Relay (fragments colocation, compiler); GraphQL Codegen for types
- [ ] **tRPC** — end-to-end typed APIs in TS monorepos
- [ ] **Waterfalls** — detecting & eliminating (parallelize, hoist fetching to routes/loaders, prefetch, RSC)
- [ ] **Race conditions** — out-of-order responses, aborting stale requests, request IDs
- [ ] **Error & loading UX** — skeletons vs spinners, error boundaries, retry UI, empty states, partial failure handling
- [ ] **Caching layers** — HTTP cache, CDN, client query cache, service worker cache; invalidation strategies
- [ ] **Real-time** — WebSockets/SSE integration with query caches (patching cache on events), polling fallbacks, reconnection with backoff
- [ ] **Pagination patterns** — offset vs cursor, infinite scroll vs "load more" vs numbered pages (a11y & SEO trade-offs)
- [ ] **API layer design** — typed client, interceptors (auth refresh, error normalization), retries with backoff, request cancellation, mocking (MSW)

---

## 12. Forms (P1)

- [ ] Controlled vs uncontrolled inputs; performance of controlled forms with many fields
- [ ] **React Hook Form** — `register`, `Controller` for UI-library inputs, `useFieldArray`, validation modes, resolvers (**Zod**), `formState` subscriptions, performance via uncontrolled inputs
- [ ] Formik (legacy), TanStack Form, Conform (progressive enhancement), React 19 form actions
- [ ] **Validation strategy** — client vs server validation (server is the authority), shared schemas, async validation (username availability with debounce), error display timing
- [ ] **Accessible forms** — labels, `aria-describedby` for errors, `aria-invalid`, focus first error on submit, error summaries, required indicators
- [ ] Multi-step wizards (state machines), autosave drafts, dirty-state & unsaved changes warnings, file uploads (progress, chunking, drag & drop, pre-signed URLs), date pickers & masks, i18n of validation messages

---

## 13. Routing (P1)

- [ ] **Client-side routing** fundamentals — History API, route matching, nested routes, layouts, dynamic segments, query params, 404s, scroll restoration, focus management on navigation (a11y)
- [ ] **React Router v7** — library vs **framework mode** (Remix merged in): loaders, actions, `fetcher`, nested routes with `Outlet`, pending UI, error elements, type-safe route modules, SSR/SSG support
- [ ] **TanStack Router** — fully type-safe routes & search params, loaders, caching
- [ ] **Next.js App Router** — file-system routing, `layout`/`page`/`loading`/`error`/`not-found`/`template`, route groups `(group)`, dynamic `[slug]`, catch-all, **parallel routes** (`@slot`) & **intercepting routes** (modals), route handlers
- [ ] **Patterns** — protected routes & auth redirects, role-based routes, route-based code splitting, prefetching links, breadcrumbs, preserving state across navigation, deep linking, URL design

---

## 14. Meta-Frameworks & Rendering Strategies (P0)

### 14.1 Rendering Strategies
- [ ] **CSR** (SPA), **SSR**, **SSG**, **ISR** (incremental static regeneration), **streaming SSR**, **Partial Prerendering** (static shell + dynamic holes), **islands architecture**, **edge rendering**, **RSC**
- [ ] **Trade-offs** — TTFB, LCP, SEO, interactivity (hydration cost), server cost, caching, personalization, complexity
- [ ] **Hydration** — what it is, hydration mismatches (dates, random, `window` checks) and fixes, progressive/selective hydration, resumability (Qwik) as contrast
- [ ] **SEO for SPAs** — SSR/SSG, metadata, sitemaps, canonical URLs, structured data, Core Web Vitals as ranking signal

### 14.2 Next.js (P0 for React roles)
- [ ] **App Router vs Pages Router** — `getServerSideProps`/`getStaticProps` (legacy) vs RSC async components
- [ ] **Server Components by default**, Client Components with `'use client'`, Server Actions
- [ ] **Caching model** — request memoization, data cache, full route cache, router cache; revalidation (`revalidatePath`, `revalidateTag`, time-based); the evolution in Next 15/16 toward explicit caching (`'use cache'`, Cache Components, `cacheLife`/`cacheTag`), dynamic APIs (`cookies()`, `headers()`) opting into dynamic rendering
- [ ] **Static vs dynamic rendering**, `generateStaticParams`, Partial Prerendering
- [ ] **Middleware** (renamed `proxy` in Next 16) — auth checks, redirects, geolocation, A/B testing at the edge; runtime limits
- [ ] **Route handlers** (API endpoints), streaming responses
- [ ] **Optimizations** — `next/image`, `next/font`, `next/script`, `next/link` prefetching, Metadata API, bundle analysis
- [ ] **Turbopack** (default bundler in recent versions), React Compiler support
- [ ] **Runtimes** — Node.js vs Edge
- [ ] **Deployment** — Vercel vs self-hosting (Docker, standalone output, OpenNext for AWS/Cloudflare), CDN caching, ISR storage on self-host
- [ ] **Auth** in Next.js — Auth.js/NextAuth, Clerk, Better Auth, middleware-based protection pitfalls (also check auth at data access layer)

### 14.3 Other Frameworks (P1/P2)
- [ ] **React Router 7 framework mode / Remix** — web-fundamentals, loaders/actions, progressive enhancement
- [ ] **TanStack Start**, **Astro** (islands, content sites, multiple framework support), **Gatsby** (legacy), **Vite SPA** templates
- [ ] **Other UI frameworks** (be able to compare) — **Vue 3** (Composition API, reactivity via proxies, Nuxt), **Angular** (signals, standalone components, DI, RxJS, zoneless), **Svelte 5** (runes, compiler), **SolidJS** (fine-grained signals), **Qwik** (resumability), **Preact**, **Lit/Web Components**, htmx (hypermedia)

---

## 15. Styling & Design Systems (P0)

- [ ] **Styling approaches in React** — global CSS, CSS Modules, Sass, Tailwind, runtime CSS-in-JS (styled-components/Emotion — maintenance mode concerns & RSC incompatibility), zero-runtime CSS-in-JS (vanilla-extract, Panda, StyleX), inline styles; trade-offs for performance, DX, theming, SSR
- [ ] **Component libraries** — MUI, Ant Design, Chakra UI, Mantine, Fluent UI; **headless/unstyled** — Radix UI, React Aria (Adobe), Headless UI, Ark UI, Base UI; **shadcn/ui** (copy-paste components on Radix + Tailwind)
- [ ] **Design systems** (P0 for leads)
  - [ ] Tokens (color, spacing, typography, radii, shadows, motion), theming (dark mode, brands, multi-tenant white-labeling), CSS variables
  - [ ] Component API design — consistent props, variants (`cva`), composition (slots, compound components), polymorphism (`as`/`asChild`), controlled/uncontrolled support, forwarding refs & props, accessibility built in
  - [ ] **Storybook** — stories, controls, docs, interaction tests, visual regression (Chromatic), a11y addon
  - [ ] Distribution — versioning (semver, changesets), publishing (npm private registry), tree-shakeable builds, peer dependencies, breaking-change policies & codemods
  - [ ] Governance — contribution model, adoption metrics, design–engineering collaboration (Figma variables → tokens, Figma Dev Mode/Code Connect)
  - [ ] Documentation & usage guidelines
- [ ] **Icons & assets** — SVG components, sprite sheets, icon libraries (lucide), image CDNs
- [ ] **Animations in React** — CSS transitions, Framer Motion (Motion), React Spring, View Transitions API integration, reduced motion

---

## 16. Component Architecture & Patterns (P0)

- [ ] **Component design principles** — single responsibility, composition over configuration, minimal props, avoiding prop drilling (composition first, then context), colocation, pure presentational vs stateful containers (historical pattern — hooks changed it)
- [ ] **Advanced patterns**
  - [ ] **Compound components** (Tabs/Tab/TabPanel sharing implicit state via context)
  - [ ] **Render props** & **function as children**
  - [ ] **Higher-Order Components** (legacy; cross-cutting concerns; why hooks replaced most)
  - [ ] **Custom hooks** as the primary logic-reuse mechanism
  - [ ] **Controlled/uncontrolled hybrid props** (`value`/`defaultValue`/`onChange`) — `useControllableState`
  - [ ] **Prop getters** & **state reducer pattern** (Downshift style inversion of control)
  - [ ] **Headless components** (logic without UI), **slots**, **polymorphic components** (`as` prop, `asChild`)
  - [ ] **Provider pattern**, dependency injection via context
  - [ ] **Container/presenter with hooks**, **feature components**
- [ ] **Project structure** — feature-based (vertical slices) vs type-based folders, `features/` + `shared/` + `app/`, **Feature-Sliced Design**, module boundaries enforced by lint rules (eslint-plugin-boundaries), barrel files pitfalls (tree shaking & circular deps, slow tooling)
- [ ] **Separation of concerns** — UI vs domain logic vs data access; keeping business logic out of components; testing seams
- [ ] **Error handling architecture** — boundaries at route/feature level, toast vs inline errors, logging to Sentry
- [ ] **Loading architecture** — Suspense boundaries placement, skeletons, avoiding layout shift

---

## 17. TypeScript with React (P0)

- [ ] **Typing props** — `type Props = {...}`, optional/default props, `children: React.ReactNode`, `PropsWithChildren`, avoiding `React.FC` debates (know the history), `ComponentProps<'button'>`/`ComponentPropsWithoutRef` to extend native elements, `Omit` to override
- [ ] **Events** — `React.ChangeEvent<HTMLInputElement>`, `MouseEvent`, `FormEvent`, `KeyboardEvent`, typed handlers
- [ ] **Hooks typing** — `useState<User | null>(null)`, `useRef<HTMLDivElement>(null)` (React 19 ref typing changes), `useReducer` with discriminated union actions, typed context with non-null guard hook (`useXContext` throwing outside provider)
- [ ] **Generic components** — `<Table<Row>>`, `<Select<T>>` with inference
- [ ] **Polymorphic components** — typing `as` prop correctly
- [ ] **Discriminated union props** — mutually exclusive props (`variant: 'link'` requires `href`)
- [ ] **Refs** — `forwardRef` generics (legacy) vs ref-as-prop in React 19
- [ ] **Typing HOCs & render props**
- [ ] **Typing API data** — generated types (OpenAPI/GraphQL), Zod-inferred types, never trusting `as` on fetch results
- [ ] **Typing state libraries** — Redux Toolkit (`RootState`, `AppDispatch`, typed hooks), Zustand stores, TanStack Query generics
- [ ] **Typing env vars, CSS modules, SVG imports** (declaration files)

---

# PART C — ENGINEERING QUALITY

## 18. Build Tooling, Package Management & Monorepos (P0)

### 18.1 Package Management
- [ ] **npm vs Yarn (classic/Berry PnP) vs pnpm** (content-addressable store, strict `node_modules`, no phantom dependencies) vs Bun
- [ ] **Lockfiles** — why commit them, `npm ci`, deterministic installs, lockfile conflicts
- [ ] **Semver ranges** (`^`, `~`), dependencies vs devDependencies vs **peerDependencies** (libraries & design systems), optionalDependencies, `overrides`/`resolutions`
- [ ] **`package.json` fields** — `type: "module"`, **`exports`** (conditional exports: import/require/types/browser), `main`/`module`, `sideEffects`, `files`, `engines`, `scripts`
- [ ] **Publishing libraries** — dual ESM/CJS builds (tsup, unbuild), type declarations, `publint`/`are-the-types-wrong`, provenance (`npm publish --provenance`), private registries
- [ ] **Dependency hygiene** — audit, Dependabot/Renovate, bundle impact (bundlephobia), license compliance, removing unused deps (knip, depcheck)
- [ ] **Supply-chain risks** — typosquatting, compromised maintainers, malicious `postinstall` scripts, self-propagating npm worms (2025 incidents), mitigations (pinning, lockfiles, `ignore-scripts`, minimum release age policies, provenance, scoped registries)

### 18.2 Bundlers & Compilers (P0)
- [ ] **Why bundle** — module resolution, transpilation, minification, code splitting, asset handling, tree shaking
- [ ] **Vite** — native ESM dev server, esbuild pre-bundling, Rollup → **Rolldown** (Rust) for builds, plugins, env vars (`import.meta.env`), library mode, SSR mode
- [ ] **webpack** — entry/output, loaders vs plugins, chunks & `SplitChunksPlugin`, dynamic imports, **Module Federation** (micro-frontends), caching, dev server/HMR, why it's slower; migrations webpack → Vite/Rspack
- [ ] **Rspack** (Rust webpack-compatible), **Turbopack** (Next.js), **esbuild**, **Rollup**, **Parcel**, **Bun bundler**
- [ ] **Transpilers** — Babel (presets, plugins, polyfills with core-js), **SWC**, esbuild, TypeScript `tsc`; browserslist targets; differential serving (legacy)
- [ ] **Minification** (Terser, esbuild, SWC), **source maps** (types, uploading to Sentry, not exposing in prod)
- [ ] **Tree shaking** requirements — ESM, `sideEffects: false`, avoiding barrel re-exports, pure annotations
- [ ] **Code splitting** strategies — route-level, vendor chunks, shared chunks, preloading
- [ ] **HMR & Fast Refresh** — how they preserve state
- [ ] **Asset handling** — images, fonts, SVG as components, CSS extraction, content hashing
- [ ] **Bundle analysis** — webpack-bundle-analyzer, rollup-plugin-visualizer, source-map-explorer; performance budgets in CI

### 18.3 Code Quality Tooling
- [ ] **ESLint** (flat config), typescript-eslint (type-aware rules), `eslint-plugin-react-hooks`, `jsx-a11y`, `import`/`import-x`, React Compiler lint rules
- [ ] **Prettier**; **Biome** (Rust lint+format); **Oxc/oxlint** (very fast linting)
- [ ] **Husky + lint-staged**, commitlint, conventional commits
- [ ] **Type checking in CI** (`tsc --noEmit`, project references)
- [ ] **Dead code detection** — knip, ts-prune

### 18.4 Monorepos (P1)
- [ ] **Tools** — pnpm/Yarn/npm workspaces, **Turborepo** (task pipelines, remote caching), **Nx** (project graph, affected commands, generators, module boundary rules), Lerna (legacy), Rush, Bazel
- [ ] **Patterns** — shared UI/design system packages, shared config packages (eslint/tsconfig), internal packages (source vs built), versioning with **Changesets**, affected-only CI, ownership (CODEOWNERS)
- [ ] **Monorepo vs polyrepo** trade-offs

---

## 19. Testing (P0)

### 19.1 Strategy
- [ ] **Testing trophy** (static → unit → integration → E2E; most value in integration) vs pyramid
- [ ] Test **user behavior, not implementation details**; confidence vs cost; what not to test
- [ ] **Coverage** and its limits; mutation testing (Stryker)
- [ ] Flaky test causes (timing, animations, network, shared state, test order) & fixes

### 19.2 Unit & Component Testing
- [ ] **Vitest** (Vite-native, Jest-compatible) vs **Jest** — config, `jsdom`/`happy-dom` environments, mocking modules (`vi.mock`/`jest.mock`), spies, **fake timers**, snapshot testing (and why to use sparingly), watch mode
- [ ] **React Testing Library** — guiding principles, **query priority** (`getByRole` > `getByLabelText` > `getByText` > … > `getByTestId`), `getBy` vs `queryBy` vs `findBy`, **`user-event`** over `fireEvent`, `waitFor`, `screen`, `within`, testing async UI, `renderHook`, wrappers for providers (router, query client, store)
- [ ] **API mocking with MSW** (Mock Service Worker) — shared handlers for tests, Storybook and local dev
- [ ] Testing custom hooks, reducers, context, forms, error boundaries, Suspense, Server Components (limited unit-testing support — prefer E2E/integration)
- [ ] **Vitest Browser Mode** / Playwright component testing / Cypress component testing — real-browser component tests

### 19.3 End-to-End
- [ ] **Playwright** (P0) — auto-waiting, locators (role-based), fixtures, parallelism & sharding, trace viewer, network interception, auth state reuse, multiple browsers, visual comparisons, API testing, codegen
- [ ] **Cypress** — architecture (in-browser), commands, intercepts, component testing; Playwright vs Cypress trade-offs
- [ ] **E2E strategy** — critical user journeys only, test data management, environments, running against preview deployments, flakiness control

### 19.4 Other Testing
- [ ] **Visual regression** — Chromatic, Percy, Playwright screenshots, Storybook test runner
- [ ] **Accessibility testing** — axe-core (`jest-axe`, `@axe-core/playwright`), Storybook a11y addon, manual screen-reader testing
- [ ] **Performance testing** — Lighthouse CI, WebPageTest, performance budgets, bundle size checks (size-limit)
- [ ] **Contract testing** — Pact, schema validation against OpenAPI
- [ ] **Cross-browser/device** — BrowserStack/Sauce Labs, real device testing
- [ ] **Testing in production** — feature flags, canaries, synthetic monitoring

### 🎯 Frequently Asked
- What's your frontend testing strategy for a large app?
- Why prefer `getByRole`? Why avoid testing implementation details?
- How do you test a component that fetches data?
- Playwright vs Cypress — which and why?

---

## 20. Web Performance & Core Web Vitals (P0)

### 20.1 Metrics
- [ ] **Core Web Vitals** — **LCP** (Largest Contentful Paint, good ≤ 2.5 s), **INP** (Interaction to Next Paint, good ≤ 200 ms — replaced FID in March 2024), **CLS** (Cumulative Layout Shift, good ≤ 0.1); measured at the 75th percentile
- [ ] Other metrics — TTFB, FCP, TBT (lab proxy for INP), Speed Index, TTI (deprecated), long animation frames (LoAF)
- [ ] **Lab vs field data** — Lighthouse/WebPageTest vs CrUX/RUM; `web-vitals` library; attribution builds to find culprits
- [ ] **RUM** — collecting vitals by route/device/country, segmenting, regression alerts

### 20.2 Optimization Playbook
- [ ] **LCP** — fast TTFB (CDN, caching, SSR/SSG, edge), preload/`fetchpriority="high"` LCP image, no lazy-loading the LCP image, optimized images (AVIF/WebP, responsive sizes, image CDN), eliminate render-blocking resources, inline critical CSS, font loading strategy, avoid client-side-only rendering of hero content
- [ ] **INP** — break up long tasks (`scheduler.yield`), reduce JS execution, defer non-critical work, avoid large re-renders on input (transitions, memoization, virtualization), debounce expensive handlers, Web Workers, minimize hydration cost, avoid layout thrashing, third-party script control
- [ ] **CLS** — image/video dimensions & `aspect-ratio`, reserve space for ads/embeds/dynamic content, font metric overrides & `font-display`, avoid inserting content above existing content, transform-based animations
- [ ] **JavaScript** — bundle size budgets, code splitting, tree shaking, removing polyfills for modern targets, lazy-loading below-the-fold components, Server Components to ship less JS, partial hydration
- [ ] **Network** — HTTP/2/3, Brotli, CDN, caching headers, preconnect, prefetch next routes, Speculation Rules (prerender), service worker caching, reducing request waterfalls, API response size
- [ ] **Third-party scripts** — audit, async/defer, facades (YouTube embeds), Partytown, tag managers governance
- [ ] **Rendering** — compositor-only animations, `content-visibility: auto`, CSS containment, virtualization, avoiding forced reflows
- [ ] **Memory** — leak detection, large DOM size, detached nodes
- [ ] **Perceived performance** — skeletons, optimistic UI, progressive loading, instant navigations with prefetch
- [ ] **Performance culture** — budgets in CI, dashboards, regression alerts, ownership

### 20.3 Tools
- [ ] Chrome DevTools — Performance panel (flame charts, long tasks, layout shifts, Performance insights), Network (waterfall, throttling), Coverage, Lighthouse, Memory, Rendering (paint flashing, layer borders)
- [ ] WebPageTest, PageSpeed Insights, CrUX dashboard, Search Console CWV report, React Profiler

### 🎯 Frequently Asked
- Explain LCP, INP and CLS and how you'd improve each
- Your INP is 500 ms on a product page — walk me through the investigation
- How do you reduce JavaScript bundle size in a large React app?
- How do you prevent performance regressions across 50 engineers?

---

## 21. Accessibility (P0)

- [ ] **Why** — users with disabilities, legal requirements (ADA, Section 508, **European Accessibility Act** enforced from June 2025, EN 301 549), SEO & UX benefits
- [ ] **WCAG 2.2** — POUR principles (Perceivable, Operable, Understandable, Robust), levels A/AA/AAA (target AA), new 2.2 criteria (focus not obscured, target size minimum, dragging alternatives, accessible authentication, consistent help); WCAG 3 in progress (awareness)
- [ ] **Semantic HTML first** — native elements (`button`, `a`, `input`, `label`, `nav`, headings) over `div`s with ARIA
- [ ] **ARIA** — first rule of ARIA (don't use it if native exists), roles, states & properties (`aria-expanded`, `aria-controls`, `aria-selected`, `aria-current`, `aria-hidden`, `aria-label`/`labelledby`/`describedby`, `aria-invalid`), **live regions** (`aria-live` polite/assertive, `role="status"`/`alert`), "no ARIA is better than bad ARIA"
- [ ] **Keyboard accessibility** — tab order, `tabindex` (0, -1; avoid positive), focus visibility (`:focus-visible`), keyboard traps, skip links, roving tabindex & arrow-key navigation in composite widgets
- [ ] **Focus management** — modals (focus trap, return focus on close, `inert` background), route changes in SPAs (move focus/announce), dynamically added content, error summaries
- [ ] **Accessible names** — labels for inputs, alt text (informative vs decorative `alt=""`), icon buttons with labels, link text that makes sense out of context
- [ ] **Visual** — color contrast (4.5:1 text, 3:1 large text & UI components), not relying on color alone, text resize/zoom to 200–400%, reflow, reduced motion, dark mode contrast
- [ ] **ARIA Authoring Practices (APG) patterns** — dialog, menu/menubar, tabs, combobox/autocomplete, listbox, disclosure/accordion, tooltip, tree view, grid, carousel, toast notifications
- [ ] **Forms a11y** — labels, grouping, error identification & suggestions, required fields, autocomplete attributes
- [ ] **Media** — captions, transcripts, audio descriptions, no autoplay with sound
- [ ] **Screen readers** — VoiceOver (macOS/iOS), NVDA/JAWS (Windows), TalkBack (Android); accessibility tree in DevTools
- [ ] **Testing** — automated (axe, Lighthouse, eslint-plugin-jsx-a11y) catches ~30–40%; manual keyboard & screen reader testing; user testing
- [ ] **Building a11y into the process** — design system components accessible by default, definition of done, audits, VPAT/ACR documents

### 🎯 Frequently Asked
- How do you build an accessible modal / dropdown / autocomplete?
- When should you use ARIA, and when not?
- How do you handle focus on route changes in an SPA?

---

## 22. Frontend Security (P0)

- [ ] **XSS** (stored, reflected, DOM-based) — React escapes by default; risks: `dangerouslySetInnerHTML`, `href`/`src` with `javascript:` URLs, injecting into `<script>`/JSON in SSR (`serialize-javascript`), third-party HTML, Markdown rendering, `eval`/`new Function`; **sanitize with DOMPurify**; **Trusted Types**
- [ ] **Content Security Policy** — `script-src` with nonces/hashes + `'strict-dynamic'`, avoiding `'unsafe-inline'`, `frame-ancestors`, report-only mode & reporting, CSP in Next.js (nonces via middleware)
- [ ] **CSRF** — cookie-based auth risk, SameSite cookies, CSRF tokens, Origin/Referer checks; Server Actions' built-in origin checks
- [ ] **Clickjacking** — `frame-ancestors`/`X-Frame-Options`
- [ ] **CORS** — misconfigurations (`*` with credentials, reflecting origin), it is not a security boundary for the server
- [ ] **Authentication in SPAs** — token storage (HttpOnly Secure SameSite cookies vs localStorage/XSS exposure vs in-memory + refresh), **OAuth 2.0 Authorization Code + PKCE**, OIDC, **BFF pattern** (tokens stay server-side), silent refresh, logout everywhere, session fixation, MFA/passkeys (WebAuthn)
- [ ] **Authorization** — never trust the client; hiding UI ≠ access control; server-side checks for every Server Action/route handler
- [ ] **Secrets** — nothing secret in client bundles (`NEXT_PUBLIC_` exposure), API keys restrictions, environment variable leaks
- [ ] **Third-party scripts & supply chain** — SRI (`integrity`), CSP allowlists, npm supply-chain attacks, lockfiles, audit, provenance
- [ ] **`postMessage`** — always validate `event.origin`; iframe `sandbox`
- [ ] **Prototype pollution**, **open redirects**, **SSRF** in SSR/image optimization endpoints, **ReDoS** in client validation
- [ ] **Security headers** — CSP, HSTS, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, COOP/COEP (cross-origin isolation)
- [ ] **Privacy** — cookies & consent (GDPR/ePrivacy), PII in analytics/logs/session replay, storage partitioning
- [ ] **OWASP Top 10** awareness for full-stack work

### 🎯 Frequently Asked
- Where should a SPA store auth tokens? Explain the trade-offs
- How does React protect against XSS and where can you still get burned?
- How would you implement CSP in a Next.js app?

---

## 23. Browser APIs, PWAs & Advanced Web (P1)

- [ ] **Web Workers** (offloading CPU work; Comlink), SharedWorker, **Service Workers** (lifecycle: install/activate/fetch; caching strategies: cache-first, network-first, stale-while-revalidate; Workbox; update flows; pitfalls of stale SW)
- [ ] **PWAs** — web app manifest, installability, offline support, background sync, push notifications (Push API + Notifications API), iOS limitations
- [ ] **Offline-first & local-first** — IndexedDB (idb, Dexie), sync engines, conflict resolution, CRDTs (Yjs, Automerge)
- [ ] **Real-time** — WebSockets (reconnection, heartbeats), SSE, WebRTC (peer-to-peer video/data), WebTransport (awareness)
- [ ] **Graphics** — Canvas 2D (performance for many objects), SVG (DOM-based), WebGL (three.js, react-three-fiber), WebGPU, OffscreenCanvas
- [ ] **WebAssembly** — use cases (image/video processing, heavy compute, porting C/C++/Rust), JS interop
- [ ] **Other APIs** — Clipboard, File System Access, Drag and Drop, Fullscreen, Geolocation, Page Visibility, Broadcast Channel, Navigation API, **View Transitions API**, Web Share, Credential Management, Web Locks, Intl, Performance APIs (User Timing, Resource Timing)
- [ ] **Cross-origin isolation** (COOP/COEP) for `SharedArrayBuffer`

---

## 24. Internationalization (P1)

- [ ] **Libraries** — react-intl/FormatJS (ICU MessageFormat), i18next/react-i18next, LinguiJS, next-intl
- [ ] **ICU messages** — plurals, select, gender, nested formatting; never concatenate translated strings
- [ ] **`Intl` APIs** — `NumberFormat` (currencies, units, compact), `DateTimeFormat`, `RelativeTimeFormat`, `PluralRules`, `ListFormat`, `Collator`, `Segmenter`, `DisplayNames`
- [ ] **RTL support** — `dir="rtl"`, logical CSS properties, mirroring icons
- [ ] **Locale strategy** — detection (Accept-Language, user setting), routing (`/en/…`, subdomains), SEO (hreflang), lazy-loading translation bundles, fallbacks
- [ ] **Translation workflow** — extraction, TMS (Crowdin, Lokalise, Phrase), pseudo-localization, string length expansion in layouts
- [ ] Time zones & date handling in UIs; currency & number input parsing

---

# PART D — ARCHITECTURE & SYSTEM DESIGN

## 25. Frontend Architecture at Scale (P0)

- [ ] **Scaling a codebase to 100+ engineers** — module boundaries, ownership (CODEOWNERS), shared libraries vs duplication, design system, conventions & linting, ADRs, dependency direction rules
- [ ] **Monolith SPA vs modular monolith vs micro-frontends**
- [ ] **Micro-frontends** (P1) — motivations (team autonomy, independent deploys, legacy migration), approaches (build-time packages, **Module Federation** runtime composition, single-spa, iframes, Web Components, server-side composition/edge includes), shared dependencies & singleton React, routing between MFEs, shared state/communication (events, URL), design consistency, performance costs, versioning; **when not to use them**
- [ ] **BFF (Backend for Frontend)** & API gateways; GraphQL federation as an aggregation layer
- [ ] **Data layer architecture** — API clients, caching strategy, normalization, real-time updates, offline support
- [ ] **Configuration & feature flags** — LaunchDarkly/Unleash/Statsig/GrowthBook/OpenFeature; flag lifecycle & cleanup; kill switches; server-evaluated vs client-evaluated flags
- [ ] **Experimentation** — A/B testing infrastructure, avoiding flicker (server-side assignment, edge), metrics & guardrails
- [ ] **Analytics & tracking** — event taxonomy/tracking plans, Segment/RudderStack, privacy & consent, performance impact
- [ ] **Multi-tenancy & white-labeling** — theming at runtime, tenant config, per-tenant feature sets
- [ ] **Large migrations** (have a story) — class components → hooks, JS → TS, CRA → Vite/Next, Pages Router → App Router, AngularJS/Backbone/jQuery → React (strangler pattern), Redux → TanStack Query/Zustand, CSS-in-JS → Tailwind/CSS Modules, design system v1 → v2 with codemods (jscodeshift, ts-morph)
- [ ] **Dependency & upgrade strategy** — React/Next major upgrades, Renovate, deprecations, codemods
- [ ] **Frontend observability** — error monitoring (Sentry: source maps, release health, breadcrumbs), RUM & Web Vitals, logging, session replay (privacy!), frontend tracing (OpenTelemetry web), synthetic monitoring
- [ ] **Release strategies** — immutable deploys, atomic deploys, preview environments per PR, canary/percentage rollouts, instant rollback, cache busting & stale clients (version skew between client and server; Next.js skew protection), forced refresh prompts
- [ ] **Architecture documentation** — C4 diagrams, ADRs, RFCs, tech radar

---

## 26. Frontend System Design (P0)

### 26.1 Framework (e.g., RADIO)
- [ ] **R — Requirements** — functional (core features, scope), non-functional (performance targets, devices/browsers, offline, a11y, i18n, SEO, security, scale of data)
- [ ] **A — Architecture** — component hierarchy, rendering strategy (CSR/SSR/SSG/RSC), client vs server responsibilities, state management placement, data flow diagram
- [ ] **D — Data model** — client-side entities, normalized store shape, server vs client state, caching
- [ ] **I — Interface (API)** — API endpoints/GraphQL schema, pagination (cursor), real-time protocol choice, component props APIs
- [ ] **O — Optimizations & deep dives** — performance (virtualization, lazy loading, prefetching, image strategy), network (batching, caching, retries, offline), UX (optimistic updates, loading/error/empty states), accessibility, i18n, security (XSS, auth), observability, testing
- [ ] Senior signals — trade-off articulation, user experience on bad networks/low-end devices, scale of data, edge cases, team/ownership considerations

### 26.2 Practice Problems
| # | Problem | Key deep dives |
|---|---------|----------------|
| 1 | [ ] **News feed (Facebook/Twitter)** | Infinite scroll, virtualization, cursor pagination, optimistic likes, real-time new posts, media lazy loading |
| 2 | [ ] **Autocomplete / Typeahead** | Debouncing, caching results, race conditions, keyboard navigation & a11y (combobox), highlighting |
| 3 | [ ] **Chat application (Messenger/Slack)** | WebSockets, message ordering, optimistic sends & retries, offline queue, read receipts, virtualized message list, unread counts |
| 4 | [ ] **Collaborative editor (Google Docs)** | OT vs CRDT (Yjs), presence & cursors, offline edits, conflict resolution, rich text model |
| 5 | [ ] **Spreadsheet (Google Sheets)** | Virtualized grid (rows & columns), formula dependency graph, Web Workers, canvas rendering |
| 6 | [ ] **Kanban board (Trello/Jira)** | Drag & drop (a11y), optimistic reordering, fractional indexing, real-time sync |
| 7 | [ ] **Video streaming player (YouTube/Netflix)** | Adaptive bitrate (HLS/DASH, MSE), buffering, controls a11y, analytics, recommendations rail |
| 8 | [ ] **E-commerce product page & checkout** | SSR/SSG for SEO, image gallery, variants, cart state, payment integration security, performance (LCP) |
| 9 | [ ] **Photo gallery / Pinterest masonry** | Masonry layout, responsive images, infinite loading, lightbox |
| 10 | [ ] **Real-time dashboard / analytics charts** | Data streaming, throttled updates, charting library choice (canvas vs SVG), large datasets |
| 11 | [ ] **Notifications system / toast library** | Real-time delivery, queueing, a11y live regions, persistence |
| 12 | [ ] **Design system / component library** | Tokens, theming, API design, a11y, distribution, versioning |
| 13 | [ ] **Form builder / survey tool** | Schema-driven rendering, validation, conditional logic, drag & drop |
| 14 | [ ] **Calendar (Google Calendar)** | Time zones, recurring events, overlapping event layout, drag to resize |
| 15 | [ ] **File uploader (Google Drive/Dropbox)** | Chunked/resumable uploads, progress, parallelism, retries, pre-signed URLs, folder trees |
| 16 | [ ] **Nested comments thread (Reddit)** | Tree rendering, collapsing, pagination of replies, optimistic posting |
| 17 | [ ] **Data table / grid** | Sorting, filtering, pagination vs virtualization, column resizing, server-side ops, TanStack Table |
| 18 | [ ] **Rich text editor** | contenteditable pitfalls, editor frameworks (Lexical, ProseMirror/Tiptap, Slate), paste sanitization |
| 19 | [ ] **Figma-like canvas app** | Canvas/WebGL rendering, scene graph, hit testing, multiplayer, undo/redo |
| 20 | [ ] **Travel/hotel booking site** | Search filters in URL, maps integration, date pickers, SSR + caching |
| 21 | [ ] **Social media stories / image editor** | Media capture, canvas manipulation, upload pipeline |
| 22 | [ ] **Email client (Gmail)** | Offline, keyboard shortcuts, large lists, sanitizing HTML emails |
| 23 | [ ] **Micro-frontend platform for multiple teams** | Composition, shared deps, routing, deployments, governance |
| 24 | [ ] **AI chat interface (ChatGPT-like)** | Token streaming (SSE/fetch streams), markdown rendering & sanitization, stop/regenerate, conversation history, optimistic UI, code highlighting |
| 25 | [ ] **Maps / ride tracking UI** | Real-time location updates, map tiles, marker clustering, battery/network considerations |

---

## 27. UI Machine Coding Round (P0)

> 45–90 minutes to build a working component/app in React (sometimes vanilla JS). Evaluated on correctness, component structure, state design, a11y, edge cases, styling basics, and code quality.

- [ ] **Practice list (build each in React + TS, then some in vanilla JS)**
  - [ ] Accordion · Tabs · Modal/Dialog (focus trap) · Tooltip/Popover · Dropdown/Select · **Autocomplete with debounce & keyboard nav**
  - [ ] Image carousel/slider · Star rating · Progress bar(s) with queue · Pagination · Infinite scroll · **Data table with sort/filter/paginate**
  - [ ] Todo app (CRUD, filters, persistence) · Kanban board with drag & drop · Nested checkboxes · **File explorer tree** · Nested comments
  - [ ] Stopwatch/timer/countdown · Traffic light · OTP input · Multi-step form with validation · Transfer list · Toast notifications · Poll widget
  - [ ] Tic-tac-toe / Connect Four / Memory game / Wordle · Snake game
  - [ ] Typeahead with caching · Infinite feed with virtualization · Calendar/date picker · Like button with optimistic update · Chips input · Color picker · Grid light-up
- [ ] **Checklist while coding** — clarify requirements; plan component tree & state; type props; handle loading/error/empty states; keyboard & ARIA; clean up effects/timers; avoid unnecessary re-renders; extract hooks; test manually with edge cases; talk through trade-offs

---

# PART E — FULL-STACK

## 28. Node.js (Deep) (P0)

- [ ] **Architecture** — V8 + **libuv**, single-threaded event loop, thread pool (fs, DNS lookup, crypto, zlib; `UV_THREADPOOL_SIZE`)
- [ ] **Event loop phases** — timers → pending callbacks → poll → check (`setImmediate`) → close callbacks; `process.nextTick` vs microtasks vs `setImmediate` vs `setTimeout(0)` ordering
- [ ] **Blocking the event loop** — CPU-heavy work, sync APIs (`fs.readFileSync`, `JSON.parse` of huge payloads, crypto), regex backtracking; detection (event loop lag/utilization metrics, clinic.js, `--prof`); fixes (worker_threads, offloading, streaming)
- [ ] **Concurrency** — `worker_threads` (CPU parallelism, `SharedArrayBuffer`, `MessageChannel`), `cluster` module (multi-process on one host), `child_process` (`spawn`/`exec`/`fork`), PM2; in containers prefer one process per container
- [ ] **Streams** — readable/writable/duplex/transform, backpressure, `pipeline()` (error handling & cleanup), object mode, async iteration over streams, Web Streams interop; streaming large files/CSV/JSON
- [ ] **Buffers** & binary data, encodings
- [ ] **EventEmitter** — memory leak warnings, error events, `once`
- [ ] **Modules** — CommonJS vs ESM in Node (`"type": "module"`, `.mjs`/`.cjs`, `require(esm)` support in modern Node), module resolution, `exports` field
- [ ] **Error handling** — async errors, `unhandledRejection`/`uncaughtException` (crash & restart), operational vs programmer errors, graceful shutdown (SIGTERM, closing servers & DB pools)
- [ ] **Modern Node features** — built-in `fetch`/undici, test runner (`node:test`), watch mode, `--env-file`, permission model, native TypeScript type stripping, `AsyncLocalStorage` (request context, tracing), `node:` prefix imports, single executable apps
- [ ] **Performance & memory** — heap snapshots, `--inspect` with Chrome DevTools, `--max-old-space-size`, memory leaks (closures, global caches, listeners), clinic.js, 0x flame graphs
- [ ] **Security** — dependency risks, `eval`, prototype pollution, path traversal, ReDoS, `child_process` injection, secrets handling, helmet, rate limiting
- [ ] **Alternative runtimes** — **Deno** (secure by default, TS, web standards), **Bun** (fast runtime, bundler, test runner, package manager), edge runtimes (Cloudflare Workers/V8 isolates, Vercel Edge) & WinterTC (common runtime APIs)

### 🎯 Frequently Asked
- Explain the Node.js event loop phases; `nextTick` vs `setImmediate`
- How would you handle CPU-intensive work in Node?
- Streams and backpressure — process a 10 GB file
- How do you scale a Node.js service across cores?

---

## 29. Backend for Frontend Engineers (P0)

### 29.1 Server Frameworks
- [ ] **Express** — middleware chain, routers, error middleware, async error handling, limitations
- [ ] **Fastify** — plugins & encapsulation, JSON schema validation & serialization (speed), hooks, logging (pino)
- [ ] **NestJS** — modules, providers & DI, controllers, pipes, guards, interceptors, exception filters, decorators, microservices transport (enterprise Node)
- [ ] **Hono** (edge-first, multi-runtime), Koa, tRPC servers, GraphQL servers (Apollo Server, GraphQL Yoga, Pothos/Nexus schema builders)
- [ ] **Next.js as a backend** — route handlers, Server Actions, middleware/proxy; limits (long-running jobs, websockets) and when to split a separate service

### 29.2 APIs
- [ ] **REST design** — resources, methods, status codes, error format (RFC 9457), pagination (cursor), filtering, idempotency keys, versioning, OpenAPI
- [ ] **GraphQL** — schema design, resolvers, N+1 & DataLoader, auth in resolvers, complexity limits, persisted queries, subscriptions, federation
- [ ] **tRPC** & typed RPC; **gRPC** awareness (gRPC-Web, Connect)
- [ ] **Real-time** — WebSockets (socket.io, ws), SSE, scaling with Redis pub/sub & sticky sessions
- [ ] **Validation** — Zod/Valibot at every boundary, typed request/response

### 29.3 Data
- [ ] **SQL fundamentals** — joins, indexes (B-tree, composite, covering), transactions & isolation levels, N+1, EXPLAIN, migrations, connection pooling (critical with serverless — PgBouncer, Neon/Supabase poolers, Prisma Accelerate/Data Proxy)
- [ ] **ORMs/query builders** — **Prisma** (schema, migrations, client, relation queries), **Drizzle** (SQL-like, type-safe), TypeORM, Kysely, Knex, Sequelize (legacy); raw SQL when needed
- [ ] **Databases** — PostgreSQL (primary), MySQL, SQLite (Turso/libSQL, local-first), MongoDB (Mongoose), Redis (caching, sessions, rate limiting, queues), serverless DBs (Neon, PlanetScale, Supabase, DynamoDB)
- [ ] **Caching** — cache-aside, TTLs, invalidation, stampede protection, CDN caching of API responses
- [ ] **Background jobs** — BullMQ (Redis), Inngest, Trigger.dev, Temporal, SQS; retries, idempotency, DLQs
- [ ] **File storage** — S3/R2, pre-signed uploads, image processing (sharp), CDN

### 29.4 Auth (P0)
- [ ] Sessions (cookie + server store) vs JWT; refresh token rotation; revocation
- [ ] OAuth 2.0/OIDC flows (Authorization Code + PKCE), social login, SSO (SAML/OIDC for enterprise), MFA, passkeys/WebAuthn, magic links
- [ ] Libraries/services — **Auth.js (NextAuth)**, **Better Auth**, Lucia (deprecated as a library — now a learning resource), Clerk, Auth0, Cognito, Supabase Auth, Firebase Auth, Keycloak
- [ ] Authorization — RBAC/ABAC, row-level security (Supabase/Postgres RLS), checking permissions server-side in every action/handler, multi-tenant isolation
- [ ] Password storage (bcrypt/argon2), account enumeration, brute-force protection, CSRF with cookie sessions

### 29.5 Backend Quality
- [ ] Testing APIs (Vitest/Jest + Supertest, Testcontainers, contract tests), logging (pino, structured), metrics, tracing (OpenTelemetry Node SDK), error tracking
- [ ] Rate limiting (token bucket, sliding window; Upstash Ratelimit, express-rate-limit), input validation, security headers (helmet), secrets management

---

## 30. Backend System Design Essentials (P1)

> Full-stack seniors are often given a classic backend system design round. Know the fundamentals.

- [ ] **Framework** — requirements → estimates → APIs → data model → high-level design → deep dives → failure modes → monitoring
- [ ] **Building blocks** — DNS, CDN, load balancers (L4/L7), API gateways, stateless app servers, caches (Redis), SQL vs NoSQL, object storage, message queues (Kafka/RabbitMQ/SQS), search (Elasticsearch), workers/cron
- [ ] **Concepts** — horizontal scaling, replication & read replicas, sharding & consistent hashing, CAP/consistency models, caching strategies & invalidation, async processing, idempotency, rate limiting, circuit breakers/retries/timeouts, transactional outbox, sagas, unique ID generation
- [ ] **Estimation** — QPS, storage, bandwidth (1 day ≈ 10⁵ s)
- [ ] **Classic problems** — URL shortener, rate limiter, notification system, chat system, news feed, typeahead backend, file storage (Dropbox), video streaming, ticket booking, payment system, web crawler
- [ ] **Full-stack framing** — design both client and server for features like chat, feeds, collaborative editing, uploads

---

## 31. DevOps, Deployment & Observability (P1)

- [ ] **Hosting models** — static hosting + CDN (S3/CloudFront, Netlify, Cloudflare Pages), Vercel/Netlify platforms, containers (Docker, ECS, Kubernetes, Cloud Run), serverless functions (Lambda, Vercel Functions), edge functions (Cloudflare Workers)
- [ ] **Docker for Node/Next.js** — multi-stage builds, `node:alpine`/distroless/slim, standalone Next output, non-root, `.dockerignore`, signal handling (PID 1), layer caching with lockfiles
- [ ] **Kubernetes basics** — deployments, services, ingress, probes, resource limits, HPA — enough to discuss SSR app hosting
- [ ] **CI/CD** — GitHub Actions/GitLab CI: install (cached), lint, typecheck, unit tests, build, E2E against preview, bundle-size & Lighthouse checks, deploy; preview deployments per PR; trunk-based development; feature flags; rollbacks
- [ ] **Caching & CDN config** — immutable hashed assets, HTML short TTL/revalidation, stale-while-revalidate, cache invalidation on deploy, edge caching of SSR responses
- [ ] **Environment config** — build-time vs runtime env vars (a classic SPA/Docker problem), secrets
- [ ] **Observability** — Sentry (errors, performance, source maps, releases), RUM/Web Vitals, logs (structured), OpenTelemetry for Node & browser, synthetic monitoring, uptime checks, alerting on error rate & vitals regressions
- [ ] **Cloud basics** — AWS (S3, CloudFront, Lambda, API Gateway, Cognito, DynamoDB, RDS), IAM least privilege, cost awareness

---

## 32. Mobile & Cross-Platform (P2)

- [ ] **React Native** — architecture (New Architecture: Fabric renderer, TurboModules, JSI, Hermes), Expo (EAS builds, OTA updates, Expo Router), navigation, native modules, performance (lists, animations with Reanimated), code sharing with web (monorepo, react-native-web)
- [ ] **Responsive & mobile web** — touch targets, viewport units, safe areas, input modes, mobile performance on low-end Android devices, network variability
- [ ] **Alternatives** — PWAs, Capacitor/Ionic, Flutter, native — trade-offs

---

## 33. AI in Frontend Engineering (P1)

- [ ] **Building AI UIs** — token streaming (fetch streams/SSE), incremental Markdown rendering with sanitization, stop/regenerate, conversation state, attachments, tool-call/"thinking" UIs, citations, feedback (thumbs), error/rate-limit handling
- [ ] **Vercel AI SDK** (`useChat`, `streamText`, generative UI), LangChain.js, OpenAI/Anthropic JS SDKs (call from server — never expose API keys in the browser)
- [ ] **On-device AI** — WebGPU/ONNX Runtime Web/Transformers.js, Chrome built-in AI APIs (awareness)
- [ ] **Security** — prompt injection reaching the UI, rendering untrusted model output (XSS via Markdown/HTML), data leakage
- [ ] **AI-assisted development** — AI coding tools (Cursor, Claude Code, Copilot, v0), design-to-code, generating tests; having a mature, balanced point of view (review discipline, security, team practices) — a common 2026 interview question

---

# PART F — PROBLEM SOLVING

## 34. DSA in JavaScript/TypeScript (P0)

> Frontend loops at product/big-tech companies still include 1–2 DSA rounds (usually Easy–Medium). Target **150–200 problems**.

- [ ] **JS/TS idioms** — `Map`/`Set` for hashing, array as stack (`push`/`pop`), **queue pitfalls** (`shift` is O(n) — use index pointer or deque implementation), **no built-in heap** (implement a binary heap/PriorityQueue class — practice this!), sorting with comparators (`(a, b) => a - b`; default sort is lexicographic!), `Array.from({length: n}, () => [])` for 2D arrays (not `fill([])`), BigInt for large numbers, string immutability, `charCodeAt`
- [ ] **Complexity** — Big-O, amortized, recursion space
- [ ] **Data structures** — arrays/strings, hash maps, linked lists, stacks/queues/deques, heaps, trees (BST, traversal, LCA), tries, graphs, union-find, LRU cache (with `Map` insertion order)
- [ ] **Patterns** — two pointers, sliding window, fast/slow pointers, merge intervals, binary search (incl. on answer), BFS/DFS, topological sort, backtracking, top-K with heap, monotonic stack, prefix sums, DP (1D/2D, knapsack, LIS/LCS), greedy
- [ ] **Frontend-flavored problems** — DOM tree traversal (find element by attribute, get path between nodes, identical DOM trees), flatten nested objects/arrays, JSON diff, virtual DOM diff (simplified), parsing (templating engine, simple expression evaluator), dependency resolution (topological sort of modules), rate limiter/throttler, LRU cache, event scheduler, text justification, autocomplete with trie
- [ ] **Must-practice (LeetCode)** — Two Sum, Valid Anagram, Group Anagrams, Top K Frequent, Product Except Self, Longest Substring Without Repeating, Minimum Window Substring, Valid Parentheses, Daily Temperatures, Binary Search variants, Merge Intervals, Meeting Rooms II, Reverse Linked List, Merge K Lists, LRU Cache, Level Order Traversal, Validate BST, LCA, Serialize Tree, Number of Islands, Course Schedule, Word Ladder, Implement Trie, Subsets, Permutations, Combination Sum, Coin Change, LIS, Word Break, Edit Distance, Kth Largest Element
- [ ] **Execution protocol** — clarify → examples → brute force → optimize → code cleanly in TS → test → complexity

---

## 35. JavaScript Coding Questions (P0)

> Very common in frontend loops: implement language/library features from scratch. Practice each in TypeScript.

- [ ] **Function utilities** — `debounce` (leading/trailing, cancel, flush), `throttle`, `once`, `memoize` (with key resolver), `curry` (and infinite curry `sum(1)(2)(3)()`), `compose`/`pipe`, `partial`
- [ ] **Polyfills** — `Function.prototype.bind`/`call`/`apply`, `Array.prototype.map`/`filter`/`reduce`/`flat`, `Object.create`, `new` operator, `instanceof`, `JSON.stringify` (simplified), `Object.assign`, `Array.from`
- [ ] **Promises** — implement `Promise` (A+ basics: states, then chaining, microtasks), `Promise.all`/`allSettled`/`race`/`any`, `promisify`, **promise pool with concurrency limit**, retry with exponential backoff, `sleep`, timeout wrapper, sequential execution, cancelable promise
- [ ] **Objects & data** — `deepClone` (cycles, Map/Set, Dates), `deepEqual`, `flatten` (arrays & objects), `unflatten`, lodash `get`/`set`/`groupBy`/`chunk`/`uniqBy`, `classnames` utility, query string parse/stringify, immutable update helpers
- [ ] **Events & patterns** — `EventEmitter` (on/off/once/emit), pub/sub, observable (simplified RxJS), middleware pipeline, dependency injection container
- [ ] **DOM** — `getElementsByClassName`/`querySelectorAll` implementation (tree traversal), event delegation helper, infinite scroll with IntersectionObserver, drag & drop, virtualized list (vanilla), simple templating/`render` (virtual DOM `createElement` + `render`), `useState`-like hook mechanics
- [ ] **Async scenarios** — request deduplication/caching layer, auto-retrying fetch with abort, task scheduler with priorities, rate-limited API caller, batching requests (DataLoader-style)
- [ ] **Output prediction** — hoisting, closures, `this`, event loop ordering, coercion, prototype chain puzzles

---

# PART G — LEADERSHIP, BEHAVIORAL & CAREER

## 36. Technical Leadership (P0)

- [ ] **Technical direction** — frontend vision & roadmap, architecture RFCs & ADRs, choosing frameworks (with trade-offs, not hype), build vs buy (component libraries, auth, CMS), tech debt strategy, large migrations (§25), standards (TS strictness, lint rules, testing, a11y & perf budgets), platform/DX investments (monorepo, CI speed, design system)
- [ ] **Cross-functional leadership** — partnering with design (design system, Figma workflows), product (scope & trade-offs), backend (API contracts, BFF), QA, SEO/marketing, security, accessibility specialists
- [ ] **Execution** — breaking down epics, estimation with uncertainty, managing dependencies on APIs, delivery metrics (DORA), quality gates, release management
- [ ] **People** — mentoring (juniors in React/TS/a11y/perf), code review culture, delegation, feedback (SBI), hiring & interview design (UI coding exercises, take-homes), onboarding docs, guilds/chapters, conflict resolution
- [ ] **Business impact** — conversion, SEO traffic, Core Web Vitals → revenue, accessibility compliance risk, developer velocity; communicating impact to executives
- [ ] **Track decision** — Staff/Principal frontend IC vs Engineering Manager

---

## 37. Behavioral Interviews & Story Bank (P0)

### 37.1 Format
- [ ] STAR / STAR-L; 2–3 minutes; "I" not "we"; quantify (LCP −40%, conversion +3%, bundle −35%, build time −60%, a11y issues −90%); show trade-offs; real failures; prepare for deep follow-ups

### 37.2 Story Bank (15–20 stories)
- [ ] Hardest technical problem · biggest frontend initiative led (e.g., migration, design system, platform rewrite) · architecture decision & trade-offs · production incident (broken release, CDN cache issue, version skew) · failure/mistake · conflict with designer/PM/backend · disagree & commit · influencing without authority across teams · mentoring success · underperformer · tight deadline · ambiguity · pushing back on product · convincing stakeholders to invest in perf/a11y/tech debt · improving DX/CI · customer obsession (a11y or performance for real users) · innovation · data-driven decision (A/B test, RUM data) · critical feedback received · bad news delivered · performance win with numbers · security issue (XSS, leaked key) · hiring/building a team · learning a new stack fast · simplifying over-engineered frontend

### 37.3 Common Questions
- [ ] Tell me about yourself (90–120 s) · **why the career break** (intentional 2–3 months of upskilling — confident, specific) · why leaving · why this company · strengths/weaknesses · greatest achievement · where in 5 years · IC vs manager · how you stay current (frontend moves fast — show judgment, not hype)
- [ ] Company frameworks — Amazon LPs, Google Googleyness, Meta signals; map stories to values
- [ ] Questions to ask — frontend architecture & tech stack, design system maturity, performance & a11y culture, release process, how frontend is valued in the org, growth to Staff

---

## 38. Project Deep-Dive, Resume & Negotiation (P0)

- [ ] **Deep dives (2–3 projects)** — business problem, scale (users, pages, team size, bundle size, traffic), architecture diagram (rendering strategy, state, data flow, deployment), your role, decisions & alternatives (why Next.js vs SPA, why Zustand vs Redux, why micro-frontends or not), hardest problems, performance/a11y results, incidents, testing & release approach, what you'd change
- [ ] **Portfolio** (strong signal for frontend) — GitHub projects, live demos, design system contributions, blog posts/talks, open-source contributions
- [ ] **Resume** — impact bullets with numbers, leadership & scale, keywords (React 19, TypeScript, Next.js, RSC, performance/Core Web Vitals, accessibility, design systems, testing, Node.js)
- [ ] **Search & negotiation** — tiered targets, referrals, apply by week 4–6, track pipeline, research comp (levels.fyi), negotiate level & total comp, evaluate team/manager/growth

---

## 39. Interview Formats

| Company type | Typical loop for a 10 YOE frontend/full-stack engineer | Prep emphasis |
|--------------|---------------------------------------------------------|---------------|
| **Big Tech** | JS/DOM coding · DSA (1–2) · **frontend system design** · behavioral/leadership | JS fundamentals, DSA, RADIO system design |
| **Product companies / scale-ups** | **UI machine coding (React)** · JS implementation questions · frontend system design · HM | Machine coding speed, React depth, perf & a11y |
| **Full-stack roles** | React coding · backend API/system design · DB questions · behavioral | Node.js, SQL, API design, backend system design |
| **Startups** | Take-home or pairing on a realistic feature · architecture discussion · culture | Pragmatism, end-to-end ownership, Next.js |
| **Staff/Principal** | Architecture review · large-scale frontend design (micro-frontends, design systems) · cross-team leadership | Strategy, influence, migrations |

---

# PART H — EXECUTION

## 40. Rapid-Fire Questions (Top 100)

**Web Platform, HTML & CSS**
1. [ ] What happens when you type a URL?
2. [ ] Critical rendering path; render-blocking resources
3. [ ] Reflow vs repaint vs composite; layout thrashing
4. [ ] `async` vs `defer` vs `module` scripts
5. [ ] HTTP caching headers for hashed assets vs HTML
6. [ ] CORS and preflight requests
7. [ ] Cookies: `SameSite`, `HttpOnly`, `Secure`
8. [ ] Semantic HTML and why it matters
9. [ ] Specificity, cascade layers, `:where` vs `:is`
10. [ ] Stacking contexts and z-index
11. [ ] Flexbox vs Grid
12. [ ] Container queries vs media queries
13. [ ] CSS-in-JS vs CSS Modules vs Tailwind
14. [ ] How to avoid CLS from fonts and images
15. [ ] Responsive images (`srcset`, `sizes`, `<picture>`)

**JavaScript**
16. [ ] Closures — practical uses and pitfalls
17. [ ] `this` binding rules
18. [ ] Prototypal inheritance; how `new` works
19. [ ] `var`/`let`/`const`, hoisting, TDZ
20. [ ] `==` vs `===`; coercion
21. [ ] Event loop: microtasks vs macrotasks ordering
22. [ ] Promise combinators; implement `Promise.all`
23. [ ] async/await error handling; parallel vs sequential awaits
24. [ ] AbortController and cancelling stale requests
25. [ ] Debounce vs throttle (implement)
26. [ ] Event delegation and propagation
27. [ ] ESM vs CommonJS; tree shaking
28. [ ] Map vs Object; WeakMap use cases
29. [ ] Memory leaks in SPAs — detection & fixes
30. [ ] Deep clone (`structuredClone` limits) and deep equal

**TypeScript**
31. [ ] `any` vs `unknown` vs `never`
32. [ ] `interface` vs `type`
33. [ ] Discriminated unions & exhaustiveness
34. [ ] Generics with constraints; `keyof`, indexed access
35. [ ] Mapped & conditional types; `infer`
36. [ ] Implement `Pick`/`Omit`/`DeepPartial`/`ReturnType`
37. [ ] `satisfies` vs `as` vs annotation
38. [ ] Type guards & assertion functions
39. [ ] Runtime validation with Zod; inferring types
40. [ ] tsconfig strictness flags you insist on
41. [ ] Module augmentation & declaration files
42. [ ] Typing polymorphic and generic React components

**React**
43. [ ] Render vs commit phase; what triggers re-renders
44. [ ] Reconciliation & keys (why index keys break)
45. [ ] Fiber & concurrent rendering
46. [ ] Rules of hooks — why
47. [ ] `useEffect` dependencies, cleanup, race conditions
48. [ ] "You might not need an effect" examples
49. [ ] `useMemo`/`useCallback`/`React.memo` — when they help
50. [ ] React Compiler — what it does
51. [ ] `useLayoutEffect` vs `useEffect`
52. [ ] `useRef` use cases
53. [ ] Context performance problems & solutions
54. [ ] `useTransition` / `useDeferredValue`
55. [ ] `useSyncExternalStore` and tearing
56. [ ] Error boundaries — what they don't catch
57. [ ] Suspense for code splitting & data
58. [ ] Server Components vs Client Components vs SSR
59. [ ] Server Actions — how and security implications
60. [ ] React 19 features (actions, `use`, `useOptimistic`, ref as prop)
61. [ ] Hydration & hydration mismatches
62. [ ] Controlled vs uncontrolled components
63. [ ] Compound components / render props / HOCs / custom hooks
64. [ ] State classification; Redux vs Zustand vs Context vs TanStack Query
65. [ ] TanStack Query: `staleTime` vs `gcTime`; optimistic updates
66. [ ] Virtualizing a 100k-row list
67. [ ] Code splitting strategy
68. [ ] Forms with React Hook Form + Zod
69. [ ] Next.js caching & revalidation
70. [ ] CSR vs SSR vs SSG vs ISR vs PPR

**Quality, Performance, A11y, Security**
71. [ ] LCP, INP, CLS — definitions & fixes
72. [ ] Investigating a slow interaction
73. [ ] Reducing bundle size
74. [ ] Performance budgets in CI
75. [ ] Testing strategy; RTL query priority
76. [ ] MSW for API mocking
77. [ ] Playwright vs Cypress
78. [ ] Accessible modal/combobox implementation
79. [ ] Focus management in SPAs
80. [ ] ARIA — when to use and not
81. [ ] XSS vectors in React; DOMPurify
82. [ ] CSP with nonces
83. [ ] Token storage in SPAs; BFF pattern
84. [ ] npm supply-chain risks & mitigations
85. [ ] Vite vs webpack; Module Federation

**Architecture, Full-Stack & Leadership**
86. [ ] Micro-frontends — when and how
87. [ ] Design system architecture & governance
88. [ ] Monorepo tooling (Turborepo/Nx)
89. [ ] Feature flags & A/B testing without flicker
90. [ ] Version skew between client and server after deploys
91. [ ] Frontend system design: news feed
92. [ ] Frontend system design: chat app
93. [ ] Frontend system design: autocomplete
94. [ ] Node.js event loop phases
95. [ ] CPU-heavy work in Node
96. [ ] REST vs GraphQL vs tRPC
97. [ ] Auth with OAuth + PKCE / sessions in Next.js
98. [ ] A large migration you led
99. [ ] Raising frontend quality across teams
100. [ ] A decision that turned out wrong

---

## 41. 12-Week Preparation Plan

### Daily Template (≈ 8–9 focused hours, 6 days/week)
| Block | Time | Activity |
|-------|------|----------|
| Morning | 2 h | **DSA in TS** (2–3 problems) or **JS implementation questions** (alternate days) |
| Midday | 2 h | **UI machine coding** — build one component/app under a timer |
| Afternoon | 2.5 h | **Core topic of the week** — read, build demos, write notes |
| Evening | 1.5 h | **Frontend system design** (alternate with backend design / behavioral) |
| End of day | 15 min | Update checklist; Anki review |

### Week-by-Week
| Week | Core Topic | Coding Focus | Design / Behavioral |
|------|------------|--------------|---------------------|
| **1** | How browsers work, HTML, CSS (§1–3) | Arrays, hashing; accordion, tabs, modal | RADIO framework; resume & intro pitch |
| **2** | JavaScript deep (§4) | debounce/throttle/curry/memoize; strings, two pointers | Autocomplete design; story candidates |
| **3** | Async JS, Promises, event loop, modules | Promise polyfills, promise pool; sliding window, stacks | News feed design; 5 STAR stories |
| **4** | TypeScript deep (§5) + type challenges | Utility types; linked lists, trees | Chat app design; 5 more stories; target list |
| **5** | React fundamentals & hooks (§6–7) | Custom hooks; autocomplete, data table | Kanban & file uploader designs; **start applying** |
| **6** | React performance, React 19 & RSC (§8–9) | Virtualized list, infinite scroll; graphs | Google Docs/Sheets designs; project deep-dive #1 |
| **7** | State, data fetching, forms, routing (§10–13) | Multi-step form, todo with persistence; heaps | Dashboard & video player designs; mocks start |
| **8** | Next.js & rendering strategies, styling & design systems (§14–17) | Carousel, star rating, nested comments; DP I | Design system design; project deep-dive #2 |
| **9** | Tooling, testing (§18–19) | Write tests for previous builds; DP II | E-commerce page design; behavioral mocks |
| **10** | Performance, a11y, security (§20–22) | Accessible combobox/dialog; mixed DSA | Micro-frontends platform design; apply to dream tier |
| **11** | Node.js & backend, architecture at scale (§25, §28–31) | Small full-stack app (Next.js + Postgres + auth) | Backend system design basics; negotiation prep |
| **12** | Rapid-fire 100 & revision | Timed mocks | Final mocks; rest |

### Throughout
- [ ] 10+ mocks (UI coding ×3, JS/DSA ×3, frontend system design ×3, behavioral ×1+)
- [ ] Portfolio project polished (React 19 + TS + Next.js + TanStack Query + tests + a11y + perf budget) for fresh talking points

---

## 42. Resources

### Books
- [ ] **You Don't Know JS Yet** — Kyle Simpson; **Eloquent JavaScript** — Marijn Haverbeke; **JavaScript: The Definitive Guide** — Flanagan
- [ ] **Effective TypeScript (2nd ed.)** — Dan Vanderkam; **Programming TypeScript** — Boris Cherny; **Total TypeScript** (Matt Pocock, online)
- [ ] **Learning React / Fluent React** — Tejas Kumar; react.dev docs (best React resource)
- [ ] **CSS: The Definitive Guide**; **Every Layout**; Josh Comeau's CSS for JS Developers (course)
- [ ] **High Performance Browser Networking** — Ilya Grigorik (free online)
- [ ] **Web Performance in Action**; web.dev performance & Core Web Vitals guides
- [ ] **Inclusive Components** — Heydon Pickering; **Form Design Patterns** — Adam Silver; WAI-ARIA APG
- [ ] **Building Micro-Frontends** — Luca Mezzalira
- [ ] **Node.js Design Patterns (3rd ed.)** — Casciaro & Mammino
- [ ] **Designing Data-Intensive Applications** — Kleppmann (for full-stack depth); **System Design Interview** — Alex Xu
- [ ] **The Staff Engineer's Path** — Tanya Reilly

### Online
- [ ] react.dev (especially "You Might Not Need an Effect", "Rules of React"), Next.js docs, TypeScript Handbook, MDN, web.dev, Chrome for Developers blog
- [ ] **GreatFrontEnd** (UI coding, JS questions, front-end system design), **BigFrontEnd.dev** (JS/TS coding), **Frontend Interview Handbook**, **type-challenges** repo, LeetCode/NeetCode
- [ ] Blogs — Dan Abramov (overreacted), Kent C. Dodds (testing), Josh Comeau, TkDodo (React Query), Matt Pocock, Addy Osmani, Jake Archibald, Smashing Magazine, CSS-Tricks archive, Vercel/Shopify/Airbnb/Netflix/Meta engineering blogs
- [ ] Newsletters/podcasts — This Week in React, JavaScript Weekly, Frontend Focus, Syntax.fm, JS Party
- [ ] Mocks — Pramp, interviewing.io, GreatFrontEnd mock interviews, peers

---

## 43. Final Readiness Checklist

### Interview Readiness
- [ ] Can explain the browser rendering pipeline, event loop, and JS fundamentals without hesitation
- [ ] Can implement debounce, throttle, Promise.all, promise pool, deepClone, EventEmitter, curry, bind from memory
- [ ] Can write advanced TS types (mapped/conditional/infer) and type React components rigorously
- [ ] Built 25+ UI components/apps under time pressure with a11y and edge cases
- [ ] Practiced 20+ frontend system designs and 5+ backend designs aloud
- [ ] 150–200 DSA problems in JS/TS; can implement a heap
- [ ] Clear stories on performance wins, migrations, design systems, incidents, leadership
- [ ] Rapid-fire 100 answered aloud; 10+ mocks completed

### Production-Ready Frontend Checklist (great interview answer too)
- [ ] **Code** — TypeScript strict, linted, formatted, tested (unit + integration + critical E2E), typed API layer with runtime validation
- [ ] **Performance** — Core Web Vitals within targets at p75 (RUM), bundle budgets in CI, images/fonts optimized, code splitting, caching headers correct
- [ ] **Accessibility** — WCAG 2.2 AA, keyboard & screen reader tested, axe in CI, accessible design-system components
- [ ] **Security** — CSP, no `dangerouslySetInnerHTML` without sanitization, safe token storage, server-side authorization, dependency scanning, no secrets in bundles, security headers
- [ ] **Resilience & UX** — error boundaries, loading/empty/error states, retries/backoff, offline handling where needed, optimistic updates with rollback
- [ ] **Observability** — Sentry with source maps & releases, RUM & Web Vitals dashboards, alerts on error rate & vitals regressions
- [ ] **Delivery** — preview deployments, feature flags, canary/instant rollback, version-skew handling, cache invalidation strategy
- [ ] **i18n & SEO** — localized formatting, RTL readiness if needed, metadata, SSR/SSG for indexable pages

---

> **Final advice:** At 10 YOE, interviewers expect you to go beyond "how to use React" into **why it works the way it does** (rendering model, reconciliation, concurrency, RSC), **how to make it fast, accessible and secure at scale**, and **how you lead frontend architecture across teams**. For every topic, be ready to explain **what**, **how it works internally**, **when to use / not use**, **trade-offs**, and **a real experience**.
