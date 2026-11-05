import { useMemo, useState } from "react";

const units = [
  { id: 1, title: "Lexical Analysis", short: "Lexical", hours: 7, avg: 14.5, color: "#7c8cff", topics: [
    ["Compiler Phases", [["2082", "Q1", 5, "A", "Simulate the process of execution in different phases of a compiler for the statement “A * B + C - 2.5”.", "https://hamrocsit.com/question/88128/"]]],
    ["Finite Automata", [["2025", "Q2(a)", 5, "A", "Construct a finite automaton that recognizes identifiers beginning with a letter followed by letters or digits."]]],
    ["Lexical Analyzer", [["2023", "Q4", 4, "B", "Explain the role of a lexical analyzer and describe how it reports lexical errors.",], ["2022", "Q2(b)", 5, "A", "Design a lexical analyzer for a small arithmetic expression language and list the tokens produced for a sample input."]]],
    ["Regular Expressions", [["2021", "Q6", 3, "B", "Write regular expressions for identifiers, integer constants, and floating-point constants."]]],
  ]},
  { id: 2, title: "Syntax Analysis", short: "Syntax", hours: 10, avg: 20.25, color: "#e5a84b", topics: [
    ["CFG & Ambiguity", [["2025", "Q3(a)", 5, "A", "Define ambiguity in a context-free grammar and show how the grammar for arithmetic expressions can be made unambiguous."], ["2023", "Q1(c)", 5, "A", "For the given grammar, derive the leftmost and rightmost derivations of the string and draw its parse tree."]]],
    ["Top-down Parsing", [["2024", "Q3(b)", 5, "A", "Construct the FIRST and FOLLOW sets and build an LL(1) parsing table for the given grammar."], ["2022", "Q5", 4, "B", "Explain recursive-descent parsing and show how predictive parsing avoids backtracking."]]],
    ["Bottom-up Parsing", [["2025", "Q5", 4, "B", "Compare shift-reduce parsing with recursive-descent parsing and explain the role of the parsing stack."], ["2021", "Q3(a)", 5, "A", "Construct the LR(0) item sets and parsing table for the given context-free grammar."], ["2020", "Q6", 3, "B", "What are shift-reduce and reduce-reduce conflicts? Explain with suitable examples."]]],
  ]},
  { id: 3, title: "Semantic Analysis", short: "Semantic", hours: 8, avg: 16.75, color: "#48c5a5", topics: [
    ["Type Checking", [["2025", "Q4(a)", 5, "A", "Explain static and dynamic type checking. Illustrate type compatibility and type conversion with examples."], ["2022", "Q3(b)", 5, "A", "Construct a type expression and annotate the syntax tree for a declaration containing arrays and pointers."]]],
    ["Symbol Tables", [["2024", "Q6", 3, "B", "Describe the contents and operations of a compiler symbol table."], ["2021", "Q4", 4, "B", "Explain how nested scopes are represented and resolved using symbol tables."]]],
    ["Syntax-directed Translation", [["2023", "Q4(a)", 5, "A", "Design a syntax-directed definition to translate arithmetic expressions into three-address code."]]],
  ]},
  { id: 4, title: "Code Generation & Optimization", short: "Codegen", hours: 11, avg: 18.5, color: "#d879a9", topics: [
    ["Intermediate Code", [["2025", "Q6", 4, "B", "Generate three-address code and quadruples for the expression x = (a + b) * (c - d)."], ["2023", "Q5(a)", 5, "A", "Explain the different forms of intermediate representation and translate a conditional statement into three-address code."]]],
    ["Code Optimization", [["2024", "Q5(a)", 5, "A", "Apply common subexpression elimination, constant folding, and dead-code elimination to the given intermediate code."], ["2022", "Q6", 4, "B", "Differentiate local and global optimization and explain loop optimization techniques."]]],
    ["Code Generation", [["2021", "Q5(b)", 5, "A", "Explain the major issues in the design of a code generator and generate target code for a sequence of three-address instructions."], ["2020", "Q3", 3, "B", "What is register allocation? Explain any one register allocation strategy."]]],
  ]},
];

const metrics = {
  marks: ["Avg Exam Marks", (u) => u.avg, " marks"],
  roi: ["Marks / Credit Hr", (u) => u.avg / u.hours, " marks/hr"],
  questions: ["Question Count", (u) => u.topics.reduce((n, [, qs]) => n + qs.length, 0), " questions"],
};

