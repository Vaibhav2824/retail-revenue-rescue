const pptxgen = require("pptxgenjs");
const OUT = process.argv[2];

const C = { ink: "1B2430", ink2: "4A5563", muted: "6B7684", card: "F2F4F7", line: "D9DEE5",
            risk: "D1495B", good: "1F8A70", gold: "E9B44C", white: "FFFFFF" };
const H = "Cambria", B = "Calibri";

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.title = "Retail Revenue Rescue: findings";

const title = (s, text, color = C.ink) =>
  s.addText(text, { x: 0.5, y: 0.35, w: 9, h: 0.8, fontFace: H, fontSize: 26, bold: true, color, margin: 0, valign: "top", isTextBox: true });
const kicker = (s, text, color = C.risk) =>
  s.addText(text.toUpperCase(), { x: 0.5, y: 0.12, w: 9, h: 0.25, fontFace: B, fontSize: 10, bold: true, color, charSpacing: 2, margin: 0, isTextBox: true });
const source = (s, text) =>
  s.addText(text, { x: 0.5, y: 5.25, w: 9, h: 0.25, fontFace: B, fontSize: 9, color: C.muted, margin: 0, isTextBox: true });
const card = (s, x, y, w, h, fill = C.card) =>
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill }, rectRadius: 0.08 });
const badge = (s, x, y, n, fill) => {
  s.addShape(pres.shapes.OVAL, { x, y, w: 0.42, h: 0.42, fill: { color: fill }, line: { color: fill } });
  s.addText(String(n), { x, y, w: 0.42, h: 0.42, fontFace: B, fontSize: 14, bold: true, color: C.white, align: "center", valign: "middle", margin: 0, isTextBox: true });
};
const stat = (s, x, y, w, big, label, color) => {
  s.addText(big, { x, y, w, h: 0.75, fontFace: H, fontSize: 40, bold: true, color, margin: 0, isTextBox: true });
  s.addText(label, { x, y: y + 0.78, w, h: 0.6, fontFace: B, fontSize: 12, color: C.ink2, margin: 0, valign: "top", isTextBox: true });
};

// 1 — title
{
  const s = pres.addSlide(); s.background = { color: C.ink };
  s.addText("RETAIL REVENUE RESCUE", { x: 0.6, y: 1.2, w: 8.8, h: 0.35, fontFace: B, fontSize: 12, bold: true, color: C.gold, charSpacing: 3, margin: 0, isTextBox: true });
  s.addText("Where revenue is leaking, who is about to leave, and what to do on Monday", { x: 0.6, y: 1.65, w: 8.4, h: 1.5, fontFace: H, fontSize: 34, bold: true, color: C.white, margin: 0, valign: "top", isTextBox: true });
  s.addText("Findings for a UK online gift retailer  ·  1.07M invoice lines, Dec 2009 – Dec 2011", { x: 0.6, y: 3.45, w: 8.4, h: 0.4, fontFace: B, fontSize: 14, color: "C9D1DB", margin: 0, isTextBox: true });
  [["£1.27M", "revenue at risk"], ["34%", "of leakage = 2 keying errors"], ["100", "customers to call first"]].forEach(([b, l], i) => {
    const x = 0.6 + i * 2.9;
    s.addText(b, { x, y: 4.2, w: 2.7, h: 0.5, fontFace: H, fontSize: 24, bold: true, color: C.gold, margin: 0, isTextBox: true });
    s.addText(l, { x, y: 4.7, w: 2.7, h: 0.3, fontFace: B, fontSize: 11, color: "C9D1DB", margin: 0, isTextBox: true });
  });
  s.addNotes("Open with the client's question, then the three numbers. Everything after this slide backs them up.");
}

// 2 — question + approach
{
  const s = pres.addSlide(); s.background = { color: C.white };
  kicker(s, "The brief", C.good); title(s, "The client asked three questions, and we agreed how we'd prove the answers");
  card(s, 0.5, 1.4, 4.1, 3.6);
  s.addText("“Revenue looks fine on the top line, but finance says cancellations are eating into it, and we only notice a wholesale customer has gone quiet months after they’ve left.”",
    { x: 0.75, y: 1.6, w: 3.6, h: 2.2, fontFace: H, fontSize: 15, italic: true, color: C.ink, margin: 0, valign: "top", isTextBox: true });
  s.addText("Head of Commercial (fictional client, real data)", { x: 0.75, y: 4.35, w: 3.6, h: 0.4, fontFace: B, fontSize: 11, color: C.muted, margin: 0, isTextBox: true });
  [["Where are we leaking revenue?", "Every excluded row explained; ratio-of-sums leakage"],
   ["Who is about to churn?", "Model must beat the rule already in use, on a later period"],
   ["What is it worth?", "Expected £ loss per customer → a ranked call list"]].forEach(([q, p], i) => {
    const y = 1.45 + i * 1.2;
    badge(s, 4.95, y, i + 1, C.good);
    s.addText(q, { x: 5.55, y: y - 0.02, w: 3.95, h: 0.4, fontFace: B, fontSize: 15, bold: true, color: C.ink, margin: 0, isTextBox: true });
    s.addText("Proof: " + p, { x: 5.55, y: y + 0.38, w: 3.95, h: 0.6, fontFace: B, fontSize: 12, color: C.ink2, margin: 0, valign: "top", isTextBox: true });
  });
  s.addNotes("Success criteria were agreed before any analysis, so the results can't be cherry-picked.");
}

