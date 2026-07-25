# AI Stack: Skills, Agents, RAG, and Routines

A curated reference for the tooling around this repo's MCP work — researched July 2026.

This is opinionated. The ecosystem has more "awesome" lists than useful tools, and most
curated lists are ranked by stars rather than by whether the thing survives contact with
production. Where a claim has a number attached, the number came from a primary source.

## Contents

- [Start here: the pruning problem](#start-here-the-pruning-problem)
- [Agent skills](#agent-skills)
- [Agent frameworks](#agent-frameworks)
- [RAG](#rag) — see also [`rag/reference-architecture.md`](rag/reference-architecture.md)
- [MCP servers](#mcp-servers)
- [Routines](#routines) — see also [`routines/README.md`](routines/README.md)
- [Workflow automation](#workflow-automation)

---

## Start here: the pruning problem

Before adding anything: this account currently has **~70 plugins and ~15 skills enabled
simultaneously**. That is not a flex, it is a liability, for two concrete reasons:

1. **Trigger collisions.** Skill descriptions are how the model decides what to load. With a
   dozen legal plugins enabled (`ip-legal`, `commercial-legal`, `litigation-legal`,
   `regulatory-legal`, `corporate-legal`, `privacy-legal`, `employment-legal`,
   `product-legal`, `ai-governance-legal`, `legal-clinic`, `legal-builder-hub`, `law-student`,
   plus `legal`), a single legal question has thirteen plausible matches. The model picks one.
   You cannot predict which, and the wrong pick is worse than no pick.
2. **Context cost.** Every enabled skill's description sits in the context window on every
   turn, before you have asked anything.

**Recommendation:** enable per-project, not globally. Keep the four that are genuinely
distinct and high-signal for your work — `arabic-legal-defense`, `arabic-court-prep`,
`skill-creator`, `mcp-builder` — plus whatever the current project needs. Disable the rest
until a task calls for it. The healthcare cluster (`icd10-codes`, `cms-coverage`,
`npi-registry`, `pubmed`, `healthcare`) and the sales cluster (`apollo`, `zoominfo`,
`nimble`, `hubspot`) are the obvious candidates to park, since neither overlaps the MCP and
security work in these repos.

This single change will do more for output quality than any addition below.

---

## Agent skills

The skills ecosystem consolidated hard in 2026. Four collections matter:

| Collection | Scale | What it is | Worth it? |
|---|---|---|---|
| [obra/superpowers](https://github.com/obra/superpowers) | ~94k stars | Enforces a 7-phase workflow: Brainstorm → Spec → Plan → TDD → Subagent Development → Review → Finalize. Accepted into the Anthropic marketplace. | Yes, if you want process discipline. The rigidity is the point; it is also the main complaint. |
| [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) | 1000+ skills | Aggregates *official* vendor skills — Anthropic, Google Labs, Vercel, Stripe, Cloudflare, Netlify, Trail of Bits, Sentry, Expo, Hugging Face, Figma. Cross-compatible with Codex, Gemini CLI, Cursor. | Yes — best source for first-party skills. Trail of Bits' security skills are the standout. |
| [antigravity-awesome-skills](https://github.com/topics/claude-code-skills) | 1200+ skills, ~22k stars | Community library, installs via `npx antigravity-awesome-skills -- claude`. | Browse, don't bulk-install. See the pruning problem above. |
| [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills) | Curated list | Resources and tooling rather than skills themselves. | Good orientation, low ongoing value. |

**On your own skills library.** The `Anthropic-Cybersecurity-Skills` fork (817 skills, 29
domains, 6 framework mappings) is already larger and better-mapped than anything in the lists
above for security specifically. It is not the thing to replace — it is the thing to keep
synced. That is why the sync routine exists.

Note that fork is a *community* project, unaffiliated with Anthropic despite the name, and it
bundles offensive and dual-use techniques. Authorized, lawful use only — see its
`SECURITY.md`. If you ever publish derived work from it, carry that framing forward.

**Building your own:** use the `skill-creator` skill (already enabled). A good skill is a
sharp description plus a narrow job. The description is the hard part — it is what determines
whether the skill ever fires. The `prompt-engineer` skill is the right tool for tightening it.

---

## Agent frameworks

Pick by workload shape, not popularity.

| Framework | Best for | Notes |
|---|---|---|
| **Claude Agent SDK** | Anthropic-native production agents | Hierarchical subagent spawning. The natural fit given this stack. |
| **LangGraph 1.0** | Complex stateful workflows | Best-in-class for graph-structured, resumable agent state. Pairs with LangSmith for tracing. |
| **LlamaIndex Workflows 1.0** | RAG-grounded agents | Choose when retrieval is the core of the agent, not a side quest. |
| **CrewAI** | Role-based multi-agent | Simplest mental model — roles map to team members. Fewer dependencies. |
| **AgentScope** (Alibaba) | Distributed, fault-tolerant | Real distributed deployment and fault tolerance. Under-discussed in English sources. |
| **Microsoft Agent Framework 1.0** | Enterprise .NET | Semantic Kernel + AutoGen merged into one SDK. |

Context: enterprise survey data puts ~57% of organizations running agents in production
workflows as of 2026, so the "is this real yet" question is settled. What is not settled is
observability — budget for tracing from day one, not after the first silent failure.

---

## RAG

Full blueprint in [`rag/reference-architecture.md`](rag/reference-architecture.md). The short
version:

**Frameworks by star count (Jan 2026):** LangChain ~125k, Dify ~114k, RAGFlow ~70k,
LlamaIndex ~46.5k, Haystack ~24k.

- **LangChain** — widest ecosystem (700+ integrations), LangGraph for agentic RAG, LangSmith
  for observability. Default choice for most teams.
- **LlamaIndex** — better when the pipeline is fundamentally document retrieval. 300+ data
  connectors, purpose-built query engines.
- **Haystack** — cleanest modular architecture. Choose it when you want to understand your
  own pipeline in six months.
- **RAGFlow** — low-code, fuses RAG with agent capabilities. Fastest path to something running.

**The single highest-leverage technique:** Anthropic's contextual retrieval — prefix every
chunk with a one-sentence summary of its parent document. Reported 35–50% retrieval
improvement. It is cheap, it is boring, and it beats most architectural cleverness.

**Do not start with GraphRAG.** Start with hybrid retrieval plus a reranker, measure, and only
add complexity when the metrics demand it.

---

## MCP servers

You are already building here (`examples/dice-roller`, `mcp-builder-prompt/`), and the
`mcp-builder` skill is enabled. For discovery rather than construction:

- [tolkonepiu/best-of-mcp-servers](https://github.com/tolkonepiu/best-of-mcp-servers) —
  ~400 servers, quality-scored from GitHub and package-manager metrics, updated weekly. The
  ranking methodology is why this beats the plain awesome-lists.
- [awesome-mcp.tools](https://awesome-mcp.tools/blog/mcp-servers-list) — 2000+ servers,
  searchable and filterable, with install commands.
- [wong2/awesome-mcp-servers](https://github.com/wong2/awesome-mcp-servers) and
  [appcypher/awesome-mcp-servers](https://github.com/appcypher/awesome-mcp-servers) — the
  established general lists.

Servers worth knowing about for this stack: **Qdrant** (vector memory — the natural companion
to a RAG build), **Postgres MCP Pro** (health monitoring, index tuning, query plan analysis —
substantially more than a query wrapper), **BrowserMCP** (local Chrome automation).

**Security note, since you maintain a security skills library:** MCP servers are a live
supply-chain surface. A server runs with whatever credentials you hand it. Pin versions, read
the source of anything that touches secrets, and prefer first-party servers where one exists.
The weekly digest routine watches for MCP advisories specifically.

---

## Routines

Two are live now; three more need the claude.ai UI because of a connector limitation.
Details and copy-paste prompts in [`routines/README.md`](routines/README.md).

---

## Workflow automation

You have both **n8n** and **Zapier** connected, which is redundant unless deliberate. They
are not equivalent:

- **n8n** — self-hostable, code-friendly, has real branching and error handling. Correct
  choice for anything with logic in it, and for anything touching client data you would rather
  not route through a third party. Given the legal work, that consideration is not minor.
- **Zapier** — 9000+ app integrations. Correct choice when the requirement is purely "app A
  talks to app B" and the app is obscure.

**Suggested split:** n8n for pipelines with branching, retries, or sensitive data. Zapier only
to reach an integration n8n lacks.

Also connected and worth noting: **Cloudflare Developer Platform** gives you Workers, D1,
R2, KV, and Hyperdrive. That is a complete serverless substrate for hosting an MCP server or
a RAG API without standing up infrastructure — a natural next step from the Docker work in
this repo.

---

## Sources

Agent skills and Claude Code:
[VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) ·
[travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills) ·
[claude-code-skills topic](https://github.com/topics/claude-code-skills) ·
[Best Claude Code Plugins 2026](https://designrevision.com/blog/best-claude-code-plugins) ·
[7 Claude Code Plugins Worth Your Time](https://securityboulevard.com/2026/06/7-claude-code-plugins-from-the-marketplace-worth-your-time/)

RAG:
[15 Best Open-Source RAG Frameworks](https://www.firecrawl.dev/blog/best-open-source-rag-frameworks) ·
[Top 10 RAG Frameworks by Stars](https://florinelchis.medium.com/top-10-rag-frameworks-on-github-by-stars-january-2026-e6edff1e0d91) ·
[RAG Techniques Compared](https://blog.starmorph.com/blog/rag-techniques-compared-best-practices-guide) ·
[infiniflow/ragflow](https://github.com/infiniflow/ragflow) ·
[Awesome-RAG-Production](https://github.com/Yigtwxx/Awesome-RAG-Production)

Agents:
[Best open source agent frameworks](https://www.firecrawl.dev/blog/best-open-source-agent-frameworks) ·
[Best AI Agent Frameworks 2026](https://alicelabs.ai/en/insights/best-ai-agent-frameworks-2026) ·
[aloth/awesome-ai-agents](https://github.com/aloth/awesome-ai-agents)

MCP:
[best-of-mcp-servers](https://github.com/tolkonepiu/best-of-mcp-servers) ·
[MCP Servers List (2000+)](https://awesome-mcp.tools/blog/mcp-servers-list) ·
[wong2/awesome-mcp-servers](https://github.com/wong2/awesome-mcp-servers)
