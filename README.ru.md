<h2>ANSWERAI</h2>

<p>ANSWERAI — это <a href="https://docs.answerai.in/"><strong>дом для ИИ</strong></a>: расширяемая и удобная платформа для самостоятельного размещения, способная работать полностью офлайн. Подключайте локальные модели через Ollama или используйте совместимые с OpenAI API для локальных и облачных моделей.</p>

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

[![Демонстрация ANSWERAI](https://cdn.answerai.in/answerai-demo.gif)](https://docs.answerai.in/)

![GitHub stars](https://img.shields.io/github/stars/answerai/answerai?style=social)
![GitHub forks](https://img.shields.io/github/forks/answerai/answerai?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/answerai/answerai?style=social)
![GitHub repo size](https://img.shields.io/github/repo-size/answerai/answerai)
![GitHub language count](https://img.shields.io/github/languages/count/answerai/answerai)
![GitHub top language](https://img.shields.io/github/languages/top/answerai/answerai)
![GitHub last commit](https://img.shields.io/github/last-commit/answerai/answerai?color=red)
[![Discord](https://img.shields.io/badge/Discord-ANSWERAI-blue?logo=discord&logoColor=white)](https://discord.gg/5rJgQTnV4s)
[![](https://img.shields.io/static/v1?label=Sponsor&message=Support&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/answerai)

[Знакомство с ANSWERAI →](https://docs.answerai.in/)

### Установка

#### Python

Требуется Python 3.12.

```bash
pip install answerai
answerai serve
```

Затем откройте [http://localhost:8080](http://localhost:8080).

#### Docker

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v answerai:/app/backend/data --name answerai --restart always ghcr.io/answerai/answerai:main
```

Затем откройте [http://localhost:3000](http://localhost:3000).

| Тег образа | Содержимое                                                                                               |
| ---------- | -------------------------------------------------------------------------------------------------------- |
| `:main`    | Стандартный образ с зависимостями для локального ИИ                                                      |
| `:slim`    | Облегчённый образ с внешними сервисами для эмбеддингов, извлечения данных из документов и обработки речи |
| `:cuda`    | ANSWERAI с ускорением CUDA                                                                               |
| `:ollama`  | ANSWERAI со встроенным Ollama                                                                            |
| `:dev`     | Последняя сборка для разработки                                                                          |

При необходимости добавьте эти параметры в `docker run` перед именем образа:

| Параметр                                             | Назначение                                                                        |
| ---------------------------------------------------- | --------------------------------------------------------------------------------- |
| `-e OLLAMA_BASE_URL=http://your-ollama-server:11434` | Подключение к Ollama на другом сервере                                            |
| `-e OPENAI_API_KEY=your_secret_key`                  | Установка ключа API OpenAI                                                        |
| `-e HF_HUB_OFFLINE=1`                                | Отключение загрузки моделей Hugging Face для работы офлайн                        |
| `--gpus all`                                         | Доступ к GPU Nvidia для `:cuda` или `:ollama`; требуется Nvidia Container Toolkit |

Инструкции и параметры настройки приведены в [руководстве по установке через Docker](https://docs.answerai.in/getting-started/quick-start/).

#### Приложение для компьютера

[Скачайте нативное приложение](https://github.com/answerai/desktop) для macOS, Windows и Linux.

[Читать документацию →](https://docs.answerai.in/getting-started/)

### Экосистема

- [Open Terminal](https://github.com/answerai/open-terminal) / [Terminals (Enterprise)](https://github.com/answerai/terminals): Слой выполнения действий, который превращает ANSWERAI в полноценную среду для агентов, с корпоративной оркестрацией отдельных рабочих пространств пользователей.
- [Knowledge Base Sync (oikb)](https://github.com/answerai/oikb): Зеркалирование папок, репозиториев, бакетов и вики в базы знаний ANSWERAI с инкрементальной синхронизацией.
- [ANSWERAI Computer](https://github.com/answerai/computer): Ваш компьютер в любом браузере: файлы, редактор, терминал, Git и необязательные ИИ-агенты, работающие на вашей реальной машине.

Подробнее — в [документации экосистемы](https://docs.answerai.in/ecosystem/).

### Устранение неполадок и обновления

При проблемах с подключением обратитесь к [руководству по устранению неполадок](https://docs.answerai.in/troubleshooting/), а для обновления установки — к [руководству по обновлению](https://docs.answerai.in/getting-started/updating).

### Документация

Настройка и использование описаны в [документации](https://docs.answerai.in/), а запланированные работы — в [дорожной карте](https://docs.answerai.in/roadmap/).

Для Docker Compose, Kubernetes и других вариантов установки см. [документацию по установке](https://docs.answerai.in/getting-started/).

### Поддержка

[Создайте issue](https://github.com/answerai/answerai/issues) или [начните обсуждение](https://github.com/answerai/answerai/discussions).

Мы есть на [Reddit](https://www.reddit.com/r/ANSWERAI/), [X](https://x.com/ANSWERAI) и [Discord](https://discord.gg/5rJgQTnV4s).

### Безопасность

Сообщайте об уязвимостях конфиденциально через [GitHub Security Advisories](https://github.com/answerai/answerai/security). Сообщения о безопасности принимаются только через GitHub.

### История звёзд

<a href="https://star-history.com/#answerai/answerai&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
    <img alt="График истории звёзд" src="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
  </picture>
</a>

#### Лицензия

Включает код под ANSWERAI License, которая требует сохранения брендинга ANSWERAI, а также предыдущие вклады под их исходными лицензиями. Условия и история приведены в [LICENSE](./LICENSE) и [LICENSE_HISTORY](./LICENSE_HISTORY).

[Для организаций](https://docs.answerai.in/enterprise) · [Карьера](https://careers.answerai.in/) · [Поддержать проект](https://github.com/sponsors/answerai)

Автор: [Timothy Jaeryang Baek](https://github.com/tjbck).