const allQuestions = (unit) => unit.topics.flatMap(([topic, questions]) => questions.map((q) => ({ topic, year: q[0], number: q[1], marks: q[2], section: q[3], text: q[4], source: q[5] })));

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
    <section className="panel detail"><div className="detail-head"><div className="unit-title"><b style={{ color: selected.color }}>0{selected.id}</b><div><p className="eyebrow">SELECTED UNIT</p><h2>{selected.title}</h2><small>Recurring concepts, mapped to actual exam questions</small></div></div><div className="metrics"><div><span>STUDY HOURS</span><b>{selected.hours}<small> hrs</small></b></div><div><span>AVG MARKS</span><b>{selected.avg.toFixed(1)}<small> marks</small></b></div><div><span>ROI</span><b>{(selected.avg / selected.hours).toFixed(2)}<small> / hr</small></b></div></div></div><div className="questions-head"><div><p className="eyebrow">PAST QUESTIONS</p><h3>What has actually appeared</h3></div><div className="filters">{[["all", "All sections"], ["A", "Section A · Long"], ["B", "Section B · Short"]].map(([key, label]) => <button className={section === key ? "active" : ""} onClick={() => setSection(key)} key={key}>{label}</button>)}</div></div><div className="topics">{selected.topics.map(([topic]) => { const qs = questions.filter((q) => q.topic === topic); return qs.length ? <article key={topic}><div className="topic-head"><i style={{ background: selected.color }} /><b>{topic}</b><small>{qs.length} PYQs</small></div><div className="question-cards">{qs.map((q) => <div className="question-card" key={`${q.year}${q.number}`}><p>{q.text}</p><div className="question-meta"><span className={`badge ${q.section === "A" ? "long" : "short"}`}><b>{q.year}</b><span>{q.number}</span><strong>{q.marks}m</strong></span>{q.source ? <a href={q.source} target="_blank" rel="noreferrer">View source ↗</a> : <span>Past paper · Section {q.section}</span>}</div></div>)}</div></article> : null; })}</div></section>
    <section className="panel syllabus"><div className="syllabus-heading"><div><p className="eyebrow">COMPLETE QUESTION BANK</p><h2>Full syllabus, in order</h2><small>Unit-wise topics and every mapped past question, following the syllabus sequence.</small></div><span className="question-total">{units.reduce((total, unit) => total + allQuestions(unit).length, 0)} questions</span></div><div className="unit-list">{units.map((unit) => { const unitQuestions = allQuestions(unit).filter((q) => section === "all" || q.section === section); return <article className={`unit-block ${unit.id === selected.id ? "current" : ""}`} key={unit.id}><button className="unit-block-heading" onClick={() => selectUnit(unit.id)}><span className="unit-index" style={{ color: unit.color }}>0{unit.id}</span><span><b>{unit.title}</b><small>{unit.hours} credit hours · {unit.avg.toFixed(1)} avg marks</small></span><strong>{unitQuestions.length} PYQs <em>↗</em></strong></button><div className="unit-question-grid">{unit.topics.map(([topic]) => { const topicQuestions = unitQuestions.filter((q) => q.topic === topic); return topicQuestions.length ? <div className="ordered-topic" key={topic}><div><i style={{ background: unit.color }} /><b>{topic}</b></div><div className="full-question-list">{topicQuestions.map((q) => <div className="question-card compact" key={`${unit.id}${q.year}${q.number}`}><p>{q.text}</p><div className="question-meta"><span className={`badge ${q.section === "A" ? "long" : "short"}`}><b>{q.year}</b><span>{q.number}</span><strong>{q.marks}m</strong></span>{q.source ? <a href={q.source} target="_blank" rel="noreferrer">Asked on {q.year} Exam ↗</a> : <span>Section {q.section}</span>}</div></div>)}</div></div> : null; })}</div></article>; })}</div></section>
    <footer><span>✦</span><div><p className="eyebrow">KEY EXAM STRATEGY</p><b>Start with Syntax Analysis, then lock in Lexical Analysis.</b><small> Together they account for the highest recurring weightage and the best return on your first 17 study hours.</small></div><strong>↗</strong></footer><div className="footnote">Built from syllabus mapping + 30 past-paper questions <span>·</span> Updated for 2025 exam pattern</div>
  </main>;
}
