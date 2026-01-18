/**
 * Language Selector for Chainlit
 * Injeta um seletor de idioma no header e sobrescreve navigator.language
 * para forçar o Chainlit a usar o idioma selecionado.
 */

(function () {
    'use strict';

    const LANGUAGES = [
        { code: 'pt-BR', label: 'Português', flag: '🇧🇷' },
        { code: 'en-US', label: 'English', flag: '🇺🇸' },
        { code: 'es', label: 'Español', flag: '🇪🇸' },
        { code: 'fr-FR', label: 'Français', flag: '🇫🇷' },
        { code: 'de-DE', label: 'Deutsch', flag: '🇩🇪' },
        { code: 'zh-CN', label: '中文', flag: '🇨🇳' },
        { code: 'it', label: 'Italiano', flag: '🇮🇹' }
    ];

    const STORAGE_KEY = 'chainlit-language';
    const DEFAULT_LANG = 'pt-BR';

    // === PARTE 1: Sobrescrever navigator.language ANTES do Chainlit usar ===
    // Isso deve rodar o mais cedo possível

    function getCurrentLanguage() {
        return localStorage.getItem(STORAGE_KEY) || DEFAULT_LANG;
    }

    // Sobrescrever navigator.language e navigator.languages
    const selectedLang = getCurrentLanguage();

    try {
        Object.defineProperty(navigator, 'language', {
            get: function () { return selectedLang; },
            configurable: true
        });

        Object.defineProperty(navigator, 'languages', {
            get: function () { return [selectedLang]; },
            configurable: true
        });
    } catch (e) {
        console.warn('Could not override navigator.language:', e);
    }

    // === PARTE 2: setLanguage com reload ===

    function setLanguage(langCode) {
        localStorage.setItem(STORAGE_KEY, langCode);
        window.location.reload();
    }

    // === PARTE 3: UI do Seletor ===

    function createLanguageSelector() {
        const currentLang = getCurrentLanguage();
        const currentLangData = LANGUAGES.find(l => l.code === currentLang) || LANGUAGES[0];

        const container = document.createElement('div');
        container.id = 'language-selector';
        container.style.cssText = `
      position: relative;
      display: flex;
      align-items: center;
      margin-left: 8px;
    `;

        const button = document.createElement('button');
        button.type = 'button';
        button.innerHTML = `${currentLangData.flag} <span style="font-size: 10px;">▼</span>`;
        button.title = 'Selecionar idioma';
        button.style.cssText = `
      background: transparent;
      border: 1px solid rgba(255,255,255,0.2);
      border-radius: 6px;
      padding: 6px 10px;
      cursor: pointer;
      font-size: 16px;
      display: flex;
      align-items: center;
      gap: 4px;
      transition: all 0.2s ease;
    `;

        button.addEventListener('mouseenter', () => {
            button.style.background = 'rgba(255,255,255,0.1)';
        });
        button.addEventListener('mouseleave', () => {
            button.style.background = 'transparent';
        });

        const dropdown = document.createElement('div');
        dropdown.style.cssText = `
      position: absolute;
      top: 100%;
      right: 0;
      margin-top: 4px;
      background: var(--paper-bg, #1e1e1e);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 8px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
      display: none;
      z-index: 9999;
      min-width: 140px;
      overflow: hidden;
    `;

        LANGUAGES.forEach(lang => {
            const item = document.createElement('button');
            item.type = 'button';
            item.innerHTML = `${lang.flag} ${lang.label}`;
            item.style.cssText = `
        display: flex;
        align-items: center;
        gap: 8px;
        width: 100%;
        padding: 10px 14px;
        background: ${lang.code === currentLang ? 'rgba(255,255,255,0.1)' : 'transparent'};
        border: none;
        color: inherit;
        cursor: pointer;
        font-size: 14px;
        text-align: left;
        transition: background 0.15s ease;
      `;

            item.addEventListener('mouseenter', () => {
                item.style.background = 'rgba(255,255,255,0.15)';
            });
            item.addEventListener('mouseleave', () => {
                item.style.background = lang.code === currentLang ? 'rgba(255,255,255,0.1)' : 'transparent';
            });

            item.addEventListener('click', (e) => {
                e.stopPropagation();
                if (lang.code !== currentLang) {
                    setLanguage(lang.code);
                }
                dropdown.style.display = 'none';
            });

            dropdown.appendChild(item);
        });

        button.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
        });

        document.addEventListener('click', () => {
            dropdown.style.display = 'none';
        });

        container.appendChild(button);
        container.appendChild(dropdown);

        return container;
    }

    function injectSelector() {
        const header = document.querySelector('#header') || document.querySelector('header');
        if (!header) {
            setTimeout(injectSelector, 500);
            return;
        }

        if (document.getElementById('language-selector')) {
            return;
        }

        const readmeBtn = document.getElementById('readme-button');
        const actionsContainer = readmeBtn ? readmeBtn.parentElement : null;

        if (actionsContainer) {
            actionsContainer.appendChild(createLanguageSelector());
        }
    }

    // === Inicialização ===

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => setTimeout(injectSelector, 300));
    } else {
        setTimeout(injectSelector, 300);
    }

    const observer = new MutationObserver(() => {
        if (!document.getElementById('language-selector')) {
            injectSelector();
        }
    });

    if (document.body) {
        observer.observe(document.body, { childList: true, subtree: true });
    } else {
        document.addEventListener('DOMContentLoaded', () => {
            observer.observe(document.body, { childList: true, subtree: true });
        });
    }
})();
