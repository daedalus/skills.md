---
name: rebuild-benchmark-audit
description: Audit and construct verifier-graded "rebuild the program" benchmarks and RLVR reward environments — hunting duplicate reward, shortcut-passable tests, ambient implementations already installed in the task image, proxy/short-circuit assertions, wall-clock time bombs, unreachable tests with missing fixtures, and grader-only dependencies. Use this whenever the user mentions ProgramBench, SWE-style or agentic benchmark construction, cleanroom task images, gold/dummy test validation, behavioral test suites as reward, verifier design, reward hacking, test-suite deduplication, or asks why a model scores suspiciously high or low on a coding benchmark — even if they don't use the word "benchmark". Also use it when designing the same recipe for APIs, libraries, protocol daemons, or data pipelines.
---

# Rebuild-benchmark audit and construction

A rebuild benchmark seals a working artifact (classically a compiled CLI), keeps its
documentation, deletes source and history, and grades an agent's reimplementation with a
generated behavioral test suite. The suite is the whole specification of reward. So the
quality question is never "is this task hard?" — it is **"does each point of reward
correspond to the behavior it claims to measure?"**

Use this skill to audit an existing suite, to build a new one, or to diagnose an anomalous
score.

## The task package

Fix these mechanics before anything else, because every audit fraction below is meaningless
without them. The reference implementation of the format (ProgramBench, Meta, May 2026,
200 tasks; ProgramBench Vetted, 50 held-out tasks) works like this:

- **What the agent gets:** a compiled reference it can *execute but not read*, the project's
  retained documentation, a shell, and a workspace. **What is removed:** source, git
  history, upstream tests, and internet access.
- **Budget:** on the order of 1,000 steps and 6 hours, where a step is one model call.
- **Grading:** the generated behavioral suite runs against the reconstruction. The task score
  is the fraction of active tests passed; a task is **resolved** only at 100%. Report
  pass@1 and name the harness configuration (e.g. the default mini-SWE-agent setup) —
  scores are not comparable across harnesses.
- **A submission that does not compile or run scores zero**, not "no data". Decide this
  explicitly; it visibly moves survival curves.
- **Health signal:** in the reference analysis, frontier agents spent 23–34% of their actions
  probing the binary. Empirical investigation should be a substantial fraction of the
  trajectory. If it is not, the documentation is probably carrying the score — which is
  exactly the defect the documentation-facade control below detects.

## The governing insight

Standard validation requires each generated test to **pass the gold binary** and **fail a
dummy binary**. Both gates are necessary. Neither, nor both together, is sufficient — they
prove a test is *runnable* and *not vacuous*, but say nothing about whether passing it
required rebuilding anything.

Two independent gates that most pipelines omit:

1. **Passability** — can an authentic implementation pass this test at all, given only what
   the agent is handed?
2. **Earnedness** — is there a cheaper path to the point than reconstruction?

Audit both. Failing either makes the score mean something other than what it claims.

## Audit procedure

Run the control battery first (it is cheap and finds most of the damage), then the
per-class checks. Score everything against the **active/scored** manifest only; exclude
ignored IDs and count missing or skipped active IDs as failures, or the fractions are not
comparable.

### Step 1 — The control battery

Build four deliberately-not-solutions and score each against the full active suite. Each
one isolates a different defect.

| Control | What to build | What a pass means |
|---|---|---|
| **Null program** | `int main(void){return 0;}` | Skill-independent reward floor: tests that accept silence, empty output, or "nothing happened" without first proving the behavior ran |
| **Documentation facade** | Prints only the help/version/usage/error text copied from the docs; shallow arg checks; implements no core behavior | Reward attached to the CLI surface rather than the program |
| **Ambient delegate** | A thin wrapper that `execv`s or links whatever implementation is already installed in the image | Environment leak: the container ships the answer |
| **Ablated delegate** | Same wrapper, but the calls into the ambient implementation are made to fail | Causal control — the delta between this and the delegate is reward attributable to the installed software, not the candidate |

