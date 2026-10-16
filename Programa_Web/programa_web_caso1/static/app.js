const locale = "es-PE";

const number = (value, digits = 2) => new Intl.NumberFormat(locale, {
  minimumFractionDigits: digits,
  maximumFractionDigits: digits,
}).format(value);

const probability = (value) => value === null || value === undefined ? "No definida" : number(value, 4);
const percent = (value) => `${number(value * 100, 2)} %`;
const money = (value) => new Intl.NumberFormat(locale, {
  style: "currency",
  currency: "PEN",
  minimumFractionDigits: 2,
}).format(value);

const escapeHtml = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

function setTable(id, headers, rows) {
  const table = document.getElementById(id);
  const caption = table.querySelector("caption")?.outerHTML ?? "";
  table.innerHTML = `${caption}<thead><tr>${headers.map((header) => `<th scope="col">${escapeHtml(header)}</th>`).join("")}</tr></thead>
    <tbody>${rows.map((row) => `<tr>${row.map((cell, index) => index === 0 ? `<th scope="row">${escapeHtml(cell)}</th>` : `<td>${escapeHtml(cell)}</td>`).join("")}</tr>`).join("")}</tbody>`;
}

function showToast(message) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 2800);
}

function statusLabel(value) {
  return value ? "Cumple" : "No cumple";
}

function renderFrequencyTable(id, rows) {
  const totalFi = rows.reduce((sum, row) => sum + row.fi, 0);
  const totalHi = rows.reduce((sum, row) => sum + row.hi, 0);
  const displayedRows = rows.map((row) => [
    row.interval,
    number(row.class_mark, 2),
    row.fi,
    row.Fi,
    probability(row.hi),
    probability(row.Hi),
    number(row.percent, 2),
  ]);
  displayedRows.push(["Total", "—", totalFi, totalFi, probability(totalHi), probability(totalHi), number(totalHi * 100, 2)]);
  setTable(id, ["Intervalo (ms)", "Marca", "fi", "Fi", "hi", "Hi", "%"], displayedRows);
}

function renderSummary(data) {
  const { A, B } = data.rules;
  document.getElementById("decision-reason").textContent = data.decision.reason;
  document.getElementById("decision-badges").innerHTML = [
    `P90 B = ${number(B.p90)} ms`,
    `Retrasos B = ${B.late_count}/24`,
    "Decisión con valores sin redondear",
  ].map((item) => `<span>${escapeHtml(item)}</span>`).join("");

  document.getElementById("a-p90").textContent = `${number(A.p90)} ms`;
  document.getElementById("b-p90").textContent = `${number(B.p90)} ms`;
  document.getElementById("a-late").textContent = `${A.late_count}/24 respuestas tardías · ${percent(A.late_proportion)}`;
  document.getElementById("b-late").textContent = `${B.late_count}/24 respuestas tardías · ${percent(B.late_proportion)}`;
  document.getElementById("a-p90-bar").style.width = `${Math.min(100, A.p90 / 130 * 100)}%`;
  document.getElementById("b-p90-bar").style.width = `${Math.min(100, B.p90 / 130 * 100)}%`;

  const cvA = data.descriptive.A.cv_percent;
  const cvB = data.descriptive.B.cv_percent;
  document.getElementById("cv-ratio").textContent = `${number(cvA / cvB, 1)}×`;
  document.getElementById("cv-detail").textContent = `CV A = ${number(cvA)} % · CV B = ${number(cvB)} %`;
}

function renderT1(data) {
  renderFrequencyTable("freq-a", data.frequencies.A);
  renderFrequencyTable("freq-b", data.frequencies.B);
  const labels = { N: "Carga normal", H: "Carga alta" };
  document.getElementById("load-strip").innerHTML = data.frequencies.loads.map((row) =>
    `<div class="${row.load === "N" ? "load-normal" : "load-high"}"><span>${labels[row.load]}</span><span>${row.fi} · ${number(row.percent)} %</span></div>`
  ).join("");
  const loadRows = data.frequencies.loads.map((row) => [
    labels[row.load], row.fi, probability(row.hi), number(row.percent, 2),
  ]);
  const totalLoad = data.frequencies.loads.reduce((sum, row) => sum + row.fi, 0);
  const totalLoadHi = data.frequencies.loads.reduce((sum, row) => sum + row.hi, 0);
  loadRows.push(["Total", totalLoad, probability(totalLoadHi), number(totalLoadHi * 100, 2)]);
  setTable("load-table", ["Tipo de carga", "fi", "hi", "%"], loadRows);
}

