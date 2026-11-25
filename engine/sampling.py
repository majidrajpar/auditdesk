"""
AuditDesk Statistical Sampling Engine
AICPA & IIA compliant sample size calculations and reproducible item extraction:
- Attribute Sampling for Internal Controls Testing
- Monetary Unit Sampling (MUS / Dollar Unit Sampling)
- Systematic & Simple Random Selection with deterministic seeds
"""

import math
import random
from typing import List, Dict, Any, Tuple


class SamplingEngine:
    @staticmethod
    def calculate_attribute_sample_size(
        population_size: int,
        confidence_level: float = 0.95,
        tolerable_deviation_rate: float = 0.05,
        expected_deviation_rate: float = 0.01
    ) -> Dict[str, Any]:
        """
        Calculates AICPA-aligned attribute sample size based on standard binomial/Poisson approximations.
        """
        if tolerable_deviation_rate <= expected_deviation_rate:
            tolerable_deviation_rate = expected_deviation_rate + 0.01

        # Z-scores for standard confidence levels
        z_map = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        z = z_map.get(confidence_level, 1.96)

        # Standard attribute sample size formula: n = (Z^2 * p * (1-p)) / (TDR - EPDR)^2
        p = expected_deviation_rate if expected_deviation_rate > 0 else 0.02
        diff = tolerable_deviation_rate - expected_deviation_rate

        raw_n = (z ** 2 * p * (1 - p)) / (diff ** 2)

        # Finite Population Correction (FPC)
        if population_size > 0:
            n_adjusted = raw_n / (1 + (raw_n - 1) / population_size)
        else:
            n_adjusted = raw_n

        # Practical minimums based on AICPA audit guidelines
        # Typically 25-60 for high reliance controls, capped at population size
        if population_size <= 0:
            sample_size = 0
        else:
            sample_size = min(population_size, max(25, int(math.ceil(n_adjusted))))

        return {
            "method": "Attribute Sampling (Controls Testing)",
            "population_size": population_size,
            "confidence_level": confidence_level,
            "tolerable_deviation_rate": tolerable_deviation_rate,
            "expected_deviation_rate": expected_deviation_rate,
            "computed_sample_size": sample_size,
            "sample_percentage": round((sample_size / population_size) * 100, 2) if population_size > 0 else 0,
            "rationale": f"AICPA guidelines for {confidence_level*100:.0f}% confidence, {tolerable_deviation_rate*100:.1f}% TDR, and {expected_deviation_rate*100:.1f}% EPDR yield a sample of {sample_size} items from a population of {population_size:,}."
        }

    @staticmethod
    def calculate_mus_sample_size(
        population_items: List[Dict[str, Any]],
        tolerable_misstatement: float,
        confidence_level: float = 0.95,
        expected_misstatement: float = 0.0,
        amount_field: str = "amount"
    ) -> Dict[str, Any]:
        """
        Calculates Monetary Unit Sampling parameters and sampling interval.
        """
        # Reliability factors based on Poisson distribution (zero expected errors)
        rf_map = {0.90: 2.31, 0.95: 3.00, 0.99: 4.61}
        rf = rf_map.get(confidence_level, 3.00)

        total_book_value = sum(abs(float(x.get(amount_field, 0.0))) for x in population_items)
        sampling_interval = tolerable_misstatement / rf

        high_value_items = []
        regular_items = []

        for item in population_items:
            amt = abs(float(item.get(amount_field, 0.0)))
            if amt >= sampling_interval:
                high_value_items.append(item)
            else:
                regular_items.append(item)

        est_sample_size = int(math.ceil(total_book_value / sampling_interval)) if sampling_interval > 0 else len(population_items)

        return {
            "method": "Monetary Unit Sampling (MUS)",
            "total_book_value": round(total_book_value, 2),
            "tolerable_misstatement": tolerable_misstatement,
            "confidence_level": confidence_level,
            "reliability_factor": rf,
            "sampling_interval": round(sampling_interval, 2),
            "estimated_sample_size": est_sample_size,
            "high_value_items_count": len(high_value_items),
            "high_value_total_amount": round(sum(abs(float(x.get(amount_field, 0.0))) for x in high_value_items), 2),
            "rationale": f"With a total book value of ${total_book_value:,.2f} and a ${tolerable_misstatement:,.2f} tolerable misstatement, the sampling interval is ${sampling_interval:,.2f}. {len(high_value_items)} items meet 100% testing criteria."
        }

    @staticmethod
    def draw_sample(
        records: List[Dict[str, Any]],
        sample_size: int,
        random_seed: int = 42,
        sampling_method: str = "random",
        amount_field: str = "amount"
    ) -> Dict[str, Any]:
        """
        Extracts a reproducible sample from the population using a fixed seed.
        """
        n_pop = len(records)
        if n_pop == 0:
            return {"sample": [], "seed": random_seed, "count": 0}

        sample_size = min(sample_size, n_pop)
        rng = random.Random(random_seed)

        indexed_records = []
        for idx, rec in enumerate(records):
            item_copy = dict(rec)
            item_copy["_pop_index"] = idx + 1
            indexed_records.append(item_copy)

        if sampling_method == "systematic":
            # Systematic interval sampling
            interval = n_pop / sample_size
            start = rng.uniform(0, interval)
            selected = []
            for i in range(sample_size):
                idx = int(start + (i * interval))
                if idx < n_pop:
                    selected.append(indexed_records[idx])
        elif sampling_method == "mus":
            # Monetary unit cumulative selection
            total_amt = sum(abs(float(x.get(amount_field, 0.0))) for x in indexed_records)
            interval = total_amt / sample_size if total_amt > 0 else 1.0
            start = rng.uniform(0, interval)
            
            selected = []
            cum_sum = 0.0
            next_target = start

            for item in indexed_records:
                amt = abs(float(item.get(amount_field, 0.0)))
                cum_sum += amt
                while cum_sum >= next_target and len(selected) < sample_size:
                    selected.append(item)
                    next_target += interval
        else:
            # Simple Random Sampling
            selected = rng.sample(indexed_records, sample_size)

        # Attach audit workpaper test fields
        for item in selected:
            item["_audit_status"] = "Pending Review"
            item["_test_result"] = "Not Tested"
            item["_auditor_notes"] = ""

        return {
            "sample": selected,
            "seed": random_seed,
            "sample_size": len(selected),
            "population_size": n_pop,
            "method": sampling_method
        }
