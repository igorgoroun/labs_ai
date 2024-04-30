import os
import random

import click
import redis
import math
from dotenv import load_dotenv
from PIL import Image

load_dotenv()
# connect to redis
db = redis.Redis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'), decode_responses=True)

# define some static values
DIGITS_W = 10
DIGITS_H = 10
DIGITS_SQUARE = DIGITS_W * DIGITS_H
CLASSES = ['2', '3', '4', '5', '7']
INITIAL_WEIGHT_RANGE = [-0.3, 0.3]
WEIGHT_STEP = 0.05
N_MAX = 30
DEFINITION_ENOUGH = 0.95
DEFINITION_LESS = 0.05

# KEY_DEFINITIONS = f"{os.getenv('REDIS_KEY')}.definitions"
KEY_PRIMAL_WEIGHTS = f"{os.getenv('REDIS_KEY')}:inner_weights"
# KEY_PRIMAL_RESULT = f"{os.getenv('REDIS_KEY')}:result_primal"
KEY_CLASS_WEIGHTS = f"{os.getenv('REDIS_KEY')}:outer_weights"
# KEY_CLASS_RESULT = f"{os.getenv('REDIS_KEY')}:result_class"

PRIMAL_NEURONS_COUNT = int(math.ceil(DIGITS_SQUARE / 10 * 5))
CLASS_NEURONS_COUNT = len(CLASSES)


def empty_list(size: int, initial: float = 0) -> list:
    return [initial for _ in range(size)]


def empty_matrix(i: int, j: int) -> list[list[int]]:
    return [[0] * j for _ in range(i)]


def expected_learn_definitions(result: str) -> list[float]:
    definitions = empty_list(len(CLASSES), DEFINITION_LESS)
    definitions[CLASSES.index(result)] = DEFINITION_ENOUGH
    return definitions


def load_image_matrix(image_path: str) -> tuple[int, list]:
    with Image.open(image_path) as im:
        # resize to 10x10
        if im.size != (DIGITS_W, DIGITS_H):
            im = im.resize((DIGITS_W, DIGITS_H))
        # convert images to a greyscale:
        # https://pillow.readthedocs.io/en/latest/handbook/concepts.html#concept-modes
        # im = im.convert('L')
        im = im.convert('1', colors=2)
        # normalize data
        # picture_data = list(im.getdata())
        # n_min = min(*picture_data)
        # n_max = max(*picture_data)
        # normalized_data = [(x - n_min) / (n_max - n_min) for x in picture_data]
        normalized_data = list(map(lambda p: -1 if p == 255 else 1, list(im.getdata())))
        return hash(tuple(normalized_data)), normalized_data


class RedisMatrix:
    def __init__(self, key: str, n: int, m: int) -> None:
        self.key = key
        self.n = n
        self.m = m

    def get(self, i: int, j: int) -> float:
        res = db.lrange(f"{self.key}:{i}", j, j)
        if len(res) > 0:
            return float(res[0])
        raise KeyError(f"No such element [{i}][{j}]")

    def set(self, i: int, j: int, val: float):
        if i >= self.n or j >= self.m:
            raise IndexError(f"No such element [{i}][{j}]")
        db.lset(f"{self.key}:{i}", j, str(val))

    def create(self) -> None:
        for i in range(self.n):
            db.lpush(f"{self.key}:{i}", *empty_list(self.m))

    def clean(self):
        for key in db.scan_iter(f"{self.key}:*"):
            db.delete(key)

    def print_matrix(self) -> None:
        for i in range(self.n):
            line = list(map(float, db.lrange(f"{self.key}:{i}", 0, self.m - 1)))
            click.echo(line)


class Neuron(RedisMatrix):

    expected_output: list[float]
    inputs: list[float]
    weighted: list[float]
    outputs: list[float]

    def init_weights(self, range_start: float = -0.3, range_end: float = 0.3):
        for i in range(self.n):
            for j in range(self.m):
                w = round(random.uniform(range_start, range_end), 3)
                db.lset(f"{self.key}:{i}", j, str(w))

    def compute_weighted(self):
        self.weighted = empty_list(self.m)
        for i in range(self.n):
            for j in range(self.m):
                self.weighted[j] += self.get(i, j) * self.inputs[i]

    def compute_outputs(self):
        self.compute_weighted()
        self.outputs = empty_list(self.m)
        for j in range(self.m):
            self.outputs[j] = 1/(1 + math.exp(-self.weighted[j]))


class OuterNeuron(Neuron):
    def compute_weights(self):
        for j in range(self.n):
            for k in range(self.m):
                new_weight = self.get(j, k) - (WEIGHT_STEP * self.inputs[j] * self.outputs[k] * (self.outputs[k] - self.expected_output[k]) * (1 - self.outputs[k]))
                self.set(j, k, new_weight)


