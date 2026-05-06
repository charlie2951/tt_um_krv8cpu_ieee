# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

@cocotb.test()
async def test_cpu_signed_operations(dut):
    """Replicating Verilog Testbench cases for Signed CPU on TinyTapeout Hardware"""

    # --- Setup ---
    # Start clock (10ns period = 100MHz)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Initialize Inputs
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0 # Active Low Reset
    
    # Wait 15ns (as per Verilog #15)
    await Timer(15, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # Helper function for pin mapping: ui_in=High, uio_in=Low
    async def run_instr(instr_hex, label):
        dut.ui_in.value = (instr_hex >> 8) & 0xFF
        dut.uio_in.value = instr_hex & 0xFF
        await RisingEdge(dut.clk)
        
        # Access internal signals for the $monitor equivalent log
        # Assuming the CPU instance inside the wrapper is named 'krv8cpu'
        acc_raw = dut.user_project.cpu0.acc.value
        acc_dec = acc_raw.signed_integer
        x1_val  = dut.user_project.cpu0.registers[1].value
        out_val = dut.uo_out.value
        
        dut._log.info(f"Instr: {instr_hex:04X} | {label:25} | ACC: {acc_raw} ({acc_dec:4d}) | x1: {x1_val} | Out: {out_val}")

    dut._log.info("--- Starting Test Cases ---")

    # --- TEST 1: Positive Sign Extension ---
    # Op: 1 (LDI), Imm: 6'b000101 (5) -> 0x1005
    await run_instr(0x1005, "LDI 5")
    assert dut.user_project.cpu0.acc.value == 0x05

    # --- TEST 2: Negative Sign Extension ---
    # Op: 1 (LDI), Imm: 6'b111110 (-2) -> 0x103E
    await run_instr(0x103E, "LDI -2")
    assert dut.user_project.cpu0.acc.value.signed_integer == -2

    # --- TEST 3: Signed Addition (Negative + Positive) ---
    # Current ACC = -2, ADI 5 -> 0x3005
    await run_instr(0x3005, "ADI 5")
    assert dut.user_project.cpu0.acc.value.signed_integer == 3

    # --- TEST 4: Store and Subtraction ---
    # STA x1 -> 0x4400
    await run_instr(0x4400, "STA x1")
    # LDI 1 -> 0x1001
    await run_instr(0x1001, "LDI 1")
    # SUB x1 (1 - 3 = -2) -> 0x5400
    await run_instr(0x5400, "SUB x1")
    assert dut.user_project.cpu0.acc.value.signed_integer == -2

    # --- TEST 5: Signed Comparison (SLT) ---
    # Is -2 < 3? Yes (0x01) -> 0x0400
    await run_instr(0x0400, "SLT x1")
    assert dut.user_project.cpu0.acc.value == 1

    # --- TEST 6: Signed Comparison (Reverse) ---
    # LDI 10 -> 0x100A
    await run_instr(0x100A, "LDI 10")
    # STA x2 -> 0x4800
    await run_instr(0x4800, "STA x2")
    # LDI -5 (0x3B in 6-bit) -> 0x103B
    await run_instr(0x103B, "LDI -5")
    # SLT x2 (Is -5 < 10? Yes) -> 0x0800
    await run_instr(0x0800, "SLT x2")
    assert dut.user_project.cpu0.acc.value == 1

    # --- TEST 7: Output Check ---
    # OUT -> 0xF000
    await run_instr(0xF000, "OUT")
    assert dut.uo_out.value == 1

    # Final Delay
    await Timer(20, units="ns")
    dut._log.info("--- Testbench Complete ---")
