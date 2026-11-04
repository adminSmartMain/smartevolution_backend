# Estado actual de pruebas automatizadas

Fecha de verificación: **4 de noviembre de 2026**.

Este documento resume las pruebas incorporadas en las ramas `feature/quality-ci`
de backend y frontend. No realiza despliegues, no utiliza RDS y no modifica
datos reales.

## Resultado verificado

| Capa | Resultado local | Entorno |
| --- | --- | --- |
| Backend Django / Pytest | **80 de 80 aprobadas** | Python 3.11, MySQL 8 y Redis efímeros en Docker. |
| Frontend / Playwright | **19 de 19 aprobadas** | Compilación Next.js nueva y Chromium en el puerto local 3100. |

La ejecución backend tardó aproximadamente cuatro minutos. Presentó cuatro
advertencias no bloqueantes: una deprecación de `PyPDF2` y tres advertencias de
longitud de llave JWT usada solo en pruebas.

## Backend: 80 pruebas

| Área | Casos que cubre |
| --- | --- |
| Autenticación y sesión | Login válido e inválido, emisión de access/refresh token, token vencido, revocación por cambio de seguridad y validaciones de usuario. |
| Recuperación de contraseña | Solicitud de recuperación, token válido/vencido/reutilizado, correo inexistente y URL de retorno al frontend. |
| Clientes y cuentas | Campos obligatorios, documento activo duplicado, reutilización del documento tras archivar y una sola cuenta primaria por cliente. |
| Autorización | Un usuario sin el permiso de facturas recibe `403`; las rutas protegidas no aceptan una sesión inválida. |
| Facturas XML | Acepta XML válido de los tipos `text/xml` y `application/xml`; rechaza PDF, XML malformado y base64 inválido. |
| Facturas asociadas | Una factura asociada a una preoperación no se puede editar y responde `409 Conflict`. |
| Billy | Reintentos, polling, cliente, carga, límites globales y controles de sincronización. |
| Notificaciones | Creación, lectura y marcado de notificaciones. |
| Preoperaciones / operaciones | Asignación y redondeo de centavos COP, normalización, desbalances, filas vacías y resumen de liquidación. |
| Excel masivo | Fila válida, campos obligatorios vacíos y fracciones duplicadas o no consecutivas. |
| Depósitos y devoluciones | El depósito incrementa el saldo; la devolución descuenta monto y GM; una devolución mayor al saldo se rechaza sin cambiar la cuenta. |

Archivos principales: `apps/authentication/`, `apps/client/tests/`,
`apps/bill/tests/`, `apps/operation/tests/` y `apps/administration/tests/`.

### Ejecutar backend localmente

```powershell
cd backend2
docker compose -f docker-compose.qa.yml up --build --abort-on-container-exit --exit-code-from test
docker compose -f docker-compose.qa.yml down --volumes
```

El primer comando crea una base MySQL y Redis descartables para QA; no usa el
archivo `.env` ni la base local del desarrollador.

## Frontend: 19 pruebas E2E

| Archivo | Casos que cubre |
| --- | --- |
| `login.spec.js` | Renderizado de inicio de sesión y controles principales. |
| `public-pages.spec.js` | Raíz redirige a login; correo y contraseña obligatorios; recuperación pública. |
| `auth-flow.spec.js` | Credenciales rechazadas, login exitoso, token persistido, navegación al dashboard y mostrar/ocultar contraseña. |
| `password-recovery.spec.js` | Correo obligatorio, recuperación exitosa/fallida, contraseñas distintas y cambio con token válido. |
| `route-and-bill-guards.spec.js` | Redirección sin sesión, denegación de facturas sin permiso y selector de extracción limitado a XML. |
| `critical-workflows.spec.js` | Registro de cliente autorizado, asistente de cliente vacío marcado como incompleto, formulario de factura manual y preoperación autorizados; separa adjuntos manuales de la extracción XML. |

Las pruebas simulan las respuestas API necesarias. Por tanto validan interfaz,
navegación, validaciones y permisos sin crear clientes, facturas u operaciones
en una base real.

### Ejecutar frontend localmente

```powershell
cd frontend
npm ci
npm run build
$env:PLAYWRIGHT_PORT = '3100'
npm run test:e2e -- --workers=1
Remove-Item Env:PLAYWRIGHT_PORT
```

Para observar el navegador despacio:

```powershell
$env:PLAYWRIGHT_PORT = '3100'
$env:PLAYWRIGHT_SLOW_MO = '800'
npx playwright test --headed --workers=1
Remove-Item Env:PLAYWRIGHT_PORT
Remove-Item Env:PLAYWRIGHT_SLOW_MO
```

Para inspección paso a paso se puede reemplazar el último comando por:

```powershell
npx playwright test --debug --workers=1
```

## Reglas de merge en GitHub

Los checks que deben configurarse como obligatorios en las protecciones de
`development` y `main` son exactamente:

- `Backend tests`
- `Frontend checks`

El backend ejecuta `python manage.py check` y Pytest. El frontend ejecuta
`npm ci`, lint, compilación, Chromium y Playwright. Un fallo en cualquiera de
ellos debe impedir el merge.

## Cobertura pendiente prioritaria

La base ya protege las reglas más riesgosas incorporadas hasta ahora. Los
siguientes incrementos deben enfocarse en recorridos completos con datos de
prueba: creación válida de cliente/cuenta, creación y asociación de factura,
transiciones aprobar/rechazar de preoperaciones, importación Excel end-to-end,
recaudos y navegación visible por cada rol real.
