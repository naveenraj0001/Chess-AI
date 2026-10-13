import math
import random

from dataclasses import dataclass

import chess

from .evaluation import evaluate


@dataclass
class Analysis:
    best_move: chess.Move | None
    evaluation: float
    possible_moves: int
    search_depth: int


class MinimaxAI:
    def __init__(self, depth: int = 3):
        self.depth = depth

    def best_move(self, board: chess.Board) -> Analysis:
        board = board.copy(stack=False)
        possible_moves = board.legal_moves.count()

        if possible_moves == 0:
            return Analysis(
                best_move=None,
                evaluation=evaluate(board, self.depth),
                possible_moves=0,
                search_depth=self.depth,
            )

        maximizing = board.turn == chess.WHITE

        if maximizing:
            best_score = -math.inf
        else:
            best_score = math.inf

        best_moves: list[chess.Move] = []

        for move in board.legal_moves:
            board.push(move)
            score = self._minimax(
                board,
                self.depth - 1,
                not maximizing,
            )
            board.pop()

            if score == best_score:
                best_moves.append(move)

            elif maximizing:
                if score > best_score:
                    best_score = score
                    best_moves = [move]

            else:
                if score < best_score:
                    best_score = score
                    best_moves = [move]

        best_move = random.choice(best_moves) if best_moves else None

        return Analysis(
            best_move=best_move,
            evaluation=best_score,
            possible_moves=possible_moves,
            search_depth=self.depth,
        )

    def _minimax(
        self,
        board: chess.Board,
        depth: int,
        maximizing: bool,
    ) -> float:
        if depth == 0 or board.is_game_over():
            return evaluate(board, depth)

        if maximizing:
            best = -math.inf
            for move in board.legal_moves:
                board.push(move)
                value = self._minimax(
                    board,
                    depth - 1,
                    False,
                )
                board.pop()
                best = max(best, value)

            return best

        else:
            best = math.inf
            for move in board.legal_moves:
                board.push(move)
                value = self._minimax(
                    board,
                    depth - 1,
                    True,
                )
                board.pop()
                best = min(best, value)

            return best
