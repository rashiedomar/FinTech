#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sentence_transformers import SentenceTransformer

from mteb import MTEB, get_tasks
from mteb.models.sentence_transformer_wrapper import SentenceTransformerEncoderWrapper
from mteb.types import PromptType


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT_DIR / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from safeguard_ai.ch4_retrieval import load_jsonl, retrieve_support_for_query


BENCHMARK_DIR = ROOT_DIR / "data" / "benchmarks" / "ko_public_retrieval"
LANGUAGE_FILTER = ["kor-Hang"]

CORE_TASKS = [
    "Ko-StrategyQA",
    "AutoRAGRetrieval",
    "PublicHealthQA",
]

FAST_TASKS = [
    *CORE_TASKS,
    "MultiLongDocRetrieval",
    "XPQARetrieval",
]

FULL_TASKS = FAST_TASKS + [
    "BelebeleRetrieval",
    "MIRACLRetrieval",
    "MrTidyRetrieval",
]

SKIPPED_TASK_NOTES = {
    "MultiLongDocRetrieval": "Excluded from the core profile because it is substantially slower than the short public tasks and was not completed within the current run window.",
    "XPQARetrieval": "Excluded from the core profile because it evaluates multiple Korean-involved retrieval directions and takes materially longer than the short public tasks.",
    "BelebeleRetrieval": "Skipped from the runnable fast profile because MTEB 2.15.4 fails to auto-select the Korean HF dataset config for this task.",
    "MIRACLRetrieval": "Excluded from the fast profile because it is a known long-running leaderboard task with a very large corpus.",
    "MrTidyRetrieval": "Excluded from the fast profile because it is a known long-running leaderboard task.",
}


@dataclass(frozen=True)
class ModelConfig:
    alias: str
    model_name: str
    batch_size: int
    prompt_query: str = ""
    prompt_document: str = ""
    use_raw_sentence_transformer: bool = False