Reference magnitudes from the published audit of the original ProgramBench release (useful
as calibration for "is my number bad?"): a null program passed 23/477 `nnn`, 19/792 `xq`,
22/1994 `ripgrep` active tests; a 99-line non-rendering `cmatrix` facade passed 403/507
(79.5%); an eight-line `execv` wrapper around the preinstalled `/usr/bin/xz` passed
1090/1410 (77.3%); a 349-line adapter over `liblz4.so.1` passed 557/1496 (37.2%), of which
31.62 percentage points vanished when the library calls were ablated.

Always re-run the winning control in a digest-pinned, no-network rebuild to confirm the
hash and the aggregate reproduce, and delete the ambient binary/library from a disposable
copy of the image to prove causation rather than correlation.

### Step 2 — Per-class checks

**Ambient implementations.** Enumerate what the cleanroom already provides:
`which`/`command -v` for every plausible name and alias of the target, `ldconfig -p` and
`ldd` for the target's library, package manifests, `/workspace` for stray copies. Compare
SHA-256 of everything readable against the sealed reference — a match (as with the
paper-era Ctags image shipping a readable `/workspace/ctags` identical to the gold
executable) means the task measures discovery, not reconstruction. Verify with
`NEEDED`/dynamic-section inspection of any candidate binary.

**Proxy and short-circuit assertions.** Grep the scored suite for tests whose invocation
includes an early-exit flag (`-V`, `--version`, `-h`, `--help`) alongside the flag the test
is named after — the program exits before the named behavior runs. Also flag assertions
that are satisfied by almost any output (`assert b"." in stdout`, length thresholds,
`returncode == 0` alone) and disjunctions that admit the empty case
(`stdout == b"" or ...`). A test named `test_color_option_accepted` that asserts only that
a version banner printed is grading the banner.

**Named shortcut classes to probe deliberately.** Beyond the controls, sweep the suite for
these four shapes, each of which produces reward without reconstruction:
- **non-varying gold behavior** — the reference emits the same output across the whole input
  range the test explores, so any constant reproduces it;
- **reachable reference implementations** — the answer is present in the environment (see
  below) or derivable from a retained asset;
- **constant-pinning tests** — the assertion pins a literal captured at generation time
  (a banner, a hash, a version, a date) rather than a behavior;
- **degenerate suite shapes** — reward concentrated on one narrow family of checks, or a
  suite whose score is effectively a single all-or-nothing block.

**Wall-clock and environment time bombs.** Grep for hardcoded years, dates, versions,
hostnames, paths, and locale assumptions in assertions. Re-run the suite with the container
date advanced by one year and by one day across a DST boundary; anything that flips is
grading the calendar. A test that hard-asserts the generation year passes today and fails
every implementation, gold included, from next year on.

**Unreachable requirements.** Replay the full active suite against the released gold
binary (and, if available, a second authentic build). Any test gold fails is measuring
packaging, not reconstruction — the canonical case is 1,029 of 1,091 active FFmpeg FATE
cases requiring media that was never shipped. Then invert the screen: list active tests
with no pass in any available public per-test result, and check each against gold. That
screen does not prove impossibility; it tells you where to look.

Every screened test needs an **authentic passing witness** — the released gold, or another
genuine build of the same product at a compatible revision. In the reference audit, all
five heavily-unreached tasks (PHP, Ctags, Cppcheck, Pandoc, GROMACS) turned out to have
witnesses for every screened identity, so the finding was *not* a broken subset; it was a
recoverability problem, which is a different report. Only FFmpeg was genuinely unreachable.

**Grader-only dependencies (asymmetric execution).** Diff what the *grading* fixture sets
up against what the *inference* cleanroom contains. If the fixture copies in a config,
data directory, or path setting the agent never had, the agent could not probe the behavior
it is scored on — Cppcheck's core analysis path dies on a missing `std.cfg` during
inference while the grader restores it. Treat every fixture-side `cp`, `export`, and
`mkdir` as a suspect.

