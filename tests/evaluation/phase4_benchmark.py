"""
Phase 4 — Business Rule Retrieval Quality Benchmark.

Steps 2–3: Evaluate individual retrieval channels (vector, BM25, FTS) and hybrid RRF.
Compute Recall@K, Precision@K, MRR@K for each channel.
Compare channels in a structured table.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional
import time


@dataclass
class RetrievalResult:
    """Single retrieval result from a channel."""
    rule_id: str
    rank: int  # 1-based rank
    score: float


@dataclass
class ChannelResults:
    """Results from a single retrieval channel for all queries."""
    channel_name: str  # "Vector", "BM25", "FTS", "Hybrid RRF"
    query_results: Dict[str, List[RetrievalResult]] = field(default_factory=dict)
    latencies_ms: Dict[str, float] = field(default_factory=dict)  # query_id -> latency in ms


@dataclass
class MetricsAtK:
    """Metrics computed at cutoff K."""
    k: int
    recall: float
    precision: float
    mrr: float
    num_queries_evaluated: int
    num_queries_no_relevant: int


@dataclass
class ChannelMetrics:
    """All metrics for a single channel."""
    channel_name: str
    metrics_at_5: MetricsAtK
    metrics_at_10: MetricsAtK
    avg_latency_ms: float
    p95_latency_ms: float
    total_queries: int


class BenchmarkEvaluator:
    """Evaluator for retrieval quality against ground-truth queries."""

    def __init__(self):
        self.ground_truth: Dict[str, Set[str]] = {}  # query_id -> set of expected rule_ids
        self.query_categories: Dict[str, str] = {}  # query_id -> category
        self.no_result_queries: Set[str] = set()  # queries with no expected relevant rules

    def set_ground_truth(self, query_id: str, expected_rule_ids: Set[str], category: str = ""):
        """Set ground truth for a single query."""
        self.ground_truth[query_id] = expected_rule_ids
        if category:
            self.query_categories[query_id] = category
        if not expected_rule_ids:
            self.no_result_queries.add(query_id)

    def compute_metrics_at_k(
        self,
        channel_results: ChannelResults,
        k: int,
    ) -> MetricsAtK:
        """
        Compute Recall@K, Precision@K, MRR@K for a channel at cutoff K.

        Recall@K = (relevant retrieved at K) / (total relevant)
        Precision@K = (relevant retrieved at K) / (total retrieved at K)
        MRR@K = average reciprocal rank of first relevant result (or 0 if none)
        """
        recall_sum = 0.0
        precision_sum = 0.0
        mrr_sum = 0.0
        evaluated_count = 0
        no_relevant_count = 0

        for query_id, expected_relevant in self.ground_truth.items():
            retrieved_results = channel_results.query_results.get(query_id, [])
            retrieved_at_k = retrieved_results[:k]
            retrieved_ids_at_k = {r.rule_id for r in retrieved_at_k}

            # Skip if no relevant rules exist for this query (for recall/precision)
            if not expected_relevant:
                no_relevant_count += 1
                continue

            evaluated_count += 1

            # Recall@K
            relevant_retrieved = len(retrieved_ids_at_k & expected_relevant)
            recall = relevant_retrieved / len(expected_relevant)
            recall_sum += recall

            # Precision@K
            precision = (
                relevant_retrieved / len(retrieved_ids_at_k)
                if retrieved_ids_at_k
                else 0.0
            )
            precision_sum += precision

            # MRR@K: reciprocal rank of first relevant result
            mrr_k = 0.0
            for rank, result in enumerate(retrieved_at_k, start=1):
                if result.rule_id in expected_relevant:
                    mrr_k = 1.0 / rank
                    break
            mrr_sum += mrr_k

        # Average metrics
        avg_recall = recall_sum / evaluated_count if evaluated_count > 0 else 0.0
        avg_precision = precision_sum / evaluated_count if evaluated_count > 0 else 0.0
        avg_mrr = mrr_sum / evaluated_count if evaluated_count > 0 else 0.0

        return MetricsAtK(
            k=k,
            recall=avg_recall,
            precision=avg_precision,
            mrr=avg_mrr,
            num_queries_evaluated=evaluated_count,
            num_queries_no_relevant=no_relevant_count,
        )

    def compute_channel_metrics(self, channel_results: ChannelResults) -> ChannelMetrics:
        """Compute all metrics (Recall@5, @10; Precision@5, @10; MRR@5, @10; latency)."""
        metrics_at_5 = self.compute_metrics_at_k(channel_results, k=5)
        metrics_at_10 = self.compute_metrics_at_k(channel_results, k=10)

        # Latency statistics
        latencies = list(channel_results.latencies_ms.values())
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) >= 20 else max(latencies) if latencies else 0.0

        return ChannelMetrics(
            channel_name=channel_results.channel_name,
            metrics_at_5=metrics_at_5,
            metrics_at_10=metrics_at_10,
            avg_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            total_queries=len(self.ground_truth),
        )

    def compare_channels(self, channel_metrics_list: List[ChannelMetrics]) -> str:
        """
        Generate a comparison table of all channels.

        Returns a formatted markdown table.
        """
        lines = [
            "| Metric | Vector | BM25 | FTS | Hybrid RRF |",
            "|---|---:|---:|---:|---:|",
        ]

        # Recall@5
        recall_5_row = "| Recall@5 |"
        for cm in channel_metrics_list:
            recall_5_row += f" {cm.metrics_at_5.recall:.3f} |"
        lines.append(recall_5_row)

        # Precision@5
        precision_5_row = "| Precision@5 |"
        for cm in channel_metrics_list:
            precision_5_row += f" {cm.metrics_at_5.precision:.3f} |"
        lines.append(precision_5_row)

        # MRR@5
        mrr_5_row = "| MRR@5 |"
        for cm in channel_metrics_list:
            mrr_5_row += f" {cm.metrics_at_5.mrr:.3f} |"
        lines.append(mrr_5_row)

        # Recall@10
        recall_10_row = "| Recall@10 |"
        for cm in channel_metrics_list:
            recall_10_row += f" {cm.metrics_at_10.recall:.3f} |"
        lines.append(recall_10_row)

        # Precision@10
        precision_10_row = "| Precision@10 |"
        for cm in channel_metrics_list:
            precision_10_row += f" {cm.metrics_at_10.precision:.3f} |"
        lines.append(precision_10_row)

        # MRR@10
        mrr_10_row = "| MRR@10 |"
        for cm in channel_metrics_list:
            mrr_10_row += f" {cm.metrics_at_10.mrr:.3f} |"
        lines.append(mrr_10_row)

        # Average Latency
        latency_row = "| Average Latency (ms) |"
        for cm in channel_metrics_list:
            latency_row += f" {cm.avg_latency_ms:.1f} |"
        lines.append(latency_row)

        # P95 Latency
        p95_row = "| P95 Latency (ms) |"
        for cm in channel_metrics_list:
            p95_row += f" {cm.p95_latency_ms:.1f} |"
        lines.append(p95_row)

        return "\n".join(lines)

    def analyze_missed_queries(
        self,
        channel_results: ChannelResults,
        k: int = 10,
    ) -> List[Dict]:
        """
        Analyze queries where the channel retrieves no relevant results.

        Returns: List of dicts with query_id, category, expected_count, retrieved_count, reason.
        """
        missed = []

        for query_id, expected_relevant in self.ground_truth.items():
            if not expected_relevant:
                # Skip no-answer queries; they're not "missed"
                continue

            retrieved_results = channel_results.query_results.get(query_id, [])
            retrieved_at_k = retrieved_results[:k]
            retrieved_ids_at_k = {r.rule_id for r in retrieved_at_k}

            # Check if any expected rule was retrieved
            relevant_retrieved = retrieved_ids_at_k & expected_relevant

            if not relevant_retrieved:
                missed.append(
                    {
                        "query_id": query_id,
                        "category": self.query_categories.get(query_id, "unknown"),
                        "expected_count": len(expected_relevant),
                        "retrieved_count": len(retrieved_ids_at_k),
                        "expected_rules": sorted(expected_relevant),
                        "retrieved_rules": sorted(retrieved_ids_at_k),
                    }
                )

        return missed


# Helper function: Format missed-query analysis as markdown
def format_missed_query_analysis(missed_list: List[Dict]) -> str:
    """Format missed-query analysis for the report."""
    if not missed_list:
        return "No missed queries (all expected rules retrieved)."

    lines = [
        f"## Missed Queries Analysis ({len(missed_list)} queries)\n",
        "| Query ID | Category | Expected Count | Retrieved Count | Expected IDs | Retrieved IDs |",
        "|---|---|---:|---:|---|---|",
    ]

    for entry in missed_list:
        expected_ids = ", ".join(entry["expected_rules"][:3])
        if len(entry["expected_rules"]) > 3:
            expected_ids += f", +{len(entry['expected_rules']) - 3} more"

        retrieved_ids = ", ".join(entry["retrieved_rules"][:3])
        if len(entry["retrieved_rules"]) > 3:
            retrieved_ids += f", +{len(entry['retrieved_rules']) - 3} more"

        lines.append(
            f"| {entry['query_id']} | {entry['category']} | {entry['expected_count']} | {entry['retrieved_count']} | {expected_ids} | {retrieved_ids} |"
        )

    return "\n".join(lines)
