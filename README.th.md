<h2>ANSWERAI</h2>

<p>ANSWERAI คือ <a href="https://docs.answerai.in/"><strong>บ้านสำหรับ AI</strong></a>: แพลตฟอร์มที่โฮสต์เองได้ ขยายความสามารถได้ ใช้งานง่าย และออกแบบให้ทำงานแบบออฟไลน์ได้ทั้งหมด เชื่อมต่อโมเดลภายในเครื่องผ่าน Ollama หรือใช้ API ที่เข้ากันได้กับ OpenAI สำหรับโมเดลภายในเครื่องและบนคลาวด์</p>

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

[![การสาธิต ANSWERAI](https://cdn.answerai.in/answerai-demo.gif)](https://docs.answerai.in/)

![GitHub stars](https://img.shields.io/github/stars/answerai/answerai?style=social)
![GitHub forks](https://img.shields.io/github/forks/answerai/answerai?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/answerai/answerai?style=social)
![GitHub repo size](https://img.shields.io/github/repo-size/answerai/answerai)
![GitHub language count](https://img.shields.io/github/languages/count/answerai/answerai)
![GitHub top language](https://img.shields.io/github/languages/top/answerai/answerai)
![GitHub last commit](https://img.shields.io/github/last-commit/answerai/answerai?color=red)
[![Discord](https://img.shields.io/badge/Discord-ANSWERAI-blue?logo=discord&logoColor=white)](https://discord.gg/5rJgQTnV4s)
[![](https://img.shields.io/static/v1?label=Sponsor&message=Support&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/answerai)

[สำรวจ ANSWERAI →](https://docs.answerai.in/)

### การติดตั้ง

#### Python

ต้องใช้ Python 3.12

```bash
pip install answerai
answerai serve
```

จากนั้นเปิด [http://localhost:8080](http://localhost:8080)

#### Docker

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v answerai:/app/backend/data --name answerai --restart always ghcr.io/answerai/answerai:main
```

จากนั้นเปิด [http://localhost:3000](http://localhost:3000)

| แท็กอิมเมจ | สิ่งที่มีให้                                                                      |
| ---------- | --------------------------------------------------------------------------------- |
| `:main`    | อิมเมจมาตรฐานพร้อมแพ็กเกจที่จำเป็นสำหรับ AI ภายในเครื่อง                          |
| `:slim`    | อิมเมจขนาดเล็กที่ใช้บริการภายนอกสำหรับ embeddings การสกัดข้อมูลจากเอกสาร และเสียง |
| `:cuda`    | ANSWERAI พร้อมการเร่งความเร็วด้วย CUDA                                            |
| `:ollama`  | ANSWERAI ที่รวม Ollama มาให้                                                      |
| `:dev`     | บิลด์สำหรับการพัฒนาล่าสุด                                                         |

เพิ่มตัวเลือกเหล่านี้ใน `docker run` ก่อนชื่ออิมเมจได้ตามต้องการ:

| ตัวเลือก                                             | จุดประสงค์                                                                          |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `-e OLLAMA_BASE_URL=http://your-ollama-server:11434` | เชื่อมต่อกับ Ollama บนเซิร์ฟเวอร์อื่น                                               |
| `-e OPENAI_API_KEY=your_secret_key`                  | กำหนดคีย์ API ของ OpenAI                                                            |
| `-e HF_HUB_OFFLINE=1`                                | ปิดการดาวน์โหลดโมเดลจาก Hugging Face สำหรับการใช้งานออฟไลน์                         |
| `--gpus all`                                         | เปิดใช้ GPU Nvidia สำหรับ `:cuda` หรือ `:ollama` โดยต้องมี Nvidia Container Toolkit |

ดูขั้นตอนการติดตั้งและตัวเลือกการตั้งค่าใน[คู่มือการติดตั้งด้วย Docker](https://docs.answerai.in/getting-started/quick-start/)

#### แอปเดสก์ท็อป

[ดาวน์โหลดแอปเดสก์ท็อปเนทีฟ](https://github.com/answerai/desktop)สำหรับ macOS, Windows และ Linux

[อ่านเอกสาร →](https://docs.answerai.in/getting-started/)

### ระบบนิเวศ

- [Open Terminal](https://github.com/answerai/open-terminal) / [Terminals (Enterprise)](https://github.com/answerai/terminals): ชั้นการทำงานที่ทำให้ ANSWERAI เป็นสภาพแวดล้อมเอเจนต์ที่ครบถ้วน พร้อมระบบจัดการพื้นที่ทำงานแยกตามผู้ใช้ในระดับองค์กร
- [Knowledge Base Sync (oikb)](https://github.com/answerai/oikb): ทำสำเนาโฟลเดอร์ รีโพซิทอรี บักเก็ต และวิกิลงในฐานความรู้ ANSWERAI ด้วยการซิงก์เฉพาะส่วนที่เปลี่ยนแปลง
- [ANSWERAI Computer](https://github.com/answerai/computer): คอมพิวเตอร์ของคุณในทุกเบราว์เซอร์: ไฟล์ ตัวแก้ไข เทอร์มินัล Git และเอเจนต์ AI ที่เลือกใช้ได้ ทั้งหมดทำงานบนเครื่องจริงของคุณ

ดูรายละเอียดใน[เอกสารระบบนิเวศ](https://docs.answerai.in/ecosystem/)

### การแก้ไขปัญหาและการอัปเดต

ดู[คู่มือแก้ไขปัญหา](https://docs.answerai.in/troubleshooting/)สำหรับปัญหาการเชื่อมต่อ และ[คู่มืออัปเดต](https://docs.answerai.in/getting-started/updating)เพื่ออัปเดตการติดตั้งของคุณ

### เอกสาร

ดู[เอกสาร](https://docs.answerai.in/)สำหรับการตั้งค่าและการใช้งาน และ[แผนการพัฒนา](https://docs.answerai.in/roadmap/)สำหรับงานที่วางแผนไว้

สำหรับ Docker Compose, Kubernetes และการติดตั้งแบบอื่น ๆ ดู[เอกสารการติดตั้ง](https://docs.answerai.in/getting-started/)

### การช่วยเหลือ

[เปิด issue](https://github.com/answerai/answerai/issues) หรือ[เริ่มการสนทนา](https://github.com/answerai/answerai/discussions)

พบเราได้ที่ [Reddit](https://www.reddit.com/r/ANSWERAI/), [X](https://x.com/ANSWERAI) และ [Discord](https://discord.gg/5rJgQTnV4s)

### ความปลอดภัย

รายงานช่องโหว่แบบเป็นส่วนตัวผ่าน [GitHub Security Advisories](https://github.com/answerai/answerai/security) โดยรับรายงานด้านความปลอดภัยผ่าน GitHub เท่านั้น

### ประวัติจำนวนดาว

<a href="https://star-history.com/#answerai/answerai&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
    <img alt="กราฟประวัติจำนวนดาว" src="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
  </picture>
</a>

#### สัญญาอนุญาต

มีโค้ดภายใต้ ANSWERAI License ซึ่งกำหนดให้คงแบรนด์ ANSWERAI ไว้ รวมถึงผลงานที่มีผู้ร่วมพัฒนาก่อนหน้านี้ภายใต้สัญญาอนุญาตเดิมของแต่ละส่วน ดูเงื่อนไขและประวัติได้ที่ [LICENSE](./LICENSE) และ [LICENSE_HISTORY](./LICENSE_HISTORY)

[องค์กร](https://docs.answerai.in/enterprise) · [ร่วมงานกับเรา](https://careers.answerai.in/) · [สนับสนุนโครงการ](https://github.com/sponsors/answerai)

สร้างโดย [Timothy Jaeryang Baek](https://github.com/tjbck)