**Duplicate and subsumed reward.** Two tests are duplicates when they exercise the same or
materially similar behavior, or when one subsumes the other. Detect in layers, because no
single layer is enough:
- deterministic: exact and structural repetition, normalized command + assertion shape;
- embedding/clustering: combine multiple test embeddings, project (e.g. UMAP) and inspect
  neighborhoods — but proximity alone is not duplication, since tests cluster on shared
  scaffolding;
- agentic: classify candidate pairs for same-behavior or subsumption;
- human: resolve ambiguous pairs, and feed each new pattern back into the earlier layers.

Report the removable share after retaining one representative per cluster. In a 60-task
audit the median task carried 11% removable duplicates, over half were above a tenth, and
the worst was 37%; a broad task like QuickJS sat at 6.1%. Duplication is not cosmetic — a
behavior counted *n* times is worth *n* times the gradient of an equivalent single
requirement, which reweights the objective toward whatever the generators happened to
rediscover.

**Recoverability.** The last and least mechanical gate, and the one most often skipped.
Passability says a configured grader can produce a pass; recoverability asks whether an
agent could plausibly *identify* the required behavior from the supplied documentation and
probes within its episode budget. The reference binary is an oracle only after the agent
has guessed the question. Sample active tests and ask what the agent would have had to
guess. The five diagnosed shapes are distinct and call for different repairs:

| Shape | Example | Repair direction |
|---|---|---|
| Sparse spec vs. huge historical regression surface | PHP: 10,259 of 10,880 unreached cases harvested from the upstream PHPT suite, 10,234 of them text-exact at the pinned revision, with nothing pointing the agent at a particular DST or OPcache regression | Retain more spec, or drop the unadvertised historical block |
| Environment leak | Ctags: the evaluated image also shipped a readable `/workspace/ctags` with the same SHA-256 as the sealed reference, plus `libctags.a` | Reseal the environment |
| Oracle incomplete during inference | Cppcheck: core analysis aborts on a missing `std.cfg` the grader restores, so 242 of 249 dump-protocol tests were never probeable | Give inference the same dependency, or cut the block |
| Breadth and exactness | Pandoc: well documented and introspectable, but 2,487 of 3,378 unreached cases assert exact stdout/stderr equality, including an 8,928-byte AST literal | Accept as legitimate, but watch the correlated block |
| Probe assets withheld | GROMACS: commands documented, but the trajectories, topologies, and force-field directories that 964 of 1,039 unreached tests need are supplied only to the grader | Ship representative fixtures into the cleanroom |

The calibration concern in all five is **correlated reward blocks**: when one missing
convention, format, or intermediate representation erases hundreds of tests at once, the
score stops tracking incremental progress and useful partial work becomes invisible. Report
recoverability findings as their own class — they are calibration problems, not bugs, and
exact output can be a perfectly legitimate requirement.

### Step 3 — Calibration

Run several models across the candidate set and study the distribution of partial credit,
not just the mean.

- Report three numbers per model: **mean reward** (macro average of fractional test score),
  **almost** (share of tasks ≥95%), **resolved** (share at 100%). They dissociate: a model
  can lead mean reward and trail resolved.
- Draw **fractional-score survival curves** — share of tasks at or above each threshold from
  0 to 100%. Curves that stay separated across the threshold range preserve model
  differences; curves that collapse into one band do not.
- Bin tasks by mean fractional score across the model panel. Target most of the mass in the
  **20–80%** range: enough accessible behavior to measure progress, enough unsolved
  behavior to leave headroom. Tasks that land near-uniformly solved, near-uniformly failed,
  or on a sharp all-or-nothing threshold need review, not celebration.
- Track average model calls per task. Longer trajectories indicate more interaction; they
  do not by themselves measure difficulty, cost, or reasoning tokens, so don't present them
  as such.

Comparisons across two benchmarks are descriptive unless the model panels match exactly.
If only a subset of configurations overlaps, if one panel includes small models the other
omits, or if some rows are vendor-reported rather than replicated, say so and mark those
rows; a mixed direction of change across the overlapping configurations does not license
calling either benchmark harder.

