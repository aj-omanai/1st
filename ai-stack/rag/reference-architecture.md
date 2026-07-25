# RAG Reference Architecture (2026)

A build order, not a menu. Every stage below is justified by a measured result, and the stages
are ordered so that you stop as soon as your metrics are good enough.

The governing principle: **start with the simplest thing that works, measure it, and only add
complexity when the numbers prove the simpler version is insufficient.** Most RAG projects that
fail in 2026 fail from premature architecture, not from missing features.

---

## Stage 0 — Evaluation first

Build the eval set before the pipeline. This inverts the instinct and it is the whole game:
without it, every later decision is taste rather than evidence.

- 50–100 real questions with known-correct source passages. Real user questions, not
  synthesized ones — synthesized questions flatter your chunking strategy because they were
  written against it.
- Use [RAGAS](https://github.com/explodinggradients/ragas) for retrieval quality metrics.
- Track **retrieval** and **generation** separately. Conflating them is the most common
  diagnostic mistake: a wrong answer from correctly-retrieved context is a prompt problem, and
  no amount of retrieval tuning will fix it.

Metrics that matter: context recall (did we retrieve the right passage at all — the ceiling on
everything downstream), context precision (how much retrieved text was noise), faithfulness
(is the answer grounded in what was retrieved).

---

## Stage 1 — Chunking

**2026 defaults:** 512–1024 tokens with 50–100 tokens of overlap, then a semantic re-chunker
that respects section boundaries.

Chunk size is one of the most consequential knobs in the entire pipeline, and it is worth
sweeping empirically against your eval set rather than accepting the default. Respecting
document structure — headings, sections, clause boundaries — matters more than hitting an exact
token count.

For structured documents (contracts, statutes, court filings, RFCs), chunk on the document's
own boundaries. A legal clause split across two chunks retrieves badly in a way that no
reranker recovers from, because neither half is independently meaningful.

---

## Stage 2 — Contextual retrieval

**This is the highest-leverage single change in the pipeline.**

Prefix every chunk with a one-sentence summary of its parent document before embedding.
Anthropic's benchmark reports a **35–50% retrieval improvement**.

The reason it works: an isolated chunk loses the context that makes it findable. A chunk reading
"The defendant's appeal was denied on procedural grounds" is nearly unretrievable without
knowing which case, which court, which year. The prefix restores exactly that.

It costs one cheap LLM call per chunk at index time and nothing at query time. Do this before
you consider anything below.

---

## Stage 3 — Hybrid retrieval

**BM25 + dense embeddings, fused with Reciprocal Rank Fusion (RRF), beats either alone** on
public 2024–2025 benchmarks.

They fail in complementary directions, which is the point:

- **BM25** (lexical) catches exact terms — case numbers, statute references, error codes,
  proper nouns, acronyms. Dense embeddings routinely miss these because they are semantically
  uninformative but referentially critical.
- **Dense embeddings** catch paraphrase and conceptual similarity, where the user's wording
  shares no tokens with the source.

RRF needs no tuning and no score normalization between the two systems, which is why it is the
default fusion method rather than weighted score blending.

For a corpus with heavy domain terminology — legal citations, CVE identifiers, MITRE technique
IDs — the BM25 half will carry more weight than you expect. Do not skip it.

---

## Stage 4 — Reranking

A **cross-encoder reranker** on top of hybrid retrieval adds **another 5–15 points of MRR on
hard question sets**.

Retrieve broadly (top 50–100), rerank down to what you actually pass to the model (top 5–10).
The asymmetry is deliberate: the retriever optimizes recall cheaply, the reranker optimizes
precision expensively, and you only pay the expensive step on a small candidate set.

Cross-encoders are slower than embedding similarity because they jointly encode the query with
each candidate rather than comparing precomputed vectors. On 50–100 candidates that is a
tolerable cost. On 10,000 it is not — which is why this stage comes after retrieval, never
instead of it.

---

## Stage 5 — Adaptive routing

**Match query complexity to pipeline complexity.** The best production systems in 2026 route
rather than applying one fixed pipeline to everything.

- Simple factual lookup → hybrid retrieval, single pass, done.
- Multi-hop or comparative question → agentic loop with query decomposition.
- Relationship or "how do these connect" question → graph traversal.

This keeps cost and latency low for the majority of queries while reserving the expensive
machinery for the minority that genuinely need it. A single always-maximal pipeline is both
slower and, counterintuitively, often *less* accurate on simple queries, because extra
reasoning steps introduce extra failure modes.

---

## Stage 6 — Only if the metrics demand it

Reach for these when Stage 0's numbers say the simpler pipeline is insufficient — not before.

### Agentic RAG

The 2026 patterns and what each one actually fixes:

| Problem | Pattern |
|---|---|
| Hallucination | Critic agents, reflection loops, Graph-of-Thought reasoning |
| Context window limits | Hybrid memory, context fusion |
| Poor retrieval | Iterative query rewriting, reranking, graph traversal |
| No real reasoning | Multi-agent planning, tree search, LLM-as-judge loops |

Best implemented with **LangGraph** (stateful, resumable, inspectable) or **LlamaIndex
Workflows 1.0** (retrieval-first). The critical requirement is a hard iteration cap — an
agentic retrieval loop without one will happily spend your budget rewriting the same failing
query.

### GraphRAG

Extract entities and relationships into a knowledge graph, then traverse it for retrieval.
Pipeline: entity extraction → knowledge graph construction → community detection → community
summaries.

Full GraphRAG indexing is expensive. **Microsoft's LazyGraphRAG (2025) cut indexing cost to
0.1% of full GraphRAG**, which is what moved it from research curiosity to practical for large
corpora. Use LazyGraphRAG as the entry point.

Worth it when relationships between entities *are* the query — "which threat actors share this
infrastructure," "how do these contracts interact," "what precedent chain leads here."
Overkill for straightforward document lookup.

---

## Framework selection

| Framework | Stars (Jan 2026) | Choose when |
|---|---|---|
| **LangChain** | ~125k | You want the largest ecosystem (700+ integrations), LangGraph for agentic pipelines, LangSmith for observability. Default for most teams. |
| **Dify** | ~114k | You want a low-code platform with a UI over the pipeline. |
| **RAGFlow** | ~70k | You want RAG fused with agent capabilities and the fastest path to running. |
| **LlamaIndex** | ~46.5k | The pipeline is fundamentally document retrieval. 300+ connectors, structured query engines. |
| **Haystack** | ~24k | You want clean modular architecture you can still reason about in six months. |

Also: **FlashRAG** ships 36 pre-processed benchmark datasets and 17 RAG algorithms behind one
interface — the right tool for comparing approaches on your own data before committing.

---

## Deployment note

The **Cloudflare Developer Platform** connector on this account covers a full serverless RAG
substrate: **Workers** (inference orchestration), **D1** (metadata and chunk store), **R2**
(source documents), **KV** (query and embedding cache), **Vectorize** (vector index),
**Hyperdrive** (pooled connections to an existing Postgres).

Given the Docker MCP work in this repo, the natural shape is an MCP server exposing retrieval
as a tool, deployed on Workers, with the agent calling it over MCP rather than embedding
retrieval logic in the agent itself. That boundary keeps the retrieval pipeline independently
testable — you can evaluate it against Stage 0's eval set without running the agent at all.

---

## Anti-patterns

Each of these is common and each has a specific failure mode:

1. **No eval set.** You cannot tell improvement from change. Every decision becomes taste.
2. **GraphRAG on day one.** Expensive indexing, added complexity, and usually no measurable
   gain over hybrid + rerank on document-lookup workloads.
3. **Dense-only retrieval.** Silently fails on exact identifiers — case numbers, CVEs, error
   codes. The failure is invisible without lexical comparison, because the results look
   plausible.
4. **Chunking without respecting structure.** Splits meaning across boundaries in a way no
   downstream stage recovers.
5. **Skipping the reranker.** The cheapest large accuracy win after contextual retrieval.
6. **Conflating retrieval and generation failures.** They have different fixes. Measure
   separately or you will tune the wrong stage indefinitely.

---

## Sources

[RAG Techniques Compared](https://blog.starmorph.com/blog/rag-techniques-compared-best-practices-guide) ·
[RAG Architecture 2026: Patterns, Code, Eval](https://futureagi.com/blog/rag-architecture-llm-2025/) ·
[Next-Generation Agentic RAG with LangGraph](https://medium.com/@vinodkrane/next-generation-agentic-rag-with-langgraph-2026-edition-d1c4c068d2b8) ·
[RAG Optimization Strategies](https://synthimind.net/blog/rag-optimization-strategies-2025/) ·
[Best Open Source RAG Frameworks](https://www.firecrawl.dev/blog/best-open-source-rag-frameworks) ·
[Awesome-RAG-Production](https://github.com/Yigtwxx/Awesome-RAG-Production) ·
[Systematic Review of RAG Systems (arXiv 2507.18910)](https://arxiv.org/pdf/2507.18910) ·
[Rethinking Agentic RAG (arXiv 2605.27123)](https://arxiv.org/pdf/2605.27123)
