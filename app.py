import streamlit as st
from datetime import time, date, datetime, timedelta
from zoneinfo import ZoneInfo
import re, secrets, hashlib, hmac, smtplib, ssl, unicodedata, threading
from email.message import EmailMessage
from time import monotonic

st.set_page_config(page_title='UCA Rides', page_icon='🚘', layout='centered')

DEPARTAMENTOS = ['Ahuachapán','Santa Ana','Sonsonate','Chalatenango','La Libertad','San Salvador','Cuscatlán','La Paz','Cabañas','San Vicente','Usulután','San Miguel','Morazán','La Unión']
DIAS = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']

def hoy(): return datetime.now(ZoneInfo('America/El_Salvador')).date()
def normal(s): return ' '.join(''.join(c for c in unicodedata.normalize('NFD',s.casefold()) if unicodedata.category(c)!='Mn').split())
def valid_email(e): return bool(re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@uca\.edu\.sv",e)) and len(e)<=254

@st.cache_resource
def limits(): return threading.Lock(), {}, []

def reserve_send(email):
    lock, per_email, global_times = limits(); now=monotonic()
    with lock:
        global_times[:] = [x for x in global_times if now-x<3600]
        for key in list(per_email):
            per_email[key]=[x for x in per_email[key] if now-x<3600]
            if not per_email[key]: del per_email[key]
        times=per_email.setdefault(email,[])
        if len(global_times)>=30 or len(times)>=3 or (times and now-times[-1]<60): return False
        times.append(now); global_times.append(now); return True

def smtp_config():
    try:
        c=st.secrets['smtp']; return c if all(c.get(k) for k in ('user','password')) else None
    except (KeyError, FileNotFoundError): return None

def send_code(email, code, cfg):
    msg=EmailMessage(); msg['Subject']='UCA Rides | Código de verificación'; msg['From']=cfg['user']; msg['To']=email
    msg.set_content(f'Tu código de UCA Rides es {code}. Vence en 10 minutos. Si no solicitaste este código, ignora este mensaje. Prototipo académico independiente, no oficial de la UCA.')
    with smtplib.SMTP_SSL(cfg.get('host','smtp.gmail.com'),int(cfg.get('port',465)),context=ssl.create_default_context(),timeout=15) as server:
        server.login(cfg['user'],cfg['password']); server.send_message(msg)

def zona_form(prefix, defaults=None):
    defaults=defaults or {}; dep=st.selectbox('Departamento',DEPARTAMENTOS,index=DEPARTAMENTOS.index(defaults.get('dep','La Libertad')),key=prefix+'dep')
    mun=st.text_input('Municipio o distrito',defaults.get('mun',''),key=prefix+'mun',placeholder='Ej. distrito o municipio')
    local=st.text_input('Colonia, cantón, caserío o sector (opcional)',defaults.get('local',''),key=prefix+'local')
    return dict(dep=dep,mun=mun.strip(),local=local.strip())
def zona_text(z): return ', '.join(x for x in (z['local'],z['mun'],z['dep']) if x)
def aplica(t,d): return (t['fecha']==d if t['frecuencia']=='Una sola vez' else d>=t['fecha'] and d.weekday() in t['dias'])
def hora_match(a,b): return abs((a.hour*60+a.minute)-(b.hour*60+b.minute))<=15

def compatible(a,b,d):
    return (aplica(a,d) and aplica(b,d) and a['sentido']==b['sentido']
            and all(normal(a['zona'][k])==normal(b['zona'][k]) for k in ('dep','mun'))
            and a['rol']!=b['rol'] and (a if a['rol']=='Conductor' else b)['asientos']>0
            and hora_match(a['hora'],b['hora']))


st.markdown('''<style>.stApp {background:#f4f8f7;} [data-testid="stHeader"] {background:#f4f8f7;} .hero {background:#08665e;color:white;padding:24px;border-radius:18px;margin-bottom:18px;} .hero h1 {color:white;margin:0;padding:0;} .hero p {margin:8px 0 0;} div[data-testid="stVerticalBlockBorderWrapper"] {background:white;border-radius:14px;} </style>''', unsafe_allow_html=True)
s=st.session_state
for k,v in {'page':'Registro','profile':{},'email':'','code_sent':False,'verified':False,'match':None,'messages':[],'agreed':False,'done':False,'rated':False,'reports':[],'trips':[],'otp_hash':'','otp_exp':0,'otp_attempts':0,'demo_mode':False}.items():
    if k not in s: s[k]=v

def go(page):
    s.page=page
    st.rerun()

def mins(t): return t.hour*60+t.minute

st.markdown('<div class="hero"><h1>🚘 UCA Rides</h1><p>Tu misma ruta. Tu mismo horario. Tu comunidad.</p></div>',unsafe_allow_html=True)
st.caption('Prototipo académico independiente · Coincidencias ficticias · Sin pagos ni transporte real')
with st.sidebar:
    st.title('UCA Rides')
    st.caption('Demostración del servicio')
    if s.verified:
        st.write(s.email)
        if st.button('Mi perfil'): go('Perfil')
        if s.profile and st.button('Mis desplazamientos'): go('Desplazamientos')
        if s.profile and s.trips and st.button('Buscar coincidencias'): go('Coincidencias')
    if st.button('Cerrar sesión y borrar datos'):
        s.clear(); st.rerun()

if s.page=='Registro':
    st.subheader('1. Registro universitario')
    cfg=smtp_config()
    st.write('Accede con un correo institucional @uca.edu.sv.')
    st.caption('La verificación confirma acceso al buzón, no matrícula activa. Los datos del perfil y los viajes permanecen en la sesión. No introduzcas datos sensibles.')
    email=st.text_input('Correo institucional',value=s.email,placeholder='estudiante@uca.edu.sv').strip().lower()
    if not cfg: st.warning('El envío real aún no está configurado. Puedes usar únicamente la demostración identificada abajo.')
    if st.button('Enviar código al correo',type='primary',disabled=not bool(cfg)):
        if not valid_email(email): st.error('Introduce un correo válido @uca.edu.sv.')
        elif not reserve_send(email): st.warning('Límite de envíos alcanzado. Espera antes de volver a solicitar un código.')
        else:
            code=f'{secrets.randbelow(1000000):06d}'
            s.code_sent=False; s.otp_hash=''; s.otp_attempts=0
            try:
                send_code(email,code,cfg)
                s.email=email; s.otp_hash=hashlib.sha256(code.encode()).hexdigest(); s.otp_exp=monotonic()+600; s.code_sent=True
                st.success('Código enviado. Revisa tu buzón y correo no deseado.')
            except Exception: st.error('No se pudo enviar el correo. Revisa la configuración SMTP con el administrador.')
    if s.code_sent and cfg:
        code=st.text_input('Código de seis dígitos',max_chars=6,type='password')
        consent=st.checkbox('Acepto las reglas de convivencia y el tratamiento temporal de datos para este prototipo.')
        if st.button('Verificar y continuar',type='primary'):
            if email!=s.email: st.error('Solicita un código para el correo actualizado.')
            elif monotonic()>s.otp_exp or s.otp_attempts>=5: s.code_sent=False; s.otp_hash=''; st.error('Código vencido o límite de intentos alcanzado. Solicita otro.')
            elif not consent: st.error('Acepta las reglas para continuar.')
            else:
                s.otp_attempts+=1
                if hmac.compare_digest(hashlib.sha256(code.encode()).hexdigest(),s.otp_hash):
                    s.verified=True; s.demo_mode=False; s.code_sent=False; s.otp_hash=''; go('Perfil')
                else: st.error('Código incorrecto.')
    st.divider()
    if st.button('Entrar a demostración ficticia (sin verificación)'):
        s.email='demo@uca.edu.sv'; s.verified=True; s.demo_mode=True; s.code_sent=False; s.otp_hash=''; go('Perfil')

elif s.page=='Perfil':
    st.subheader('2. Mi perfil')
    p=s.profile
    with st.form('perfil'):
        name=st.text_input('Nombre o alias',p.get('name',''))
        carrera=st.text_input('Carrera',p.get('carrera',''))
        st.markdown('**Zona de residencia**')
        zona=zona_form('res',p.get('zona'))
        opciones=['Prefiero no indicar','Mujer','Hombre','Otro']
        genero=st.selectbox('Género (opcional)',opciones,index=opciones.index(p.get('genero',opciones[0])))
        st.caption('No escribas direcciones exactas. Puedes registrar viajes desde tu trabajo u otra zona más adelante.')
        if st.form_submit_button('Guardar perfil',type='primary'):
            if not name.strip() or not carrera.strip() or not zona['mun']: st.error('Completa nombre, carrera y municipio o distrito.')
            else: s.profile=dict(name=name,carrera=carrera,zona=zona,genero=genero); go('Desplazamientos')

elif s.page=='Desplazamientos':
    st.subheader('3. Mis desplazamientos')
    st.write('Registra tantos viajes como necesites por día. Cada viaje puede tener una ubicación, horario y rol distintos.')
    for i,t in enumerate(s.trips):
        with st.container(border=True):
            st.write(f"**{t['sentido']}** · {zona_text(t['zona'])} · {t['hora']:%H:%M} · {t['rol']}")
            st.caption(f"{t['frecuencia']} · "+(str(t['fecha']) if t['frecuencia']=='Una sola vez' else ', '.join(DIAS[j] for j in t['dias'])+f" desde {t['fecha']}"))
            if st.button('Eliminar viaje',key=f'del{i}'): s.trips.pop(i); st.rerun()
    with st.container(border=True):
        st.markdown('**Agregar desplazamiento**')
        sentido=st.radio('Sentido',['Hacia la UCA','Desde la UCA'],horizontal=True)
        origen=st.radio('Ubicación fuera del campus',['Mi residencia','Trabajo u otro sector'],horizontal=True)
        zona=s.profile['zona'] if origen=='Mi residencia' else zona_form('viaje')
        frecuencia=st.radio('Frecuencia',['Una sola vez','Semanal recurrente'],horizontal=True)
        fecha=st.date_input('Fecha del viaje' if frecuencia=='Una sola vez' else 'Fecha de inicio',value=hoy(),min_value=hoy(),key='fecha_viaje')
        dias=st.multiselect('Días de la semana',DIAS) if frecuencia=='Semanal recurrente' else []
        hora=st.time_input('Hora prevista de llegada a la UCA' if sentido=='Hacia la UCA' else 'Hora prevista de salida de la UCA',value=None,step=timedelta(minutes=1))
        rol=st.radio('Rol en este viaje',['Pasajero','Conductor'],horizontal=True)
        asientos=st.number_input('Asientos disponibles',min_value=1,max_value=8,value=1) if rol=='Conductor' else 0
        if st.button('Agregar viaje',type='primary'):
            if not zona['mun'] or hora is None or (frecuencia=='Semanal recurrente' and not dias): st.error('Completa ubicación, hora y días si es recurrente.')
            else:
                s.trips.append(dict(sentido=sentido,zona=zona,frecuencia=frecuencia,fecha=fecha,dias=[DIAS.index(d) for d in dias],hora=hora,rol=rol,asientos=asientos)); st.rerun()
    if s.trips and st.button('Buscar coincidencias',type='primary'): go('Coincidencias')

elif s.page=='Coincidencias':
    st.subheader('4. Encuentra tu ride')
    if not s.trips: st.info('Agrega un viaje primero.'); st.stop()
    idx=st.selectbox('Desplazamiento',range(len(s.trips)),format_func=lambda i:f"{i+1}. {s.trips[i]['sentido']} · {zona_text(s.trips[i]['zona'])} · {s.trips[i]['hora']:%H:%M}")
    t=s.trips[idx]
    fecha=st.date_input('Fecha a buscar',value=max(hoy(),t['fecha']),min_value=hoy(),key=f'buscar{idx}')
    filtro=st.selectbox('Filtrar por género',['Todos','Mujer','Hombre','Otro'])
    st.caption('Se compara fecha, sentido, municipio/distrito y departamento, roles complementarios y hora en la UCA ±15 minutos. La colonia y ruta se confirman en el chat; no se calcula una ruta GPS.')
    if not aplica(t,fecha): st.warning('Este desplazamiento no está programado para esa fecha.'); st.stop()
    if not st.checkbox('Mostrar coincidencias ficticias de prueba para este viaje'):
        st.info('No hay un directorio real de estudiantes conectado. Activa la simulación para probar el flujo.')
    else:
        st.warning('Perfiles ficticios generados para probar el algoritmo; no son ofertas reales.')
        base=t['hora'].hour*60+t['hora'].minute
        role='Conductor' if t['rol']=='Pasajero' else 'Pasajero'
        found=0
        for name,carrera,delta,g,seat in [('Luis R.','Ingeniería Industrial',-5,'Hombre',2),('Sofía M.','Psicología',10,'Mujer',1),('Alex T.','Economía',30,'Otro',1)]:
            n=base+delta
            if not 0<=n<1440: continue
            h=time(n//60,n%60)
            candidate=dict(t,frecuencia='Una sola vez',fecha=fecha,hora=h,rol=role,asientos=seat if role=='Conductor' else 0)
            if not compatible(t,candidate,fecha) or (filtro!='Todos' and filtro!=g): continue
            found+=1
            with st.container(border=True):
                st.write(f'**{name} (ficticio)** · {role} · {carrera}')
                st.caption(f"{zona_text(t['zona'])} · {fecha} · {h:%H:%M} · diferencia {abs(delta)} min")
                if role=='Conductor': st.write(f'{seat} asiento(s) disponible(s)')
                if st.button('Contactar',key='contact'+name,type='primary'):
                    s.match=dict(name=name,rol=role,hora=h,zona=zona_text(t['zona']),sentido=t['sentido'],fecha=fecha); s.messages=[]; s.agreed=False; s.done=False; s.rated=False; go('Chat')
        if not found: st.info('No hay coincidencias ficticias con estos filtros.')
    if st.button('Volver a mis desplazamientos'): go('Desplazamientos')

elif s.page=='Chat':
    m=s.match
    st.subheader('5. Chat interno')
    st.write(f"Conversación con **{m['name']}** · {m['zona']}")
    st.caption('Mensajes simulados; no se comparten números telefónicos.')
    with st.chat_message('assistant'): st.write('¡Hola! Vamos por la misma ruta. ¿Nos conocemos primero en el campus?')
    for msg in s.messages:
        with st.chat_message('user'): st.write(msg)
        with st.chat_message('assistant'): st.write('¡Perfecto! Podemos acordar un punto público en el campus. (Respuesta simulada)')
    msg=st.chat_input('Escribe un mensaje')
    if msg: s.messages.append(msg); st.rerun()
    if st.button('Acordar encuentro',type='primary'): go('Acuerdo')
    if st.button('Reportar conducta inadecuada'): go('Reporte')
    if st.button('Volver a coincidencias'): go('Coincidencias')

elif s.page=='Acuerdo':
    st.subheader('6. Acuerdo de viaje')
    m=s.match
    st.write(f"{m['name']} · {m['sentido']} · {m['zona']} · {m['fecha']}")
    st.caption('Conózcanse previamente en el campus. Para viajes hacia la UCA, acuerden un punto público de salida fuera del campus.')
    punto=st.text_input('Punto público de encuentro (sin dirección privada)')
    hora=st.time_input('Hora acordada',m['hora'])
    ok=st.checkbox('Entiendo que el encuentro, el viaje y cualquier reparto voluntario de gastos se acuerdan entre particulares.')
    if st.button('Confirmar acuerdo simulado',type='primary'):
        if not ok or not punto.strip(): st.error('Indica el punto público y acepta la condición para continuar.')
        else: s.agreed=True; s.punto=punto; s.hora=hora; go('Viaje')

elif s.page=='Viaje':
    st.subheader('Viaje acordado')
    st.success('Acuerdo confirmado en la simulación.')
    st.write(f"📍 {s.punto} · {s.hora:%H:%M}")
    st.write(f"Con {s.match['name']} · {s.match['zona']}")
    st.info('La plataforma no presta transporte, no fija precios y no procesa pagos.')
    if st.button('Simular viaje completado',type='primary'): s.done=True; go('Calificación')
    if st.button('Cancelar acuerdo'): s.agreed=False; go('Coincidencias')

elif s.page=='Calificación':
    st.subheader('7. Evalúa tu experiencia')
    stars=st.radio('Calificación',['★','★★','★★★','★★★★','★★★★★'],index=4,horizontal=True)
    comment=st.text_area('Comentario opcional')
    if st.button('Enviar calificación',type='primary'):
        s.rated=True; s.rating=len(stars); go('Final')

elif s.page=='Final':
    st.success('¡Gracias por compartir tu experiencia!')
    st.write(f"Calificación simulada: {s.rating}/5")
    st.write('Has completado el recorrido principal del prototipo.')
    if st.button('Buscar otro viaje',type='primary'): go('Coincidencias')

elif s.page=='Reporte':
    st.subheader('Reporte de seguridad')
    reason=st.selectbox('Motivo',['Conducta inadecuada','Perfil sospechoso','Otro'])
    detail=st.text_area('Descripción (solo datos ficticios)')
    if st.button('Enviar reporte simulado',type='primary'):
        s.reports.append((reason,detail)); st.success('Reporte guardado temporalmente en esta sesión. No se ha enviado a ninguna institución.')
    if st.button('Volver al chat'): go('Chat')

if s.verified and s.demo_mode: st.info('Sesión de demostración: correo no verificado.')
st.divider()
st.caption('Proyecto de Innovación y Desarrollo de Productos y Servicios · Prototipo no oficial de UCA Rides')
