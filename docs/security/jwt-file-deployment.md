# Despliegue de autenticación con claves PEM

La plantilla `.env.example` documenta las variables de `core/.env`; no contiene credenciales reales. Los valores vigentes de base de datos, correo, AWS y otros servicios deben conservarse. No sustituya un archivo existente por la plantilla.

## Preparación por el responsable del servidor

1. Conservar `DEBUG=False` y configurar `AUTH_SECURITY_ENVIRONMENT=production` y `AUTH_JWT_ALGORITHM=RS256` en la configuración efectiva del backend. Con `DEBUG=False` se aplica la política estricta también en desarrollo.
2. Mantener `AUTH_CAPTCHA_ENABLED=False` hasta integrar y validar Turnstile en ambos lados. El backend conserva los controles de Redis, límite de intentos y bloqueo. Si más adelante se activa, configurar también el secreto, el hostname correspondiente y la clave pública del frontend.
3. Confirmar las rutas absolutas en el servidor de los PEM privado y público. Son archivos distintos para desarrollo y producción. Mantenerlos fuera del repositorio y del contexto de build; comprobar que Docker pueda leerlos sin hacerlos públicos. El responsable conserva propiedad y permisos adecuados.
4. Crear en el directorio de despliegue un archivo local **`jwt-paths.env`**, que no se versiona ni se copia a las imágenes. Contiene solo las rutas del servidor, no las claves:

   ```dotenv
   JWT_PRIVATE_KEY_HOST_PATH=/RUTA/REAL/DEL/SERVIDOR/jwt-private.pem
   JWT_PUBLIC_KEY_HOST_PATH=/RUTA/REAL/DEL/SERVIDOR/jwt-public.pem
   ```

   Sustituir ambas rutas. No editar el `docker.env` versionado para este fin. Compose expone los archivos, en modo de solo lectura, a los cuatro servicios bajo `/run/secrets/jwt-private.pem` y `/run/secrets/jwt-public.pem`. Las variables `AUTH_JWT_SIGNING_KEY_FILE` y `AUTH_JWT_VERIFYING_KEY_FILE` se proporcionan automáticamente a esos servicios.
5. Para desarrollo, configurar `AUTH_TURNSTILE_EXPECTED_HOSTNAMES=devapp.smartevolution.com.co`; para producción, `app.smartevolution.com.co`. `AUTH_TURNSTILE_SECRET_KEY` se configura privadamente por ambiente, pero no es necesaria mientras `AUTH_CAPTCHA_ENABLED=False`. No compartir ni subir los valores reales.

El entorno de proceso tiene prioridad sobre `core/.env`; comprobar que no exista un valor contradictorio en `docker.env` o `docker.production.env`. Si se define una variable `*_FILE`, django-environ lee ese archivo en lugar del valor directo. No ejecutar `docker compose config` sin `--quiet`, ya que podría mostrar variables sensibles.

## Preflight y migraciones

Ambos workflows usan `scripts/deploy_compose.sh`. Este valida los archivos, cambios rastreados, configuración de Compose, arranque de Django, pareja de claves, política RS256 y conexión a Redis antes de recrear servicios. También comprueba el estado de migraciones. Una configuración ausente o migración pendiente detiene el despliegue; no se reemplazan los archivos de entorno ni se eliminan volúmenes.

La migración `authentication.0015_authentication_security_audit` puede estar pendiente porque el override anterior omitía `entrypoint.sh`. Antes de aplicar migraciones, revisar su plan y respaldo con el equipo. Si el preflight informa que hay migraciones pendientes, el responsable debe aplicar **solo las migraciones revisadas** siguiendo el procedimiento de la empresa y volver a ejecutar el workflow. El preflight también falla si no puede conectarse a la base; consultar el error sin compartir credenciales.

Para verificar el override sin imprimir la configuración, desde el directorio de despliegue:

```sh
sudo docker compose --env-file docker.env --env-file jwt-paths.env -f docker-compose.yml -f docker-compose.development.yml config --quiet
```

En producción se usa `docker-compose.production.yml` en lugar del override de desarrollo y se conserva `docker.production.env`. No se ejecuta `up`, `down` ni migración durante esta comprobación.
