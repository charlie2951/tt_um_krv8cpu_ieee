# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def cpu_basic_test(dut):
    """Test all major operations of the cpu"""

    # Start the clock (10ns period = 100MHz)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # --- Reset Phase ---
    dut.reset.value = 1
    dut.instruction.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value = 0
    await RisingEdge(dut.clk)

    # Helper function to send instruction and wait for execution
    async def run_instr(hex_val, label):
        dut.instruction.value = hex_val
        await RisingEdge(dut.clk)
        # cocotb handles signed conversion automatically if we use .signed_integer
        acc_val = dut.acc.value.signed_integer
        dut._log.info(f"{label:15} | Instr: {hex_val:04X} | ACC: {acc_val:4d} | Out: {dut.out_port.value}")

    # --- Test 1: Positive Sign Extension ---
    # LDI 5 (Op: 1, Imm: 05) -> 0x1005
    await run_instr(0x1005, "LDI 5")

    # --- Test 2: Negative Sign Extension ---
    # LDI -2 (Op: 1, Imm: 3E [6-bit -2]) -> 0x103E
    await run_instr(0x103E, "LDI -2")

    # --- Test 3: Signed Addition ---
    # ADI 5 (-2 + 5 = 3) -> 0x3005
    await run_instr(0x3005, "ADI 5")

    # --- Test 4: Store and Subtraction ---
    # STA x1 (x1 = 3)
    await run_instr(0x4400, "STA x1")
    # LDI 1
    await run_instr(0x1001, "LDI 1")
    # SUB x1 (1 - 3 = -2)
    await run_instr(0x5400, "SUB x1")
    assert dut.acc.value.signed_integer == -2, "Subtraction failed!"

    # --- Test 5: Signed Comparison (SLT) ---
    # Current ACC is -2, x1 is 3. Is -2 < 3? Yes (Result 1)
    await run_instr(0x0400, "SLT x1")
    assert dut.acc.value == 1

    # --- Test 6: Shift Operations ---
    # LDI 1
    await run_instr(0x1001, "LDI 1")
    # SLI 3 (1 << 3 = 8)
    await run_instr(0xD003, "SLI 3")
    assert dut.acc.value == 8

    # --- Test 7: Output ---
    await run_instr(0xF000, "OUT")
    assert dut.out_port.value == 8

    dut._log.info("All tests passed successfully!")
