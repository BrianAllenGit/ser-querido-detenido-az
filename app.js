(function () {
  'use strict';
  // Nothing is stored and nothing is sent. The language choice lives only in the page address (?lang=en).
  var TITLES = { es: 'Mi familiar fue detenido por ICE: las mejores guías', en: 'A loved one was detained by ICE: the best guides' };
  var DESCS = {
    es: 'Guías ya hechas por organizaciones para familias de personas detenidas por ICE, en español e inglés, a un toque. Con las herramientas oficiales. Sin rastreo.',
    en: 'Guides already made by organizations for families of people detained by ICE, in Spanish and English, one tap away. With the official tools. No tracking.'
  };
  var root = document.documentElement;

  function current() { return root.classList.contains('en') ? 'en' : 'es'; }

  function setLang(lang, keepHash) {
    if (lang !== 'en') lang = 'es';
    root.classList.toggle('en', lang === 'en');
    root.lang = lang;
    document.title = TITLES[lang];
    var md = document.querySelector('meta[name="description"]');
    if (md) md.setAttribute('content', DESCS[lang]);
    document.getElementById('lang-es').setAttribute('aria-pressed', String(lang === 'es'));
    document.getElementById('lang-en').setAttribute('aria-pressed', String(lang === 'en'));
    try {
      var hash = keepHash ? location.hash : '';
      history.replaceState(null, '', location.pathname + (lang === 'en' ? '?lang=en' : '') + hash);
    } catch (e) { /* file:// or old browser: the page still works */ }
  }

  function initial() {
    var m = /[?&]lang=(en|es)\b/.exec(location.search);
    if (m) return m[1];
    var h = /^#(en|es)-/.exec(location.hash);
    if (h) return h[1];
    return 'es'; // Spanish first
  }

  document.getElementById('lang-es').addEventListener('click', function () { setLang('es'); });
  document.getElementById('lang-en').addEventListener('click', function () { setLang('en'); });

  var printers = document.querySelectorAll('.js-print');
  // The print button prints the card: the answer and the steps only.
  for (var i = 0; i < printers.length; i++) printers[i].addEventListener('click', function () {
    root.classList.add('print-card');
    window.print();
  });
  window.addEventListener('afterprint', function () { root.classList.remove('print-card'); });

  // Move keyboard and screen reader focus to the section a menu button jumps to.
  document.addEventListener('click', function (e) {
    var a = e.target.closest ? e.target.closest('a[href^="#"]') : null;
    if (!a) return;
    var t = document.getElementById(a.getAttribute('href').slice(1));
    if (t && t.hasAttribute('tabindex')) setTimeout(function () { t.focus({ preventScroll: true }); }, 0);
  });

  setLang(initial(), true);
  if (location.hash && current() === 'en') {
    var el = document.getElementById(location.hash.slice(1));
    if (el) el.scrollIntoView();
  }
})();
