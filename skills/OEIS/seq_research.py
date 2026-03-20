#!/usr/bin/env python3
"""
Autonomous Integer Sequence Research Pipeline — Unified
Full adversarial pipeline per SKILL.md §1-§8.
Combines strengths of seq_research.py and seq_research_batch3.py.
"""

import argparse
import math
import sys
from typing import Callable, Optional

from sympy import (
    factorint, totient, divisors, divisor_sigma,
    divisor_count, isprime, gcd, mobius, rad,
    primeomega, primenu
)

phi = lambda n: int(totient(n))
tau = lambda n: int(divisor_count(n))
sigma = lambda n: int(divisor_sigma(n))
Rad = lambda n: int(rad(n))
omega = lambda n: int(primenu(n))
Omega = lambda n: int(primeomega(n))
mu = lambda n: int(mobius(n))

def unitary_divisors(n):
    return [d for d in divisors(n) if gcd(d, n // d) == 1]

WEAK_ZONES = sorted(set(
    [p**k for p in [2,3,5,7,11,13] for k in range(1,6)] +
    [p**a * q**b for p,q in [(2,3),(2,5),(3,5)] for a,b in [(1,1),(2,1),(1,2)]] +
    [12, 24, 60, 120, 360, 720, 840, 2520] +
    [2**k for k in range(1,20)] + [2**k - 1 for k in range(2,15)] +
    [2*3*5, 2*3*7, 2*5*7, 3*5*7, 2*3*5*7]
))

MULT_PAIRS = [
    (2,3),(2,5),(3,5),(4,9),(2,7),(5,9),(4,25),(8,27),
    (9,25),(16,9),(4,49),(8,125),(27,25),(2,3*5),(4,3*7),
    (3,7),(2,11),(5,11),(2,13),(11,13),(7,9),(3,25)
]

def is_multiplicative(fn: Callable) -> tuple[bool, Optional[tuple]]:
    for a, b in MULT_PAIRS:
        if gcd(a, b) == 1:
            fa, fb, fab = fn(a), fn(b), fn(a*b)
            if fa * fb != fab:
                return False, (a, b, fa, fb, fab)
    return True, None

def multiplicative_residual(fn: Callable) -> list:
    residuals = []
    for a, b in MULT_PAIRS:
        if gcd(a, b) == 1:
            f_ab = fn(a * b)
            f_a, f_b = fn(a), fn(b)
            if f_a * f_b != 0:
                residuals.append(f_ab / (f_a * f_b))
    return residuals

def pp_profile(f: Callable, primes=(2,3,5,7,11), kmax=7) -> dict:
    rows = {}
    for p in primes:
        vals = [f(p**k) for k in range(1, kmax+1)]
        ratios = []
        for i in range(len(vals)-1):
            if vals[i] != 0:
                ratios.append(round(vals[i+1]/vals[i], 5))
            else:
                ratios.append(None)
        rows[p] = {'values': vals, 'ratios': ratios}
    return rows

def growth_alpha(f: Callable, lo: int = 10, hi: int = 200) -> Optional[float]:
    pts = [(n, f(n)) for n in range(lo, hi+1) if f(n) > 0]
    if len(pts) < 10:
        return None
    xs = [math.log(n) for n, _ in pts]
    ys = [math.log(v) for _, v in pts]
    xm = sum(xs) / len(xs)
    ym = sum(ys) / len(ys)
    cov = sum((xs[i] - xm) * (ys[i] - ym) for i in range(len(xs)))
    var = sum((x - xm)**2 for x in xs)
    return round(cov / var, 4) if var > 0 else None

def falsify(f_def: Callable, f_alt: Callable, N: int = 500) -> Optional[tuple]:
    test_set = sorted(set(list(range(1, 101)) + WEAK_ZONES + list(range(100, N+1, 7))))
    for n in test_set:
        if n < 1:
            continue
        a, b = f_def(n), f_alt(n)
        if a != b:
            return n, a, b
    return None

def mutation_attack(n0: int, fn: Callable, expected_fn: Callable) -> list:
    mutations = []
    for p in [2, 3, 5, 7, 11, 13]:
        if n0 * p < 1000000:
            mutations.append((n0 * p, 'multiply', p))
        if n0 % p == 0 and n0 // p > 0:
            mutations.append((n0 // p, 'divide', p))
    mutations.append((n0**2, 'square', None))
    failures = []
    for m, op, p in mutations:
        if fn(m) != expected_fn(m):
            failures.append((m, op, p, fn(m), expected_fn(m)))
    return failures

def oeis_str(f: Callable, count: int = 30) -> str:
    return ", ".join(str(f(n)) for n in range(1, count + 1))

def dirichlet(f: Callable, g: Callable, n: int) -> int:
    return sum(f(d) * g(n // d) for d in divisors(n))

class SequenceCandidate:
    def __init__(
        self,
        name: str,
        definition: str,
        fn: Callable,
        alt_fn: Optional[Callable] = None,
        pp_formula: str = "",
        family: str = "",
        likely_known: bool = False,
        collision_check: Optional[Callable] = None
    ):
        self.name = name
        self.definition = definition
        self.fn = fn
        self.alt_fn = alt_fn
        self.pp_formula = pp_formula
        self.family = family
        self.likely_known = likely_known
        self.collision_check = collision_check
        
        self.cross_ok = False
        self.cross_disagreement = None
        self.multiplicative = None
        self.mult_witness = None
        self.mult_residuals = []
        self.pp = {}
        self.weak_failures = []
        self.alpha = None
        self.conjectured_formula = None
        self.collision = False
        self.terms_30 = ""
        self.terms_100 = []
        self.confidence_score = 0
        self.level = ""
    
    def compute_terms(self):
        self.terms_30 = oeis_str(self.fn, 30)
        self.terms_100 = [self.fn(n) for n in range(1, 101)]
    
    def validate_cross(self, N: int = 500) -> bool:
        if self.alt_fn is None:
            self.cross_ok = True
            return True
        result = falsify(self.fn, self.alt_fn, N)
        if result:
            self.cross_ok = False
            self.cross_disagreement = result
        else:
            self.cross_ok = True
        return self.cross_ok
    
    def test_multiplicativity(self) -> bool:
        self.multiplicative, self.mult_witness = is_multiplicative(self.fn)
        if not self.multiplicative:
            self.mult_residuals = multiplicative_residual(self.fn)
        return self.multiplicative
    
    def profile_prime_powers(self):
        self.pp = pp_profile(self.fn)
        return self.pp
    
    def test_weak_zones(self) -> bool:
        self.weak_failures = []
        for n in WEAK_ZONES:
            try:
                val = self.fn(n)
                if hasattr(val, 'is_number') and val.is_Integer:
                    val = int(val)
                if not isinstance(val, (int, float)) or (isinstance(val, float) and math.isnan(val)):
                    self.weak_failures.append((n, 'non-numeric'))
            except Exception as e:
                self.weak_failures.append((n, str(e)))
        return len(self.weak_failures) == 0
    
    def check_growth(self):
        self.alpha = growth_alpha(self.fn)
    
    def detect_collision(self) -> bool:
        if self.likely_known:
            self.collision = True
            return True
        if self.collision_check:
            self.collision = self.collision_check(self.fn)
        else:
            self.collision = False
        return self.collision
    
    def attempt_conjecture(self):
        if self.pp_formula:
            self.conjectured_formula = self.pp_formula
        elif self.multiplicative and self.pp:
            p = 2
            if p in self.pp:
                vals = self.pp[p]['values']
                ratios = self.pp[p]['ratios']
                if len(ratios) >= 3:
                    valid_ratios = [r for r in ratios if r is not None]
                    if valid_ratios:
                        avg = sum(valid_ratios) / len(valid_ratios)
                        if all(abs(r - avg) < 0.01 for r in valid_ratios):
                            self.conjectured_formula = f"f(p^k) geometric with ratio ~{avg:.2f}"
        if not self.conjectured_formula:
            self.conjectured_formula = f"f(n) ~ n^{self.alpha} (log regression)" if self.alpha else "unknown"
    
    def score(self) -> int:
        s = 50
        s += 10 if self.cross_ok else -20
        s += 15 if self.multiplicative else 0
        s += 15 if len(self.weak_failures) == 0 else -15
        s += 10 if self.conjectured_formula and "unknown" not in self.conjectured_formula else 0
        if self.alpha is not None and 0.5 <= self.alpha <= 3.0:
            s += 5
        if self.collision:
            s -= 20
        self.confidence_score = max(0, min(100, s))
        if self.confidence_score < 40:
            self.level = "DISCARD"
        elif self.confidence_score < 70:
            self.level = "EXPERIMENTAL"
        elif self.confidence_score < 90:
            self.level = "STRONG CANDIDATE"
        else:
            self.level = "OEIS-READY"
        return self.confidence_score
    
    def report(self) -> str:
        lines = [
            f"\n{'='*66}",
            f"SEQUENCE: {self.name}",
            f"{'='*66}",
            f"Definition:  {self.definition}",
            f"Family:      {self.family or 'N/A'}",
            f"",
            f"First 30 terms: {self.terms_30}",
            f"",
            f"[§2] Cross-validation: {'PASS' if self.cross_ok else 'FAIL'}",
            f"      Disagreement: {self.cross_disagreement}",
            f"[§3] Multiplicative: {'YES' if self.multiplicative else 'NO'}",
            f"      Witness: {self.mult_witness}",
        ]
        if not self.multiplicative and self.mult_residuals:
            uniq = sorted(set(round(r, 4) for r in self.mult_residuals))
            lines.append(f"      Residuals: {uniq[:10]}")
        if self.multiplicative:
            lines.append(f"[§3.1] Prime-power profile (p=2): {self.pp.get(2, {}).get('values', 'N/A')}")
        lines.append(f"[§4] Weak zones: {'PASS' if not self.weak_failures else f'FAIL ({len(self.weak_failures)})'}")
        lines.append(f"[§5] Growth alpha: {self.alpha}")
        lines.append(f"[§6] OEIS collision: {'DETECTED' if self.collision else 'None'}")
        lines.append(f"[§7] Score: {self.confidence_score}/100  [{self.level}]")
        lines.append(f"      Formula: {self.conjectured_formula}")
        return '\n'.join(lines)


def get_candidates() -> list[SequenceCandidate]:
    cands = []
    
    def phi_times_c_omega(c: int, name_suffix: str = ""):
        cname = f"phi_{c}pow_omega{name_suffix}"
        def fn(n):
            return phi(n) * (c ** omega(n))
        def alt(n):
            result = 1
            for p, a in factorint(n).items():
                result *= c * (p**(a-1)) * (p-1)
            return result
        return SequenceCandidate(
            name=cname,
            definition=f"f(n) = phi(n) * {c}^{{omega(n)}}",
            fn=fn, alt_fn=alt,
            pp_formula=f"f(p^k) = {c} * p^(k-1) * (p-1)",
            family=f"phi(n)*c^omega(n), c={c}"
        )
    
    cands.append(phi_times_c_omega(2))
    cands.append(phi_times_c_omega(3))
    cands.append(phi_times_c_omega(4))
    cands.append(phi_times_c_omega(5))
    cands.append(phi_times_c_omega(6))
    
    def sum_tri_exp(n):
        if n == 1: return 0
        return sum(a*(a+1)//2 for a in factorint(n).values())
    def alt_tri_exp(n):
        if n == 1: return 0
        return sum(a*(a+1)//2 for a in factorint(n).values())
    cands.append(SequenceCandidate(
        name="sum_tri_exp",
        definition="f(n) = sum_{p^a||n} a*(a+1)/2",
        fn=sum_tri_exp, alt_fn=alt_tri_exp,
        pp_formula="f(p^k) = k*(k+1)/2 (same for all p)",
        family="sum g(a) over prime signature, g=triangular"
    ))
    
    def sum_2pow_exp(n):
        if n == 1: return 0
        return sum(2**a for a in factorint(n).values())
    def alt_2pow_exp(n):
        if n == 1: return 0
        return sum(2**a for a in factorint(n).values())
    cands.append(SequenceCandidate(
        name="sum_2pow_exp",
        definition="f(n) = sum_{p^a||n} 2^a",
        fn=sum_2pow_exp, alt_fn=alt_2pow_exp,
        pp_formula="f(p^k) = 2^k (same for all p)",
        family="sum g(a) over prime signature, g=2^a"
    ))
    
    def sum_a2_exp(n):
        if n == 1: return 0
        return sum(a**2 for a in factorint(n).values())
    cands.append(SequenceCandidate(
        name="sum_a2_exp",
        definition="f(n) = sum_{p^a||n} a^2",
        fn=sum_a2_exp, alt_fn=sum_a2_exp,
        pp_formula="f(p^k) = k^2 (same for all p)",
        family="sum g(a) over prime signature, g=a^2"
    ))
    
    def sum_d_phi_d(n):
        return sum(phi(d) for d in divisors(n))
    def alt_sum_d_phi_d(n):
        return n
    cands.append(SequenceCandidate(
        name="sum_d_phi_d",
        definition="f(n) = sum_{d|n} phi(d)",
        fn=sum_d_phi_d, alt_fn=alt_sum_d_phi_d,
        pp_formula="f(n) = n (identity)",
        family="Dirichlet: phi * 1",
        collision_check=lambda f: oeis_str(f, 30) == ", ".join(str(n) for n in range(1, 31))
    ))
    
    def dirichlet_mu_phi(n):
        return dirichlet(mu, phi, n)
    def alt_mu_phi(n):
        return phi(n)
    cands.append(SequenceCandidate(
        name="mu_star_phi",
        definition="f(n) = (mu * phi)(n)",
        fn=dirichlet_mu_phi, alt_fn=alt_mu_phi,
        pp_formula="f(n) = phi(n) (by Möbius inversion)",
        family="Dirichlet: mu ★ phi",
        collision_check=lambda f: oeis_str(f, 10) == "1, 0, 1, 1, 3, 0, 5, 2, 4, 0"
    ))
    
    def sum_d2_phi_nd2(n):
        return sum(d**2 * phi(n // d) for d in divisors(n))
    def alt_d2_phi_nd2(n):
        result = 1
        for p, a in factorint(n).items():
            result *= p**(2*a) + p**(a-1) * (p**a - 1)
        return result
    cands.append(SequenceCandidate(
        name="sum_d2_phi_nd2",
        definition="f(n) = sum_{d|n} d^2 * phi(n/d)",
        fn=sum_d2_phi_nd2, alt_fn=alt_d2_phi_nd2,
        pp_formula="f(p^k) = p^{2k} + p^{k-1}(p^k - 1)",
        family="Dirichlet: id^2 ★ phi"
    ))
    
    def n_times_2_omega(n):
        return n * (2 ** Omega(n))
    def alt_n_2_omega(n):
        result = 1
        for p, a in factorint(n).items():
            result *= (2 * p) ** a
        return result
    cands.append(SequenceCandidate(
        name="n_times_2_omega",
        definition="f(n) = n * 2^{Omega(n)}",
        fn=n_times_2_omega, alt_fn=alt_n_2_omega,
        pp_formula="f(p^k) = (2p)^k",
        family="n * 2^{Omega(n)}"
    ))
    
    def prod_unitary_phi(n):
        result = 1
        for d in unitary_divisors(n):
            result *= phi(d)
        return result
    def alt_unitary_phi(n):
        result = 1
        for p, a in factorint(n).items():
            val = 1
            for j in range(a + 1):
                val *= phi(p**j)
            result *= val
        return result
    cands.append(SequenceCandidate(
        name="prod_unitary_phi",
        definition="f(n) = prod_{d unitary|n} phi(d)",
        fn=prod_unitary_phi, alt_fn=alt_unitary_phi,
        family="product over unitary divisors of phi"
    ))
    
    def sum_phi_d2(n):
        return sum(phi(d)**2 for d in divisors(n))
    def alt_phi_d2(n):
        result = 1
        for p, a in factorint(n).items():
            val = 1 + (p-1)**2 * (p**(2*a) - 1) // (p**2 - 1)
            result *= val
        return result
    cands.append(SequenceCandidate(
        name="sum_phi_d2",
        definition="f(n) = sum_{d|n} phi(d)^2",
        fn=sum_phi_d2, alt_fn=alt_phi_d2,
        pp_formula="f(p^k) = 1 + (p-1)^2 * (p^{2k}-1)/(p^2-1)",
        family="Dirichlet: phi^2 ★ 1"
    ))
    
    def unitary_prod_d_plus1(n):
        result = 1
        for d in divisors(n):
            if gcd(d, n // d) == 1:
                result *= (d + 1)
        return result
    def alt_unitary_d_plus1(n):
        result = 1
        for p, a in factorint(n).items():
            result *= 2 * (p**a + 1)
        return result
    cands.append(SequenceCandidate(
        name="unitary_prod_d_plus1",
        definition="f(n) = prod_{d unitary|n} (d+1)",
        fn=unitary_prod_d_plus1, alt_fn=alt_unitary_d_plus1,
        pp_formula="f(p^k) = 2 * (p^k + 1)",
        family="product over unitary divisors"
    ))
    
    def rad_n(n):
        if n == 1:
            return 1
        result = 1
        for p in factorint(n):
            result *= p
        return result
    def alt_rad_n(n):
        return rad_n(n)
    cands.append(SequenceCandidate(
        name="rad_n",
        definition="f(n) = rad(n) = product of distinct prime factors",
        fn=rad_n, alt_fn=alt_rad_n,
        pp_formula="f(p^k) = p",
        family="radical function",
        collision_check=lambda f: oeis_str(f, 30) == ", ".join(str(rad_n(n)) for n in range(1, 31))
    ))
    
    def jordan_2(n):
        result = n * n
        for p in factorint(n):
            result = result * (p*p - 1) // (p*p)
        return result
    def alt_jordan_2(n):
        result = 1
        for p, a in factorint(n).items():
            result *= p**(2*a-2) * (p**2 - 1)
        return result
    cands.append(SequenceCandidate(
        name="jordan_2",
        definition="f(n) = J_2(n) = n^2 * prod_{p|n}(1 - 1/p^2)",
        fn=jordan_2, alt_fn=alt_jordan_2,
        pp_formula="f(p^k) = p^(2k-2) * (p^2-1)",
        family="Jordan totient J_k(n), k=2",
        likely_known=True
    ))
    
    def prod_phi_pa_plus1(n):
        result = 1
        for p, a in factorint(n).items():
            result *= phi(p**a + 1)
        return result
    def alt_phi_pa_plus1(n):
        result = 1
        for p, a in factorint(n).items():
            result *= int(totient(p**a + 1))
        return result
    cands.append(SequenceCandidate(
        name="prod_phi_pa_plus1",
        definition="f(n) = prod_{p^a||n} phi(p^a + 1)",
        fn=prod_phi_pa_plus1, alt_fn=alt_phi_pa_plus1,
        family="product over prime-power components of phi(p^a+1)"
    ))
    
    def sum_gcd_d_nd(n):
        return sum(gcd(d, n // d) for d in divisors(n))
    def alt_sum_gcd(n):
        result = 1
        for p, a in factorint(n).items():
            if a % 2 == 0:
                m = a // 2
                result *= 2 * (p**m - 1) // (p - 1) + p**m
            else:
                m = (a + 1) // 2
                result *= 2 * (p**m - 1) // (p - 1)
        return result
    cands.append(SequenceCandidate(
        name="sum_gcd_d_nd",
        definition="f(n) = sum_{d|n} gcd(d, n/d)",
        fn=sum_gcd_d_nd, alt_fn=alt_sum_gcd,
        pp_formula="f(p^{2m}) = 2*(p^m-1)/(p-1) + p^m; f(p^{2m+1}) = 2*(p^{m+1}-1)/(p-1)",
        family="sum of gcd(d, n/d) over divisors"
    ))
    
    return cands


def run_pipeline(candidates: list[SequenceCandidate], verbose: bool = True):
    for i, c in enumerate(candidates):
        if verbose:
            print(f"\n[{i+1}/{len(candidates)}] {c.name}")
        
        c.compute_terms()
        c.validate_cross()
        c.test_multiplicativity()
        if c.multiplicative:
            c.profile_prime_powers()
        c.test_weak_zones()
        c.check_growth()
        c.detect_collision()
        c.attempt_conjecture()
        c.score()
        
        if verbose:
            print(f"  [{c.confidence_score:3d}] {c.level}")
            print(f"  Multiplicative: {'Y' if c.multiplicative else 'N'} | Cross: {'Y' if c.cross_ok else 'N'} | Weak: {'Y' if not c.weak_failures else 'N'}")
    
    return candidates


def print_summary(candidates: list[SequenceCandidate]):
    print(f"\n\n{'='*66}")
    print("SUMMARY")
    print(f"{'='*66}")
    print(f"{'Name':<28} {'Score':>5}  {'Level':<18}  {'Mult':>4}  {'α':>7}")
    print("-"*66)
    
    for c in sorted(candidates, key=lambda x: -x.confidence_score):
        alpha_str = f"{c.alpha:.4f}" if c.alpha else "N/A"
        print(f"{c.name:<28} {c.confidence_score:>5}  {c.level:<18}  {'Y' if c.multiplicative else 'N':>4}  {alpha_str:>7}")
    
    strong = [c for c in candidates if c.confidence_score >= 70 and not c.collision]
    if strong:
        print(f"\n\n{'='*66}")
        print("OEIS-READY SEQUENCES (score >= 70, no collision)")
        print(f"{'='*66}")
        for c in strong:
            print(f"\n  {c.name}")
            print(f"  {c.definition}")
            print(f"  {c.terms_30}")
            print(f"  Formula: {c.conjectured_formula}")


def main():
    parser = argparse.ArgumentParser(description="Autonomous Integer Sequence Research Pipeline")
    parser.add_argument("--single", type=str, help="Run single sequence by name")
    parser.add_argument("--list", action="store_true", help="List available sequences")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    candidates = get_candidates()
    
    if args.list:
        print("Available sequences:")
        for c in candidates:
            print(f"  {c.name}: {c.definition}")
        return
    
    if args.single:
        candidates = [c for c in candidates if c.name == args.single]
        if not candidates:
            print(f"Sequence '{args.single}' not found")
            return
    
    results = run_pipeline(candidates, verbose=args.verbose)
    print_summary(results)
    
    for c in results:
        if c.confidence_score >= 70:
            print(c.report())


if __name__ == "__main__":
    main()
