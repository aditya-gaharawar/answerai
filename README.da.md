<h2>ANSWERAI</h2>

<p>ANSWERAI er <a href="https://docs.answerai.in/"><strong>et hjem til AI</strong></a>: en udvidelig og brugervenlig platform, som du selv hoster, og som er bygget til at køre helt offline. Tilslut lokale modeller via Ollama, eller brug OpenAI-kompatible API’er til lokale modeller og cloudmodeller.</p>

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

[![ANSWERAI-demonstration](https://cdn.answerai.in/answerai-demo.gif)](https://docs.answerai.in/)

![GitHub stars](https://img.shields.io/github/stars/answerai/answerai?style=social)
![GitHub forks](https://img.shields.io/github/forks/answerai/answerai?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/answerai/answerai?style=social)
![GitHub repo size](https://img.shields.io/github/repo-size/answerai/answerai)
![GitHub language count](https://img.shields.io/github/languages/count/answerai/answerai)
![GitHub top language](https://img.shields.io/github/languages/top/answerai/answerai)
![GitHub last commit](https://img.shields.io/github/last-commit/answerai/answerai?color=red)
[![Discord](https://img.shields.io/badge/Discord-ANSWERAI-blue?logo=discord&logoColor=white)](https://discord.gg/5rJgQTnV4s)
[![](https://img.shields.io/static/v1?label=Sponsor&message=Support&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/answerai)

[Udforsk ANSWERAI →](https://docs.answerai.in/)

### Installation

#### Python

Kræver Python 3.12.

```bash
pip install answerai
answerai serve
```

Åbn derefter [http://localhost:8080](http://localhost:8080).

#### Docker

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v answerai:/app/backend/data --name answerai --restart always ghcr.io/answerai/answerai:main
```

Åbn derefter [http://localhost:3000](http://localhost:3000).

| Image-tag | Indhold                                                                     |
| --------- | --------------------------------------------------------------------------- |
| `:main`   | Standardimage med afhængigheder til lokal AI                                |
| `:slim`   | Letvægtsimage med eksterne tjenester til embeddings, dokumentudtræk og tale |
| `:cuda`   | ANSWERAI med CUDA-acceleration                                              |
| `:ollama` | ANSWERAI med Ollama inkluderet                                              |
| `:dev`    | Nyeste udviklingsbuild                                                      |

Tilføj disse indstillinger til `docker run` før image-navnet efter behov:

| Indstilling                                          | Formål                                                                                 |
| ---------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `-e OLLAMA_BASE_URL=http://your-ollama-server:11434` | Opret forbindelse til Ollama på en anden server                                        |
| `-e OPENAI_API_KEY=your_secret_key`                  | Angiv din OpenAI-API-nøgle                                                             |
| `-e HF_HUB_OFFLINE=1`                                | Deaktiver download af Hugging Face-modeller til offlinebrug                            |
| `--gpus all`                                         | Aktiver Nvidia-GPU-adgang for `:cuda` eller `:ollama`; kræver Nvidia Container Toolkit |

Se [installationsvejledningen til Docker](https://docs.answerai.in/getting-started/quick-start/) for opsætning og konfigurationsmuligheder.

#### Desktop-app

[Download den native desktop-app](https://github.com/answerai/desktop) til macOS, Windows og Linux.

[Læs dokumentationen →](https://docs.answerai.in/getting-started/)

### Økosystem

- [Open Terminal](https://github.com/answerai/open-terminal) / [Terminals (Enterprise)](https://github.com/answerai/terminals): Det eksekveringslag, der gør ANSWERAI til et komplet agentmiljø, med enterprise-orkestrering af individuelle arbejdsområder til hver bruger.
- [Knowledge Base Sync (oikb)](https://github.com/answerai/oikb): Spejl mapper, repositories, buckets og wikier i ANSWERAI Knowledge Bases med inkrementel synkronisering.
- [ANSWERAI Computer](https://github.com/answerai/computer): Din computer i enhver browser: filer, editor, terminal, Git og valgfrie AI-agenter, som kører på din egen maskine.

Se [dokumentationen til økosystemet](https://docs.answerai.in/ecosystem/) for flere oplysninger.

### Fejlfinding og opdateringer

Se [fejlfindingsvejledningen](https://docs.answerai.in/troubleshooting/) ved forbindelsesproblemer og [opdateringsvejledningen](https://docs.answerai.in/getting-started/updating) for at opdatere din installation.

### Dokumentation

Se [dokumentationen](https://docs.answerai.in/) for konfiguration og brug samt [køreplanen](https://docs.answerai.in/roadmap/) for planlagt arbejde.

For Docker Compose, Kubernetes og andre opsætninger, se [installationsdokumentationen](https://docs.answerai.in/getting-started/).

### Hjælp

[Opret et issue](https://github.com/answerai/answerai/issues), eller [start en diskussion](https://github.com/answerai/answerai/discussions).

Find os på [Reddit](https://www.reddit.com/r/ANSWERAI/), [X](https://x.com/ANSWERAI) og [Discord](https://discord.gg/5rJgQTnV4s).

### Sikkerhed

Indberet sårbarheder fortroligt via [GitHub Security Advisories](https://github.com/answerai/answerai/security). Sikkerhedsrapporter modtages kun via GitHub.

### Stjernehistorik

<a href="https://star-history.com/#answerai/answerai&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
    <img alt="Diagram over stjernehistorik" src="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
  </picture>
</a>

#### Licens

Indeholder kode under ANSWERAI License, som kræver, at ANSWERAI-brandingen bevares, samt tidligere bidrag under deres oprindelige licenser. Se [LICENSE](./LICENSE) og [LICENSE_HISTORY](./LICENSE_HISTORY) for vilkår og historik.

[Enterprise](https://docs.answerai.in/enterprise) · [Karriere](https://careers.answerai.in/) · [Støt projektet](https://github.com/sponsors/answerai)

Skabt af [Timothy Jaeryang Baek](https://github.com/tjbck).
