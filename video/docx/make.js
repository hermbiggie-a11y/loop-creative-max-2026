// Word version of the narration script: every slide, its timing, and every line the cloned voice says.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, HeadingLevel, WidthType, ShadingType,
  AlignmentType, BorderStyle, Footer, PageNumber, ImageRun,
} = require("docx");
const FRAMES = path.join(__dirname, "frames");
const SHOTS = { "beat1": ["beat1_a", "beat1_b"], "beat2-hero": ["beat2-hero_a", "beat2-hero_b"], "beat2-six": ["beat2-six_a", "beat2-six_b"], "beat3": ["beat3_a", "beat3_b"], "beat4": ["beat4_a", "beat4_b"] };
const img = (n, w) => new ImageRun({ type: "jpg", data: fs.readFileSync(path.join(FRAMES, n + ".jpg")), transformation: { width: w, height: Math.round(w * 9 / 16) } });
const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
function shots(name) {
  const list = SHOTS[name] || [name];
  if (list.length === 1) return [new Paragraph({ keepNext: true, spacing: { after: 120 }, children: [img(list[0], 624)] })];
  return [new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [W / 2, W / 2], borders: { top: none, bottom: none, left: none, right: none, insideHorizontal: none, insideVertical: none },
    rows: [new TableRow({ cantSplit: true, children: list.map((n) => new TableCell({ width: { size: W / 2, type: WidthType.DXA }, borders: { top: none, bottom: none, left: none, right: none }, margins: { top: 0, bottom: 80, left: 0, right: 80 },
      children: [new Paragraph({ keepNext: true, children: [img(n, 306)] })] })) })] }), new Paragraph({ spacing: { after: 60 }, children: [] })];
}

const data = JSON.parse(fs.readFileSync(process.argv[3] || path.join(__dirname, "..", "post", "out", "narration-by-slide.json"), "utf8"));
const OUT = process.argv[2];

const NAMES = {
  title: "Title card", hook: "Cold open: Story resize", built: "Built with AI", diagram: "How it fits together",
  rules: "Four rules", login: "Telegram login (simulated)", "beat1-card": "Beat 1 card", beat1: "Beat 1: the brief",
  "beat2-card": "Beat 2 card", "beat2-hero": "Beat 2: hero + Firefly", ask: "Audience question",
  "beat2-six": "Beat 2: six sizes", "beat3-card": "Beat 3 card", beat3: "Beat 3: rough cut", "spot-card": "Spot card",
  spot: "The 30-second spot", "beat4-card": "Beat 4 card", beat4: "Beat 4: offline", spanish: "Missouri + Spanish line",
  close: "Close + QR codes",
};
const NOTES = {
  spot: "No narration. The spot plays with its own voice-over (your cloned read of the ad script).",
  spanish: "Between the two lines, the 5-second Spanish clip plays in your cloned voice: “Cabana Cold Brew. Sol en una lata. Ya en la Pequeña Habana.”",
  close: "The last 29 seconds are silent so you can take the first question with the QR codes still on screen.",
};

