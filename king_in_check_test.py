import chess
import chess.engine
import os
from speaker import play_sound
from display import ChessOLED
import time
STOCKFISH_PATH = os.getenv("STOCKFISH_PATH", "/usr/games/stockfish")
oled = ChessOLED()
def test_fen(fen, from_sq=None, to_sq=None, check_current = 0):
    print(f"\nFEN: {fen}")
    board = chess.Board(fen)
    print("\nBoard:")
    print(board, "\n")

    # Checkmate or Stalemate
    if board.is_checkmate():
        print("❌ CHECKMATE detected.")
        oled.display("My Friend,","It's a CHECKMATE!")
        play_sound("checkmate", block = True)
        time.sleep(100)
        return
    elif board.is_stalemate():
        print("⚪ STALEMATE detected.")
        oled.display("My Friend,","It's a Stalemate")
        return
    
    if(check_current == 1):
    # Current King Safety
        if board.is_check():
            oled.display("My Friend,","It's a CHECKMATE!")
            play_sound("checkmate", block = True)
            time.sleep(100)
            #print("⚠️  The king is currently in CHECK.")
            #oled.display("King in","Danger!!")
            #play_sound("your_king_in_danger", block = True)
            time.sleep(2)
            return True, "in_check"
        else:
            print("✅ The king is NOT in check.")
            return False, "not_check"

    

    # If from_sq and to_sq provided, test legality
    if from_sq and to_sq:
        move = chess.Move.from_uci(from_sq + to_sq)
        if move in board.legal_moves:
            print(f"✅ Move {from_sq}->{to_sq} is LEGAL and does NOT leave king in check.")
            return False, "clear"
        else:
            print(f"❌ Move {from_sq}->{to_sq} is ILLEGAL or leaves king in check.")
            oled.display("King STILL","in Danger!!")
            play_sound("your_king_in_danger", block = True)
            time.sleep(2)
            return True, "in_check_still"
    else:
        print("ℹ️  No move provided. Skipping move legality test.")
