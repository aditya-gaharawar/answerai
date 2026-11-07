<h2>ANSWERAI</h2>

<p>ANSWERAI — це <a href="https://docs.answerai.in/"><strong>дім для ШІ</strong></a>: розширювана й зручна платформа для самостійного розгортання, здатна працювати повністю офлайн. Підключайте локальні моделі через Ollama або використовуйте сумісні з OpenAI API для локальних і хмарних моделей.</p>

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

[![Демонстрація ANSWERAI](https://cdn.answerai.in/answerai-demo.gif)](https://docs.answerai.in/)

![GitHub stars](https://img.shields.io/github/stars/answerai/answerai?style=social)
![GitHub forks](https://img.shields.io/github/forks/answerai/answerai?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/answerai/answerai?style=social)
![GitHub repo size](https://img.shields.io/github/repo-size/answerai/answerai)
![GitHub language count](https://img.shields.io/github/languages/count/answerai/answerai)
![GitHub top language](https://img.shields.io/github/languages/top/answerai/answerai)
![GitHub last commit](https://img.shields.io/github/last-commit/answerai/answerai?color=red)
[![Discord](https://img.shields.io/badge/Discord-ANSWERAI-blue?logo=discord&logoColor=white)](https://discord.gg/5rJgQTnV4s)
[![](https://img.shields.io/static/v1?label=Sponsor&message=Support&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/answerai)

[Дізнатися про ANSWERAI →](https://docs.answerai.in/)

### Встановлення

#### Python

Потрібен Python 3.12.

```bash
pip install answerai
answerai serve
```

Потім відкрийте [http://localhost:8080](http://localhost:8080).

#### Docker

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v answerai:/app/backend/data --name answerai --restart always ghcr.io/answerai/answerai:main
```

Потім відкрийте [http://localhost:3000](http://localhost:3000).

| Тег образу | Вміст                                                                                                       |
| ---------- | ----------------------------------------------------------------------------------------------------------- |
| `:main`    | Стандартний образ із залежностями для локального ШІ                                                         |
| `:slim`    | Полегшений образ із зовнішніми сервісами для ембедингів, видобування даних із документів і обробки мовлення |
| `:cuda`    | ANSWERAI з прискоренням CUDA                                                                                |
| `:ollama`  | ANSWERAI із вбудованим Ollama                                                                               |
| `:dev`     | Найновіша збірка для розробки                                                                               |

За потреби додайте ці параметри до `docker run` перед назвою образу:

| Параметр                                             | Призначення                                                                       |
| ---------------------------------------------------- | --------------------------------------------------------------------------------- |
| `-e OLLAMA_BASE_URL=http://your-ollama-server:11434` | Підключення до Ollama на іншому сервері                                           |
| `-e OPENAI_API_KEY=your_secret_key`                  | Встановлення ключа API OpenAI                                                     |
| `-e HF_HUB_OFFLINE=1`                                | Вимкнення завантаження моделей Hugging Face для роботи офлайн                     |
| `--gpus all`                                         | Доступ до GPU Nvidia для `:cuda` або `:ollama`; потрібен Nvidia Container Toolkit |

Інструкції та параметри налаштування наведено в [посібнику зі встановлення через Docker](https://docs.answerai.in/getting-started/quick-start/).

#### Настільний застосунок

[Завантажте нативний настільний застосунок](https://github.com/answerai/desktop) для macOS, Windows і Linux.

[Читати документацію →](https://docs.answerai.in/getting-started/)

### Екосистема

- [Open Terminal](https://github.com/answerai/open-terminal) / [Terminals (Enterprise)](https://github.com/answerai/terminals): Шар виконання дій, який перетворює ANSWERAI на повноцінне середовище для агентів, із корпоративною оркестрацією окремих робочих просторів користувачів.
- [Knowledge Base Sync (oikb)](https://github.com/answerai/oikb): Дзеркальне копіювання папок, репозиторіїв, бакетів і вікі до баз знань ANSWERAI з інкрементальною синхронізацією.
- [ANSWERAI Computer](https://github.com/answerai/computer): Ваш комп’ютер у будь-якому браузері: файли, редактор, термінал, Git і необов’язкові ШІ-агенти, що працюють на вашій реальній машині.

Докладніше — у [документації екосистеми](https://docs.answerai.in/ecosystem/).

### Усунення несправностей та оновлення

У разі проблем із підключенням дивіться [посібник з усунення несправностей](https://docs.answerai.in/troubleshooting/), а для оновлення інсталяції — [посібник з оновлення](https://docs.answerai.in/getting-started/updating).

### Документація

Налаштування й використання описано в [документації](https://docs.answerai.in/), а заплановані роботи — у [дорожній карті](https://docs.answerai.in/roadmap/).

Для Docker Compose, Kubernetes та інших способів встановлення дивіться [документацію зі встановлення](https://docs.answerai.in/getting-started/).

### Підтримка

[Створіть issue](https://github.com/answerai/answerai/issues) або [розпочніть обговорення](https://github.com/answerai/answerai/discussions).

Знайдіть нас на [Reddit](https://www.reddit.com/r/ANSWERAI/), [X](https://x.com/ANSWERAI) і [Discord](https://discord.gg/5rJgQTnV4s).

### Безпека

Повідомляйте про вразливості конфіденційно через [GitHub Security Advisories](https://github.com/answerai/answerai/security). Повідомлення про безпеку приймаються лише через GitHub.

### Історія зірок

<a href="https://star-history.com/#answerai/answerai&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
    <img alt="Графік історії зірок" src="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
  </picture>
</a>

#### Ліцензія

Містить код під ANSWERAI License, яка вимагає збереження брендингу ANSWERAI, а також попередні внески під їхніми початковими ліцензіями. Умови й історію наведено в [LICENSE](./LICENSE) та [LICENSE_HISTORY](./LICENSE_HISTORY).

[Для організацій](https://docs.answerai.in/enterprise) · [Кар’єра](https://careers.answerai.in/) · [Підтримати проєкт](https://github.com/sponsors/answerai)

Автор: [Timothy Jaeryang Baek](https://github.com/tjbck).
