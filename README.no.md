<h2>ANSWERAI</h2>

<p>ANSWERAI er <a href="https://docs.answerai.in/"><strong>et hjem for KI</strong></a>: en utvidbar og brukervennlig plattform du drifter selv, bygget for å kjøre helt uten nettilgang. Koble til lokale modeller via Ollama, eller bruk OpenAI-kompatible API-er for lokale og skybaserte modeller.</p>

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

[![Demonstrasjon av ANSWERAI](https://cdn.answerai.in/answerai-demo.gif)](https://docs.answerai.in/)

![GitHub stars](https://img.shields.io/github/stars/answerai/answerai?style=social)
![GitHub forks](https://img.shields.io/github/forks/answerai/answerai?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/answerai/answerai?style=social)
![GitHub repo size](https://img.shields.io/github/repo-size/answerai/answerai)
![GitHub language count](https://img.shields.io/github/languages/count/answerai/answerai)
![GitHub top language](https://img.shields.io/github/languages/top/answerai/answerai)
![GitHub last commit](https://img.shields.io/github/last-commit/answerai/answerai?color=red)
[![Discord](https://img.shields.io/badge/Discord-ANSWERAI-blue?logo=discord&logoColor=white)](https://discord.gg/5rJgQTnV4s)
[![](https://img.shields.io/static/v1?label=Sponsor&message=Support&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/answerai)

[Utforsk ANSWERAI →](https://docs.answerai.in/)

### Installasjon

#### Python

Krever Python 3.12.

```bash
pip install answerai
answerai serve
```

Åpne deretter [http://localhost:8080](http://localhost:8080).

#### Docker

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v answerai:/app/backend/data --name answerai --restart always ghcr.io/answerai/answerai:main
```

Åpne deretter [http://localhost:3000](http://localhost:3000).

| Image-tagg | Innhold                                                                       |
| ---------- | ----------------------------------------------------------------------------- |
| `:main`    | Standardimage med avhengigheter for lokal KI                                  |
| `:slim`    | Lettvektsimage med eksterne tjenester for embeddings, dokumentuttrekk og tale |
| `:cuda`    | ANSWERAI med CUDA-akselerasjon                                                |
| `:ollama`  | ANSWERAI med Ollama inkludert                                                 |
| `:dev`     | Nyeste utviklingsbygg                                                         |

Legg til disse valgene i `docker run` før image-navnet etter behov:

| Valg                                                 | Formål                                                                                      |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `-e OLLAMA_BASE_URL=http://your-ollama-server:11434` | Koble til Ollama på en annen server                                                         |
| `-e OPENAI_API_KEY=your_secret_key`                  | Angi OpenAI-API-nøkkelen din                                                                |
| `-e HF_HUB_OFFLINE=1`                                | Deaktiver nedlasting av Hugging Face-modeller for bruk uten nettilgang                      |
| `--gpus all`                                         | Aktiver tilgang til Nvidia-GPU for `:cuda` eller `:ollama`; krever Nvidia Container Toolkit |

Se [installasjonsveiledningen for Docker](https://docs.answerai.in/getting-started/quick-start/) for oppsett og konfigurasjonsvalg.

#### Skrivebordsapp

[Last ned den native skrivebordsappen](https://github.com/answerai/desktop) for macOS, Windows og Linux.

[Les dokumentasjonen →](https://docs.answerai.in/getting-started/)

### Økosystem

- [Open Terminal](https://github.com/answerai/open-terminal) / [Terminals (Enterprise)](https://github.com/answerai/terminals): Utførelseslaget som gjør ANSWERAI til et komplett agentmiljø, med enterprise-orkestrering av egne arbeidsområder for hver bruker.
- [Knowledge Base Sync (oikb)](https://github.com/answerai/oikb): Speil mapper, kodearkiver, bøtter og wikier til ANSWERAI Knowledge Bases med inkrementell synkronisering.
- [ANSWERAI Computer](https://github.com/answerai/computer): Datamaskinen din i enhver nettleser: filer, editor, terminal, Git og valgfrie KI-agenter, som kjører på din egen maskin.

Se [økosystemets dokumentasjon](https://docs.answerai.in/ecosystem/) for detaljer.

### Feilsøking og oppdateringer

Se [feilsøkingsveiledningen](https://docs.answerai.in/troubleshooting/) ved tilkoblingsproblemer og [oppdateringsveiledningen](https://docs.answerai.in/getting-started/updating) for å oppdatere installasjonen.

### Dokumentasjon

Se [dokumentasjonen](https://docs.answerai.in/) for konfigurasjon og bruk, og [veikartet](https://docs.answerai.in/roadmap/) for planlagt arbeid.

For Docker Compose, Kubernetes og andre oppsett, se [installasjonsdokumentasjonen](https://docs.answerai.in/getting-started/).

### Hjelp

[Opprett en sak](https://github.com/answerai/answerai/issues) eller [start en diskusjon](https://github.com/answerai/answerai/discussions).

Du finner oss på [Reddit](https://www.reddit.com/r/ANSWERAI/), [X](https://x.com/ANSWERAI) og [Discord](https://discord.gg/5rJgQTnV4s).

### Sikkerhet

Rapporter sårbarheter privat via [GitHub Security Advisories](https://github.com/answerai/answerai/security). Sikkerhetsrapporter mottas kun via GitHub.

### Stjernehistorikk

<a href="https://star-history.com/#answerai/answerai&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
    <img alt="Diagram over stjernehistorikk" src="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
  </picture>
</a>

#### Lisens

Inneholder kode under ANSWERAI License, som krever at ANSWERAI-merkevaren beholdes, samt tidligere bidrag under sine opprinnelige lisenser. Se [LICENSE](./LICENSE) og [LICENSE_HISTORY](./LICENSE_HISTORY) for vilkår og historikk.

[Enterprise](https://docs.answerai.in/enterprise) · [Karriere](https://careers.answerai.in/) · [Støtt prosjektet](https://github.com/sponsors/answerai)

Laget av [Timothy Jaeryang Baek](https://github.com/tjbck).