class InnerNeuron(Neuron):
    def compute_weights(self, outer_neuron: OuterNeuron):
        for i in range(self.n):
            for j in range(self.m):
                outer_sigma = sum([outer_neuron.get(j, p) * outer_neuron.outputs[p] * (outer_neuron.outputs[p] - self.expected_output[p]) * (1 - outer_neuron.outputs[p]) for p in range(outer_neuron.m)])
                new_weight = self.get(i, j) - (WEIGHT_STEP * self.inputs[i] * self.outputs[j] * (1 - self.outputs[j]) * outer_sigma)
                self.set(i, j, new_weight)


class NeuralNetwork:
    inner_neuron: InnerNeuron
    outer_neuron: OuterNeuron

    def __init__(self, inner_neuron: InnerNeuron, outer_neuron: OuterNeuron):
        self.inner_neuron = inner_neuron
        self.outer_neuron = outer_neuron

    def learn(self, input_data: list[float], expected_output: list[float]) -> None:
        # check result
        computed_result = self.result(input_data)
        print(f"Computed initial result: {[round(x, 2) for x in computed_result]}")
        iteration_number = 0
        while not self.result_ok(computed_result, expected_output):
            iteration_number += 1
            if iteration_number > N_MAX:
                break
            # recompute outer neuron weights
            self.outer_neuron.expected_output = expected_output
            self.outer_neuron.compute_weights()
            # recompute inner neuron weights
            self.inner_neuron.expected_output = expected_output
            self.inner_neuron.compute_weights(self.outer_neuron)
            # re-compute result with new weights
            computed_result = self.result(input_data)
            print(f"Iteration: {iteration_number} result: {[round(x, 2) for x in computed_result]}")

    def result_ok(self, result: list[float], expected_output: list[float]) -> bool:
        # find index of searched definition
        se = expected_output.index(max(expected_output))
        res = []
        for c in range(self.outer_neuron.m):
            if c == se and self.outer_neuron.outputs[c] >= expected_output[c]:
                res.append(True)
            elif c != se and self.outer_neuron.outputs[c] < expected_output[c]:
                res.append(True)
            else:
                res.append(False)
        # break and return if achieved the limits
        if all(res):
            return True
        return False

    def result(self, input_data: list[float]) -> list[float]:
        self.inner_neuron.inputs = input_data
        self.inner_neuron.compute_outputs()
        self.outer_neuron.inputs = self.inner_neuron.outputs
        self.outer_neuron.compute_outputs()
        return self.outer_neuron.outputs


@click.command()
@click.argument('image', type=click.Path(exists=True))
@click.argument('result', type=str)
def learn(image: str, result):
    """Learn a symbol from an image."""
    click.echo(f"Path is: {image}")
    click.echo(f"Expected result is: {result}")
    im_hash, im_data = load_image_matrix(image)
    click.echo(f"Data is: {im_data}")
    definitions = expected_learn_definitions(result)
    click.echo(f"Definitions are: {definitions}")
    inner_neuron = InnerNeuron(KEY_PRIMAL_WEIGHTS, DIGITS_SQUARE, PRIMAL_NEURONS_COUNT)
    outer_neuron = OuterNeuron(KEY_CLASS_WEIGHTS, PRIMAL_NEURONS_COUNT, CLASS_NEURONS_COUNT)
    neural_net = NeuralNetwork(inner_neuron, outer_neuron)
    neural_net.learn(im_data, definitions)


@click.command()
@click.argument('image', type=click.Path(exists=True))
def test(image: str):
    """Test what a symbol is on image."""
    im_hash, im_data = load_image_matrix(image)
    inner_neuron = InnerNeuron(KEY_PRIMAL_WEIGHTS, DIGITS_SQUARE, PRIMAL_NEURONS_COUNT)
    outer_neuron = OuterNeuron(KEY_CLASS_WEIGHTS, PRIMAL_NEURONS_COUNT, CLASS_NEURONS_COUNT)
    neural_net = NeuralNetwork(inner_neuron, outer_neuron)

    outer_neuron_output = neural_net.result(im_data)
    combined = dict(zip(CLASSES, outer_neuron_output))
    result = dict(sorted(combined.items(), key=lambda item: item[1], reverse=True))
    uf_results = [f"[{k}]: {round(v*100, 2)}%" for k, v in result.items()]
    print("RESULT:\t", "\t".join(uf_results))


@click.command()
def init():
    click.echo("(Re)Initializing data...")
    # re-init inner neuron weights matrix
    inner_matrix = Neuron(KEY_PRIMAL_WEIGHTS, DIGITS_SQUARE, PRIMAL_NEURONS_COUNT)
    inner_matrix.clean()
    inner_matrix.create()
    inner_matrix.init_weights()
    # re-init outer neuron weights matrix
    outer_matrix = Neuron(KEY_CLASS_WEIGHTS, PRIMAL_NEURONS_COUNT, CLASS_NEURONS_COUNT)
    outer_matrix.clean()
    outer_matrix.create()
    outer_matrix.init_weights()
    # outer_matrix.print_matrix()


@click.group()
def numbers():
    pass


numbers.add_command(learn)
numbers.add_command(test)
numbers.add_command(init)

if __name__ == '__main__':
    numbers()