// 3 — leakage
{
  const s = pres.addSlide(); s.background = { color: C.white };
  kicker(s, "Finding 1 · Leakage"); title(s, "Leakage didn’t double in 2011. Two keying errors did.");
  s.addChart(pres.charts.BAR, [{ name: "Cancelled value as % of gross revenue", labels: ["2010", "2011 as reported", "2011 excl. 2 errors"], values: [2.54, 4.84, 2.31] }], {
    x: 0.5, y: 1.3, w: 5.0, h: 3.8, barDir: "col", chartColors: [C.line, C.risk, C.good],
    showTitle: true, title: "Cancelled value as % of gross revenue", titleFontFace: B, titleFontSize: 12, titleColor: C.ink2,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: '0.0"%"', dataLabelFontSize: 14, dataLabelFontBold: true, dataLabelColor: C.ink,
    catAxisLabelColor: C.ink2, catAxisLabelFontSize: 12, valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
    showLegend: false, barGapWidthPct: 60, varyColors: true, valAxisMinVal: 0, valAxisMaxVal: 6,
  });
  stat(s, 5.9, 1.35, 3.6, "34%", "of all cancelled value over two years (£246k) came from just two bulk orders of 80,995 and 74,215 units", C.risk);
  card(s, 5.9, 3.4, 3.6, 1.65);
  s.addText([{ text: "Both were reversed within 16 minutes. ", options: { bold: true } },
             { text: "No cash was lost, but they distorted reporting. Fix: a quantity / value check at order entry. Near-zero cost." }],
    { x: 6.1, y: 3.5, w: 3.25, h: 1.45, fontFace: B, fontSize: 12, color: C.ink, margin: 0, valign: "middle", isTextBox: true });
  source(s, "Source: silver_transactions; invoices 541431/C541433 (Jan 2011) and 581483/C581484 (Dec 2011).");
  s.addNotes("The obvious reading is 'returns are getting worse'. The real answer is 'two typos'. Recommending an investigation would have wasted the client's money.");
}

// 4 — revenue at risk
{
  const s = pres.addSlide(); s.background = { color: C.white };
  kicker(s, "Finding 2 · Retention"); title(s, "£1.27M of next year’s revenue is at risk, and it is concentrated");
  stat(s, 0.5, 1.35, 2.8, "£1.27M", "expected revenue at risk (16% of £7.97M from 4,261 active customers)", C.risk);
  stat(s, 0.5, 2.85, 2.8, "£203k", "held by just 100 customers (2% of the base): the call list", C.ink);
  s.addText("Expected loss = P(churn in 90 days) × last-12-month spend", { x: 0.5, y: 4.4, w: 2.8, h: 0.6, fontFace: B, fontSize: 11, italic: true, color: C.muted, margin: 0, isTextBox: true });
  s.addChart(pres.charts.BAR, [{ name: "Last-12-month revenue (£k)", labels: ["Champions", "Loyal", "At Risk", "Needs Attention", "Hibernating", "Promising"], values: [6150, 1182, 194, 192, 144, 102] }], {
    x: 3.7, y: 1.3, w: 5.8, h: 3.8, barDir: "bar", chartColors: [C.good, C.line, C.line, C.line, C.line, C.line], varyColors: true,
    showTitle: true, title: "Champions (1,576 customers) bring 77% of revenue: last-12-month £k by segment", titleFontFace: B, titleFontSize: 12, titleColor: C.ink2,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: '"£"#,##0"k"', dataLabelFontSize: 11, dataLabelColor: C.ink,
    catAxisLabelColor: C.ink2, catAxisLabelFontSize: 11, catAxisOrientation: "maxMin", valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
    showLegend: false, barGapWidthPct: 40, valAxisMaxVal: 7500,
  });
  source(s, "Source: gold_customer_churn_risk, gold_customer_rfm (as of 10 Dec 2011).");
  s.addNotes("Ranking by expected loss, not probability, puts big accounts with moderate risk above small accounts that are certain to leave. That's the right order for a sales team's time.");
}

