import sys
from pathlib import Path
from time import perf_counter

WIDTH = 320
HEIGHT = 240
PALETTE_SIZE = 256
FILE_LENGTH = WIDTH * HEIGHT


def read_exact(file, length):
    # Leemos la cantidad de bytes indicada y comprobamos que estén completos.
    data = file.read(length)
    if len(data) != length:
        raise ValueError('El archivo comprimido está incompleto')
    return data


def read_huffman_header(file, number_of_codes=None):
    # El primer byte indica cuántos símbolos contiene la tabla de Huffman.
    if number_of_codes is None:
        number_of_codes = read_exact(file, 1)[0]
    if not 1 <= number_of_codes <= 256:
        raise ValueError('Cantidad de símbolos inválida')

    coding = {}
    used_colors = set()

    for _ in range(number_of_codes):
        # Cada entrada contiene el color, la longitud y el código Huffman.
        color = read_exact(file, 1)[0]
        code_length = read_exact(file, 1)[0]
        if code_length == 0 or color in used_colors:
            raise ValueError('Tabla de Huffman inválida')

        # Redondeamos hacia arriba para saber cuántos bytes ocupa el código.
        number_of_bytes = (code_length + 7) // 8
        packed_code = read_exact(file, number_of_bytes)

        # Recuperamos los bits, incluyendo los ceros a la izquierda.
        bits = ''.join(f'{byte:08b}' for byte in packed_code)
        # Quitamos los ceros de relleno que agregó el compresor.
        code = bits[:code_length]
        if '1' in bits[code_length:] or code in coding:
            raise ValueError('Código Huffman inválido')

        # Guardamos el código como clave y el color como valor para decodificar.
        coding[code] = color
        used_colors.add(color)

    return coding


def build_tree(coding):
    # Reconstruimos el árbol a partir de los códigos recibidos, no de frecuencias.
    tree = {}
    for code, color in coding.items():
        node = tree
        # Cada bit representa una rama: 0 a la izquierda y 1 a la derecha.
        for bit in code[:-1]:
            node = node.setdefault(int(bit), {})
            if isinstance(node, int):
                raise ValueError('Los códigos Huffman se superponen')

        # Al llegar al último bit guardamos el color en la hoja del árbol.
        last_bit = int(code[-1])
        if last_bit in node:
            raise ValueError('Los códigos Huffman se superponen')
        node[last_bit] = color

    return tree


def decompress_payload(payload, tree, expected_length=FILE_LENGTH):
    if expected_length < 1:
        raise ValueError('La longitud esperada debe ser positiva')
    # Los códigos cortos se resuelven con una consulta por símbolo, evitando
    # divisiones, búsquedas y comprobaciones de tipo por cada bit en ARMv6.
    # Los códigos mayores de 8 bits conservan el recorrido del árbol original.
    lookup = [None] * 256
    for prefix in range(256):
        node = tree
        for length in range(1, 9):
            branch = node.get((prefix >> (8 - length)) & 1)
            if branch is None:
                break
            if isinstance(branch, int):
                lookup[prefix] = (branch, length)
                break
            node = branch

    recovered = bytearray()
    append = recovered.append
    position = accumulator = bits = 0
    for _ in range(expected_length):
        while bits < 8 and position < len(payload):
            accumulator = (accumulator << 8) | payload[position]
            position += 1
            bits += 8
        entry = lookup[(accumulator >> (bits - 8)) & 255] if bits >= 8 else None
        if entry is not None:
            symbol, length = entry
            bits -= length
            accumulator &= (1 << bits) - 1
        else:
            node = tree
            while not isinstance(node, int):
                if bits == 0:
                    if position == len(payload):
                        raise ValueError('No se recuperaron todos los píxeles de la imagen')
                    accumulator = payload[position]
                    position += 1
                    bits = 8
                bits -= 1
                bit = (accumulator >> bits) & 1
                accumulator &= (1 << bits) - 1
                if bit not in node:
                    raise ValueError('El payload contiene un código inválido')
                node = node[bit]
            symbol = node
        append(symbol)

    remaining = bits + (len(payload) - position) * 8
    if remaining > 7 or accumulator:
        raise ValueError('El relleno del payload es inválido')
    return bytes(recovered)


def rebuild_palette():
    # Las imágenes del proyecto usan una paleta estándar de escala de grises.
    # Cada color ocupa cuatro bytes: azul, verde, rojo y un byte reservado en cero.
    palette = bytearray()
    for color in range(PALETTE_SIZE):
        palette.extend([color, color, color, 0])
    return bytes(palette)


def decompress(input_file, output_file):
    with open(input_file, 'rb') as stream:
        magic = stream.read(4)
    if magic == b'HUF2':
        from transmision.codecs import huffman_decode
        restored = huffman_decode(Path(input_file).read_bytes())
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        Path(output_file).write_bytes(restored)
        return
    # Leemos el archivo en el mismo orden en que Javier lo escribió.
    with open(input_file, 'rb') as file:
        identifier = file.read(1)
        if (identifier == b"B"):
            coding = read_huffman_header(file)
            header = read_exact(file, 54)
            payload = file.read()
            palette = rebuild_palette()
            # Comprobamos que el encabezado corresponde al tipo de BMP del proyecto.
            if (header[:2] != b'BM' or int.from_bytes(header[10:14], 'little') != 1078
                    or int.from_bytes(header[14:18], 'little') != 40
                    or int.from_bytes(header[18:22], 'little', signed=True) != WIDTH
                    or abs(int.from_bytes(header[22:26], 'little', signed=True)) != HEIGHT
                    or int.from_bytes(header[28:30], 'little') != 8
                    or int.from_bytes(header[30:34], 'little') != 0):
                raise ValueError('El encabezado BMP no corresponde al formato del proyecto')
        elif (identifier == b"P"):
            coding = read_huffman_header(file)
            header = read_exact(file, 15)
            payload = file.read()
            palette = bytes(0) # Inexistent on PGM file
        else:
            raise ValueError("No se recuperó el tipo de archivo")

    tree = build_tree(coding)
    pixels = decompress_payload(payload, tree)

    # Volvemos a unir el encabezado, la paleta y los píxeles en el orden original.
    with open(output_file, 'wb') as file:
        file.write(header)
        if (identifier == b"B"): file.write(palette)
        file.write(pixels)


def main():
    # Recibimos el nombre del archivo comprimido y el nombre del BMP de salida.
    if len(sys.argv) != 3:
        print('Uso: python descompresor_sin_perdidas.py entrada.bin salida.bmp')
        return 1

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    try:
        if Path(input_file).resolve() == Path(output_file).resolve():
            raise ValueError('La entrada y la salida deben ser archivos diferentes')

        # Medimos el tiempo que tarda el proceso completo de descompresión.
        # start = perf_counter()
        decompress(input_file, output_file)
        # elapsed = perf_counter() - start
        # Measuring decompression time is unnecessary, good for debugging

        # print(f'Imagen recuperada: {output_file}')
        # print(f'Tamaño recuperado: {Path(output_file).stat().st_size} bytes')
        # print(f'Tiempo de descompresión: {elapsed * 1000:.3f} ms')
    except (OSError, ValueError) as error:
        print(f'Error: {error}')
        return 1
    return 0


# Ejecutamos main solamente cuando este archivo se usa como programa principal.
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    sys.exit(main())
