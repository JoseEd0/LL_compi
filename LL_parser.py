import streamlit as st
import pandas as pd

EPSILON = 'ε'

def trim_elements(elements):
    return [e.strip() for e in elements if e.strip()]

def add_unique(e, arr):
    if e not in arr:
        arr.append(e)
        return True
    return False

def procesar_gramatica(reglas_raw):
    reglas = [r.strip() for r in reglas_raw.strip().split('\n') if r.strip()]
    alfabeto, no_terminales, terminales = [], [], []
    for r in reglas:
        partes = r.split('->')
        if len(partes) != 2:
            continue
        nt = partes[0].strip()
        desarrollo = trim_elements(partes[1].split())
        add_unique(nt, alfabeto)
        add_unique(nt, no_terminales)
        for s in desarrollo:
            if s != EPSILON:
                add_unique(s, alfabeto)
    for s in alfabeto:
        if s not in no_terminales:
            add_unique(s, terminales)
    return reglas, alfabeto, no_terminales, terminales

def obtener_firsts(reglas, no_terminales, terminales):
    firsts = {nt: [] for nt in no_terminales}
    cambio = True
    while cambio:
        cambio = False
        for regla in reglas:
            nt, des = [p.strip() for p in regla.split('->')]
            desarrollo = trim_elements(des.split())
            if len(desarrollo) == 1 and desarrollo[0] == EPSILON:
                if add_unique(EPSILON, firsts[nt]):
                    cambio = True
            else:
                deriva_epsilon = True
                for s in desarrollo:
                    if s in terminales:
                        if add_unique(s, firsts[nt]):
                            cambio = True
                        deriva_epsilon = False
                        break
                    elif s in no_terminales:
                        for f in firsts[s]:
                            if f != EPSILON and add_unique(f, firsts[nt]):
                                cambio = True
                        if EPSILON not in firsts[s]:
                            deriva_epsilon = False
                            break
                if deriva_epsilon and add_unique(EPSILON, firsts[nt]):
                    cambio = True
    return firsts

def obtener_first_seq(secuencia, firsts, terminales, no_terminales):
    resultado = []
    epsilon = True
    for s in secuencia:
        if s in terminales:
            add_unique(s, resultado)
            epsilon = False
            break
        elif s in no_terminales:
            for f in firsts[s]:
                if f != EPSILON:
                    add_unique(f, resultado)
            if EPSILON not in firsts[s]:
                epsilon = False
                break
    if epsilon:
        add_unique(EPSILON, resultado)
    return resultado

def obtener_follows(reglas, no_terminales, firsts, terminales):
    follows = {nt: [] for nt in no_terminales}
    follows[no_terminales[0]].append('$')
    cambio = True
    while cambio:
        cambio = False
        for regla in reglas:
            A, des = [p.strip() for p in regla.split('->')]
            desarrollo = trim_elements(des.split())
            for i, B in enumerate(desarrollo):
                if B in no_terminales:
                    beta = desarrollo[i+1:]
                    first_beta = obtener_first_seq(beta, firsts, terminales, no_terminales)
                    for s in first_beta:
                        if s != EPSILON and add_unique(s, follows[B]):
                            cambio = True
                    if not beta or EPSILON in first_beta:
                        for f in follows[A]:
                            if add_unique(f, follows[B]):
                                cambio = True
    return follows

def construir_tabla(reglas, firsts, follows, terminales, no_terminales):
    tabla = {t: {nt: '' for nt in no_terminales} for t in terminales + ['$']}
    for r in reglas:
        A, des = [p.strip() for p in r.split('->')]
        secuencia = des.split()
        primeros = obtener_first_seq(secuencia, firsts, terminales, no_terminales)
        for t in primeros:
            if t != EPSILON:
                tabla[t][A] = r
        if EPSILON in primeros:
            for f in follows[A]:
                tabla[f][A] = r

    for t in terminales + ['$']:
        for nt in no_terminales:
            if tabla[t][nt] == '':
                if t in follows[nt] or t == '$':
                    tabla[t][nt] = 'EXT'  
                else:
                    tabla[t][nt] = 'EXP'
    return tabla

def es_ll1(tabla, no_terminales, terminales):
    for nt in no_terminales:
        for t1 in terminales:
            for t2 in terminales:
                if t1 != t2 and tabla[t1][nt] == tabla[t2][nt] and tabla[t1][nt] != '':
                    return False
    return True