function renderDescriptive(data) {
  const a = data.descriptive.A;
  const b = data.descriptive.B;
  const rows = [
    ["Media (ms)", number(a.mean), number(b.mean)],
    ["Mediana (ms)", number(a.median), number(b.median)],
    ["Modas (ms)", a.modes.join(", "), b.modes.join(", ")],
    ["Q1 (ms)", number(a.q1), number(b.q1)],
    ["Q3 (ms)", number(a.q3), number(b.q3)],
    ["D9 = P90 (ms)", number(a.p90), number(b.p90)],
    ["P95 (ms)", number(a.p95), number(b.p95)],
    ["Rango (ms)", number(a.range), number(b.range)],
    ["Rango intercuartílico (ms)", number(a.iqr), number(b.iqr)],
    ["Varianza muestral (ms²)", number(a.sample_variance), number(b.sample_variance)],
    ["Desviación estándar (ms)", number(a.sample_sd), number(b.sample_sd)],
    ["Coeficiente de variación (%)", number(a.cv_percent), number(b.cv_percent)],
  ];
  setTable("descriptive-table", ["Medida", "Versión A", "Versión B"], rows);
  document.getElementById("descriptive-insight").textContent = `A presenta una media menor (${number(a.mean)} ms), pero su desviación estándar llega a ${number(a.sample_sd)} ms. B concentra sus tiempos alrededor de ${number(b.mean)} ms con una desviación de solo ${number(b.sample_sd)} ms.`;
  const rules = [
    ["A · P90 ≤ 100 ms", data.rules.A.p90_ok],
    ["A · retrasos ≤ 5 %", data.rules.A.proportion_ok],
    ["B · P90 ≤ 100 ms", data.rules.B.p90_ok],
    ["B · retrasos ≤ 5 %", data.rules.B.proportion_ok],
  ];
  document.getElementById("rule-list").innerHTML = rules.map(([label, passed]) =>
    `<div class="rule-row"><span>${escapeHtml(label)}</span><strong class="${passed ? "pass" : "fail"}">${statusLabel(passed)}</strong></div>`
  ).join("");
}

function renderProbability(data) {
  const c = data.probability.contingency;
  const p = data.probability.probabilities;
  setTable("contingency-table", ["Evento", "H", "No H", "Total"], [
    ["F", c.F_H, c.F_not_H, c.F_total],
    ["No F", c.not_F_H, c.not_F_not_H, c.not_F_total],
    ["Total", c.H_total, c.not_H_total, c.total],
  ]);
  const cards = [
    ["P(F)", p.P_F], ["P(H)", p.P_H], ["P(F ∩ H)", p.P_F_and_H], ["P(F ∪ H)", p.P_F_or_H],
    ["P(no F)", p.P_not_F], ["P(F | H)", p.P_F_given_H], ["P(H | F)", p.P_H_given_F], ["P(F)P(H)", p.P_F_times_P_H],
  ];
  document.getElementById("probability-cards").innerHTML = cards.map(([label, value]) =>
    `<div class="probability-card"><span>${escapeHtml(label)}</span><strong>${probability(value)}</strong></div>`
  ).join("");
  const conditionals = data.probability.conditionals;
  const scenarioList = (items) => items.join(", ");
  setTable("conditional-table", ["Probabilidad", "Cálculo", "Escenarios del numerador", "Escenarios del denominador", "Resultado"], [
    [
      "P(F | H)",
      `${conditionals.P_F_given_H.numerator}/${conditionals.P_F_given_H.denominator}`,
      scenarioList(conditionals.P_F_given_H.numerator_scenarios),
      scenarioList(conditionals.P_F_given_H.denominator_scenarios),
      probability(conditionals.P_F_given_H.value),
    ],
    [
      "P(H | F)",
      `${conditionals.P_H_given_F.numerator}/${conditionals.P_H_given_F.denominator}`,
      scenarioList(conditionals.P_H_given_F.numerator_scenarios),
      scenarioList(conditionals.P_H_given_F.denominator_scenarios),
      probability(conditionals.P_H_given_F.value),
    ],
  ]);
  document.getElementById("conditional-policy").textContent = `Control de caso límite: ${conditionals.zero_denominator_policy}`;
  document.getElementById("logic-results").innerHTML = [
    `No son mutuamente excluyentes: F ∩ H contiene los escenarios ${data.probability.sets.F_and_H.join(" y ")}.`,
    `No son independientes: ${probability(p.P_F_and_H)} ≠ ${probability(p.P_F_times_P_H)}.`,
  ].map((text) => `<p class="logic-result">${escapeHtml(text)}</p>`).join("");
  document.getElementById("selection-probabilities").innerHTML = [
    ["Dos F con reposición", p.two_F_with_replacement],
    ["Dos F sin reposición", p.two_F_without_replacement],
    ["Primera F en el tercer sorteo", p.first_F_on_third],
    ["F en tercero | dos primeras no F", p.third_F_given_first_two_not_F],
  ].map(([label, value]) => `<dt>${escapeHtml(label)}</dt><dd>${probability(value)}</dd>`).join("");
}

