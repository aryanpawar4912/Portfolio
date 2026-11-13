document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('responsiveNavToggle');
    const sidebar = document.getElementById('interactiveSidebarNode');
    const overlay = document.getElementById('responsiveBlurOverlay');

    const setDrawerOpen = (isOpen) => {
        if (!toggle || !sidebar || !overlay) return;
        sidebar.classList.toggle('mobile-drawer-active', isOpen);
        overlay.classList.toggle('mobile-drawer-active', isOpen);
        toggle.setAttribute('aria-expanded', String(isOpen));
    };

    if (toggle && sidebar && overlay) {
        toggle.addEventListener('click', () => {
            setDrawerOpen(toggle.getAttribute('aria-expanded') !== 'true');
        });
        overlay.addEventListener('click', () => setDrawerOpen(false));
        sidebar.querySelectorAll('a').forEach((link) => {
            link.addEventListener('click', () => setDrawerOpen(false));
        });
        window.addEventListener('resize', () => {
            if (window.innerWidth > 991) setDrawerOpen(false);
        });
    }

    const welcome = document.getElementById('adminWelcome');
    if (welcome && typeof welcome.showModal === 'function') {
        const welcomeKey = 'admin-workspace-welcome-seen';
        let alreadySeen = false;
        try {
            alreadySeen = window.sessionStorage.getItem(welcomeKey) === 'true';
        } catch (error) {
            console.warn('Admin welcome session storage is unavailable:', error);
        }

        const dismissWelcome = () => {
            try {
                window.sessionStorage.setItem(welcomeKey, 'true');
            } catch (error) {
                console.warn('Unable to save the admin welcome preference:', error);
            }
            welcome.classList.add('is-leaving');
            window.setTimeout(() => {
                if (welcome.open) welcome.close();
                welcome.classList.remove('is-leaving');
            }, 320);
        };

        if (!alreadySeen) {
            welcome.showModal();
            welcome.querySelector('[data-welcome-dismiss]')?.focus();
            welcome.querySelectorAll('[data-welcome-dismiss]').forEach((button) => {
                button.addEventListener('click', dismissWelcome, { once: true });
            });
            welcome.addEventListener('cancel', () => {
                try {
                    window.sessionStorage.setItem(welcomeKey, 'true');
                } catch (error) {
                    console.warn('Unable to save the admin welcome preference:', error);
                }
            }, { once: true });
            window.setTimeout(() => {
                if (welcome.open) dismissWelcome();
            }, 4800);
        }
    }

    const palette = document.getElementById('commandPalette');
    const searchInput = document.getElementById('commandSearchInput');
    const searchResults = document.getElementById('commandSearchResults');
    const quickLinks = document.getElementById('commandQuickLinks');
    const openPaletteButtons = document.querySelectorAll('[data-command-open]');
    const closePaletteButton = document.querySelector('[data-command-close]');
    let searchTimer = 0;
    let activeRequest = null;
    let searchSequence = 0;

    const closePalette = () => {
        if (palette?.open) palette.close();
    };

    const openPalette = () => {
        if (!palette || typeof palette.showModal !== 'function') return;
        palette.showModal();
        searchInput?.focus();
    };

    const showSearchMessage = (message) => {
        if (!searchResults) return;
        searchResults.replaceChildren();
        const row = document.createElement('p');
        row.className = 'command-search-message';
        row.textContent = message;
        searchResults.append(row);
    };

    const renderSearchResults = (results) => {
        if (!searchResults) return;
        searchResults.replaceChildren();
        if (!results.length) {
            showSearchMessage('No matching records found.');
            return;
        }

        results.forEach((result) => {
            const row = document.createElement('div');
            row.className = 'command-result-row';
            const link = document.createElement('a');
            link.className = 'command-result-link';
            link.href = result.url;
            link.setAttribute('role', 'option');
            const icon = document.createElement('i');
            icon.className = result.kind === 'Message'
                ? 'bi bi-inbox'
                : result.kind === 'Project'
                    ? 'bi bi-window-stack'
                    : result.kind === 'Article'
                        ? 'bi bi-journal-text'
                        : 'bi bi-person-vcard';
            icon.setAttribute('aria-hidden', 'true');
            const title = document.createElement('span');
            title.className = 'command-result-title';
            title.textContent = result.title;
            const kind = document.createElement('span');
            kind.className = 'command-result-kind';
            kind.textContent = result.kind;
            const arrow = document.createElement('i');
            arrow.className = 'bi bi-arrow-return-left';
            arrow.setAttribute('aria-hidden', 'true');
            link.append(icon, title, kind, arrow);
            row.append(link);

            if (result.preview_url) {
                const preview = document.createElement('a');
                preview.className = 'command-result-preview';
                preview.href = result.preview_url;
                preview.target = '_blank';
                preview.rel = 'noopener noreferrer';
                preview.textContent = 'PREVIEW';
                preview.setAttribute('aria-label', `Preview ${result.title} in a new tab`);
                row.append(preview);
            }
            searchResults.append(row);
        });
    };

    const searchRecords = async (query) => {
        if (!palette || !searchResults || !quickLinks) return;
        const normalizedQuery = query.trim();
        quickLinks.hidden = normalizedQuery.length > 0;
        if (activeRequest) activeRequest.abort();
        if (normalizedQuery.length < 2) {
            searchResults.replaceChildren();
            return;
        }

        activeRequest = new AbortController();
        const requestSequence = ++searchSequence;
        showSearchMessage('Searching workspace…');
        try {
            const response = await fetch(
                `${palette.dataset.searchUrl}?q=${encodeURIComponent(normalizedQuery)}`,
                { credentials: 'same-origin', headers: { Accept: 'application/json' }, signal: activeRequest.signal }
            );
            if (!response.ok) throw new Error(`Search failed with status ${response.status}`);
            const data = await response.json();
            if (requestSequence === searchSequence) renderSearchResults(data.results);
        } catch (error) {
            if (error.name === 'AbortError') return;
            console.error('Unable to search workspace records:', error);
            showSearchMessage('Search is unavailable. Try again in a moment.');
        }
    };

    openPaletteButtons.forEach((button) => button.addEventListener('click', openPalette));
    closePaletteButton?.addEventListener('click', closePalette);
    palette?.addEventListener('click', (event) => {
        if (event.target === palette) closePalette();
    });
    searchInput?.addEventListener('input', () => {
        window.clearTimeout(searchTimer);
        searchTimer = window.setTimeout(() => searchRecords(searchInput.value), 160);
    });
    searchInput?.addEventListener('keydown', (event) => {
        const options = searchResults?.querySelectorAll('.command-result-link') || [];
        if (event.key === 'ArrowDown' && options.length) {
            event.preventDefault();
            options[0].focus();
        } else if (event.key === 'Enter' && options.length) {
            event.preventDefault();
            options[0].click();
        } else if (!searchInput.value && !event.ctrlKey && !event.metaKey && !event.altKey) {
            const quickKeyTargets = { p: 0, w: 1, r: 2, i: 3 };
            const targetIndex = quickKeyTargets[event.key.toLowerCase()];
            const target = targetIndex === undefined
                ? null
                : quickLinks?.querySelectorAll('a')[targetIndex];
            if (target) {
                event.preventDefault();
                window.location.assign(target.href);
            }
        }
    });
    searchResults?.addEventListener('keydown', (event) => {
        const options = [...searchResults.querySelectorAll('.command-result-link')];
        const index = options.indexOf(document.activeElement);
        if (event.key === 'ArrowDown' && index < options.length - 1) {
            event.preventDefault();
            options[index + 1].focus();
        } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            if (index <= 0) searchInput?.focus();
            else options[index - 1].focus();
        }
    });
    document.addEventListener('keydown', (event) => {
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
            event.preventDefault();
            openPalette();
        } else if (event.key === 'Escape') {
            closePalette();
            setDrawerOpen(false);
        }
    });

    const counters = document.querySelectorAll('[data-count-up]');
    const animateCounter = (element) => {
        const target = Number(element.dataset.countUp);
        if (!Number.isFinite(target)) return;
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            element.textContent = String(target);
            return;
        }
        const start = performance.now();
        const duration = 720;
        const update = (now) => {
            const progress = Math.min(1, (now - start) / duration);
            element.textContent = String(Math.round(target * (1 - (1 - progress) ** 3)));
            if (progress < 1) window.requestAnimationFrame(update);
        };
        window.requestAnimationFrame(update);
    };
    if ('IntersectionObserver' in window) {
        const counterObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            });
        }, { threshold: 0.6 });
        counters.forEach((counter) => counterObserver.observe(counter));
    } else {
        counters.forEach(animateCounter);
    }
});
