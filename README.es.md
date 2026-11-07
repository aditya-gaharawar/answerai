<h2>ANSWERAI</h2>

<p>ANSWERAI es <a href="https://docs.answerai.in/"><strong>un hogar para la IA</strong></a>: una plataforma autoalojada, extensible y fácil de usar, diseñada para funcionar completamente sin conexión. Conecta modelos locales mediante Ollama o usa API compatibles con OpenAI para modelos locales y en la nube.</p>

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

[![Demostración de ANSWERAI](https://cdn.answerai.in/answerai-demo.gif)](https://docs.answerai.in/)

![GitHub stars](https://img.shields.io/github/stars/answerai/answerai?style=social)
![GitHub forks](https://img.shields.io/github/forks/answerai/answerai?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/answerai/answerai?style=social)
![GitHub repo size](https://img.shields.io/github/repo-size/answerai/answerai)
![GitHub language count](https://img.shields.io/github/languages/count/answerai/answerai)
![GitHub top language](https://img.shields.io/github/languages/top/answerai/answerai)
![GitHub last commit](https://img.shields.io/github/last-commit/answerai/answerai?color=red)
[![Discord](https://img.shields.io/badge/Discord-ANSWERAI-blue?logo=discord&logoColor=white)](https://discord.gg/5rJgQTnV4s)
[![](https://img.shields.io/static/v1?label=Sponsor&message=Support&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/answerai)

[Explora ANSWERAI →](https://docs.answerai.in/)

### Instalación

#### Python

Requiere Python 3.12.

```bash
pip install answerai
answerai serve
```

Después, abre [http://localhost:8080](http://localhost:8080).

#### Docker

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v answerai:/app/backend/data --name answerai --restart always ghcr.io/answerai/answerai:main
```

Después, abre [http://localhost:3000](http://localhost:3000).

| Etiqueta de imagen | Contenido                                                                                |
| ------------------ | ---------------------------------------------------------------------------------------- |
| `:main`            | Imagen estándar con dependencias de IA local                                             |
| `:slim`            | Imagen ligera que usa servicios externos para embeddings, extracción de documentos y voz |
| `:cuda`            | ANSWERAI con aceleración CUDA                                                            |
| `:ollama`          | ANSWERAI con Ollama incluido                                                             |
| `:dev`             | Última compilación de desarrollo                                                         |

Añade estas opciones a `docker run` antes del nombre de la imagen según lo necesites:

| Opción                                               | Función                                                                                      |
| ---------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `-e OLLAMA_BASE_URL=http://your-ollama-server:11434` | Conectarse a Ollama en otro servidor                                                         |
| `-e OPENAI_API_KEY=your_secret_key`                  | Configurar tu clave de API de OpenAI                                                         |
| `-e HF_HUB_OFFLINE=1`                                | Desactivar las descargas de modelos de Hugging Face para el uso sin conexión                 |
| `--gpus all`                                         | Habilitar el acceso a GPU Nvidia para `:cuda` o `:ollama`; requiere Nvidia Container Toolkit |

Consulta la [guía de instalación con Docker](https://docs.answerai.in/getting-started/quick-start/) para ver las instrucciones y opciones de configuración.

#### Aplicación de escritorio

[Descarga la aplicación de escritorio nativa](https://github.com/answerai/desktop) para macOS, Windows y Linux.

[Lee la documentación →](https://docs.answerai.in/getting-started/)

### Ecosistema

- [Open Terminal](https://github.com/answerai/open-terminal) / [Terminals (Enterprise)](https://github.com/answerai/terminals): La capa de ejecución que convierte ANSWERAI en un entorno completo para agentes, con orquestación empresarial de espacios de trabajo por usuario.
- [Knowledge Base Sync (oikb)](https://github.com/answerai/oikb): Replica carpetas, repositorios, buckets y wikis en las bases de conocimiento de ANSWERAI mediante sincronización incremental.
- [ANSWERAI Computer](https://github.com/answerai/computer): Tu ordenador en cualquier navegador: archivos, editor, terminal, Git y agentes de IA opcionales, ejecutándose en tu propia máquina.

Consulta la [documentación del ecosistema](https://docs.answerai.in/ecosystem/) para más información.

### Resolución de problemas y actualizaciones

Consulta la [guía de resolución de problemas](https://docs.answerai.in/troubleshooting/) para los problemas de conexión y la [guía de actualización](https://docs.answerai.in/getting-started/updating) para actualizar tu instalación.

### Documentación

Consulta la [documentación](https://docs.answerai.in/) para la configuración y el uso, y la [hoja de ruta](https://docs.answerai.in/roadmap/) para el trabajo previsto.

Para Docker Compose, Kubernetes y otras instalaciones, consulta la [documentación de instalación](https://docs.answerai.in/getting-started/).

### Ayuda

[Abre una incidencia](https://github.com/answerai/answerai/issues) o [inicia una discusión](https://github.com/answerai/answerai/discussions).

Encuéntranos en [Reddit](https://www.reddit.com/r/ANSWERAI/), [X](https://x.com/ANSWERAI) y [Discord](https://discord.gg/5rJgQTnV4s).

### Seguridad

Comunica vulnerabilidades de forma privada mediante [GitHub Security Advisories](https://github.com/answerai/answerai/security). Solo se aceptan informes de seguridad a través de GitHub.

### Historial de estrellas

<a href="https://star-history.com/#answerai/answerai&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
    <img alt="Gráfico del historial de estrellas" src="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
  </picture>
</a>

#### Licencia

Incluye código bajo la ANSWERAI License, que exige conservar la marca ANSWERAI, y contribuciones anteriores bajo sus licencias originales. Consulta [LICENSE](./LICENSE) y [LICENSE_HISTORY](./LICENSE_HISTORY) para conocer las condiciones y el historial.

[Empresas](https://docs.answerai.in/enterprise) · [Empleo](https://careers.answerai.in/) · [Patrocinar](https://github.com/sponsors/answerai)

Creado por [Timothy Jaeryang Baek](https://github.com/tjbck).
