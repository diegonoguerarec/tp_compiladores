#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import unicodedata
from typing import List, Tuple, Dict, Any

def strip_accents(text: str) -> str:
    """
    Elimina los acentos de un texto y devuelve la versión normalizada.
    """
    return ''.join(
        ch for ch in unicodedata.normalize('NFD', text)
        if unicodedata.category(ch) != 'Mn'
    )

def load_lexicon(path: str = 'tokens.json') -> Tuple[Dict[str,int], Dict[str,int], Dict[str,int]]:
    """
    Carga desde el JSON las categorías de tokens:
    - positivos: palabra -> peso > 0
    - negativos: palabra -> peso < 0
    - neutros:    palabra -> 0
    """
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return (
        data.get('positivos', {}),
        data.get('negativos', {}),
        data.get('neutros', {})
    )

# ─── Patrones de protocolo (sin acentos) ────────────────────────────────────

# 1) SALUDOS: variantes de saludo inicial que el agente podría usar
SALUDOS = [
    # Básicos
    r'\bhola\b',
    r'\bbuen[oa]s?\b',                      # hola, buenas, buen día
    r'\bbuenos dias\b',
    r'\bbuenas tardes\b',
    r'\bbuenas noches\b',
    r'\bfeliz dia\b',
    r'\bfeliz jornada\b',
    # Muy formales
    r'\bestimad[ao]s?\b',                   # estimado/a(s)
    r'\bsaludos cordiales\b',
    r'\bbienvenid[oa]s?\b',
    r'\bgracias por llamar\b',
    r'\bgracias por contactar\b',
    r'\bgracias por comunicarse\b',
    r'\bgracias por elegirnos\b',
    r'\bgracias por su preferencia\b',
    r'\bles saluda\b',
    r'\besta es la linea de\b',
    r'\blínea de atencion\b',
    r'\bes un placer atenderle\b',
    r'\bmucho gusto en atenderle\b',
    # Preguntas de apertura
    r'\ben que puedo ayudarle\b',
    r'\bcomo puedo ayudarle\b',
    r'\ben que le podemos ayudar\b',
    r'\b¿?en que puedo asistirle\b',
    r'\b¿?en que le puedo servir\b',
    # Variantes informales
    r'\bque tal\b',
    r'\bqué tal\b',
    r'\bholas\b'
]

# 2) ID_PATTERNS: frases para solicitar datos de identificación del cliente
ID_PATTERNS = [
    # Números de documento
    r'\bnumero de documento\b',
    r'\bnumero de cedula\b',
    r'\bdni\b',
    r'\bci\b',
    r'\bdocumento de identidad\b',
    # Cuentas y clientes
    r'\bnumero de cuenta\b',
    r'\bnumero de cliente\b',
    r'\bcodigo de cliente\b',
    r'\breferencia de cliente\b',
    r'\bcodigo de usuario\b',
    r'\bnumero de orden\b',
    # Datos personales
    r'\bnombre completo\b',
    r'\bnombre y apellido\b',
    r'\bapellido\b',
    r'\bfecha de nacimiento\b',
    r'\bnumero de telefono\b',
    r'\btelefono celular\b',
    r'\bwhatsapp\b',
    r'\bcorreo electr[oó]nico\b',
    r'\bdireccion\b',
    # Formas de pedirlo
    r'\bpuede (?:darme|facilitarme|proporcionarme) su (?:numero de )?(?:documento|cedula|dni|ci|numero de cliente)\b',
    r'\bpodria (?:darme|facilitarme|proporcionarme) su (?:numero de )?(?:documento|cedula|dni|ci|numero de cliente)\b',
    r'\bconfirmar su (?:numero de )?(?:documento|cedula|dni|ci)\b',
    r'\bpara verificar su identidad\b',
    r'\bpara confirmar su cuenta\b'
]

# 3) PALABRAS_RUDAS: términos que no deberían aparecer en una atención cordial
PALABRAS_RUDAS = [
    # Insultos comunes
    r'\btonto\b', r'\bidiota\b', r'\best[úu]pido\b', r'\bimb[ée]cil\b',
    r'\bpendejo\b', r'\btarado\b', r'\bgilipollas\b', r'\bmaldito\b',
    r'\bcabr[oó]n\b', r'\bco[ñn]o\b', r'\bmierda\b',
    # Descalificativos
    r'\bpat[ée]tico\b', r'\bdespreciable\b', r'\bestupidez\b',
    r'\bmediocre\b', r'\babsurdo\b', r'\batroz\b', r'\bhorrible\b',
    r'\bdesastroso\b', r'\bp[eé]simo\b', r'\bdefectuoso\b',
    r'\bdeficiente\b', r'\bineficiente\b', r'\binsuficiente\b',
    r'\bincompetente\b', r'\bfraudulento\b', r'\bterrible\b',
    r'\blamentable\b', r'\brepugnante\b', r'\bvergonzoso\b'
]

