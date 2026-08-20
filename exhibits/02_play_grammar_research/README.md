# Exhibit 2 — The Play-Grammar Research Program (WMRF)

One document from the desk's NFL play-calling research lane, plus the process story
around it. **Nothing in this lane has touched data yet** — the document says so
explicitly, and that is the point of the exhibit: this is what the desk's process
looks like *between* the idea and the first fit, where most quantitative sins are
committed.

[`WMRF_TRANSLATION.md`](WMRF_TRANSLATION.md) (2026-08-12) is the origin document. An
operator-sourced intuition ("the NFL is patterns replicated with
coach/team/QB-conditional frequencies") led to a real, niche bioinformatics paper:
the Wasserstein-Markov Random Forest, which fingerprints protein sequences by their
Markov transition grammar plus Wasserstein distance-to-consensus features. This note
translates the architecture to NFL play-calling — coach grammar fingerprints as
low-dimensional identity covariates for a play-level transition kernel — and files
it as *a candidate architecture, not a result*.

## What happened next (the part that matters)

The desk did not build it. Instead, the candidate was put through the standard
gauntlet before any model code was written:

1. **The paper was examined properly.** A follow-up deep-dive worked through what
   the algorithm actually does, why Wasserstein rather than KL, which
   implementation details the abstract does not pin down (flagged as ratification
   blockers, not assumed), and six named stress points where the protein→football
   analogy creaks — the biggest being state confounding: a trailing team's raw
   grammar fingerprint records its circumstances, not its coach.

2. **Then the desk commissioned a six-family methods survey (~30 methods) with a
   mandate to beat its own idea** — context-tree Markov machinery, hierarchical
   Bayes + tensor factorization, latent-mode HMMs, neural sequence models,
   decision-theoretic policy learning, and optimal-transport/graph methods,
   surveyed in parallel lanes. The survey's verdict: **the incumbent enters a
   designed three-arm bake-off** — WMRF remains the primary candidate, now with
   two challengers it must beat on identical pre-registered tests, because the
   survey argued the pricing fingerprint may be better
   estimated *inside* the likelihood; and a league-pooled shrunk-multinomial
   control — which cannot lose — must be built first. The survey also produced a
   near-free kill test: if a context tree prunes to depth zero once game state is
   conditioned on, the whole grammar story dies honestly in days.

The deep-dive and the survey are internal working documents in the private
repository and are not included here; this exhibit includes the origin document and
reports the outcome.

## Why this is the exhibit

- **Ideas are traced to sources and verified**, including the honest provenance note
  that the paper was initially read at abstract level, with full-text verification
  registered as a blocker before any prereg freezes.
- **The staged plan puts existence tests before value tests**: split-half fingerprint
  reliability, out-of-sample coach identification, and a "0th-order costume test"
  (does grammar add anything over raw play-mix frequencies?) all gate anything
  downstream. Expected effect sizes are taken from the published record
  (~0.01–0.03 nats/play), and any prereg must be powered for an effect that small.
- **The incumbent gets no home-field advantage.** The desk's own filed idea was
  handed to six independent survey lanes with a mandate to find something better,
  and the demotion verdict is kept, not buried.

References to internal task numbers, companion documents (the deep-dive, the
survey, a staged game plan, an estimation charter, a draft prereg), and agent lanes
point into the private repository. The dated filename cited inside the document —
`WMRF_TRANSLATION_20260812.md` — is the private-repo name of the file above.
