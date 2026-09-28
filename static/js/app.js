// Main Application Controller
window.AppManager = {
  currentPage: 1,
  pageSize: 15,
  currentSort: { by: 'price', order: 'asc' },
  allSectors: [],

  init() {
    this.bindNavigation();
    this.bindThemeToggle();
    this.loadOverviewData();
    this.loadSectorsList();
    this.bindEdaControls();
    this.bindExplorerControls();
    this.bindModal();
    window.RecommenderManager.init();
  },

  bindNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        const tabId = item.getAttribute('data-tab');
        
        // Update active nav
        navItems.forEach(n => n.classList.remove('active'));
        item.classList.add('active');

        // Show active pane
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
        const targetPane = document.getElementById(tabId);
        if (targetPane) {
          targetPane.classList.add('active');
          this.onTabActivated(tabId);
        }
      });
    });
  },

  onTabActivated(tabId) {
    if (tabId === 'tab-overview') {
      this.loadOverviewData();
    } else if (tabId === 'tab-eda') {
      this.loadUnivariateData(document.getElementById('univariateFeatureSelect').value);
      this.loadMultivariateData();
    } else if (tabId === 'tab-sectors') {
      this.loadSectorsOverview();
    } else if (tabId === 'tab-explorer') {
      this.loadPropertiesTable();
    }
  },

  bindThemeToggle() {
    const btn = document.getElementById('themeToggleBtn');
    if (!btn) return;
    btn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme');
      const nextTheme = current === 'light' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', nextTheme);
      btn.innerHTML = nextTheme === 'light' ? '<i class="fas fa-moon"></i>' : '<i class="fas fa-sun"></i>';
      
      // Refresh active charts for theme colors
      const activeTab = document.querySelector('.nav-item.active')?.getAttribute('data-tab');
      if (activeTab) this.onTabActivated(activeTab);
    });
  },

  async loadOverviewData() {
    try {
      const res = await fetch('/api/overview');
      const data = await res.json();

      document.getElementById('kpiTotalProps').innerText = data.total_properties.toLocaleString();
      document.getElementById('kpiMedianPrice').innerText = `₹ ${data.median_price_cr} Cr`;
      document.getElementById('kpiAvgSqft').innerText = `₹ ${data.avg_price_sqft.toLocaleString()}`;
      document.getElementById('kpiAvgArea').innerText = `${data.avg_area_sqft.toLocaleString()} sqft`;
      document.getElementById('kpiAvgLuxury').innerText = `${data.avg_luxury_score} / 100`;

      window.ChartManager.renderOverviewCharts(data);
    } catch (err) {
      console.error('Failed to load overview KPIs:', err);
    }
  },

  async loadSectorsList() {
    try {
      const res = await fetch('/api/sectors');
      const data = await res.json();
      this.allSectors = data.all_sectors;

      const sectorSelects = [
        'univariateSectorSelect',
        'sectorDeepDiveSelect',
        'tableFilterSector',
        'predSector',
        'recSector'
      ];

      sectorSelects.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        
        const hasAll = id === 'tableFilterSector' || id === 'recSector';
        el.innerHTML = (hasAll ? '<option value="all">All Sectors</option>' : '') +
          this.allSectors.map(s => `<option value="${s}">${s}</option>`).join('');
      });

      // Default sector selection
      const diveSelect = document.getElementById('sectorDeepDiveSelect');
      if (diveSelect && this.allSectors.length > 0) {
        diveSelect.value = this.allSectors[0];
        this.loadSectorDeepDive(this.allSectors[0]);
      }
    } catch (err) {
      console.error('Failed to load sectors list:', err);
    }
  },

  bindEdaControls() {
    const uniSelect = document.getElementById('univariateFeatureSelect');
    if (uniSelect) {
      uniSelect.addEventListener('change', () => {
        this.loadUnivariateData(uniSelect.value);
      });
    }

    const diveSelect = document.getElementById('sectorDeepDiveSelect');
    if (diveSelect) {
      diveSelect.addEventListener('change', () => {
        this.loadSectorDeepDive(diveSelect.value);
      });
    }
  },

  async loadUnivariateData(feature) {
    try {
      const res = await fetch(`/api/eda/univariate?feature=${encodeURIComponent(feature)}`);
      const data = await res.json();
      
      window.ChartManager.renderUnivariateChart(data);

      const statsArea = document.getElementById('univariateStatsGrid');
      if (statsArea && data.is_numerical) {
        statsArea.style.display = 'grid';
        statsArea.innerHTML = `
          <div class="stat-pill"><div class="stat-pill-label">Count</div><div class="stat-pill-val">${data.stats.count}</div></div>
          <div class="stat-pill"><div class="stat-pill-label">Mean</div><div class="stat-pill-val">${data.stats.mean}</div></div>
          <div class="stat-pill"><div class="stat-pill-label">Median</div><div class="stat-pill-val">${data.stats.median}</div></div>
          <div class="stat-pill"><div class="stat-pill-label">Std Dev</div><div class="stat-pill-val">${data.stats.std}</div></div>
          <div class="stat-pill"><div class="stat-pill-label">Min</div><div class="stat-pill-val">${data.stats.min}</div></div>
          <div class="stat-pill"><div class="stat-pill-label">Q1 (25%)</div><div class="stat-pill-val">${data.stats.q1}</div></div>
          <div class="stat-pill"><div class="stat-pill-label">Q3 (75%)</div><div class="stat-pill-val">${data.stats.q3}</div></div>
          <div class="stat-pill"><div class="stat-pill-label">Max</div><div class="stat-pill-val">${data.stats.max}</div></div>
          <div class="stat-pill"><div class="stat-pill-label">Skewness</div><div class="stat-pill-val">${data.stats.skewness}</div></div>
        `;
      } else if (statsArea) {
        statsArea.style.display = 'none';
      }
    } catch (err) {
      console.error('Failed to load univariate data:', err);
    }
  },

  async loadMultivariateData() {
    try {
      const res = await fetch('/api/eda/multivariate');
      const data = await res.json();
      window.ChartManager.renderMultivariateCharts(data);
    } catch (err) {
      console.error('Failed to load multivariate data:', err);
    }
  },

  async loadSectorsOverview() {
    try {
      const res = await fetch('/api/sectors');
      const data = await res.json();

      // Render top expensive table
      const expBody = document.getElementById('topExpensiveSectorsBody');
      if (expBody) {
        expBody.innerHTML = data.top_expensive.map((s, idx) => `
          <tr>
            <td><strong>#${idx + 1}</strong></td>
            <td><strong>${s.sector}</strong></td>
            <td><span style="color: #10b981; font-weight: 700;">₹ ${s.avg_price} Cr</span></td>
            <td>₹ ${s.avg_price_sqft.toLocaleString()}</td>
            <td>${s.total_properties} listings</td>
          </tr>
        `).join('');
      }

      // Render top affordable table
      const affBody = document.getElementById('topAffordableSectorsBody');
      if (affBody) {
        affBody.innerHTML = data.top_affordable.map((s, idx) => `
          <tr>
            <td><strong>#${idx + 1}</strong></td>
            <td><strong>${s.sector}</strong></td>
            <td><span style="color: #3b82f6; font-weight: 700;">₹ ${s.avg_price} Cr</span></td>
            <td>₹ ${s.avg_price_sqft.toLocaleString()}</td>
            <td>${s.total_properties} listings</td>
          </tr>
        `).join('');
      }
    } catch (err) {
      console.error('Failed to load sectors overview:', err);
    }
  },

  async loadSectorDeepDive(sectorName) {
    if (!sectorName) return;
    try {
      const res = await fetch(`/api/sectors/${encodeURIComponent(sectorName)}`);
      const data = await res.json();

      document.getElementById('secTotalProps').innerText = data.total_properties;
      document.getElementById('secMedianPrice').innerText = `₹ ${data.median_price} Cr`;
      document.getElementById('secAvgSqft').innerText = `₹ ${data.avg_price_sqft.toLocaleString()}`;
      document.getElementById('secAvgLuxury').innerText = `${data.avg_luxury} / 100`;

      // Top societies tags
      const socContainer = document.getElementById('secTopSocieties');
      if (socContainer) {
        socContainer.innerHTML = Object.entries(data.top_societies).map(([name, count]) => `
          <span class="rec-tag" style="font-size: 13px; padding: 6px 12px;"><strong>${name}</strong> (${count})</span>
        `).join('');
      }
    } catch (err) {
      console.error('Failed to load sector detail:', err);
    }
  },

  bindExplorerControls() {
    const filterIds = [
      'tableFilterType', 'tableFilterSector', 'tableFilterFurnish',
      'tableFilterBhk', 'tableFilterMinPrice', 'tableFilterMaxPrice',
      'tableFilterMinLuxury', 'tableFilterStudy', 'tableFilterServant',
      'tableFilterStore', 'tableFilterPooja', 'tableSearchInput'
    ];

    filterIds.forEach(id => {
      const el = document.getElementById(id);
      if (!el) return;
      el.addEventListener('input', () => {
        this.currentPage = 1;
        this.loadPropertiesTable();
      });
      el.addEventListener('change', () => {
        this.currentPage = 1;
        this.loadPropertiesTable();
      });
    });

    document.getElementById('btnResetFilters')?.addEventListener('click', () => {
      document.getElementById('tableFilterType').value = 'all';
      document.getElementById('tableFilterSector').value = 'all';
      document.getElementById('tableFilterFurnish').value = 'all';
      document.getElementById('tableFilterBhk').value = 'all';
      document.getElementById('tableFilterMinPrice').value = '';
      document.getElementById('tableFilterMaxPrice').value = '';
      document.getElementById('tableFilterMinLuxury').value = '';
      document.getElementById('tableFilterStudy').checked = false;
      document.getElementById('tableFilterServant').checked = false;
      document.getElementById('tableFilterStore').checked = false;
      document.getElementById('tableFilterPooja').checked = false;
      document.getElementById('tableSearchInput').value = '';
      this.currentPage = 1;
      this.loadPropertiesTable();
    });

    document.getElementById('btnExportCsv')?.addEventListener('click', () => {
      this.exportFilteredCsv();
    });
  },

  getFilterPayload() {
    const bhkVal = document.getElementById('tableFilterBhk')?.value;
    let bedrooms = null;
    if (bhkVal && bhkVal !== 'all') {
      bedrooms = [parseInt(bhkVal)];
    }

    return {
      property_type: document.getElementById('tableFilterType')?.value || 'all',
      sector: document.getElementById('tableFilterSector')?.value || 'all',
      furnishing: document.getElementById('tableFilterFurnish')?.value || 'all',
      bedrooms: bedrooms,
      min_price: parseFloat(document.getElementById('tableFilterMinPrice')?.value) || null,
      max_price: parseFloat(document.getElementById('tableFilterMaxPrice')?.value) || null,
      min_luxury: parseFloat(document.getElementById('tableFilterMinLuxury')?.value) || null,
      study_room: document.getElementById('tableFilterStudy')?.checked || false,
      servant_room: document.getElementById('tableFilterServant')?.checked || false,
      store_room: document.getElementById('tableFilterStore')?.checked || false,
      pooja_room: document.getElementById('tableFilterPooja')?.checked || false,
      search_query: document.getElementById('tableSearchInput')?.value || null,
      page: this.currentPage,
      page_size: this.pageSize,
      sort_by: this.currentSort.by,
      sort_order: this.currentSort.order
    };
  },

  async loadPropertiesTable() {
    const tbody = document.getElementById('propertiesTableBody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding: 30px;"><i class="fas fa-spinner fa-spin"></i> Loading properties...</td></tr>';

    try {
      const payload = this.getFilterPayload();
      const res = await fetch('/api/properties/filter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      document.getElementById('tableTotalCount').innerText = `Showing ${(data.records.length ? (data.page - 1) * data.page_size + 1 : 0)} - ${Math.min(data.page * data.page_size, data.total_count)} of ${data.total_count} properties`;

      if (data.records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding: 40px; color: var(--text-muted);">No properties match your filter criteria.</td></tr>';
        return;
      }

      tbody.innerHTML = data.records.map(p => `
        <tr>
          <td>#${p.id}</td>
          <td><span class="prop-badge badge-${p.property_type.toLowerCase()}">${p.property_type}</span></td>
          <td><strong>${p.society}</strong></td>
          <td>${p.sector}</td>
          <td><span style="color: #10b981; font-weight: 700;">₹ ${p.price} Cr</span></td>
          <td>₹ ${p.price_per_sqft.toLocaleString()}</td>
          <td>${p.built_up_area} sqft</td>
          <td>${p.bedRoom} BHK / ${p.bathroom} B</td>
          <td>
            <button class="btn btn-outline-primary" style="padding: 4px 10px; font-size: 12px;" onclick="AppManager.openPropertyModal(${p.id})">
              <i class="fas fa-eye"></i> Specs
            </button>
          </td>
        </tr>
      `).join('');

      this.renderPagination(data.total_pages);
    } catch (err) {
      console.error('Failed to load table:', err);
    }
  },

  renderPagination(totalPages) {
    const bar = document.getElementById('tablePagination');
    if (!bar) return;

    bar.innerHTML = `
      <button class="btn" ${this.currentPage === 1 ? 'disabled' : ''} onclick="AppManager.changePage(${this.currentPage - 1})">
        <i class="fas fa-chevron-left"></i> Prev
      </button>
      <span style="font-size: 13px; font-weight: 600;">Page ${this.currentPage} of ${totalPages}</span>
      <button class="btn" ${this.currentPage >= totalPages ? 'disabled' : ''} onclick="AppManager.changePage(${this.currentPage + 1})">
        Next <i class="fas fa-chevron-right"></i>
      </button>
    `;
  },

  changePage(newPage) {
    this.currentPage = newPage;
    this.loadPropertiesTable();
  },

  bindModal() {
    const modal = document.getElementById('propertyModal');
    const closeBtn = document.getElementById('modalCloseBtn');
    if (!modal) return;

    closeBtn?.addEventListener('click', () => modal.classList.remove('active'));
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.classList.remove('active');
    });
  },

  async openPropertyModal(id) {
    try {
      const res = await fetch(`/api/properties/${id}`);
      const prop = await res.json();

      document.getElementById('modalSocietyTitle').innerText = prop.society;
      document.getElementById('modalSector').innerText = `${prop.sector} • ${prop.property_type.toUpperCase()}`;
      document.getElementById('modalPrice').innerText = `₹ ${prop.price} Cr`;
      document.getElementById('modalSqftRate').innerText = `₹ ${Number(prop.price_per_sqft).toLocaleString()} / Sq.Ft`;
      document.getElementById('modalArea').innerText = `${prop.built_up_area} Sq.Ft`;
      document.getElementById('modalBhk').innerText = `${prop.bedRoom} Bedrooms`;
      document.getElementById('modalBaths').innerText = `${prop.bathroom} Bathrooms`;
      document.getElementById('modalFloor').innerText = `Floor ${prop.floorNum || 'N/A'}`;
      document.getElementById('modalFacing').innerText = prop.facing || 'East';
      document.getElementById('modalFurnishing').innerText = prop.furnishing_desc || 'Unfurnished';
      document.getElementById('modalLuxuryScore').innerText = `${prop.luxury_score} / 100`;

      // Extra rooms badges
      const roomsContainer = document.getElementById('modalExtraRooms');
      const extraRooms = [];
      if (prop['study room'] == 1) extraRooms.push('Study Room');
      if (prop['servant room'] == 1) extraRooms.push('Servant Room');
      if (prop['store room'] == 1) extraRooms.push('Store Room');
      if (prop['pooja room'] == 1) extraRooms.push('Pooja Room');

      roomsContainer.innerHTML = extraRooms.length 
        ? extraRooms.map(r => `<span class="rec-tag"><i class="fas fa-check-circle" style="color:#10b981;"></i> ${r}</span>`).join('')
        : '<span style="color: var(--text-muted); font-size: 13px;">No additional servant/study rooms</span>';

      document.getElementById('propertyModal').classList.add('active');
    } catch (err) {
      console.error('Modal error:', err);
    }
  },

  async exportFilteredCsv() {
    const payload = this.getFilterPayload();
    payload.page = 1;
    payload.page_size = 5000;

    const res = await fetch('/api/properties/filter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (!data.records.length) return alert('No data to export!');

    const headers = Object.keys(data.records[0]);
    const csvRows = [headers.join(',')];
    data.records.forEach(r => {
      const values = headers.map(h => `"${(r[h] ?? '').toString().replace(/"/g, '""')}"`);
      csvRows.push(values.join(','));
    });

    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `gurgaon_real_estate_filtered_${Date.now()}.csv`;
    a.click();
  }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.AppManager.init();
});
