<h2>ANSWERAI</h2>

<p>ANSWERAI je <a href="https://docs.answerai.in/"><strong>dom za AI</strong></a>: proširiva platforma jednostavna za korištenje, koju sami hostujete i koja može raditi potpuno offline. Povežite lokalne modele putem Ollame ili koristite API-je kompatibilne s OpenAI-jem za lokalne modele i modele u oblaku.</p>

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

[![Demonstracija ANSWERAI-ja](https://cdn.answerai.in/answerai-demo.gif)](https://docs.answerai.in/)

![GitHub stars](https://img.shields.io/github/stars/answerai/answerai?style=social)
![GitHub forks](https://img.shields.io/github/forks/answerai/answerai?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/answerai/answerai?style=social)
![GitHub repo size](https://img.shields.io/github/repo-size/answerai/answerai)
![GitHub language count](https://img.shields.io/github/languages/count/answerai/answerai)
![GitHub top language](https://img.shields.io/github/languages/top/answerai/answerai)
![GitHub last commit](https://img.shields.io/github/last-commit/answerai/answerai?color=red)
[![Discord](https://img.shields.io/badge/Discord-ANSWERAI-blue?logo=discord&logoColor=white)](https://discord.gg/5rJgQTnV4s)
[![](https://img.shields.io/static/v1?label=Sponsor&message=Support&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/answerai)

[Istražite ANSWERAI →](https://docs.answerai.in/)

### Instalacija

#### Python

Potreban je Python 3.12.

```bash
pip install answerai
answerai serve
```

Zatim otvorite [http://localhost:8080](http://localhost:8080).

#### Docker

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v answerai:/app/backend/data --name answerai --restart always ghcr.io/answerai/answerai:main
```

Zatim otvorite [http://localhost:3000](http://localhost:3000).

| Oznaka slike | Sadržaj                                                                                         |
| ------------ | ----------------------------------------------------------------------------------------------- |
| `:main`      | Standardna slika sa zavisnostima za lokalni AI                                                  |
| `:slim`      | Lagana slika koja koristi vanjske servise za embeddinge, izdvajanje sadržaja dokumenata i govor |
| `:cuda`      | ANSWERAI s CUDA ubrzanjem                                                                       |
| `:ollama`    | ANSWERAI s uključenom Ollamom                                                                   |
| `:dev`       | Najnovija razvojna verzija                                                                      |

Po potrebi dodajte ove opcije u `docker run` prije naziva slike:

| Opcija                                               | Namjena                                                                                           |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `-e OLLAMA_BASE_URL=http://your-ollama-server:11434` | Povezivanje s Ollamom na drugom serveru                                                           |
| `-e OPENAI_API_KEY=your_secret_key`                  | Postavljanje OpenAI API ključa                                                                    |
| `-e HF_HUB_OFFLINE=1`                                | Isključivanje preuzimanja Hugging Face modela za rad offline                                      |
| `--gpus all`                                         | Omogućavanje pristupa Nvidia GPU-u za `:cuda` ili `:ollama`; potreban je Nvidia Container Toolkit |

Upute i opcije konfiguracije nalaze se u [vodiču za instalaciju putem Dockera](https://docs.answerai.in/getting-started/quick-start/).

#### Desktop aplikacija

[Preuzmite nativnu desktop aplikaciju](https://github.com/answerai/desktop) za macOS, Windows i Linux.

[Pročitajte dokumentaciju →](https://docs.answerai.in/getting-started/)

### Ekosistem

- [Open Terminal](https://github.com/answerai/open-terminal) / [Terminals (Enterprise)](https://github.com/answerai/terminals): Izvršni sloj koji pretvara ANSWERAI u potpuno okruženje za agente, s poslovnom orkestracijom zasebnih radnih prostora za svakog korisnika.
- [Knowledge Base Sync (oikb)](https://github.com/answerai/oikb): Preslikajte foldere, repozitorije, spremnike i wikije u baze znanja ANSWERAI-ja uz inkrementalnu sinhronizaciju.
- [ANSWERAI Computer](https://github.com/answerai/computer): Vaš računar u bilo kojem pregledniku: datoteke, uređivač, terminal, Git i opcionalni AI agenti koji rade na vašem stvarnom računaru.

Detalje potražite u [dokumentaciji ekosistema](https://docs.answerai.in/ecosystem/).

### Rješavanje problema i ažuriranja

Za probleme s povezivanjem pogledajte [vodič za rješavanje problema](https://docs.answerai.in/troubleshooting/), a za ažuriranje instalacije [vodič za ažuriranje](https://docs.answerai.in/getting-started/updating).

### Dokumentacija

Za konfiguraciju i korištenje pogledajte [dokumentaciju](https://docs.answerai.in/), a za planirani rad [plan razvoja](https://docs.answerai.in/roadmap/).

Za Docker Compose, Kubernetes i druge načine instalacije pogledajte [dokumentaciju za instalaciju](https://docs.answerai.in/getting-started/).

### Podrška

[Otvorite prijavu](https://github.com/answerai/answerai/issues) ili [pokrenite raspravu](https://github.com/answerai/answerai/discussions).

Pronađite nas na [Redditu](https://www.reddit.com/r/ANSWERAI/), [X-u](https://x.com/ANSWERAI) i [Discordu](https://discord.gg/5rJgQTnV4s).

### Sigurnost

Ranjivosti prijavite privatno putem [GitHub Security Advisories](https://github.com/answerai/answerai/security). Sigurnosne prijave prihvatamo isključivo putem GitHuba.

### Historija zvjezdica

<a href="https://star-history.com/#answerai/answerai&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
    <img alt="Grafikon historije zvjezdica" src="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
  </picture>
</a>

#### Licenca

Sadrži kod pod licencom ANSWERAI License, koja zahtijeva očuvanje brenda ANSWERAI, te ranije doprinose pod njihovim izvornim licencama. Uslove i historiju pogledajte u [LICENSE](./LICENSE) i [LICENSE_HISTORY](./LICENSE_HISTORY).

[Enterprise](https://docs.answerai.in/enterprise) · [Karijere](https://careers.answerai.in/) · [Sponzorišite](https://github.com/sponsors/answerai)

Autor: [Timothy Jaeryang Baek](https://github.com/tjbck).
