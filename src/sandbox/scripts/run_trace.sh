#!/bin/bash

# This is run inside the Docker Container
# Launch the Xvfb for GUI support next connect Intel PIN to the JVM
# Runs the target jar file and captures the opcode trace

# Args used in this Script
# $1 - path to the jar file inside the container
# $2 - path to the output trace file inside the container
# $3 - max opcodes to capture and saved (default set to 1000000 - 1M)
# $4 - execution timeout in seconds (default set to 60)
# $5 - optional path to an input file which use for program's stdin
# Which is used for interactive CLI programs that need some inputs to start


# Argument set
JAR_FILE=${1}
OUTPUT_FILE=${2}
MAX_OPCODES=${3:-1000000}
TIMEOUT_SEC=${4:-60}
INPUT_FILE=${5:-}

PIN=/pin/pin
PINTOOL=/pintool/opcode_tracer.so


# Input Validation
if [ -z "$JAR_FILE" ] || [ -z "$OUTPUT_FILE" ]; then
    echo "[run_trace] ERROR: JAR_FILE and OUTPUT_FILE arguments are required"
    echo "Usage: run_trace.sh <jar_file> <output_file> [max_opcodes] [timeout] [input_file]"
    exit 1
fi

if [ ! -f "$JAR_FILE" ]; then
    echo "[run_trace] ERROR: JAR file not found: $JAR_FILE"
    exit 1
fi

if [ ! -f "$PINTOOL" ]; then
    echo "[run_trace] ERROR: Pintool not found: $PINTOOL"
    exit 1
fi


# Start the Xvfb virtual display
# Only GUI programs will use this, CLI programs ignore the DISPLAY variable
Xvfb :99 -screen 0 1024x768x24 -ac &
XVFB_PID=$!
export DISPLAY=:99
sleep 0.5

echo "[run_trace] JAR: $JAR_FILE"
echo "[run_trace] Output: $OUTPUT_FILE"
echo "[run_trace] Max opcodes: $MAX_OPCODES"
echo "[run_trace] Timeout: ${TIMEOUT_SEC}s"


# Identify stdin source
if [ -n "$INPUT_FILE" ] && [ -f "$INPUT_FILE" ]; then
    STDIN_SOURCE="$INPUT_FILE"
    echo "[run_trace] Input: $INPUT_FILE (Feeding as stdin)"
else
    STDIN_SOURCE="/dev/null"
    echo "[run_trace] Input: None (stdin closed)"
fi


# Run Intel PIN with JVM
# PIN Flags
# -t path to the pintool
# -o output file for opcode 
# -max maximum opcodes to capture then stop it
# -- use to separates PIN flags from the target program and it args

# -XX:CompileThreshold=100 - lower the JIT compilation threshold
# Which makes JIT compilted code to visible in the trace even for short runs

# -XX:+TieredCompilation - enable to produce more native instruction to the trace

timeout "$TIMEOUT_SEC" "$PIN" \
    -injection child \
    -t "$PINTOOL" \
    -o "$OUTPUT_FILE" \
    -max "$MAX_OPCODES" \
    -- \
    java \
    -XX:CompileThreshold=100 \
    -XX:+TieredCompilation \
    -jar "$JAR_FILE" \
    < "$STDIN_SOURCE" \
    >/dev/null 2>/dev/null

EXIT_CODE=$?


# Cleanup the processes
kill "$XVFB_PID" 2>/dev/null
wait "$XVFB_PID" 2>/dev/null


# Exit types
# Code 124 - timeout (normally and intentionally keep the program run until timeout)
# Code 0 - program finished naturally before timeout
# Any other code - error or program specific exits
if [ "$EXIT_CODE" -eq 124 ]; then
    echo "[run_trace] Timeout reached - trace captured up to max opcodes"
elif [ "$EXIT_CODE" -eq 0 ]; then
    echo "[run_trace] Program finished naturally"
else
    echo "[run_trace] Process exited with code: $EXIT_CODE"
fi

# Finaly check the output file to confirm the content
if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
    LINE_COUNT=$(wc -l < "$OUTPUT_FILE")
    echo "[run_trace] Opcodes recorded: $LINE_COUNT"
    exit 0
else
    echo "[run_trace] WARNING: Output file is empty or missing - no opcodes captured"
    exit 1
fi