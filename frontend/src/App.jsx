import { useState } from "react";

const DEFAULT_CODE = `class Animal {
    int age;
    void Init() {
        this.age = 0;
    }
}
class Cow extends Animal {
    void Moo() {
        Print("Moo");
    }
}
int main() {
    Cow c;
    c = New(Cow);
    c.Init();
    c.Moo();
    return 0;
}`;

const TOKEN_COLORS = {
  KEYWORD: { bg: "#dbeafe", text: "#1e40af", border: "#bfdbfe" },
  IDENT: { bg: "#f3f4f6", text: "#374151", border: "#e5e7eb" },
  OP: { bg: "#fef3c7", text: "#92400e", border: "#fde68a" },
  PUNCT: { bg: "#f3f4f6", text: "#6b7280", border: "#e5e7eb" },
  INT_CONST: { bg: "#dcfce7", text: "#166534", border: "#bbf7d0" },
  DOUBLE_CONST: { bg: "#dcfce7", text: "#166534", border: "#bbf7d0" },
  BOOL_CONST: { bg: "#fce7f3", text: "#9d174d", border: "#fbcfe8" },
  STRING_CONST: { bg: "#ede9fe", text: "#6d28d9", border: "#ddd6fe" },
  EOF: { bg: "#f9fafb", text: "#9ca3af", border: "#f3f4f6" },
};

function getTokenColor(type) {
  if (type.startsWith("KEYWORD")) return TOKEN_COLORS.KEYWORD;
  if (type.startsWith("OP")) return TOKEN_COLORS.OP;
  if (type.startsWith("PUNCT")) return TOKEN_COLORS.PUNCT;
  return TOKEN_COLORS[type] || TOKEN_COLORS.EOF;
}

function getTokenCategory(type) {
  if (type.startsWith("KEYWORD")) return "keyword";
  if (type === "IDENT") return "ident";
  if (type.startsWith("OP")) return "operator";
  if (type.startsWith("PUNCT")) return "punct";
  if (type.includes("CONST")) return "literal";
  return "other";
}

function getTokenDisplay(t) {
  if (t.type.startsWith("KEYWORD")) return t.value;
  if (t.type.startsWith("OP")) return t.value;
  if (t.type.startsWith("PUNCT")) return t.value;
  if (t.type === "IDENT") return t.value;
  if (t.type === "STRING_CONST") return `"${t.value}"`;
  if (t.type === "EOF") return "EOF";
  return t.value;
}

// ── Sub-components ─────────────────────────────────────────────────────────

function Badge({ children, color = "#6b7280" }) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "2px 8px",
        borderRadius: 999,
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: "0.04em",
        background: color + "22",
        color,
        border: `1px solid ${color}44`,
      }}
    >
      {children}
    </span>
  );
}

function SectionHeader({ title, count, color = "#374151" }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        marginBottom: 14,
      }}
    >
      <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600, color }}>
        {title}
      </h3>
      {count !== undefined && (
        <span
          style={{
            background: "#f3f4f6",
            color: "#6b7280",
            fontSize: 12,
            fontWeight: 600,
            borderRadius: 999,
            padding: "1px 8px",
            border: "1px solid #e5e7eb",
          }}
        >
          {count}
        </span>
      )}
    </div>
  );
}

function EmptyState({ msg }) {
  return (
    <div
      style={{
        textAlign: "center",
        padding: "40px 20px",
        color: "#9ca3af",
        fontSize: 14,
      }}
    >
      <div style={{ fontSize: 32, marginBottom: 8 }}>—</div>
      {msg}
    </div>
  );
}

