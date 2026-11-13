'use strict';

document.documentElement.classList.add('js');

document.addEventListener('DOMContentLoaded', () => {
  const welcome = document.getElementById('viewerWelcome');
  if (welcome && typeof welcome.showModal === 'function') {
    const welcomeKey = 'portfolio-welcome-seen';
    const setWelcomeSeen = () => {
      try {
        window.sessionStorage.setItem(welcomeKey, 'true');
      } catch (error) {
        console.warn('Unable to save the welcome-screen preference:', error);
      }
    };
    const dismissWelcome = () => {
      setWelcomeSeen();
      welcome.classList.add('is-leaving');
      window.setTimeout(() => {
        if (welcome.open) welcome.close();
        welcome.classList.remove('is-leaving');
      }, 360);
    };

    let alreadySeen = false;
    try {
      alreadySeen = window.sessionStorage.getItem(welcomeKey) === 'true';
    } catch (error) {
      console.warn('Welcome-screen session storage is unavailable:', error);
    }

    if (!alreadySeen) {
      welcome.showModal();
      welcome.querySelector('[data-welcome-dismiss]')?.focus();
      welcome.querySelectorAll('[data-welcome-dismiss]').forEach((button) => {
        button.addEventListener('click', dismissWelcome, { once: true });
      });
      welcome.addEventListener('cancel', setWelcomeSeen, { once: true });
      window.setTimeout(() => {
        if (welcome.open) dismissWelcome();
      }, 5200);
    }
  }

  const themeToggle = document.querySelector('.theme-toggle');
  const themeIcon = themeToggle?.querySelector('i');
  let savedTheme = null;
  try {
    savedTheme = window.localStorage.getItem('portfolio-theme');
  } catch (error) {
    console.warn('Theme preference storage is unavailable:', error);
  }
  if (savedTheme === 'dark') document.documentElement.dataset.theme = 'dark';

  const updateThemeButton = () => {
    const isDark = document.documentElement.dataset.theme === 'dark';
    const themeColor = document.querySelector('meta[name="theme-color"]');
    if (themeIcon) themeIcon.className = isDark ? 'bi bi-sun' : 'bi bi-moon-stars';
    if (themeColor) themeColor.content = isDark ? '#101a31' : '#fff5e3';
    if (themeToggle) {
      themeToggle.setAttribute('aria-label', isDark ? 'Switch to light theme' : 'Switch to dark theme');
      themeToggle.title = isDark ? 'Switch to light theme' : 'Switch to dark theme';
    }
  };
  updateThemeButton();
  themeToggle?.addEventListener('click', () => {
    const isDark = document.documentElement.dataset.theme === 'dark';
    if (isDark) {
      delete document.documentElement.dataset.theme;
      try {
        window.localStorage.removeItem('portfolio-theme');
      } catch (error) {
        console.warn('Unable to clear the saved theme preference:', error);
      }
    } else {
      document.documentElement.dataset.theme = 'dark';
      try {
        window.localStorage.setItem('portfolio-theme', 'dark');
      } catch (error) {
        console.warn('Unable to save the theme preference:', error);
      }
    }
    updateThemeButton();
  });

  const navToggle = document.querySelector('.nav-toggle');
  const navPanel = document.querySelector('.nav-panel');

  if (navToggle && navPanel) {
    const closeNavigation = () => {
      navToggle.setAttribute('aria-expanded', 'false');
      navToggle.setAttribute('aria-label', 'Open navigation');
      navPanel.classList.remove('is-open');
    };

    navToggle.addEventListener('click', () => {
      const isExpanded = navToggle.getAttribute('aria-expanded') === 'true';
      navToggle.setAttribute('aria-expanded', String(!isExpanded));
      navToggle.setAttribute('aria-label', isExpanded ? 'Open navigation' : 'Close navigation');
      navPanel.classList.toggle('is-open', !isExpanded);
    });

    navPanel.querySelectorAll('a').forEach((link) => link.addEventListener('click', closeNavigation));
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') closeNavigation();
    });
  }

  const aboutSection = document.getElementById('about');
  const homeNavLinks = document.querySelectorAll('[data-nav-section]');
  if (aboutSection && homeNavLinks.length) {
    const updateHomeNavigation = () => {
      const aboutTop = aboutSection.getBoundingClientRect().top;
      const aboutIsActive = aboutTop <= 150;
      homeNavLinks.forEach((link) => {
        link.classList.toggle('is-active', link.dataset.navSection === (aboutIsActive ? 'about' : 'home'));
      });
    };
    window.addEventListener('scroll', updateHomeNavigation, { passive: true });
    updateHomeNavigation();
  }

  const revealItems = document.querySelectorAll('[data-reveal]');
  if ('IntersectionObserver' in window) {
    const revealObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    revealItems.forEach((item) => revealObserver.observe(item));
  } else {
    revealItems.forEach((item) => item.classList.add('is-visible'));
  }

  const timelineEntries = document.querySelectorAll('.timeline-entry');
  if ('IntersectionObserver' in window && timelineEntries.length) {
    const activeTimelineObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const timeline = entry.target.closest('.timeline-list');
        timeline?.querySelectorAll('.timeline-entry.is-current').forEach((current) => {
          current.classList.remove('is-current');
        });
        entry.target.classList.add('is-current');
      });
    }, { rootMargin: '-43% 0px -43% 0px', threshold: 0 });

    timelineEntries.forEach((entry) => activeTimelineObserver.observe(entry));
  }

  const timelines = document.querySelectorAll('.timeline-list');
  if (timelines.length) {
    let timelineFrame = 0;
    let timelineResizeObserver;
    const updateTimelineProgress = () => {
      timelineFrame = 0;
      const viewportHeight = window.innerHeight;
      timelines.forEach((timeline) => {
        const bounds = timeline.getBoundingClientRect();
        const progress = Math.max(0, Math.min(
          1,
          (viewportHeight * 0.78 - bounds.top) / (bounds.height + viewportHeight * 0.56)
        ));
        timeline.style.setProperty('--timeline-progress', String(progress));
      });
    };
    const scheduleTimelineProgress = () => {
      if (!timelineFrame) timelineFrame = window.requestAnimationFrame(updateTimelineProgress);
    };

    window.addEventListener('scroll', scheduleTimelineProgress, { passive: true });
    window.addEventListener('resize', scheduleTimelineProgress);
    if ('ResizeObserver' in window) {
      timelineResizeObserver = new ResizeObserver(scheduleTimelineProgress);
      timelines.forEach((timeline) => timelineResizeObserver.observe(timeline));
    }
    updateTimelineProgress();
  }

  const filterButtons = document.querySelectorAll('[data-filter]');
  const projectCards = document.querySelectorAll('#projectContainer [data-category]');
  let filterTimers = new WeakMap();

  filterButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const category = button.dataset.filter;
      filterButtons.forEach((item) => {
        const active = item === button;
        item.classList.toggle('is-active', active);
        item.setAttribute('aria-pressed', String(active));
      });

      projectCards.forEach((card) => {
        const matches = category === 'all' || card.dataset.category === category;
        const priorTimer = filterTimers.get(card);
        if (priorTimer) window.clearTimeout(priorTimer);

        if (matches) {
          card.hidden = false;
          requestAnimationFrame(() => card.classList.remove('is-filtering-out'));
        } else {
          card.classList.add('is-filtering-out');
          filterTimers.set(card, window.setTimeout(() => {
            card.hidden = true;
          }, 280));
        }
      });
    });
  });

  const wordCount = (text) => text.trim().split(/\s+/).filter(Boolean).length;
  const readingMinutes = (text) => Math.max(1, Math.ceil(wordCount(text) / 220));

  document.querySelectorAll('[data-reading-source]').forEach((label) => {
    const source = document.getElementById(label.dataset.readingSource);
    if (source) label.textContent = `${readingMinutes(source.textContent)} MIN READ`;
  });

  const articleDialog = document.getElementById('articleDialog');
  if (articleDialog && typeof articleDialog.showModal === 'function') {
    const dialogTitle = document.getElementById('dialogTitle');
    const dialogCategory = document.getElementById('dialogCategory');
    const dialogDate = document.getElementById('dialogDate');
    const dialogReadingTime = document.getElementById('dialogReadingTime');
    const dialogBody = document.getElementById('dialogBody');

    document.querySelectorAll('[data-article-id]').forEach((button) => {
      button.addEventListener('click', () => {
        const source = document.getElementById(button.dataset.articleId);
        if (!source) return;
        dialogTitle.textContent = button.dataset.title;
        dialogCategory.textContent = button.dataset.category;
        dialogDate.textContent = button.dataset.date;
        dialogReadingTime.textContent = `${readingMinutes(source.textContent)} MIN READ`;
        dialogBody.innerHTML = source.innerHTML;
        articleDialog.showModal();
        document.body.classList.add('dialog-open');
      });
    });

    const closeDialog = () => {
      articleDialog.close();
      document.body.classList.remove('dialog-open');
    };
    articleDialog.querySelector('.dialog-close').addEventListener('click', closeDialog);
    articleDialog.addEventListener('click', (event) => {
      if (event.target === articleDialog) closeDialog();
    });
    articleDialog.addEventListener('close', () => document.body.classList.remove('dialog-open'));
  }

  document.querySelectorAll('a[href*="#"]').forEach((link) => {
    link.addEventListener('click', (event) => {
      const url = new URL(link.href, window.location.href);
      if (url.pathname !== window.location.pathname || !url.hash) return;
      const target = document.querySelector(url.hash);
      if (!target) return;
      event.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      history.replaceState(null, '', url.hash);
    });
  });

  document.addEventListener('submit', async (event) => {
    const form = event.target.closest('[data-contact-form]');
    if (!form || !window.fetch) return;
    event.preventDefault();

    const submitButton = form.querySelector('[type="submit"]');
    const originalButtonContent = submitButton.innerHTML;
    submitButton.disabled = true;
    submitButton.textContent = 'Sending…';

    try {
      const response = await fetch(form.action || window.location.href, {
        method: 'POST',
        body: new FormData(form),
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'same-origin'
      });
      if (!response.ok) throw new Error(`Contact request failed with status ${response.status}`);

      const responseDocument = new DOMParser().parseFromString(await response.text(), 'text/html');
      const returnedForm = responseDocument.querySelector('[data-contact-form]');
      if (!returnedForm) throw new Error('The server response did not contain the contact form.');

      const feedback = document.getElementById('messageFeedback');
      feedback.replaceChildren();
      const serverMessage = responseDocument.querySelector('.global-messages .flash-message');
      const formErrors = returnedForm.querySelector('.form-error-summary, .form-error');
      if (serverMessage) {
        feedback.append(serverMessage.cloneNode(true));
      } else if (formErrors) {
        const errorNotice = document.createElement('div');
        errorNotice.className = 'flash-message flash-error';
        errorNotice.setAttribute('role', 'alert');
        errorNotice.textContent = 'Please review the highlighted fields and try again.';
        feedback.append(errorNotice);
      } else {
        throw new Error('The server did not confirm the contact submission.');
      }

      form.replaceWith(returnedForm);
    } catch (error) {
      console.error('Unable to submit the contact form:', error);
      const feedback = document.getElementById('messageFeedback');
      feedback.replaceChildren();
      const errorNotice = document.createElement('div');
      errorNotice.className = 'flash-message flash-error';
      errorNotice.setAttribute('role', 'alert');
      errorNotice.textContent = 'Your message could not be submitted. Please try again or email me directly.';
      feedback.append(errorNotice);
      submitButton.disabled = false;
      submitButton.innerHTML = originalButtonContent;
    }
  });
});
