# Pruebas locales

Las pruebas no usan `core/.env`, RDS ni Redis locales. Levantan MySQL y Redis
efímeros en Docker con datos de prueba.

```bash
docker compose -f docker-compose.qa.yml up --build --abort-on-container-exit --exit-code-from test
docker compose -f docker-compose.qa.yml down --volumes
```

Usar exactamente `docker-compose.qa.yml`. El archivo histórico
`docker-compose.test.yml` no inicia MySQL ni Redis y por eso las pruebas de
autenticación, usuarios y recuperación de contraseña no pueden conectarse a la
base de datos de prueba.

El contenedor de pruebas espera explícitamente a MySQL y Redis antes de iniciar
Pytest. Esto evita la carrera de arranque que puede ocurrir aunque Docker ya
haya creado los contenedores.

También inicializa permisos para que Django cree y elimine
`test_smartevolution_test`. Es una base efímera del contenedor de QA, no una
credencial ni un permiso usado por los entornos reales.

Para ejecutar solo una prueba, reemplazar el comando del servicio `test`:

```bash
docker compose -f docker-compose.qa.yml run --rm test pytest apps/operation/tests/test_penny_allocation.py
```

El workflow de GitHub ejecuta el mismo conjunto de pruebas con MySQL y Redis de
GitHub Actions. No realiza despliegues.
