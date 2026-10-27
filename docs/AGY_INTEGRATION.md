# Manual de Integración y Extensión: FreeLingo + Antigravity CLI (`agy`)

> **Documento de uso personal para Dan**  
> **Repositorio local:** `/home/dan/Documentos/proyectos/freelingo-agy`  
> **Repositorio remoto (Fork):** `https://github.com/Daniel-Cossio/freelingo.git`  
> **Repositorio oficial (Upstream):** `https://github.com/artcc/freelingo.git`  

---

## 1. Visión General y Motivación

[FreeLingo](https://github.com/artcc/freelingo) es una plataforma open-source de aprendizaje de idiomas alineada con el marco europeo (MCER A1–C2). De origen, requiere APIs de pago (OpenAI, Anthropic, DeepSeek) o servidores de Ollama.

**El objetivo de este fork personal** es sustituir la dependencia de APIs comerciales por **Antigravity CLI (`agy`)**, el agente CLI instalado localmente en tu sistema (`/home/dan/.local/bin/agy`).

### Ventajas de esta integración:
1. **Coste cero en APIs:** Utiliza los modelos de Google DeepMind (Gemini 4 Argon, Gemini 3.8 Flash) y otros disponibles en tu entorno sin facturación por token.
2. **Razonamiento avanzado en idiomas:** Excelente comprensión gramatical, deducción pedagógica y generación estructurada de ejercicios en formato JSON.
3. **Privacidad total:** El control de datos y el flujo de comunicación se mantienen en tu estación de trabajo (CachyOS).
4. **Compatibilidad con upstream:** Las modificaciones en el código original se redujeron a únicamente **16 líneas** en dos archivos centrales, permitiendo incorporar futuras actualizaciones oficiales sin conflictos de Git.

---

## 2. Arquitectura del Sistema

El sistema implementa una **arquitectura híbrida**:
* **Contenedores Docker (Aislados):** Base de datos relacional (PostgreSQL 16) y caché/cola en memoria (Redis 7). No dejan residuos en el sistema operativo host.
* **Procesos en Host (CachyOS):** El backend (FastAPI en Python 3.14) y el frontend (Next.js 16) se ejecutan directamente en tu espacio de usuario, lo que les permite acceder sin barreras de contenedor al binario `/home/dan/.local/bin/agy`.

```mermaid
flowchart TD
    subgraph Browser ["Navegador Web (Usuario)"]
        UI["Interfaz Next.js 16\n(http://localhost:3000)"]
    end

    subgraph Host ["CachyOS Host (Procesos Locales)"]
        FrontendDev["Servidor Dev Next.js (Puerto 3000)"]
        BackendDev["FastAPI Uvicorn (Puerto 8000)"]
        LLMAdapter["LLMAdapter\n(app/services/llm_adapter.py)"]
        AGYClient["AntigravityLLMClient\n(app/services/llm_antigravity.py)"]
        AGYBin["/home/dan/.local/bin/agy\n-p '<prompt>' --output-format stream-json"]
        GeminiCore["Modelos IA: Gemini 3.8 Flash / Gemini 4"]
    end

    subgraph Docker ["Docker (docker-compose.infra.yml)"]
        PG["PostgreSQL 16\n(127.0.0.1:5432 / 29 tablas)"]
        RD["Redis 7\n(127.0.0.1:6379)"]
    end

    UI <-->|HTTP / WebSocket / SSE| FrontendDev
    FrontendDev <-->|API Calls| BackendDev
    BackendDev <--> PG
    BackendDev <--> RD
    BackendDev --> LLMAdapter
    LLMAdapter -->|"provider == 'antigravity'"| AGYClient
    AGYClient -->|Subproceso asíncrono| AGYBin
    AGYBin --> GeminiCore
```

---

## 3. Registro Exhaustivo de Archivos Modificados y Creados

### Archivos Nuevos

#### 1. `backend/app/services/llm_antigravity.py`
Es el núcleo de la integración. Implementa:
* **`AntigravityStreamChunk`:** Simula la estructura esperada por FreeLingo (`chunk.choices[0].delta.content`) y a la vez implementa `__str__` para consumidores directos de texto.
* **`AntigravityStream`:** Consumidor asíncrono línea por línea del protocolo NDJSON de `agy`. Captura eventos:
  * `step_update`: Extrae `text_delta` para streaming inmediato en el chat del tutor. Captura `usage` (tokens de entrada/salida).
  * `result`: Valida el estado de finalización (`SUCCESS`).
* **`AntigravityLLMClient`:**
  * Formatea listas de mensajes (`system`, `user`, `assistant`) en un prompt contextual estructurado.
  * Lanza el subproceso con los flags requeridos:
    ```bash
    /home/dan/.local/bin/agy -p "<prompt>" --output-format stream-json --disable-slash-commands [--model <model>] [--effort <effort>]
    ```
  * **Sanitización de esfuerzo (`model_has_effort`):** Detecta automáticamente si el modelo ya especifica un nivel de esfuerzo (ej. `gemini-3.8-flash-high`) para evitar el conflicto con el flag `--effort`.
  * Soporta tanto el modo streaming (`stream=True`) como la recolección completa para generación de JSON (`stream=False`).

#### 2. `docker-compose.infra.yml`
Define exclusivamente los servicios de datos necesarios para el backend:
* **`postgres`:** Imagen `postgres:16-alpine`, exponiendo el puerto `127.0.0.1:5432`. Almacena datos en el volumen Docker `freelingo_pg_data`.
* **`redis`:** Imagen `redis:7-alpine`, exponiendo el puerto `127.0.0.1:6379`. Almacena datos en el volumen Docker `freelingo_redis_data`.

#### 3. `.env` (en raíz) y `backend/.env`
Archivo de variables de entorno del backend:
```ini
DATABASE_URL=postgresql+asyncpg://freelingo:freelingodevpassword@localhost:5432/freelingo
REDIS_URL=redis://:freelingoredispassword@localhost:6379/0
SECRET_KEY=94c8b74e8932b704e6c1e95fa97f58bb74944a95ef3950ef9c09c2a74c2d3648
LLM_PROVIDER=antigravity
ANTIGRAVITY_BIN_PATH=/home/dan/.local/bin/agy
ANTIGRAVITY_MODEL=gemini-3.8-flash-high
ANTIGRAVITY_EFFORT=
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
ALLOW_REGISTRATION=true
FIRST_USER_IS_ADMIN=true
AVAILABLE_TARGET_LANGUAGES=["en-US","en-GB","fr-FR","de-DE","it-IT","pt-PT","zh-CN","ja-JP"]
LOG_LEVEL=INFO
```

#### 4. `frontend/.env.local`
Configuración del frontend Next.js:
```ini
BACKEND_URL=http://127.0.0.1:8000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### 5. `start-all.sh` y `stop-all.sh`
* `start-all.sh`: Script interactivo ejecutable que:
  1. Verifica y levanta PostgreSQL y Redis en Docker.
  2. Activa el `.venv` y arranca FastAPI en `127.0.0.1:8000` con recarga automática.
  3. Arranca el frontend Next.js en `http://localhost:3000`.
  4. Implementa una trampa de señales (`trap cleanup INT TERM`) para matar los subprocesos de Node y Python ordenadamente con `Ctrl + C`.
* `stop-all.sh`: Detiene los contenedores Docker cuando no vayas a usar la aplicación.

#### 6. `scripts/sync-upstream.sh`
Automatiza la sincronización con el repositorio oficial:
```bash
git fetch upstream
git merge upstream/main --no-edit
```

#### 7. `test_agy_adapter.py`
Suite de validación que prueba:
* Test 1: Llamada directa síncrona a `agy`.
* Test 2: Streaming en tiempo real y lectura de tokens.
* Test 3: Llamada a través de `LLMAdapter` con parseo de JSON (`parse_llm_json`).

---

### Archivos Modificados del Repositorio Oficial

#### 1. `backend/app/services/llm_adapter.py`
* **En `__init__`:** Se registró el proveedor:
  ```python
  elif self.provider in ("antigravity", "agy"):
      from app.services.llm_antigravity import AntigravityLLMClient
      self.client = AntigravityLLMClient(
          binary_path=settings.ANTIGRAVITY_BIN_PATH,
          model=settings.ANTIGRAVITY_MODEL,
          effort=settings.ANTIGRAVITY_EFFORT,
      )
      self.model = settings.ANTIGRAVITY_MODEL
  ```
* **En `chat()`:** Se configuró el retorno directo del stream para no re-envolverlo innecesariamente:
  ```python
  if self.provider in ("openai", "antigravity", "agy"):
      return result
  ```
* **En `_do_chat()`:** Se redirigió la ejecución a `self.client.do_chat(...)`:
  ```python
  if self.provider in ("antigravity", "agy"):
      return await self.client.do_chat(
          messages,
          stream=stream,
          request_timeout=request_timeout,
      )
  ```

#### 2. `backend/app/core/config.py`
Se agregaron las 3 variables de configuración con sus valores predeterminados:
```python
ANTIGRAVITY_BIN_PATH: str = "/home/dan/.local/bin/agy"
ANTIGRAVITY_MODEL: str = "gemini-3.8-flash-high"
ANTIGRAVITY_EFFORT: str = ""
```

#### 3. `backend/alembic.ini`
Se ajustó la ruta relativa del script de migraciones:
* **Antes:** `script_location = /app/alembic` (solo funcionaba dentro del contenedor Docker oficial).
* **Ahora:** `script_location = %(here)s/alembic` (funciona tanto en local como en Docker).

---

## 4. Guía de Operación Diaria

### Poner en marcha la plataforma:
```bash
cd /home/dan/Documentos/proyectos/freelingo-agy
./start-all.sh
```
* **Acceso web:** [http://localhost:3000](http://localhost:3000)
* **API Documentación Swagger:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* Para detener todo: presiona `Ctrl + C`.

### Detener contenedores Docker en segundo plano:
```bash
./stop-all.sh
```

### Ejecutar pruebas del adaptador `agy`:
```bash
cd /home/dan/Documentos/proyectos/freelingo-agy
source .venv/bin/activate
python test_agy_adapter.py
```

---

## 5. Guía para Futuras Adiciones y Modificaciones

Esta sección contiene las instrucciones paso a paso para cuando desees personalizar o ampliar tu instalación:

### Adición 1: Cambiar de Modelo de Inteligencia Artificial

Si deseas cambiar el modelo que usa FreeLingo (por ejemplo, para probar un modelo más reflexivo o más rápido):
1. Consulta los modelos disponibles en tu CLI:
   ```bash
   agy models
   ```
2. Abre el archivo `.env` en la raíz del proyecto y en `backend/.env`.
3. Modifica la variable `ANTIGRAVITY_MODEL`:
   * Para máxima velocidad y razonamiento diario: `gemini-3.8-flash-high` (predeterminado).
   * Para explicaciones de máxima profundidad o textos literarios: `gemini-4-argon-high`.
   * Para probar modelos de Anthropic si los tienes activos: `claude-sonnet-5-5-medium`.
4. Reinicia los servidores (`Ctrl + C` y `./start-all.sh`).

---

### Adición 2: Añadir Nuevos Idiomas para Estudiar

FreeLingo tiene soporte para múltiples idiomas mediante códigos BCP-47.
Para habilitar o deshabilitar idiomas:
1. Abre `.env` y busca la variable:
   ```ini
   AVAILABLE_TARGET_LANGUAGES=["en-US","en-GB","fr-FR","de-DE","it-IT","pt-PT","zh-CN","ja-JP"]
   ```
2. Códigos soportados por el currículum de FreeLingo:
   * `en-US` / `en-GB` (Inglés americano / británico)
   * `es-ES` (Español)
   * `fr-FR` (Francés)
   * `de-DE` (Alemán)
   * `it-IT` (Italiano)
   * `pt-PT` (Portugués)
   * `zh-CN` (Chino simplificado)
   * `ja-JP` (Japonés)
   * `ko-KR` (Coreano)
3. Guarda el archivo y reinicia el backend.

---

### Adición 3: Activación de Voz Local (Síntesis TTS y Reconocimiento STT)

En esta primera fase hemos dejado el sistema operando en modo texto interactivo. Cuando desees activar el audio para que el tutor *Lingu* hable y evalúe tu pronunciación:
1. **Motores soportados por FreeLingo:**
   * **STT (Escuchar):** `faster-whisper`
   * **TTS (Hablar):** `Kokoro-FastAPI`
2. **Cómo agregarlos a Docker:**
   Puedes añadir los dos servicios al archivo `docker-compose.infra.yml`:
   ```yaml
   kokoro:
     image: ghcr.io/remsky/kokoro-fastapi-cpu:latest
     container_name: freelingo-kokoro
     ports:
       - "127.0.0.1:8880:8880"

   whisper:
     image: fedirz/faster-whisper-server:latest-cpu
     container_name: freelingo-whisper
     ports:
       - "127.0.0.1:9000:9000"
   ```
3. En tu `.env`:
   ```ini
   TTS_PROVIDER=local
   TTS_BASE_URL=http://localhost:8880
   STT_PROVIDER=local
   STT_BASE_URL=http://localhost:9000
   ```

---

### Adición 4: Personalizar la Personalidad del Tutor (*Lingu*)

Las instrucciones del tutor conversacional residen en:
`/home/dan/Documentos/proyectos/freelingo-agy/backend/app/services/prompts/`
* `conversation_pipeline.py`: Define el prompt de sistema del tutor *Lingu*.
* Puedes ajustar su nivel de corrección, añadir reglas de conversación socrática o modificar la frecuencia con la que introduce vocabulario nuevo.

---

### Adición 5: Sincronizar Nuevas Funciones del Proyecto Oficial (`upstream`)

Para traer las últimas mejoras publicadas en el repositorio oficial de FreeLingo sin tocar tus adaptaciones:

1. Ejecuta el script automatizado:
   ```bash
   cd /home/dan/Documentos/proyectos/freelingo-agy
   ./scripts/sync-upstream.sh
   ```
2. El script descargará `upstream/main` y lo fusionará con tu rama actual.
3. Dado que nuestros cambios en archivos oficiales son mínimos (16 líneas), Git resolverá la fusión automáticamente.
4. Si todo está correcto, sube la actualización a tu GitHub personal:
   ```bash
   git push origin main
   ```

---

## 6. Resolución de Problemas Frecuentes (Troubleshooting)

### Error de permisos de Docker (`permission denied ... /var/run/docker.sock`)
Si ejecutas comandos de Docker y obtienes este error en una nueva terminal de Konsole:
* **Causa:** La sesión de terminal no ha recargado el nuevo grupo `docker`.
* **Solución:** Ejecuta `newgrp docker` en esa terminal o reinicia la sesión gráfica de KDE.

### Conflicto de puerto 5432 o 6379 ocupado
* **Causa:** Hay otra instancia de PostgreSQL o Redis corriendo en la máquina.
* **Solución:** Verifica qué proceso ocupa el puerto con `ss -tulpn | grep -E "5432|6379"` y detén el servicio conflictivo.

### Base de datos no sincronizada tras un cambio de modelos
Si añades nuevas tablas o el proyecto oficial actualiza el esquema de base de datos:
```bash
cd /home/dan/Documentos/proyectos/freelingo-agy/backend
source ../.venv/bin/activate
PYTHONPATH=. alembic upgrade head
```
