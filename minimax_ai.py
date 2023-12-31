import dataclasses
import random

from game import Player, Side, BoardView, has_won


@dataclasses.dataclass(frozen=True)
class MinimaxAi(Player):
    """
    An AI of the game
    """

    think_chance: tuple[float, float] = (1.0, 1.0)
    """
    The chance that it gives up to think and decide to move randomly instead.
    Note that it will still block obvious about-to-win and decide a move leading to a win.
    
    The first number is the chance the AI "think" the move deeply by looking at the table and consider all the move.
    The second number is the chance the AI will "think" about the obvious move, if they don't wanna think deeply
    """

    def decide_move(self, board_view: BoardView, current_side: Side) -> int:
        # it saves a lot of runtime cost
        # it is guaranteed that all the tiles in the empty board have equal chances of winning
        if all(tile is None for tile in board_view):
            return random.randrange(0, 9)

        # the AI don't wanna "think" deeply
        if random.random() >= self.think_chance[0]:
            # if so, if the AI wanna "think" about obvious moves
            if random.random() < self.think_chance[1]:
                match _find_win_move(board_view, current_side):
                    case None:
                        pass
                    case at:
                        return at

                match _find_win_move(board_view, current_side.swap_side()):
                    case None:
                        pass
                    case at:
                        return at

            # if they don't wanna "think" about obvious moves, or there are no obvious move
            avail_moves = [i for i, tile in enumerate(board_view) if tile is None]
            return random.choice(avail_moves)

        # if the AI decides to "think" deeply, let it "minimax" you
        board = list(board_view)

        move_scores = _move_scores(board, current_side, True)
        best_move, max_score = next(move_scores)
        # there may be more than 1 best moves. Make the AI less predictable by randomizing these best moves
        best_move = [best_move]
        for move, score in move_scores:
            if score > max_score:
                max_score = score
                best_move = [move]
            elif score == max_score:
                best_move.append(move)

        return random.choice(best_move)


def _max_score(board: list[Side | None], current_side: Side, is_maximizing: bool) -> int:
    """
    Evaluates the board to determine the max score for the current side.
    It alternates between maximizing and minimizing strategy based on the current side.

    :param board: the board. May be modified
    :param current_side: the current side
    :param is_maximizing: is the current side is maximizing or not?
    :return: 1 if the best the maximizing side
    """
    # Base case: checking for win (1), loss (-1), or draw (0).
    if is_maximizing and has_won(board, current_side):  # the maximizing side has achieved their goal
        return 1
    if not is_maximizing and has_won(board, current_side.swap_side()):  # the minimizing side has achieved their goal
        return -1
    if None not in board:  # full board
        return 0

    # Recursive case: evaluate scores of possible moves and return the best one.
    is_maximizing = not is_maximizing  # now we consider the opponent if the current state is not deterministic yet
    scores = (score for move, score in _move_scores(board, current_side, is_maximizing))
    return max(scores) if is_maximizing else min(scores)


def _move_scores(board: list[Side | None], current_side: Side, is_maximizing: bool):
    """
    Generator over the possible moves and outcomes they yield

    :param board: the game board. DO NOT do something with the board (except the _max_score function) while
                  the generator isn't finished, as the board is in the unspecified state
                  because it is modified in the generator
    :param current_side: the side to consider
    :param is_maximizing: is the current side is maximizing or not?
    :return:
    """

    for i in (i for i in range(len(board)) if board[i] is None):
        # Temporarily make a move on the board.
        board[i] = current_side if is_maximizing else current_side.swap_side()
        max_score = _max_score(board, current_side, is_maximizing)
        # Undo it
        board[i] = None

        # Move it to the end since leaving the board[i] not empty while being held across `yield`
        # would be a logic error if the generator is ended early
        yield i, max_score


def _find_win_move(board, side: Side) -> int | None:
    """
    Find a spot that leads to a win of a given side
    :param board: the board
    :param side: the given side
    :return: that winning move, or `None` if there is not
    """
    to_checks = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
        [0, 4, 8], [2, 4, 6]  # Diagonals
    ]

    for to_check in to_checks:
        count = 0
        empty_spot = None
        for i in to_check:
            if board[i] is None:
                empty_spot = i
            elif board[i] is side:
                count += 1

        # there should be that there are 2 filled already and only one is awaited to be filled for a win
        if count == 2 and empty_spot is not None:
            return empty_spot

    return None
