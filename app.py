import streamlit as st
from datetime import time

st.set_page_config(page_title='UCA Rides', page_icon='🚘', layout='centered')
st.markdown('''<style>.stApp {background:#f4f8f7;} [data-testid="stHeader"] {background:#f4f8f7;} .hero {background:#08665e;color:white;padding:24px;border-radius:18px;margin-bottom:18px;} .hero h1 {color:white;margin:0;padding:0;} .hero p {margin:8px 0 0;} div[data-testid="stVerticalBlockBorderWrapper"] {background:white;border-radius:14px;} </style>''', unsafe_allow_html=True)
ZONAS=['Santa Tecla / Nuevo Cuscatlán','San Salvador centro','Antiguo Cuscatlán / Escalón','Mejicanos / Apopa','Soyapango / Ilopango / San Martín','Lourdes / Colón']
DEMO=[('Luis R.','Ingeniería Industrial',0,'Conductor',time(17,0),'Hombre',2),('Sofía M.','Psicología',0,'Conductor',time(17,10),'Mujer',1),('Diego A.','Economía',0,'Pasajero',time(17,5),'Hombre',0),('Ana P.','Arquitectura',1,'Conductor',time(17,15),'Mujer',2),('Carlos V.','Ingeniería Informática',1,'Pasajero',time(17,0),'Hombre',0),('María G.','Comunicación',2,'Conductor',time(17,0),'Mujer',2),('Elena T.','Ingeniería Industrial',3,'Conductor',time(17,0),'Mujer',1)]
s=st.session_state
for k,v in {'page':'Registro','profile':{},'email':'','code_sent':False,'verified':False,'match':None,'messages':[],'agreed':False,'done':False,'rated':False,'reports':[]}.items():
    if k not in s: s[k]=v

def go(page):
    s.page=page
    st.rerun()

def mins(t): return t.hour*60+t.minute

st.markdown('<div class="hero"><h1>🚘 UCA Rides</h1><p>Tu misma ruta. Tu mismo horario. Tu comunidad.</p></div>',unsafe_allow_html=True)
st.caption('Prototipo académico independiente · Datos ficticios · Sin pagos ni transporte real')
with st.sidebar:
    st.title('UCA Rides')
    st.caption('Demostración del servicio')
    if s.verified:
        st.write(s.email)
        if st.button('Mi perfil'): go('Perfil')
        if s.profile and st.button('Buscar coincidencias'): go('Coincidencias')
    if st.button('Reiniciar demostración'):
        s.clear(); st.rerun()

if s.page=='Registro':
    st.subheader('1. Registro universitario')
    st.write('Accede con tu correo institucional.')
    email=st.text_input('Correo institucional',value=s.email,placeholder='estudiante@uca.edu.sv')
    if st.button('Generar código de demostración',type='primary'):
        email=email.strip().lower()
        if email.count('@')==1 and email.endswith('@uca.edu.sv') and email.split('@')[0]:
            s.email=email; s.code_sent=True; st.rerun()
        else: st.error('Introduce un correo con dominio @uca.edu.sv.')
    if s.code_sent:
        st.info('Código de prueba: 123456. No se envía ningún correo real.')
        code=st.text_input('Código de seis dígitos',max_chars=6)
        consent=st.checkbox('Acepto las reglas de convivencia y entiendo que esta es una simulación.')
        if st.button('Verificar y continuar',type='primary'):
            if email.strip().lower()!=s.email: st.error('Genera un código para el correo actualizado.')
            elif code!='123456' or not consent: st.error('Revisa el código y acepta las reglas.')
            else: s.verified=True; go('Perfil')
    if st.button('Entrar con perfil ficticio'):
        s.email='demo@uca.edu.sv'; s.verified=True; go('Perfil')

