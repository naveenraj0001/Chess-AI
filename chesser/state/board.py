import chess


class Board:
    def __init__(self):
        self._board = chess.Board()

    @property
    def raw(self) -> chess.Board:
        return self._board

    @property
    def turn(self) -> chess.Color:
        return self._board.turn

    def reset(self):
        self._board.reset()

    def piece_at(self, square: int):
        return self._board.piece_at(square)

    def legal_moves_from(self, square: int) -> list[chess.Move]:
        return [m for m in self._board.legal_moves if m.from_square == square]

    def push(self, move: chess.Move):
        self._board.push(move)

    def is_check(self) -> bool:
        return self._board.is_check()

    def is_game_over(self) -> bool:
        return self._board.is_game_over()

    def is_checkmate(self) -> bool:
        return self._board.is_checkmate()