# 4) DESPEDIDAS: cierres cordiales que confirman una despedida amable
DESPEDIDAS = [
    r'gracias por su tiempo\b',
    r'gracias por llamar al servicio de atencion al cliente\b',
    r'gracias por contactar con nosotros\b',
    r'gracias por comunicarse con nosotros\b',
    r'gracias por elegirnos\b',
    r'muchas gracias\b',
    r'muchas gracias por su preferencia\b',
    r'ha sido un placer atenderle\b',
    r'estamos a su disposicion\b',
    r'quedo a sus ordenes\b',
    r'quedo a su disposicion\b',
    r'no dude en contactarnos\b',
    r'hasta luego\b',
    r'hasta pronto\b',
    r'hasta la proxima\b',
    r'hasta manana\b',
    r'hasta mañana\b',
    r'nos vemos\b',
    r'nos mantenemos en contacto\b',
    r'que tenga un buen dia\b',
    r'que tenga un excelente dia\b',
    r'le deseamos un buen dia\b',
    r'que disfrute el resto de su dia\b',
    r'que pase un buen dia\b',
    r'feliz dia\b',
    r'adios\b',
    r'adiós\b'
]

def normalize_text(text: str) -> List[str]:
    """
    Convierte el texto a minúsculas, quita acentos y extrae todas las palabras
    formadas solo por letras a–z.
    """
    clean = strip_accents(text.lower())
    return re.findall(r"[a-z]+", clean)

def analiza_sentimiento(
    words: List[str],
    positivos: Dict[str,int],
    negativos: Dict[str,int],
    neutros: Dict[str,int]
) -> Tuple[
    int,
    int, List[str], List[str], int,
    int, List[str], List[str], int,
    int, List[str]
]:
    """
    Calcula:
      - total: suma de todos los pesos (positivos + negativos)
      - pos_count     y lista pos_words
      - top_pos_words (todas con el peso máximo positivo) y top_pos_weight
      - neg_count     y lista neg_words
      - top_neg_words (todas con el peso mínimo negativo) y top_neg_weight
      - neut_count    y lista neut_words
    """
    total = 0
    pos_list: List[Tuple[str,int]] = []
    neg_list: List[Tuple[str,int]] = []
    neut_list: List[str] = []

    for w in words:
        if w in positivos:
            p = positivos[w]
            total += p
            pos_list.append((w, p))
        elif w in negativos:
            n = negativos[w]
            total += n
            neg_list.append((w, n))
        elif w in neutros:
            neut_list.append(w)

    pos_count = len(pos_list)
    neg_count = len(neg_list)
    neut_count = len(neut_list)

    pos_words = [w for w, _ in pos_list]
    neg_words = [w for w, _ in neg_list]

    if pos_list:
        top_pos_weight = max(p for _, p in pos_list)
        top_pos_words = [w for w, p in pos_list if p == top_pos_weight]
    else:
        top_pos_weight = 0
        top_pos_words = []

    if neg_list:
        top_neg_weight = min(n for _, n in neg_list)
        top_neg_words = [w for w, n in neg_list if n == top_neg_weight]
    else:
        top_neg_weight = 0
        top_neg_words = []

    return (
        total,
        pos_count, pos_words, top_pos_words, top_pos_weight,
        neg_count, neg_words, top_neg_words, top_neg_weight,
        neut_count, neut_list
    )

def analiza_protocolo(text: str) -> Tuple[bool,bool,List[str],bool]:
    """
    Valida:
      - saludo en la primera línea
      - identificación en todo el texto
      - palabras rudas en todo el texto
      - despedida en la última línea
    """
    clean = strip_accents(text.lower())
    lines = [l.strip() for l in clean.splitlines() if l.strip()]
    first = lines[0] if lines else ''
    last  = lines[-1] if lines else ''

    saludo_ok = any(re.search(p, first) for p in SALUDOS)
    id_ok     = any(re.search(p, clean) for p in ID_PATTERNS)
    rudas     = [m.group() for p in PALABRAS_RUDAS for m in re.finditer(p, clean)]
    desp_ok   = any(re.search(p, last) for p in DESPEDIDAS)

    return saludo_ok, id_ok, rudas, desp_ok

def find_undefined(
    words: List[str],
    positivos: Dict[str,int],
    negativos: Dict[str,int],
    neutros: Dict[str,int]
) -> List[str]:
    """
    Lista de palabras no presentes en ninguno de los tres lexicones.
    """
    return sorted({
        w for w in words
        if w not in positivos
        and w not in negativos
        and w not in neutros
    })

def run_analysis(path_txt: str) -> Dict[str, Any]:
    """
    Ejecuta todo el análisis y devuelve un diccionario con resultados.
    """
    texto = open(path_txt, encoding='utf-8').read()
    pos, neg, neut = load_lexicon()
    words = normalize_text(texto)

    (
        total,
        pos_count, pos_words, top_pos_words, top_pos_weight,
        neg_count, neg_words, top_neg_words, top_neg_weight,
        neut_count, neut_words
    ) = analiza_sentimiento(words, pos, neg, neut)

    saludo, ident, rudas, desp = analiza_protocolo(texto)
    undefined = find_undefined(words, pos, neg, neut)

    return {
        'total': total,
        'pos_count': pos_count,
        'pos_words': pos_words,
        'top_pos_words': top_pos_words,
        'top_pos_weight': top_pos_weight,
        'neg_count': neg_count,
        'neg_words': neg_words,
        'top_neg_words': top_neg_words,
        'top_neg_weight': top_neg_weight,
        'neut_count': neut_count,
        'neut_words': neut_words,
        'saludo': saludo,
        'ident': ident,
        'rudas': rudas,
        'desp': desp,
        'undefined': undefined
    }

