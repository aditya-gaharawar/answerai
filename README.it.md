<h2>ANSWERAI</h2>

<p>ANSWERAI è <a href="https://docs.answerai.in/"><strong>una casa per l’IA</strong></a>: una piattaforma self-hosted, estensibile e facile da usare, progettata per funzionare completamente offline. Collega modelli locali tramite Ollama oppure usa API compatibili con OpenAI per modelli locali e cloud.</p>

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

[![Demo di ANSWERAI](https://cdn.answerai.in/answerai-demo.gif)](https://docs.answerai.in/)

![GitHub stars](https://img.shields.io/github/stars/answerai/answerai?style=social)
![GitHub forks](https://img.shields.io/github/forks/answerai/answerai?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/answerai/answerai?style=social)
![GitHub repo size](https://img.shields.io/github/repo-size/answerai/answerai)
![GitHub language count](https://img.shields.io/github/languages/count/answerai/answerai)
![GitHub top language](https://img.shields.io/github/languages/top/answerai/answerai)
![GitHub last commit](https://img.shields.io/github/last-commit/answerai/answerai?color=red)
[![Discord](https://img.shields.io/badge/Discord-ANSWERAI-blue?logo=discord&logoColor=white)](https://discord.gg/5rJgQTnV4s)
[![](https://img.shields.io/static/v1?label=Sponsor&message=Support&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/answerai)

[Esplora ANSWERAI →](https://docs.answerai.in/)

### Installazione

#### Python

Richiede Python 3.12.

```bash
pip install answerai
answerai serve
```

Poi apri [http://localhost:8080](http://localhost:8080).

#### Docker

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v answerai:/app/backend/data --name answerai --restart always ghcr.io/answerai/answerai:main
```

Poi apri [http://localhost:3000](http://localhost:3000).

| Tag dell’immagine | Contenuto                                                                               |
| ----------------- | --------------------------------------------------------------------------------------- |
| `:main`           | Immagine standard con dipendenze per l’IA locale                                        |
| `:slim`           | Immagine leggera che usa servizi esterni per embedding, estrazione dei documenti e voce |
| `:cuda`           | ANSWERAI con accelerazione CUDA                                                         |
| `:ollama`         | ANSWERAI con Ollama incluso                                                             |
| `:dev`            | Ultima build di sviluppo                                                                |

Aggiungi queste opzioni a `docker run` prima del nome dell’immagine, secondo necessità:

| Opzione                                              | Scopo                                                                                          |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `-e OLLAMA_BASE_URL=http://your-ollama-server:11434` | Collegarsi a Ollama su un altro server                                                         |
| `-e OPENAI_API_KEY=your_secret_key`                  | Impostare la chiave API OpenAI                                                                 |
| `-e HF_HUB_OFFLINE=1`                                | Disabilitare i download dei modelli Hugging Face per l’uso offline                             |
| `--gpus all`                                         | Abilitare l’accesso alla GPU Nvidia per `:cuda` o `:ollama`; richiede Nvidia Container Toolkit |

Consulta la [guida all’installazione con Docker](https://docs.answerai.in/getting-started/quick-start/) per le istruzioni e le opzioni di configurazione.

#### App desktop

[Scarica l’app desktop nativa](https://github.com/answerai/desktop) per macOS, Windows e Linux.

[Leggi la documentazione →](https://docs.answerai.in/getting-started/)

### Ecosistema

- [Open Terminal](https://github.com/answerai/open-terminal) / [Terminals (Enterprise)](https://github.com/answerai/terminals): Il livello di esecuzione che rende ANSWERAI un ambiente completo per gli agenti, con orchestrazione enterprise degli spazi di lavoro per utente.
- [Knowledge Base Sync (oikb)](https://github.com/answerai/oikb): Replica cartelle, repository, bucket e wiki nelle basi di conoscenza di ANSWERAI tramite sincronizzazione incrementale.
- [ANSWERAI Computer](https://github.com/answerai/computer): Il tuo computer in qualsiasi browser: file, editor, terminale, Git e agenti IA facoltativi, in esecuzione sulla tua macchina.

Consulta la [documentazione dell’ecosistema](https://docs.answerai.in/ecosystem/) per i dettagli.

### Risoluzione dei problemi e aggiornamenti

Consulta la [guida alla risoluzione dei problemi](https://docs.answerai.in/troubleshooting/) per i problemi di connessione e la [guida agli aggiornamenti](https://docs.answerai.in/getting-started/updating) per aggiornare l’installazione.

### Documentazione

Consulta la [documentazione](https://docs.answerai.in/) per configurazione e utilizzo, e la [roadmap](https://docs.answerai.in/roadmap/) per il lavoro previsto.

Per Docker Compose, Kubernetes e altre installazioni, consulta la [documentazione di installazione](https://docs.answerai.in/getting-started/).

### Supporto

[Apri una segnalazione](https://github.com/answerai/answerai/issues) oppure [avvia una discussione](https://github.com/answerai/answerai/discussions).

Ci trovi su [Reddit](https://www.reddit.com/r/ANSWERAI/), [X](https://x.com/ANSWERAI) e [Discord](https://discord.gg/5rJgQTnV4s).

### Sicurezza

Segnala le vulnerabilità in privato tramite [GitHub Security Advisories](https://github.com/answerai/answerai/security). Le segnalazioni di sicurezza sono accettate solo tramite GitHub.

### Cronologia delle stelle

<a href="https://star-history.com/#answerai/answerai&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
    <img alt="Grafico della cronologia delle stelle" src="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
  </picture>
</a>

#### Licenza

Include codice soggetto alla ANSWERAI License, che richiede di mantenere il marchio ANSWERAI, e contributi precedenti soggetti alle rispettive licenze originali. Consulta [LICENSE](./LICENSE) e [LICENSE_HISTORY](./LICENSE_HISTORY) per condizioni e cronologia.

[Enterprise](https://docs.answerai.in/enterprise) · [Lavora con noi](https://careers.answerai.in/) · [Sostieni](https://github.com/sponsors/answerai)

Creato da [Timothy Jaeryang Baek](https://github.com/tjbck).
