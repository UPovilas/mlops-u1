# Docker vaizdas

| Laukas | Reikšmė |
|---|---|
| Vaizdas | `wine-u1-inference:worktree-c3e2b8057da8` |
| ID | `sha256:db877cb80c05bdfa4ba82268503c5e5e445067682794e4995750147e62590a40` |
| Architektūra | arm64 |
| Dydis | 411763692 B = 411.76 MB = 392.69 MiB |
| Vartotojas | `10001:10001` |
| Modelio SHA256 | `223689954b6d8aa42b477046167b5aa0a0c5cb26bbfc43fffb226692d9cef0be` |

Dydis gautas su `docker image inspect` (`.Size`); tai ne registry perdavimo dydis.
Vaizdas išbandytas be tinklo, su read-only failų sistema ir be papildomų capabilities.
Python bazė fiksuota digest'u; bibliotekos prisegtos `docker/requirements-inference.txt`.
Darbinis tag'as pakeičiamas `sha-<commit>` publikavimo metu.
