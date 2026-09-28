from dataclasses import dataclass
from enum import Enum


class PieceType(str, Enum):
    NONE = " "
    KING = "K"
    QUEEN = "Q"
    ROOK = "R"
    BISHOP = "B"
    KNIGHT = "N"
    PAWN = "p"


class ColorType(str, Enum):
    NONE = "none"
    WHITE = "white"
    BLACK = "black"


@dataclass
class PieceMove:
    directional: bool
    slide: bool
    moves: list[tuple[int, int]]

    @staticmethod
    def get_linear_moves() -> list[tuple[int, int]]:
        return [(0, 1), (0, -1), (1, 0), (-1, 0)]

    @staticmethod
    def get_diagonal_moves() -> list[tuple[int, int]]:
        return [(1, 1), (-1, -1), (1, -1), (-1, 1)]

    @staticmethod
    def get_pawn_attack():
        return [(2, 1), (-2, 1)]


@dataclass
class ChessPiece:
    piece_type: PieceType
    color: ColorType

    def __repr__(self) -> str:
        return f"{self.piece_type.value}{self.color.value[0]}"

    @staticmethod
    def empty():
        return ChessPiece(PieceType.NONE, ColorType.NONE)

    @staticmethod
    def white(ptype: PieceType):
        return ChessPiece(ptype, ColorType.WHITE)

    @staticmethod
    def black(ptype: PieceType):
        return ChessPiece(ptype, ColorType.BLACK)

    def get_move(self) -> PieceMove:
        match self.piece_type:
            case PieceType.KING:
                return PieceMove(
                    False,
                    False,
                    PieceMove.get_linear_moves() + PieceMove.get_diagonal_moves(),
                )

            case PieceType.QUEEN:
                return PieceMove(
                    False,
                    True,
                    PieceMove.get_linear_moves() + PieceMove.get_diagonal_moves(),
                )

            case PieceType.ROOK:
                return PieceMove(False, True, PieceMove.get_linear_moves())

            case PieceType.BISHOP:
                return PieceMove(False, True, PieceMove.get_diagonal_moves())

            case PieceType.KNIGHT:
                return PieceMove(
                    False,
                    False,
                    [
                        (2, 1),
                        (2, -1),
                        (-2, 1),
                        (-2, -1),
                        (1, 2),
                        (1, -2),
                        (-1, 2),
                        (-1, -2),
                    ],
                )

            case PieceType.PAWN:
                return PieceMove(
                    True,
                    False,
                    [
                        (0, 1),
                    ],
                )

        return PieceMove(False, False, [])
