<h2>ANSWERAI</h2>

<p>Το ANSWERAI είναι <a href="https://docs.answerai.in/"><strong>ένα σπίτι για την τεχνητή νοημοσύνη</strong></a>: μια επεκτάσιμη, εύχρηστη πλατφόρμα που φιλοξενείτε εσείς, σχεδιασμένη να λειτουργεί πλήρως εκτός σύνδεσης. Συνδέστε τοπικά μοντέλα μέσω του Ollama ή χρησιμοποιήστε API συμβατά με το OpenAI για τοπικά μοντέλα και μοντέλα στο cloud.</p>

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

[![Επίδειξη του ANSWERAI](https://cdn.answerai.in/answerai-demo.gif)](https://docs.answerai.in/)

![GitHub stars](https://img.shields.io/github/stars/answerai/answerai?style=social)
![GitHub forks](https://img.shields.io/github/forks/answerai/answerai?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/answerai/answerai?style=social)
![GitHub repo size](https://img.shields.io/github/repo-size/answerai/answerai)
![GitHub language count](https://img.shields.io/github/languages/count/answerai/answerai)
![GitHub top language](https://img.shields.io/github/languages/top/answerai/answerai)
![GitHub last commit](https://img.shields.io/github/last-commit/answerai/answerai?color=red)
[![Discord](https://img.shields.io/badge/Discord-ANSWERAI-blue?logo=discord&logoColor=white)](https://discord.gg/5rJgQTnV4s)
[![](https://img.shields.io/static/v1?label=Sponsor&message=Support&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/answerai)

[Εξερευνήστε το ANSWERAI →](https://docs.answerai.in/)

### Εγκατάσταση

#### Python

Απαιτείται Python 3.12.

```bash
pip install answerai
answerai serve
```

Στη συνέχεια, ανοίξτε το [http://localhost:8080](http://localhost:8080).

#### Docker

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v answerai:/app/backend/data --name answerai --restart always ghcr.io/answerai/answerai:main
```

Στη συνέχεια, ανοίξτε το [http://localhost:3000](http://localhost:3000).

| Ετικέτα εικόνας | Περιεχόμενο                                                                                                 |
| --------------- | ----------------------------------------------------------------------------------------------------------- |
| `:main`         | Τυπική εικόνα με εξαρτήσεις για τοπική AI                                                                   |
| `:slim`         | Ελαφριά εικόνα που χρησιμοποιεί εξωτερικές υπηρεσίες για embeddings, εξαγωγή περιεχομένου εγγράφων και φωνή |
| `:cuda`         | ANSWERAI με επιτάχυνση CUDA                                                                                 |
| `:ollama`       | ANSWERAI με ενσωματωμένο Ollama                                                                             |
| `:dev`          | Νεότερη έκδοση ανάπτυξης                                                                                    |

Προσθέστε αυτές τις επιλογές στο `docker run` πριν από το όνομα της εικόνας, ανάλογα με τις ανάγκες σας:

| Επιλογή                                              | Σκοπός                                                                                            |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `-e OLLAMA_BASE_URL=http://your-ollama-server:11434` | Σύνδεση με Ollama σε άλλον διακομιστή                                                             |
| `-e OPENAI_API_KEY=your_secret_key`                  | Ορισμός του κλειδιού API OpenAI                                                                   |
| `-e HF_HUB_OFFLINE=1`                                | Απενεργοποίηση λήψεων μοντέλων Hugging Face για χρήση εκτός σύνδεσης                              |
| `--gpus all`                                         | Ενεργοποίηση πρόσβασης σε GPU Nvidia για `:cuda` ή `:ollama`· απαιτείται Nvidia Container Toolkit |

Δείτε τον [οδηγό εγκατάστασης με Docker](https://docs.answerai.in/getting-started/quick-start/) για οδηγίες και επιλογές διαμόρφωσης.

#### Εφαρμογή υπολογιστή

[Κατεβάστε την εγγενή εφαρμογή υπολογιστή](https://github.com/answerai/desktop) για macOS, Windows και Linux.

[Διαβάστε την τεκμηρίωση →](https://docs.answerai.in/getting-started/)

### Οικοσύστημα

- [Open Terminal](https://github.com/answerai/open-terminal) / [Terminals (Enterprise)](https://github.com/answerai/terminals): Το επίπεδο εκτέλεσης που μετατρέπει το ANSWERAI σε πλήρες περιβάλλον πρακτόρων, με εταιρική ενορχήστρωση χώρων εργασίας ανά χρήστη.
- [Knowledge Base Sync (oikb)](https://github.com/answerai/oikb): Αντικατοπτρίστε φακέλους, αποθετήρια, buckets και wiki στις βάσεις γνώσεων του ANSWERAI με αυξητικό συγχρονισμό.
- [ANSWERAI Computer](https://github.com/answerai/computer): Ο υπολογιστής σας σε οποιονδήποτε περιηγητή: αρχεία, επεξεργαστής, τερματικό, Git και προαιρετικοί πράκτορες AI, που εκτελούνται στο πραγματικό σας μηχάνημα.

Δείτε την [τεκμηρίωση του οικοσυστήματος](https://docs.answerai.in/ecosystem/) για λεπτομέρειες.

### Αντιμετώπιση προβλημάτων και ενημερώσεις

Δείτε τον [οδηγό αντιμετώπισης προβλημάτων](https://docs.answerai.in/troubleshooting/) για προβλήματα σύνδεσης και τον [οδηγό ενημέρωσης](https://docs.answerai.in/getting-started/updating) για να ενημερώσετε την εγκατάστασή σας.

### Τεκμηρίωση

Δείτε την [τεκμηρίωση](https://docs.answerai.in/) για τη διαμόρφωση και τη χρήση, και τον [οδικό χάρτη](https://docs.answerai.in/roadmap/) για τις προγραμματισμένες εργασίες.

Για Docker Compose, Kubernetes και άλλες εγκαταστάσεις, δείτε την [τεκμηρίωση εγκατάστασης](https://docs.answerai.in/getting-started/).

### Υποστήριξη

[Ανοίξτε ένα issue](https://github.com/answerai/answerai/issues) ή [ξεκινήστε μια συζήτηση](https://github.com/answerai/answerai/discussions).

Βρείτε μας στο [Reddit](https://www.reddit.com/r/ANSWERAI/), στο [X](https://x.com/ANSWERAI) και στο [Discord](https://discord.gg/5rJgQTnV4s).

### Ασφάλεια

Αναφέρετε ευπάθειες ιδιωτικά μέσω των [GitHub Security Advisories](https://github.com/answerai/answerai/security). Οι αναφορές ασφάλειας γίνονται δεκτές μόνο μέσω του GitHub.

### Ιστορικό αστεριών

<a href="https://star-history.com/#answerai/answerai&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
    <img alt="Γράφημα ιστορικού αστεριών" src="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
  </picture>
</a>

#### Άδεια χρήσης

Περιλαμβάνει κώδικα υπό την ANSWERAI License, η οποία απαιτεί τη διατήρηση της ταυτότητας του ANSWERAI, καθώς και παλαιότερες συνεισφορές υπό τις αρχικές τους άδειες. Δείτε τα [LICENSE](./LICENSE) και [LICENSE_HISTORY](./LICENSE_HISTORY) για τους όρους και το ιστορικό.

[Επιχειρήσεις](https://docs.answerai.in/enterprise) · [Καριέρα](https://careers.answerai.in/) · [Χορηγία](https://github.com/sponsors/answerai)

Δημιουργήθηκε από τον [Timothy Jaeryang Baek](https://github.com/tjbck).
