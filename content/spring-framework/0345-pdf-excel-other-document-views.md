---
card: spring-framework
gi: 345
slug: pdf-excel-other-document-views
title: "PDF/Excel/other document views"
---

## 1. What it is

Spring MVC provides abstract `View` base classes — `AbstractPdfView` (using the iText/OpenPDF library) and `AbstractXlsView`/`AbstractXlsxView` (using Apache POI) — for generating binary document formats as the response, using the exact same `Controller` → view name → `ViewResolver` → `View` pipeline as HTML rendering. You subclass one of these, implement a single method to build the document from the model, and register it like any other view.

```java
public class InvoicePdfView extends AbstractPdfView {
    @Override
    protected void buildPdfDocument(Map<String, Object> model, Document doc,
                                     PdfWriter writer, HttpServletRequest req, HttpServletResponse res) {
        doc.add(new Paragraph("Invoice #" + model.get("invoiceId")));
    }
}
```

## 2. Why & when

Business applications routinely need to produce downloadable documents — invoices as PDFs, data exports as Excel spreadsheets, reports for offline distribution. Building these through Spring MVC's `View` abstraction (rather than a raw `HttpServletResponse` manipulation in a controller) keeps document generation consistent with the rest of the application's view-resolution and model-population patterns, and lets the same content-negotiation mechanisms (previous card) select a document view alongside HTML/JSON when appropriate.

Use these abstract views when:
- Generating a PDF/Excel document is a first-class response option for an existing resource (e.g. `/invoices/1` as HTML for browsing, `/invoices/1.pdf` or content-negotiated `Accept: application/pdf` for download).
- You want document-generation code organized as a reusable `View` class rather than inline byte-manipulation scattered through controller methods.

For very large or complex documents, consider whether `StreamingResponseBody` (an earlier card) might be a better fit for memory efficiency — `AbstractPdfView`/`AbstractXlsView` build the whole document in memory before writing it, which is fine for typical business documents but not ideal for a huge generated report.

## 3. Core concept

```
Controller returns "invoice-pdf"
        |
        v
BeanNameViewResolver (or another resolver) finds a bean
named "invoice-pdf" that IS a View — the InvoicePdfView bean itself
        |
        v
DispatcherServlet calls view.render(model, request, response)
        |
        v
AbstractPdfView's render() already handles:
  - setting Content-Type: application/pdf
  - creating a PdfWriter bound to the response's OutputStream
  - opening/closing the PDF Document lifecycle
        |
        v
YOUR buildPdfDocument(model, document, writer, request, response)
  is called in the middle — you only add CONTENT, not plumbing
        |
        v
Response: binary PDF bytes, Content-Type: application/pdf,
  optionally Content-Disposition: attachment for browser download prompt
```

The abstract base class owns all the format-specific plumbing (PDF document lifecycle, Excel workbook creation); your subclass only supplies the content-building logic.

## 4. Diagram

<svg viewBox="0 0 720 210" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="210" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">AbstractPdfView: framework handles plumbing, you add content</text>

  <rect x="20" y="50" width="320" height="130" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="180" y="70" text-anchor="middle" fill="#8b949e" font-size="10">AbstractPdfView.render() (framework)</text>
  <text x="35" y="95" fill="#8b949e" font-size="10">1. set Content-Type: application/pdf</text>
  <text x="35" y="113" fill="#8b949e" font-size="10">2. create PdfWriter + Document</text>
  <text x="35" y="131" fill="#6db33f" font-size="10">3. call buildPdfDocument(...)  ← YOUR CODE</text>
  <text x="35" y="149" fill="#8b949e" font-size="10">4. close Document, flush bytes</text>

  <line x1="180" y1="180" x2="180" y2="205" stroke="none"/>
  <rect x="380" y="80" width="300" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="530" y="102" text-anchor="middle" fill="#6db33f" font-size="10">buildPdfDocument(model, doc, ...)</text>
  <text x="530" y="120" text-anchor="middle" fill="#8b949e" font-size="10">doc.add(new Paragraph(...))</text>

  <line x1="340" y1="131" x2="380" y2="110" stroke="#6db33f" marker-end="url(#a21)"/>

  <defs>
    <marker id="a21" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*The abstract view class owns the document lifecycle; your override contributes only the content-building step in the middle.*

## 5. Runnable example

### Level 1 — Basic

A minimal PDF invoice view:

```xml
<!-- pom.xml -->
<dependency>
    <groupId>com.github.librepdf</groupId>
    <artifactId>openpdf</artifactId>
    <version>1.3.42</version>
</dependency>
```

```java
// InvoicePdfView.java
import com.lowagie.text.Document;
import com.lowagie.text.Paragraph;
import com.lowagie.text.pdf.PdfWriter;
import org.springframework.web.servlet.view.document.AbstractPdfView;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.util.Map;

public class InvoicePdfView extends AbstractPdfView {
    @Override
    protected void buildPdfDocument(Map<String, Object> model, Document doc, PdfWriter writer,
                                     HttpServletRequest request, HttpServletResponse response) throws Exception {
        doc.add(new Paragraph("Invoice #" + model.get("invoiceId")));
        doc.add(new Paragraph("Total: $" + model.get("total")));
    }
}
```

