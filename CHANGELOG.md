# Changelog

## [0.10.0](https://github.com/Exar-lab/Sistema_Biblioteca/compare/sistema-biblioteca-v0.9.0...sistema-biblioteca-v0.10.0) (2026-06-07)


### Features

* agregar frontend completo del sistema de biblioteca ([bdac8f8](https://github.com/Exar-lab/Sistema_Biblioteca/commit/bdac8f8ba47cdbb2eb54e73e17b76bffcd841b96))

## [0.9.0](https://github.com/Exar-lab/Sistema_Biblioteca/compare/sistema-biblioteca-v0.8.0...sistema-biblioteca-v0.9.0) (2026-06-06)


### Features

* **api:** expose secure circulation endpoints ([5e49dff](https://github.com/Exar-lab/Sistema_Biblioteca/commit/5e49dffc3f06576004c2feeab1841f5ca5dcbddf))
* **api:** expose secure circulation endpoints ([06ceb20](https://github.com/Exar-lab/Sistema_Biblioteca/commit/06ceb20daa993814f1bbf808669caf98a1f30ad9))


### Bug Fixes

* **auth:** reject role fields on registration ([f8849b7](https://github.com/Exar-lab/Sistema_Biblioteca/commit/f8849b79e7182d8e1217933171446fd79a1268fb))

## [0.8.0](https://github.com/Exar-lab/Sistema_Biblioteca/compare/sistema-biblioteca-v0.7.0...sistema-biblioteca-v0.8.0) (2026-06-05)


### Features

* **api:** expose missing endpoints and fix registration service ([dd8e330](https://github.com/Exar-lab/Sistema_Biblioteca/commit/dd8e33065bd91747f57b244671dbf87c12ae2d1b))
* **api:** expose missing endpoints and fix registration service ([d5a422c](https://github.com/Exar-lab/Sistema_Biblioteca/commit/d5a422c72e49b503b212f4680444d3019842b52a))

## [0.7.0](https://github.com/Exar-lab/Sistema_Biblioteca/compare/sistema-biblioteca-v0.6.0...sistema-biblioteca-v0.7.0) (2026-06-03)


### Features

* **db:** add Oracle sequences and PL/SQL stored procedure packages ([301557e](https://github.com/Exar-lab/Sistema_Biblioteca/commit/301557e2ca5df12acca099ae7a4f2442a1eb83ba))
* **db:** add Oracle sequences and PL/SQL stored procedure packages ([9ea16a4](https://github.com/Exar-lab/Sistema_Biblioteca/commit/9ea16a4a375cdcde4f39fafdacfcc6402490020b)), closes [#43](https://github.com/Exar-lab/Sistema_Biblioteca/issues/43)
* **persistence:** implement Oracle stored procedure repository layer ([33e8b3b](https://github.com/Exar-lab/Sistema_Biblioteca/commit/33e8b3b913441900ea6b36285325ae900f5a1999))
* **persistence:** implement Oracle stored procedure repository layer ([986edcf](https://github.com/Exar-lab/Sistema_Biblioteca/commit/986edcf697826a2e7ec2098750682aa823f5fe5f)), closes [#44](https://github.com/Exar-lab/Sistema_Biblioteca/issues/44)


### Bug Fixes

* **db:** address Oracle schema review comments ([42915ab](https://github.com/Exar-lab/Sistema_Biblioteca/commit/42915abb071436ab749a3035bf73a09262d4d2a0))
* **persistence:** restore repository wiring ([49a4d1c](https://github.com/Exar-lab/Sistema_Biblioteca/commit/49a4d1c8ba98ad200b4493a29d325ad788196bbb))

## [0.6.0](https://github.com/Exar-lab/Sistema_Biblioteca/compare/sistema-biblioteca-v0.5.0...sistema-biblioteca-v0.6.0) (2026-06-01)


### Features

* **auth:** add auth router with login/me endpoints, JWT dependency, and error handling ([2eb4c22](https://github.com/Exar-lab/Sistema_Biblioteca/commit/2eb4c22e0437e10b9732249a1e5b3fa58a453573))
* **auth:** add AuthService with authenticate and register methods ([b7a5f19](https://github.com/Exar-lab/Sistema_Biblioteca/commit/b7a5f195f710e3cd08772deac0e00e4ed4ae348e))
* **auth:** add get_by_username, JWT config, and security utilities ([b9ae997](https://github.com/Exar-lab/Sistema_Biblioteca/commit/b9ae997fd68f52971906581392a08421a5173099))
* **auth:** add passlib and python-jose dependencies for JWT auth ([6f1e144](https://github.com/Exar-lab/Sistema_Biblioteca/commit/6f1e1444039d602ee4b70cad9e55f3d3f4ce2912))
* **auth:** add require_role dependency and protect admin endpoints ([4201c6a](https://github.com/Exar-lab/Sistema_Biblioteca/commit/4201c6a526c02aff46e58a3e13870ed4793ee568))
* JWT authentication with login/me endpoints and role-based access ([fecefe2](https://github.com/Exar-lab/Sistema_Biblioteca/commit/fecefe2a58e6b7cade03a9ab6c0cf4485aa29be8))


### Bug Fixes

* **auth:** harden JWT validation and docs ([49f9c5f](https://github.com/Exar-lab/Sistema_Biblioteca/commit/49f9c5f84b236b4131865cb0cffe85531ab42226))

## [0.5.0](https://github.com/Exar-lab/Sistema_Biblioteca/compare/sistema-biblioteca-v0.4.0...sistema-biblioteca-v0.5.0) (2026-05-30)


### Features

* **catalog:** add author CRUD slice ([e6810d2](https://github.com/Exar-lab/Sistema_Biblioteca/commit/e6810d28107cca9275c8985dea300a49a92982a9))
* **catalog:** add author CRUD slice ([cd1d24e](https://github.com/Exar-lab/Sistema_Biblioteca/commit/cd1d24ec9935c3f4516e3a416990a18a4ec73756))
* **catalog:** add book CRUD slice ([7f61f71](https://github.com/Exar-lab/Sistema_Biblioteca/commit/7f61f71fa01eb9cfaa6c196eb31be017a891efae))
* **catalog:** add book CRUD slice ([fa56f2a](https://github.com/Exar-lab/Sistema_Biblioteca/commit/fa56f2a6da517031cc9a28d09b9c752239b7b137))
* **catalog:** add category CRUD slice ([982a377](https://github.com/Exar-lab/Sistema_Biblioteca/commit/982a3775e29b49db1ca696a969e59de549b24519))
* **catalog:** add role CRUD slice ([79bde68](https://github.com/Exar-lab/Sistema_Biblioteca/commit/79bde6890f85e5b5bb3a3c18256d88ca139a9bd9))
* **circulation:** add loans CRUD slice ([d317715](https://github.com/Exar-lab/Sistema_Biblioteca/commit/d317715698a495f22a3876ff2f12429f2e510049))
* **circulation:** add returns CRUD slice ([581dd4c](https://github.com/Exar-lab/Sistema_Biblioteca/commit/581dd4cfaa5a324b19456e2e9714fca20681d699))
* **reports:** add dashboard guardrails slice ([0cf92ea](https://github.com/Exar-lab/Sistema_Biblioteca/commit/0cf92ea46f6d13547361e709567f0e32fa36de2f))
* **reports:** add dashboard guardrails slice ([da14a6a](https://github.com/Exar-lab/Sistema_Biblioteca/commit/da14a6a903854c7591779a480c104dcf377208ab))


### Bug Fixes

* **catalog:** address book review feedback ([f0ee7a8](https://github.com/Exar-lab/Sistema_Biblioteca/commit/f0ee7a8da1191f8e9cedf3adf99ffdb46bce123d))
* **catalog:** align category repository contract ([49efca3](https://github.com/Exar-lab/Sistema_Biblioteca/commit/49efca3f3ec8f58ce6c5e15f9565337f3a0bec0d))
* **circulation:** block inactive users from creating loans ([4d4b640](https://github.com/Exar-lab/Sistema_Biblioteca/commit/4d4b64023d5eeb290ea57c1322d627ddc0cf6c86))
* **persistence:** align category and user contracts ([3ce7443](https://github.com/Exar-lab/Sistema_Biblioteca/commit/3ce7443f99b97cede21f26b9a6bcf4028c9396aa))
* **reports:** normalize dashboard month dates ([f2cabfc](https://github.com/Exar-lab/Sistema_Biblioteca/commit/f2cabfccf2c1f026ffd0f5b1cd7811f95cd6238e))
* **review:** address Copilot feedback on returns slice ([93351d2](https://github.com/Exar-lab/Sistema_Biblioteca/commit/93351d207b0342069c0356c225f356ea3f9b6344))

## [0.4.0](https://github.com/Exar-lab/Sistema_Biblioteca/compare/sistema-biblioteca-v0.3.0...sistema-biblioteca-v0.4.0) (2026-05-21)


### Features

* **domain:** add ORM models, Protocol ports, BoolChar, and domain errors ([3119342](https://github.com/Exar-lab/Sistema_Biblioteca/commit/3119342dfb6ff619c623826ca4897e3c2952c186)), closes [#10](https://github.com/Exar-lab/Sistema_Biblioteca/issues/10)
* **domain:** domain foundation — ORM models, Protocol ports, BoolChar, domain errors ([3de135e](https://github.com/Exar-lab/Sistema_Biblioteca/commit/3de135ed05ea5ed73cfb6d3f0945f932d24ad620))


### Bug Fixes

* **domain:** decouple ORM Base from engine init and harden BoolChar bind ([7361170](https://github.com/Exar-lab/Sistema_Biblioteca/commit/73611707e289052ed20100cda1e16a76c1b33a3b))

## [0.3.0](https://github.com/Exar-lab/Sistema_Biblioteca/compare/sistema-biblioteca-v0.2.0...sistema-biblioteca-v0.3.0) (2026-05-19)


### Features

* **db:** add Oracle SQLAlchemy connection ([ee62154](https://github.com/Exar-lab/Sistema_Biblioteca/commit/ee62154e8448fecd8675a50363bc22ae683fd036))
* **db:** add Oracle SQLAlchemy connection ([c561af5](https://github.com/Exar-lab/Sistema_Biblioteca/commit/c561af5ec94da82ea93af36c186886050e6150f2))


### Bug Fixes

* **db:** address health review comments ([a1506fa](https://github.com/Exar-lab/Sistema_Biblioteca/commit/a1506fae58681d203e509027210ca12024dccb04))

## [0.2.0](https://github.com/Exar-lab/Sistema_Biblioteca/compare/sistema-biblioteca-v0.1.0...sistema-biblioteca-v0.2.0) (2026-05-19)


### Features

* **schemas:** add pydantic domain models ([d5574cc](https://github.com/Exar-lab/Sistema_Biblioteca/commit/d5574cca7e90129ff5003e9101d68ccf29f5a5c5))
* **schemas:** add pydantic domain models ([eb99936](https://github.com/Exar-lab/Sistema_Biblioteca/commit/eb99936c68b2ecdc1e4887cb70beec7aa67b61de))


### Bug Fixes

* **schemas:** protect credential fields ([49fe92c](https://github.com/Exar-lab/Sistema_Biblioteca/commit/49fe92cf1ac95230a81590b9be1abad007b35387))
