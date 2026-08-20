// Local-first product state. GitHub authentication will later sync this exact
// model across devices; browsing and deciding never require an account.

(() => {
  const STORAGE_KEY = 'kgnx.state.v2';
  const grid = document.querySelector('[data-grid]');
  const controls = document.querySelector('.controls');
  const cards = [...document.querySelectorAll('[data-tool]')];
  if (!grid || !controls || !cards.length) return;

  const defaults = {
    statuses: {},
    dismissed: [],
    preferences: { kind: 'all', platform: 'all', categories: [] },
    view: 'discover'
  };

  const state = (() => {
    try {
      const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
      return {
        ...defaults,
        ...stored,
        statuses: stored.statuses || {},
        dismissed: stored.dismissed || [],
        preferences: { ...defaults.preferences, ...(stored.preferences || {}) }
      };
    } catch {
      return structuredClone(defaults);
    }
  })();

  const search = controls.querySelector('[data-search]');
  const empty = document.querySelector('[data-empty]');
  const emptyCopy = document.querySelector('[data-empty-copy]');
  const title = document.querySelector('[data-view-title]');
  const eyebrow = document.querySelector('[data-view-eyebrow]');
  const summary = document.querySelector('[data-summary]');
  const toast = document.querySelector('[data-toast]');
  // Scoped to the control bar: cards carry similar attributes for filtering.
  const kindChips = [...controls.querySelectorAll('[data-kind]')];
  const platformChips = [...controls.querySelectorAll('[data-platform]')];
  const categoryChips = [...controls.querySelectorAll('[data-category]')];
  const viewButtons = [...document.querySelectorAll('[data-view]')];
  const detail = document.querySelector('[data-detail]');
  const detailBody = document.querySelector('[data-detail-body]');
  let toastTimer;
  let catalogue;
  let openSlug;

  const views = {
    discover: { eyebrow: 'Discover', title: 'Worth a look', empty: 'Try another kind, platform, or category.' },
    saved: { eyebrow: 'Your shortlist', title: 'Saved for later', empty: 'Save anything you want to remember.' },
    try: { eyebrow: 'Your queue', title: 'Try next', empty: 'Queue something you actually intend to install.' },
    using: { eyebrow: 'Your stack', title: 'Tools you use', empty: 'Mark what you already use to shape recommendations.' },
    archive: { eyebrow: 'Previous editions', title: 'Archive', empty: 'Published tools move here after 30 days.' }
  };

  const persist = () => localStorage.setItem(STORAGE_KEY, JSON.stringify(state));

  const notify = (message) => {
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 1800);
  };

  const refreshCounts = () => {
    for (const status of ['saved', 'try', 'using']) {
      const total = Object.values(state.statuses).filter((value) => value === status).length;
      for (const node of document.querySelectorAll(`[data-count="${status}"]`)) {
        node.textContent = node.closest('.profile-stats') ? total : total || '';
      }
    }
  };

  const paint = (card) => {
    const status = state.statuses[card.dataset.tool] || '';
    card.dataset.status = status;
    for (const button of card.querySelectorAll('[data-action]')) {
      const active = button.dataset.action === status;
      button.classList.toggle('active', active);
      button.setAttribute('aria-pressed', String(active));
    }
  };

  const passesFilters = (card) => {
    const { kind, platform, categories } = state.preferences;
    if (kind !== 'all' && card.dataset.toolKind !== kind) return false;

    if (platform !== 'all') {
      const wanted = platform.split(' ');
      if (!wanted.some((value) => card.dataset.platforms.includes(value))) return false;
    }
    if (categories.length && !categories.some((value) => card.dataset.categories.includes(value))) {
      return false;
    }

    const query = (search?.value || '').trim().toLowerCase();
    return !query || card.dataset.haystack.includes(query);
  };

  const describeFilters = (shown) => {
    const parts = [`${shown} of ${cards.length}`];
    const kind = kindChips.find((chip) => chip.dataset.kind === state.preferences.kind);
    if (state.preferences.kind !== 'all' && kind) {
      parts.push(kind.textContent.replace(/\d+$/, '').trim());
    }
    const platform = platformChips.find((chip) => chip.dataset.platform === state.preferences.platform);
    if (state.preferences.platform !== 'all' && platform) parts.push(platform.textContent.trim());
    if (state.preferences.categories.length) {
      parts.push(`${state.preferences.categories.length} categories`);
    }
    const query = (search?.value || '').trim();
    if (query) parts.push(`“${query}”`);
    return parts.join(' · ');
  };

  const hasFilters = () =>
    state.preferences.kind !== 'all' ||
    state.preferences.platform !== 'all' ||
    state.preferences.categories.length > 0 ||
    Boolean((search?.value || '').trim());

  const apply = () => {
    const view = state.view;
    const dismissed = new Set(state.dismissed);
    let shown = 0;

    for (const card of cards) {
      const status = state.statuses[card.dataset.tool] || '';
      const inView = view === 'discover'
        ? card.dataset.lifecycle === 'active' && !dismissed.has(card.dataset.tool)
        : view === 'archive'
          ? card.dataset.lifecycle === 'archived'
          : status === view;
      const visible = inView && passesFilters(card);
      card.hidden = !visible;
      if (visible) shown += 1;
      paint(card);
    }

    const copy = views[view];
    eyebrow.textContent = copy.eyebrow;
    title.textContent = copy.title;
    emptyCopy.textContent = hasFilters() ? 'No match for the current filters.' : copy.empty;
    empty.hidden = shown > 0;
    summary.textContent = describeFilters(shown);

    for (const button of viewButtons) {
      button.classList.toggle('active', button.dataset.view === view);
    }
    refreshCounts();
  };

  /* Detail view */

  const loadCatalogue = async () => {
    if (catalogue) return catalogue;
    const response = await fetch('tools.json');
    catalogue = await response.json();
    return catalogue;
  };

  const fact = (label, value) => `<div><dt>${label}</dt><dd>${value}</dd></div>`;

  const detailHtml = (tool) => {
    const trust = tool.trust;
    const gh = tool.github;
    const days = trust.last_push_days;
    const activity = days === 0 ? 'today' : days === null ? 'unknown' : `${days} days ago`;
    const status = state.statuses[tool.slug] || '';

    const facts = [
      fact('Last commit', activity),
      fact('Maturity', trust.maturity),
      fact('Contributors', trust.contributors ?? '—'),
      fact('Releases', trust.releases ?? '—'),
      fact('Tests', trust.has_tests ? 'yes' : 'not detected'),
      fact('CI', trust.has_ci ? 'configured' : 'not detected'),
      fact('Licence', trust.license || 'not detected'),
      fact('Language', trust.language || 'mixed'),
      fact('Stars', trust.stars.toLocaleString('en-GB').replace(/,/g, ' ')),
      fact('Commits', (trust.commits || 0).toLocaleString('en-GB').replace(/,/g, ' '))
    ].join('');

    const install = tool.install
      ? `<div class="detail-install">
           <span>Install</span>
           <code>${tool.install}</code>
           <button class="copy" data-copy="${tool.install}">Copy</button>
         </div>`
      : `<p class="detail-note">No single install command: follow the project's
         deployment instructions.</p>`;

    const description = gh.description && gh.description !== tool.pitch
      ? `<p class="detail-upstream"><span>From the project</span>${gh.description}</p>`
      : '';

    const topics = (gh.topics || []).slice(0, 8)
      .map((topic) => `<span>${topic}</span>`).join('');
    const automated = tool.automated
      ? `<p class="auto-reason"><b>Automatically selected</b>${tool.selection_reason}</p>`
      : '';

    return `
      <p class="eyebrow">${tool.kind_label} · ${tool.platforms.join(' · ')}</p>
      <h2>${tool.name}</h2>
      <p class="detail-pitch">${tool.pitch}</p>
      ${automated}
      ${description}
      <div class="traits">${tool.traits.map((t) => `<span>${t}</span>`).join('')}</div>
      ${install}
      <div class="detail-actions">
        <button class="action save ${status === 'saved' ? 'active' : ''}" data-action="saved">Save</button>
        <button class="action try ${status === 'try' ? 'active' : ''}" data-action="try">Try next</button>
        <button class="action using ${status === 'using' ? 'active' : ''}" data-action="using">I use this</button>
      </div>
      <h3 class="detail-heading">Why trust it</h3>
      <dl class="detail-facts">${facts}</dl>
      ${topics ? `<div class="detail-topics">${topics}</div>` : ''}
      <div class="detail-links">
        <a href="${tool.get_url}" target="_blank" rel="noopener">Project page ↗</a>
        <a href="${gh.url}" target="_blank" rel="noopener">Source on GitHub ↗</a>
      </div>`;
  };

  const openDetail = async (slug) => {
    openSlug = slug;
    detailBody.innerHTML = '<p class="detail-loading">Loading…</p>';
    if (!detail.open) detail.showModal();
    const data = await loadCatalogue();
    const tool = data.tools.find((item) => item.slug === slug);
    detailBody.innerHTML = tool ? detailHtml(tool) : '<p>Details unavailable.</p>';
  };

  const setStatus = (slug, action) => {
    const wasActive = state.statuses[slug] === action;
    if (wasActive) delete state.statuses[slug];
    else state.statuses[slug] = action;
    persist();
    apply();
    const messages = {
      saved: ['Saved for later', 'Removed from Saved'],
      try: ['Added to Try next', 'Removed from Try next'],
      using: ['Added to your stack', 'Removed from your stack']
    };
    notify(messages[action][wasActive ? 1 : 0]);
  };

  grid.addEventListener('click', (event) => {
    const card = event.target.closest('[data-tool]');
    if (!card) return;
    const slug = card.dataset.tool;
    const action = event.target.closest('[data-action]');

    if (action) {
      if (action.dataset.action === 'dismiss') {
        if (!state.dismissed.includes(slug)) state.dismissed.push(slug);
        persist();
        apply();
        notify('Hidden from discovery');
        return;
      }
      setStatus(slug, action.dataset.action);
      return;
    }

    openDetail(slug);
  });

  detail.addEventListener('click', async (event) => {
    const copy = event.target.closest('[data-copy]');
    if (copy) {
      try {
        await navigator.clipboard.writeText(copy.dataset.copy);
        notify('Install command copied');
      } catch {
        notify('Copying was blocked by the browser');
      }
      return;
    }
    const action = event.target.closest('[data-action]');
    if (action && openSlug) {
      setStatus(openSlug, action.dataset.action);
      openDetail(openSlug);
      return;
    }
    if (event.target === detail) detail.close();
  });

  for (const button of viewButtons) {
    button.addEventListener('click', () => {
      if (!views[button.dataset.view]) return;
      state.view = button.dataset.view;
      persist();
      apply();
      document.querySelector('.feed')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }

  const exclusive = (chips, chip, key) => {
    state.preferences[key] = chip.dataset[key];
    for (const peer of chips) {
      const active = peer === chip;
      peer.classList.toggle('active', active);
      peer.setAttribute('aria-pressed', String(active));
    }
    persist();
    apply();
  };

  for (const chip of kindChips) {
    chip.addEventListener('click', () => exclusive(kindChips, chip, 'kind'));
  }
  for (const chip of platformChips) {
    chip.addEventListener('click', () => exclusive(platformChips, chip, 'platform'));
  }
  for (const chip of categoryChips) {
    chip.addEventListener('click', () => {
      const selected = new Set(state.preferences.categories);
      const value = chip.dataset.category;
      if (selected.has(value)) selected.delete(value);
      else selected.add(value);
      state.preferences.categories = [...selected];
      chip.setAttribute('aria-pressed', String(selected.has(value)));
      persist();
      apply();
    });
  }

  search?.addEventListener('input', apply);

  const clearFilters = () => {
    state.preferences = { kind: 'all', platform: 'all', categories: [] };
    if (search) search.value = '';
    for (const [chips, key] of [[kindChips, 'kind'], [platformChips, 'platform']]) {
      for (const chip of chips) {
        const active = chip.dataset[key] === 'all';
        chip.classList.toggle('active', active);
        chip.setAttribute('aria-pressed', String(active));
      }
    }
    for (const chip of categoryChips) chip.setAttribute('aria-pressed', 'false');
    persist();
    apply();
  };

  document.querySelector('[data-clear]')?.addEventListener('click', clearFilters);

  const profileDialog = document.querySelector('[data-profile-dialog]');
  document.querySelector('[data-profile]')?.addEventListener('click', () => profileDialog.showModal());
  for (const button of document.querySelectorAll('[data-dialog-close]')) {
    button.addEventListener('click', () => button.closest('dialog')?.close());
  }
  profileDialog?.addEventListener('click', (event) => {
    if (event.target === profileDialog) profileDialog.close();
  });

  document.querySelector('[data-export]')?.addEventListener('click', () => {
    const tools = cards
      .map((card) => ({
        tool: card.querySelector('.tool-name')?.textContent.trim(),
        slug: card.dataset.tool,
        kind: card.dataset.toolKind,
        status: state.statuses[card.dataset.tool] || null
      }))
      .filter((item) => item.status);
    const blob = new Blob(
      [JSON.stringify({ exportedAt: new Date().toISOString(), tools, preferences: state.preferences }, null, 2)],
      { type: 'application/json' }
    );
    const url = URL.createObjectURL(blob);
    Object.assign(document.createElement('a'), { href: url, download: 'kgnx-my-tools.json' }).click();
    URL.revokeObjectURL(url);
    notify('Your list was exported');
  });

  // Restore control state before the first paint.
  for (const [chips, key] of [[kindChips, 'kind'], [platformChips, 'platform']]) {
    for (const chip of chips) {
      const active = chip.dataset[key] === state.preferences[key];
      chip.classList.toggle('active', active);
      chip.setAttribute('aria-pressed', String(active));
    }
  }
  for (const chip of categoryChips) {
    chip.setAttribute('aria-pressed', String(state.preferences.categories.includes(chip.dataset.category)));
  }
  apply();

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('sw.js').catch(() => {});
    });
  }
})();
