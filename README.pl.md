<h2>ANSWERAI</h2>

<p>ANSWERAI to <a href="https://docs.answerai.in/"><strong>dom dla AI</strong></a>: rozszerzalna, łatwa w obsłudze platforma do samodzielnego hostowania, zaprojektowana do pracy całkowicie offline. Podłącz lokalne modele przez Ollama lub korzystaj z API zgodnych z OpenAI dla modeli lokalnych i chmurowych.</p>

[English](README.md) |
[简体中文](README.zh.md) |
[繁體中文](README.zht.md) |
[한국어](README.ko.md) |
[Deutsch](README.de.md) |
[Español](README.es.md) |
[Français](README.fr.md) |
[Italiano](README.it.md) |
[Dansk](README.da.md) |
[日本語](README.ja.md) |
[Polski](README.pl.md) |
[Русский](README.ru.md) |
[Bosanski](README.bs.md) |
[العربية](README.ar.md) |
[Norsk](README.no.md) |
[Português (Brasil)](README.br.md) |
[ไทย](README.th.md) |
[Türkçe](README.tr.md) |
[Українська](README.uk.md) |
[বাংলা](README.bn.md) |
[Ελληνικά](README.gr.md) |
[Tiếng Việt](README.vi.md)

[![Prezentacja ANSWERAI](https://cdn.answerai.in/answerai-demo.gif)](https://docs.answerai.in/)

![GitHub stars](https://img.shields.io/github/stars/answerai/answerai?style=social)
![GitHub forks](https://img.shields.io/github/forks/answerai/answerai?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/answerai/answerai?style=social)
![GitHub repo size](https://img.shields.io/github/repo-size/answerai/answerai)
![GitHub language count](https://img.shields.io/github/languages/count/answerai/answerai)
![GitHub top language](https://img.shields.io/github/languages/top/answerai/answerai)
![GitHub last commit](https://img.shields.io/github/last-commit/answerai/answerai?color=red)
[![Discord](https://img.shields.io/badge/Discord-ANSWERAI-blue?logo=discord&logoColor=white)](https://discord.gg/5rJgQTnV4s)
[![](https://img.shields.io/static/v1?label=Sponsor&message=Support&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/answerai)

[Poznaj ANSWERAI →](https://docs.answerai.in/)

### Instalacja

#### Python

Wymaga Pythona 3.12.

```bash
pip install answerai
answerai serve
```

Następnie otwórz [http://localhost:8080](http://localhost:8080).

#### Docker

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v answerai:/app/backend/data --name answerai --restart always ghcr.io/answerai/answerai:main
```

Następnie otwórz [http://localhost:3000](http://localhost:3000).

| Tag obrazu | Zawartość                                                                                       |
| ---------- | ----------------------------------------------------------------------------------------------- |
| `:main`    | Standardowy obraz z zależnościami dla lokalnej AI                                               |
| `:slim`    | Lekki obraz korzystający z usług zewnętrznych do osadzeń, ekstrakcji dokumentów i obsługi głosu |
| `:cuda`    | ANSWERAI z akceleracją CUDA                                                                     |
| `:ollama`  | ANSWERAI z dołączonym Ollama                                                                    |
| `:dev`     | Najnowsza kompilacja rozwojowa                                                                  |

W razie potrzeby dodaj te opcje do `docker run` przed nazwą obrazu:

| Opcja                                                | Zastosowanie                                                                               |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `-e OLLAMA_BASE_URL=http://your-ollama-server:11434` | Połączenie z Ollama na innym serwerze                                                      |
| `-e OPENAI_API_KEY=your_secret_key`                  | Ustawienie klucza API OpenAI                                                               |
| `-e HF_HUB_OFFLINE=1`                                | Wyłączenie pobierania modeli Hugging Face do pracy offline                                 |
| `--gpus all`                                         | Włączenie dostępu do GPU Nvidia dla `:cuda` lub `:ollama`; wymaga Nvidia Container Toolkit |

Instrukcje i opcje konfiguracji znajdziesz w [przewodniku instalacji przez Docker](https://docs.answerai.in/getting-started/quick-start/).

#### Aplikacja desktopowa

[Pobierz natywną aplikację desktopową](https://github.com/answerai/desktop) dla macOS, Windows i Linux.

[Przeczytaj dokumentację →](https://docs.answerai.in/getting-started/)

### Ekosystem

- [Open Terminal](https://github.com/answerai/open-terminal) / [Terminals (Enterprise)](https://github.com/answerai/terminals): Warstwa wykonawcza, która zmienia ANSWERAI w kompletne środowisko agentowe, z orkiestracją klasy enterprise dla osobnych przestrzeni roboczych użytkowników.
- [Knowledge Base Sync (oikb)](https://github.com/answerai/oikb): Synchronizuj przyrostowo foldery, repozytoria, zasobniki i wiki z bazami wiedzy ANSWERAI.
- [ANSWERAI Computer](https://github.com/answerai/computer): Twój komputer w dowolnej przeglądarce: pliki, edytor, terminal, Git i opcjonalni agenci AI, działający na twojej własnej maszynie.

Szczegóły znajdziesz w [dokumentacji ekosystemu](https://docs.answerai.in/ecosystem/).

### Rozwiązywanie problemów i aktualizacje

W razie problemów z połączeniem skorzystaj z [poradnika rozwiązywania problemów](https://docs.answerai.in/troubleshooting/), a aby zaktualizować instalację — z [poradnika aktualizacji](https://docs.answerai.in/getting-started/updating).

### Dokumentacja

Informacje o konfiguracji i użytkowaniu znajdziesz w [dokumentacji](https://docs.answerai.in/), a planowane prace w [planie rozwoju](https://docs.answerai.in/roadmap/).

Informacje o Docker Compose, Kubernetes i innych sposobach instalacji znajdziesz w [dokumentacji instalacji](https://docs.answerai.in/getting-started/).

### Pomoc

[Utwórz zgłoszenie](https://github.com/answerai/answerai/issues) lub [rozpocznij dyskusję](https://github.com/answerai/answerai/discussions).

Znajdziesz nas na [Reddicie](https://www.reddit.com/r/ANSWERAI/), [X](https://x.com/ANSWERAI) i [Discordzie](https://discord.gg/5rJgQTnV4s).

### Bezpieczeństwo

Zgłaszaj luki poufnie przez [GitHub Security Advisories](https://github.com/answerai/answerai/security). Zgłoszenia dotyczące bezpieczeństwa przyjmujemy wyłącznie przez GitHub.

### Historia gwiazdek

<a href="https://star-history.com/#answerai/answerai&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
    <img alt="Wykres historii gwiazdek" src="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
  </picture>
</a>

#### Licencja

Zawiera kod na licencji ANSWERAI License, która wymaga zachowania oznaczeń marki ANSWERAI, oraz wcześniejsze wkłady na ich oryginalnych licencjach. Warunki i historię znajdziesz w [LICENSE](./LICENSE) i [LICENSE_HISTORY](./LICENSE_HISTORY).

[Enterprise](https://docs.answerai.in/enterprise) · [Kariera](https://careers.answerai.in/) · [Wesprzyj](https://github.com/sponsors/answerai)

Autor: [Timothy Jaeryang Baek](https://github.com/tjbck).
