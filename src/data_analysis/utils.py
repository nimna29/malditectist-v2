# This utils file contains helper functions for data analysis stage
# Two main responsibilities are:
# 1. Parse the tracer log to create manifest file for each opcode extraction
# 2. Stream the large opcode output files line by line 
# - without loading the entire file into memeory

import os
import re
import csv
from typing import Iterator, Optional
from datetime import datetime
import numpy as np
import json


# Log parser to create a manifest csv file

# Regex pattern to identify the start of the file processing header
FILE_HEADER_RE = re.compile(
    r"^\[(?P<index>\d+)/(?P<total>\d+)\]\s*-\s*(?P<filename>\S+\.jar)\s*$"
)

# Regex pattern to identify a generic timestamped log line
TIMESTAMP_RE = re.compile(r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")

# Regex pattern to identify the recorded opcode count
OPCODE_COUNT_RE = re.compile(r"Opcodes (?:recorded|captured):\s*([\d,]+)")

# Exit reasons to look for in the log file
EXIT_REASON_PATTERNS = [
    ("size_limit", re.compile(r"Output exceeded .*?MB - stopping trace early")),
    ("timeout", re.compile(r"Timeout reached")),
    ("natural_exit", re.compile(r"Program finished naturally")),
    ("skipped_already_traced", re.compile(r"SKIPPED - Already traced")),
    ("skipped_has_content", re.compile(r"SKIPPED - Trace file already have content")),
    ("docker_timeout", re.compile(r"Docker timeout .*?and container killed")),
    ("output_missing", re.compile(r"Output file is empty or missing")),
    ("docker_run_failed", re.compile(r"Docker run failed"))
]

# Regex pattern to check if the programs exit with a code
EXIT_CODE_RE = re.compile(r"Process exited with code:\s*(-?\d+)")

# Function to parse the timestamp from the log line
def parse_timestamp(line: str) -> Optional[str]:
    match = TIMESTAMP_RE.match(line)
    if match:
        return match.group("timestamp")
    return None

# Function to count the seconds between two timestamps
def seconds_between(ts_start: Optional[str], ts_end: Optional[str]) -> Optional[int]:
    
    # Return None if both timestamp is None
    if not ts_start or not ts_end:
        return None
    
    fmt = "%Y-%m-%d %H:%M:%S"
    
    # Try to parse the timestamps and calculate the difference in seconds
    try:
        t0 = datetime.strptime(ts_start, fmt)
        t1 = datetime.strptime(ts_end, fmt)
        return int((t1 - t0).total_seconds())
    
    except ValueError:
        return None


# Isolate the session to keep the last trace session in the log file
# Regex pattern to match the log line format with timestamp, logger name, log level, and message
LOG_LINE_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*-\s*(?P<logger>\S+)\s*-\s*(?P<level>\S+)\s*-\s*(?P<message>.*)$"
)

# Function to keep only log lines that belongs tracer module 
def filter_session_lines(log_lines: Iterator[str], session_start: str,
                        session_end: str, logger_name: str = "tracer") -> list:
    
    # Set an empty list to store the filtered log lines
    result = []
    last_logger = None
    last_ts = None
    
    # Loop the log lines and filter based on the session start and end timestamps
    for line in log_lines:
        match = LOG_LINE_RE.match(line)
        
        if match:
            last_ts = match.group("timestamp")
            last_logger = match.group("logger")

        if last_logger != logger_name:
            continue
        if last_ts is None:
            continue
        if not (session_start <= last_ts <= session_end):
            continue

        result.append(line)

    return result

# Function to parse the tracer log lines and yield a dictionary for each file
def parse_tracer_log(log_lines: Iterator[str]) -> Iterator[dict]:

    current = None
    block_lines = []
    last_ts = None
    
    # Function to finalize the current block and return the result as dictionary
    def final_result(block):
        
        # Return None if the block is None
        if block is None:
            return None
        text = "\n".join(block_lines)
        
        opcode_count = None
        match = OPCODE_COUNT_RE.search(text)
        
        # If the opcode count is found and convert it to an int and remove commas
        if match:
            opcode_count = int(match.group(1).replace(",", ""))
            
        exit_reason = None
        
        # Check for exit reasons in the log text using the regex patterns
        for name, pattern in EXIT_REASON_PATTERNS:
            if pattern.search(text):
                exit_reason = name
                break
        
        # Check for exit code in the log text using the regex pattern
        exit_code = None
        match = EXIT_CODE_RE.search(text)
        
        if match:
            exit_code = int(match.group(1))
        
        # If exit reason is None and exit code is not None
        # Set the exit reason to have the exit code   
        if exit_reason is None and exit_code is not None:
            exit_reason = f"exit_code_{exit_code}"
        
        max_size_hit = bool(re.search(r"Output exceeded .*?MB", text))
            
        # Last visible ts for duration calculation
        ts_end = block["timestamp_start"]
        
        # Loop through the block lines in reverse order to find the last ts
        for line in reversed(block_lines):
            ts = parse_timestamp(line)
            if ts:
                ts_end = ts
                break
        
        duration = seconds_between(block["timestamp_start"], ts_end)
        
        # Return the result as a dictionary with the info
        return_result = {
            "index": block["index"],
            "total": block["total"],
            "filename": block["filename"],
            "timestamp_start": block["timestamp_start"],
            "timestamp_end": ts_end,
            "duration_sec": duration,
            "opcode_count": opcode_count,
            "exit_reason": exit_reason,
            "exit_code": exit_code,
            "max_size_hit": max_size_hit,
            "raw_line_count": len(block_lines)
        }
        return return_result

    # Loop through the log lines and parse the tracer log
    for line in log_lines:
        
        ts = parse_timestamp(line)
        
        if ts:
            last_ts = ts

        # Check if the line matches the file header pattern
        header = FILE_HEADER_RE.match(line.strip())
        
        if header:
            # New block starts and finalizing and yielding the previous one 1st
            result = final_result(current)
            if result is not None:
                yield result
            
            current = {
                "index": int(header.group("index")),
                "total": int(header.group("total")),
                "filename": header.group("filename"),
                "timestamp_start": last_ts,
            }
            
            block_lines = [line]
        
        # If the line does not match the file header pattern
        # Append it to the current block lines
        else:
            if current is not None:
                block_lines.append(line)
    
    # Finalize and yield the last block after the loop ends
    result = final_result(current)
    if result is not None:
        yield result

