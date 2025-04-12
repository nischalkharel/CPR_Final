from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont

class ChessOLED:
    def __init__(self):
        serial = i2c(port=1, address=0x3C)
        self.device = ssd1306(serial, width=128, height=64)
        self.piece_symbols = {
            "white_king": "\u2654",
            "white_queen": "\u2655",
            "white_rook": "\u2656",
            "white_bishop": "\u2657",
            "white_knight": "\u2658",
            "white_pawn": "\u2659",
            "black_king": "\u265A",
            "black_queen": "\u265B",
            "black_rook": "\u265C",
            "black_bishop": "\u265D",
            "black_knight": "\u265E",
            "black_pawn": "\u265F"
        }

    def display(self, line1, line2, piece=None):
        image = Image.new("1", (self.device.width, self.device.height))
        draw = ImageDraw.Draw(image)

        symbol = ""
        if piece and piece.lower() in self.piece_symbols:
            symbol = self.piece_symbols[piece.lower()]

        max_width, max_height = self.device.width, self.device.height-15

        # Fit line1 + piece
        for font1_size in range(28, 7, -1):
            font1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font1_size)

            h_piece, piece_width = 0, 0
            if symbol:
                bbox_piece = draw.textbbox((0, 0), symbol, font=font1)
                h_piece = bbox_piece[3] - bbox_piece[1]
                piece_width = bbox_piece[2] - bbox_piece[0]

            bbox1 = draw.textbbox((0, 0), line1, font=font1)
            w1, h1 = bbox1[2] - bbox1[0], bbox1[3] - bbox1[1]

            space_above_line2 = max(h_piece, h1) + 4
            if max(w1, piece_width) <= max_width and space_above_line2 < max_height - 8:
                break

        # Now fit line2
        max_line2_height = max_height - space_above_line2 - 4
        for font2_size in range(28, 7, -1):
            font2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font2_size)
            bbox2 = draw.textbbox((0, 0), line2, font=font2)
            w2, h2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]
            if w2 <= max_width and h2 <= max_line2_height:
                break

        total_height = space_above_line2 + h2
        current_y = (max_height - total_height) // 2

        if symbol:
            x_piece = (max_width - piece_width) // 2
            draw.text((x_piece, current_y), symbol, font=font1, fill=255)
            current_y += h_piece + 4
        else:
            x1 = (max_width - w1) // 2
            draw.text((x1, current_y), line1, font=font1, fill=255)
            current_y += h1 + 4

        if symbol:
            x1 = (max_width - w1) // 2
            draw.text((x1, current_y), line1, font=font1, fill=255)
            current_y += h1 + 4

        x2 = (max_width - w2) // 2
        draw.text((x2, current_y), line2, font=font2, fill=255)

        self.device.display(image)
