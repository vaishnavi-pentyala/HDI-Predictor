// HDI Predictor Web Application Logic

document.addEventListener('DOMContentLoaded', () => {
  // --- 1. Theme Configuration (Dark / Light Mode) ---
  const themeToggle = document.getElementById('theme-toggle');
  const body = document.body;

  const savedTheme = localStorage.getItem('hdi-theme') || 'light';
  if (savedTheme === 'dark') {
    body.classList.add('dark-mode');
  }

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      body.classList.toggle('dark-mode');
      const currentTheme = body.classList.contains('dark-mode') ? 'dark' : 'light';
      localStorage.setItem('hdi-theme', currentTheme);
    });
  }

  // --- 1b. Sidebar Toggle (Mobile) ---
  const sidebar = document.getElementById('app-sidebar');
  const sidebarToggle = document.getElementById('sidebar-toggle');
  const sidebarOverlay = document.getElementById('sidebar-overlay');

  function closeSidebar() {
    if (sidebar) sidebar.classList.remove('open');
    if (sidebarOverlay) sidebarOverlay.classList.remove('active');
    document.body.style.overflow = '';
  }

  function openSidebar() {
    if (sidebar) sidebar.classList.add('open');
    if (sidebarOverlay) sidebarOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => {
      if (sidebar && sidebar.classList.contains('open')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
  }

  if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', closeSidebar);
  }

  document.querySelectorAll('.sidebar-link').forEach(link => {
    link.addEventListener('click', () => {
      if (window.innerWidth <= 1024) closeSidebar();
    });
  });

  // --- 1c. Animated Metric Counters ---
  function animateCounter(el, target, suffix = '', decimals = 1, duration = 1200) {
    const start = 0;
    const startTime = performance.now();

    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = start + (target - start) * eased;

      if (decimals > 0) {
        el.textContent = current.toFixed(decimals) + suffix;
      } else {
        el.textContent = Math.round(current) + suffix;
      }

      if (progress < 1) {
        requestAnimationFrame(update);
      } else {
        if (decimals > 0) {
          el.textContent = target.toFixed(decimals) + suffix;
        } else {
          el.textContent = Math.round(target) + suffix;
        }
      }
    }

    requestAnimationFrame(update);
  }

  document.querySelectorAll('[data-counter]').forEach(el => {
    const target = parseFloat(el.dataset.counter);
    const suffix = el.dataset.suffix || '';
    const decimals = el.dataset.decimals !== undefined ? parseInt(el.dataset.decimals, 10) : 1;

    if (!isNaN(target)) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            animateCounter(el, target, suffix, decimals);
            observer.unobserve(el);
          }
        });
      }, { threshold: 0.3 });

      observer.observe(el);
    }
  });

  // Initialize Bootstrap Tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // --- 2. Input Elements Synchronization & Calculations ---
  // Sliders
  const lifeSlider = document.getElementById('input-life');
  const eysSlider = document.getElementById('input-eys');
  const mysSlider = document.getElementById('input-mys');
  const gniSlider = document.getElementById('input-gni'); // Log scale: 0 to 100

  // Numbers
  const lifeNum = document.getElementById('num-life');
  const eysNum = document.getElementById('num-eys');
  const mysNum = document.getElementById('num-mys');
  const gniNum = document.getElementById('num-gni');

  // GNI Constants for Log Scale
  const minGni = 100;
  const maxGni = 75000;
  const minLn = Math.log(minGni);
  const maxLn = Math.log(maxGni);

  // Conversion: GNI $ to Log Slider (0-100)
  function gniToSliderVal(gni) {
    const clamped = Math.max(minGni, Math.min(maxGni, gni));
    return ((Math.log(clamped) - minLn) / (maxLn - minLn)) * 100;
  }

  // Conversion: Log Slider (0-100) to GNI $
  function sliderToGniVal(sliderVal) {
    const gni = Math.exp(minLn + (sliderVal / 100) * (maxLn - minLn));
    if (gni < 1000) {
      return Math.round(gni);
    } else if (gni < 10000) {
      return Math.round(gni / 50) * 50;
    } else {
      return Math.round(gni / 100) * 100;
    }
  }

  // Sync inputs
  function setupSync(slider, number, transformFromSlider = null, transformToSlider = null) {
    if (!slider || !number) return;
    
    slider.addEventListener('input', () => {
      const val = transformFromSlider ? transformFromSlider(slider.value) : slider.value;
      number.value = val;
      validateSchoolingRange();
    });

    number.addEventListener('change', () => {
      let val = parseFloat(number.value);
      const min = parseFloat(number.min);
      const max = parseFloat(number.max);
      
      if (isNaN(val)) val = min;
      if (val < min) val = min;
      if (val > max) val = max;
      
      number.value = val;
      slider.value = transformToSlider ? transformToSlider(val) : val;
      validateSchoolingRange();
    });
  }

  // Validate EYS and MYS constraints
  function validateSchoolingRange() {
    if (!eysNum || !mysNum) return;
    const eys = parseFloat(eysNum.value);
    const mys = parseFloat(mysNum.value);
    
    // Mean schooling should not exceed expected schooling
    if (mys > eys) {
      mysNum.classList.add('is-invalid');
    } else {
      mysNum.classList.remove('is-invalid');
    }
  }

  // Sync groups
  setupSync(lifeSlider, lifeNum);
  setupSync(eysSlider, eysNum);
  setupSync(mysSlider, mysNum);
  setupSync(gniSlider, gniNum, sliderToGniVal, gniToSliderVal);

  // Initialize GNI slider position on start
  if (gniSlider && gniNum) {
    gniSlider.value = gniToSliderVal(parseFloat(gniNum.value));
  }

  // --- 3. Scenario Presets Loader ---
  const presetDev = document.getElementById('preset-developed');
  const presetEmerg = document.getElementById('preset-emerging');
  const presetLeast = document.getElementById('preset-least');

  const presets = {
    developed: { life: 81.2, eys: 16.4, mys: 12.2, gni: 45000 },
    emerging: { life: 72.8, eys: 12.7, mys: 8.6, gni: 16700 },
    least: { life: 59.4, eys: 8.2, mys: 4.2, gni: 1800 }
  };

  function applyPreset(key) {
    const config = presets[key];
    if (!config) return;

    if (lifeNum) {
      lifeNum.value = config.life;
      lifeSlider.value = config.life;
    }
    if (eysNum) {
      eysNum.value = config.eys;
      eysSlider.value = config.eys;
    }
    if (mysNum) {
      mysNum.value = config.mys;
      mysSlider.value = config.mys;
    }
    if (gniNum) {
      gniNum.value = config.gni;
      gniSlider.value = gniToSliderVal(config.gni);
    }
    validateSchoolingRange();
  }

  if (presetDev) presetDev.addEventListener('click', () => applyPreset('developed'));
  if (presetEmerg) presetEmerg.addEventListener('click', () => applyPreset('emerging'));
  if (presetLeast) presetLeast.addEventListener('click', () => applyPreset('least'));

  // Form Controls
  const btnReset = document.getElementById('btn-reset');
  const btnSample = document.getElementById('btn-sample');

  if (btnReset) {
    btnReset.addEventListener('click', () => {
      applyPreset('emerging');
    });
  }

  if (btnSample) {
    btnSample.addEventListener('click', () => {
      // Load a random realistic set of values
      const life = (60 + Math.random() * 23).toFixed(1);
      const eys = (8 + Math.random() * 9).toFixed(1);
      const mys = (Math.max(1, eys - 1 - Math.random() * 4)).toFixed(1);
      const gni = Math.round(1000 + Math.random() * 50000);
      
      if (lifeNum) { lifeNum.value = life; lifeSlider.value = life; }
      if (eysNum) { eysNum.value = eys; eysSlider.value = eys; }
      if (mysNum) { mysNum.value = mys; mysSlider.value = mys; }
      if (gniNum) { gniNum.value = gni; gniSlider.value = gniToSliderVal(gni); }
      validateSchoolingRange();
    });
  }

  // --- 4. Prediction Submission and Display ---
  const predictForm = document.getElementById('prediction-form');
  const btnPredict = document.getElementById('btn-predict');
  const btnText = btnPredict ? btnPredict.querySelector('.btn-text') : null;
  const loader = btnPredict ? btnPredict.querySelector('.loader') : null;
  const formErrors = document.getElementById('form-errors');

  // Outputs elements
  const resultsWelcome = document.getElementById('results-welcome');
  const resultsActive = document.getElementById('results-active');
  const hdiScoreValue = document.getElementById('hdi-score-value');
  const predictedTierText = document.getElementById('predicted-tier-text');
  const confidenceValue = document.getElementById('confidence-value');
  const predictedTierRange = document.getElementById('predicted-tier-range');
  const predictedTierBadge = document.getElementById('predicted-tier-badge');
  const gaugeProgressCircle = document.getElementById('gauge-progress-circle');

  // Progress Bars
  const valHealth = document.getElementById('val-health');
  const barHealth = document.getElementById('bar-health');
  const valEducation = document.getElementById('val-education');
  const barEducation = document.getElementById('bar-education');
  const valIncome = document.getElementById('val-income');
  const barIncome = document.getElementById('bar-income');

  // XAI Components
  const weakestDimensionName = document.getElementById('weakest-dimension-name');
  const xaiTableBody = document.getElementById('xai-table-body');
  const policySuggestions = document.getElementById('policy-suggestions');
  const predictedCategoryName = document.getElementById('predicted-category-name');
  const weakestLinkBadge = document.getElementById('weakest-link-badge');

  if (predictForm) {
    predictForm.addEventListener('submit', (e) => {
      e.preventDefault();
      
      // Clear errors
      if (formErrors) {
        formErrors.classList.add('d-none');
        formErrors.innerHTML = '';
      }

      // Collect data
      const payload = {
        life_expectancy: parseFloat(lifeNum.value),
        expected_schooling: parseFloat(eysNum.value),
        mean_schooling: parseFloat(mysNum.value),
        gni_capita: parseFloat(gniNum.value)
      };

      // Client-side validations
      const validationErrors = [];
      if (payload.mean_schooling > payload.expected_schooling) {
        validationErrors.push("Mean Years of Schooling cannot exceed Expected Years of Schooling.");
      }
      if (validationErrors.length > 0) {
        if (formErrors) {
          formErrors.innerHTML = validationErrors.join('<br>');
          formErrors.classList.remove('d-none');
        }
        return;
      }

      // Show loader
      if (btnPredict) btnPredict.disabled = true;
      if (btnText) btnText.classList.add('d-none');
      if (loader) loader.classList.remove('d-none');

      // POST Request
      fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      .then(res => res.json())
      .then(data => {
        if (data.errors || data.error) {
          const errMsg = data.error || data.errors.join('<br>');
          if (formErrors) {
            formErrors.innerHTML = errMsg;
            formErrors.classList.remove('d-none');
          }
          return;
        }

        // Display results
        if (resultsWelcome) {
          resultsWelcome.classList.add('d-none');
          resultsWelcome.classList.remove('d-flex');
        }
        if (resultsActive) resultsActive.classList.remove('d-none');

        // HDI Score Animation
        const score = data.explanation.sub_indices['Calculated HDI'];
        if (hdiScoreValue) hdiScoreValue.innerText = score.toFixed(3);
        
        // Circular Gauge
        if (gaugeProgressCircle) {
          const circumference = 2 * Math.PI * 50; // r=50 -> 314
          gaugeProgressCircle.style.strokeDasharray = circumference;
          const offset = circumference - (score * circumference);
          gaugeProgressCircle.style.strokeDashoffset = offset;
        }

        // Tiers Badge Styling
        const category = data.prediction;
        if (predictedTierText) predictedTierText.innerText = `${category} Human Development`;
        if (predictedCategoryName) predictedCategoryName.innerText = category;
        if (confidenceValue) confidenceValue.innerText = `${(data.confidence * 100).toFixed(1)}%`;

        let rangeText = "";
        let classColor = "";
        let bootstrapBgClass = "";
        if (category === 'Very High') {
          rangeText = "Score Range: ≥ 0.800";
          classColor = "tier-veryhigh";
          bootstrapBgClass = "bg-indigo-subtle text-primary border border-primary-subtle";
        } else if (category === 'High') {
          rangeText = "Score Range: 0.700 – 0.799";
          classColor = "tier-high";
          bootstrapBgClass = "bg-success-subtle text-success border border-success-subtle";
        } else if (category === 'Medium') {
          rangeText = "Score Range: 0.550 – 0.699";
          classColor = "tier-medium";
          bootstrapBgClass = "bg-warning-subtle text-warning border border-warning-subtle";
        } else {
          rangeText = "Score Range: < 0.550";
          classColor = "tier-low";
          bootstrapBgClass = "bg-danger-subtle text-danger border border-danger-subtle";
        }

        if (predictedTierRange) predictedTierRange.innerText = rangeText;
        if (predictedTierBadge) {
          predictedTierBadge.className = `tier-badge d-inline-flex align-items-center gap-2 px-3 py-2 rounded-pill mb-3 ${bootstrapBgClass}`;
          // Set dot color
          const dot = predictedTierBadge.querySelector('.badge-dot');
          if (dot) {
            dot.className = 'badge-dot rounded-circle';
            if (category === 'Very High') dot.style.backgroundColor = 'var(--tier-veryhigh)';
            else if (category === 'High') dot.style.backgroundColor = 'var(--tier-high)';
            else if (category === 'Medium') dot.style.backgroundColor = 'var(--tier-medium)';
            else dot.style.backgroundColor = 'var(--tier-low)';
          }
        }
        if (gaugeProgressCircle) {
          gaugeProgressCircle.className.baseVal = `gauge-fill ${classColor}`;
        }

        // Sub-index bars
        const healthScore = data.explanation.sub_indices['Health Index'];
        const eduScore = data.explanation.sub_indices['Education Index'];
        const incScore = data.explanation.sub_indices['Income Index'];

        if (valHealth) valHealth.innerText = healthScore.toFixed(3);
        if (barHealth) barHealth.style.width = `${healthScore * 100}%`;

        if (valEducation) valEducation.innerText = eduScore.toFixed(3);
        if (barEducation) barEducation.style.width = `${eduScore * 100}%`;

        if (valIncome) valIncome.innerText = incScore.toFixed(3);
        if (barIncome) barIncome.style.width = `${incScore * 100}%`;

        // Explainable AI Table
        if (weakestDimensionName) weakestDimensionName.innerText = data.explanation.weakest_dimension;
        
        // Style weakest dimension alert container
        if (weakestLinkBadge) {
          let alertClass = "alert alert-warning border-0 p-3 rounded-lg mb-4";
          if (data.explanation.weakest_dimension === 'Health Index') alertClass = "alert alert-danger border-0 p-3 rounded-lg mb-4";
          else if (data.explanation.weakest_dimension === 'Income Index') alertClass = "alert alert-info border-0 p-3 rounded-lg mb-4";
          weakestLinkBadge.className = alertClass;
        }

        if (xaiTableBody) {
          xaiTableBody.innerHTML = "";
          data.explanation.feature_comparisons.forEach(item => {
            const tr = document.createElement('tr');
            
            const diffClass = item.direction === 'positive' ? 'text-success fw-bold' : (item.direction === 'negative' ? 'text-danger fw-bold' : 'text-muted');
            const badgeClass = item.direction === 'positive' ? 'badge bg-success-subtle text-success border border-success-subtle' : (item.direction === 'negative' ? 'badge bg-danger-subtle text-danger border border-danger-subtle' : 'badge bg-secondary-subtle text-secondary border border-secondary-subtle');
            const directionLabel = item.direction === 'positive' ? 'ABOVE MEDIAN' : (item.direction === 'negative' ? 'BELOW MEDIAN' : 'TYPICAL');
            
            let userValStr = item.user_val.toFixed(1);
            let medianValStr = item.class_median.toFixed(1);
            let diffValStr = item.difference >= 0 ? `+${item.difference.toFixed(1)}` : `${item.difference.toFixed(1)}`;
            
            if (item.feature === 'GNI_Per_Capita') {
              userValStr = `$${Math.round(item.user_val).toLocaleString()}`;
              medianValStr = `$${Math.round(item.class_median).toLocaleString()}`;
              diffValStr = item.difference >= 0 ? `+$${Math.round(item.difference).toLocaleString()}` : `-$${Math.round(Math.abs(item.difference)).toLocaleString()}`;
            }

            tr.innerHTML = `
              <td><strong>${item.display}</strong></td>
              <td>${userValStr}</td>
              <td>${medianValStr}</td>
              <td class="${diffClass}">${diffValStr}</td>
              <td><span class="${badgeClass} fs-8 px-2 py-1">${directionLabel}</span></td>
              <td>${(item.importance * 100).toFixed(1)}%</td>
            `;
            xaiTableBody.appendChild(tr);
          });
        }

        // Policy Suggestions
        if (policySuggestions) {
          policySuggestions.innerHTML = "";
          const policies = {
            'Health Index': [
              "Allocate resources to expand rural community clinic networks and medical staffing.",
              "Introduce state-backed health coverage programs for marginalized demographics.",
              "Upgrade nutritional supplements and regional clean water infrastructure."
            ],
            'Education Index': [
              "Allocate educational budgets towards lowering primary pupil-to-teacher bounds.",
              "Introduce adult digital literacy programs and technical vocational academies.",
              "Fund school food programs and uniform subsidies to reduce dropout ratios."
            ],
            'Income Index': [
              "Simplify regulations to trigger job growth in manufacturing and technology sectors.",
              "Deploy microfinance credits to incentivize localized entrepreneurship.",
              "Form partnerships with clean tech entities to attract green investments."
            ]
          };

          const activePolicies = policies[data.explanation.weakest_dimension] || policies['Health Index'];
          activePolicies.forEach(p => {
            const li = document.createElement('li');
            li.className = "list-group-item bg-transparent px-0 border-0 d-flex align-items-start gap-2 py-1 text-secondary";
            li.innerHTML = `<i class="bi bi-check-circle-fill text-primary mt-1" style="font-size: 0.85rem;"></i> <span>${p}</span>`;
            policySuggestions.appendChild(li);
          });
        }

        // Refresh History Log
        loadHistory();
      })
      .catch(err => {
        console.error(err);
        if (formErrors) {
          formErrors.innerHTML = "An unexpected connection error occurred.";
          formErrors.classList.remove('d-none');
        }
      })
      .finally(() => {
        // Reset button states
        if (btnPredict) btnPredict.disabled = false;
        if (btnText) btnText.classList.remove('d-none');
        if (loader) loader.classList.add('d-none');
      });
    });
  }

  // --- 5. PDF Download Action ---
  const btnDownloadPdf = document.getElementById('btn-download-pdf');
  if (btnDownloadPdf) {
    btnDownloadPdf.addEventListener('click', () => {
      const element = document.getElementById('results-active');
      const opt = {
        margin:       0.5,
        filename:     'hdi_prediction_report.pdf',
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { scale: 2, useCORS: true },
        jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
      };
      
      element.classList.add('printing-pdf');
      
      html2pdf().set(opt).from(element).save().then(() => {
        element.classList.remove('printing-pdf');
      });
    });
  }

  // --- 6. Prediction History Table Populate ---
  const historyTableBody = document.getElementById('history-table-body');
  const btnClearHistory = document.getElementById('btn-clear-history');

  function loadHistory() {
    if (!historyTableBody) return;
    
    fetch('/api/history')
    .then(res => res.json())
    .then(data => {
      historyTableBody.innerHTML = "";
      
      if (data.length === 0) {
        historyTableBody.innerHTML = `
          <tr>
            <td colspan="7" class="text-center text-muted py-4">No prediction history recorded yet.</td>
          </tr>
        `;
        return;
      }

      data.forEach(row => {
        const tr = document.createElement('tr');
        
        let badgeColorClass = "";
        if (row.predicted_category === 'Very High') badgeColorClass = 'bg-indigo-subtle text-primary border border-primary-subtle';
        else if (row.predicted_category === 'High') badgeColorClass = 'bg-success-subtle text-success border border-success-subtle';
        else if (row.predicted_category === 'Medium') badgeColorClass = 'bg-warning-subtle text-warning border border-warning-subtle';
        else badgeColorClass = 'bg-danger-subtle text-danger border border-danger-subtle';

        // Format Date Time
        const dt = new Date(row.timestamp);
        const dateStr = dt.toLocaleString();

        tr.innerHTML = `
          <td>${dateStr}</td>
          <td>${row.life_expectancy.toFixed(1)} yrs</td>
          <td>${row.expected_schooling.toFixed(1)} yrs</td>
          <td>${row.mean_schooling.toFixed(1)} yrs</td>
          <td>$${row.gni_capita.toLocaleString()}</td>
          <td><span class="badge ${badgeColorClass} fs-8 px-2 py-1">${row.predicted_category}</span></td>
          <td><strong>${row.confidence}%</strong></td>
        `;
        historyTableBody.appendChild(tr);
      });
    })
    .catch(err => {
      console.error("Error loading prediction history:", err);
    });
  }

  if (btnClearHistory) {
    btnClearHistory.addEventListener('click', () => {
      if (confirm("Are you sure you want to permanently clear the prediction history log?")) {
        fetch('/api/history/clear', { method: 'POST' })
        .then(res => res.json())
        .then(() => {
          loadHistory();
        })
        .catch(err => {
          console.error("Error clearing history:", err);
        });
      }
    });
  }

  // Load history log on start
  loadHistory();
});
