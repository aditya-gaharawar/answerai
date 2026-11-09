# Chat workspace review

Captured from the running local application using an isolated test database and a synthetic account.

- [Desktop](desktop.png) and [mobile](mobile.png): the new welcome, sidebar, and composer.
- [Desktop conversation](conversation-desktop.png) and [mobile conversation](conversation-mobile.png): a labelled interface fixture with Markdown, code, and a table, persisted through the real chat API. The fixture is removed after the browser test.
- [Mobile controls](mobile-menu.png): existing model, attachment, and execution controls remain in the plus menu.
- [Light theme](light-mobile.png): the stored light preference is preserved.

Browser verification used Chromium at 320–1440px. The premium UI suite checked 360, 768, 1024, and 1440px, including keyboard menus, workspace search, the mobile drawer, light/OLED selection, reduced motion, and loading/error states. Its automated axe checks reported no violations in the tested views; incomplete color-contrast checks still need manual review.

The compact-composer suite successfully submitted a real request to a deterministic local test provider and checked the nested controls and short viewport. The conversation rendering suite checked code/table rendering, horizontal overflow, and anchored input at 360, 768, and 1440px. These tests establish UI behavior; they do not evaluate model quality or external provider reliability.
