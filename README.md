# UCA Rides v2 — prototipo académico independiente

Cobertura nacional mediante 14 departamentos y texto libre de municipio/distrito y sector. Viajes independientes hacia o desde la UCA, por fecha o recurrentes por días de la semana. Cada uno tiene hora prevista en la UCA, rol y asientos. No hay pagos ni transporte real.

## Publicación
Reemplazar app.py y README.md en el repositorio existente. Conservar requirements.txt y .streamlit/config.toml. Streamlit Community Cloud: rama main (o la rama real del repositorio), archivo app.py.

## Correo real (opcional)
Crear una cuenta Gmail dedicada al prototipo y habilitar verificación en dos pasos y contraseña de aplicación. En Streamlit, Settings > Secrets (o Advanced settings al publicar), guardar:

```toml
[smtp]
host = "smtp.gmail.com"
port = 465
user = "TU_CORREO@gmail.com"
password = "TU_CONTRASEÑA_DE_APLICACION"
```

No subir claves a GitHub. La cuenta remitente puede ser Gmail, pero solo se aceptan destinatarios @uca.edu.sv. El código aleatorio vence en 10 minutos, tiene cinco intentos, y se limitan los envíos por destinatario y por proceso. Sin configuración, el acceso real se deshabilita; la demostración ficticia permanece disponible. El acceso al buzón no confirma matrícula activa. No se ha probado el envío SMTP desde Community Cloud.

## Pruebas
Registrar varias salidas/llegadas distintas en un día, incluida una ubicación diferente de la residencia. Elegir fecha de búsqueda compatible con el viaje y activar las coincidencias ficticias. Se comprueban fecha, sentido, municipio/distrito, departamento, roles y tolerancia de 15 minutos. No se geocodifica ni se calculan rutas GPS. Las coincidencias se generan para probar la interfaz; no son usuarios reales. Chat, acuerdos y calificaciones siguen siendo simulados. No hay base de datos compartida: cada sesión conserva temporalmente sus datos. No usar el prototipo para coordinar viajes reales.
