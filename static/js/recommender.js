// Recommender & Price Estimator Module
window.RecommenderManager = {
  init() {
    this.bindPricePredictor();
    this.bindRecommender();
  },

  bindPricePredictor() {
    const form = document.getElementById('priceEstimatorForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = form.querySelector('button[type="submit"]');
      const originalText = btn.innerHTML;
      btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Estimating...';
      btn.disabled = true;

      const payload = {
        property_type: document.getElementById('predPropType').value,
        sector: document.getElementById('predSector').value,
        built_up_area: parseFloat(document.getElementById('predArea').value) || 1500,
        bedRoom: parseInt(document.getElementById('predBhk').value) || 3,
        bathroom: parseInt(document.getElementById('predBaths').value) || 3,
        floorNum: parseFloat(document.getElementById('predFloor').value) || 4,
        luxury_score: parseFloat(document.getElementById('predLuxury').value) || 40,
        furnishing_desc: document.getElementById('predFurnishing').value,
        study_room: document.getElementById('predStudy').checked ? 1 : 0,
        servant_room: document.getElementById('predServant').checked ? 1 : 0,
        store_room: document.getElementById('predStore').checked ? 1 : 0,
        pooja_room: document.getElementById('predPooja').checked ? 1 : 0
      };

      try {
        const res = await fetch('/api/predict-price', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();

        // Render result hero
        const resultContainer = document.getElementById('valuationResultArea');
        resultContainer.style.display = 'block';
        
        document.getElementById('valEstimatedPrice').innerText = `₹ ${data.estimated_price_cr} Cr`;
        document.getElementById('valPriceRange').innerText = data.estimated_range;
        document.getElementById('valPriceSqft').innerText = `₹ ${data.price_per_sqft.toLocaleString()} / Sq.Ft`;
        
        const bench = data.sector_benchmark;
        const compText = bench.comparison_pct >= 0 
          ? `+${bench.comparison_pct}% vs Sector Average (₹ ${bench.sector_avg_price_cr} Cr)`
          : `${bench.comparison_pct}% vs Sector Average (₹ ${bench.sector_avg_price_cr} Cr)`;
        
        document.getElementById('valSectorBenchmark').innerText = `${bench.sector}: ${compText}`;
      } catch (err) {
        console.error('Valuation error:', err);
        alert('Failed to calculate price valuation. Please check inputs.');
      } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
      }
    });
  },

  bindRecommender() {
    const form = document.getElementById('propertyRecommenderForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = form.querySelector('button[type="submit"]');
      const originalText = btn.innerHTML;
      btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Finding Matches...';
      btn.disabled = true;

      const payload = {
        budget_min: parseFloat(document.getElementById('recBudgetMin').value) || 0.5,
        budget_max: parseFloat(document.getElementById('recBudgetMax').value) || 4.0,
        target_sector: document.getElementById('recSector').value,
        property_type: document.getElementById('recPropType').value,
        preferred_bhk: parseInt(document.getElementById('recBhk').value) || null,
        min_luxury: parseFloat(document.getElementById('recLuxury').value) || 0,
        need_servant_room: document.getElementById('recServant').checked,
        need_study_room: document.getElementById('recStudy').checked,
        top_k: 9
      };

      try {
        const res = await fetch('/api/recommend', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        this.renderRecommendations(data.recommendations);
      } catch (err) {
        console.error('Recommendation error:', err);
        alert('Failed to retrieve recommendations. Please try again.');
      } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
      }
    });
  },

  renderRecommendations(list) {
    const grid = document.getElementById('recommendationsGrid');
    if (!grid) return;

    if (!list || list.length === 0) {
      grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-muted);">No matching properties found with these criteria. Try adjusting your budget or sector filters.</div>';
      return;
    }

    grid.innerHTML = list.map(item => `
      <div class="rec-card">
        <div class="rec-match-badge"><i class="fas fa-bullseye"></i> ${item.match_score}% Match</div>
        <div>
          <span class="prop-badge badge-${item.property_type.toLowerCase()}">${item.property_type}</span>
          <h3 style="font-size: 17px; font-weight: 700; margin-top: 8px;">${item.society}</h3>
          <p style="font-size: 13px; color: var(--text-secondary);"><i class="fas fa-map-marker-alt" style="color: var(--accent-primary);"></i> ${item.sector}</p>
        </div>
        
        <div style="display: flex; justify-content: space-between; align-items: baseline; border-top: 1px solid var(--card-border); border-bottom: 1px solid var(--card-border); padding: 12px 0;">
          <div>
            <div style="font-size: 22px; font-weight: 800; color: #10b981;">₹ ${item.price} Cr</div>
            <div style="font-size: 11px; color: var(--text-muted);">₹ ${item.price_per_sqft.toLocaleString()} / Sq.Ft</div>
          </div>
          <div style="text-align: right;">
            <div style="font-weight: 600;">${item.bedRoom} BHK | ${item.bathroom} Baths</div>
            <div style="font-size: 12px; color: var(--text-secondary);">${item.built_up_area} Sq.Ft</div>
          </div>
        </div>

        <div class="rec-highlights">
          ${item.highlights.map(h => `<span class="rec-tag">${h}</span>`).join('')}
        </div>

        <button class="btn btn-outline-primary" style="width: 100%; justify-content: center; margin-top: auto;" onclick="AppManager.openPropertyModal(${item.id})">
          <i class="fas fa-info-circle"></i> View Property Specs
        </button>
      </div>
    `).join('');
  }
};
