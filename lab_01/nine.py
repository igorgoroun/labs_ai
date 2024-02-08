from random import choice
import time
import tracemalloc


class Done(Exception):
    
    def __init__(self, state: list, iterations: int):
        self.state = state
        self.iterations = iterations
    
    def __str__(self):
        return f"DONE!!!"


class Eights:
    evristic_classes: list = []
    INP_STATE: list = []     # = [2, 1, 4, 6, 8, 7, 0, 3, 5]
    # index:                 0  1  2  3  4  5  6  7  8
    RES_STATE: list = []     # = [1, 2, 3, 8, 0, 4, 7, 6, 5]
    STATE: list = []         # = INP_STATE.copy()
    POSSIBLE_MOVES: dict = {
        0: [1, 3],
        1: [0, 2, 4],
        2: [1, 5],
        3: [0, 4, 6],
        4: [1, 3, 5, 7],
        5: [2, 4, 8],
        6: [3, 7],
        7: [4, 6, 8],
        8: [5, 7]
    }
    CHECKED_STATES: list = []
    UNCHECKED_STATES: list = []
    ITER: int = 0
    PATH: list = []

    def __init__(self, input_state: list, result_state: list):
        self.INP_STATE = input_state
        self.RES_STATE = result_state
        self.STATE = input_state.copy()
        self.CHECKED_STATES = []
        self.UNCHECKED_STATES = []
        self.ITER = 0
        self.evristic_classes = []
        self.PATH = []

    def select_best_move(self, available_moves: list):
        if not self.evristic_classes:
            return available_moves[0]
        
        bests = dict()

        for evr in self.evristic_classes:
            e_res = evr(self.STATE, available_moves, self.RES_STATE, self).decide()
            bests.setdefault(e_res, 0)
            bests[e_res] = bests[e_res] + 1

        # print(bests)
        
        best_choice = None
        best_weight = 0
        for p_move, weight in bests.items():
            if weight >= best_weight:
                best_weight = weight
                best_choice = p_move
        # print(f"Best move is: {best_choice}")
        return best_choice

    def available_moves(self):
        moves = []
        # print(f"Possible moves: {self.POSSIBLE_MOVES.get(self.STATE.index(0))}")
        for possible_move in self.POSSIBLE_MOVES.get(self.STATE.index(0)):
            # print(f"Check is available move: {possible_move}")
            to_check_state = self.STATE.copy()
            zero_in = to_check_state.index(0)
            to_check_state[possible_move], to_check_state[zero_in] = to_check_state[zero_in], to_check_state[possible_move]
            if self.to_str(to_check_state) in self.CHECKED_STATES:
                # print(f"{to_check_state} in CHECKED_STATES")
                continue
            moves.append(possible_move)
        return moves

    def make_move(self):
        self.ITER += 1
        # print(f"Checking state: {self.STATE}")
        if self.is_result_state():
            # print(f"DONE!!! Result is: {state}, iterations: {i}")
            raise Done(self.STATE, self.ITER)
            # exit(1)
        self.CHECKED_STATES.append(self.to_str(self.STATE))
        available = self.available_moves()
        # print(f"Available moves: {available}")
        if not available:
            # self.make_move()
            return
        # print(f"Available moves: {available}")
        best_move = self.select_best_move(available)
        # print(f"Best move: {best_move}")
        other_moves = list(set(available) - {best_move})
        for other_move in other_moves:
            to_check_state = self.STATE.copy()
            to_check_state[other_move], to_check_state[to_check_state.index(0)] = to_check_state[to_check_state.index(0)], to_check_state[other_move]
            # print(f"Saving {other_move}")
            self.UNCHECKED_STATES.append(self.to_str(to_check_state))
        zero_in = self.STATE.index(0)
        # print(f"Zero in: {zero_in}")
        self.PATH.append(best_move)
        self.STATE[best_move], self.STATE[zero_in] = self.STATE[zero_in], self.STATE[best_move]
        # print(f"Updated state: {self.STATE}")
        self.UNCHECKED_STATES.append(self.to_str(self.STATE))

    def is_result_state(self):
        return self.STATE == self.RES_STATE

    @staticmethod
    def to_str(state: list):
        return "".join(map(str, state))

    @staticmethod
    def to_list(state: str):
        return list(map(int, [*state]))

    def compute(self):
        self.UNCHECKED_STATES.append(self.to_str(self.STATE))
        while len(self.UNCHECKED_STATES) > 0:
            self.STATE = self.to_list(self.UNCHECKED_STATES.pop())
            self.make_move()
            # if self.ITER >= 3:
            #     break


