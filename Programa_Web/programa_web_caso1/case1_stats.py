"""Motor estadístico del Caso 1: programa de navegación Apolo 11.

Todos los resultados parten de DATASET, la única tabla de datos del programa.
Las funciones no redondean para decidir; el redondeo se reserva para la interfaz.
"""

from __future__ import annotations

from collections import Counter
from math import sqrt
from typing import Iterable, Sequence

import numpy as np


DATASET = [
    {"scenario": 1, "load": "N", "time_a": 35, "time_b": 67},
    {"scenario": 2, "load": "N", "time_a": 42, "time_b": 69},
    {"scenario": 3, "load": "H", "time_a": 45, "time_b": 72},
    {"scenario": 4, "load": "N", "time_a": 38, "time_b": 66},
    {"scenario": 5, "load": "N", "time_a": 40, "time_b": 70},
    {"scenario": 6, "load": "H", "time_a": 47, "time_b": 74},
    {"scenario": 7, "load": "N", "time_a": 44, "time_b": 68},
    {"scenario": 8, "load": "N", "time_a": 42, "time_b": 69},
    {"scenario": 9, "load": "H", "time_a": 46, "time_b": 71},
    {"scenario": 10, "load": "N", "time_a": 48, "time_b": 70},
    {"scenario": 11, "load": "N", "time_a": 50, "time_b": 73},
    {"scenario": 12, "load": "H", "time_a": 51, "time_b": 72},
    {"scenario": 13, "load": "N", "time_a": 45, "time_b": 68},
    {"scenario": 14, "load": "N", "time_a": 41, "time_b": 67},
    {"scenario": 15, "load": "H", "time_a": 55, "time_b": 75},
    {"scenario": 16, "load": "N", "time_a": 43, "time_b": 70},
    {"scenario": 17, "load": "N", "time_a": 49, "time_b": 71},
    {"scenario": 18, "load": "H", "time_a": 58, "time_b": 76},
    {"scenario": 19, "load": "N", "time_a": 47, "time_b": 69},
    {"scenario": 20, "load": "N", "time_a": 40, "time_b": 68},
    {"scenario": 21, "load": "H", "time_a": 125, "time_b": 77},
    {"scenario": 22, "load": "N", "time_a": 52, "time_b": 72},
    {"scenario": 23, "load": "N", "time_a": 150, "time_b": 76},
    {"scenario": 24, "load": "H", "time_a": 205, "time_b": 78},
]

INTERVALS = [(20, 60), (61, 100), (101, 140), (141, 180), (181, 220)]
LATE_LIMIT_MS = 100.0
MAX_LATE_PROPORTION = 0.05
DEFAULT_SEED = 321
SIMULATION_SIZES = (100, 500, 1000)
REVIEW_SEQUENCE = (0, 0, 1, 0, 0, 0, 0, 0, 1, 0)


def quantile_linear(values: Sequence[float], probability: float) -> float:
    """Cuantil con h = 1 + (n - 1)p e interpolación lineal."""
    if not values:
        raise ValueError("Se requiere al menos un valor.")
    if not 0 <= probability <= 1:
        raise ValueError("La probabilidad debe estar entre 0 y 1.")
    ordered = sorted(values)
    h = 1 + (len(ordered) - 1) * probability
    lower_position = int(h)
    fraction = h - lower_position
    if fraction == 0:
        return float(ordered[lower_position - 1])
    lower = ordered[lower_position - 1]
    upper = ordered[lower_position]
    return float(lower + fraction * (upper - lower))


def describe(values: Sequence[float]) -> dict:
    n = len(values)
    if n < 2:
        raise ValueError("Se requieren al menos dos observaciones.")
    mean = sum(values) / n
    counts = Counter(values)
    modal_frequency = max(counts.values())
    modes = sorted(value for value, count in counts.items() if count == modal_frequency)
    sample_variance = sum((value - mean) ** 2 for value in values) / (n - 1)
    sample_sd = sqrt(sample_variance)
    q1 = quantile_linear(values, 0.25)
    q3 = quantile_linear(values, 0.75)
    return {
        "n": n,
        "mean": mean,
        "median": quantile_linear(values, 0.50),
        "modes": modes,
        "mode_frequency": modal_frequency,
        "q1": q1,
        "q3": q3,
        "d9": quantile_linear(values, 0.90),
        "p90": quantile_linear(values, 0.90),
        "p95": quantile_linear(values, 0.95),
        "minimum": min(values),
        "maximum": max(values),
        "range": max(values) - min(values),
        "iqr": q3 - q1,
        "sample_variance": sample_variance,
        "sample_sd": sample_sd,
        "cv_percent": sample_sd / mean * 100,
    }


