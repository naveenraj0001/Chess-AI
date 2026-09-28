import math
import random

import chess

from .evaluation import evaluate


class MinimaxAI:
    def __init__(self, depth: int = 3):
        self.depth = depth

    def best_move(self, board: chess.Board) -> chess.Move | None:
        board = board.copy(stack=False)

        maximizing = board.turn == chess.WHITE
        best_score = -math.inf if maximizing else math.inf
        best_moves: list[chess.Move] = []

        for move in list(board.legal_moves):
            board.push(move)
            score = self._minimax(board, self.depth - 1, not maximizing)
            board.pop()

            if score == best_score:
                best_moves.append(move)
            elif (maximizing and score > best_score) or (
                not maximizing and score < best_score
            ):
                best_score = score
                best_moves = [move]

        return random.choice(best_moves) if best_moves else None

    def _minimax(self, board: chess.Board, depth: int, maximizing: bool) -> float:
        if depth == 0 or board.is_game_over():
            return evaluate(board, depth)

        if maximizing:
            best = -math.inf
            for move in list(board.legal_moves):
                board.push(move)
                best = max(best, self._minimax(board, depth - 1, False))
                board.pop()
            return best

        best = math.inf
        for move in list(board.legal_moves):
            board.push(move)
            best = min(best, self._minimax(board, depth - 1, True))
            board.pop()
        return best
