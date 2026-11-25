import streamlit as st
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
import json
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
        server.login(cfg['user'],''.join(cfg['password'].split())); server.send_message(msg)

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



def db(sql,args=(),one=False):
    cfg=st.secrets['database']
    if cfg.get('host'):
        params={k:cfg[k] for k in ('host','port','dbname','user','password')}
        conn=psycopg.connect(**params,sslmode='require',row_factory=dict_row,connect_timeout=10)
    else:
        conn=psycopg.connect(cfg['url'],row_factory=dict_row,connect_timeout=10)
    with conn as c:
        with c.cursor() as cur:
            cur.execute(sql,args)
            return (cur.fetchone() if one else cur.fetchall()) if cur.description else None

def pack(t): return {**t,'fecha':t['fecha'].isoformat(),'hora':t['hora'].isoformat()}
def unpack(t): return {**t,'fecha':date.fromisoformat(t['fecha']),'hora':time.fromisoformat(t['hora'])}
def label(t): return f"{t['sentido']} · {zona_text(t['zona'])} · {t['hora']:%H:%M} · {t['rol']}"
def refresh(): st.rerun()

st.title('🚘 UCA Rides')
st.caption('Tu misma ruta. Tu mismo horario. Tu comunidad. · Proyecto académico independiente, no oficial de la UCA.')
s=st.session_state
if 'verified' not in s: s.verified=False
if not s.verified:
    st.subheader('Acceso institucional')
    email=st.text_input('Correo @uca.edu.sv').strip().lower()
    cfg=smtp_config()
    if not cfg: st.warning('El administrador debe configurar el correo remitente. No se permite acceso sin verificación.'); st.stop()
    if st.button('Enviar código',type='primary'):
        if not valid_email(email): st.error('Solo se aceptan correos @uca.edu.sv.')
        elif not reserve_send(email): st.warning('Límite de envíos. Intenta más tarde.')
        else:
            s.pop('otp',None); code=f'{secrets.randbelow(1000000):06d}'
            try:
                send_code(email,code,cfg); s.otp=(email,hashlib.sha256(code.encode()).hexdigest(),monotonic()+600); s.attempts=0; st.success('Código enviado. Revisa Outlook y correo no deseado.')
            except Exception: st.error('No se pudo enviar. El administrador debe revisar SMTP.')
    if 'otp' in s:
        code=st.text_input('Código de seis dígitos',type='password',max_chars=6)
        st.info('Privacidad: se guardan correo, nombre, carrera, zona aproximada, horarios, mensajes y valoraciones para conectar estudiantes. No publiques domicilio exacto, teléfonos ni datos sensibles. Los participantes pueden ver tu perfil y tus viajes compatibles. Los administradores pueden revisar reportes y datos para operar el piloto. Solicita eliminación al equipo responsable antes de participar si necesitas más información.')
        ok=st.checkbox('Acepto participar en el piloto, el tratamiento descrito y las reglas: respeto, encuentro público, ningún cobro de la plataforma y reporte de incidentes.')
        if st.button('Verificar y entrar'):
            e,h,expiry=s.otp
            if email!=e or monotonic()>expiry or s.attempts>=5: s.pop('otp',None); st.error('Solicita otro código.')
            elif not ok: st.error('Debes aceptar las condiciones.')
            else:
                s.attempts+=1
                if hmac.compare_digest(hashlib.sha256(code.encode()).hexdigest(),h): s.email=e; s.verified=True; s.pop('otp',None); refresh()
                else: st.error('Código incorrecto.')
    st.stop()
me=s.email
with st.sidebar:
    st.caption(me)
    if st.button('Cerrar sesión'): s.clear(); refresh()
try: profile=db('select data from ur_profiles where email=%s',(me,),True)
except Exception as exc:
    state=getattr(exc,'sqlstate',None)
    msg=str(exc).lower()
    if state=='28P01' or 'password authentication failed' in msg:
        reason='DB-01: autenticación rechazada; revisa la contraseña vigente y el usuario del pooler.'
    elif 'tenant or user not found' in msg or 'tenant not found' in msg:
        reason='DB-02: usuario o proyecto del pooler no reconocido.'
    elif state=='42P01':
        reason='DB-03: no se encuentra la tabla ur_profiles en la base conectada.'
    elif state=='42501':
        reason='DB-04: permisos insuficientes para consultar la tabla.'
    elif isinstance(exc,(KeyError,FileNotFoundError)):
        reason='DB-05: faltan campos de Secrets.'
    elif 'timeout' in msg or 'timed out' in msg or 'could not translate host' in msg or 'network is unreachable' in msg or 'connection refused' in msg:
        reason='DB-06: problema de red, DNS o tiempo de conexión.'
    elif 'invalid dsn' in msg or 'invalid uri' in msg or 'invalid connection' in msg:
        reason='DB-07: formato de conexión incorrecto.'
    else:
        reason='DB-08: otro error de conexión o consulta.'
    st.error(reason)
    st.caption('Diagnóstico seguro: '+type(exc).__name__+(' · SQLSTATE '+state if state else ''))
    st.stop()