def frequency_distribution(values: Sequence[int]) -> list[dict]:
    rows = []
    cumulative = 0
    n = len(values)
    for lower, upper in INTERVALS:
        absolute = sum(lower <= value <= upper for value in values)
        cumulative += absolute
        relative = absolute / n
        rows.append(
            {
                "interval": f"{lower}–{upper}",
                "lower": lower,
                "upper": upper,
                "class_mark": (lower + upper) / 2,
                "fi": absolute,
                "Fi": cumulative,
                "hi": relative,
                "Hi": cumulative / n,
                "percent": relative * 100,
            }
        )
    return rows


def compliance(values: Sequence[int]) -> dict:
    p90 = quantile_linear(values, 0.90)
    late_count = sum(value > LATE_LIMIT_MS for value in values)
    late_proportion = late_count / len(values)
    p90_ok = p90 <= LATE_LIMIT_MS
    proportion_ok = late_proportion <= MAX_LATE_PROPORTION
    return {
        "p90": p90,
        "p90_ok": p90_ok,
        "late_count": late_count,
        "late_proportion": late_proportion,
        "proportion_ok": proportion_ok,
        "complies": p90_ok and proportion_ok,
    }


def conditional_probability(numerator_count: int, denominator_count: int) -> float | None:
    """Devuelve una probabilidad condicional o ``None`` si no está definida."""
    if numerator_count < 0 or denominator_count < 0:
        raise ValueError("Los conteos no pueden ser negativos.")
    if numerator_count > denominator_count:
        raise ValueError("El numerador no puede exceder el denominador.")
    if denominator_count == 0:
        return None
    return numerator_count / denominator_count


def probability_analysis() -> dict:
    f_scenarios = {row["scenario"] for row in DATASET if row["time_a"] > LATE_LIMIT_MS}
    h_scenarios = {row["scenario"] for row in DATASET if row["load"] == "H"}
    universe = {row["scenario"] for row in DATASET}
    intersection = f_scenarios & h_scenarios
    n = len(universe)
    p_f = len(f_scenarios) / n
    p_h = len(h_scenarios) / n
    p_intersection = len(intersection) / n
    p_f_given_h = conditional_probability(len(intersection), len(h_scenarios))
    p_h_given_f = conditional_probability(len(intersection), len(f_scenarios))
    return {
        "sets": {
            "F": sorted(f_scenarios),
            "H": sorted(h_scenarios),
            "F_and_H": sorted(intersection),
        },
        "contingency": {
            "F_H": len(intersection),
            "F_not_H": len(f_scenarios - h_scenarios),
            "not_F_H": len(h_scenarios - f_scenarios),
            "not_F_not_H": len(universe - (f_scenarios | h_scenarios)),
            "F_total": len(f_scenarios),
            "not_F_total": n - len(f_scenarios),
            "H_total": len(h_scenarios),
            "not_H_total": n - len(h_scenarios),
            "total": n,
        },
        "probabilities": {
            "P_F": p_f,
            "P_H": p_h,
            "P_F_and_H": p_intersection,
            "P_F_or_H": len(f_scenarios | h_scenarios) / n,
            "P_not_F": 1 - p_f,
            "P_F_given_H": p_f_given_h,
            "P_H_given_F": p_h_given_f,
            "P_F_times_P_H": p_f * p_h,
            "two_F_with_replacement": p_f**2,
            "two_F_without_replacement": (len(f_scenarios) / n) * ((len(f_scenarios) - 1) / (n - 1)),
            "first_F_on_third": (1 - p_f) ** 2 * p_f,
            "third_F_given_first_two_not_F": p_f,
        },
        "conditionals": {
            "P_F_given_H": {
                "numerator": len(intersection),
                "denominator": len(h_scenarios),
                "value": p_f_given_h,
                "numerator_scenarios": sorted(intersection),
                "denominator_scenarios": sorted(h_scenarios),
            },
            "P_H_given_F": {
                "numerator": len(intersection),
                "denominator": len(f_scenarios),
                "value": p_h_given_f,
                "numerator_scenarios": sorted(intersection),
                "denominator_scenarios": sorted(f_scenarios),
            },
            "zero_denominator_policy": "No definida: se devuelve un valor nulo y no se divide entre cero.",
        },
        "mutually_exclusive": len(intersection) == 0,
        "independent": abs(p_intersection - p_f * p_h) < 1e-12,
    }


