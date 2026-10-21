# Trivy skenavimas

Vaizdas: `wine-u1-inference:worktree-c3e2b8057da8`. Skenuota: 2026-10-19T09:42:01.233887+03:00.
Skenavimo ir vaizdo ID sutapimas patikrintas. Visas rezultatas — `trivy.json`.

| Svarba | Radinių skaičius |
|---|---:|
| CRITICAL | 0 |
| HIGH | 44 |
| MEDIUM | 58 |
| LOW | 61 |
| UNKNOWN | 1 |

CRITICAL publikavimo patikra: **PASS**.
Iš HIGH radinių 0 turi skene nurodytą pataisytą versiją.
OS paketai atnaujinti build metu. Inferencijos runtime pašalinti pip ir ensurepip;
vykdymui jie nereikalingi. Likę radiniai nėra paslėpti su ignore taisyklėmis.
Radinys vertinamas kartu su paketu, pataisos prieinamumu ir vykdymo kontekstu;
ne root, read-only ir išjungtas tinklas nepanaikina paties CVE.
