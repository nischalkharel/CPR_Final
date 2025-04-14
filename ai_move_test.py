import chess
import chess.engine
import os

# Path to your Stockfish engine
STOCKFISH_PATH = os.getenv("STOCKFISH_PATH", "/usr/games/stockfish")

def test_fen(fen, difficulty="easy"):
    print(f"\nTesting FEN: {fen}")
    board = chess.Board(fen)

    print("Board position:")
    print(board)

    if board.is_checkmate():
        print("✅ CHECKMATE detected.")
        return
    elif board.is_stalemate():
        print("🟡 STALEMATE detected.")
        return

    # Try to get AI move
    time_limit = {"easy": 0.5, "medium": 1.0, "hard": 3.0}.get(difficulty, 1.0)
    limit = chess.engine.Limit(time=time_limit)

    try:
        with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
            result = engine.play(board, limit)
            if result.move:
                print(f"🤖 AI suggests: {result.move.uci()}")
            else:
                print("❌ No move returned.")
    except Exception as e:
        print(f"⚠️ Engine error: {e}")

# === EXAMPLES ===
# Fool's Mate: checkmate in 2 moves
fools_mate_fen = "rnb1kbnr/ppppqppp/8/8/6P1/5P2/PPPPP2P/RNBQKBNR w KQkq - 0 3"

# In-progress position, white to move
normal_position = "r1bqkbnr/pppppppp/2n5/8/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"

# Call tester
test_fen(fools_mate_fen)        # Should detect CHECKMATE
test_fen(normal_position)       # Should return a move
checkmate_position = "r2k3r/ppp1n1pp/1pn5/3p1qbN/1pBKp1b1/N7/PPP2PPP/R6R w - - 0 1"
test_fen(checkmate_position)