p=profile['data'] if profile else {}
page=st.sidebar.radio('Menú',['Mi perfil','Mis viajes','Coincidencias','Solicitudes y chat','Historial y reportes']) if p else 'Mi perfil'
if page=='Mi perfil':
    st.subheader('Mi perfil')
    with st.form('perfil'):
        name=st.text_input('Nombre',p.get('name',''),max_chars=80); carrera=st.text_input('Carrera',p.get('carrera',''),max_chars=100)
        zona=zona_form('res',p.get('zona')); options=['Prefiero no indicar','Mujer','Hombre','Otro']; gender=st.selectbox('Género (opcional)',options,index=options.index(p.get('genero',options[0])))
        avatar=st.selectbox('Avatar',['🚗','🎓','🌿','⭐'],index=['🚗','🎓','🌿','⭐'].index(p.get('avatar','🎓')))
        if st.form_submit_button('Guardar perfil'):
            if not name.strip() or not carrera.strip() or not zona['mun']: st.error('Completa los campos.')
            else: db('insert into ur_profiles values (%s,%s) on conflict(email) do update set data=excluded.data',(me,Jsonb(dict(name=name,carrera=carrera,zona=zona,genero=gender,avatar=avatar)))); refresh()
    st.caption('La verificación acredita acceso al correo, no matrícula activa. No escribas direcciones exactas.')