Difficulty alone is never evidence of quality. A task can be brutally hard *because* it is
broken.

## Construction pipeline

When building rather than auditing, validate and repair continuously instead of relying on
one final review. Four stages, each with the same shape: deterministic gates where a
property can be measured exactly, an **investigating judge** that scores and produces
evidence, a paired **doctor** that makes a constrained repair using that evidence and
returns to the same judge, and escalation to a human after N failed rounds. Human findings
become new criteria for later runs.

**Stage 1 — Source and build.** Select a repository (compiled languages travel best; C,
C++, Rust have the deepest transferable build expertise). Sourcing judge scores viability;
build agent produces the gold binary; deterministic gates check compile, launch, and
behavior; build judge/doctor loop until it holds. Output: gold binary plus cleanroom basis.

Select against a **fixed taxonomy** so the set does not collapse into one kind of CLI. The
reference 50-task mix: interpreters/compilers/VMs (18), assemblers and disassemblers (12),
structured-data codecs (7), developer tools (4), media and geometry processing (4),
mathematical and constraint-solving tools (3), machine and console emulators (2). The
archetype is a language implementation — its input space is unbounded and cheap to explore,
so every new program is another behavior to pin. Note that calibrated tasks from small,
less familiar repositories sustained *longer* trajectories than the original set, so
picking giant projects like FFmpeg is not how you get long-horizon work.

**Stage 2 — Generate and deduplicate.** Run many independent test-generation branches
(e.g. up to 15 trials across several frontier models) with source, docs, existing tests, and
coverage guidance. Gate each generated test on reliable execution, gold pass, and dummy
fail. Then deduplicate, so extra branches *broaden* the suite instead of multiplying credit
for the same behavior.

**Stage 3 — Audit and repair the cleanroom and the tests together.** They are one system.
A leak judge checks the environment for ambient implementations, readable references, and
shortcut surfaces; a test-quality judge checks reachability, stability, and whether an
assertion measures its stated subject. Optional doctors repair; unresolved cases go to a
human; any repair re-clears the affected criteria.

**Stage 4 — Calibration and adversarial approval.** Run normal inference with several
models *and* adversarial inference whose explicit instruction is to find the cheapest path
to reward ("determine which system library or CLI already implements this; write a thin
wrapper; implement none of the algorithm yourself"). A general-quality judge weighs both
streams for fairness, reliability, and hackability. The accept/repair/reject decision stays
human.

Distribute effort across specialized stages rather than one general check: build integrity,
environment leaks, test quality, and reward exploits require different investigations and no
single score covers them.

Expect scale: the original release carried 247,723 active test IDs across 1,759 generation
branches, so every gate above has to be mechanized before it can be applied corpus-wide.
Human review is the escape hatch for ambiguity and the source of new criteria, not the
first line of defense.

**Maintenance.** A benchmark is a living artifact. Each revision should be (1) *more fair* —
broader task mix, fewer shortcuts, fewer requirements a real implementation cannot satisfy;
(2) *more reliable* — stronger replay, deduplication, environment controls, ongoing
validation; (3) *harder as models improve* — more demanding but still reachable behavior, so
partial progress stays measurable and stronger models keep headroom.

## Reporting format

Write each finding as four labeled parts, and keep the claims inside what was actually
executed:

```
**What we tested.**   exact candidate, image digest, manifest, active/ignored counts
**What we found.**    counts and fractions, e.g. 1,090 / 1,410 (77.30%)
**Why it happened.**  the mechanism, not the symptom
**Implications.**     separately for evaluation (ranking distortion) and for RLVR (objective weighting)
```

For any executed exploit, attach an identity-and-replay table so a reader can reproduce it:

| Field | Content |
|---|---|
| task | task ID and pinned upstream commit |
| public artifacts | test suite location, upstream source at the pinned commit |
| pinned environment | image digest, plus the exact ambient versions vs. gold (e.g. `/usr/bin/xz` 5.2.5 against gold 5.8.2) |
| retained candidate | source hash, binary hash, and confirmation both differ from gold |
| active-only result | `N / M (xx.xx%)`, ignored count excluded, and zero skipped/missing/timed-out |
| independent replay | digest-pinned no-network rebuild reproducing hash and aggregate; note any cross-architecture divergence and its cause |
| causal control | what removing or ablating the shortcut does to the score |

Divergences are findings, not noise: an amd64-on-arm64 replay landing one test lower because
an 80 MiB case crossed a 40-second internal timeout belongs in the table.

State the evidence boundary explicitly: "no eligible public pass" means no available
artifact reports a pass, not that every model failed. Do not silently convert missing rows
into failures. Where a trajectory's own narration explains a result, distrust it and rely on
retained commands, source, and verifier output. Keep the scope of the claim tight — say which
artifacts are yours (candidates, trajectories) and which are the original dataset's (images,
manifests, scored suites), and don't generalize a mechanism demonstrated on two tasks into a
prevalence claim about the corpus.

