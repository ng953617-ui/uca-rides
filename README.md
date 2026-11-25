# UCA Rides V3 — MVP académico
1. Crear un proyecto Supabase exclusivo. En SQL Editor ejecutar schema.sql completo.
2. En Connect copiar la URI Session pooler (5432), sustituir la contraseña de base de datos (codificar caracteres especiales de URI) y añadir ?sslmode=require si no tiene parámetros.
3. Configurar una cuenta Gmail remitente con verificación en dos pasos y contraseña de aplicación.
4. En Streamlit Settings > Secrets guardar:
```toml
[database]
url = "postgresql://USUARIO:CONTRASEÑA@HOST:5432/postgres?sslmode=require"
[smtp]
host = "smtp.gmail.com"
port = 465
user = "REMITENTE@gmail.com"
password = "CONTRASEÑA_DE_APLICACION"
```
5. Subir app.py, requirements.txt, README.md y schema.sql al repositorio existente. No subir secretos. Reiniciar aplicación.
6. Probar con dos buzones institucionales autorizados, misma zona y fecha, roles complementarios y horario con diferencia menor de 15 min. Probar rechazo de dominios externos, OTP incorrecto, persistencia, solicitudes, chat, cancelación y valoración.

Alcance: piloto controlado, no servicio oficial. El código verifica el buzón, no matrícula. Coincidencias por texto normalizado de municipio y departamento, no GPS. Chat mediante actualización manual; reportes consultables por administrador en Supabase. Avatar, no fotografía. Sin notificaciones automáticas. Los límites de correo son en memoria y se reinician con el proceso. Usar proyecto aislado; la conexión de base de datos tiene privilegios elevados, solo en servidor. Antes de abrir al público: revisión de seguridad y privacidad, rol SQL restringido, límites persistentes, gestión de incidentes, eliminación de datos, confirmación bilateral y autorización institucional. No se ha probado integración real con servicios externos.
