import os
import csv
import subprocess
import shlex
import matplotlib.pyplot as plt

#---------------------------------
# Configuration
#---------------------------------

UNIT_FOLDER = r"C:\Users\zhlee_t\Desktop\Git Project\day-4-signal-processing-LZH-Oppstar"
UNIT = "impl1.exe"
CSR_ADDR = 0x0
COEF_ADDR = 0x4

CONFIGS = ["p0.cfg", "p4.cfg", "p7.cfg", "p9.cfg"]
VEC_FILE = "sqr.vec"

#----------------------------------
# Helpers 
#----------------------------------

def run(command):
    unit_path = os.path.join(UNIT_FOLDER, UNIT)
    print(f"[{UNIT}] {command}")
    subprocess.check_call([unit_path] + shlex.split(command))

def read_csr():
    unit_path = os.path.join(UNIT_FOLDER, UNIT)
    out = subprocess.check_output(
        [unit_path] + shlex.split(f"cfg --address {hex(CSR_ADDR)}")
    ).decode()
    return int(out, 0)

def write_csr(value):
    run(f"cfg --address {hex(CSR_ADDR)} --data {hex(value)}")

def write_coef(value):
    run(f"cfg --address {hex(COEF_ADDR)} --data {hex(value)}")

def drive(value):
    unit_path = os.path.join(UNIT_FOLDER, UNIT)
    out = subprocess.check_output(
        [unit_path] + shlex.split(f"sig --data {hex(value)}")
    ).decode()
    return int(out, 0)

def load_coeffs(cfg_file):
    print(f"--- Loading coefficients from {cfg_file} ---")
    coefs = [0, 0, 0, 0]
    en_flags = [0, 0, 0, 0]

    with open(os.path.join(UNIT_FOLDER, cfg_file)) as f:
        reader = csv.DictReader(f)
        for row in reader:
            idx = int(row["coef"])
            val = int(row["value"], 0)
            en  = int(row["en"])
            coefs[idx] = val & 0xFF   # 8-bit signed
            en_flags[idx] = en

    # Pack coefficients into 32-bit register
    coef_reg = (coefs[3] << 24) | (coefs[2] << 16) | (coefs[1] << 8) | coefs[0]
    write_coef(coef_reg)

    # Update CSR for coefficient enable bits [1:4]
    csr = read_csr()
    csr &= ~(0xF << 1)  # Clear old enable bits
    csr |= (en_flags[0] << 1) | (en_flags[1] << 2) | (en_flags[2] << 3) | (en_flags[3] << 4)
    write_csr(csr)

#----------------------------------
# Main script
#----------------------------------

for cfg in CONFIGS:
    print(f"\n===== DAY 4 :: Signal Processing :: {cfg} =====")

    # Reset and enable filter
    run("com --action reset")
    run("com --action enable")

    # Halt filter, clear taps and input buffer
    csr = read_csr()
    csr |= (1 << 5)   # HALT
    csr |= (1 << 17)  # IBCLR: clear input buffer
    csr |= (1 << 18)  # TCLR: clear filter taps
    write_csr(csr)

    # Load coefficients and enable bits
    load_coeffs(cfg)

    # Release HALT to start filtering
    csr = read_csr()
    csr &= ~(1 << 5)  # HALT = 0
    write_csr(csr)

    # Drive input vector
    sig_in = []
    sig_out = []

    print("--- Driving input vector ---")
    vec_path = os.path.join(UNIT_FOLDER, VEC_FILE)
    with open(vec_path) as f:
        for line in f:
            samp = int(line, 0)
            sig_in.append(samp)
            sig_out.append(drive(samp))

    # Plot results
    plt.figure()
    plt.plot(sig_in, label="Input", drawstyle="steps-post")
    plt.plot(sig_out, label="Output", drawstyle="steps-post")
    plt.title(f"Filter response ({cfg})")
    plt.xlabel("Sample")
    plt.ylabel("Value")
    plt.legend()
    plt.grid(True)
    plt.show()
