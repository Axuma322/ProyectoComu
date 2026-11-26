# Huffman Lossless Compressor - C32382 - IE_0527
import heapq
import struct
import sys

WIDTH = 320
HEIGHT = 240
PALETTE_SIZE = 256
FILE_LENGTH = 76800

def read_bmp(file_path : str):
    # Open file and read as bytes
    with open(file_path, mode="rb") as file:
        # Get the headers for the file
        header_file = file.read(14)
        header_dib = file.read(40)
        header_palette = []
        # Grayscale is implemented as consequent brightness values (0-256) where B=G=R
        # Thus, it is sufficient to read only the blue channel to form the coding
        for color in range(PALETTE_SIZE):
            header_palette.append(file.read(1))
            file.read(3)
        pixel_array = {}
        payload_array = []
        for color in header_palette:
            pixel_array[color] = 0
        for i in range(FILE_LENGTH):
            read_byte = file.read(1)
            payload_array.append(read_byte)
            for byte_palette in pixel_array:
                if (read_byte == byte_palette):
                    pixel_array[byte_palette] += 1
    file.close()
    return (pixel_array, header_file, header_dib, payload_array)

def read_pgm(file_path: str):
    with open(file_path, mode="rb") as file:
        file.read(15) # Discard header, will be rebuilt later on known parameters
        pixel_array = {}
        # Initialize the pixel array manually, as header was discarded
        for i in range (256):
            pixel_array[i.to_bytes(1, "big")] = 0
        payload_array = []
        for i in range(FILE_LENGTH):
            read_byte = file.read(1)
            payload_array.append(read_byte)
            for byte_palette in pixel_array:
                if (read_byte == byte_palette):
                    pixel_array[byte_palette] += 1
    file.close()
    return (pixel_array, payload_array)

# GeekForGeeks algorithm modified to adapt to the needs of the compressor

# ---
# Class to represent Huffman tree node
class Node:

    # Leaf node
    def __init__(self, d, i, left=None, right=None):
        # frequency
        self.data = d

        # smallest original index in subtree
        self.index = i

        # smallest original index in subtree
        self.left = left
        self.right = right

# Function to traverse tree in preorder
# manner and push the Huffman representation
# of each character.
def preOrder(root, ans, curr):
    if root is None:
        return

    # Leaf node represents a character.
    if root.left is None and root.right is None:
        # single character case
        if curr == "":
            curr = "0"
        ans.append((root.index, curr))
        return

    preOrder(root.left, ans, curr + '0')
    preOrder(root.right, ans, curr + '1')

def huffmanCodes(tree_nodes: dict[bytes,int]) -> dict[bytes,str]:

    # Min heap for Node class.
    pq = []

    for key, val in tree_nodes.items():
        if (val != 0):
            # include index
            tmp = Node(val, key)
            heapq.heappush(pq, (tmp.data, tmp.index, tmp))

    if not pq:
        raise ValueError('No hay símbolos para codificar')
    if len(pq) == 1:
        return {pq[0][2].index: "0"}

    # Construct Huffman tree.
    while len(pq) >= 2:

        # Left node
        f1, i1, l = heapq.heappop(pq)

        # Right node
        f2, i2, r = heapq.heappop(pq)

        # internal node with freq + index
        newNode = Node(l.data + r.data, min(l.index, r.index), l, r)
        heapq.heappush(pq, (newNode.data, newNode.index, newNode))

    root = pq[0][2]
    ans = []
    preOrder(root, ans, "")
    coding = {}
    for i in ans:
        coding[i[0]] = i[1]
    return coding
# ---

def huffman_header(coding: dict[bytes,str]) -> bytes:
    packed_bytes = [] # Get a list of bytes to turn into a bytestream
    packed_bytes.append(struct.pack(">B", len(coding))) # Number of bytes coded
    # Code each byte in the format (color value (1 byte), number of bits (n) in the code (1 byte), code(n bits, padded to fit in bytes))
    for color, code in sorted(coding.items()):
        code_length = len(code).to_bytes(1, "big")
        if (len(code) % 8 != 0):
            padded_code = code + "0" * ((8 - len(code) % 8) % 8)
        else: padded_code = code
        packed_bytes.append(color)
        packed_bytes.append(code_length)
        packed_bytes.append(int(padded_code, 2).to_bytes((len(code)+7)//8, "big"))
    return b"".join(packed_bytes)


def compress_payload(payload_array: list[bytes], coding: dict[bytes,str]):
    raw_filestring = ""
    for raw_byte in payload_array:
        for value, code in coding.items():
            if (raw_byte == value):
                raw_filestring = raw_filestring + code
    if (len(raw_filestring) % 8 != 0):
        padded_raw_filestring = raw_filestring + "0" * ((8 - len(raw_filestring) % 8) % 8)
    else: padded_raw_filestring = raw_filestring
    payload_str_bit_list = [padded_raw_filestring[i:i+8] for i in range(0, len(padded_raw_filestring), 8)]
    payload_list = []
    for byte_str in payload_str_bit_list:
        byte_to_pack = int(byte_str, 2)
        payload_list.append(struct.pack(">B", byte_to_pack))
    return b"".join(payload_list)


def legacy_main():
    file_name = sys.argv[1]
    output_file_name = sys.argv[2]
    try:
        file_extension = file_name.split(".")
        if (file_extension[1] == "bmp"):
            (pixel_array, header_file, header_dib, payload_array) = read_bmp(file_name)
            header = b"".join([header_file,header_dib])
            color_freq = {}
            for byte_palette in pixel_array:
                if (pixel_array[byte_palette] != 0):
                    color_freq[byte_palette] = pixel_array[byte_palette]
            coding = huffmanCodes(pixel_array)
            raw_huffman_table = huffman_header(coding)
            compressed_payload = compress_payload(payload_array, coding)
            with open(output_file_name, "+wb") as bin_file:
                bin_file.write(b"B")
                bin_file.write(raw_huffman_table)
                bin_file.write(header)
                bin_file.write(compressed_payload)
            bin_file.close()
        elif (file_extension[1] == "pgm"):
            (pixel_array, payload_array) = read_pgm(file_name)
            color_freq = {}
            for byte_palette in pixel_array:
                if (pixel_array[byte_palette] != 0):
                    color_freq[byte_palette] = pixel_array[byte_palette]
            coding = huffmanCodes(pixel_array)
            raw_huffman_table = huffman_header(coding)
            compressed_payload = compress_payload(payload_array,coding)
            with open(output_file_name, "+wb") as bin_file:
                bin_file.write(b"P")
                bin_file.write(raw_huffman_table)
                bin_file.write(b"P5\n320 240\n255\n")
                bin_file.write(compressed_payload)
        else:
            print("File extension invalid")
            return
    except:
        print("Couldn't parse arguments or filepath")
def compress(input_file, output_file):
    from pathlib import Path
    from transmision.codecs import encode
    if Path(input_file).resolve() == Path(output_file).resolve():
        raise ValueError('La entrada y la salida deben ser diferentes')
    data, metadata = encode(input_file, 'sin_perdidas')
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    Path(output_file).write_bytes(data)
    return metadata


def main():
    import argparse
    import json
    parser = argparse.ArgumentParser(description='Huffman sin pérdidas; contenedor HUF2')
    parser.add_argument('entrada')
    parser.add_argument('salida')
    args = parser.parse_args()
    try:
        print(json.dumps(compress(args.entrada, args.salida)))
    except (ValueError, OSError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    sys.exit(main())
