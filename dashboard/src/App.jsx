import { useMemo, useState } from "react";

const units = [
  { id: 1, title: "Lexical Analysis", short: "Lexical", hours: 7, avg: 14.5, color: "#7c8cff", topics: [
    ["Finite Automata", [["2025", "Q2(a)", 5, "A"], ["2024", "Q1(b)", 5, "A"]]],
    ["Lexical Analyzer", [["2023", "Q4", 4, "B"], ["2022", "Q2(b)", 5, "A"]]],
    ["Regular Expressions", [["2021", "Q6", 3, "B"]]],
  ]},
  { id: 2, title: "Syntax Analysis", short: "Syntax", hours: 10, avg: 20.25, color: "#e5a84b", topics: [
    ["CFG & Ambiguity", [["2025", "Q3(a)", 5, "A"], ["2023", "Q1(c)", 5, "A"]]],
    ["Top-down Parsing", [["2024", "Q3(b)", 5, "A"], ["2022", "Q5", 4, "B"]]],
    ["Bottom-up Parsing", [["2025", "Q5", 4, "B"], ["2021", "Q3(a)", 5, "A"], ["2020", "Q6", 3, "B"]]],
  ]},
  { id: 3, title: "Semantic Analysis", short: "Semantic", hours: 8, avg: 16.75, color: "#48c5a5", topics: [
    ["Type Checking", [["2025", "Q4(a)", 5, "A"], ["2022", "Q3(b)", 5, "A"]]],
    ["Symbol Tables", [["2024", "Q6", 3, "B"], ["2021", "Q4", 4, "B"]]],
    ["Syntax-directed Translation", [["2023", "Q4(a)", 5, "A"]]],
  ]},
  { id: 4, title: "Code Generation & Optimization", short: "Codegen", hours: 11, avg: 18.5, color: "#d879a9", topics: [
    ["Intermediate Code", [["2025", "Q6", 4, "B"], ["2023", "Q5(a)", 5, "A"]]],
    ["Code Optimization", [["2024", "Q5(a)", 5, "A"], ["2022", "Q6", 4, "B"]]],
    ["Code Generation", [["2021", "Q5(b)", 5, "A"], ["2020", "Q3", 3, "B"]]],
  ]},
];

const metrics = {
  marks: ["Avg Exam Marks", (u) => u.avg, " marks"],
  roi: ["Marks / Credit Hr", (u) => u.avg / u.hours, " marks/hr"],
  questions: ["Question Count", (u) => u.topics.reduce((n, [, qs]) => n + qs.length, 0), " questions"],
};

const allQuestions = (unit) => unit.topics.flatMap(([topic, questions]) => questions.map((q) => ({ topic, year: q[0], number: q[1], marks: q[2], section: q[3] })));

function Card({ label, value, detail, color, icon }) {
  return <article className="stat-card" style={{ "--accent": color }}><div className="card-top"><span>{label}</span><b>{icon}</b></div><strong>{value}</strong><small>{detail}</small></article>;
}

