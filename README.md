# FreeLingo — Edición Personal con Antigravity CLI (`agy`)

![License](https://img.shields.io/badge/license-AGPL%20v3-blue?style=flat-square)
![Next.js](https://img.shields.io/badge/next.js-16-black?style=flat-square)
![Python](https://img.shields.io/badge/python-3.14-blue?style=flat-square)
![Platform](https://img.shields.io/badge/engine-Antigravity%20CLI%20(agy)-orange?style=flat-square)

<p align="left">
  <img src="assets/logo_large.png" alt="FreeLingo logo" width="320" />
</p>

Plataforma integral de aprendizaje y autoestudio de idiomas con Inteligencia Artificial, adaptada para ejecutarse 100% en local sobre Linux (CachyOS) utilizando **Antigravity CLI (`agy`)** como motor de razonamiento (LLM).

> 📌 **Nota del Proyecto:** Este repositorio es un **fork de uso estrictamente personal** creado por **Dan** con fines de autoestudio, retención de vocabulario y experimentación técnica.  
> Proyecto original de código abierto: [artcc/freelingo](https://github.com/artcc/freelingo) (licenciado bajo AGPL-3.0).

---

## 🚀 Inicio Rápido (Comando Global en PATH)

Puedes controlar FreeLingo desde **cualquier terminal** de tu sistema gracias al comando `freelingo` instalado en `~/.local/bin/freelingo`:

```bash
# Iniciar la plataforma en segundo plano (Docker + Backend + Frontend):
freelingo on

# Consultar el estado en vivo de los servicios:
freelingo status

# Abrir en el navegador:
freelingo open    # o visita http://localhost:3000

# Ver logs en tiempo real:
freelingo logs backend
freelingo logs frontend

# Detener todos los servicios y contenedores:
freelingo off
```

---

## 🧠 ¿Qué hace especial esta edición con Antigravity CLI?

A diferencia de la versión original que requiere claves de API comerciales de pago (OpenAI, Anthropic, DeepSeek) o hardware GPU masivo para servidores de Ollama:

1. **Cero costes de API:** Se conecta directamente al binario local `/home/dan/.local/bin/agy`, utilizando los modelos avanzados de Google DeepMind (Gemini 3.8 Flash, Gemini 4 Argon) ya configurados en tu equipo.
2. **Streaming en tiempo real:** Soporte completo de respuestas fragmento a fragmento (`stream-json`) para que el tutor conversacional responda de manera instantánea y fluida.
3. **Generación estructurada:** Los diagnósticos de nivel (A1–C2), cuestionarios de repaso y lecciones gramaticales se generan y validan en esquemas JSON nativos.
4. **Infraestructura ligera y aislada:** Base de datos relacional y caché en contenedores Docker mínimos, ejecutando el backend y frontend nativamente en el host.

> 📖 **Manual de Integración y Guía de Extensión:**  
> Consulta [`docs/AGY_INTEGRATION.md`](docs/AGY_INTEGRATION.md) para ver la arquitectura detallada, el código del adaptador, guías para activar voz local con Whisper/Kokoro y sincronización con el repositorio oficial.

---

## 🎯 Características de Estudio

* **Currículum alineado con el MCER (A1 a C2):** Diagnóstico inicial de nivel y planificación de estudio en bloques semanales de intensidad personalizable.
* **Tutor interactivo (*Lingu*):** Práctica conversacional continua con explicaciones contextuales y memoria de errores comunes.
* **Repetición espaciada (SRS):** Generación automática de tarjetas de vocabulario utilizando el algoritmo SM-2.
* **Mini-juegos didácticos:** Modo *Error Detective* para detectar y corregir fallos gramaticales típicos.
* **Múltiples idiomas disponibles:** Inglés (US/UK), Francés, Alemán, Italiano, Portugués, Japonés, Chino simplificado y Español.

---

## 🛠️ Stack Tecnológico

* **Frontend:** Next.js 16 (App Router), React, Tailwind CSS, shadcn/ui.
* **Backend:** FastAPI (Python 3.14), SQLAlchemy asíncrono, Alembic, Pydantic v2.
* **Cerebro (LLM):** Antigravity CLI (`agy`) ➔ Modelos Gemini.
* **Datos:** PostgreSQL 16 y Redis 7 (vía Docker Compose).
* **Entorno:** CachyOS / Linux con KDE Plasma 6 sobre Wayland.

---

## 🔄 Sincronización con el Repositorio Oficial

Para traer las últimas mejoras del repositorio oficial de FreeLingo sin perder tus adaptaciones de Antigravity:

```bash
./scripts/sync-upstream.sh
```
El script descarga y fusiona `upstream/main` de forma automática.
