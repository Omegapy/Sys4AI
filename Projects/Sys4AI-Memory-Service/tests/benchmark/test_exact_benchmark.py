from __future__ import annotations

from tools.benchmark_exact_index import run_benchmark


def test_small_exact_benchmark_exercises_the_public_index_path() -> None:
    result = run_benchmark(fragments=1_000, batch_size=250, exact_samples=20)
    corpus = result["corpus"]
    exact = result["exact"]
    lexical = result["lexical"]
    assert isinstance(corpus, dict)
    assert isinstance(exact, dict)
    assert isinstance(lexical, dict)
    assert corpus["fragments"] == 1_000
    assert corpus["indexed_records"] == 1_004
    assert exact["samples"] == 20
    assert exact["target_met"] is True
    assert lexical["samples"] == 100
