"""Minimal headless-browser fingerprint patches.

The standard headless-Chromium signals — ``navigator.webdriver`` truthy,
empty plugin list, missing ``window.chrome`` runtime, mismatched language
list — are checked by every modern bot detection vendor (Cloudflare
Turnstile, DataDome, PerimeterX, Akamai). This module ships a small set
of init scripts that patch those signals back to the values a real Chrome
session would expose.

The scripts are returned as JavaScript strings and applied via
``BrowserContext.add_init_script(...)`` on each context construction in
:class:`PlaywrightBrowserObservationAdapter`. They run before any page
script (``add_init_script`` injects on every navigation), so the patched
values are in place when bot-detection JS first reads them.

This is **minimal** stealth — covers the most commonly-checked surface
without pulling in a third-party stealth library. Production deployments
that need to defeat well-funded WAFs may layer additional patches on top
through the adapter's ``stealth_init_scripts`` constructor kwarg.
"""

from __future__ import annotations

# 1. navigator.webdriver. Real Chrome leaves this as ``undefined``;
#    Chromium under Playwright sets it ``true``.
_WEBDRIVER_PATCH = """
Object.defineProperty(navigator, 'webdriver', {
    configurable: true,
    get: () => undefined,
});
""".strip()

# 2. navigator.plugins. Real Chrome reports several built-in PDF / Chromium
#    plugins; headless Chrome reports an empty array.
_PLUGINS_PATCH = """
Object.defineProperty(navigator, 'plugins', {
    configurable: true,
    get: () => [
        {name: 'PDF Viewer'},
        {name: 'Chrome PDF Viewer'},
        {name: 'Chromium PDF Viewer'},
        {name: 'Microsoft Edge PDF Viewer'},
        {name: 'WebKit built-in PDF'},
    ],
});
""".strip()

# 3. navigator.languages. Headless leaves only ``['en-US']`` (length 1);
#    real browsers usually expose two-or-more entries.
_LANGUAGES_PATCH = """
Object.defineProperty(navigator, 'languages', {
    configurable: true,
    get: () => ['en-US', 'en'],
});
""".strip()

# 4. window.chrome.runtime. Bot detection scripts often check for the
#    object's existence to distinguish a Chrome browser from a headless
#    Chromium build.
_CHROME_RUNTIME_PATCH = """
if (!window.chrome) {
    Object.defineProperty(window, 'chrome', {
        configurable: true,
        value: {runtime: {}},
    });
} else if (!window.chrome.runtime) {
    window.chrome.runtime = {};
}
""".strip()

# 5. Permissions API consistency. Some detectors call
#    ``navigator.permissions.query({name: 'notifications'})`` and compare
#    the returned ``state`` against ``Notification.permission``. A genuine
#    browser keeps them in sync; headless Chromium does not.
_PERMISSIONS_PATCH = """
const originalQuery = navigator.permissions.query;
navigator.permissions.query = (parameters) => {
    if (parameters && parameters.name === 'notifications') {
        return Promise.resolve({state: Notification.permission});
    }
    return originalQuery.call(navigator.permissions, parameters);
};
""".strip()


DEFAULT_STEALTH_INIT_SCRIPTS: tuple[str, ...] = (
    _WEBDRIVER_PATCH,
    _PLUGINS_PATCH,
    _LANGUAGES_PATCH,
    _CHROME_RUNTIME_PATCH,
    _PERMISSIONS_PATCH,
)
