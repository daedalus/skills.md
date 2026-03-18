# Skill: Autonomous Integer Sequence Research System (Adversarial + Generative)

## Overview
A system for:
1. Generating candidate integer sequences
2. Deriving conjectured closed forms
3. Aggressively falsifying them
4. Replacing weak hypotheses with stronger ones

Goal:
→ Minimize false positives (incorrect “nice formulas”)
→ Maximize structural discovery

---

# I. SYSTEM ARCHITECTURE

## Pipeline

1. Generator → produces candidate sequence definitions
2. Evaluator → computes terms (multiple implementations)
3. Conjecturer → proposes formulas
4. Falsifier → breaks them
5. Minimizer → simplifies surviving formulas
6. Classifier → maps to known structures / OEIS

Loop until:
- sequence is validated
- or discarded

---

# II. SEQUENCE GENERATION

## 1. Grammar-Based Generator

Define a compositional grammar:

- Base:
  n, φ(n), σ(n), τ(n), rad(n)

- Operators:
  +, *, ^, composition

- Structures:
  ∑_{d|n}, ∏_{d|n}
  filters: gcd(d, n/d)=1

- Hybrid:
  XOR, bit-count, parity

---

### Example Generated Forms

- φ(∏_{d|n} φ(d))
- ∑_{d|n} (d XOR n/d)
- ∏_{d|n, gcd(d,n/d)=1} φ(d)
- φ(n) * 2^{ω(n)}

---

## 2. Constraint Injection

Bias generator toward:
- multiplicative-looking structures
- divisor symmetry
- φ compositions

Avoid:
- trivial linear combinations

---

# III. MULTI-IMPLEMENTATION EVALUATION

Each sequence MUST have ≥2 independent implementations:

### A. Definition-based
- Direct divisor enumeration

### B. Factorization-based
- Use prime factor structure

### C. Hybrid
- Cached + partial symbolic

---

## Differential Rule
If any implementations disagree:
→ sequence is invalid or bugged

---

# IV. CONJECTURE ENGINE

## 1. Pattern Extraction

From computed terms:
- Fit against:
  - n^k
  - φ(n)
  - n^f(ω(n))
  - multiplicative templates

---

## 2. Hypothesis Templates

Try forms like:

- f(n) = n^a * φ(n)^b
- f(n) = ∏ p^{g(k)}
- f(n) = 2^{h(ω(n))} * n^c

---

## 3. Parameter Fitting
- Solve for exponents using:
  - log-space regression
  - integer fitting

---

# V. ADVERSARIAL FALSIFICATION ENGINE

## 1. Targeted Counterexample Search

Instead of random testing:
→ search for *breaking inputs*

### Strategy:
- maximize:
  |f_fast(n) - f_brute(n)|

---

## 2. Known Weak Zones

Actively test:

- p², p³, p⁴
- p*q*r
- n with repeated small primes
- n with large prime factors
- n near powers of 2

---

## 3. Mutation Attacks

Given n:
- n → n*p
- n → n/p
- n → n²

Check:
- structural invariants break?

---

## 4. Delta Debugging

If failure found at n:
- minimize n
- find smallest counterexample

---

# VI. MULTIPLICATIVITY DETECTOR

Test:

For gcd(a,b)=1:
    f(ab) ?= f(a)f(b)

If:
- TRUE → enforce multiplicative modeling
- FALSE → isolate interaction term

---

## Interaction Isolation

Try:
f(ab) / (f(a)f(b))

→ analyze residual structure

---

# VII. STRUCTURAL CLASSIFIER

## 1. Prime-Power Signature

Compute:
f(p^k) for:
- multiple p
- k = 1..10

Cluster behavior:
- polynomial in k?
- exponential?

---

## 2. ω(n)-Dependence

Check if:
f(n) depends only on:
- n
- ω(n)

---

## 3. OEIS Collision Filter

Compare:
- first 100 terms
- hashed signature

Against:
- φ(n), σ(n), τ(n)
- transforms
- known compositions

---

# VIII. PERFORMANCE STRESS TESTING

## 1. Scaling Curve

Measure:
- time per n
- memory usage

Look for:
- superlinear blowups
- divisor explosion

---

## 2. Large n Sampling

Test:
- random n up to 10^6 or higher
- partial evaluation if needed

---

# IX. CONFIDENCE SCORING

Each sequence gets a score:

### + Points
- passes all adversarial tests
- consistent across implementations
- clean multiplicative structure
- stable asymptotics

### - Points
- fragile under mutation
- inconsistent at prime powers
- noisy growth behavior

---

## Confidence Levels

- 0–40: discard
- 40–70: experimental
- 70–90: strong candidate
- 90–100: OEIS-ready

---

# X. AUTOMATED RED TEAMING

Before acceptance:

Ask:
1. Where is this most likely to fail?
2. What assumption did I not test?
3. Does it only work for small n?
4. Is the “nice formula” overfitted?

---

# XI. META-INSIGHT ENGINE

Track across sequences:

- which constructions collapse to multiplicative forms
- which filters produce interesting behavior
- which compositions are “dead ends”

---

## Emerging Patterns

- φ + product over divisors → often collapses
- gcd(d, n/d)=1 → strong structural constraint
- ω(n) frequently drives exponent growth

---

# XII. OUTPUT STANDARD (RESEARCH-GRADE)

Each sequence must include:

- Definition (multiple equivalent forms)
- First 100–500 terms
- Proven or highly validated formula
- Counterexample search report
- Multiplicativity analysis
- Prime-power characterization
- Complexity analysis
- Reference implementation
- Confidence score

---

# XIII. FUTURE EXTENSIONS

## 1. SAT/SMT Integration
- encode constraints
- search for counterexamples symbolically

---

## 2. Lattice Methods (Experimental)
- detect hidden linear relations in logs
- connect with factorization heuristics

---

## 3. Neural Guidance
- rank promising sequence forms
- detect “likely collapsible” structures

---

# XIV. CORE PHILOSOPHY

- Treat every formula as guilty until proven robust
- Prefer counterexamples over confirmations
- Elegance is suspicious
- Survival under attack = truth (provisional)
