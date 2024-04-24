from PIL import Image
import os

DISTORTED_DIGITS_DIR = "distorted"
DIGITS_DIR = "digits"
DIGITS_NAMES = ['2', '3', '4', '5']
DIGITS_W = 10
DIGITS_H = 10
DIGITS_SQUARE = DIGITS_W * DIGITS_H
DIGITS_HASHES = {}


def empty_matrix(size: int) -> list:
    return [[0] * size for _ in range(size)]


def empty_list(size: int) -> list:
    return [0 for _ in range(size)]


def load_image_matrix(image_path: str) -> tuple[int, list]:
    with Image.open(image_path) as im:
        # resize to 10x10
        if im.size != (DIGITS_W, DIGITS_H):
            im = im.resize((DIGITS_W, DIGITS_H))
        # convert images to a 1-bit pixels, black and white, stored with one pixel per byte:
        # https://pillow.readthedocs.io/en/latest/handbook/concepts.html#concept-modes
        im = im.convert('1', colors=2)
        # convert 0:255 to 1:-1
        picture_data = list(map(lambda p: -1 if p == 255 else 1, list(im.getdata())))
        return hash(tuple(picture_data)), picture_data


def make_memory(matrixes: list[list]) -> list[list[int]]:
    memory = empty_matrix(DIGITS_SQUARE)
    # fill w-matrix with computed values
    for i in range(DIGITS_SQUARE):
        for j in range(DIGITS_SQUARE):
            for k in range(len(matrixes)):
                if i != j:
                    memory[i][j] += matrixes[k][i] * matrixes[k][j]
    return memory


def recognize(image_matrix: list, memory: list[list[int]]):
    # original state slice
    y = image_matrix[:]
    loops_count = 0
    # start recognition
    while True:
        loops_count += 1
        # compute new neurons state
        s = empty_list(DIGITS_SQUARE)
        for i in range(DIGITS_SQUARE):
            for j in range(DIGITS_SQUARE):
                s[j] += y[i] * memory[i][j]
        # slice to result from current state
        y_res = y[:]
        for i in range(DIGITS_SQUARE):
            # apply neuron state to a result instance
            if s[i] < 0:
                y_res[i] = -1
            elif s[i] > 0:
                y_res[i] = 1
        # break infinite loop in case
        # when original state is equal to result state
        if y == y_res:
            break
        # or assign result state as original
        y = y_res
    # return
    return y, loops_count


# import original images
pictures_matrix = []
for im_num in DIGITS_NAMES:
    im_path = os.path.join(DIGITS_DIR, im_num + ".gif")
    im_hash, im_matrix = load_image_matrix(im_path)
    # print(im_path, im_hash)
    pictures_matrix.append(im_matrix)
    DIGITS_HASHES.setdefault(im_hash, im_num)

# print(pictures_matrix)

# build w-matrix (Матриця вагових коефіцієнтів)
w = make_memory(pictures_matrix)

# walk through all distorted and original images in the directory
for distorted_im in sorted(next(os.walk(DISTORTED_DIGITS_DIR), (None, None, []))[2]):
    # build distorted image matrix
    dim_hash, dim_matrix = load_image_matrix(os.path.join(DISTORTED_DIGITS_DIR, distorted_im))
    # try to recognize the distorted image
    result_matrix, loops = recognize(dim_matrix, w)
    result_hash = hash(tuple(result_matrix))
    # print result
    if result_hash in DIGITS_HASHES:
        print(f"File {distorted_im} recognized as {DIGITS_HASHES[result_hash]} with {loops} loop(s)")
    else:
        print(f"File {distorted_im} NOT recognized with {loops} loop(s)!")

