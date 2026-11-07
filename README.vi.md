<h2>ANSWERAI</h2>

<p>ANSWERAI là <a href="https://docs.answerai.in/"><strong>ngôi nhà dành cho AI</strong></a>: một nền tảng tự lưu trữ, dễ mở rộng, dễ sử dụng và được thiết kế để hoạt động hoàn toàn ngoại tuyến. Kết nối mô hình cục bộ qua Ollama hoặc dùng API tương thích với OpenAI cho các mô hình cục bộ và trên đám mây.</p>

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

[![Bản trình diễn ANSWERAI](https://cdn.answerai.in/answerai-demo.gif)](https://docs.answerai.in/)

![GitHub stars](https://img.shields.io/github/stars/answerai/answerai?style=social)
![GitHub forks](https://img.shields.io/github/forks/answerai/answerai?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/answerai/answerai?style=social)
![GitHub repo size](https://img.shields.io/github/repo-size/answerai/answerai)
![GitHub language count](https://img.shields.io/github/languages/count/answerai/answerai)
![GitHub top language](https://img.shields.io/github/languages/top/answerai/answerai)
![GitHub last commit](https://img.shields.io/github/last-commit/answerai/answerai?color=red)
[![Discord](https://img.shields.io/badge/Discord-ANSWERAI-blue?logo=discord&logoColor=white)](https://discord.gg/5rJgQTnV4s)
[![](https://img.shields.io/static/v1?label=Sponsor&message=Support&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/answerai)

[Khám phá ANSWERAI →](https://docs.answerai.in/)

### Cài đặt

#### Python

Yêu cầu Python 3.12.

```bash
pip install answerai
answerai serve
```

Sau đó mở [http://localhost:8080](http://localhost:8080).

#### Docker

```bash
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v answerai:/app/backend/data --name answerai --restart always ghcr.io/answerai/answerai:main
```

Sau đó mở [http://localhost:3000](http://localhost:3000).

| Thẻ image | Nội dung                                                                             |
| --------- | ------------------------------------------------------------------------------------ |
| `:main`   | Image tiêu chuẩn với các thư viện phụ thuộc cho AI cục bộ                            |
| `:slim`   | Image gọn nhẹ dùng dịch vụ bên ngoài cho embedding, trích xuất tài liệu và giọng nói |
| `:cuda`   | ANSWERAI với tăng tốc CUDA                                                           |
| `:ollama` | ANSWERAI tích hợp sẵn Ollama                                                         |
| `:dev`    | Bản dựng phát triển mới nhất                                                         |

Thêm các tùy chọn sau vào `docker run` trước tên image khi cần:

| Tùy chọn                                             | Mục đích                                                                                   |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `-e OLLAMA_BASE_URL=http://your-ollama-server:11434` | Kết nối đến Ollama trên máy chủ khác                                                       |
| `-e OPENAI_API_KEY=your_secret_key`                  | Thiết lập khóa API OpenAI                                                                  |
| `-e HF_HUB_OFFLINE=1`                                | Tắt tải mô hình Hugging Face để sử dụng ngoại tuyến                                        |
| `--gpus all`                                         | Bật quyền truy cập GPU Nvidia cho `:cuda` hoặc `:ollama`; yêu cầu Nvidia Container Toolkit |

Xem [hướng dẫn cài đặt Docker](https://docs.answerai.in/getting-started/quick-start/) để biết các bước thiết lập và tùy chọn cấu hình.

#### Ứng dụng máy tính

[Tải ứng dụng máy tính gốc](https://github.com/answerai/desktop) cho macOS, Windows và Linux.

[Đọc tài liệu →](https://docs.answerai.in/getting-started/)

### Hệ sinh thái

- [Open Terminal](https://github.com/answerai/open-terminal) / [Terminals (Enterprise)](https://github.com/answerai/terminals): Lớp thực thi biến ANSWERAI thành môi trường tác tử hoàn chỉnh, với khả năng điều phối cấp doanh nghiệp cho không gian làm việc riêng của từng người dùng.
- [Knowledge Base Sync (oikb)](https://github.com/answerai/oikb): Đồng bộ các thư mục, kho mã, bucket và wiki vào cơ sở tri thức ANSWERAI theo kiểu gia tăng.
- [ANSWERAI Computer](https://github.com/answerai/computer): Máy tính của bạn trong bất kỳ trình duyệt nào: tệp, trình soạn thảo, terminal, Git và các tác tử AI tùy chọn đều chạy trên máy thật của bạn.

Xem [tài liệu hệ sinh thái](https://docs.answerai.in/ecosystem/) để biết chi tiết.

### Khắc phục sự cố và cập nhật

Xem [hướng dẫn khắc phục sự cố](https://docs.answerai.in/troubleshooting/) khi gặp vấn đề kết nối và [hướng dẫn cập nhật](https://docs.answerai.in/getting-started/updating) để cập nhật bản cài đặt.

### Tài liệu

Xem [tài liệu](https://docs.answerai.in/) để biết cách cấu hình và sử dụng, cùng [lộ trình](https://docs.answerai.in/roadmap/) cho các công việc dự kiến.

Với Docker Compose, Kubernetes và các cách thiết lập khác, xem [tài liệu cài đặt](https://docs.answerai.in/getting-started/).

### Hỗ trợ

[Tạo issue](https://github.com/answerai/answerai/issues) hoặc [bắt đầu thảo luận](https://github.com/answerai/answerai/discussions).

Tìm chúng tôi trên [Reddit](https://www.reddit.com/r/ANSWERAI/), [X](https://x.com/ANSWERAI) và [Discord](https://discord.gg/5rJgQTnV4s).

### Bảo mật

Báo cáo lỗ hổng một cách riêng tư qua [GitHub Security Advisories](https://github.com/answerai/answerai/security). Báo cáo bảo mật chỉ được tiếp nhận qua GitHub.

### Lịch sử sao

<a href="https://star-history.com/#answerai/answerai&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
    <img alt="Biểu đồ lịch sử sao" src="https://api.star-history.com/svg?repos=answerai/answerai&type=Date" />
  </picture>
</a>

#### Giấy phép

Bao gồm mã theo ANSWERAI License, yêu cầu giữ nguyên thương hiệu ANSWERAI, và các đóng góp trước đây theo giấy phép gốc tương ứng. Xem [LICENSE](./LICENSE) và [LICENSE_HISTORY](./LICENSE_HISTORY) để biết điều khoản và lịch sử.

[Doanh nghiệp](https://docs.answerai.in/enterprise) · [Tuyển dụng](https://careers.answerai.in/) · [Tài trợ](https://github.com/sponsors/answerai)

Được tạo bởi [Timothy Jaeryang Baek](https://github.com/tjbck).
