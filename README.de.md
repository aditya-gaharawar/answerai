<h2>ANSWERAI</h2>

<p>ANSWERAI ist <a href="https://docs.answerai.in/"><strong>ein Zuhause für KI</strong></a>: eine erweiterbare, benutzerfreundliche Plattform zum Selbsthosten, die vollständig offline betrieben werden kann. Verbinde lokale Modelle über Ollama oder nutze OpenAI-kompatible APIs für lokale und cloudbasierte Modelle.</p>

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

[![ANSWERAI in Aktion](https://cdn.answerai.in/answerai-demo.gif)](https://docs.answerai.in/)

![GitHub stars](https://img.shields.io/github/stars/answerai/answerai?style=social)
![GitHub forks](https://img.shields.io/github/forks/answerai/answerai?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/answerai/answerai?style=social)
![GitHub repo size](https://img.shields.io/github/repo-size/answerai/answerai)
![GitHub language count](https://img.shields.io/github/languages/count/answerai/answerai)
![GitHub top language](https://img.shields.io/github/languages/top/answerai/answerai)
![GitHub last commit](https://img.shields.io/github/last-commit/answerai/answerai?color=red)
[![Discord](https://img.shields.io/badge/Discord-ANSWERAI-blue?logo=discord&logoColor=white)](https://discord.gg/5rJgQTnV4s)
[![](https://img.shields.io/static/v1?label=Sponsor&message=Support&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/answerai)

[ANSWERAI entdecken →](https://docs.answerai.in/)

### Installation

#### Python

Erfordert Python 3.12.

```bash
pip install answerai
answerai serve
```

Öffne anschließend [http://localhost:8080](http://localhost:8080).

#### Docker

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v answerai:/app/backend/data --name answerai --restart always ghcr.io/answerai/answerai:main
```

Öffne anschließend [http://localhost:3000](http://localhost:3000).

| Image-Tag | Inhalt                                                                                 |
| --------- | -------------------------------------------------------------------------------------- |
| `:main`   | Standard-Image mit Abhängigkeiten für lokale KI                                        |
| `:slim`   | Schlankes Image mit externen Diensten für Embeddings, Dokumentenextraktion und Sprache |
| `:cuda`   | ANSWERAI mit CUDA-Beschleunigung                                                       |
| `:ollama` | ANSWERAI mit integriertem Ollama                                                       |
| `:dev`    | Neuester Entwicklungsbuild                                                             |

Füge diese Optionen bei Bedarf vor dem Image-Namen zu `docker run` hinzu:

| Option                                               | Zweck                                                                                            |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `-e OLLAMA_BASE_URL=http://your-ollama-server:11434` | Verbindung zu Ollama auf einem anderen Server                                                    |
| `-e OPENAI_API_KEY=your_secret_key`                  | OpenAI-API-Schlüssel festlegen                                                                   |
| `-e HF_HUB_OFFLINE=1`                                | Downloads von Hugging-Face-Modellen für den Offlinebetrieb deaktivieren                          |
| `--gpus all`                                         | Nvidia-GPU-Zugriff für `:cuda` oder `:ollama` aktivieren; erfordert das Nvidia Container Toolkit |

Einrichtung und Konfigurationsoptionen findest du in der [Docker-Installationsanleitung](https://docs.answerai.in/getting-started/quick-start/).

#### Desktop-App

[Native Desktop-App herunterladen](https://github.com/answerai/desktop) für macOS, Windows und Linux.

[Dokumentation lesen →](https://docs.answerai.in/getting-started/)

### Ökosystem

- [Open Terminal](https://github.com/answerai/open-terminal) / [Terminals (Enterprise)](https://github.com/answerai/terminals): Die Ausführungsebene, die ANSWERAI zu einer vollständigen Agentenumgebung macht, mit Enterprise-Orchestrierung für Arbeitsbereiche pro Benutzer.
- [Knowledge Base Sync (oikb)](https://github.com/answerai/oikb): Ordner, Repositories, Buckets und Wikis durch inkrementelle Synchronisierung in ANSWERAI Knowledge Bases spiegeln.
- [ANSWERAI Computer](https://github.com/answerai/computer): Dein Computer in jedem Browser: Dateien, Editor, Terminal, Git und optionale KI-Agenten auf deinem eigenen Rechner.

Weitere Informationen findest du in der [Ökosystem-Dokumentation](https://docs.answerai.in/ecosystem/).

### Fehlerbehebung und Updates

Bei Verbindungsproblemen hilft die [Anleitung zur Fehlerbehebung](https://docs.answerai.in/troubleshooting/); zum Aktualisieren deiner Installation gibt es die [Update-Anleitung](https://docs.answerai.in/getting-started/updating).

### Dokumentation

Informationen zu Konfiguration und Nutzung findest du in der [Dokumentation](https://docs.answerai.in/), geplante Arbeiten in der [Roadmap](https://docs.answerai.in/roadmap/).

Für Docker Compose, Kubernetes und weitere Installationsarten siehe die [Installationsdokumentation](https://docs.answerai.in/getting-started/).

### Hilfe

[Erstelle ein Issue](https://github.com/answerai/answerai/issues) oder [starte eine Diskussion](https://github.com/answerai/answerai/discussions).

Du findest uns auf [Reddit](https://www.reddit.com/r/ANSWERAI/), [X](https://x.com/ANSWERAI) und [Discord](https://discord.gg/5rJgQTnV4s).

### Sicherheit

Melde Sicherheitslücken vertraulich über [GitHub Security Advisories](https://github.com/answerai/answerai/security). Sicherheitsmeldungen werden ausschließlich über GitHub angenommen.

### GitHub-Sterne im Zeitverlauf

<a href="https://star-history.com/#answerai/answerai&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
    <img alt="Diagramm der GitHub-Sterne" src="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
  </picture>
</a>

#### Lizenz

Enthält Code unter der ANSWERAI License, die den Erhalt des Open-WebUI-Brandings vorschreibt, sowie frühere Beiträge unter ihren ursprünglichen Lizenzen. Bedingungen und Lizenzhistorie stehen in [LICENSE](./LICENSE) und [LICENSE_HISTORY](./LICENSE_HISTORY).

[Enterprise](https://docs.answerai.in/enterprise) · [Karriere](https://careers.answerai.in/) · [Unterstützen](https://github.com/sponsors/answerai)

Erstellt von [Timothy Jaeryang Baek](https://github.com/tjbck).