// 5 — model credibility
{
  const s = pres.addSlide(); s.background = { color: C.white };
  kicker(s, "Can we trust it?", C.good); title(s, "The model beats the rule the business already uses, on a period it never saw");
  s.addChart(pres.charts.BAR, [{ name: "AUC", labels: ["Rule: longest since last order", "Churn model"], values: [0.707, 0.760] }], {
    x: 0.5, y: 1.35, w: 4.4, h: 3.0, barDir: "col", chartColors: [C.line, C.good], varyColors: true,
    showTitle: true, title: "Ranking quality (AUC, out-of-time)", titleFontFace: B, titleFontSize: 12, titleColor: C.ink2,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", dataLabelFontSize: 14, dataLabelFontBold: true, dataLabelColor: C.ink,
    catAxisLabelColor: C.ink2, catAxisLabelFontSize: 11, valAxisHidden: true, valAxisMinVal: 0.5, valAxisMaxVal: 0.8, valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false, barGapWidthPct: 70,
  });
  s.addChart(pres.charts.BAR, [{ name: "Churn rate", labels: ["All active customers", "Top 10% flagged"], values: [49, 76] }], {
    x: 5.1, y: 1.35, w: 4.4, h: 3.0, barDir: "col", chartColors: [C.line, C.risk], varyColors: true,
    showTitle: true, title: "Share who actually churned (%)", titleFontFace: B, titleFontSize: 12, titleColor: C.ink2,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: '0"%"', dataLabelFontSize: 14, dataLabelFontBold: true, dataLabelColor: C.ink,
    catAxisLabelColor: C.ink2, catAxisLabelFontSize: 11, valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 100, valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false, barGapWidthPct: 70,
  });
  s.addText("Trained on the June 2011 snapshot, tested on September 2011 (unseen). A random split would leak the future and flatter the score. Every published score carries the MLflow run ID that produced it.",
    { x: 0.5, y: 4.5, w: 9, h: 0.6, fontFace: B, fontSize: 12, color: C.ink2, margin: 0, isTextBox: true });
  s.addNotes("Be honest that 0.76 is good, not magic. The point is it's measurably better than what they do today, and it's tested the way it will be used.");
}

// 6 — recommendations
{
  const s = pres.addSlide(); s.background = { color: C.white };
  kicker(s, "Recommendation", C.good); title(s, "Three actions, starting Monday");
  [["Add an order-entry check", "Lines over 5,000 units or £10k need a second confirmation.", "Ops · 1 week · ~£0"],
   ["Call the top-100 list", "Account managers call the highest expected-loss customers. Champions go to senior AMs.", "Sales · weekly · refreshed by the pipeline"],
   ["Automate win-back", "Email offer to the other 1,905 customers with ≥50% churn risk (£462k at risk).", "CRM · 2 weeks"]].forEach(([h, d, o], i) => {
    const y = 1.35 + i * 1.05;
    card(s, 0.5, y, 5.4, 0.9);
    badge(s, 0.68, y + 0.24, i + 1, C.good);
    s.addText(h, { x: 1.25, y: y + 0.08, w: 4.5, h: 0.3, fontFace: B, fontSize: 14, bold: true, color: C.ink, margin: 0, isTextBox: true });
    s.addText(d + "  " + o, { x: 1.25, y: y + 0.38, w: 4.5, h: 0.48, fontFace: B, fontSize: 11, color: C.ink2, margin: 0, valign: "top", isTextBox: true });
  });
  s.addText("Value of the call list (if calls retain X% of its £203k at risk)", { x: 6.3, y: 1.35, w: 3.2, h: 0.5, fontFace: B, fontSize: 12, bold: true, color: C.ink, margin: 0, isTextBox: true });
  s.addTable([
    [{ text: "Retained", options: { bold: true, color: C.ink2 } }, { text: "£ / year", options: { bold: true, color: C.ink2, align: "right" } }],
    ["10%", { text: "£20k", options: { align: "right" } }],
    [{ text: "20% (base case)", options: { bold: true } }, { text: "£41k", options: { bold: true, align: "right", color: C.good } }],
    ["30%", { text: "£61k", options: { align: "right" } }],
  ], { x: 6.3, y: 1.95, w: 3.2, colW: [2.0, 1.2], rowH: 0.42, fontFace: B, fontSize: 13, color: C.ink, border: { type: "solid", pt: 0.75, color: C.line }, margin: 0.06 });
  s.addText("Retention rates are assumptions until A/B-tested (see next phase).", { x: 6.3, y: 3.8, w: 3.2, h: 0.5, fontFace: B, fontSize: 10, italic: true, color: C.muted, margin: 0, isTextBox: true });
  s.addNotes("Show the scenario as a range, not a promise. The A/B test in the next phase turns the assumption into evidence.");
}

