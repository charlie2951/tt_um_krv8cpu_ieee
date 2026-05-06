# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

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

    dut.ui_in.value = 0x32
    dut.uio_in.value = 0x33

    # Final Delay
    await Timer(20, units="ns")
    dut._log.info("--- Testbench Complete ---")