const mmss = (t) => { const s = Math.round(t); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`; };
const len = (s) => (s < 60 ? `${Math.round(s)} s` : mmss(s));
const pct = (a, b) => `${Math.round((100 * a) / b)}%`;
const clean = (t) => t.replace(/Loop\.\.\./g, "Loop").replace(/G P U/g, "GPU").replace(/F F probe/g, "ffprobe")
  .replace(/F F mpeg/g, "ffmpeg").replace(/S R T/g, "SRT").replace(/N D A/g, "NDA");

const FONT = "Calibri";
const INK = "1F2933", MUTED = "5F6B7A", HEAD = "0B3954", ZEBRA = "F3F6F9", LINE = "D5DCE3";
const W = 9360; // 6.5" text width on US Letter with 1" margins
const border = { style: BorderStyle.SINGLE, size: 4, color: LINE };
const borders = { top: border, bottom: border, left: border, right: border };

function cell(text, width, { bold = false, fill, align = AlignmentType.LEFT, color = INK } = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA }, borders,
    shading: fill ? { type: ShadingType.CLEAR, color: "auto", fill } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ alignment: align, children: [new TextRun({ text, bold, color, font: FONT, size: 20 })] })],
  });
}
function table(widths, header, rows, aligns = []) {
  return new Table({
    width: { size: widths.reduce((a, b) => a + b), type: WidthType.DXA }, columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, children: header.map((h, i) => cell(h, widths[i], { bold: true, fill: HEAD, color: "FFFFFF", align: aligns[i] })) }),
      ...rows.map((r, k) => new TableRow({
        cantSplit: true,
        children: r.map((v, i) => cell(v, widths[i], { fill: k % 2 ? ZEBRA : undefined, align: aligns[i], bold: r.bold })),
      })),
    ],
  });
}
const p = (text, opts = {}) => new Paragraph({ spacing: { after: 120 }, ...opts.para,
  children: [new TextRun({ text, font: FONT, size: opts.size || 22, color: opts.color || INK, bold: opts.bold, italics: opts.italics })] });

const totalTalk = data.reduce((a, s) => a + s.talk, 0);
const totalShow = data[data.length - 1].end;
const lines = data.reduce((a, s) => a + s.lines.length, 0);

const children = [
  new Paragraph({ heading: HeadingLevel.TITLE, spacing: { after: 80 }, children: [new TextRun({ text: "Loop Creative — Narration Script", font: FONT })] }),
  p("Adobe MAX 2026 · Logan Lawler · narrated backup video", { color: MUTED }),
  p(`What is on screen and what your cloned voice says on each slide of Golden\\loop-backup-20min-narrated.mp4: ${lines} lines, ${mmss(totalTalk)} of talking across ${mmss(totalShow)} on screen (${pct(totalTalk, totalShow)}). Talking time counts narration only; the spot’s own voice-over and the 5-second Spanish clip are not included.`),
  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: "Summary by slide", font: FONT })] }),
  table([500, 3460, 1700, 1200, 1300, 1200],
    ["#", "Slide", "On screen", "Shown", "Talking", "Share"],
    [...data.map((s, i) => [String(i + 1), NAMES[s.name], `${mmss(s.start)}–${mmss(s.end)}`, len(s.show), len(s.talk), pct(s.talk, s.show)]),
     Object.assign(["", "Total", `0:00–${mmss(totalShow)}`, mmss(totalShow), mmss(totalTalk), pct(totalTalk, totalShow)], { bold: true })],
    [AlignmentType.RIGHT, AlignmentType.LEFT, AlignmentType.LEFT, AlignmentType.RIGHT, AlignmentType.RIGHT, AlignmentType.RIGHT]),
  new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [new TextRun({ text: "Slide by slide", font: FONT })] }),
];

data.forEach((s, i) => {
  children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, keepNext: true, pageBreakBefore: i > 0, spacing: { before: 0, after: 60 },
    children: [new TextRun({ text: `${i + 1}. ${NAMES[s.name]}`, font: FONT }), new TextRun({ text: `   ${mmss(s.start)}–${mmss(s.end)}`, font: FONT, color: MUTED })] }));
  children.push(p(`Shown ${len(s.show)} · talking ${len(s.talk)} (${pct(s.talk, s.show)})`, { color: MUTED, size: 20, para: { keepNext: true } }));
  children.push(...shots(s.name));
  if (s.lines.length) {
    children.push(table([800, 800, 7760], ["At", "Length", "What is said"],
      s.lines.map(([t, d, txt]) => [mmss(t), len(d), clean(txt)]),
      [AlignmentType.LEFT, AlignmentType.RIGHT, AlignmentType.LEFT]));
  }
  if (NOTES[s.name]) children.push(p(NOTES[s.name], { italics: true, color: MUTED, size: 20, para: { spacing: { before: 80 } } }));
});

const doc = new Document({
  creator: "Logan Lawler", title: "Loop Creative — Narration Script",
  styles: {
    default: { document: { run: { font: FONT, size: 22, color: INK } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", run: { size: 48, bold: true, color: HEAD } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", run: { size: 30, bold: true, color: HEAD }, paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", run: { size: 24, bold: true, color: INK }, paragraph: { outlineLevel: 1 } },
    ],
  },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: "Loop Creative narration script · page ", font: FONT, size: 18, color: MUTED }), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: MUTED })] })] }) },
    children,
  }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(OUT, b); console.log("wrote", OUT, b.length); });