class Evristics:
    state: list = []
    available_moves: list = []
    resulting_state: list = []
    eights = None

    def __init__(self, state: list, available_moves: list, result_state: list, obj: Eights = None):
        self.state = state
        self.available_moves = available_moves
        self.resulting_state = result_state
        self.eights = obj

    def decide(self):
        raise


class LeftHand(Evristics):
    def decide(self):
        return self.available_moves[0]


class Manhattan(Evristics):
    def decide(self):
        # print("Manhattan decides")
        # return choice(self.available_moves)
        distances = dict()
        for possible_move in self.available_moves:
            # make a move
            next_state = self.state.copy()
            zero_cell = next_state.index(0)
            next_state[possible_move], next_state[zero_cell] = next_state[zero_cell], next_state[possible_move]
            distances.setdefault(possible_move, self.compute_distance(next_state))

        best_choice = None
        shortest_distance = None
        for p_move, distance in distances.items():
            if shortest_distance is None or distance <= shortest_distance:
                shortest_distance = distance
                best_choice = p_move
        # print(f"Shortest: {best_choice}")
        return best_choice

    def compute_distance(self, state: list):
        state_distance = 0
        for i in range(len(state)):
            state_distance += self.compute_single_distance(state, i)
        return state_distance

    def compute_single_distance(self, state: list, cell_index: int):
        number = state[cell_index]
        resulting_index = self.resulting_state.index(number)
        # identify vetical diff
        vertical_diff = abs(self.compute_row(cell_index) - self.compute_row(resulting_index))
        # identofy horizontal diff
        horizontal_diff = abs(self.compute_column(cell_index) - self.compute_column(resulting_index))
        return vertical_diff + horizontal_diff

    @staticmethod
    def compute_column(cell_index: int):
        if cell_index in [0, 3, 6]:
            return 1
        elif cell_index in [1, 4, 7]:
            return 2
        elif cell_index in [2, 5, 8]:
            return 3
        else:
            raise

    @staticmethod
    def compute_row(cell_index: int):
        if cell_index in [0, 1, 2]:
            return 1
        elif cell_index in [3, 4, 5]:
            return 2
        elif cell_index in [6, 7, 8]:
            return 3
        else:
            raise


class ManhattanSingle(Manhattan):
    def decide(self):
        distances = dict()
        for possible_move in self.available_moves:
            # make a move
            next_state = self.state.copy()
            zero_cell = next_state.index(0)
            # check current cell distance
            curr_dist = self.compute_single_distance(next_state, possible_move)
            # check distance after movement
            next_state[possible_move], next_state[zero_cell] = next_state[zero_cell], next_state[possible_move]
            next_dist = self.compute_single_distance(next_state, zero_cell)
            distances.setdefault(possible_move, next_dist - curr_dist)

        best_choice = None
        shortest_distance = None
        for p_move, distance in distances.items():
            if shortest_distance is None or distance <= shortest_distance:
                shortest_distance = distance
                best_choice = p_move
        # print(f"Shortest ManhattanSingle: {best_choice}")
        return best_choice


