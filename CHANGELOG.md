# Changelog

## [0.12.3](https://github.com/Exar-lab/Sistema_Biblioteca/compare/sistema-biblioteca-v0.12.2...sistema-biblioteca-v0.12.3) (2026-06-08)


### Bug Fixes

* **catalog:** bind book active flag for Oracle ([f665e9f](https://github.com/Exar-lab/Sistema_Biblioteca/commit/f665e9fc0d85645b3ba6b77ecae750a9664a0cde))

## [0.12.2](https://github.com/Exar-lab/Sistema_Biblioteca/compare/sistema-biblioteca-v0.12.1...sistema-biblioteca-v0.12.2) (2026-06-08)


### Bug Fixes

* **catalog:** preserve book authors and partial updates ([bf779fe](https://github.com/Exar-lab/Sistema_Biblioteca/commit/bf779fe5cf388fac1892bc4477374f3520a53035))
* **catalog:** preserve book authors and partial updates ([1f13386](https://github.com/Exar-lab/Sistema_Biblioteca/commit/1f133863d40713d490bfce2421559ea23863cf51))

## [0.12.1](https://github.com/Exar-lab/Sistema_Biblioteca/compare/sistema-biblioteca-v0.12.0...sistema-biblioteca-v0.12.1) (2026-06-08)


### Bug Fixes

* **catalog:** resolve stock_available AttributeError and missing confirm dialog ([7cf002f](https://github.com/Exar-lab/Sistema_Biblioteca/commit/7cf002fd3e8dd18728be00312009e31786548fc0))
* **catalog:** resolve stock_available AttributeError and missing confirm dialog ([90e6f2a](https://github.com/Exar-lab/Sistema_Biblioteca/commit/90e6f2aef16cee5e864cfc099677cc2aa36eb4ba))

## [0.12.0](https://github.com/Exar-lab/Sistema_Biblioteca/compare/sistema-biblioteca-v0.11.0...sistema-biblioteca-v0.12.0) (2026-06-08)


### Features

* **loans:** add self-service loan request for authenticated users ([8dcd92a](https://github.com/Exar-lab/Sistema_Biblioteca/commit/8dcd92a083ca970f264b5987d2201cc17a70d1c3))
* **loans:** user self-service loan request + API/return bug fixes ([01b1c82](https://github.com/Exar-lab/Sistema_Biblioteca/commit/01b1c8227605f87c317423fd6c3d2d77bd2a2ba4))


### Bug Fixes

* **api:** use relative API_BASE, fix return flow and Oracle type issues ([719a0da](https://github.com/Exar-lab/Sistema_Biblioteca/commit/719a0da4063f3d0ced6defec3becc36b4459d727))

## [0.11.0](https://github.com/Exar-lab/Sistema_Biblioteca/compare/sistema-biblioteca-v0.10.2...sistema-biblioteca-v0.11.0) (2026-06-08)


### Features

* **frontend:** refresh login and registration UI ([453d28f](https://github.com/Exar-lab/Sistema_Biblioteca/commit/453d28fb84b9d7647a43a9abdd02e4b112745295))
* **frontend:** refresh login and registration UI ([fa8f242](https://github.com/Exar-lab/Sistema_Biblioteca/commit/fa8f242feb77a20e31c3cac99d40718ee5b79515))
* **seed:** add deterministic demo data ([df871f2](https://github.com/Exar-lab/Sistema_Biblioteca/commit/df871f210d9e2fcad6b287d50842135e489d2623))
* **seed:** add deterministic demo data ([a59c767](https://github.com/Exar-lab/Sistema_Biblioteca/commit/a59c767683a2e9aef659215bc4d9472376a159fe))

## [0.10.2](https://github.com/Exar-lab/Sistema_Biblioteca/compare/sistema-biblioteca-v0.10.1...sistema-biblioteca-v0.10.2) (2026-06-07)


### Bug Fixes

* **frontend:** serve static app at root ([5fbb6fe](https://github.com/Exar-lab/Sistema_Biblioteca/commit/5fbb6feff2f4c969f8b601a0942819d47c27569a))
* **frontend:** serve static app at root ([b071000](https://github.com/Exar-lab/Sistema_Biblioteca/commit/b0710005c6bf8b135ba88ef5498436eda9c3ea32))

## [0.10.1](https://github.com/Exar-lab/Sistema_Biblioteca/compare/sistema-biblioteca-v0.10.0...sistema-biblioteca-v0.10.1) (2026-06-07)


### Bug Fixes

* **frontend:** harden static app delivery ([66e5350](https://github.com/Exar-lab/Sistema_Biblioteca/commit/66e53507127edd07ef81f5c18b6d82475368b23e))
* **frontend:** harden static app delivery ([4d1ada3](https://github.com/Exar-lab/Sistema_Biblioteca/commit/4d1ada35c8230e2d61a99a024040f7cb7fda28fd))

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
