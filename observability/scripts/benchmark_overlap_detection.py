# /// script
# requires-python = ">=3.10"
# dependencies = ["nltk", "pyyaml"]
# ///
"""Benchmark for semantic overlap detection (ADR-077).

Measures the full detection pipeline: tokenization + stemming + Jaccard
+ classification + hint generation + rendered dict.

Usage:
    uv run observability/scripts/benchmark_overlap_detection.py
    uv run observability/scripts/benchmark_overlap_detection.py --counts 50 100 200 500
    uv run observability/scripts/benchmark_overlap_detection.py --real-data
"""
import argparse
import itertools
import random
import string
import subprocess
import sys
import time
from pathlib import Path
from nltk.stem.porter import PorterStemmer

_stemmer = PorterStemmer()
stem = _stemmer.stem


SAMPLE_TRIGGERS = [
    "debug", "debugging", "systematic debugging", "code review",
    "review changes", "review code", "run tests", "test runner",
    "scan secrets", "secret scanner", "analyze usage", "usage analysis",
    "deploy service", "service deployment", "optimize build",
    "build cache setup", "check code quality", "quality review",
    "create commit", "commit changes", "format code", "code formatter",
    "find bugs", "bug finder", "write documentation", "document code",
    "refactor module", "module refactoring", "performance profiling",
    "profile performance", "security audit", "audit security",
]

BLOCKLIST = {"the", "a", "an", "is", "are", "to", "for", "of", "in", "on", "with"}

CLASSIFICATIONS = ["COLLISION", "SEMANTIC", "PATTERN"]


def tokenize_and_stem(trigger: str) -> frozenset:
    tokens = trigger.lower().replace("-", " ").replace("_", " ").split()
    tokens = [t.strip(string.punctuation) for t in tokens]
    stemmed = {stem(t) for t in tokens if t and t not in BLOCKLIST}
    return frozenset(stemmed)


