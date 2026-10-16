# Programa web Python — Caso 1: Apolo 11

Aplicación local para reproducir el análisis del informe final de Estadística y Probabilidades. El programa trabaja desde una sola tabla de 24 escenarios pareados y automatiza T1–T7.

## Qué incluye

- T1: distribuciones de frecuencia de A y B con filas de totales y tabla formal de carga.
- T2–T3: tendencia central, cuantiles, posición, dispersión y reglas técnicas.
- T4: contingencia F–H, probabilidades, independencia, reposición, detalle de numeradores y denominadores, control del denominador cero y sesgo por exclusión.
- T5: valor esperado y detención en la primera barrera.
- T6: simulación reproducible con NumPy PCG64 y semilla 321.
- T7: recomendación B, evidencias, limitación y mejora verificable.
- Tabla original descargable como CSV, impresión y once autocomprobaciones visibles.

## Requisitos

- Python 3.10 o posterior.
- NumPy 1.24 o posterior.

Para instalar NumPy si deseas usar una instalación propia de Python:

```powershell
python -m pip install -r requirements.txt
```

## Ejecutar

En Windows, haz doble clic en `run_app.bat` desde el Explorador de archivos. El iniciador abre el navegador automáticamente y busca Python en este orden:

1. El entorno virtual `.venv` del proyecto.
2. Una instalación normal de `py`, `python` o `python3`.
3. El Python incluido con Codex.

También puedes abrir PowerShell en esta carpeta y ejecutar:

```powershell
.\start_app.ps1
```

En este equipo, el lanzador abre la aplicación en `http://192.168.56.1:8765` mediante el adaptador virtual privado autorizado. Mantén abierta la ventana del servidor. Para detenerla, vuelve a esa ventana y presiona `Ctrl+C`.

> Si trabajas dentro de una terminal aislada de Codex, el navegador externo puede no alcanzar `localhost`. En ese caso, ejecuta `run_app.bat` con doble clic desde el Explorador de archivos de Windows.

### Ejecutar desde VS Code

Abre como carpeta raíz `EyP_Parcial`. El proyecto contiene una configuración en `.vscode` que selecciona automáticamente el Python funcional con NumPy.

- Pulsa `F5` y elige **Caso 1: abrir aplicación web**.
- También puedes usar **Terminal → Run Task → Abrir programa web Caso 1**.
- Si utilizas la extensión Code Runner, el botón **Run Code** también queda asociado al mismo intérprete.

Mantén abierta la terminal del servidor mientras usas la página. Para detenerlo, presiona `Ctrl+C`.

## Ejecutar pruebas

```powershell
python -m unittest discover -s tests -v
```

Las pruebas verifican datos, límites de clase, medidas descriptivas, multimodas, D9/P90, varianza muestral, probabilidades condicionales (incluido denominador cero), sesgo de exclusión, detención y resultados oficiales de la simulación.

## Publicar para acceder desde cualquier computadora

El proyecto está preparado para desplegarse como **Web Service en Render** mediante el archivo `render.yaml` ubicado en la raíz de `EyP_Parcial`.

1. Sube la carpeta completa `EyP_Parcial` a un repositorio de GitHub.
2. En Render, selecciona **New → Blueprint** y conecta ese repositorio.
3. Render detectará `render.yaml`, instalará `requirements.txt` y comprobará `/api/health`.
4. Al finalizar, Render entregará una dirección pública terminada en `.onrender.com`.

El servicio usa localmente `127.0.0.1:8765`; en Render escucha en `0.0.0.0` y utiliza automáticamente el puerto asignado mediante la variable `PORT`. El plan gratuito puede suspender el servicio después de un periodo sin tráfico, por lo que la primera apertura posterior puede tardar aproximadamente un minuto.

## Decisiones metodológicas incorporadas

- Se conservan los 24 registros, incluidos 125, 150 y 205 ms.
- F significa `Tiempo A > 100 ms`; 100 ms exactos no pertenece a F.
- Los intervalos son inclusivos y disjuntos: 20–60, 61–100, 101–140, 141–180 y 181–220.
- Los cuantiles usan `h = 1 + (n - 1)p` con interpolación lineal.
- La varianza es muestral, con divisor `n - 1`.
- Una versión cumple solo si satisface simultáneamente `P90 ≤ 100 ms` y proporción `> 100 ms ≤ 5 %`.
- La simulación usa una sola secuencia de 1000 sorteos de `numpy.random.default_rng(321)`; 100 y 500 son prefijos de esa secuencia.
- Una muestra mayor tiende a estabilizar la frecuencia relativa, pero no tiene que reducir el error en cada ampliación particular.
- La decisión económica no reemplaza el cumplimiento técnico.

## Estructura

```text
programa_web_caso1/
├── app.py                 # Servidor web y API
├── case1_stats.py         # Motor estadístico y datos
├── requirements.txt
├── run_app.bat
├── start_app.ps1
├── static/
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── tests/
    └── test_case1_stats.py
```
