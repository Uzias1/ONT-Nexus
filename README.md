# ONT Tester NEXUS

ONT Tester NEXUS es un sistema de pruebas automatizadas para dispositivos **ONT (Optical Network Terminal)** diseñado para ejecutar **múltiples pruebas en paralelo** sobre varios equipos conectados a una misma estación de test.

A diferencia del ONT Tester original, el cual está diseñado para probar **un solo equipo a la vez**, ONT Tester NEXUS permite ejecutar pruebas simultáneas sobre **hasta 24 dispositivos ONT**, aprovechando un switch Gigabit de 24 puertos y una arquitectura basada en workers concurrentes.

El objetivo principal del proyecto es **maximizar velocidad y capacidad de pruebas en entornos de laboratorio o manufactura**, reduciendo la intervención manual y aumentando el throughput de dispositivos evaluados.

---

# Acerca de

ONT Tester NEXUS es una evolución de ONT Tester, cumple con funciones similares, como lo son la ejecución de pruebas automatizadas para dispositivos ONT; sin embargo, tiene un par de diferencias, las cuales se listan a continuación:

- **Pruebas unitarias:** En ONT NEXUS no se pueden realizar pruebas unitarias, debido a que se busca priorizar velocidad y cantidad de equipos.
- **Cantidad de equipos:** En ONT NEXUS se podrán realizar pruebas automatizadas para **24 dispositivos ONT de manera simultánea** (debido a la capacidad del switch), a diferencia del ONT Tester original que solo puede testear **1 a la vez**.
- **Interfaz:** Debido a la cantidad de equipos la interfaz tendrá los **elementos mínimos necesarios** para mostrar funcionamiento y rendimiento de las ONT.
- **Montado físico:** Se requerirá de una **estructura física organizada** para acomodar los dispositivos ONT y el propio ONT NEXUS.

---

# Características principales

- Ejecución de pruebas automatizadas para dispositivos ONT
- Soporte para múltiples fabricantes (ZTE, Huawei, FiberHome)
- Ejecución de **hasta 24 pruebas simultáneas**
- Arquitectura basada en **workers concurrentes**
- Descubrimiento automático de dispositivos en red
- Monitoreo de conectividad de dispositivos
- Interfaz minimalista enfocada en estado y rendimiento
- Arquitectura modular para facilitar mantenimiento y escalabilidad

---

# Pruebas automatizadas

Las pruebas realizadas por ONT Tester NEXUS incluyen:

- **Ping**
- **Factory Reset**
- **Actualización de software**
- **Prueba de puerto USB**
- **Prueba de potencia óptica (fibra)**
- **Validación de redes WiFi**

Estas pruebas se ejecutan mediante automatización de interfaz web utilizando **Selenium**.

---

# Arquitectura del sistema

El proyecto está organizado en múltiples capas para separar responsabilidades:

UI (interfaz)
│
Application Layer
│
Domain Logic
│
Infrastructure
│
Workers / Concurrency


Esto permite:

- Separar lógica de negocio de la interfaz
- Facilitar pruebas unitarias
- Agregar nuevos fabricantes de ONT sin modificar el núcleo
- Escalar el sistema a más estaciones en el futuro

---

# Estructura del proyecto
app/
├─ ui/ # Interfaz gráfica
├─ application/ # Casos de uso y servicios
├─ domain/ # Entidades y reglas de negocio
├─ infrastructure/ # Integraciones (network, selenium, vendors)
├─ workers/ # Workers concurrentes
└─ shared/ # Utilidades comunes

tests/
├─ unit/
└─ integration/

data/
├─ config/
├─ logs/
└─ results/

---

# Requisitos

- Python **3.11+**
- Selenium
- Chrome / Chromium
- ChromeDriver
- Switch Gigabit de **24 puertos**
- Dispositivos ONT compatibles

---

# Instalación

Clonar el repositorio:

```bash
git clone https://github.com/tu-org/ont-tester-nexus.git
cd ont-tester-nexus
```

Instalar dependencias:
```bash
pip install -r requirements.txt
```

Iniciar el sistema:
```bash
python main.py
```

# Operación básica

1. Conectar los dispositivos ONT al switch.
2. Iniciar ONT Tester NEXUS.
3. El sistema detectará automáticamente los dispositivos disponibles.
4. Se asignarán workers para ejecutar las pruebas.
5. La interfaz mostrará el estado de cada dispositivo.

# Interfaz

La interfaz está diseñada para ser minimalista, enfocada en:

- Estado de cada dispositivo
- Progreso de pruebas
- Alertas de fallo
- Conectividad