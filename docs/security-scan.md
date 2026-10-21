# Trivy skenavimas

Vaizdas: `wine-u1-inference:sha-00962be3a4b9`. Skenuota: 2026-10-21T22:39:27.919215+03:00.
Skenavimo ir vaizdo ID sutapimas patikrintas. Visas rezultatas — `trivy.json`.

| Svarba | Radinių skaičius |
|---|---:|
| CRITICAL | 0 |
| HIGH | 44 |
| MEDIUM | 58 |
| LOW | 61 |
| UNKNOWN | 2 |

CRITICAL publikavimo patikra: **PASS**.
Iš HIGH radinių 0 turi skene nurodytą pataisytą versiją.
OS paketai atnaujinti build metu. Inferencijos runtime pašalinti pip ir ensurepip;
vykdymui jie nereikalingi. Likę radiniai nėra paslėpti su ignore taisyklėmis.
Radinys vertinamas kartu su paketu, pataisos prieinamumu ir vykdymo kontekstu;
ne root, read-only ir išjungtas tinklas nepanaikina paties CVE.
