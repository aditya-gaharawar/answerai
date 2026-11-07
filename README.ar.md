<h2>ANSWERAI</h2>

<p>ANSWERAI هو <a href="https://docs.answerai.in/"><strong>بيت للذكاء الاصطناعي</strong></a>: منصة قابلة للتوسعة وسهلة الاستخدام تستضيفها بنفسك، ومصممة للعمل بالكامل دون اتصال بالإنترنت. اربط النماذج المحلية عبر Ollama أو استخدم واجهات API المتوافقة مع OpenAI للنماذج المحلية والسحابية.</p>

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

[![عرض توضيحي لـ ANSWERAI](https://cdn.answerai.in/answerai-demo.gif)](https://docs.answerai.in/)

![GitHub stars](https://img.shields.io/github/stars/answerai/answerai?style=social)
![GitHub forks](https://img.shields.io/github/forks/answerai/answerai?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/answerai/answerai?style=social)
![GitHub repo size](https://img.shields.io/github/repo-size/answerai/answerai)
![GitHub language count](https://img.shields.io/github/languages/count/answerai/answerai)
![GitHub top language](https://img.shields.io/github/languages/top/answerai/answerai)
![GitHub last commit](https://img.shields.io/github/last-commit/answerai/answerai?color=red)
[![Discord](https://img.shields.io/badge/Discord-ANSWERAI-blue?logo=discord&logoColor=white)](https://discord.gg/5rJgQTnV4s)
[![](https://img.shields.io/static/v1?label=Sponsor&message=Support&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/answerai)

[استكشف ANSWERAI →](https://docs.answerai.in/)

### التثبيت

#### Python

يتطلب Python 3.12.

```bash
pip install answerai
answerai serve
```

ثم افتح [http://localhost:8080](http://localhost:8080).

#### Docker

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v answerai:/app/backend/data --name answerai --restart always ghcr.io/answerai/answerai:main
```

ثم افتح [http://localhost:3000](http://localhost:3000).

| وسم الصورة | المحتوى                                                                  |
| ---------- | ------------------------------------------------------------------------ |
| `:main`    | صورة قياسية تتضمن اعتماديات الذكاء الاصطناعي المحلي                      |
| `:slim`    | صورة خفيفة تستخدم خدمات خارجية للتضمينات واستخراج محتوى المستندات والصوت |
| `:cuda`    | ANSWERAI مع تسريع CUDA                                                   |
| `:ollama`  | ANSWERAI مرفقًا معه Ollama                                               |
| `:dev`     | أحدث نسخة تطوير                                                          |

أضف هذه الخيارات إلى `docker run` قبل اسم الصورة حسب الحاجة:

| الخيار                                               | الغرض                                                                                                 |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `-e OLLAMA_BASE_URL=http://your-ollama-server:11434` | الاتصال بـ Ollama على خادم آخر                                                                        |
| `-e OPENAI_API_KEY=your_secret_key`                  | تعيين مفتاح API الخاص بك لدى OpenAI                                                                   |
| `-e HF_HUB_OFFLINE=1`                                | تعطيل تنزيل نماذج Hugging Face للاستخدام دون اتصال                                                    |
| `--gpus all`                                         | تمكين الوصول إلى وحدة معالجة الرسوميات Nvidia مع `:cuda` أو `:ollama`؛ يتطلب Nvidia Container Toolkit |

راجع [دليل التثبيت باستخدام Docker](https://docs.answerai.in/getting-started/quick-start/) للاطلاع على خطوات الإعداد وخيارات الضبط.

#### تطبيق سطح المكتب

[نزّل تطبيق سطح المكتب الأصلي](https://github.com/answerai/desktop) لأنظمة macOS وWindows وLinux.

[اقرأ الوثائق →](https://docs.answerai.in/getting-started/)

### المنظومة

- [Open Terminal](https://github.com/answerai/open-terminal) / [Terminals (Enterprise)](https://github.com/answerai/terminals): طبقة التنفيذ التي تجعل ANSWERAI بيئة متكاملة للوكلاء، مع تنسيق مؤسسي لمساحات عمل منفصلة لكل مستخدم.
- [Knowledge Base Sync (oikb)](https://github.com/answerai/oikb): اعكس المجلدات والمستودعات وحاويات التخزين ومواقع الويكي في قواعد معرفة ANSWERAI باستخدام المزامنة التزايدية.
- [ANSWERAI Computer](https://github.com/answerai/computer): حاسوبك في أي متصفح: الملفات والمحرر والطرفية وGit ووكلاء الذكاء الاصطناعي الاختياريون، جميعها تعمل على جهازك الفعلي.

راجع [وثائق المنظومة](https://docs.answerai.in/ecosystem/) لمزيد من التفاصيل.

### استكشاف الأخطاء والتحديثات

راجع [دليل استكشاف الأخطاء](https://docs.answerai.in/troubleshooting/) لحل مشكلات الاتصال، و[دليل التحديث](https://docs.answerai.in/getting-started/updating) لتحديث تثبيتك.

### الوثائق

راجع [الوثائق](https://docs.answerai.in/) للإعداد والاستخدام، و[خارطة الطريق](https://docs.answerai.in/roadmap/) للاطلاع على الأعمال المخطط لها.

لإعداد Docker Compose أو Kubernetes أو غيرهما، راجع [وثائق التثبيت](https://docs.answerai.in/getting-started/).

### الدعم

[افتح بلاغًا](https://github.com/answerai/answerai/issues) أو [ابدأ نقاشًا](https://github.com/answerai/answerai/discussions).

تجدنا على [Reddit](https://www.reddit.com/r/ANSWERAI/) و[X](https://x.com/ANSWERAI) و[Discord](https://discord.gg/5rJgQTnV4s).

### الأمان

أبلغ عن الثغرات بسرية عبر [GitHub Security Advisories](https://github.com/answerai/answerai/security). تُقبل البلاغات الأمنية عبر GitHub فقط.

### سجل النجوم

<a href="https://star-history.com/#answerai/answerai&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
    <img alt="مخطط سجل النجوم" src="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
  </picture>
</a>

#### الترخيص

يتضمن كودًا يخضع لترخيص ANSWERAI License الذي يشترط الحفاظ على هوية ANSWERAI التجارية، ومساهمات سابقة تخضع لتراخيصها الأصلية. راجع [LICENSE](./LICENSE) و[LICENSE_HISTORY](./LICENSE_HISTORY) للاطلاع على الشروط والسجل.

[المؤسسات](https://docs.answerai.in/enterprise) · [الوظائف](https://careers.answerai.in/) · [الرعاية](https://github.com/sponsors/answerai)

أنشأه [Timothy Jaeryang Baek](https://github.com/tjbck).
