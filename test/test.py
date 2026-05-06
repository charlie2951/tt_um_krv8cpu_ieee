# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, ReadOnly

@cocotb.test()
async def test_cpu_signed_operations(dut):
    """Replicating Verilog Testbench cases for Signed CPU on TinyTapeout Hardware"""

    # --- Setup ---
    # Fix: Rename 'units' to 'unit'
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0 
    
    # Fix: Rename 'units' to 'unit'
    await Timer(15, unit="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    async def run_instr(instr_hex, label):
        dut.ui_in.value = (instr_hex >> 8) & 0xFF
        dut.uio_in.value = instr_hex & 0xFF
        await RisingEdge(dut.clk)
        
        # FIX: Wait for the logic to settle before reading
        await ReadOnly() 
        
        # Fix: Use to_signed() instead of signed_integer
        acc_raw = dut.user_project.cpu0.acc.value
        acc_dec = acc_raw.to_signed()
        x1_val  = dut.user_project.cpu0.registers[1].value
        out_val = dut.uo_out.value
        
        dut._log.info(f"Instr: {instr_hex:04X} | {label:25} | ACC: {acc_raw} ({acc_dec:4d}) | x1: {x1_val} | Out: {out_val}")

    dut._log.info("--- Starting Test Cases ---")

    # TEST 1
    await run_instr(0x1005, "LDI 5")
    # FIX: Check against the decimal value 5 or integer
    assert dut.user_project.cpu0.acc.value.integer == 5, f"Expected 5, got {dut.user_project.cpu0.acc.value.integer}"

    # TEST 2
    await run_instr(0x103E, "LDI -2")
    assert dut.user_project.cpu0.acc.value.to_signed() == -2

    # TEST 3
    await run_instr(0x3005, "ADI 5")
    assert dut.user_project.cpu0.acc.value.to_signed() == 3

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