elif s.page=='Perfil':
    st.subheader('2. Mi perfil')
    p=s.profile
    with st.form('perfil'):
        name=st.text_input('Nombre',p.get('name','Alex Demo'))
        carrera=st.text_input('Carrera',p.get('carrera','Ingeniería Industrial'))
        zona=st.selectbox('Zona de residencia',ZONAS,index=ZONAS.index(p.get('zona',ZONAS[0])))
        genero=st.selectbox('Género (opcional)',['Prefiero no indicar','Mujer','Hombre','Otro'],index=['Prefiero no indicar','Mujer','Hombre','Otro'].index(p.get('genero','Prefiero no indicar')))
        rol=st.radio('¿Cómo viajas?',['Pasajero','Conductor','Ambos'],index=['Pasajero','Conductor','Ambos'].index(p.get('rol','Pasajero')))
        entrada=st.time_input('Hora de entrada',p.get('entrada',time(8,0)))
        salida=st.time_input('Hora de salida',p.get('salida',time(17,5)))
        asientos=st.number_input('Asientos libres (si conduces)',1,5,p.get('asientos',2))
        st.caption('Avatar ficticio; no se solicitan fotos ni direcciones reales.')
        if st.form_submit_button('Guardar y buscar coincidencias',type='primary'):
            if not name.strip() or not carrera.strip(): st.error('Completa nombre y carrera.')
            else:
                s.profile=dict(name=name,carrera=carrera,zona=zona,genero=genero,rol=rol,entrada=entrada,salida=salida,asientos=asientos); go('Coincidencias')

elif s.page=='Coincidencias':
    st.subheader('3. Encuentra tu ride')
    p=s.profile
    st.write(f"Hola, {p['name']} · {p['zona']}")
    sentido=st.radio('Viaje',['Regreso','Ida'],horizontal=True)
    role=p['rol'] if p['rol']!='Ambos' else st.radio('Viajar como',['Pasajero','Conductor'],horizontal=True)
    filtro=st.selectbox('Filtrar por género',['Todos','Mujer','Hombre'])
    horario=p['salida'] if sentido=='Regreso' else p['entrada']
    st.caption(f'Buscando roles complementarios en tu zona, con diferencia máxima de 15 minutos de las {horario:%H:%M}.')
    found=0
    for name,carrera,z,rol,t,g,seat in DEMO:
        if sentido=='Ida': t=time(8,t.minute)
        if ZONAS[z]!=p['zona'] or rol==role or abs(mins(t)-mins(horario))>15 or (filtro!='Todos' and filtro!=g): continue
        found+=1
        with st.container(border=True):
            st.markdown(f'**👤 {name}** · {rol}')
            st.write(carrera)
            st.caption(f'{ZONAS[z]} · {t:%H:%M} · diferencia {abs(mins(t)-mins(horario))} min')
            if rol=='Conductor': st.write(f'🚘 {seat} asiento(s) disponible(s)')
            if st.button('Contactar',key='contact'+name,type='primary'):
                s.match=dict(name=name,rol=rol,hora=t,zona=ZONAS[z],sentido=sentido); s.messages=[]; s.agreed=False; s.done=False; s.rated=False; go('Chat')
    if not found: st.warning('No hay coincidencias en los datos ficticios para estos filtros. Prueba Santa Tecla y una salida cercana a las 17:00.')

elif s.page=='Chat':
    m=s.match
    st.subheader('4. Chat interno')
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
    st.subheader('5. Acuerdo de viaje')
    m=s.match
    st.write(f"{m['name']} · {m['sentido']} · {m['zona']}")
    punto=st.selectbox('Punto público de encuentro (ejemplo)',['Entrada principal del campus','Zona de parqueo del campus','Otro punto público acordado'])
    hora=st.time_input('Hora acordada',m['hora'])
    ok=st.checkbox('Entiendo que el encuentro, el viaje y cualquier reparto voluntario de gastos se acuerdan entre particulares.')
    if st.button('Confirmar acuerdo simulado',type='primary'):
        if not ok: st.error('Acepta la condición para continuar.')
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
    st.subheader('6. Evalúa tu experiencia')
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

st.divider()
st.caption('Proyecto de Innovación y Desarrollo de Productos y Servicios · Prototipo no oficial de UCA Rides')
