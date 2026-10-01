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

        if maximizing == True:
            best_score = -math.inf
        else:
            best_score = math.inf
        best_moves: list[chess.Move] = []

        for move in list(board.legal_moves):
            board.push(move)
            score = self._minimax(board, self.depth - 1, not maximizing)
            board.pop()

            if score == best_score:
                best_moves.append(move)

            elif maximizing == True:
                if score > best_score:
                    best_score = score
                    best_moves = [move]

            else:
                if score < best_score:
                    best_score = score
                    best_moves = [move]

        if best_moves:
            return random.choice(best_moves)
        else:
            return None

    def _minimax(self, board: chess.Board, depth: int, maximizing: bool) -> float:
        if depth == 0 or board.is_game_over():
            return evaluate(board, depth)

        if maximizing == True:
            best = -math.inf

            for move in list(board.legal_moves):
                board.push(move)
                value = self._minimax(board, depth - 1, False)
                board.pop()

                best = max(best, value)

            return best
        else:
            best = math.inf

            for move in list(board.legal_moves):
                board.push(move)
                value = self._minimax(board, depth - 1, True)
                board.pop()

                best = min(best, value)

            return best