// 7 — what we built
{
  const s = pres.addSlide(); s.background = { color: C.white };
  kicker(s, "How it runs", C.good); title(s, "One governed pipeline feeds the dashboard and the AI assistant");
  const steps = [["Land", "Bronze: extract as received, audit columns"], ["Clean", "Silver: typed, deduped; 11.9k rows quarantined with a reason"],
                 ["Shape", "Gold: KPIs, products, RFM segments"], ["Predict", "Churn model, MLflow-tracked, scores in gold"]];
  steps.forEach(([h, d], i) => {
    const x = 0.5 + i * 2.3;
    card(s, x, 1.4, 2.1, 1.55);
    s.addText(h, { x: x + 0.15, y: 1.5, w: 1.8, h: 0.35, fontFace: H, fontSize: 16, bold: true, color: C.ink, margin: 0, isTextBox: true });
    s.addText(d, { x: x + 0.15, y: 1.9, w: 1.8, h: 0.95, fontFace: B, fontSize: 11, color: C.ink2, margin: 0, valign: "top", isTextBox: true });
    if (i < 3) s.addShape(pres.shapes.CHEVRON, { x: x + 2.13, y: 2.05, w: 0.14, h: 0.26, fill: { color: C.muted }, line: { color: C.muted } });
  });
  [["Power BI", "3 pages: overview, leakage, call list. Ratio-of-sums DAX."], ["Ask-the-data assistant", "LangChain text-to-SQL; shows its SQL; read-only guard; scored on a 10-question eval."]].forEach(([h, d], i) => {
    const x = 0.5 + i * 4.6;
    card(s, x, 3.2, 4.4, 1.0, "E7F3EF");
    s.addText(h, { x: x + 0.2, y: 3.28, w: 4.0, h: 0.32, fontFace: B, fontSize: 14, bold: true, color: C.good, margin: 0, isTextBox: true });
    s.addText(d, { x: x + 0.2, y: 3.6, w: 4.0, h: 0.55, fontFace: B, fontSize: 11, color: C.ink2, margin: 0, valign: "top", isTextBox: true });
  });
  s.addText("Databricks Workflows · Unity Catalog (permissions, lineage, documentation) · Delta · PySpark unit-tested in CI · job fails if <90% of rows pass quality checks",
    { x: 0.5, y: 4.45, w: 9, h: 0.6, fontFace: B, fontSize: 11, color: C.muted, margin: 0, isTextBox: true });
  s.addNotes("Tool choices and alternatives (Glue, ADF, Azure OpenAI) are in the ADR. The stack is replaceable; the gold tables are open Delta/Parquet.");
}

// 8 — next phase
{
  const s = pres.addSlide(); s.background = { color: C.ink };
  s.addText("NEXT PHASE", { x: 0.6, y: 0.6, w: 8.8, h: 0.35, fontFace: B, fontSize: 12, bold: true, color: C.gold, charSpacing: 3, margin: 0, isTextBox: true });
  s.addText("Turn assumptions into evidence", { x: 0.6, y: 1.0, w: 8.8, h: 0.8, fontFace: H, fontSize: 34, bold: true, color: C.white, margin: 0, isTextBox: true });
  [["A/B-test the call list", "against a control group to measure real retention uplift"],
   ["Add cost-of-goods data", "so every finding is in margin, not revenue"],
   ["Harden the assistant", "service principal with SELECT-only grants; log and review questions"]].forEach(([h, d], i) => {
    const y = 2.2 + i * 0.85;
    badge(s, 0.6, y, i + 1, C.gold);
    s.addText([{ text: h + "  ", options: { bold: true, color: C.white } }, { text: d, options: { color: "C9D1DB" } }],
      { x: 1.2, y: y - 0.04, w: 8.2, h: 0.5, fontFace: B, fontSize: 16, margin: 0, valign: "middle", isTextBox: true });
  });
  s.addText("Code, notebooks and docs: github.com/Vaibhav2824/retail-revenue-rescue", { x: 0.6, y: 4.85, w: 8.8, h: 0.3, fontFace: B, fontSize: 11, color: "C9D1DB", margin: 0, isTextBox: true });
  s.addNotes("Close by asking what the client would want to test first. It turns the presentation into a conversation.");
}

pres.writeFile({ fileName: OUT }).then(f => console.log("wrote", f));
