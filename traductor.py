import re


def extraer_impares(ruta_entrada: str, ruta_salida: str):
    """
    Lee 'ruta_entrada' buscando bloques que empiecen con 'Speaker X  hh:mm'.
    Ignora cualquier línea que comience con 'Transcribed by'.
    Extrae solo las intervenciones en posiciones impares (1, 3, 5, ...)
    guardando únicamente el texto (sin el encabezado Speaker, la hora ni 'Transcribed by')
    en 'ruta_salida'.
    """
    contador = 0
    incluir = False
    buffer_texto = []

    pattern_speaker = re.compile(r"^Speaker\s+\d+\s+\d{1,2}:\d{2}")
    pattern_transcribed = re.compile(r"^Transcribed by https://otter.ai", re.IGNORECASE)

    with open(ruta_entrada, "r", encoding="utf-8") as f_in:
        for linea in f_in:
            linea = linea.rstrip("\n")

            # Omitir cualquier línea que empiece con "Transcribed by"
            if pattern_transcribed.match(linea):
                continue

            # Si la línea indica el inicio de una intervención:
            if pattern_speaker.match(linea):
                contador += 1
                incluir = contador % 2 == 1
                if incluir:
                    buffer_texto.append("")  # inicializar nuevo bloque impar
                continue

            # Si estamos en un bloque impar, guardamos la línea
            if incluir:
                if linea.strip():
                    buffer_texto[-1] += linea + " "

    # Volcar cada bloque en una línea del archivo de salida
    with open(ruta_salida, "w", encoding="utf-8") as f_out:
        for bloque in buffer_texto:
            texto_limpio = bloque.strip()
            if texto_limpio:
                f_out.write(texto_limpio + "\n")


if __name__ == "__main__":
    # Ajusta aquí el nombre de tu archivo de entrada si no se llama "input.txt"
    extraer_impares("conv1.txt", "conversacion.txt")
    print("salida en conversacion.txt")
