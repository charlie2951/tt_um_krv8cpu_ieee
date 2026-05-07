module krv8cpu (
    input wire clk,
    input wire reset,
    input wire [15:0] instruction, 
    output reg [7:0] out_port      
);

    // Register Files and Accumulator
    reg [7:0] registers [3:0];
    reg [7:0] acc; 

    // Decoding
    wire [3:0] opcode = instruction[15:12];
    wire [1:0] rs1    = instruction[11:10];
    
    // --- Sign Extension Logic ---
    // Let's assume bits [5:0] are a 6-bit signed immediate.
    // We "extend" bit 5 to the 8-bit width.
   // wire [7:0] imm_extended = { {2{instruction[5]}}, instruction[5:0] };
     wire [7:0] imm_extended = instruction[7:0];
    // Standard 8-bit operand for logic ops
    wire [7:0] raw_imm = instruction[7:0];

    // Opcode Table
    localparam SLT = 4'h0, LDI = 4'h1, ADD = 4'h2, ADI = 4'h3,
               STA = 4'h4, SUB = 4'h5, AND = 4'h6, OR  = 4'h7,
               XOR = 4'h8, ANI = 4'h9, NOT = 4'hA, SLL = 4'hB,
               SRL = 4'hC, SLI = 4'hD, SRI = 4'hE, OUT = 4'hF;

    always @(posedge clk) begin
        if (reset) begin
            acc <= 8'h00;
            out_port <= 8'h00;
            registers[0] <= 8'h00; registers[1] <= 8'h00;
            registers[2] <= 8'h00; registers[3] <= 8'h00;
        end else begin
            registers[0] <= 8'h00; // x0 hardwired to 0

            case (opcode)
                // SLT: Signed Comparison (Set Less Than)
                // If ACC < Reg, ACC = 1, else 0
                SLT: acc <= ($signed(acc) < $signed(registers[rs1])) ? 8'h01 : 8'h00;

                // Load and Add use the Sign-Extended 6-bit immediate
                LDI: acc <= imm_extended;
                ADI: acc <= acc + imm_extended;

                // Standard Arithmetic (Two's Complement)
                ADD: acc <= acc + registers[rs1];
                SUB: acc <= acc - registers[rs1];

                // Logical Operations (Use raw 8-bit immediate for masking)
                AND: acc <= acc & registers[rs1];
                ANI: acc <= acc & raw_imm;
                OR:  acc <= acc | registers[rs1];
                XOR: acc <= acc ^ registers[rs1];
                NOT: acc <= ~acc;

                // Shift Operations
                SLI: acc <= acc << instruction[2:0]; // Shift by 3-bit immediate
                SRI: acc <= acc >> instruction[2:0];
                SLL: acc <= acc << registers[rs1];
                SRL: acc <= acc >> registers[rs1];
                // Data Movement
                STA: if (rs1 != 2'b00) registers[rs1] <= acc;
                OUT: out_port <= acc;

                default: acc <= acc;
            endcase
        end
    end
endmodule
