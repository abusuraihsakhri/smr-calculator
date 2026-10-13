/* Browser-only presentation for the SMR statistical engine. */
(function () {
  'use strict';
  const byId = id => document.getElementById(id);
  const numeric = (n, digits = 3) => Number(n).toLocaleString('en-US', {
    maximumFractionDigits: digits, minimumFractionDigits: digits
  });
  const plain = n => Number(n).toLocaleString('en-US', {maximumFractionDigits: 6});
  let latest = null;

  function showResult(result) {
    byId('smr-result').textContent = numeric(result.smr);
    byId('ci-result').textContent = (100 * result.confidence_level).toFixed(0) +
      '% exact Poisson CI: ' + numeric(result.ci_lower) + ' – ' + numeric(result.ci_upper);
    byId('smr100').textContent = numeric(result.smr_per_100, 1);
    byId('observed-result').textContent = plain(result.observed);
    byId('expected-result').textContent = plain(result.expected);
    byId('excess-result').textContent = (result.excess_deaths > 0 ? '+' : '') + plain(result.excess_deaths);
    byId('relative-result').textContent = (result.relative_difference_percent > 0 ? '+' : '') +
      numeric(result.relative_difference_percent, 1) + '%';
  }

  byId('single-form').addEventListener('submit', event => {
    event.preventDefault();
    byId('single-error').textContent = '';
    try {
      showResult(SMR.calculate(byId('observed').value, byId('expected').value,
        Number(byId('confidence').value)));
    } catch (error) {
      byId('single-error').textContent = error.message;
    }
  });
  byId('clear-single').addEventListener('click', () => {
    byId('single-form').reset();
    byId('single-error').textContent = '';
    showResult(SMR.calculate(45, 36, 0.95));
  });

  function parseCSV(input) {
    if (input.length > 2_000_000) throw new Error('CSV exceeds the 2 MB input limit.');
    const text = input.replace(/^\uFEFF/, '');
    const cells = [];
    let row = [], field = '', quoted = false, afterQuote = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (quoted) {
        if (c === '"') {
          if (text[i + 1] === '"') { field += '"'; i++; }
          else { quoted = false; afterQuote = true; }
        } else field += c;
      } else if (c === '"') {
        if (field.trim() || afterQuote) throw new Error('Malformed CSV quote near position ' + (i + 1));
        quoted = true;
      } else if (c === ',') {
        row.push(field); field = ''; afterQuote = false;
      } else if (c === '\n' || c === '\r') {
        if (c === '\r' && text[i + 1] === '\n') i++;
        row.push(field); field = ''; afterQuote = false;
        if (row.some(cell => cell.trim() !== '')) cells.push(row);
        row = [];
        if (cells.length > 10001) throw new Error('CSV is limited to 10,000 data rows.');
      } else {
        if (afterQuote && !/\s/.test(c)) throw new Error('Unexpected character after quoted field.');
        field += c;
      }
    }
    if (quoted) throw new Error('Unclosed CSV quoted field.');
    row.push(field);
    if (row.some(cell => cell.trim() !== '')) cells.push(row);
    if (cells.length < 2) throw new Error('CSV needs a header and at least one data row.');
    if (cells.length > 10001) throw new Error('CSV is limited to 10,000 data rows.');
    const names = cells[0].map(value => value.trim().toLowerCase());
    if (new Set(names).size !== names.length) throw new Error('CSV contains duplicate column names.');
    const observed = names.indexOf('observed'), expected = names.indexOf('expected');
    const stratum = names.indexOf('stratum');
    if (observed === -1 || expected === -1) {
      throw new Error('CSV headers must include observed and expected.');
    }
    return cells.slice(1).map((values, index) => {
      if (values.length !== names.length) throw new Error('CSV row ' + (index + 2) + ' has an incorrect column count.');
      const record = {
        stratum: stratum === -1 ? 'Row ' + (index + 1) : values[stratum].trim() || 'Row ' + (index + 1),
        observed: values[observed].trim(), expected: values[expected].trim()
      };
      // Validate each row even when the aggregate would otherwise appear valid.
      const counts = SMR.validate(record.observed, record.expected);
      return {...record, observed: counts.observed, expected: counts.expected};
    });
  }

  function addCell(row, value) {
    const cell = document.createElement('td');
    cell.textContent = String(value);
    row.appendChild(cell);
  }

  byId('csv-file').addEventListener('change', async event => {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    byId('csv-error').textContent = '';
    if (file.size > 2_000_000) {
      byId('csv-error').textContent = 'CSV exceeds the 2 MB file limit.';
      return;
    }
    try {
      byId('csv-data').value = await file.text();
    } catch {
      byId('csv-error').textContent = 'Unable to read the selected file.';
    }
  });

  byId('csv-example').addEventListener('click', () => {
    byId('csv-file').value = '';
    byId('csv-data').value = 'stratum,observed,expected\nAge 45–64,12,10.5\nAge 65+,33,25.5';
    byId('csv-error').textContent = '';
  });

  byId('csv-analyze').addEventListener('click', () => {
    byId('csv-error').textContent = '';
    byId('csv-results').hidden = true;
    byId('csv-export').disabled = true;
    latest = null;
    try {
      const rows = parseCSV(byId('csv-data').value);
      const result = SMR.aggregate(rows, Number(byId('confidence').value));
      latest = {rows, result};
      showResult(result);
      byId('csv-summary').textContent = rows.length + ' strata • ' + result.observed + ' observed deaths • ' +
        plain(result.expected) + ' expected deaths • overall SMR ' + numeric(result.smr) +
        ' (' + (result.confidence_level * 100).toFixed(0) + '% CI: ' +
        numeric(result.ci_lower) + '–' + numeric(result.ci_upper) + ')';
      const tbody = byId('csv-preview');
      tbody.replaceChildren();
      rows.slice(0, 12).forEach(record => {
        const tr = document.createElement('tr');
        addCell(tr, record.stratum);
        addCell(tr, record.observed);
        addCell(tr, record.expected);
        addCell(tr, numeric(SMR.calculate(record.observed, record.expected).smr));
        tbody.appendChild(tr);
      });
      byId('csv-preview-note').textContent = rows.length > 12 ?
        'Showing first 12 strata; the export includes all ' + rows.length + '.' : '';
      byId('csv-results').hidden = false;
      byId('csv-export').disabled = false;
    } catch (error) {
      byId('csv-error').textContent = error.message;
    }
  });

  function csvCell(value, columnIndex) {
    let text = String(value);
    // Protect spreadsheet imports against CSV formula injection from labels.
    if (columnIndex === 1 && /^[\s]*[=+@-]/.test(text)) text = "'" + text;
    return '"' + text.replace(/"/g, '""') + '"';
  }

  byId('csv-export').addEventListener('click', async () => {
    if (!latest) return;
    const result = latest.result;
    const lines = [
      ['type', 'stratum', 'observed', 'expected', 'smr', 'ci_lower', 'ci_upper', 'confidence_level', 'excess_deaths'],
      ['overall', 'all strata', result.observed, result.expected, result.smr,
        result.ci_lower, result.ci_upper, result.confidence_level, result.excess_deaths]
    ];
    const button = byId('csv-export');
    button.disabled = true;
    try {
      for (let i = 0; i < latest.rows.length; i++) {
        const row = latest.rows[i];
        const item = SMR.calculate(row.observed, row.expected, result.confidence_level);
        lines.push(['stratum', row.stratum, item.observed, item.expected, item.smr,
          item.ci_lower, item.ci_upper, item.confidence_level, item.excess_deaths]);
        if (i % 100 === 99) {
          button.textContent = 'Preparing ' + (i + 1) + '/' + latest.rows.length;
          await new Promise(resolve => setTimeout(resolve, 0));
        }
      }
    } finally {
      button.textContent = 'Download results CSV';
      button.disabled = false;
    }
    const blob = new Blob([lines.map(line => line.map((value, index) => csvCell(value, index)).join(',')).join('\r\n') + '\r\n'],
      {type: 'text/csv;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'smr-results.csv';
    document.body.appendChild(a);
    a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });

  showResult(SMR.calculate(45, 36, 0.95));
})();