function ErrorList({ errors }) {
  if (!errors || errors.length === 0) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "10px 14px",
          borderRadius: 8,
          background: "#f0fdf4",
          border: "1px solid #bbf7d0",
          color: "#166534",
          fontSize: 13,
          fontWeight: 500,
        }}
      >
        <span>✓</span> No errors
      </div>
    );
  }
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      {errors.map((e, i) => {
        const msg = typeof e === "string" ? e : e.message;
        const line = typeof e === "object" ? e.line : null;
        const col = typeof e === "object" ? e.col : null;
        return (
          <div
            key={i}
            style={{
              padding: "8px 12px",
              borderRadius: 8,
              background: "#fef2f2",
              border: "1px solid #fecaca",
              color: "#991b1b",
              fontSize: 13,
              display: "flex",
              gap: 10,
              alignItems: "flex-start",
            }}
          >
            <span style={{ flexShrink: 0, fontWeight: 700 }}>✕</span>
            <div>
              {line != null && (
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 700,
                    color: "#b91c1c",
                    background: "#fee2e2",
                    borderRadius: 4,
                    padding: "0 5px",
                    marginRight: 6,
                  }}
                >
                  line {line}
                  {col ? `, col ${col}` : ""}
                </span>
              )}
              {msg}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Tokens tab ─────────────────────────────────────────────────────────────

function TokensTab({ tokens, summary }) {
  const [filter, setFilter] = useState("all");
  const categories = [
    "all",
    "keyword",
    "ident",
    "operator",
    "punct",
    "literal",
  ];

  const filtered =
    filter === "all"
      ? tokens.filter((t) => t.type !== "EOF")
      : tokens.filter((t) => getTokenCategory(t.type) === filter);

  const summaryItems = [
    { label: "Keywords", key: "keyword", color: "#1d4ed8" },
    { label: "Identifiers", key: "identifier", color: "#374151" },
    { label: "Operators", key: "operator", color: "#92400e" },
    { label: "Punctuation", key: "punctuation", color: "#6b7280" },
    { label: "Literals", key: "literal", color: "#166534" },
  ];

  return (
    <div>
      <SectionHeader
        title="Lexical Analysis"
        count={tokens.filter((t) => t.type !== "EOF").length + " tokens"}
      />

      {/* Summary bar */}
      <div
        style={{
          display: "flex",
          gap: 10,
          flexWrap: "wrap",
          marginBottom: 16,
        }}
      >
        {summaryItems.map((s) => (
          <div
            key={s.key}
            style={{
              background: "#f9fafb",
              border: "1px solid #e5e7eb",
              borderRadius: 8,
              padding: "6px 14px",
              fontSize: 13,
            }}
          >
            <span style={{ color: s.color, fontWeight: 700 }}>
              {summary?.[s.key] ?? 0}
            </span>
            <span style={{ color: "#6b7280", marginLeft: 5 }}>{s.label}</span>
          </div>
        ))}
      </div>

      {/* Filter pills */}
      <div
        style={{ display: "flex", gap: 6, marginBottom: 14, flexWrap: "wrap" }}
      >
        {categories.map((c) => (
          <button
            key={c}
            onClick={() => setFilter(c)}
            style={{
              padding: "4px 12px",
              borderRadius: 999,
              fontSize: 12,
              fontWeight: 500,
              cursor: "pointer",
              border: "1px solid",
              borderColor: filter === c ? "#3b82f6" : "#e5e7eb",
              background: filter === c ? "#eff6ff" : "#fff",
              color: filter === c ? "#1d4ed8" : "#6b7280",
            }}
          >
            {c === "all" ? "All" : c.charAt(0).toUpperCase() + c.slice(1)}
          </button>
        ))}
      </div>

      {/* Token grid */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
        {filtered.map((t, i) => {
          const col = getTokenColor(t.type);
          return (
            <div
              key={i}
              title={`${t.type} | line ${t.line}, col ${t.column}`}
              style={{
                display: "inline-flex",
                flexDirection: "column",
                padding: "4px 10px",
                borderRadius: 7,
                background: col.bg,
                border: `1px solid ${col.border}`,
                cursor: "default",
                userSelect: "none",
              }}
            >
              <span
                style={{
                  fontSize: 13,
                  fontWeight: 600,
                  color: col.text,
                  lineHeight: 1.4,
                }}
              >
                {getTokenDisplay(t)}
              </span>
              <span
                style={{
                  fontSize: 10,
                  color: col.text + "99",
                  lineHeight: 1.2,
                }}
              >
                {t.type
                  .replace("KEYWORD_", "")
                  .replace("PUNCT_", "")
                  .replace("OP_", "")}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Grammar sets tab ───────────────────────────────────────────────────────

function GrammarTab({ grammar }) {
  const [search, setSearch] = useState("");
  const [view, setView] = useState("first");

  const data = grammar[view] ?? {};
  const entries = Object.entries(data)
    .filter(([k]) => !search || k.toLowerCase().includes(search.toLowerCase()))
    .sort(([a], [b]) => a.localeCompare(b));

  return (
    <div>
      <SectionHeader title="Grammar — FIRST & FOLLOW Sets" />

      <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
        {["first", "follow"].map((v) => (
          <button
            key={v}
            onClick={() => setView(v)}
            style={{
              padding: "5px 16px",
              borderRadius: 999,
              fontSize: 13,
              fontWeight: 600,
              cursor: "pointer",
              border: "1px solid",
              borderColor: view === v ? "#3b82f6" : "#e5e7eb",
              background: view === v ? "#eff6ff" : "#fff",
              color: view === v ? "#1d4ed8" : "#6b7280",
            }}
          >
            {view === v ? "▶ " : ""}
            {v.toUpperCase()}(·)
          </button>
        ))}
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter non-terminals…"
          style={{
            marginLeft: "auto",
            padding: "5px 12px",
            borderRadius: 8,
            border: "1px solid #e5e7eb",
            fontSize: 13,
            outline: "none",
            minWidth: 180,
          }}
        />
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {entries.map(([nt, set]) => (
          <div
            key={nt}
            style={{
              display: "flex",
              gap: 12,
              padding: "8px 12px",
              borderRadius: 8,
              background: "#f9fafb",
              border: "1px solid #f3f4f6",
              alignItems: "flex-start",
            }}
          >
            <code
              style={{
                minWidth: 180,
                fontWeight: 700,
                color: "#1d4ed8",
                fontSize: 13,
                flexShrink: 0,
                paddingTop: 1,
              }}
            >
              {nt}
            </code>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
              {(Array.isArray(set) ? set : []).map((sym, i) => (
                <span
                  key={i}
                  style={{
                    padding: "1px 8px",
                    borderRadius: 5,
                    fontSize: 12,
                    background:
                      sym === "$"
                        ? "#fef3c7"
                        : sym === "epsilon" || sym === "ε"
                          ? "#f3f4f6"
                          : "#ede9fe",
                    color:
                      sym === "$"
                        ? "#92400e"
                        : sym === "epsilon" || sym === "ε"
                          ? "#9ca3af"
                          : "#6d28d9",
                    fontFamily: "monospace",
                    fontWeight: 500,
                    border: "1px solid",
                    borderColor:
                      sym === "$"
                        ? "#fde68a"
                        : sym === "epsilon" || sym === "ε"
                          ? "#e5e7eb"
                          : "#ddd6fe",
                  }}
                >
                  {sym === "epsilon" ? "ε" : sym}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── RD parse tree tab ──────────────────────────────────────────────────────

function TreeNode({ node, depth = 0 }) {
  const [open, setOpen] = useState(depth < 3);
  if (!node || typeof node !== "object") return null;

  const label = node.node || "?";
  const name = node.name ? ` : ${node.name}` : "";
  const children = node.children || [];
  const hasKids = children.length > 0;
  const isLeaf = !hasKids;

  return (
    <div
      style={{
        marginLeft: depth === 0 ? 0 : 18,
        borderLeft: depth > 0 ? "1.5px solid #e5e7eb" : "none",
      }}
    >
      <div
        onClick={() => hasKids && setOpen(!open)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          padding: "3px 8px",
          borderRadius: 6,
          cursor: hasKids ? "pointer" : "default",
          userSelect: "none",
          color: isLeaf ? "#6b7280" : "#111827",
          fontWeight: isLeaf ? 400 : 600,
          fontSize: 13,
        }}
      >
        {hasKids && (
          <span style={{ color: "#9ca3af", fontSize: 10, width: 10 }}>
            {open ? "▾" : "▸"}
          </span>
        )}
        {!hasKids && <span style={{ width: 10, display: "inline-block" }} />}
        <span
          style={{
            background: isLeaf ? "#f9fafb" : "#eff6ff",
            color: isLeaf ? "#6b7280" : "#1d4ed8",
            padding: "1px 7px",
            borderRadius: 5,
            fontFamily: "monospace",
            border: `1px solid ${isLeaf ? "#f3f4f6" : "#bfdbfe"}`,
            fontSize: 12,
          }}
        >
          {label}
        </span>
        {name && <span style={{ color: "#6b7280", fontSize: 12 }}>{name}</span>}
      </div>
      {open &&
        hasKids &&
        children.map((child, i) => (
          <TreeNode key={i} node={child} depth={depth + 1} />
        ))}
    </div>
  );
}

function RDTab({ rd }) {
  if (!rd) return <EmptyState msg="No RD parse result." />;
  return (
    <div>
      <SectionHeader title="Recursive Descent Parse Tree" />
      <ErrorList errors={rd.errors} />
      {rd.tree && (
        <div
          style={{
            marginTop: 14,
            padding: "12px 8px",
            borderRadius: 10,
            background: "#f9fafb",
            border: "1px solid #f3f4f6",
            maxHeight: 520,
            overflowY: "auto",
          }}
        >
          <TreeNode node={rd.tree} depth={0} />
        </div>
      )}
    </div>
  );
}

// ── LL(1) trace tab ────────────────────────────────────────────────────────

const ACTION_STYLE = {
  predict: { bg: "#eff6ff", text: "#1d4ed8", border: "#bfdbfe" },
  match: { bg: "#f0fdf4", text: "#166534", border: "#bbf7d0" },
  error: { bg: "#fef2f2", text: "#991b1b", border: "#fecaca" },
  accept: { bg: "#f0fdf4", text: "#065f46", border: "#6ee7b7" },
  default: { bg: "#f9fafb", text: "#374151", border: "#e5e7eb" },
};

function TraceRow({ step }) {
  const s = ACTION_STYLE[step.action] || ACTION_STYLE.default;
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "42px 1fr 1fr",
        gap: 0,
        borderBottom: "1px solid #f3f4f6",
        fontSize: 12,
        fontFamily: "monospace",
      }}
    >
      <div
        style={{
          padding: "6px 10px",
          color: "#9ca3af",
          fontWeight: 600,
          background: "#fafafa",
          borderRight: "1px solid #f3f4f6",
          display: "flex",
          alignItems: "center",
        }}
      >
        {step.step}
      </div>
      <div
        style={{
          padding: "6px 10px",
          color: "#374151",
          borderRight: "1px solid #f3f4f6",
          wordBreak: "break-all",
          lineHeight: 1.5,
          display: "flex",
          alignItems: "center",
        }}
      >
        {step.input}
      </div>
      <div
        style={{
          padding: "6px 10px",
          background: s.bg,
          color: s.text,
          wordBreak: "break-word",
          lineHeight: 1.5,
        }}
      >
        {step.action_label}
      </div>
    </div>
  );
}

function LL1Tab({ ll1 }) {
  const [page, setPage] = useState(0);
  const [filter, setFilter] = useState("all");
  if (!ll1) return <EmptyState msg="No LL(1) result." />;

  const PAGE_SIZE = 50;
  const filtered =
    filter === "all" ? ll1.trace : ll1.trace.filter((s) => s.action === filter);
  const pages = Math.ceil(filtered.length / PAGE_SIZE);
  const slice = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <div>
      <SectionHeader
        title="LL(1) Predictive Parser Trace"
        count={ll1.trace.length + " steps"}
      />
      <ErrorList errors={ll1.errors} />

      <div
        style={{
          display: "flex",
          gap: 6,
          marginTop: 14,
          marginBottom: 10,
          flexWrap: "wrap",
        }}
      >
        {["all", "predict", "match", "error", "accept"].map((f) => (
          <button
            key={f}
            onClick={() => {
              setFilter(f);
              setPage(0);
            }}
            style={{
              padding: "3px 12px",
              borderRadius: 999,
              fontSize: 11,
              fontWeight: 600,
              cursor: "pointer",
              border: "1px solid",
              borderColor:
                filter === f ? ACTION_STYLE[f]?.border || "#e5e7eb" : "#e5e7eb",
              background:
                filter === f ? ACTION_STYLE[f]?.bg || "#f9fafb" : "#fff",
              color:
                filter === f ? ACTION_STYLE[f]?.text || "#374151" : "#6b7280",
            }}
          >
            {f}
          </button>
        ))}
        <span
          style={{
            marginLeft: "auto",
            fontSize: 12,
            color: "#9ca3af",
            alignSelf: "center",
          }}
        >
          {filtered.length} step{filtered.length !== 1 ? "s" : ""}
        </span>
      </div>

      <div
        style={{
          borderRadius: 10,
          border: "1px solid #f3f4f6",
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "42px 1fr 1fr",
            background: "#f3f4f6",
            borderBottom: "1px solid #e5e7eb",
            fontSize: 11,
            fontWeight: 700,
            color: "#6b7280",
            fontFamily: "monospace",
          }}
        >
          <div style={{ padding: "6px 10px" }}>#</div>
          <div style={{ padding: "6px 10px", borderLeft: "1px solid #e5e7eb" }}>
            Input
          </div>
          <div style={{ padding: "6px 10px", borderLeft: "1px solid #e5e7eb" }}>
            Action
          </div>
        </div>
        {slice.map((s, i) => (
          <TraceRow key={i} step={s} />
        ))}
      </div>

      {/* Pagination */}
      {pages > 1 && (
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: 6,
            marginTop: 12,
          }}
        >
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            style={{
              padding: "4px 12px",
              borderRadius: 6,
              border: "1px solid #e5e7eb",
              cursor: page === 0 ? "not-allowed" : "pointer",
              background: "#fff",
              color: page === 0 ? "#d1d5db" : "#374151",
              fontSize: 13,
            }}
          >
            ← Prev
          </button>
          <span style={{ padding: "4px 12px", fontSize: 13, color: "#6b7280" }}>
            Page {page + 1} of {pages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(pages - 1, p + 1))}
            disabled={page === pages - 1}
            style={{
              padding: "4px 12px",
              borderRadius: 6,
              border: "1px solid #e5e7eb",
              cursor: page === pages - 1 ? "not-allowed" : "pointer",
              background: "#fff",
              color: page === pages - 1 ? "#d1d5db" : "#374151",
              fontSize: 13,
            }}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}

// ── LR trace tab ───────────────────────────────────────────────────────────

const LR_STYLE = {
  shift: { bg: "#eff6ff", text: "#1d4ed8", border: "#bfdbfe" },
  reduce: { bg: "#fdf4ff", text: "#7e22ce", border: "#e9d5ff" },
  accept: { bg: "#f0fdf4", text: "#065f46", border: "#6ee7b7" },
  error: { bg: "#fef2f2", text: "#991b1b", border: "#fecaca" },
  default: { bg: "#f9fafb", text: "#374151", border: "#e5e7eb" },
};

function LRTraceRow({ step }) {
  const s = LR_STYLE[step.action] || LR_STYLE.default;
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "42px 60px 1fr 2fr",
        borderBottom: "1px solid #f3f4f6",
        fontSize: 12,
        fontFamily: "monospace",
      }}
    >
      <div
        style={{
          padding: "6px 8px",
          color: "#9ca3af",
          fontWeight: 600,
          background: "#fafafa",
          borderRight: "1px solid #f3f4f6",
          display: "flex",
          alignItems: "center",
        }}
      >
        {step.step}
      </div>
      <div
        style={{
          padding: "6px 8px",
          color: "#374151",
          borderRight: "1px solid #f3f4f6",
          display: "flex",
          alignItems: "center",
        }}
      >
        <span
          style={{
            padding: "1px 7px",
            borderRadius: 5,
            background: "#f3f4f6",
            color: "#374151",
            fontSize: 11,
          }}
        >
          s{step.state}
        </span>
      </div>
      <div
        style={{
          padding: "6px 8px",
          color: "#374151",
          borderRight: "1px solid #f3f4f6",
          display: "flex",
          alignItems: "center",
        }}
      >
        {step.input}
      </div>
      <div
        style={{
          padding: "6px 10px",
          background: s.bg,
          color: s.text,
          wordBreak: "break-word",
          lineHeight: 1.5,
        }}
      >
        {step.action_label}
      </div>
    </div>
  );
}

function LRTab({ lr }) {
  const [page, setPage] = useState(0);
  const [filter, setFilter] = useState("all");
  if (!lr) return <EmptyState msg="No LR result." />;

  const PAGE_SIZE = 50;
  const filtered =
    filter === "all" ? lr.trace : lr.trace.filter((s) => s.action === filter);
  const pages = Math.ceil(filtered.length / PAGE_SIZE);
  const slice = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <div>
      <SectionHeader
        title="LR Parser Trace (SLR)"
        count={lr.trace.length + " steps"}
      />
      <ErrorList errors={lr.errors} />

      <div
        style={{
          display: "flex",
          gap: 6,
          marginTop: 14,
          marginBottom: 10,
          flexWrap: "wrap",
        }}
      >
        {["all", "shift", "reduce", "accept", "error"].map((f) => (
          <button
            key={f}
            onClick={() => {
              setFilter(f);
              setPage(0);
            }}
            style={{
              padding: "3px 12px",
              borderRadius: 999,
              fontSize: 11,
              fontWeight: 600,
              cursor: "pointer",
              border: "1px solid",
              borderColor:
                filter === f ? LR_STYLE[f]?.border || "#e5e7eb" : "#e5e7eb",
              background: filter === f ? LR_STYLE[f]?.bg || "#f9fafb" : "#fff",
              color: filter === f ? LR_STYLE[f]?.text || "#374151" : "#6b7280",
            }}
          >
            {f}
          </button>
        ))}
        <span
          style={{
            marginLeft: "auto",
            fontSize: 12,
            color: "#9ca3af",
            alignSelf: "center",
          }}
        >
          {filtered.length} step{filtered.length !== 1 ? "s" : ""}
        </span>
      </div>

      <div
        style={{
          borderRadius: 10,
          border: "1px solid #f3f4f6",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "42px 60px 1fr 2fr",
            background: "#f3f4f6",
            borderBottom: "1px solid #e5e7eb",
            fontSize: 11,
            fontWeight: 700,
            color: "#6b7280",
            fontFamily: "monospace",
          }}
        >
          <div style={{ padding: "6px 8px" }}>#</div>
          <div style={{ padding: "6px 8px", borderLeft: "1px solid #e5e7eb" }}>
            State
          </div>
          <div style={{ padding: "6px 8px", borderLeft: "1px solid #e5e7eb" }}>
            Input
          </div>
          <div style={{ padding: "6px 8px", borderLeft: "1px solid #e5e7eb" }}>
            Action
          </div>
        </div>
        {slice.map((s, i) => (
          <LRTraceRow key={i} step={s} />
        ))}
      </div>

      {pages > 1 && (
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: 6,
            marginTop: 12,
          }}
        >
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            style={{
              padding: "4px 12px",
              borderRadius: 6,
              border: "1px solid #e5e7eb",
              cursor: page === 0 ? "not-allowed" : "pointer",
              background: "#fff",
              color: page === 0 ? "#d1d5db" : "#374151",
              fontSize: 13,
            }}
          >
            ← Prev
          </button>
          <span style={{ padding: "4px 12px", fontSize: 13, color: "#6b7280" }}>
            Page {page + 1} of {pages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(pages - 1, p + 1))}
            disabled={page === pages - 1}
            style={{
              padding: "4px 12px",
              borderRadius: 6,
              border: "1px solid #e5e7eb",
              cursor: page === pages - 1 ? "not-allowed" : "pointer",
              background: "#fff",
              color: page === pages - 1 ? "#d1d5db" : "#374151",
              fontSize: 13,
            }}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}

// ── Symbol table tab ────────────────────────────────────────────────────────

const KIND_COLORS = {
  variable: { bg: "#eff6ff", text: "#1d4ed8", border: "#bfdbfe" },
  function: { bg: "#fdf4ff", text: "#7e22ce", border: "#e9d5ff" },
  class: { bg: "#fff7ed", text: "#c2410c", border: "#fed7aa" },
  object: { bg: "#f0fdf4", text: "#166534", border: "#bbf7d0" },
  default: { bg: "#f9fafb", text: "#6b7280", border: "#e5e7eb" },
};

function SymbolTab({ symbols }) {
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState("line_number");
  const [filterKind, setFilterKind] = useState("all");

  const kinds = ["all", ...new Set((symbols || []).map((s) => s.kind))];
  const filtered = (symbols || [])
    .filter((s) => filterKind === "all" || s.kind === filterKind)
    .filter(
      (s) => !search || s.name.toLowerCase().includes(search.toLowerCase()),
    )
    .sort((a, b) => {
      if (sortBy === "name") return a.name.localeCompare(b.name);
      if (sortBy === "scope_level") return a.scope_level - b.scope_level;
      return a.line_number - b.line_number;
    });

  if (!symbols || symbols.length === 0)
    return <EmptyState msg="No symbols recorded." />;

  const SortBtn = ({ col, label }) => (
    <button
      onClick={() => setSortBy(col)}
      style={{
        background: "none",
        border: "none",
        cursor: "pointer",
        padding: "6px 10px",
        fontWeight: sortBy === col ? 700 : 500,
        color: sortBy === col ? "#1d4ed8" : "#6b7280",
        fontSize: 12,
        userSelect: "none",
      }}
    >
      {label} {sortBy === col ? "↑" : ""}
    </button>
  );

  return (
    <div>
      <SectionHeader title="Symbol Table" count={symbols.length} />

      <div
        style={{ display: "flex", gap: 10, marginBottom: 14, flexWrap: "wrap" }}
      >
        {/* Kind filter */}
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {kinds.map((k) => {
            const s = KIND_COLORS[k] || KIND_COLORS.default;
            return (
              <button
                key={k}
                onClick={() => setFilterKind(k)}
                style={{
                  padding: "3px 12px",
                  borderRadius: 999,
                  fontSize: 11,
                  fontWeight: 600,
                  cursor: "pointer",
                  border: "1px solid",
                  borderColor: filterKind === k ? s.border : "#e5e7eb",
                  background: filterKind === k ? s.bg : "#fff",
                  color: filterKind === k ? s.text : "#6b7280",
                }}
              >
                {k}
              </button>
            );
          })}
        </div>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name…"
          style={{
            marginLeft: "auto",
            padding: "4px 12px",
            borderRadius: 8,
            border: "1px solid #e5e7eb",
            fontSize: 13,
            outline: "none",
          }}
        />
      </div>

      <div
        style={{
          borderRadius: 10,
          border: "1px solid #e5e7eb",
          overflow: "hidden",
        }}
      >
        <table
          style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}
        >
          <thead style={{ background: "#f9fafb" }}>
            <tr>
              <th
                style={{
                  textAlign: "left",
                  borderBottom: "1px solid #e5e7eb",
                  padding: 0,
                }}
              >
                <SortBtn col="name" label="Name" />
              </th>
              <th
                style={{
                  textAlign: "left",
                  borderBottom: "1px solid #e5e7eb",
                  padding: "6px 10px",
                  color: "#6b7280",
                  fontWeight: 600,
                  fontSize: 12,
                }}
              >
                Kind
              </th>
              <th
                style={{
                  textAlign: "left",
                  borderBottom: "1px solid #e5e7eb",
                  padding: "6px 10px",
                  color: "#6b7280",
                  fontWeight: 600,
                  fontSize: 12,
                }}
              >
                Type
              </th>
              <th
                style={{
                  textAlign: "left",
                  borderBottom: "1px solid #e5e7eb",
                  padding: 0,
                }}
              >
                <SortBtn col="scope_level" label="Scope" />
              </th>
              <th
                style={{
                  textAlign: "left",
                  borderBottom: "1px solid #e5e7eb",
                  padding: 0,
                }}
              >
                <SortBtn col="line_number" label="Line" />
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((sym, i) => {
              const k = KIND_COLORS[sym.kind] || KIND_COLORS.default;
              return (
                <tr
                  key={i}
                  style={{ background: i % 2 === 0 ? "#fff" : "#fafafa" }}
                >
                  <td
                    style={{
                      padding: "8px 10px",
                      borderBottom: "1px solid #f3f4f6",
                    }}
                  >
                    <code
                      style={{
                        fontWeight: 700,
                        color: "#111827",
                        fontSize: 13,
                      }}
                    >
                      {sym.name}
                    </code>
                  </td>
                  <td
                    style={{
                      padding: "8px 10px",
                      borderBottom: "1px solid #f3f4f6",
                    }}
                  >
                    <span
                      style={{
                        padding: "2px 8px",
                        borderRadius: 5,
                        fontSize: 11,
                        fontWeight: 600,
                        background: k.bg,
                        color: k.text,
                        border: `1px solid ${k.border}`,
                      }}
                    >
                      {sym.kind}
                    </span>
                  </td>
                  <td
                    style={{
                      padding: "8px 10px",
                      borderBottom: "1px solid #f3f4f6",
                    }}
                  >
                    <code style={{ color: "#6d28d9", fontSize: 12 }}>
                      {sym.type}
                    </code>
                  </td>
                  <td
                    style={{
                      padding: "8px 10px",
                      borderBottom: "1px solid #f3f4f6",
                    }}
                  >
                    <span
                      style={{
                        padding: "1px 8px",
                        borderRadius: 5,
                        fontSize: 11,
                        background: "#f3f4f6",
                        color: "#6b7280",
                      }}
                    >
                      {"›".repeat(sym.scope_level)} {sym.scope_level}
                    </span>
                  </td>
                  <td
                    style={{
                      padding: "8px 10px",
                      borderBottom: "1px solid #f3f4f6",
                      color: "#6b7280",
                      fontSize: 12,
                      fontFamily: "monospace",
                    }}
                  >
                    {sym.line_number}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Errors tab ─────────────────────────────────────────────────────────────

function ErrorsTab({ errors }) {
  if (!errors) return <EmptyState msg="No error data." />;
  const phases = [
    { key: "lexical", label: "Lexical", color: "#b45309" },
    { key: "syntactic", label: "Syntactic", color: "#991b1b" },
    { key: "semantic", label: "Semantic", color: "#6d28d9" },
  ];
  const total = phases.reduce((n, p) => n + (errors[p.key]?.length || 0), 0);

  return (
    <div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          marginBottom: 16,
        }}
      >
        <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>
          Error Report
        </h3>
        {total === 0 ? (
          <Badge color="#166534">✓ Clean</Badge>
        ) : (
          <Badge color="#991b1b">
            {total} error{total !== 1 ? "s" : ""}
          </Badge>
        )}
        {errors.summary && (
          <span style={{ fontSize: 12, color: "#9ca3af", marginLeft: "auto" }}>
            {errors.summary}
          </span>
        )}
      </div>

      {phases.map((p) => {
        const errs = errors[p.key] || [];
        return (
          <div key={p.key} style={{ marginBottom: 20 }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                marginBottom: 8,
              }}
            >
              <span
                style={{
                  fontWeight: 700,
                  fontSize: 13,
                  color: p.color,
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                }}
              >
                {p.label}
              </span>
              <span
                style={{
                  background: errs.length ? "#fee2e2" : "#f0fdf4",
                  color: errs.length ? "#991b1b" : "#166534",
                  fontSize: 11,
                  fontWeight: 700,
                  borderRadius: 999,
                  padding: "0 7px",
                }}
              >
                {errs.length}
              </span>
            </div>
            <ErrorList errors={errs} />
          </div>
        );
      })}
    </div>
  );
}

// ── Main App ───────────────────────────────────────────────────────────────

const TABS = [
  { id: "tokens", label: "Lexer" },
  { id: "grammar", label: "Grammar" },
  { id: "rd", label: "RD Parser" },
  { id: "ll1", label: "LL(1) Parser" },
  { id: "lr", label: "LR Parser" },
  { id: "symbol", label: "Symbol Table" },
  { id: "errors", label: "Errors" },
];

export default function App() {
  const [code, setCode] = useState(DEFAULT_CODE);
  const [activeTab, setActiveTab] = useState("tokens");
  const [compilerData, setCompilerData] = useState(null);
  const [isCompiling, setIsCompiling] = useState(false);

  const errorCount = compilerData
    ? Object.values(compilerData.errors || {})
        .flat()
        .filter((e) => typeof e === "string" || typeof e === "object").length
    : 0;

  const handleCompile = async () => {
    setIsCompiling(true);
    try {
      const res = await fetch("http://localhost:5000/api/compile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source_code: code }),
      });
      const data = await res.json();
      setCompilerData(data);
      setActiveTab("tokens");
    } catch (err) {
      alert("Cannot reach the Flask backend (localhost:5000). Is it running?");
    } finally {
      setIsCompiling(false);
    }
  };

  const renderTab = () => {
    if (!compilerData)
      return (
        <EmptyState msg="Write some Decaf code and click Compile to see results." />
      );
    switch (activeTab) {
      case "tokens":
        return (
          <TokensTab
            tokens={compilerData.tokens}
            summary={compilerData.token_summary}
          />
        );
      case "grammar":
        return <GrammarTab grammar={compilerData.grammar} />;
      case "rd":
        return <RDTab rd={compilerData.parsers.rd} />;
      case "ll1":
        return <LL1Tab ll1={compilerData.parsers.ll1} />;
      case "lr":
        return <LRTab lr={compilerData.parsers.lr} />;
      case "symbol":
        return <SymbolTab symbols={compilerData.symbol_table} />;
      case "errors":
        return <ErrorsTab errors={compilerData.errors} />;
      default:
        return null;
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        fontFamily: "system-ui, -apple-system, sans-serif",
        background: "#f8fafc",
      }}
    >
      {/* ── Header ───────────────────────────────────────────────────── */}
      <header
        style={{
          display: "flex",
          alignItems: "center",
          gap: 16,
          padding: "0 24px",
          height: 52,
          background: "#fff",
          borderBottom: "1px solid #e5e7eb",
          flexShrink: 0,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span
            style={{
              background: "#1d4ed8",
              color: "#fff",
              fontWeight: 800,
              fontSize: 13,
              padding: "3px 9px",
              borderRadius: 6,
              letterSpacing: "0.04em",
            }}
          >
            DECAF
          </span>
          <span style={{ fontWeight: 600, fontSize: 15, color: "#111827" }}>
            Compiler
          </span>
          <span style={{ fontSize: 12, color: "#9ca3af" }}>CS-471L</span>
        </div>

        <div
          style={{
            marginLeft: "auto",
            display: "flex",
            alignItems: "center",
            gap: 12,
          }}
        >
          {compilerData && errorCount > 0 && (
            <button
              onClick={() => setActiveTab("errors")}
              style={{
                padding: "5px 12px",
                borderRadius: 7,
                fontSize: 12,
                fontWeight: 600,
                cursor: "pointer",
                background: "#fef2f2",
                border: "1px solid #fecaca",
                color: "#991b1b",
              }}
            >
              ⚠ {errorCount} error{errorCount !== 1 ? "s" : ""}
            </button>
          )}
          {compilerData && errorCount === 0 && (
            <span style={{ fontSize: 12, color: "#166534", fontWeight: 600 }}>
              ✓ No errors
            </span>
          )}
          <button
            onClick={handleCompile}
            disabled={isCompiling}
            style={{
              padding: "7px 20px",
              borderRadius: 8,
              fontSize: 13,
              fontWeight: 700,
              cursor: isCompiling ? "not-allowed" : "pointer",
              background: isCompiling ? "#93c5fd" : "#1d4ed8",
              color: "#fff",
              border: "none",
              letterSpacing: "0.02em",
            }}
          >
            {isCompiling ? "Compiling…" : "▶  Compile"}
          </button>
        </div>
      </header>

      {/* ── Body ─────────────────────────────────────────────────────── */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {/* ── Editor pane ────────────────────────────────────────────── */}
        <div
          style={{
            width: 360,
            flexShrink: 0,
            display: "flex",
            flexDirection: "column",
            borderRight: "1px solid #e5e7eb",
            background: "#fff",
          }}
        >
          <div
            style={{
              padding: "8px 14px",
              fontSize: 11,
              fontWeight: 700,
              color: "#9ca3af",
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              borderBottom: "1px solid #f3f4f6",
            }}
          >
            Source Code
          </div>
          <textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            spellCheck={false}
            style={{
              flex: 1,
              resize: "none",
              border: "none",
              outline: "none",
              fontFamily: "'Fira Code', 'Cascadia Code', monospace",
              fontSize: 13,
              lineHeight: 1.7,
              padding: "14px 16px",
              color: "#1e293b",
              background: "#fff",
            }}
          />
        </div>

        {/* ── Output pane ────────────────────────────────────────────── */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
          }}
        >
          {/* Tabs */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 0,
              background: "#fff",
              borderBottom: "1px solid #e5e7eb",
              padding: "0 16px",
              flexShrink: 0,
              overflowX: "auto",
            }}
          >
            {TABS.map((t) => {
              const active = activeTab === t.id;
              const hasErr = t.id === "errors" && errorCount > 0;
              return (
                <button
                  key={t.id}
                  onClick={() => setActiveTab(t.id)}
                  style={{
                    padding: "12px 16px",
                    fontSize: 13,
                    fontWeight: active ? 700 : 500,
                    border: "none",
                    background: "none",
                    cursor: "pointer",
                    color: active ? "#1d4ed8" : hasErr ? "#991b1b" : "#6b7280",
                    borderBottom: active
                      ? "2px solid #1d4ed8"
                      : "2px solid transparent",
                    whiteSpace: "nowrap",
                  }}
                >
                  {t.label}
                  {hasErr && !active && (
                    <span
                      style={{
                        marginLeft: 5,
                        fontSize: 10,
                        fontWeight: 800,
                        background: "#fef2f2",
                        color: "#991b1b",
                        borderRadius: 999,
                        padding: "0 5px",
                      }}
                    >
                      {errorCount}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Tab content */}
          <div
            style={{
              flex: 1,
              overflowY: "auto",
              padding: "20px 24px",
            }}
          >
            {renderTab()}
          </div>
        </div>
      </div>
    </div>
  );
}
