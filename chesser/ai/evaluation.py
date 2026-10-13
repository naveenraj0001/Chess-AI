import chess

MATE_SCORE = 100.0
PIECE_VALUES = {
    chess.PAWN: 1.0,
    chess.KNIGHT: 3.2,
    chess.BISHOP: 3.3,
    chess.ROOK: 5.0,
    chess.QUEEN: 9.0,
    chess.KING: 0.0,
}


def evaluate(board: chess.Board, depth: int) -> float:
    if board.is_checkmate():
        score = MATE_SCORE + depth
        return -score if board.turn == chess.WHITE else score

    if board.is_game_over():
        return 0.0

    score = 0.0
    for piece in board.piece_map().values():
        value = PIECE_VALUES[piece.piece_type]
        score += value if piece.color == chess.WHITE else -value

    return score
