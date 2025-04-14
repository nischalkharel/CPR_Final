import chess
import chess.engine
from display import ChessOLED
import time 
class AIChess:
    def __init__(self, engine_path=r"/usr/games/stockfish"):
        oled = ChessOLED()
        self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        self.board = None

    def set_position(self, fen):
        self.board = chess.Board(fen)

    def is_checkmate(self):
        """Check if the current board state is a checkmate."""
        return self.board.is_checkmate()

    def is_stalemate(self):
        """Check if the current board state is a stalemate."""
        return self.board.is_stalemate()

    def close_engine(self):
        self.engine.quit()
        
    def get_ai_move(self, difficulty="easy") -> list[str] | None:
        oled = ChessOLED()
        time_limit = {"easy": 0.5, "medium": 1.0, "hard": 3.0}.get(difficulty, 1.0)
        limit = chess.engine.Limit(time=time_limit)

        for attempt in range(1, 7):
            try:
                result = self.engine.play(self.board, limit)
                if result.move is None or self.board.is_game_over():
                    oled.display("No Legal Move", "Game Over")
                    return None
                uci = result.move.uci()
                return [uci[:2], uci[2:4]]
            except (chess.engine.EngineTerminatedError, BrokenPipeError):
                oled.display("Stockfish Failed", f"Attempt {attempt}")
                time.sleep(1)
                if attempt == 6:
                    oled.display("Stockfish Crashed", "Game Ending")
                    raise RuntimeError("Stockfish crashed 6 in a row")
                try:
                    self.engine.quit()
                except Exception:
                    pass
                self.engine = chess.engine.SimpleEngine.popen_uci("/usr/games/stockfish")

