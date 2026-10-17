# Hackathon content and license review

Reviewed October 16, 2026. This is a project-specific inventory and release checklist, not a legal opinion. Preserve the original notices and recheck any dependency/model added before publication.

## Existing repository and sample

The repository [LICENSE](../../LICENSE) is MIT, copyright 2026 agammann. The original garden chapter at `backend/sample/chapter.txt`, its PDF/DOCX forms, and the authored offline example are project material covered by that license. They do not reproduce a textbook or a third-party curriculum. The explicit [sample notice](../../backend/sample/LICENSE.txt) records those terms and should travel with redistributed sample files. Do not imply that the sample establishes horticultural expertise; in the demonstration, it is the bounded source of educational claims.

Visitor uploads retain their owners' rights. Ask visitors to use material they may process. A source upload, short quotation, and generated export do not transfer textbook rights to Easy Street. Exports may include quotations, so users must review permission and sharing suitability. Demonstrations should use the original sample rather than visitor documents.

The released dependency review is [docs/DEPENDENCIES.md](../DEPENDENCIES.md), with built-interface notices in [THIRD_PARTY_NOTICES.txt](../../THIRD_PARTY_NOTICES.txt). The source license does not replace React, Lucide, Python-package, optional OCR, or other third-party licenses. New packages or binary distribution changes need a refreshed review. Existing optional Tesseract/PDFium installation remains separate from the application source.

The Dockerfile uses official Node.js 22 and Python 3.12 Debian Bookworm-based images and the existing application dependency locks. Node and the frontend build tools stay in the build stage. No new application package is introduced solely for Nebius: the adapter uses the already present OpenAI-compatible SDK.

The locally built October 16 runtime was inspected: 32 Python distributions, including pip, had retained license/copyright artifacts; the Python runtime license was present, along with 105 system-package copyright files. Application package versions match the pinned lock. Colorama's short license metadata is empty, but its classifier identifies BSD and its shipped `LICENSE.txt` is present. The runtime also retains the built-interface notices and project license. No model weights, NVIDIA runtime, Node executable, or optional OCR binaries are bundled.

Debian base components include separate copyleft terms; the earlier application's dependency-graph review must not be interpreted as a claim that the entire container is GPL-free. Hosting an image and redistributing a binary image have different release implications. Before any approved public image distribution, inventory the final built image and satisfy applicable source, license, and notice obligations. The app's MIT license does not replace those terms. The tested image identity is recorded in [CONTEST_CHANGES.md](CONTEST_CHANGES.md).

## Nebius and NVIDIA

The implementation pins Token Factory model ID **`nvidia/nemotron-3-super-120b-a12b`**. NVIDIA's [upstream Nemotron 3 Super 120B A12B model card](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16) identifies the [NVIDIA Nemotron Open Model License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-nemotron-open-model-license/). This identifies the family and governing upstream license. The authenticated catalog and both approved live generation/support-review runs verified this exact identifier, including revised prompt v2.1. That confirms observed account/model availability for the test, not which weight precision Nebius serves or acceptance of any new terms.

The NVIDIA license permits commercial use and derivatives, excludes separable interface-linked applications from its derivative-work definition, and does not claim ownership of model outputs. Redistributing weights or model derivatives has separate license and notice conditions. Easy Street calls hosted inference and bundles no weights, NIM container, or NVIDIA runtime. The application's MIT license does not relicense the model or Nebius service. Adding any of those artifacts requires another review.

Official references to review for the selected model:

- [Nebius API quickstart](https://docs.tokenfactory.nebius.com/quickstart) and actual model entry in the Token Factory catalog.
- The NVIDIA-owned card and license above, plus the actual catalog mapping and any model-specific policy shown by Nebius. Do not assume all future Nemotron variants have identical terms.
- [Nebius Services Agreement](https://docs.nebius.com/legal/agreement), [Acceptable Use Policy](https://docs.nebius.com/legal/aup), and any account-specific terms presented before activation.
- [Legacy Token Factory notice](https://docs.tokenfactory.nebius.com/legal/terms-of-service): the page limits its legacy terms to qualifying existing reserves and redirects other customers to the current agreement. Do not rely on a stale service summary.

No key, account setup, license-acceptance checkbox, promotional signup, or financial agreement is accepted by adding integration code. The owner must authorize any new agreements or financial commitments. Service and model policy review is separate from code-secret scanning and source-support tests.

## Video and entry assets

Use actual application footage, the original sample, and the project's own text. No copyrighted music, borrowed textbook pages, unrelated logos, stock footage, or third-party illustrations are needed. Descriptive references to the services used should not imply endorsement. Do not copy marketing claims into educational output. The entry must accurately identify inherited application features and the contest changes.

## Final inventory before publication

- [x] Record configured runtime model ID, NVIDIA upstream card, and upstream license.
- [x] Confirm the authenticated Nebius catalog mapping and model availability in both approved live runs; see [verification](VERIFICATION.md).
- [ ] Resolve any new account/model terms with the owner before accepting them or extending the service arrangement.
- [ ] Confirm no new runtime dependency was added without a corresponding license entry.
- [ ] Retain all notices in any built source/release distribution.
- [ ] Verify the sample's TXT/PDF/DOCX files derive from the same original project text.
- [ ] Review all screenshots, video frames, README examples, and exported demonstration files for third-party/private content and keys.
- [ ] Obtain the owner's remaining release/video-publication and agreement approvals; branch publication/draft PR are already approved and complete. Do not make personal ownership attestations on their behalf.