else:
    own=db('select id,data from ur_trips where owner=%s and active order by id desc',(me,))
    if page=='Mis viajes':
        st.subheader('Mis desplazamientos')
        for row in own:
            t=unpack(row['data']); st.write(label(t)); st.caption(f"Desde {t['fecha']} · {t['frecuencia']} · "+', '.join(DIAS[x] for x in t['dias']))
            if st.button('Desactivar',key=f"del{row['id']}"):
                db('update ur_trips set active=false where id=%s and owner=%s',(row['id'],me)); db("update ur_requests set status='Cancelado' where (driver_trip=%s or passenger_trip=%s) and status in ('Pendiente','Aceptado')",(row['id'],row['id'])); refresh()
        st.divider(); st.subheader('Nuevo viaje')
        sentido=st.radio('Sentido',['Hacia la UCA','Desde la UCA']); zona=p['zona'] if st.radio('Ubicación',['Mi residencia','Trabajo u otra zona'])=='Mi residencia' else zona_form('trip')
        frecuencia=st.radio('Frecuencia',['Una sola vez','Semanal recurrente']); fecha=st.date_input('Fecha de inicio',min_value=hoy()); dias=st.multiselect('Días',DIAS) if frecuencia=='Semanal recurrente' else []
        hora=st.time_input('Llegada a la UCA' if sentido=='Hacia la UCA' else 'Salida de la UCA',value=None,step=60); rol=st.radio('Rol',['Pasajero','Conductor']); seats=st.number_input('Asientos libres',1,8,1) if rol=='Conductor' else 0
        if st.button('Publicar viaje',type='primary'):
            if not zona['mun'] or hora is None or (frecuencia=='Semanal recurrente' and not dias): st.error('Completa ubicación, hora y días.')
            else: db('insert into ur_trips(owner,data) values (%s,%s)',(me,Jsonb(pack(dict(sentido=sentido,zona=zona,frecuencia=frecuencia,fecha=fecha,dias=[DIAS.index(d) for d in dias],hora=hora,rol=rol,asientos=seats))))); refresh()
    elif page=='Coincidencias':
        st.subheader('Coincidencias reales')
        if not own: st.info('Publica un viaje primero.'); st.stop()
        a=st.selectbox('Tu viaje',own,format_func=lambda r:label(unpack(r['data']))); t=unpack(a['data']); day=st.date_input('Fecha a buscar',min_value=hoy(),value=max(hoy(),t['fecha'])); g=st.selectbox('Género',['Todos','Mujer','Hombre','Otro'])
        st.caption('Mismo departamento y municipio/distrito escrito, sentido y fecha, roles complementarios, ±15 min. Confirma ruta exacta y asiento en chat; no hay GPS.')
        found=0
        for b in db('select t.id,t.owner,t.data,p.data as profile from ur_trips t join ur_profiles p on p.email=t.owner where t.active and t.owner<>%s',(me,)):
            u=unpack(b['data']); q=b['profile']
            if not compatible(t,u,day) or (g!='Todos' and q['genero']!=g): continue
            found+=1; d,pa=(a,b) if t['rol']=='Conductor' else (b,a); driver,passenger=(me,b['owner']) if t['rol']=='Conductor' else (b['owner'],me)
            with st.container(border=True):
                st.write(f"{q['avatar']} {q['name']} · {q['carrera']}"); st.write(label(u)); rating=db('select avg(stars) as avg,count(*) as n from ur_ratings where target=%s',(b['owner'],),True); st.caption(f"Valoraciones: {float(rating['avg']):.1f}/5 ({rating['n']})" if rating['n'] else 'Sin valoraciones aún')
                if st.button('Enviar solicitud',key=f"req{b['id']}"):
                    db('insert into ur_requests(driver_trip,passenger_trip,day,sender,driver,passenger) values (%s,%s,%s,%s,%s,%s) on conflict do nothing',(d['id'],pa['id'],day,me,driver,passenger)); st.success('Solicitud registrada. Revisa Solicitudes y chat.')
        if not found: st.info('No hay coincidencias por ahora. Vuelve a consultar cuando se publiquen nuevos viajes.')
    else:
        rows=db('select r.*,p.data as other from ur_requests r join ur_profiles p on p.email=case when r.driver=%s then r.passenger else r.driver end where r.driver=%s or r.passenger=%s order by r.id desc',(me,me,me))
        rows=[r for r in rows if (r['status'] in ('Pendiente','Aceptado'))==(page=='Solicitudes y chat')]
        if not rows: st.info('No hay solicitudes en esta sección.'); st.stop()
        r=st.selectbox('Viaje',rows,format_func=lambda r:f"{r['other']['name']} · {r['day']} · {r['status']} · #{r['id']}"); rid=r['id']; status=r['status']; other=r['passenger'] if r['driver']==me else r['driver']
        if status=='Pendiente' and r['sender']!=me:
            if st.button('Aceptar solicitud'):
                # Serialize approvals for a driver's trip and date using a transaction lock.
                with psycopg.connect(st.secrets['database']['url']) as c:
                    with c.cursor() as cur:
                        cur.execute('select id from ur_trips where id=%s for update',(r['driver_trip'],)); cur.execute('select data,active from ur_trips where id=%s',(r['driver_trip'],)); dt,active=cur.fetchone(); cur.execute('select active from ur_trips where id=%s',(r['passenger_trip'],)); pa_active=cur.fetchone()[0]; cur.execute("select count(*) from ur_requests where driver_trip=%s and day=%s and status in ('Aceptado','Completado')",(r['driver_trip'],r['day'])); n=cur.fetchone()[0]
                        if active and pa_active and n<int(dt['asientos']): cur.execute("update ur_requests set status='Aceptado' where id=%s and status='Pendiente'",(rid,))
                        else: st.error('No quedan asientos o el viaje fue desactivado.'); st.stop()
                refresh()
        if status in ('Pendiente','Aceptado'):
            if st.button('Cancelar / rechazar'): db("update ur_requests set status='Cancelado' where id=%s and (driver=%s or passenger=%s) and status in ('Pendiente','Aceptado')",(rid,me,me)); refresh()
            st.subheader('Chat privado'); st.button('Actualizar mensajes')
            for m in db('select sender,body from ur_messages where request_id=%s order by id',(rid,)):
                with st.chat_message('user' if m['sender']==me else 'assistant'): st.text(m['body'])
            with st.form(f'msg{rid}',clear_on_submit=True):
                msg=st.text_area('Mensaje',max_chars=1000)
                if st.form_submit_button('Enviar') and msg.strip(): db('insert into ur_messages(request_id,sender,body) values (%s,%s,%s)',(rid,me,msg.strip())); refresh()
            if status=='Aceptado':
                with st.form('meeting'):
                    meeting=st.text_input('Punto público y hora acordados',r['meeting'] or '',max_chars=200)
                    if st.form_submit_button('Guardar acuerdo') and meeting.strip(): db('update ur_requests set meeting=%s where id=%s',(meeting,rid)); refresh()
                if r['meeting'] and st.button('Marcar viaje realizado'): db("update ur_requests set status='Completado' where id=%s and status='Aceptado'",(rid,)); refresh()
        if status=='Completado':
            stars=st.slider('Calificar a tu compañero',1,5,5)
            if st.button('Guardar valoración'): db('insert into ur_ratings values (%s,%s,%s,%s) on conflict(request_id,author) do update set stars=excluded.stars',(rid,me,other,stars)); st.success('Valoración guardada.')
        with st.form(f'report{rid}'):
            reason=st.text_area('Reportar conducta inadecuada',max_chars=1000)
            if st.form_submit_button('Enviar reporte') and reason.strip(): db('insert into ur_reports(author,request_id,body) values (%s,%s,%s)',(me,rid,reason)); st.success('Reporte registrado para revisión del equipo.')
        st.caption('No se procesan pagos. Acuerda el viaje voluntariamente y reúnete en un lugar público. En una emergencia contacta a las autoridades.')
