# U1 ataskaita

Wine klasifikavimo projektas: 178 įrašai, 13 požymių, trys klasės. Train/test
padalijimas 142/36, stratifikuotas, seed 42. Random Forest mokomas CPU.

**Įgyvendinta.** DVC grandinė prepare → train → evaluate, parametrų failas,
lock ir vietinis remote. Trys skirtingų hiperparametrų mokymai log'inami į savo
MLflow kind klasteryje. PostgreSQL saugo metaduomenis, atskiras PVC — artefaktus.
Modelis, duomenų ir kodo SHA256, parametrai bei uv.lock leidžia atkurti istorinį run'ą.
Inferencijos Docker vaizdas paleidžiamas ne root vartotoju; įvestis — JSON.

| Patikra | Rezultatas |
|---|---|
| Istorinio run'o atkūrimas | 28.478 s; visos keturios metrikos sutapo |
| Didžiausia modelio fit trukmė | 0.069 s |
| Atskira projekto kopija ir tuščias DVC remote | 70.126 s; pipeline ir cache atkūrimas PASS |
| MLflow ir PostgreSQL Pod'ų perkūrimas | Metaduomenys ir artefaktų hash'ai nepasikeitė |
| Inferencijos vaizdo dydis | 411.76 MB, arm64 |
| Trivy | CRITICAL 0, HIGH 44, MEDIUM 58 |

**Kas neveikė.** MLflow pradžioje viršijo 1536 MiB limitą dėl įjungto foninių
užduočių vykdymo. Šiam darbui nenaudojamas job vykdiklis išjungtas, tracking veikia
su vienu web worker'iu. MLflow nepalaiko Pandas 3, todėl aplinkoje naudojama 2.3.3.
Medžio serializavimui aiškiai leidžiamas savo apmokyto sklearn medžio tipas.
Likę HIGH OS radiniai ir pataisų prieinamumas pateikti security-scan.md.

**Laikas.** Darbas užtruko apie 8 valandas.

**Pateikimas.** [GitHub repozitorija](https://github.com/UPovilas/mlops-u1),
tag'as [u1-final](https://github.com/UPovilas/mlops-u1/tree/u1-final).
GHCR vaizdas: `ghcr.io/upovilas/wine-u1:sha-00962be3a4b9`.
Registry digest: `sha256:e94b10ff14da9ce3d4ca3dbbb3e45e6a4bb3d03efbec0081a666cf584fe0064f`.
Vaizdo kodo commit'as: [00962be3a4b9ba1f190c95079b74315d6daa891c](https://github.com/UPovilas/mlops-u1/commit/00962be3a4b9ba1f190c95079b74315d6daa891c).