def stopping_rule(
    sequence: Iterable[int] = REVIEW_SEQUENCE,
    gain: float = 600,
    cost: float = 90,
    lower_limit: float = -270,
    upper_limit: float = 300,
) -> dict:
    balance = 0.0
    rows = []
    for revision, result in enumerate(sequence, start=1):
        benefit = gain if result else 0.0
        step_balance = benefit - cost
        balance += step_balance
        decision = "Continuar"
        if balance <= lower_limit:
            decision = "Concluir: límite inferior"
        elif balance >= upper_limit:
            decision = "Concluir: límite superior"
        rows.append(
            {
                "revision": revision,
                "result": int(result),
                "benefit": benefit,
                "cost": cost,
                "step_balance": step_balance,
                "cumulative_balance": balance,
                "decision": decision,
            }
        )
        if decision != "Continuar":
            break
    p_f = probability_analysis()["probabilities"]["P_F"]
    expected_per_review = gain * p_f - cost
    return {
        "p_f": p_f,
        "expected_per_review": expected_per_review,
        "expected_ten_fixed_reviews": 10 * expected_per_review,
        "rows": rows,
        "stop_revision": rows[-1]["revision"],
        "final_balance": rows[-1]["cumulative_balance"],
    }


def simulation(seed: int = DEFAULT_SEED, sizes: Sequence[int] = SIMULATION_SIZES) -> dict:
    if not sizes or min(sizes) <= 0:
        raise ValueError("Los tamaños de simulación deben ser positivos.")
    rng = np.random.default_rng(seed)
    sample = rng.integers(0, len(DATASET), size=max(sizes))
    event_flags = np.array([DATASET[index]["time_a"] > LATE_LIMIT_MS for index in sample])
    exact = probability_analysis()["probabilities"]["P_F"]
    rows = []
    for size in sizes:
        count = int(event_flags[:size].sum())
        relative = count / size
        rows.append(
            {
                "draws": size,
                "count_F": count,
                "relative_frequency": relative,
                "exact_probability": exact,
                "signed_error": relative - exact,
                "absolute_error": abs(relative - exact),
            }
        )
    return {
        "seed": seed,
        "library": f"NumPy {np.__version__}",
        "generator": type(rng.bit_generator).__name__,
        "protocol": "Una secuencia de 1000 sorteos; 100 y 500 son prefijos de la misma secuencia.",
        "rows": rows,
    }


def validation_checks() -> list[dict]:
    a = [row["time_a"] for row in DATASET]
    b = [row["time_b"] for row in DATASET]
    frequencies_a = frequency_distribution(a)
    frequencies_b = frequency_distribution(b)
    boundary_values = [20, 60, 61, 100, 101, 140, 141, 180, 181, 220]

    def interval_matches(value: int) -> int:
        return sum(lower <= value <= upper for lower, upper in INTERVALS)

    checks = [
        ("24 pares y 24 cargas", len(DATASET) == 24 and len(a) == len(b) == 24),
        ("Cada frontera pertenece a una sola clase", all(interval_matches(v) == 1 for v in boundary_values)),
        ("Frecuencias absolutas suman 24", sum(r["fi"] for r in frequencies_a) == 24 and sum(r["fi"] for r in frequencies_b) == 24),
        ("Frecuencias relativas suman 1", abs(sum(r["hi"] for r in frequencies_a) - 1) < 1e-12 and abs(sum(r["hi"] for r in frequencies_b) - 1) < 1e-12),
        ("Se detectan todas las modas", describe(a)["modes"] == [40, 42, 45, 47] and describe(b)["modes"] == [68, 69, 70, 72]),
        ("D9 y P90 usan la misma convención", describe(a)["d9"] == describe(a)["p90"] and describe(b)["d9"] == describe(b)["p90"]),
        ("Varianza muestral con n - 1", abs(describe(a)["sample_variance"] - 1666.7753623188) < 1e-9),
        ("F usa A > 100, no A ≥ 100", all((row["time_a"] > 100) == (row["scenario"] in {21, 23, 24}) for row in DATASET)),
        ("Primera detención en la revisión 3", stopping_rule()["stop_revision"] == 3),
        ("Simulación oficial reproducible", [r["count_F"] for r in simulation(321)["rows"]] == [14, 70, 128]),
        ("Condicional con denominador cero queda no definida", conditional_probability(0, 0) is None),
    ]
    return [{"name": name, "passed": passed} for name, passed in checks]


