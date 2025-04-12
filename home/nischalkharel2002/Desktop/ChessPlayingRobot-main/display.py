import lgpio
import spidev
import time

# Pin setup
DC_PIN = 23      # GPIO23
RESET_PIN = 25   # GPIO25

# Open correct gpiochip for Raspberry Pi 5
chip = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(chip, DC_PIN)
lgpio.gpio_claim_output(chip, RESET_PIN)

# Reset the display
lgpio.gpio_write(chip, RESET_PIN, 0)
time.sleep(0.1)
lgpio.gpio_write(chip, RESET_PIN, 1)

# SPI setup
spi = spidev.SpiDev()
spi.open(0, 0)  # SPI bus 0, CE0
spi.max_speed_hz = 800000  # Try slower if still nothing

def command(cmd):
    lgpio.gpio_write(chip, DC_PIN, 0)
    spi.writebytes([cmd])

def data(buf):
    lgpio.gpio_write(chip, DC_PIN, 1)
    spi.writebytes(buf)

# OLED SSD1306 init sequence
def init_display():
    cmds = [
        0xAE, 0xD5, 0x80, 0xA8, 0x3F,
        0xD3, 0x00, 0x40, 0x8D, 0x14,
        0x20, 0x00, 0xA1, 0xC8, 0xDA,
        0x12, 0x81, 0xCF, 0xD9, 0xF1,
        0xDB, 0x40, 0xA4, 0xA6, 0xAF
    ]
    for c in cmds:
        command(c)

# Fill screen with white (every pixel on)
def fill_white():
    for page in range(8):  # 8 pages (128x8 each)
        command(0xB0 + page)  # Set page address
        command(0x00)         # Set lower column
        command(0x10)         # Set higher column
        data([0xFF] * 128)    # 128 columns of full-on pixels

# Run test
init_display()
fill_white()
