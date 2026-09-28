// Chart instances manager
window.ChartManager = {
  instances: {},

  destroyChart(id) {
    if (this.instances[id]) {
      this.instances[id].destroy();
      delete this.instances[id];
    }
  },

  getChartColors() {
    const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
    return {
      textColor: isDark ? '#9ca3af' : '#475569',
      gridColor: isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.06)',
      primary: '#6366f1',
      secondary: '#ec4899',
      emerald: '#10b981',
      amber: '#f59e0b',
      cyan: '#06b6d4',
      bgAlpha: isDark ? 'rgba(99, 102, 241, 0.25)' : 'rgba(99, 102, 241, 0.15)'
    };
  },

  renderOverviewCharts(data) {
    const colors = this.getChartColors();

    // 1. Property Type Doughnut Chart
    this.destroyChart('propTypeChart');
    const ctxProp = document.getElementById('propTypeChart');
    if (ctxProp) {
      this.instances['propTypeChart'] = new Chart(ctxProp, {
        type: 'doughnut',
        data: {
          labels: data.property_type_data.labels,
          datasets: [{
            data: data.property_type_data.counts,
            backgroundColor: ['#6366f1', '#f59e0b'],
            borderWidth: 0,
            hoverOffset: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'bottom', labels: { color: colors.textColor, font: { family: 'Inter' } } }
          },
          cutout: '70%'
        }
      });
    }

    // 2. Top Sectors Bar Chart
    this.destroyChart('topSectorsChart');
    const ctxSectors = document.getElementById('topSectorsChart');
    if (ctxSectors) {
      const secLabels = Object.keys(data.top_sectors);
      const secCounts = Object.values(data.top_sectors);

      this.instances['topSectorsChart'] = new Chart(ctxSectors, {
        type: 'bar',
        data: {
          labels: secLabels,
          datasets: [{
            label: 'Property Listings',
            data: secCounts,
            backgroundColor: 'rgba(99, 102, 241, 0.8)',
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false }
          },
          scales: {
            x: { grid: { display: false }, ticks: { color: colors.textColor } },
            y: { grid: { color: colors.gridColor }, ticks: { color: colors.textColor } }
          }
        }
      });
    }

    // 3. BHK Distribution
    this.destroyChart('bhkDistChart');
    const ctxBhk = document.getElementById('bhkDistChart');
    if (ctxBhk) {
      const bhkLabels = Object.keys(data.bhk_distribution).map(b => `${b} BHK`);
      const bhkCounts = Object.values(data.bhk_distribution);

      this.instances['bhkDistChart'] = new Chart(ctxBhk, {
        type: 'bar',
        data: {
          labels: bhkLabels,
          datasets: [{
            label: 'Count',
            data: bhkCounts,
            backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4'],
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { display: false }, ticks: { color: colors.textColor } },
            y: { grid: { color: colors.gridColor }, ticks: { color: colors.textColor } }
          }
        }
      });
    }

    // 4. Furnishing Doughnut
    this.destroyChart('furnishDistChart');
    const ctxFurnish = document.getElementById('furnishDistChart');
    if (ctxFurnish) {
      const labels = Object.keys(data.furnishing_distribution);
      const counts = Object.values(data.furnishing_distribution);

      this.instances['furnishDistChart'] = new Chart(ctxFurnish, {
        type: 'doughnut',
        data: {
          labels: labels,
          datasets: [{
            data: counts,
            backgroundColor: ['#6b7280', '#06b6d4', '#10b981'],
            borderWidth: 0
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'bottom', labels: { color: colors.textColor } }
          },
          cutout: '65%'
        }
      });
    }
  },

  renderUnivariateChart(data) {
    const colors = this.getChartColors();
    this.destroyChart('univariateMainChart');
    const ctx = document.getElementById('univariateMainChart');
    if (!ctx) return;

    if (data.is_numerical) {
      this.instances['univariateMainChart'] = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: data.histogram.labels,
          datasets: [{
            label: 'Frequency Count',
            data: data.histogram.counts,
            backgroundColor: 'rgba(99, 102, 241, 0.75)',
            borderColor: '#6366f1',
            borderWidth: 1,
            borderRadius: 4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { labels: { color: colors.textColor } },
            tooltip: {
              callbacks: {
                title: (items) => `Range: ${items[0].label}`,
                label: (item) => `Properties: ${item.raw}`
              }
            }
          },
          scales: {
            x: { grid: { display: false }, ticks: { color: colors.textColor, maxRotation: 45 } },
            y: { grid: { color: colors.gridColor }, ticks: { color: colors.textColor } }
          }
        }
      });
    } else {
      this.instances['univariateMainChart'] = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: data.categories.labels,
          datasets: [{
            label: 'Listings Count',
            data: data.categories.counts,
            backgroundColor: 'rgba(236, 72, 153, 0.75)',
            borderColor: '#ec4899',
            borderWidth: 1,
            borderRadius: 4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { labels: { color: colors.textColor } }
          },
          scales: {
            x: { grid: { display: false }, ticks: { color: colors.textColor, maxRotation: 45 } },
            y: { grid: { color: colors.gridColor }, ticks: { color: colors.textColor } }
          }
        }
      });
    }
  },

  renderMultivariateCharts(data) {
    const colors = this.getChartColors();
    const isDark = document.documentElement.getAttribute('data-theme') !== 'light';

    // 1. Interactive Plotly Scatter Plot: Area vs Price
    const scatterContainer = document.getElementById('plotlyScatterAreaPrice');
    if (scatterContainer && window.Plotly) {
      const flatPoints = data.scatter_area_price.filter(p => p.type === 'flat');
      const housePoints = data.scatter_area_price.filter(p => p.type === 'house');

      const traceFlats = {
        x: flatPoints.map(p => p.x),
        y: flatPoints.map(p => p.y),
        text: flatPoints.map(p => `${p.society} (${p.sector})<br>${p.bhk} BHK | ${p.x} Sq.Ft | ₹ ${p.y} Cr`),
        mode: 'markers',
        type: 'scatter',
        name: 'Flats / Apartments',
        marker: { color: '#6366f1', size: 7, opacity: 0.75 }
      };

      const traceHouses = {
        x: housePoints.map(p => p.x),
        y: housePoints.map(p => p.y),
        text: housePoints.map(p => `${p.society} (${p.sector})<br>${p.bhk} BHK | ${p.x} Sq.Ft | ₹ ${p.y} Cr`),
        mode: 'markers',
        type: 'scatter',
        name: 'Independent Houses',
        marker: { color: '#f59e0b', size: 8, opacity: 0.75 }
      };

      const layout = {
        margin: { t: 20, r: 20, b: 50, l: 60 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { color: colors.textColor, family: 'Inter' },
        xaxis: { title: 'Built-up Area (Sq.Ft)', gridcolor: colors.gridColor, zerolinecolor: colors.gridColor },
        yaxis: { title: 'Price (₹ Crores)', gridcolor: colors.gridColor, zerolinecolor: colors.gridColor },
        legend: { orientation: 'h', y: 1.15 }
      };

      Plotly.newPlot(scatterContainer, [traceFlats, traceHouses], layout, { responsive: true, displayModeBar: false });
    }

    // 2. Correlation Matrix Heatmap via Plotly
    const heatmapContainer = document.getElementById('plotlyHeatmap');
    if (heatmapContainer && window.Plotly) {
      const cols = data.correlation_matrix.columns.map(c => c.replace('_', ' ').toUpperCase());
      const zValues = data.correlation_matrix.data;

      const heatTrace = {
        z: zValues,
        x: cols,
        y: cols,
        type: 'heatmap',
        colorscale: isDark ? 'Viridis' : 'YlGnBu',
        hoverongaps: false
      };

      const heatLayout = {
        margin: { t: 20, r: 20, b: 80, l: 100 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { color: colors.textColor, family: 'Inter' },
        xaxis: { tickangle: -30 }
      };

      Plotly.newPlot(heatmapContainer, [heatTrace], heatLayout, { responsive: true, displayModeBar: false });
    }

    // 3. Price by BHK Bar
    this.destroyChart('bhkPriceBarChart');
    const ctxBhkP = document.getElementById('bhkPriceBarChart');
    if (ctxBhkP) {
      this.instances['bhkPriceBarChart'] = new Chart(ctxBhkP, {
        type: 'bar',
        data: {
          labels: data.bhk_price.bhk.map(b => `${b} BHK`),
          datasets: [
            {
              label: 'Median Price (₹ Cr)',
              data: data.bhk_price.median_price,
              backgroundColor: '#10b981',
              borderRadius: 6
            },
            {
              label: 'Mean Price (₹ Cr)',
              data: data.bhk_price.mean_price,
              backgroundColor: '#6366f1',
              borderRadius: 6
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { labels: { color: colors.textColor } } },
          scales: {
            x: { grid: { display: false }, ticks: { color: colors.textColor } },
            y: { grid: { color: colors.gridColor }, ticks: { color: colors.textColor } }
          }
        }
      });
    }
  }
};
