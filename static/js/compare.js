// Country Comparison Page Logic

document.addEventListener('DOMContentLoaded', () => {
  const countryASelect = document.getElementById('country-a');
  const countryBSelect = document.getElementById('country-b');
  const btnCompare = document.getElementById('btn-compare');
  const formError = document.getElementById('compare-form-error');
  const resultsSection = document.getElementById('compare-results');

  if (!countryASelect || !countryBSelect || !btnCompare) return;

  function getTextColor() {
    return document.body.classList.contains('dark-mode') ? '#f0f5fc' : '#0c1e3d';
  }

  function showError(message) {
    if (!formError) return;
    formError.textContent = message;
    formError.classList.remove('d-none');
  }

  function hideError() {
    if (!formError) return;
    formError.classList.add('d-none');
    formError.textContent = '';
  }

  function formatValue(comparison, side) {
    const val = side === 'a' ? comparison.value_a : comparison.value_b;
    if (comparison.key === 'predicted_category') {
      return val;
    }
    if (comparison.key === 'gni_per_capita') {
      return '$' + Number(val).toLocaleString();
    }
    if (comparison.unit === 'yrs') {
      return val + ' yrs';
    }
    if (comparison.unit === 'USD') {
      return '$' + Number(val).toLocaleString();
    }
    return val;
  }

  function tierBadgeClass(category) {
    const map = {
      'Very High': 'compare-tier-veryhigh',
      'High': 'compare-tier-high',
      'Medium': 'compare-tier-medium',
      'Low': 'compare-tier-low'
    };
    return map[category] || '';
  }

  function renderCountryCard(containerId, country, comparisons, side) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const displayComparisons = comparisons.filter(c =>
      ['life_expectancy', 'mean_schooling', 'expected_schooling', 'gni_per_capita', 'predicted_category'].includes(c.key)
    );

    container.innerHTML = displayComparisons.map(c => {
      const val = side === 'a' ? c.value_a : c.value_b;
      const isWinner = c.winner === side;
      const winnerClass = isWinner ? 'compare-metric-winner' : '';

      let displayVal = val;
      if (c.key === 'gni_per_capita') displayVal = '$' + Number(val).toLocaleString();
      else if (c.key === 'predicted_category') displayVal = `<span class="compare-tier-badge ${tierBadgeClass(val)}">${val}</span>`;
      else if (c.unit === 'yrs') displayVal = val + ' yrs';

      return `
        <div class="compare-metric-row ${winnerClass}">
          <span class="compare-metric-label">${c.label}</span>
          <span class="compare-metric-value">${displayVal}</span>
          ${isWinner ? '<span class="compare-winner-tag"><i class="bi bi-check-circle-fill"></i> Higher</span>' : ''}
        </div>
      `;
    }).join('');

    container.innerHTML += `
      <div class="compare-metric-row mt-2 pt-2 border-top" style="border-color: var(--border-color) !important;">
        <span class="compare-metric-label">Model Confidence</span>
        <span class="compare-metric-value">${country.confidence}%</span>
      </div>
      <div class="compare-metric-row">
        <span class="compare-metric-label">Calculated HDI</span>
        <span class="compare-metric-value">${country.indices.calculated_hdi}</span>
      </div>
    `;
  }

  function renderComparisonTable(comparisons, nameA, nameB) {
    const tbody = document.getElementById('comparison-table-body');
    if (!tbody) return;

    document.querySelectorAll('.compare-col-a').forEach(el => { el.textContent = nameA; });
    document.querySelectorAll('.compare-col-b').forEach(el => { el.textContent = nameB; });

    tbody.innerHTML = comparisons.map(c => {
      const cellClassA = c.winner === 'a' ? 'compare-cell-winner' : '';
      const cellClassB = c.winner === 'b' ? 'compare-cell-winner' : '';
      let leaderText = 'Tie';
      let leaderIcon = 'bi-dash-circle';
      if (c.winner === 'a') { leaderText = nameA; leaderIcon = 'bi-arrow-left-circle-fill'; }
      if (c.winner === 'b') { leaderText = nameB; leaderIcon = 'bi-arrow-right-circle-fill'; }

      return `
        <tr>
          <td class="fw-semibold">${c.label}</td>
          <td class="text-center ${cellClassA}">${formatValue(c, 'a')}</td>
          <td class="text-center ${cellClassB}">${formatValue(c, 'b')}</td>
          <td class="text-center compare-leader-cell">
            <span class="compare-leader-badge ${c.winner !== 'tie' ? 'has-winner' : ''}">
              <i class="bi ${leaderIcon} me-1"></i>${leaderText}
            </span>
          </td>
        </tr>
      `;
    }).join('');
  }

  function renderRadarChart(radar, nameA, nameB) {
    const categories = radar.categories;

    const traceA = {
      type: 'scatterpolar',
      r: [...radar.country_a_values, radar.country_a_values[0]],
      theta: [...categories, categories[0]],
      fill: 'toself',
      name: nameA,
      marker: { color: '#1d6fe8' },
      line: { color: '#1d6fe8' },
      fillcolor: 'rgba(29, 111, 232, 0.15)'
    };

    const traceB = {
      type: 'scatterpolar',
      r: [...radar.country_b_values, radar.country_b_values[0]],
      theta: [...categories, categories[0]],
      fill: 'toself',
      name: nameB,
      marker: { color: '#10b981' },
      line: { color: '#10b981' },
      fillcolor: 'rgba(16, 185, 129, 0.15)'
    };

    Plotly.newPlot('compare-radar-chart', [traceA, traceB], {
      polar: {
        radialaxis: { visible: true, range: [0, 100], tickfont: { size: 10 } },
        angularaxis: { tickfont: { size: 11 } }
      },
      margin: { t: 40, b: 40, l: 60, r: 60 },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      font: { family: 'Inter, sans-serif', color: getTextColor() },
      legend: { orientation: 'h', y: -0.1 },
      showlegend: true
    }, { responsive: true, displayModeBar: false });
  }

  function renderResults(data) {
    document.getElementById('name-country-a').textContent = data.country_a.country;
    document.getElementById('name-country-b').textContent = data.country_b.country;

    renderCountryCard('metrics-country-a', data.country_a, data.comparisons, 'a');
    renderCountryCard('metrics-country-b', data.country_b, data.comparisons, 'b');
    renderComparisonTable(data.comparisons, data.country_a.country, data.country_b.country);
    renderRadarChart(data.radar, data.country_a.country, data.country_b.country);

    document.getElementById('summary-message-a').textContent = data.summary.a_message;
    document.getElementById('summary-message-b').textContent = data.summary.b_message;

    document.getElementById('winner-title').textContent = data.winner.title;
    document.getElementById('winner-name').textContent = data.winner.country;
    document.getElementById('winner-reason').textContent = data.winner.reason;

    resultsSection.classList.remove('d-none');
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // Load countries into dropdowns
  fetch('/api/countries')
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        showError(data.error);
        countryASelect.innerHTML = '<option value="">No countries available</option>';
        countryBSelect.innerHTML = '<option value="">No countries available</option>';
        return;
      }

      const options = data.map(c => {
        const escaped = c.name.replace(/"/g, '&quot;');
        return `<option value="${escaped}">${c.name}</option>`;
      }).join('');
      countryASelect.innerHTML = '<option value="">Select Country A...</option>' + options;
      countryBSelect.innerHTML = '<option value="">Select Country B...</option>' + options;
    })
    .catch(() => {
      showError('Failed to load countries from dataset. Please try again later.');
      countryASelect.innerHTML = '<option value="">Error loading</option>';
      countryBSelect.innerHTML = '<option value="">Error loading</option>';
    });

  btnCompare.addEventListener('click', () => {
    hideError();

    const countryA = countryASelect.value;
    const countryB = countryBSelect.value;

    if (!countryA || !countryB) {
      showError('Please select both Country A and Country B.');
      return;
    }

    if (countryA === countryB) {
      showError('Please select two different countries to compare.');
      return;
    }

    btnCompare.disabled = true;
    btnCompare.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Comparing...';

    fetch('/api/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ country_a: countryA, country_b: countryB })
    })
      .then(res => res.json().then(body => ({ ok: res.ok, body })))
      .then(({ ok, body }) => {
        if (!ok) {
          showError(body.error || 'Comparison failed. Please try again.');
          return;
        }
        renderResults(body);
      })
      .catch(() => showError('Network error. Could not reach the comparison service.'))
      .finally(() => {
        btnCompare.disabled = false;
        btnCompare.innerHTML = '<i class="bi bi-arrows-angle-expand me-2"></i>Compare Countries';
      });
  });

  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      setTimeout(() => {
        const el = document.getElementById('compare-radar-chart');
        if (el && el.data) {
          Plotly.relayout('compare-radar-chart', { 'font.color': getTextColor() });
        }
      }, 150);
    });
  }
});