def complete_analysis(seed: int = DEFAULT_SEED) -> dict:
    a = [row["time_a"] for row in DATASET]
    b = [row["time_b"] for row in DATASET]
    load_counts = Counter(row["load"] for row in DATASET)
    a_first_20 = a[:20]
    rules_a = compliance(a)
    rules_b = compliance(b)
    checks = validation_checks()
    return {
        "metadata": {
            "case": "Caso 1 · Apolo 11",
            "observation_unit": "Escenario de navegación ejecutado con A y B bajo la misma carga.",
            "quantile_method": "h = 1 + (n - 1)p con interpolación lineal",
            "variance_method": "Varianza muestral con divisor n - 1",
            "late_event": "F: tiempo de A > 100 ms",
        },
        "dataset": DATASET,
        "frequencies": {
            "A": frequency_distribution(a),
            "B": frequency_distribution(b),
            "loads": [
                {"load": key, "fi": load_counts[key], "hi": load_counts[key] / len(DATASET), "percent": load_counts[key] / len(DATASET) * 100}
                for key in ("N", "H")
            ],
        },
        "descriptive": {"A": describe(a), "B": describe(b)},
        "rules": {"A": rules_a, "B": rules_b},
        "probability": probability_analysis(),
        "additional_information": {
            "first_20": {
                "mean": sum(a_first_20) / len(a_first_20),
                "p90": quantile_linear(a_first_20, 0.90),
                "late_count": sum(v > LATE_LIMIT_MS for v in a_first_20),
                "late_proportion": sum(v > LATE_LIMIT_MS for v in a_first_20) / len(a_first_20),
            },
            "all_24": {
                "mean": sum(a) / len(a),
                "p90": quantile_linear(a, 0.90),
                "late_count": sum(v > LATE_LIMIT_MS for v in a),
                "late_proportion": sum(v > LATE_LIMIT_MS for v in a) / len(a),
            },
            "decision": "Conservar los 24 registros: excluir 21–24 oculta los tres retrasos críticos y sesga el dictamen.",
        },
        "review": stopping_rule(),
        "simulation": simulation(seed),
        "validation": {"all_passed": all(c["passed"] for c in checks), "checks": checks},
        "decision": {
            "recommended_version": "B",
            "summary": "Aprobar B y no liberar A sin corrección.",
            "reason": "B es la única versión que cumple simultáneamente P90 ≤ 100 ms y proporción de respuestas > 100 ms ≤ 5 %.",
            "evidence": [
                {"family": "Posición", "text": f"P90: A = {rules_a['p90']:.2f} ms; B = {rules_b['p90']:.2f} ms."},
                {"family": "Dispersión", "text": f"CV: A = {describe(a)['cv_percent']:.2f} %; B = {describe(b)['cv_percent']:.2f} %."},
                {"family": "Probabilidad", "text": f"Retrasos > 100 ms: A = {rules_a['late_count']}/24; B = {rules_b['late_count']}/24."},
                {"family": "Revisión", "text": "Valor esperado = S/ -15 por revisión; la secuencia observada se detiene en 3 con S/ 330."},
            ],
            "limitation": "Los 24 escenarios simulados no prueban que el riesgo futuro de B sea cero.",
            "improvement": "Ampliar pruebas pareadas, prerregistradas y estratificadas por carga; conservar extremos y reevaluar los dos umbrales globalmente y por estrato.",
        },
    }

