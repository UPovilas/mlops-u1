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
| Istorinio run'o atkūrimas | 32.685 s; visos keturios metrikos sutapo |
| Didžiausia modelio fit trukmė | 0.059 s |
| Atskira projekto kopija ir tuščias DVC remote | 56.914 s; pipeline ir cache atkūrimas PASS |
| MLflow ir PostgreSQL Pod'ų perkūrimas | Metaduomenys ir artefaktų hash'ai nepasikeitė |
| Inferencijos vaizdo dydis | 411.76 MB, arm64 |
| Trivy | CRITICAL 0, HIGH 44, MEDIUM 58 |

**Kas neveikė.** MLflow pradžioje viršijo 1536 MiB limitą dėl įjungto foninių
užduočių vykdymo. Šiam darbui nenaudojamas job vykdiklis išjungtas, tracking veikia
su vienu web worker'iu. MLflow nepalaiko Pandas 3, todėl aplinkoje naudojama 2.3.3.
Medžio serializavimui aiškiai leidžiamas savo apmokyto sklearn medžio tipas.
Likę HIGH OS radiniai ir pataisų prieinamumas pateikti security-scan.md.

**Pateikimo būsena.** Techninės patikros atliktos. Darbiniai failai necommitinti;
viešas repo, galutinis sha-<commit> vaizdas GHCR ir u1-final tag'as priskiriami
publikavimo metu. Pateikimo failai supakuoti į dist/wine-u1.zip.