def jaccard(a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def classify_overlap(score: float, is_exact: bool) -> str:
    if is_exact:
        return "COLLISION"
    return "SEMANTIC"


def generate_hint(classification: str, items: list[str], trigger: str, similarity: float | None) -> str:
    if classification == "PATTERN":
        return f"Assumed delegation: `{items[0]}` → `{items[1]}` (v1 heuristic) — no action needed"
    if classification == "COLLISION":
        return f"`{items[0]}` and `{items[1]}` collide on `{trigger}` — rename or consolidate"
    if classification == "SEMANTIC":
        sim_pct = f"{similarity:.0%}" if similarity is not None else "?"
        return f"Triggers overlap ({sim_pct}) — add distinct prefixes or consolidate"
    return ""


def generate_rendered(hint: str, items: list[str], trigger: str, detection_method: str, similarity: float | None, classification: str) -> dict:
    components = ", ".join(items)
    return {
        "problem": hint,
        "evidence": f"Components {components} share trigger '{trigger}' (detection: {detection_method}, similarity: {similarity})",
        "action": {
            "PATTERN": "No action needed — intentional delegation pattern.",
            "COLLISION": "Rename or consolidate the conflicting components.",
            "SEMANTIC": "Add distinct trigger prefixes or consolidate.",
        }.get(classification, "Review the overlap."),
    }


def generate_triggers(n: int) -> list[str]:
    base = list(SAMPLE_TRIGGERS)
    while len(base) < n:
        words = random.sample(["code", "test", "build", "deploy", "scan",
                                "review", "debug", "fix", "run", "check",
                                "write", "read", "parse", "format", "lint",
                                "audit", "trace", "profile", "optimize"],
                               k=random.randint(1, 3))
        base.append(" ".join(words))
    return base[:n]


def benchmark(trigger_count: int, threshold: float = 0.4, triggers: list[str] | None = None) -> dict:
    if triggers is None:
        triggers = generate_triggers(trigger_count)
    else:
        trigger_count = len(triggers)

    # Phase 1: tokenize + stem all triggers
    t0 = time.perf_counter()
    stemmed = [tokenize_and_stem(t) for t in triggers]
    t_stem = time.perf_counter() - t0

    # Phase 2: pairwise Jaccard + classification + hint + rendered
    pairs = 0
    matches = 0
    t1 = time.perf_counter()
    for i, j in itertools.combinations(range(len(stemmed)), 2):
        score = jaccard(stemmed[i], stemmed[j])
        pairs += 1
        is_exact = triggers[i].lower() == triggers[j].lower()
        if score >= threshold or is_exact:
            matches += 1
            classification = classify_overlap(score, is_exact)
            items = [f"skill:{i}", f"skill:{j}"]
            trigger_text = triggers[i] if is_exact else f"{triggers[i]} ↔ {triggers[j]}"
            hint = generate_hint(classification, items, trigger_text, score if not is_exact else None)
            generate_rendered(hint, items, trigger_text, "exact" if is_exact else "stemmed", score if not is_exact else None, classification)
    t_pipeline = time.perf_counter() - t1

    total = t_stem + t_pipeline
    return {
        "triggers": trigger_count,
        "pairs": pairs,
        "matches": matches,
        "stem_ms": t_stem * 1000,
        "pipeline_ms": t_pipeline * 1000,
        "total_ms": total * 1000,
    }


def collect_real_triggers() -> list[str]:
    """Collect triggers from installed plugins via collect_usage.py --quick-stats."""
    script = Path(__file__).parent.parent / "skills" / "observability-usage-collector" / "scripts" / "collect_usage.py"
    if not script.exists():
        print(f"ERROR: collect_usage.py not found at {script}", file=sys.stderr)
        sys.exit(1)

    sys.path.insert(0, str(script.parent))
    import collect_usage as cu
    cwd = Path.cwd()
    skill_paths = [cu.CLAUDE_DIR / "skills", cwd / ".claude" / "skills"]
    agent_paths = [cu.CLAUDE_DIR / "agents", cwd / ".claude" / "agents"]
    command_paths = [cu.CLAUDE_DIR / "commands", cwd / ".claude" / "commands"]
    skills = cu.discover_skills(skill_paths)
    agents = cu.discover_agents(agent_paths)
    commands = cu.discover_commands(command_paths)
    ps, pa, pc = cu.discover_from_plugins(cu.PLUGINS_CACHE)
    skills.extend(ps)
    agents.extend(pa)
    commands.extend(pc)
    triggers = []
    for item in skills + agents + commands:
        triggers.extend(item.triggers)
    return triggers


def main():
    parser = argparse.ArgumentParser(description="Benchmark overlap detection (ADR-077)")
    parser.add_argument("--counts", nargs="+", type=int,
                        default=[50, 100, 200, 500, 1000],
                        help="Trigger counts to benchmark")
    parser.add_argument("--threshold", type=float, default=0.4)
    parser.add_argument("--runs", type=int, default=3, help="Runs per count (takes median)")
    parser.add_argument("--real-data", action="store_true",
                        help="Benchmark with actual installed plugin triggers")
    args = parser.parse_args()

    header = f"{'Triggers':>8} {'Pairs':>8} {'Matches':>8} {'Stem(ms)':>10} {'Pipeline(ms)':>12} {'Total(ms)':>10}"
    print("Full pipeline: tokenization + stemming + Jaccard + classification + hint + rendered")
    print()

    if args.real_data:
        print("=== Real Data Benchmark ===")
        triggers = collect_real_triggers()
        print(f"Collected {len(triggers)} triggers from installed plugins")
        print()
        print(header)
        print("-" * 64)
        results = []
        for _ in range(args.runs):
            results.append(benchmark(0, args.threshold, triggers=triggers))
        results.sort(key=lambda r: r["total_ms"])
        r = results[len(results) // 2]
        print(f"{r['triggers']:>8} {r['pairs']:>8} {r['matches']:>8} "
              f"{r['stem_ms']:>10.2f} {r['pipeline_ms']:>12.2f} {r['total_ms']:>10.2f}")
        print()

    print("=== Synthetic Benchmark ===")
    print(header)
    print("-" * 64)

    for count in args.counts:
        results = []
        for _ in range(args.runs):
            results.append(benchmark(count, args.threshold))
        results.sort(key=lambda r: r["total_ms"])
        r = results[len(results) // 2]
        print(f"{r['triggers']:>8} {r['pairs']:>8} {r['matches']:>8} "
              f"{r['stem_ms']:>10.2f} {r['pipeline_ms']:>12.2f} {r['total_ms']:>10.2f}")

    print()
    print("If total_ms > 100 for your expected trigger count, consider adding")
    print("a guard to skip semantic detection (see ADR-077 Performance section).")


if __name__ == "__main__":
    main()
