#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import Levenshtein
from analysis import run_analysis, load_lexicon, strip_accents

def save_lexicon(positivos, negativos, neutros, path='tokens.json'):
    """
    Sobrescribe en el JSON los tres lexicones actualizados.
    """
    with open(path, 'r+', encoding='utf-8') as f:
        data = json.load(f)
        data['positivos'] = positivos
        data['negativos'] = negativos
        data['neutros']    = neutros
        f.seek(0)
        f.truncate()
        json.dump(data, f, ensure_ascii=False, indent=2)

def suggest_candidates(word: str, lex_keys: list[str], max_suggestions: int = 5):
    """
    Sugiere hasta `max_suggestions` palabras del lexicón,
    ordenadas por Levenshtein (y Hamming si aplicable).
    """
    dists = []
    for k in lex_keys:
        lev = Levenshtein.distance(word, k)
        ham = Levenshtein.hamming(word, k) if len(word) == len(k) else float('inf')
        dists.append((k, (lev, ham)))
    dists.sort(key=lambda x: (x[1][0], x[1][1]))
    return dists[:max_suggestions]

def prompt_user(undefined: list[str], positivos: dict, negativos: dict, neutros: dict, path_txt: str):
    """
    Interacción:
      - Elige palabra indefinida a procesar (no se elimina hasta terminar).
      - Si es válida: categoriza en P/N/T. Solo al agregarse con éxito se elimina.
      - Si no: sugiere candidatos y, al elegir uno, reemplaza en el TXT y se elimina.
    """
    lex_keys = list(positivos) + list(negativos) + list(neutros)

    while undefined:
        print("\nPalabras indefinidas pendientes:")
        for i, w in enumerate(undefined, start=1):
            print(f"  {i}. {w}")
        sel = input("\nSeleccione número de palabra (ENTER para terminar): ").strip()
        if not sel:
            print("Interacción finalizada.")
            break
        if not sel.isdigit() or not (1 <= int(sel) <= len(undefined)):
            print("  ❌ Selección inválida.")
            continue

        idx = int(sel) - 1
        raw = undefined[idx]
        word = strip_accents(raw.lower())
        print(f"\nProcesando: '{word}'")

        if input("  ¿Es un lexema válido? [s/N]: ").strip().lower() == 's':
            cat = input("  ¿[P]ositiva, [N]egativa o [T]erutral? ").strip().lower()
            if cat == 'p':
                peso = input("    Peso (+1 a +3): ").strip()
                try:
                    p = int(peso)
                    if 1 <= p <= 3 and word not in positivos:
                        positivos[word] = p
                        print(f"    ✅ Agregada '{word}': +{p}")
                        undefined.pop(idx)
                    else:
                        print("    ⚠️ No se agrega (fuera de rango o ya existe).")
                except ValueError:
                    print("    ❌ Peso inválido. Sigue pendiente.")
            elif cat == 'n':
                peso = input("    Peso (-1 a -3): ").strip()
                try:
                    n = int(peso)
                    if -3 <= n <= -1 and word not in negativos:
                        negativos[word] = n
                        print(f"    ✅ Agregada '{word}': {n}")
                        undefined.pop(idx)
                    else:
                        print("    ⚠️ No se agrega (fuera de rango o ya existe).")
                except ValueError:
                    print("    ❌ Peso inválido. Sigue pendiente.")
            elif cat == 't':
                if word not in neutros:
                    neutros[word] = 0
                    print(f"    ✅ Agregada '{word}' como neutro (0).")
                    undefined.pop(idx)
                else:
                    print("    ⚠️ Ya existe en neutros. Sigue pendiente.")
            else:
                print("    ❌ Categoría no válida. Sigue pendiente.")
        else:
            # flujo de sugerencias y reemplazo en el archivo
            print("  → No es válido. Buscando sugerencias...\n")
            cands = suggest_candidates(word, lex_keys)
            for i, (k, (lev, ham)) in enumerate(cands, start=1):
                ham_txt = f", Hamming={ham}" if ham != float('inf') else ""
                print(f"    {i}. {k} (Lev={lev}{ham_txt})")
            choice = input("\n  Elija número de candidato (ENTER para omitir): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(cands):
                cand = cands[int(choice)-1][0]
                print(f"  → Ha elegido '{cand}', actualizando texto...")
                with open(path_txt, 'r+', encoding='utf-8') as tf:
                    content = tf.read()
                    new_content = content.replace(raw, cand)
                    tf.seek(0)
                    tf.truncate()
                    tf.write(new_content)
                print("    ✅ Texto actualizado.")
                undefined.pop(idx)
            else:
                print("  → Omitido. Sigue pendiente.")

def main():
    if len(sys.argv) != 2:
        print("Uso: python interactive.py <archivo.txt>")
        sys.exit(1)

    path_txt = sys.argv[1]
    result = run_analysis(path_txt)

    # --- Resumen de resultados ---
    label = "Positivo" if result['total'] > 0 else "Negativo" if result['total'] < 0 else "Neutral"
    signo = f"{result['total']:+d}"
    print(f"\nSentimiento general: {label} ({signo})")
    print(f"Palabras positivas ({result['pos_count']}): {', '.join(result['pos_words']) or '-'}")
    print(f"Palabras más positivas (peso +{result['top_pos_weight']}): {', '.join(result['top_pos_words']) or '-'}")
    print(f"Palabras negativas ({result['neg_count']}): {', '.join(result['neg_words']) or '-'}")
    print(f"Palabras más negativas (peso {result['top_neg_weight']}): {', '.join(result['top_neg_words']) or '-'}")
    print(f"Palabras neutras ({result['neut_count']}): {', '.join(result['neut_words']) or '-'}")

    print("\n--- Cumplimiento de fases ---")
    print(f"Fase de saludo: {'OK' if result['saludo'] else 'Faltante'}")
    print(f"Identificación: {'OK' if result['ident'] else 'Faltante'}")
    print(f"Uso de palabras rudas: {', '.join(result['rudas']) or 'Ninguna'}")
    print(f"Despedida amable: {'OK' if result['desp'] else 'Faltante'}")

    print(f"\nPalabras indefinidas ({len(result['undefined'])}): {', '.join(result['undefined']) or '-'}")

    if result['undefined']:
        pos, neg, neut = load_lexicon()
        prompt_user(result['undefined'], pos, neg, neut, path_txt)
        save_lexicon(pos, neg, neut)
        print("\n>> tokens.json actualizado.")
    else:
        print("\nNo hay palabras indefinidas para procesar.")

if __name__ == "__main__":
    main()