```java
// WebConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class WebConfig {
    @Bean(name = "invoice-pdf")
    public InvoicePdfView invoicePdfView() { return new InvoicePdfView(); }
}
```

```java
// InvoiceController.java
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@Controller
public class InvoiceController {

    @GetMapping("/invoices/{id}/pdf")
    public String pdf(@PathVariable long id, Model model) {
        model.addAttribute("invoiceId", id);
        model.addAttribute("total", 149.99);
        return "invoice-pdf";     // resolves to the "invoice-pdf" View BEAN by name
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run
curl -o invoice.pdf http://localhost:8080/invoices/1/pdf
file invoice.pdf
# invoice.pdf: PDF document, version 1.4
```

`BeanNameViewResolver` (autoconfigured, checks for a bean whose name matches the view name) finds the `"invoice-pdf"` bean directly — no template file lookup involved, since `InvoicePdfView` *is* the view, not a resolver pointing to a template.

### Level 2 — Intermediate

An Excel export listing multiple products, using Apache POI via `AbstractXlsxView`, with proper download headers:

```xml
<!-- pom.xml addition -->
<dependency>
    <groupId>org.apache.poi</groupId>
    <artifactId>poi-ooxml</artifactId>
</dependency>
```

```java
// ProductExcelView.java
import org.apache.poi.ss.usermodel.*;
import org.springframework.web.servlet.view.document.AbstractXlsxView;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.util.List;
import java.util.Map;

public class ProductExcelView extends AbstractXlsxView {

    record Product(long id, String name, double price) {}

    @Override
    protected void buildExcelDocument(Map<String, Object> model, Workbook workbook,
                                       HttpServletRequest request, HttpServletResponse response) {
        @SuppressWarnings("unchecked")
        List<Product> products = (List<Product>) model.get("products");

        Sheet sheet = workbook.createSheet("Products");
        Row header = sheet.createRow(0);
        header.createCell(0).setCellValue("ID");
        header.createCell(1).setCellValue("Name");
        header.createCell(2).setCellValue("Price");

        int rowNum = 1;
        for (Product p : products) {
            Row row = sheet.createRow(rowNum++);
            row.createCell(0).setCellValue(p.id());
            row.createCell(1).setCellValue(p.name());
            row.createCell(2).setCellValue(p.price());
        }

        response.setHeader("Content-Disposition", "attachment; filename=\"products.xlsx\"");
    }
}
```

```java
// WebConfig.java (extended)
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class WebConfig {
    @Bean(name = "product-excel")
    public ProductExcelView productExcelView() { return new ProductExcelView(); }
}
```

```java
// ProductController.java
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

import java.util.List;

@Controller
public class ProductController {

    record Product(long id, String name, double price) {}

    @GetMapping("/products/export")
    public String export(Model model) {
        model.addAttribute("products", List.of(
            new Product(1, "Drill", 29.99), new Product(2, "Hammer", 14.99)));
        return "product-excel";
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run
curl -o products.xlsx http://localhost:8080/products/export
file products.xlsx
# products.xlsx: Microsoft Excel 2007+
```

**What changed:** `AbstractXlsxView` provides the Workbook lifecycle (creating the `.xlsx` structure, writing bytes with the correct content type) exactly as `AbstractPdfView` provides the PDF document lifecycle — you only implement `buildExcelDocument` to populate sheets/rows/cells from the model. `Content-Disposition: attachment` prompts a download in a browser rather than attempting inline display.

### Level 3 — Advanced

Production pattern: content-negotiated document generation (the same `/invoices/{id}` URL serves HTML, PDF, or Excel depending on `Accept`), reusing the `ContentNegotiatingViewResolver` mechanism from the previous card, plus streaming considerations for a larger export:

```java
// WebConfig.java (production version)
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.MediaType;
import org.springframework.web.accept.ContentNegotiationManager;
import org.springframework.web.servlet.View;
import org.springframework.web.servlet.ViewResolver;
import org.springframework.web.servlet.view.BeanNameViewResolver;
import org.springframework.web.servlet.view.ContentNegotiatingViewResolver;

import java.util.List;

@Configuration
public class WebConfig {

    @Bean(name = "invoice-pdf")
    public InvoicePdfView invoicePdfView() { return new InvoicePdfView(); }

    @Bean
    public BeanNameViewResolver beanNameViewResolver() {
        BeanNameViewResolver resolver = new BeanNameViewResolver();
        resolver.setOrder(1);
        return resolver;
    }

    @Bean
    public ViewResolver contentNegotiatingViewResolver(ContentNegotiationManager manager,
                                                          InvoicePdfView invoicePdfView) {
        ContentNegotiatingViewResolver resolver = new ContentNegotiatingViewResolver();
        resolver.setContentNegotiationManager(manager);
        resolver.setDefaultViews(List.of((View) invoicePdfView));   // PDF joins the negotiable formats
        resolver.setOrder(0);
        return resolver;
    }
}
```