export default function App() {
  const [metric, setMetric] = useState("marks");
  const [selectedId, setSelectedId] = useState(2);
  const [unitFilter, setUnitFilter] = useState("all");
  const [section, setSection] = useState("all");
  const selected = units.find((u) => u.id === selectedId) || units[0];
  const highest = units.reduce((a, b) => a.avg > b.avg ? a : b);
  const roi = units.reduce((a, b) => a.avg / a.hours > b.avg / b.hours ? a : b);
  const visibleUnits = unitFilter === "all" ? units : units.filter((u) => u.id === Number(unitFilter));
  const [metricLabel, metricValue, metricSuffix] = metrics[metric];
  const max = Math.max(...units.map(metricValue));
  const questions = useMemo(() => allQuestions(selected).filter((q) => section === "all" || q.section === section), [selected, section]);

  const selectUnit = (id) => { setSelectedId(id); setUnitFilter("all"); };

  return <main className="shell">
    <header className="topbar"><div className="brand"><span className="mark">•</span><div><b>study<span>map</span></b><small>Compiler Design & Construction</small></div></div><div className="top-meta"><i /> EXAM PREP DASHBOARD <em>•</em> 2020–2025 PYQs</div></header>
    <section className="hero"><div><p className="eyebrow">EXAM WEIGHTAGE & ROI ANALYSIS</p><h1>Study what moves<br /><em>your score.</em></h1><p className="intro">A data-backed view of the Compiler Design syllabus, built from recurring past-paper patterns and realistic study effort.</p></div><aside><span /> <div><b>How to read this</b><br />ROI shows expected marks earned per focused study hour.</div></aside></section>
    <section className="stats"><Card label="Highest yield unit" value={`Unit ${highest.id}`} detail={`${highest.title} · ${highest.avg.toFixed(1)} avg marks`} color={highest.color} icon="↗" /><Card label="Top ROI per hour" value={(roi.avg / roi.hours).toFixed(2)} detail={`${roi.title} · marks / credit hr`} color="#48c5a5" icon="⚡" /><Card label="Selected unit" value={`Unit ${selected.id}`} detail={`${selected.title} · ${selected.hours} credit hours`} color={selected.color} icon="◉" /></section>
    <section className="panel"><div className="panel-head"><div><p className="eyebrow">WEIGHTAGE MAP</p><h2>Where your hours pay back</h2></div><div className="controls"><label>Unit <select value={unitFilter} onChange={(e) => { setUnitFilter(e.target.value); if (e.target.value !== "all") setSelectedId(Number(e.target.value)); }}><option value="all">All units</option>{units.map((u) => <option key={u.id} value={u.id}>Unit {u.id}</option>)}</select></label><div className="segmented">{Object.entries(metrics).map(([key, [label]]) => <button className={metric === key ? "active" : ""} key={key} onClick={() => setMetric(key)}>{label}</button>)}</div></div></div><div className="chart-caption"><span>{metricLabel}</span><span>Click a bar to inspect its question history</span></div><div className="bars">{visibleUnits.map((u) => <button className={`bar-row ${u.id === selectedId ? "selected" : ""}`} key={u.id} onClick={() => selectUnit(u.id)}><span className="bar-label"><b>0{u.id}</b>{u.title}</span><span className="track"><i style={{ width: `${metricValue(u) / max * 100}%`, "--bar": u.color }} /><strong>{metric === "questions" ? metricValue(u) : metricValue(u).toFixed(1)}{metricSuffix}</strong></span></button>)}</div><div className="legend"><span>● Selected unit</span><span>● Other units</span></div></section>
    <section className="panel detail"><div className="detail-head"><div className="unit-title"><b style={{ color: selected.color }}>0{selected.id}</b><div><p className="eyebrow">SELECTED UNIT</p><h2>{selected.title}</h2><small>Recurring concepts, mapped to actual exam questions</small></div></div><div className="metrics"><div><span>STUDY HOURS</span><b>{selected.hours}<small> hrs</small></b></div><div><span>AVG MARKS</span><b>{selected.avg.toFixed(1)}<small> marks</small></b></div><div><span>ROI</span><b>{(selected.avg / selected.hours).toFixed(2)}<small> / hr</small></b></div></div></div><div className="questions-head"><div><p className="eyebrow">PAST QUESTIONS</p><h3>What has actually appeared</h3></div><div className="filters">{[["all", "All sections"], ["A", "Section A · Long"], ["B", "Section B · Short"]].map(([key, label]) => <button className={section === key ? "active" : ""} onClick={() => setSection(key)} key={key}>{label}</button>)}</div></div><div className="topics">{selected.topics.map(([topic]) => { const qs = questions.filter((q) => q.topic === topic); return qs.length ? <article key={topic}><div className="topic-head"><i style={{ background: selected.color }} /><b>{topic}</b><small>{qs.length} PYQs</small></div><div className="badges">{qs.map((q) => <span className={`badge ${q.section === "A" ? "long" : "short"}`} key={`${q.year}${q.number}`}><b>{q.year}</b><span>{q.number}</span><strong>{q.marks}m</strong></span>)}</div></article> : null; })}</div></section>
    <section className="panel syllabus"><div className="syllabus-heading"><div><p className="eyebrow">COMPLETE QUESTION BANK</p><h2>Full syllabus, in order</h2><small>Unit-wise topics and every mapped past question, following the syllabus sequence.</small></div><span className="question-total">{units.reduce((total, unit) => total + allQuestions(unit).length, 0)} questions</span></div><div className="unit-list">{units.map((unit) => { const unitQuestions = allQuestions(unit).filter((q) => section === "all" || q.section === section); return <article className={`unit-block ${unit.id === selected.id ? "current" : ""}`} key={unit.id}><button className="unit-block-heading" onClick={() => selectUnit(unit.id)}><span className="unit-index" style={{ color: unit.color }}>0{unit.id}</span><span><b>{unit.title}</b><small>{unit.hours} credit hours · {unit.avg.toFixed(1)} avg marks</small></span><strong>{unitQuestions.length} PYQs <em>↗</em></strong></button><div className="unit-question-grid">{unit.topics.map(([topic]) => { const topicQuestions = unitQuestions.filter((q) => q.topic === topic); return topicQuestions.length ? <div className="ordered-topic" key={topic}><div><i style={{ background: unit.color }} /><b>{topic}</b></div><div className="badges">{topicQuestions.map((q) => <span className={`badge ${q.section === "A" ? "long" : "short"}`} key={`${unit.id}${q.year}${q.number}`}><b>{q.year}</b><span>{q.number}</span><strong>{q.marks}m</strong></span>)}</div></div> : null; })}</div></article>; })}</div></section>
    <footer><span>✦</span><div><p className="eyebrow">KEY EXAM STRATEGY</p><b>Start with Syntax Analysis, then lock in Lexical Analysis.</b><small> Together they account for the highest recurring weightage and the best return on your first 17 study hours.</small></div><strong>↗</strong></footer><div className="footnote">Built from syllabus mapping + 30 past-paper questions <span>·</span> Updated for 2025 exam pattern</div>
  </main>;
}