# Function to build a manifest CSV file from the tracer log
def build_manifest_csv(log_path: str, output_csv_path: str,
                    session_start: str, session_end: str) -> dict:
    
    fieldnames = [
        "index", "total", "filename", "timestamp_start", "timestamp_end",
        "duration_sec", "opcode_count", "exit_reason", "exit_code",
        "max_size_hit", "raw_line_count"
    ]
    
    os.makedirs(os.path.dirname(output_csv_path) or ".", exist_ok=True)
    
    # Read the log file and filter the session lines based on the provided ts
    with open(log_path, "r", encoding="utf-8", errors="ignore") as log_file:
        session_lines = filter_session_lines(log_file, session_start, session_end)
    
    if not session_lines:
        raise ValueError(
            f"No tracer log lines found between {session_start} - {session_end} in {log_path} "
            f"Please provide the correct timestamps!"
        )
    
    count = 0
    
    # Write the parsed tracer log to the output csv file
    with open(output_csv_path, "w", newline="", encoding="utf-8") as out_file:
        writer = csv.DictWriter(out_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in parse_tracer_log(session_lines):
            writer.writerow(row)
            count += 1
    
    return_result = {
        "rows": count,
        "start_ts": session_start,
        "end_ts": session_end,
        "duration_sec": seconds_between(session_start, session_end),
    }
    
    return return_result

# Function to stream opcodes from a trace the raw file
def stream_opcodes(trace_path: str) -> Iterator[str]:
    # Stream the opcodes line by line without loading the entire file into memory
    with open(trace_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            opcode = line.rstrip("\n")
            if opcode:
                yield opcode

# Function to count the number of opcodes in a trace file
def count_opcodes_from_stream(trace_path: str) -> int:
    count = 0
    
    # Open the trace file and count the number of non empty lines
    with open(trace_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.rstrip("\n"):
                count += 1
        
    return count


# Function to build a vocabulary of unique opcodes from the trace files
# This function reads each trace file line by line and adds the unique opcodes to a set
# And it returns a sorted list of unique opcodes
def build_opcode_vocab(trace_paths: Iterator[str]) -> list:
    # Set an empty set to store unique opcodes
    vocab_set = set()
    
    # Loop through the trace file paths and read each file line by line
    for path in trace_paths:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                op = line.rstrip("\n")
                if op:
                    vocab_set.add(op)
                    
    return sorted(vocab_set)

# Function to encode the trace file to a numpy array of opcode ids
def encode_trace_to_npy(trace_path: str, vocab_to_id: dict, output_npy_path: str) -> int:
    
    # Define a generator function to yield the encoded opcode ids from the trace file
    def encoded_ids():
        with open(trace_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                op = line.rstrip("\n")
                if op:
                    yield vocab_to_id.get(op, -1)
    
    # Convert the generator to a numpy array of int32 and save it to the output npy file
    array = np.fromiter(encoded_ids(), dtype=np.int32)
    os.makedirs(os.path.dirname(output_npy_path) or ".", exist_ok=True)
    np.save(output_npy_path, array)
    
    return len(array)


# Functions to reduce the streaming again and again over for all 260 raw trace files
# Function to save the opcode vocab to a JSON file
def save_vocab(vocab: list, output_json_path: str) -> None:
    
    os.makedirs(os.path.dirname(output_json_path) or ".", exist_ok=True)
    
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(vocab, f, indent=2)
    
# Function to load a previously saved vocab list back from the JSON file
def load_vocab(vocab_json_path: str) -> list:
    
    with open(vocab_json_path, "r", encoding="utf-8") as f:
        return json.load(f)
    
# Function to decode the numpy array of opcode ids back to the original opcodes
def decode_trace_npy(npy_path: str, vocab: list) -> list:
    # Load the numpy array of opcode ids from the npy file 
    # Then decode it back to the original opcodes using the vocab list
    array = np.load(npy_path)
    decoded_trace = [vocab[i] if i >= 0 else "<UNK>" for i in array]
    return decoded_trace


# Functions for EDA and Feature Engineering

# This is a constant set as a safe limit for the maximum vocabulary size.
# It is intentionally large enough to support int32-encoded opcode ids.
MAX_SAFE_VOCAB_SIZE = np.iinfo(np.int32).max

def check_vocab_size(vocab: list) -> None:
    if len(vocab) > MAX_SAFE_VOCAB_SIZE:
        raise ValueError(
            f"Vocabulary has {len(vocab)} entries "
            f"Exceeding the int32 safe limit ({MAX_SAFE_VOCAB_SIZE})"
        )

# Small callable function to load the encoded trace    
def load_encoded_trace(npy_path: str, mmap: bool = True) -> np.ndarray:
    # Load the encoded trace from the npy file with optional memory mapping
    # Memory mapping useful for access large files without loading the entire file into memory
    return np.load(npy_path, mmap_mode = "r" if mmap else None)

# Function to calculate the frequency of each opcode id in the encoded trace array
def opcode_frequency(array: np.ndarray, vocab_size: int) -> np.ndarray:
    
    valid_array = array[array >= 0] # Ignore invalid opcode ids (negative values)
    # Use numpy bincount to count the occurrence of each opcode id in the valid array
    freq = np.bincount(valid_array, minlength = vocab_size).astype(np.int64)
    
    return freq

# Function to calculate the entropy of the opcode frequency distribution
def opcode_entropy(freq: np.ndarray) -> float:
    total = freq.sum()
    
    # If the total frequency is zero return entropy as 0.0 to avoid division by zero
    if total == 0:
        return 0.0
    
    # Calculate the probability of each opcode id by dividing the frequency by the total
    probs = freq[freq > 0] / total
    
    # Calculate the entropy using the following formula for all probs
    return float(-(probs * np.log2(probs)).sum())

# Function to calculate the n-gram counts of opcode ids in the encoded trace array
def ngram_counts(array: np.ndarray, vocab_size: int, n: int = 2) -> np.ndarray:
    
    valid_array = array[array >= 0].astype(np.int64)
    
    # If the length of the valid array is less than n
    # Return an array of zeros with size vocab_size ** n
    if len(valid_array) < n:
        return np.zeros(vocab_size ** n, dtype = np.int64)
    
    # Calculate the ngram ids by slide a window of size n over the valid array
    ids = np.zeros(len(valid_array) - n + 1, dtype = np.int64)
    
    # Loop the offsets from 0 to n-1 and calculate the ngram ids 
    # Multiplying the opcode ids by vocab_size to the power of (n - 1 - offset)
    # This is perform to create a unique id for each ngram combination of opcode ids
    for offset in range(n):
        ids += valid_array[
            offset: len(valid_array) - n + 1 + offset] * (vocab_size ** (n - 1 - offset))
    
    ngram_freq = np.bincount(ids, minlength = vocab_size ** n)
    
    return ngram_freq

# Function to calculate the Markov transition matrix from the encoded trace array
def markov_transition_matrix(array: np.ndarray, vocab_size: int) -> np.ndarray:
    
    # Calculate the bigram counts of opcode ids in the encoded trace array
    bigrams = ngram_counts(array, vocab_size, n=2).reshape(
                vocab_size, vocab_size).astype(np.float64)
    
    # Calculate the row sums of the bigram counts to normalize the transition probs
    row_sums = bigrams.sum(axis=1, keepdims = True)
    
    # Use errstate to ignore invalid / divide by zero warnings during the transition matrix calc
    with np.errstate(invalid = "ignore", divide = "ignore"):
        transition = np.where(row_sums > 0, bigrams / row_sums, 0.0)
        
    return transition

# Function to calculate the sliding window features from the encoded trace array
def sliding_window_features(array: np.ndarray, vocab_size: int, window_size: int,
                            step: Optional[int] = None) -> np.ndarray:
    
    # If step is not provided set it to the window_size to create nonoverlapping windows
    step = step or window_size
    n = len(array)
    
    # If the length of the array is zero return a empty array with shape (0, vocab_size)
    if n == 0:
        return np.zeros((0, vocab_size), dtype = np.float64)
    
    # Calculate the starting indices of the sliding windows based on above step size
    starts = range(0, n, step)
    rows = []
    
    # Loop the starting indices and extract the sliding windows from the array
    for start in starts:
        window = array[start: start + window_size]
        
        if len(window) == 0:
            continue
        
        # Calculate the frequency of each opcode id in the sliding window
        freq = opcode_frequency(window, vocab_size).astype(np.float64)
        total = freq.sum()
        
        # Normalize the frequency by dividing the total to get the related frequency
        rows.append(freq / total if total > 0 else freq)
    
    # Stack the normalized row frequencies into a 2D numpy array
    features = np.stack(rows) if rows else np.zeros((0, vocab_size), dtype = np.float64)
    
    return features
    