## Extending the recipe beyond CLIs

Nothing here is specific to compiled binaries. The general form: seal an artifact whose
behavior is observable but whose internals are hidden, keep its documentation, generate a
behavioral spec by probing it, guard the reward against shortcuts, grade rebuilds against
that spec. Each variant brings its own way to buy the reward — name it and gate it before
generating a single test:

- **APIs and servers** — proxying requests to the reference *is* this family's ambient
  implementation defect. Verify response parity, status codes, error semantics, and state
  across call sequences.
- **Libraries and SDKs** — ship a wheel, jar, or shared object without source; grade through
  the documented public interface; ban linking the original.
- **Protocol daemons** — verification is interoperability: the rebuilt server satisfies the
  reference client and vice versa.
- **Data pipelines** — a sealed transform plus a purpose description; check output parity on
  held-out inputs including probe-discovered edge cases.
- **Spec-first (no reference binary)** — an explicit specification replaces the probeable
  oracle, and every test must trace to and stay coherent with that spec.

## Framing caveats to keep in the report

- The verifier grades behavioral reproduction only. Code quality, structure, speed, memory,
  and footprint go unmeasured; a monolith that matches scores identically to a clean design.
- A rebuild task hands the agent a perfect oracle for the spec — something real engineering
  almost never has. Saturating it does not imply general engineering ability.
- For evaluation a weak suite distorts a ranking. For reinforcement learning the same suite
  *is* the objective: the tests do not describe the task, they are the task.

## Contamination and the memorization paradox

Rebuild tasks are drawn from public repositories, so prior exposure is plausible and hard to
measure. Do not resolve this by assertion in either direction.

What the evidence supports: exposure creates a strong pull toward retrieval — an
internet-access ablation flagged up to 36% of runs as cheating, mostly source lookup — while
saying nothing about what is in the weights. At launch, zero tasks were resolved. And prior
exposure does not imply retrievability: moving from observed behavior back to code is the
reversal direction, which models handle far worse than the forward one.

So on in-corpus repositories, success mixes *remembering* with *reverse engineering* in
unknown proportions. Forcing a different implementation language blunts recall but does not
measure it. Absent matched contamination or name-masking ablations, report the composite
capability and label it as such.

The same ambiguity is usable as a training instrument if membership labels are verified:
in-corpus RL tests whether training improves *access to* prior representations; out-of-corpus
RL on repositories verified absent from pretraining tests transferable reverse-engineering
skill; and checkpoint-level score changes across matched in- and out-of-corpus tasks become a
diagnostic separating retrieval from newly learned problem-solving. Each of these needs the
membership verification to be real, or it measures nothing.

## Provenance

Distilled from Vetto's ProgramBench Vetted writeup (`vetto.ai/companies/programbench-vetted.html`,
retrieved August 2026), which documents 50 held-out tasks plus executed audits of Meta's
original ProgramBench release (May 2026). Figures cited above are that report's measurements
on its audited samples — treat them as calibration reference points, not corpus-wide rates,
and re-derive them for any suite you audit.
