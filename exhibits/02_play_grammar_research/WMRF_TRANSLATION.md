# WMRF → Football: Bio-Sequence Grammar Fingerprinting as the Play-Grammar Feature Layer

**Banked 2026-08-12. Operator-sourced concept (task #62 addendum). Status: FILED, untested —
a candidate architecture, not a result. Nothing here has touched data yet.**

**Provenance:** the operator proposed a play-level sequence model ("the NFL is patterns
replicated with coach/team/QB-conditional frequencies"), coined "Markov random forest" for
it, searched the term, and
surfaced a real, niche bioinformatics paper: **Wasserstein-Markov Random Forest (WMRF) —
protein subcellular localization** (ResearchGate publication 400440793). Desk verified the
paper exists and read the method 2026-08-12. This note is the translation.

## The paper's method (TLDR, verified from abstract/indexing)

Task: predict a protein's subcellular compartment (cytoplasm / membrane / mitochondrion /
nucleus; SwissProt-derived benchmarks) from its amino-acid sequence. Pipeline:

1. **Markov = feature construction.** Each sequence is fingerprinted by its own
   multi-order (1st–3rd) **transition profiles** over the residue alphabet — the
   sequence's *grammar*, as matrices.
2. **Wasserstein = deviation-from-consensus features.** Each grammar matrix is compared
   to the training population's consensus: Wasserstein distance to the mean matrix,
   Wasserstein to the median matrix, ℓ1 to mean, KL to mean — four compact scalars
   encoding "how far, and in what way, this sequence's grammar deviates from the crowd's."
3. **Random forest = plain classifier** on those features.

Selling point: captures higher-order sequential dependencies **cheaply** — no deep model,
small feature vector, outperforms AAC/PseAAC/HMM feature baselines on their benchmarks.

Distinct object, also relevant: **Wasserstein Random Forests** (Du et al., AISTATS 2021,
arXiv 2006.04709) put Wasserstein distance inside the *splitting criterion* to estimate
conditional **distributions** — a candidate for the outcome side of our kernel (pricing
cares about distribution shape, not means — the WP-4 lesson).

## The football translation (why this maps almost 1:1)

Swap protein → team-season, amino acids → play classes:

- A team-season ≈ 1,100 plays over a finite alphabet of play concepts. Its 1st–3rd order
  transition profile = **the coach's grammar fingerprint** (captures scripting memory:
  run-run-pass sequences, tendency chains — the operator's "2nd-and-8 leans chunk play").
- Wasserstein-to-league-consensus scalars = **"how far does this coordinator's grammar
  deviate from the league's, and in which direction"** — the operator's thesis ("the
  league repeats the patterns, teams vary the frequencies") compressed into a few
  numbers.
- Uses: (a) **low-dimensional team-identity covariates** conditioning the play-level
  transition kernel — exactly the small-n charter's principle 1 (structure global,
  identity local, identity LOW-dimensional); (b) **scheme-drift detection**
  (early-vs-late-season self-distance); (c) **new-coordinator fingerprint matching**
  (predict a new staff's tendencies from its nearest grammar neighbors); (d) situational
  split deviations (red zone, 2-minute, trailing states).

## Why it's statistically disciplined for the NFL's small n

The whole appeal is charter-compatible: at 17 games/team you cannot afford a deep sequence
model, but you CAN afford transition profiles + consensus-distance scalars feeding a
regularized kernel. And the sparsity trap has a house solution: a 3rd-order profile over
~15 play classes ≈ 3,375 cells vs ~1,100 plays/team → **the grammar fingerprints
themselves need Dirichlet-multinomial smoothing — the exact machinery the MLB engine's
locked control runs on.** The tools converge across sports.

## What we take vs leave

TAKE: the feature architecture (fingerprints + deviation scalars). LEAVE: the classifier
head (we want the transition kernel itself for Monte Carlo rollout — play kernel → drive
rollout → market-grain pricing). The Du et al. Wasserstein-split forest is the separate
candidate for distributional outcome estimation inside the kernel.

## Test design sketch (prereg before any fit — nothing here is licensed to run yet)

1. Alphabet definition first (play classes from nflverse PBP fields; finer concepts need
   tracking/charting — Big Data Bowl slices). The alphabet choice is itself a declared
   parameter.
2. Fingerprint stability: split-half reliability of team grammar profiles within season
   (does the fingerprint even cohere at n≈550/half?).
3. Discriminative check: can the scalars identify the coach/coordinator out-of-sample
   (the football analog of the paper's classification task) — a pure existence test.
4. Value check, Gate-2-style: do grammar-deviation covariates improve the transition
   kernel's out-of-sample log loss over the shrunk-multinomial control (rule-#4-style
   control comparison)? Then, separately: does ANY of it add value over market prices?
5. Multiplicity: max-stat permutation on all cell scans (charter principle 7).

## The honest one-liner

The honest, checkable summary: *"I found a bioinformatics paper that fingerprints
protein sequences by their Markov transition grammar plus Wasserstein
distance-to-consensus features, and translated the architecture to NFL play-calling —
coach grammar fingerprints as low-dimensional identity covariates for a play-level
transition kernel, with Dirichlet smoothing on the sparse profiles."* Every clause of
that sentence is true today (the translation exists, the test does not — say so if
asked; the honesty IS the credential, per house policy: never claim untested results).

Related: `research/nfl/model/ESTIMATION_PRINCIPLES_20260812.md` (small-n charter +
shrinkage-targets amendment), task #62 (play-grammar project + Big Data Bowl recon),
task #60 (flip-point lane — the in-game consumer of a better kernel), memory
`nfl-flip-point-thesis`.

Sources: researchgate.net/publication/400440793 (WMRF); arxiv.org/abs/2006.04709
(Wasserstein Random Forests, Du et al.).