```java
// InvoiceController.java (production version)
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@Controller
public class InvoiceController {

    @GetMapping("/invoices/{id}")
    public String view(@PathVariable long id, Model model) {
        model.addAttribute("invoiceId", id);
        model.addAttribute("total", 149.99);
        return "invoice";      // SAME view name serves HTML normally, PDF when negotiated
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -H "Accept: text/html" http://localhost:8080/invoices/1
# renders templates/invoice.html

curl -H "Accept: application/pdf" -o invoice.pdf http://localhost:8080/invoices/1
# binary PDF, via InvoicePdfView, SAME URL, SAME controller method
```

**What changed and why:**
- Registering `invoicePdfView` as one of `ContentNegotiatingViewResolver`'s `setDefaultViews` makes PDF a genuine negotiable format alongside whatever Thymeleaf's delegate resolver produces for `"invoice"` — the exact mechanism from the previous card, now applied to a binary document format instead of JSON/XML.
- The **same** controller method and **same** URL (`/invoices/{id}`) now transparently serve either a browsable HTML page or a downloadable PDF depending purely on what the client's `Accept` header requests — no separate `/invoices/{id}/pdf` endpoint needed, no duplicated model-population logic.
- For genuinely large documents (thousands of invoice line items, a huge report), consider whether building the full `Document`/`Workbook` in memory (as both `AbstractPdfView` and `AbstractXlsView` do) remains acceptable, or whether a `StreamingResponseBody`-based custom export (see that card) better bounds memory for very large outputs — these abstract views are well-suited to typical business documents, not massive generated reports.

## 6. Walkthrough

**Request: `GET /invoices/1` with `Accept: application/pdf` (Level 3 code).**

1. `DispatcherServlet` dispatches to `InvoiceController.view(1, model)`. The handler populates `model` with `invoiceId=1` and `total=149.99`, returns `"invoice"`.
2. `ContentNegotiatingViewResolver` (registered with `order=0`, checked first) is asked to resolve `"invoice"`. It determines the requested media type from the `Accept` header: `application/pdf`.
3. It gathers candidates: any delegate `ViewResolver`s configured (Thymeleaf's autoconfigured resolver would offer a `text/html` candidate if `templates/invoice.html` exists) plus its `defaultViews` — here, `invoicePdfView` (`application/pdf`).
4. Scoring: requested `application/pdf` matches `invoicePdfView`'s content type exactly — no other candidate matches `application/pdf`, so it wins outright.
5. `DispatcherServlet` calls `invoicePdfView.render(model, request, response)`.
6. Inside `AbstractPdfView.render()` (framework-provided): sets `response.setContentType("application/pdf")`, creates a `PdfWriter` bound to `response.getOutputStream()`, opens a new `Document`.
7. Calls your overridden `buildPdfDocument(model, doc, writer, request, response)`: `model.get("invoiceId")` → `1`, `model.get("total")` → `149.99`. Two `Paragraph`s are added to `doc`: `"Invoice #1"` and `"Total: $149.99"`.
8. Control returns to the framework's `render()`, which closes the `Document` (finalizing the PDF's internal structure) and flushes the underlying `PdfWriter`'s bytes to the response's `OutputStream`.
9. Final response sent to the client:
   ```
   HTTP/1.1 200 OK
   Content-Type: application/pdf

   %PDF-1.4 ... (binary PDF bytes containing the two paragraphs)
   ```

## 7. Gotchas & takeaways

> **`AbstractPdfView`/`AbstractXlsView` build the entire document in memory before writing any bytes to the response** — for a report with hundreds of thousands of rows, this can mean significant memory pressure and a long delay before the client sees anything. For genuinely large exports, prefer manually streaming with `StreamingResponseBody` and a streaming-capable library API (e.g. Apache POI's `SXSSFWorkbook` for large Excel files) instead.

> **`BeanNameViewResolver` matches the view name against a *bean name*, not a template file path.** Forgetting to register your custom `View` subclass as a Spring bean (or naming the bean incorrectly relative to the view name string the controller returns) produces a `"Could not resolve view"` error indistinguishable at first glance from a missing-template error for HTML views — check bean registration first when a document view "isn't found."

> **`Content-Disposition: attachment` must be set explicitly inside your view's build method** (as in the Excel example) if you want a browser to prompt a file download rather than attempt inline rendering (which, for a PDF, many browsers will actually try to display inline by default without this header — sometimes desirable, sometimes not, depending on the use case).

- `AbstractPdfView`/`AbstractXlsView`/`AbstractXlsxView` handle document-format plumbing; your subclass only implements the content-building method.
- Register document view beans and resolve them via `BeanNameViewResolver`, or fold them into `ContentNegotiatingViewResolver`'s default views for format-negotiated resource endpoints.
- Set `Content-Disposition: attachment` explicitly when you want a browser download prompt rather than inline rendering.
- For very large documents, consider a manually streamed approach instead of these in-memory-building abstract views.