def analizar_cadena(cadena, tabla, simbolo_inicial, terminales, no_terminales, follows):
    pila = ['$', simbolo_inicial]
    tokens = cadena.split() + ['$']
    pasos = [(0, ' '.join(pila), ' '.join(tokens), 'Inicial')]
    apuntador, errores = 0, 0

    while pila and errores < 5:
        tope = pila[-1]
        actual = tokens[apuntador]
        accion = ""

        if tope == actual == '$':
            accion = "ACEPTAR"
            pasos.append((len(pasos), ' '.join(pila), ' '.join(tokens), accion))
            break

        elif tope == actual:
            pila.pop()
            apuntador += 1
            accion = f"Match: {actual}"

        elif tope in terminales:
            accion = f"❌ ERROR: se esperaba '{tope}', se encontró '{actual}'"
            apuntador += 1
            errores += 1

        else:
            if actual in tabla and tope in tabla[actual] and tabla[actual][tope] != '':
                regla = tabla[actual][tope]
                pila.pop()
                rhs = regla.split('->')[1].strip().split()
                if rhs[0] != EPSILON:
                    pila.extend(reversed(rhs))  
                accion = f"Expandir: {regla}"
            else:
                errores += 1
                accion = f"⚠️ EXPLORAR: Saltar {actual}"
                apuntador += 1
        
        pasos.append((len(pasos), ' '.join(pila), ' '.join(tokens[apuntador:]), accion))

    return pasos, errores == 0 and pasos[-1][3] == "ACEPTAR", errores


st.set_page_config(page_title="Analizador LL(1)", layout="wide")
st.markdown("""<style>html, body, [class*="css"]  {font-family: 'Arial', sans-serif; font-size: 18px; background-color: #f4f4f4; color: #333;} th, td { text-align: center !important; padding: 6px 12px;} .stTable tbody tr td { font-size: 16px;} .stButton > button { background-color: #007bff; color: white; font-size: 18px; border-radius: 5px; padding: 8px 15px;} </style>""", unsafe_allow_html=True)

st.title("🎯 **Analizador Predictivo LL(1)** - Estilo Clásico")
st.markdown("""#### **Instrucciones**: - Ingrese una gramática LL(1) usando `->` para producciones y `ε` para vacío. - Separe tokens en la cadena con espacios. Ejemplo: `id + id * id` ### Gramática LL(1):""")

gramatica_input = st.text_area("Gramática LL(1):", value="Struct -> struct Nombre { Comps }\nNombre -> id\nComps -> Comp Comps'\nComps' -> ; Comp Comps'\nComps' -> ε\nComp -> Type id\nType -> Typep\nType -> struct id\nType -> Pointer\nTypep -> int\nTypep -> char\nTypep -> bool\nTypep -> float\nPointer -> * id", height=220)
cadena_input = st.text_input("Cadena de entrada:", "struct id { int id ; struct id id ; * id id }")

st.markdown("### **Analizar**:")
if st.button("Analizar"):
    reglas, _, no_terminales, terminales = procesar_gramatica(gramatica_input)
    firsts = obtener_firsts(reglas, no_terminales, terminales)
    follows = obtener_follows(reglas, no_terminales, firsts, terminales)
    tabla = construir_tabla(reglas, firsts, follows, terminales, no_terminales)
    pasos, aceptada, num_errores = analizar_cadena(cadena_input, tabla, no_terminales[0], terminales, no_terminales, follows)

    st.subheader("Tabla **First & Follow**")
    df_ff = pd.DataFrame({
        "No Terminal": no_terminales,
        "FIRST": [', '.join(firsts[nt]) for nt in no_terminales],
        "FOLLOW": [', '.join(follows[nt]) for nt in no_terminales]
    })
    st.table(df_ff)

    st.subheader("Tabla **LL(1)**")
    df_ll1 = pd.DataFrame(tabla).fillna('')
    st.table(df_ll1)

    st.subheader("**Tabla de Análisis paso a paso**")
    df_pasos = pd.DataFrame(pasos, columns=["Paso", "Pila", "Entrada", "Acción"])
    st.table(df_pasos)

    if aceptada:
        st.success("✅ **Cadena aceptada correctamente.**")
    else:
        st.error(f"❌ **Cadena rechazada. Se encontraron {num_errores} errores.**")
    
    st.markdown("### Desarrollado por José Eduardo Huamani Ñaupas")

    
