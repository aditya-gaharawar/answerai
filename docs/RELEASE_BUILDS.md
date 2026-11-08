# Release build configuration

The November 2026 Docker failure was an incompatible torch/torchvision installation: Docker installed torch <=2.9.1 and a matching torchvision, then the application requirements upgraded torch to >=2.13.0. Importing embeddings failed with `RuntimeError: operator torchvision::nms does not exist`. Slim builds passed because they omitted that installation.

Docker now installs torch 2.13.0 with torchvision 0.28.0 from the same official wheel index, and constrains subsequent requirements installation to those exact installed builds. Each non-slim image enforces wheel constraints during dependency resolution and executes the native torchvision NMS operator before downloading embedding models. Unused torchaudio preinstallation is removed. The default CUDA channel is cu126, where the matched pair exists for Python 3.12 on both x86_64 and aarch64; cu128 currently lacks that pair. Override channels only when compatible wheels are available. Existing devices must support the installed torch build; the old <=2.9.1 ARM workaround cannot satisfy the application's >=2.13.0 requirement.

GHCR remains the default container destination. Manifests publish only after the whole build matrix succeeds, preventing downstream publishing from treating missing architecture builds as success.

Optional integrations require explicit repository Actions variables:

| Variable | Required configuration |
| --- | --- |
| `ENABLE_DOCKERHUB_PUBLISH=true` | `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets, with write access to `answerai/answerai` |
| `ENABLE_HELM_AUTOMATION=true` | `HELM_CHARTS_APP_ID` and `HELM_CHARTS_APP_PRIVATE_KEY` secrets, GitHub App access to `helm-charts` |
| `ENABLE_PYPI_PUBLISH=true` | A PyPI trusted publisher for this repository, `.github/workflows/release-pypi.yml` and environment `pypi` |

PyPI package builds still run on main. Distribution publishing occurs only for version tags and when explicitly enabled, avoiding an upload of the same version on every main commit. The failed PyPI upload reported `invalid-publisher`; this account-side configuration cannot be supplied through repository source. Docker Hub similarly reported missing username/password and Helm reported a missing app ID. Disabled optional integrations skip their jobs/steps rather than failing a valid GHCR build.

Old release tags retain their original workflow and Dockerfile. Re-running an old tag does not pick up these fixes; build the corrected branch or create a new versioned release through the normal release process.

The ARM CUDA rerun exposed malformed upstream NVIDIA wheel metadata: the aarch64 `nvidia-cusparselt-cu12==0.7.1` wheel declares `Tag: py3-none-manylinux2014_sbsa`. Pip check rejects that nonstandard platform tag. Both pip check and uv pip check reject that malformed tag. The Docker build therefore relies on the constrained installer resolver for dependency consistency and on mandatory torch/torchvision native execution and embedding initialization, rather than adding a whole-environment platform-tag check. No native import error is ignored.
