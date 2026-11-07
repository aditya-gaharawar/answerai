<h2>ANSWERAI</h2>

<p>ANSWERAI é <a href="https://docs.answerai.in/"><strong>um lar para a IA</strong></a>: uma plataforma auto-hospedada, extensível e fácil de usar, feita para funcionar totalmente offline. Conecte modelos locais pelo Ollama ou use APIs compatíveis com OpenAI para modelos locais e na nuvem.</p>

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

[![Demonstração do ANSWERAI](https://cdn.answerai.in/answerai-demo.gif)](https://docs.answerai.in/)

![GitHub stars](https://img.shields.io/github/stars/answerai/answerai?style=social)
![GitHub forks](https://img.shields.io/github/forks/answerai/answerai?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/answerai/answerai?style=social)
![GitHub repo size](https://img.shields.io/github/repo-size/answerai/answerai)
![GitHub language count](https://img.shields.io/github/languages/count/answerai/answerai)
![GitHub top language](https://img.shields.io/github/languages/top/answerai/answerai)
![GitHub last commit](https://img.shields.io/github/last-commit/answerai/answerai?color=red)
[![Discord](https://img.shields.io/badge/Discord-ANSWERAI-blue?logo=discord&logoColor=white)](https://discord.gg/5rJgQTnV4s)
[![](https://img.shields.io/static/v1?label=Sponsor&message=Support&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/answerai)

[Explore o ANSWERAI →](https://docs.answerai.in/)

### Instalação

#### Python

Requer Python 3.12.

```bash
pip install answerai
answerai serve
```

Depois, abra [http://localhost:8080](http://localhost:8080).

#### Docker

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v answerai:/app/backend/data --name answerai --restart always ghcr.io/answerai/answerai:main
```

Depois, abra [http://localhost:3000](http://localhost:3000).

| Tag da imagem | Conteúdo                                                                            |
| ------------- | ----------------------------------------------------------------------------------- |
| `:main`       | Imagem padrão com dependências de IA local                                          |
| `:slim`       | Imagem leve que usa serviços externos para embeddings, extração de documentos e voz |
| `:cuda`       | ANSWERAI com aceleração CUDA                                                        |
| `:ollama`     | ANSWERAI com Ollama incluído                                                        |
| `:dev`        | Build de desenvolvimento mais recente                                               |

Adicione estas opções ao `docker run` antes do nome da imagem, conforme necessário:

| Opção                                                | Finalidade                                                                                 |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `-e OLLAMA_BASE_URL=http://your-ollama-server:11434` | Conectar ao Ollama em outro servidor                                                       |
| `-e OPENAI_API_KEY=your_secret_key`                  | Definir sua chave de API da OpenAI                                                         |
| `-e HF_HUB_OFFLINE=1`                                | Desativar downloads de modelos do Hugging Face para uso offline                            |
| `--gpus all`                                         | Habilitar acesso à GPU Nvidia para `:cuda` ou `:ollama`; requer o Nvidia Container Toolkit |

Consulte o [guia de instalação com Docker](https://docs.answerai.in/getting-started/quick-start/) para instruções e opções de configuração.

#### Aplicativo para desktop

[Baixe o aplicativo nativo para desktop](https://github.com/answerai/desktop) para macOS, Windows e Linux.

[Leia a documentação →](https://docs.answerai.in/getting-started/)

### Ecossistema

- [Open Terminal](https://github.com/answerai/open-terminal) / [Terminals (Enterprise)](https://github.com/answerai/terminals): A camada de execução que transforma o ANSWERAI em um ambiente completo para agentes, com orquestração empresarial de espaços de trabalho por usuário.
- [Knowledge Base Sync (oikb)](https://github.com/answerai/oikb): Espelhe pastas, repositórios, buckets e wikis nas bases de conhecimento do ANSWERAI com sincronização incremental.
- [ANSWERAI Computer](https://github.com/answerai/computer): Seu computador em qualquer navegador: arquivos, editor, terminal, Git e agentes de IA opcionais, executados na sua própria máquina.

Consulte a [documentação do ecossistema](https://docs.answerai.in/ecosystem/) para mais detalhes.

### Solução de problemas e atualizações

Consulte o [guia de solução de problemas](https://docs.answerai.in/troubleshooting/) para problemas de conexão e o [guia de atualização](https://docs.answerai.in/getting-started/updating) para atualizar sua instalação.

### Documentação

Consulte a [documentação](https://docs.answerai.in/) para configuração e uso, e o [roteiro](https://docs.answerai.in/roadmap/) para o trabalho planejado.

Para Docker Compose, Kubernetes e outras formas de instalação, consulte a [documentação de instalação](https://docs.answerai.in/getting-started/).

### Suporte

[Abra uma issue](https://github.com/answerai/answerai/issues) ou [inicie uma discussão](https://github.com/answerai/answerai/discussions).

Encontre-nos no [Reddit](https://www.reddit.com/r/ANSWERAI/), [X](https://x.com/ANSWERAI) e [Discord](https://discord.gg/5rJgQTnV4s).

### Segurança

Relate vulnerabilidades de forma privada pelo [GitHub Security Advisories](https://github.com/answerai/answerai/security). Relatos de segurança são aceitos somente pelo GitHub.

### Histórico de estrelas

<a href="https://star-history.com/#answerai/answerai&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
    <img alt="Gráfico do histórico de estrelas" src="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
  </picture>
</a>

#### Licença

Inclui código sob a ANSWERAI License, que exige preservar a marca ANSWERAI, e contribuições anteriores sob suas licenças originais. Consulte [LICENSE](./LICENSE) e [LICENSE_HISTORY](./LICENSE_HISTORY) para os termos e o histórico.

[Empresas](https://docs.answerai.in/enterprise) · [Carreiras](https://careers.answerai.in/) · [Patrocine](https://github.com/sponsors/answerai)

Criado por [Timothy Jaeryang Baek](https://github.com/tjbck).