function renderBias(data) {
  const before = data.additional_information.first_20;
  const complete = data.additional_information.all_24;
  setTable("bias-table", ["Indicador de A", "Escenarios 1–20", "Escenarios 1–24"], [
    ["Media (ms)", number(before.mean), number(complete.mean)],
    ["P90 (ms)", number(before.p90), number(complete.p90)],
    ["Respuestas > 100 ms", `${before.late_count}/20`, `${complete.late_count}/24`],
    ["Proporción > 100 ms", percent(before.late_proportion), percent(complete.late_proportion)],
  ]);
}

function renderReview(data) {
  const review = data.review;
  document.getElementById("expected-one").textContent = money(review.expected_per_review);
  document.getElementById("expected-ten").textContent = money(review.expected_ten_fixed_reviews);
  document.getElementById("observed-balance").textContent = money(review.final_balance);
  setTable("stopping-table", ["Revisión", "Resultado", "Beneficio", "Costo", "Saldo del paso", "Acumulado", "Decisión"], review.rows.map((row) => [
    row.revision,
    row.result,
    money(row.benefit),
    money(row.cost),
    money(row.step_balance),
    money(row.cumulative_balance),
    row.decision,
  ]));
}

function renderSimulation(data) {
  const simulation = data.simulation;
  setTable("simulation-table", ["Sorteos", "Apariciones F", "Frecuencia", "P(F) exacta", "Error con signo", "Error absoluto"], simulation.rows.map((row) => [
    row.draws,
    row.count_F,
    probability(row.relative_frequency),
    probability(row.exact_probability),
    `${row.signed_error >= 0 ? "+" : ""}${probability(row.signed_error)}`,
    probability(row.absolute_error),
  ]));
  const maximum = Math.max(...simulation.rows.map((row) => row.absolute_error), 0.001);
  document.getElementById("error-bars").innerHTML = simulation.rows.map((row) =>
    `<div class="bar-row"><span>n=${row.draws}</span><div class="bar-track"><span style="width:${row.absolute_error / maximum * 100}%"></span></div><strong>${probability(row.absolute_error)}</strong></div>`
  ).join("");
  document.getElementById("simulation-protocol").textContent = `${simulation.library} · ${simulation.generator} · semilla ${simulation.seed}. ${simulation.protocol}`;
  const details = simulation.rows.map((row) => `n=${row.draws}: error ${probability(row.absolute_error)}`).join("; ");
  document.getElementById("simulation-explanation").textContent = `Una muestra mayor tiende a estabilizar la frecuencia relativa por la ley de los grandes números, pero no garantiza una mejora monótona: cada ampliación incorpora resultados aleatorios que pueden acercar o alejar temporalmente la estimación. En esta ejecución, ${details}.`;
}

function renderValidation(data) {
  const passed = data.validation.checks.filter((check) => check.passed).length;
  const total = data.validation.checks.length;
  document.getElementById("validation-title").textContent = data.validation.all_passed ? `${passed} de ${total} pruebas superadas` : `${passed} de ${total} pruebas superadas`;
  document.getElementById("validation-list").innerHTML = data.validation.checks.map((check) =>
    `<span class="validation-chip ${check.passed ? "" : "fail"}">${check.passed ? "✓" : "×"} ${escapeHtml(check.name)}</span>`
  ).join("");
}

function renderDecision(data) {
  document.getElementById("evidence-grid").innerHTML = data.decision.evidence.map((item) =>
    `<article class="evidence-card"><span>${escapeHtml(item.family)}</span><p>${escapeHtml(item.text)}</p></article>`
  ).join("");
  document.getElementById("limitation").textContent = data.decision.limitation;
  document.getElementById("improvement").textContent = data.decision.improvement;
}

function renderDataset(data) {
  setTable("data-table", ["Escenario", "Carga", "Tiempo A (ms)", "Tiempo B (ms)"], data.dataset.map((row) => [
    row.scenario,
    row.load === "N" ? "N · normal" : "H · alta",
    row.time_a,
    row.time_b,
  ]));
}

function render(data) {
  renderSummary(data);
  renderT1(data);
  renderDescriptive(data);
  renderProbability(data);
  renderBias(data);
  renderReview(data);
  renderSimulation(data);
  renderValidation(data);
  renderDecision(data);
  renderDataset(data);
}

async function loadAnalysis(seed = 321, notify = false) {
  const response = await fetch(`/api/analysis?seed=${encodeURIComponent(seed)}`);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "No se pudo completar el análisis.");
  render(payload);
  if (notify) showToast(`Simulación actualizada con semilla ${seed}.`);
}

document.getElementById("seed-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const seed = document.getElementById("seed").value;
  try {
    await loadAnalysis(seed, true);
  } catch (error) {
    showToast(error.message);
  }
});

document.getElementById("print-button").addEventListener("click", () => window.print());

loadAnalysis().catch((error) => {
  showToast(error.message);
  document.getElementById("decision-reason").textContent = "No se pudo cargar el análisis. Verifica que el servidor Python siga activo.";
});
