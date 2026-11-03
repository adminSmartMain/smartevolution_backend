# Reporte de pruebas CI

Última verificación local: **66 pruebas backend aprobadas** con MySQL 8 y
Redis efímeros. La única advertencia actual procede de la dependencia externa
`PyPDF2` deprecada; no representa un fallo de una prueba.

## Backend — check `Backend tests`

El workflow ejecuta `python manage.py check` y después `pytest` con Python
3.11, MySQL 8 y Redis 7. No usa RDS, credenciales reales ni despliega nada.

| Área | Archivo(s) | Casos cubiertos |
| --- | --- | --- |
| Recuperación de contraseña | `apps/authentication/test_password_reset.py` | Solicitud, token, cambio de contraseña, token reutilizado, correo desconocido y enlace de frontend. |
| Autenticación y usuarios | `apps/authentication/tests.py`, `apps/authentication/tests/test_jwt_revocation.py`, `apps/authentication/tests/test_login_session_security.py` | Login válido/inválido, token vencido, validaciones de usuario y revocación de JWT. |
| Clientes y cuentas | `apps/client/tests/test_client_account_rules.py` | Campos obligatorios, documento de cliente activo duplicado, reutilización tras archivar y bloqueo de segunda cuenta primaria. |
| Facturas | `apps/bill/tests/test_xml_invoice_extraction.py`, `apps/bill/tests/test_bill_operation_lock.py` | XML `text/xml` y `application/xml` válidos; rechazo de PDF base64, XML malformado y base64 inválido; y bloqueo 409 al intentar editar una factura asociada a una preoperación. |
| Sincronización Billy | `apps/bill/test_billy.py`, `apps/bill/test_billy_guardrails.py` | Reintentos, polling, cliente, carga, límites globales y guardas de sincronización. |
| Notificaciones | `apps/notifications/tests.py` | Creación, lectura y comportamiento de notificaciones. |
| Asignación de centavos | `apps/operation/test_penny_allocation.py`, `apps/operation/tests/test_penny_allocation*.py` | Distribución, normalización, redondeo positivo/negativo, desbalances, filas vacías y resúmenes. |

## Frontend — check `Frontend checks`

El workflow ejecuta `npm ci`, `npm run lint`, `npm run build`, instala Chromium
y ejecuta Playwright. Si falla, adjunta el reporte de Playwright como artefacto.

| Archivo | Casos cubiertos |
| --- | --- |
| `tests/e2e/login.spec.js` | Renderizado de la pantalla de inicio de sesión y sus controles esenciales. |
| `tests/e2e/public-pages.spec.js` | Redirección desde raíz a login, validación de email/contraseña obligatorios y mínimos, y acceso público a recuperación de contraseña. |
| `tests/e2e/auth-flow.spec.js` | Error de credenciales, sesión exitosa, persistencia del token, navegación al dashboard y mostrar/ocultar contraseña. |
| `tests/e2e/password-recovery.spec.js` | Correo obligatorio, solicitud exitosa/fallida de recuperación, contraseñas no coincidentes y actualización con token válido. |
| `tests/e2e/route-and-bill-guards.spec.js` | Redirección sin sesión, bloqueo de facturas sin permiso y filtro XML del cargador de extracción. |

Actualmente son **15 pruebas E2E**. Usan respuestas API simuladas para que no
intenten iniciar sesión contra datos reales ni escriban en la base de datos.

## Límite actual y siguiente cobertura

El CI ya bloquea el merge si fallan el chequeo Django, las 66 pruebas backend,
lint, build o cualquiera de las 15 pruebas E2E. Las siguientes pruebas de
prioridad deben ser reglas de negocio: una factura asociada a una operación no
puede editarse, permisos por rol, importación de XML DIAN completo, campos
obligatorios y transiciones de estado de preoperaciones/operaciones.
