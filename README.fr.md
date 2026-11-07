<h2>ANSWERAI</h2>

<p>ANSWERAI est <a href="https://docs.answerai.in/"><strong>un foyer pour l’IA</strong></a> : une plateforme auto-hébergée, extensible et facile à utiliser, conçue pour fonctionner entièrement hors ligne. Connectez des modèles locaux via Ollama ou utilisez des API compatibles avec OpenAI pour des modèles locaux et cloud.</p>

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

[![Démonstration d’ANSWERAI](https://cdn.answerai.in/answerai-demo.gif)](https://docs.answerai.in/)

![GitHub stars](https://img.shields.io/github/stars/answerai/answerai?style=social)
![GitHub forks](https://img.shields.io/github/forks/answerai/answerai?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/answerai/answerai?style=social)
![GitHub repo size](https://img.shields.io/github/repo-size/answerai/answerai)
![GitHub language count](https://img.shields.io/github/languages/count/answerai/answerai)
![GitHub top language](https://img.shields.io/github/languages/top/answerai/answerai)
![GitHub last commit](https://img.shields.io/github/last-commit/answerai/answerai?color=red)
[![Discord](https://img.shields.io/badge/Discord-ANSWERAI-blue?logo=discord&logoColor=white)](https://discord.gg/5rJgQTnV4s)
[![](https://img.shields.io/static/v1?label=Sponsor&message=Support&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/answerai)

[Découvrir ANSWERAI →](https://docs.answerai.in/)

### Installation

#### Python

Nécessite Python 3.12.

```bash
pip install answerai
answerai serve
```

Ouvrez ensuite [http://localhost:8080](http://localhost:8080).

#### Docker

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v answerai:/app/backend/data --name answerai --restart always ghcr.io/answerai/answerai:main
```

Ouvrez ensuite [http://localhost:3000](http://localhost:3000).

| Tag de l’image | Contenu                                                                                                |
| -------------- | ------------------------------------------------------------------------------------------------------ |
| `:main`        | Image standard avec les dépendances d’IA locales                                                       |
| `:slim`        | Image légère utilisant des services externes pour les embeddings, l’extraction de documents et la voix |
| `:cuda`        | ANSWERAI avec accélération CUDA                                                                        |
| `:ollama`      | ANSWERAI avec Ollama intégré                                                                           |
| `:dev`         | Dernière version de développement                                                                      |

Ajoutez ces options à `docker run` avant le nom de l’image, selon vos besoins :

| Option                                               | Fonction                                                                                      |
| ---------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `-e OLLAMA_BASE_URL=http://your-ollama-server:11434` | Se connecter à Ollama sur un autre serveur                                                    |
| `-e OPENAI_API_KEY=your_secret_key`                  | Définir votre clé API OpenAI                                                                  |
| `-e HF_HUB_OFFLINE=1`                                | Désactiver le téléchargement des modèles Hugging Face pour une utilisation hors ligne         |
| `--gpus all`                                         | Activer l’accès aux GPU Nvidia pour `:cuda` ou `:ollama` ; nécessite Nvidia Container Toolkit |

Consultez le [guide d’installation Docker](https://docs.answerai.in/getting-started/quick-start/) pour les instructions et les options de configuration.

#### Application de bureau

[Téléchargez l’application de bureau native](https://github.com/answerai/desktop) pour macOS, Windows et Linux.

[Lire la documentation →](https://docs.answerai.in/getting-started/)

### Écosystème

- [Open Terminal](https://github.com/answerai/open-terminal) / [Terminals (Enterprise)](https://github.com/answerai/terminals): La couche d’exécution qui fait d’ANSWERAI un environnement complet pour les agents, avec une orchestration d’entreprise des espaces de travail individuels.
- [Knowledge Base Sync (oikb)](https://github.com/answerai/oikb): Répliquez dossiers, dépôts, buckets et wikis dans les bases de connaissances ANSWERAI grâce à la synchronisation incrémentale.
- [ANSWERAI Computer](https://github.com/answerai/computer): Votre ordinateur dans n’importe quel navigateur : fichiers, éditeur, terminal, Git et agents IA facultatifs, exécutés sur votre propre machine.

Consultez la [documentation de l’écosystème](https://docs.answerai.in/ecosystem/) pour en savoir plus.

### Dépannage et mises à jour

Consultez le [guide de dépannage](https://docs.answerai.in/troubleshooting/) pour les problèmes de connexion et le [guide de mise à jour](https://docs.answerai.in/getting-started/updating) pour actualiser votre installation.

### Documentation

Consultez la [documentation](https://docs.answerai.in/) pour la configuration et l’utilisation, et la [feuille de route](https://docs.answerai.in/roadmap/) pour les travaux prévus.

Pour Docker Compose, Kubernetes et les autres modes d’installation, consultez la [documentation d’installation](https://docs.answerai.in/getting-started/).

### Assistance

[Ouvrez une issue](https://github.com/answerai/answerai/issues) ou [lancez une discussion](https://github.com/answerai/answerai/discussions).

Retrouvez-nous sur [Reddit](https://www.reddit.com/r/ANSWERAI/), [X](https://x.com/ANSWERAI) et [Discord](https://discord.gg/5rJgQTnV4s).

### Sécurité

Signalez les vulnérabilités de manière confidentielle via [GitHub Security Advisories](https://github.com/answerai/answerai/security). Les signalements de sécurité sont acceptés uniquement sur GitHub.

### Historique des étoiles

<a href="https://star-history.com/#answerai/answerai&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
    <img alt="Graphique de l’historique des étoiles" src="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
  </picture>
</a>

#### Licence

Inclut du code sous ANSWERAI License, qui impose de conserver l’identité de marque ANSWERAI, ainsi que des contributions antérieures sous leurs licences d’origine. Consultez [LICENSE](./LICENSE) et [LICENSE_HISTORY](./LICENSE_HISTORY) pour les conditions et l’historique.

[Entreprise](https://docs.answerai.in/enterprise) · [Carrières](https://careers.answerai.in/) · [Soutenir](https://github.com/sponsors/answerai)

Créé par [Timothy Jaeryang Baek](https://github.com/tjbck).
