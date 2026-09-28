import chess

MATE_SCORE = 100000

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}


def evaluate(board: chess.Board, depth: int) -> int:
    if board.is_checkmate():
        bonus = MATE_SCORE + depth
        return -bonus if board.turn == chess.WHITE else bonus
    if board.is_game_over():
        return 0
    score = 0
    for piece in board.piece_map().values():
        value = PIECE_VALUES[piece.piece_type]
        score += value if piece.color == chess.WHITE else -value
    return score
