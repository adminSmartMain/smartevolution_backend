Proyecto BACKEND en Django - SMART EVOLUTION

Este repositorio contiene un proyecto desarrollado en Django.
Instalación y Ejecución
1. Instalación Manual

Asegúrate de tener instalado Python y pip en tu sistema. Se recomienda usar un entorno virtual para la instalación de las dependencias del proyecto.
Paso 1: Clonar el Repositorio

bash

git clone <URL_DEL_REPOSITORIO>
cd <NOMBRE_DEL_DIRECTORIO>

Paso 2: Configurar el Entorno Virtual (opcional pero recomendado)

bash

# Instalar virtualenv si no está instalado
sudo apt install python3 python3-pip python3-virtualenv

# Crear un entorno virtual
virtualenv env

# Activar el entorno virtual (Unix o MacOS)
source env/bin/activate

Paso 3: Instalar Dependencias

pip install -r requirements.txt

Paso 4: Configurar la Base de Datos
Asegúrate de tener configurada tu base de datos en el archivo .env dentro de core/.env

python manage.py migrate

Paso 7: Ejecutar el Servidor de Desarrollo

python manage.py runserver

HECHO...
El servidor estará disponible en http://localhost:8000.

2. Ejecución usando Docker

Asegúrate de tener Docker instalado en tu sistema.
Paso 1: Clonar el Repositorio

bash

git clone <URL_DEL_REPOSITORIO>
cd <NOMBRE_DEL_DIRECTORIO>

Paso 2: Construir y Ejecutar el Contenedor

sudo docker compose --env-file docker.env up --build -d

Esto construirá la imagen del contenedor y comenzará a ejecutar los servicios definidos en docker-compose.yml. El contenedor estará disponible en http://localhost:8000 para el servidor de desarrollo del proyecto.

Detener y Eliminar Contenedores

Para detener los contenedores Docker, ejecuta:
docker-compose down