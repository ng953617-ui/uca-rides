# UCA Rides — prototipo académico
Demostración interactiva de conexión de estudiantes por zona, horario (±15 min) y roles complementarios. No es un servicio oficial de la universidad.

## Ejecutar localmente
`pip install -r requirements.txt`

`streamlit run app.py`

## Publicar
Subir app.py, requirements.txt, README.md y .streamlit/config.toml a un repositorio GitHub. En https://share.streamlit.io/ crear una aplicación seleccionando el repositorio, rama main y app.py.

## Demostración
Entrar con perfil ficticio o correo de ejemplo demo@uca.edu.sv y código 123456 (no se envía correo). Mantener Santa Tecla, pasajero y salida 17:05. Contactar a Luis o Sofía, enviar un mensaje, acordar encuentro, simular viaje y calificar. Reiniciar desde la barra lateral.

## Alcance
Los perfiles, mensajes y viajes son ficticios. El filtro de coincidencias se ejecuta realmente sobre datos de ejemplo. No hay autenticación real, base de datos persistente, chat entre personas, geolocalización ni pagos. Los datos permanecen temporalmente en la sesión. No introducir datos personales reales. La verificación del correo no demuestra matrícula activa.