MODEL_CONFIGS = [
    ModelConfig(
        alias="kure_v1",
        model_name="nlpai-lab/KURE-v1",
        batch_size=64,
        use_raw_sentence_transformer=True,
    ),
    ModelConfig(
        alias="multilingual_e5_small",
        model_name="intfloat/multilingual-e5-small",
        batch_size=256,
        prompt_query="query: ",
        prompt_document="passage: ",
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a public Korean retrieval benchmark comparison for embedding models."
    )
    parser.add_argument(
        "--profile",
        choices=["core", "fast", "full"],
        default="core",
        help="Benchmark task profile. 'core' is the shortest fully reproducible public subset.",
    )
    parser.add_argument(
        "--device",
        default="cuda",
        help="Device for sentence-transformers / MTEB evaluation.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Reuse existing task result JSON files when available.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.profile == "core":
        tasks = CORE_TASKS
    elif args.profile == "fast":
        tasks = FAST_TASKS
    else:
        tasks = FULL_TASKS
    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)

    for config in MODEL_CONFIGS:
        run_model_benchmark(
            config=config,
            tasks=tasks,
            device=args.device,
            skip_existing=args.skip_existing,
        )

    summary = build_benchmark_summary(tasks=tasks, profile=args.profile)
    summary_path = BENCHMARK_DIR / f"benchmark_summary.{args.profile}.json"
    report_path = BENCHMARK_DIR / f"benchmark_report.{args.profile}.md"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(render_markdown_report(summary), encoding="utf-8")
    print(f"Wrote {summary_path}")
    print(f"Wrote {report_path}")


def run_model_benchmark(
    *,
    config: ModelConfig,
    tasks: list[str],
    device: str,
    skip_existing: bool,
) -> None:
    output_dir = BENCHMARK_DIR / config.alias
    expected_task_paths = [find_task_result_path(output_dir=output_dir, task_name=task_name) for task_name in tasks]
    if skip_existing and all(path.exists() for path in expected_task_paths):
        print(f"Skipping {config.alias}: all task results already exist.")
        return

    model = build_model(config=config, device=device)
    benchmark = MTEB(tasks=get_tasks(tasks=tasks, languages=LANGUAGE_FILTER))
    benchmark.run(
        model,
        output_folder=str(output_dir),
        encode_kwargs={"batch_size": config.batch_size},
    )


def build_model(*, config: ModelConfig, device: str) -> Any:
    if config.use_raw_sentence_transformer:
        return SentenceTransformer(config.model_name, device=device)

    prompts = {}
    if config.prompt_query:
        prompts[PromptType.query.value] = config.prompt_query
    if config.prompt_document:
        prompts[PromptType.document.value] = config.prompt_document

    return SentenceTransformerEncoderWrapper(
        model=config.model_name,
        model_prompts=prompts or None,
        device=device,
    )


def build_benchmark_summary(*, tasks: list[str], profile: str) -> dict[str, Any]:
    model_summaries = [collect_model_summary(config=config, tasks=tasks) for config in MODEL_CONFIGS]
    comparison_rows = []
    by_task: dict[str, dict[str, Any]] = {}
    for task_name in tasks:
        task_entry = {"task_name": task_name, "models": {}}
        for model_summary in model_summaries:
            task_result = next((row for row in model_summary["task_results"] if row["task_name"] == task_name), None)
            if task_result:
                task_entry["models"][model_summary["alias"]] = task_result
        by_task[task_name] = task_entry
        comparison_rows.append(task_entry)

    internal_check = build_internal_retrieval_check()
    return {
        "artifact_type": "ko_public_retrieval_benchmark_summary",
        "version": "0.1.0",
        "profile": profile,
        "tasks": tasks,
        "task_count": len(tasks),
        "models": model_summaries,
        "task_comparison": comparison_rows,
        "internal_ch4_retrieval_check": internal_check,
        "skipped_public_tasks": {task: SKIPPED_TASK_NOTES[task] for task in FULL_TASKS if task not in tasks},
        "notes": [
            "Public benchmark tasks are taken from the Korean retrieval benchmark list used by the KURE project, excluding the two longest tasks in the fast profile.",
            "All public tasks are filtered to the Korean subset using the MTEB language selector `kor-Hang`.",
            "KURE-v1 is evaluated without added text prefixes; multilingual-e5-small uses query/document prefixes as recommended by the E5 family.",
            "The internal Chapter 4 retrieval check validates exact top-1 rule recovery on the current repo's saved failed-rule queries.",
        ],
    }


def collect_model_summary(*, config: ModelConfig, tasks: list[str]) -> dict[str, Any]:
    output_dir = BENCHMARK_DIR / config.alias
    task_results = []
    for task_name in tasks:
        result_path = find_task_result_path(output_dir=output_dir, task_name=task_name)
        if not result_path.exists():
            raise FileNotFoundError(f"Missing benchmark result for {task_name} under {output_dir}")
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        score_split_name, score_rows = next(iter(payload["scores"].items()))
        score_block = score_rows[0]
        task_results.append(
            {
                "task_name": task_name,
                "score_split": score_split_name,
                "main_score": score_block["ndcg_at_10"],
                "ndcg_at_10": score_block["ndcg_at_10"],
                "recall_at_10": score_block["recall_at_10"],
                "precision_at_10": score_block["precision_at_10"],
                "mrr_at_10": score_block["mrr_at_10"],
                "evaluation_time_seconds": payload.get("evaluation_time"),
                "dataset_revision": payload.get("dataset_revision"),
                "result_path": str(result_path.relative_to(ROOT_DIR)),
            }
        )

    return {
        "alias": config.alias,
        "model_name": config.model_name,
        "batch_size": config.batch_size,
        "prefix_policy": (
            "e5_query_document_prefix"
            if config.prompt_query or config.prompt_document
            else "no_prefix"
        ),
        "task_results": task_results,
        "average_main_score": safe_mean(row["main_score"] for row in task_results),
        "average_ndcg_at_10": safe_mean(row["ndcg_at_10"] for row in task_results),
        "average_recall_at_10": safe_mean(row["recall_at_10"] for row in task_results),
        "average_precision_at_10": safe_mean(row["precision_at_10"] for row in task_results),
        "average_mrr_at_10": safe_mean(row["mrr_at_10"] for row in task_results),
    }


def build_internal_retrieval_check() -> dict[str, Any]:
    query_path = ROOT_DIR / "data" / "retrieval" / "ch4_fincpa" / "ch4_example_retrieval_queries.jsonl"
    queries = load_jsonl(query_path)
    details = []
    for query in queries:
        result = retrieve_support_for_query(query, repo_root=ROOT_DIR, top_k=5)
        top_rule_id = result["results"][0]["rule_id"] if result["results"] else None
        details.append(
            {
                "input_id": query["input_id"],
                "expected_rule_id": query["rule_id"],
                "top1_rule_id": top_rule_id,
                "top1_exact_hit": top_rule_id == query["rule_id"],
            }
        )

    hit_count = sum(1 for row in details if row["top1_exact_hit"])
    return {
        "query_count": len(details),
        "top1_exact_rule_hits": hit_count,
        "top1_exact_rule_hit_rate": round(hit_count / len(details), 6) if details else None,
        "details": details,
    }


def render_markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "Korean Public Retrieval Benchmark Report",
        "=======================================",
        "",
        f"Profile: `{summary['profile']}`",
        f"Task count: `{summary['task_count']}`",
        "",
        "Benchmark scope",
        "---------------",
        "- Public Korean retrieval tasks from the KURE / MTEB benchmark family",
        "- Model comparison: `nlpai-lab/KURE-v1` vs `intfloat/multilingual-e5-small`",
        "- Main score reported here: `ndcg_at_10`",
        "- Internal add-on check: exact top-1 rule recovery on the Chapter 4 failed-rule retrieval queries",
        "",
        "Skipped Public Tasks",
        "--------------------",
    ]

    for task_name, note in summary["skipped_public_tasks"].items():
        lines.append(f"- `{task_name}`: {note}")

    lines.extend(
        [
            "",
        "Average Results",
        "---------------",
        "",
        "| model | avg ndcg@10 | avg recall@10 | avg precision@10 | avg mrr@10 |",
        "|---|---:|---:|---:|---:|",
        ]
    )

    for model_summary in summary["models"]:
        lines.append(
            f"| `{model_summary['model_name']}` | "
            f"{model_summary['average_ndcg_at_10']:.5f} | "
            f"{model_summary['average_recall_at_10']:.5f} | "
            f"{model_summary['average_precision_at_10']:.5f} | "
            f"{model_summary['average_mrr_at_10']:.5f} |"
        )

    lines.extend(
        [
            "",
            "Per-Task Results",
            "----------------",
            "",
            "| task | KURE ndcg@10 | e5-small ndcg@10 | KURE recall@10 | e5-small recall@10 |",
            "|---|---:|---:|---:|---:|",
        ]
    )

    model_lookup = {row["alias"]: row for row in summary["models"]}
    kure_tasks = {row["task_name"]: row for row in model_lookup["kure_v1"]["task_results"]}
    e5_tasks = {row["task_name"]: row for row in model_lookup["multilingual_e5_small"]["task_results"]}
    for task_name in summary["tasks"]:
        kure_row = kure_tasks[task_name]
        e5_row = e5_tasks[task_name]
        lines.append(
            f"| `{task_name}` | "
            f"{kure_row['ndcg_at_10']:.5f} | "
            f"{e5_row['ndcg_at_10']:.5f} | "
            f"{kure_row['recall_at_10']:.5f} | "
            f"{e5_row['recall_at_10']:.5f} |"
        )

    internal = summary["internal_ch4_retrieval_check"]
    lines.extend(
        [
            "",
            "Internal Chapter 4 Retrieval Check",
            "----------------------------------",
            f"- query count: `{internal['query_count']}`",
            f"- top-1 exact rule hits: `{internal['top1_exact_rule_hits']}`",
            f"- top-1 exact rule hit rate: `{internal['top1_exact_rule_hit_rate']:.5f}`",
            "",
            "Interpretation",
            "--------------",
            "- The public benchmark section shows broad Korean retrieval quality on external datasets.",
            "- The internal Chapter 4 check shows whether the embedding retriever preserves exact rule alignment for this product's legal evidence flow.",
            "- If KURE beats e5-small on both the public benchmark average and the internal check stays perfect, the switch is justified for the current Korean legal scope.",
            "",
            "Output Files",
            "------------",
        ]
    )

    for model_summary in summary["models"]:
        for task_result in model_summary["task_results"]:
            lines.append(f"- [{task_result['task_name']} result](/data/omar/RESEARCH/JB_hachkaton/{task_result['result_path']})")

    return "\n".join(lines) + "\n"


def safe_mean(values: Any) -> float:
    values = list(values)
    return statistics.fmean(values) if values else 0.0


def find_task_result_path(*, output_dir: Path, task_name: str) -> Path:
    matches = sorted(output_dir.glob(f"**/{task_name}.json"))
    if len(matches) > 1:
        raise RuntimeError(f"Multiple result files found for {task_name} under {output_dir}: {matches}")
    if matches:
        return matches[0]
    return output_dir / task_name / f"{task_name}.json"


if __name__ == "__main__":
    main()