class ManhattanDescendants(Manhattan):
    def decide(self):
        distances = dict()
        for possible_move in self.available_moves:
            # make a move
            next_state = self.state.copy()
            zero_cell = next_state.index(0)
            # check current cell distance
            # curr_dist = self.compute_single_distance(next_state, possible_move)
            # check distance after movement
            next_state[possible_move], next_state[zero_cell] = next_state[zero_cell], next_state[possible_move]
            # next_dist = self.compute_single_distance(next_state, zero_cell)
            distances.setdefault(possible_move, 0)
            for child_move in self.next_available_moves(next_state):
                child_state = next_state.copy()
                child_zero_cell = child_state.index(0)
                # check current cell distance
                curr_dist = self.compute_single_distance(child_state, child_move)
                # check distance after movement
                child_state[child_move], child_state[child_zero_cell] = child_state[child_zero_cell], child_state[child_move]
                next_dist = self.compute_single_distance(child_state, child_zero_cell)
                distances[possible_move] += next_dist - curr_dist

        best_choice = None
        shortest_distance = None
        for p_move, distance in distances.items():
            if shortest_distance is None or distance <= shortest_distance:
                shortest_distance = distance
                best_choice = p_move
        # print(f"Shortest ManhattanDescendants: {best_choice}")
        return best_choice

    def next_available_moves(self, state: list):
        moves = []
        for possible_move in self.eights.POSSIBLE_MOVES.get(state.index(0)):
            to_check_state = state.copy()
            zero_in = to_check_state.index(0)
            to_check_state[possible_move], to_check_state[zero_in] = to_check_state[zero_in], to_check_state[
                possible_move]
            if self.eights.to_str(to_check_state) in self.eights.CHECKED_STATES:
                continue
            moves.append(possible_move)
        return moves


class RandomChoice(Evristics):
    def decide(self):
        # print("RandomChoice decides")
        return choice(self.available_moves)


def print_best_result(input_state, path, on_row=10):
    def format_matrix(state):
        return ""
    all_states = []
    all_states.append(input_state)
    next_state = input_state.copy()
    for move in path:
        next_state = next_state.copy()
        zero_index = next_state.index(0)
        next_state[move], next_state[zero_index] = next_state[zero_index], next_state[move]
        all_states.append(next_state)
    # print(all_states)
    rows = []
    while len(all_states) > 0:
        to_pop = on_row if len(all_states) >= on_row else len(all_states)
        row = all_states[:to_pop]
        all_states = all_states[to_pop:]
        rows.append(row)

    for row in rows:
        print(" ")
        line_1 = [" ".join(map(lambda n: " " if n == 0 else str(n), state[0:3])) for state in row]
        line_2 = [" ".join(map(lambda n: " " if n == 0 else str(n), state[3:6])) for state in row]
        line_3 = [" ".join(map(lambda n: " " if n == 0 else str(n), state[6:9])) for state in row]
        print("  |  ".join(line_1))
        print("  |  ".join(line_2))
        print("  |  ".join(line_3))


if __name__ == "__main__":
    start_time = time.time()
    tracemalloc.start()
    input_state = [2, 1, 4, 6, 8, 7, 0, 3, 5]
    result_state = [1, 2, 3, 8, 0, 4, 7, 6, 5]
    best_result = None
    best_path = None
    for i in range(1000):
        # print(f"--- Execution {i} ---")
        eights = Eights(
            input_state=input_state,
            result_state=result_state
        )
        eights.evristic_classes.append(RandomChoice)
        eights.evristic_classes.append(LeftHand)
        eights.evristic_classes.append(Manhattan)
        eights.evristic_classes.append(ManhattanSingle)
        eights.evristic_classes.append(ManhattanDescendants)

        try:
            eights.compute()
        except Done as d:
            if best_result is None or d.iterations < best_result:
                best_result = d.iterations
                best_path = eights.PATH
            # print(str(d))
            print(f"Execution {i}: {str(d)}, Iterations: {d.iterations}")
    print("--- Done ---")
    size, peak = tracemalloc.get_traced_memory()
    print(f"Best result: {best_result}")
    # print(f"Best path: {best_path}")
    print(f"Used max memory: {peak} bytes")
    print(f"Execution time: {time.time() - start_time} sec")
    print_best_result(input_state, best_path)
