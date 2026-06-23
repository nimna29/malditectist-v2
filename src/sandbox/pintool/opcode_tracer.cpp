/*
Opcode Tracer - Pintool
Intel PIN dynamic binary instrumentation tool

Traget of the tracer is to intercepts every instructions executed at runtime
And logs that opcode strings into a txt file

This tracer works at the x86 & x64 native instruction level
When connected with a JVM process it captures the actual executed native machine
instructions, which also includes the JIT compiled Java code
Which is the runtime behavioural fingerprint of the Java program

Intel Pin Docs: https://software.intel.com/sites/landingpage/pintool/docs/99633/Pin/doc/html/index.html

Build is handled by the Dockerfile
make PIN_ROOT=/pin obj-intel64/opcode_tracer.so

but can be done manually with:
docker build -t malditectist-tracer .

Usage (Example):
pin -t opcode_tracer.so -o output.txt -max 1000000 -- java -jar program.jar

Flags in the Command
-o output file path
-max maximum number of opcodes to capture (0 = unlimited)
*/

#include "pin.H"
#include <atomic>
#include <fstream>
#include <iostream>

// Knobs - CLI flags for the Pintool
KNOB<std::string> KnobOutputFile(
    KNOB_MODE_WRITEONCE, "pintool",
    "o", "opcodes.txt",
    "Output file to write opcode strings"
);

KNOB<UINT64> KnobMaxOpcodes(
    KNOB_MODE_WRITEONCE, "pintool",
    "max", "0",
    "Maximum opcodes to capture (0 = unlimited)"
);

// Global States
static std::ofstream outFile;
static std::atomic<UINT64> opcodeCount(0);
static UINT64 maxOpcodes = 0;
static bool limitReached = false;

// Analyzing function to call before every instruction
VOID LogOpcode(UINT32 opcode)
{
    // Check if the opcodes limit has reached
    if (limitReached)
        return;

    if (maxOpcodes > 0 && opcodeCount.load() >= maxOpcodes) {
        limitReached = true;
        return;
    }

    // OPCODE_StringShort returns example - "MOV", "PUSH", "JUMP"
    outFile << OPCODE_StringShort(opcode) << "\n";
    opcodeCount++;
}

// Instrumentation function to call once per instruction on compile time
VOID Instruction(INS ins, VOID* v)
{
    if (limitReached)
        return;

    // Insert a call to LogOpcode before every instruction is executed
    INS_InsertCall(
        ins,
        IPOINT_BEFORE,
        (AFUNPTR)LogOpcode,
        IARG_UINT32, INS_Opcode(ins),
        IARG_END
    );
}

// Finalizing function to call when the program exits
VOID Fini(INT32 code, VOID* v)
{
    outFile.flush();
    outFile.close();
    std::cerr << "[opcode_tracer] Total opcodes captured: "
            << opcodeCount.load() << "\n";
}

// Usage - Prints the usage info for the Pintool
INT32 Usage()
{
    std::cerr << "MalDitectist V2 - Opcode Tracer\n"
            << "Logs x86/x64 opcode strings at runtime.\n\n"
            << KNOB_BASE::StringKnobSummary() << "\n";
    return -1;
}

// Main Function
int main(int argc, char* argv[])
{
    // Initialise PIN
    if (PIN_Init(argc, argv))
        return Usage();

    // Open the output file
    outFile.open(KnobOutputFile.Value().c_str());
    // Check if the output file is opened successfully
    if (!outFile.is_open()) {
        std::cerr << "[opcode_tracer] ERROR: Could not open output file: "
                << KnobOutputFile.Value() << "\n";
        return -1;
    }

    // Set the maximum number of opcodes to capture
    maxOpcodes = KnobMaxOpcodes.Value();

    // Print the output file and max opcodes information
    std::cerr << "[opcode_tracer] Output: " << KnobOutputFile.Value() << "\n";
    std::cerr << "[opcode_tracer] Max opcodes: "
            << (maxOpcodes == 0 ? "unlimited" : std::to_string(maxOpcodes))
            << "\n";

    // Register instrumentation and finalizing functions
    INS_AddInstrumentFunction(Instruction, 0);
    PIN_AddFiniFunction(Fini, 0);

    // Start the program - this never returns
    PIN_StartProgram();
    return 0;
}
