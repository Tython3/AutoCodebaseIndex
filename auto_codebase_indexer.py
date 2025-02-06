#!/usr/bin/env python3
"""
A complete Python program to build a hierarchical library index prompt for a large codebase.
It traverses directories, processes files, and uses LLM calls (via the llm_call function)
to generate summaries of files (with smart chunking for large files) and synthesizes a final
index prompt that is written to an output text file.
"""

import os
import re
import argparse

def llm_call(prompt, system_message, temperature, max_tokens):
    """
    Calls the GPT-4O-mini language model with the given parameters.
    In a real implementation, this function would make an API call to the LLM.
    For demonstration purposes, this stub returns a dummy summary.
    
    Parameters:
        prompt (str): The prompt text to send to the LLM.
        system_message (str): The system message guiding the LLM behavior.
        temperature (float): Sampling temperature for the LLM.
        max_tokens (int): The maximum number of tokens for the LLM's response.
    
    Returns:
        str: A dummy summary string.
    """
    # This is a stub implementation. Replace with actual API call as needed.
    dummy_response = f"LLM_Summary (truncated): {prompt[:75].replace(chr(10), ' ')}..."
    return dummy_response

def split_into_logical_chunks(file_content, file_extension, max_chunk_length=10000):
    """
    Splits file content into logical chunks for summarization.
    For Python files (.py), attempts to split by function or class definitions.
    For other file types, or if logical splitting yields overly large chunks,
    it falls back to fixed-size chunking.
    
    Parameters:
        file_content (str): The content of the file.
        file_extension (str): The file extension (e.g., ".py").
        max_chunk_length (int): The maximum character length for each chunk.
    
    Returns:
        List[str]: A list of code chunks.
    """
    chunks = []
    if file_extension.lower() == ".py":
        # Use regex to split on lines starting with 'def ' or 'class '
        pattern = re.compile(r'(?=^(def |class ))', re.MULTILINE)
        parts = pattern.split(file_content)
        # Filter out empty parts and further split any part exceeding the max_chunk_length
        for part in parts:
            part = part.strip()
            if part:
                if len(part) > max_chunk_length:
                    for i in range(0, len(part), max_chunk_length):
                        chunks.append(part[i:i + max_chunk_length])
                else:
                    chunks.append(part)
    else:
        # For non-Python files or when logical splitting is not applicable, use fixed-size chunking.
        if len(file_content) > max_chunk_length:
            for i in range(0, len(file_content), max_chunk_length):
                chunks.append(file_content[i:i + max_chunk_length])
        else:
            chunks.append(file_content)
    return chunks

def summarize_file(file_path):
    """
    Reads a file, and generates a concise summary of its purpose and functionality
    by using LLM calls. If the file is too large, it is divided into logical chunks,
    each summarized separately, and then synthesized into one overall summary.
    
    Parameters:
        file_path (str): The path to the file to summarize.
    
    Returns:
        str: The summary of the file or an error message if reading fails.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
    except Exception as e:
        return f"Error reading file: {e}"

    # Define a threshold for direct summarization (in characters)
    DIRECT_SUMMARY_THRESHOLD = 10000

    if len(file_content) <= DIRECT_SUMMARY_THRESHOLD:
        prompt = f"Please provide a concise summary of the following code:\n\n{file_content}"
        system_message = "You are a code summarization assistant."
        summary = llm_call(prompt, system_message, temperature=0.5, max_tokens=150)
        return summary

    # For larger files, perform smart chunking.
    _, ext = os.path.splitext(file_path)
    chunks = split_into_logical_chunks(file_content, ext, max_chunk_length=DIRECT_SUMMARY_THRESHOLD)
    chunk_summaries = []
    for idx, chunk in enumerate(chunks):
        prompt = (f"Please provide a brief summary of the following code chunk (part {idx + 1}):\n\n"
                  f"{chunk}")
        system_message = "You are a code summarization assistant."
        chunk_summary = llm_call(prompt, system_message, temperature=0.5, max_tokens=150)
        chunk_summaries.append(chunk_summary)

    # Synthesize an overall summary from the chunk summaries.
    synthesis_prompt = "Please synthesize the following chunk summaries into one overall summary for the entire file:\n\n"
    synthesis_prompt += "\n".join(chunk_summaries)
    system_message = "You are a code summarization assistant."
    overall_summary = llm_call(synthesis_prompt, system_message, temperature=0.5, max_tokens=200)
    return overall_summary

def process_directory(directory, indent=0):
    """
    Recursively traverses a directory, processing subdirectories and files,
    and builds a hierarchical list of strings that represents the directory structure,
    file names, and their summaries.
    
    Parameters:
        directory (str): The directory path to process.
        indent (int): The current indentation level for hierarchical formatting.
    
    Returns:
        List[str]: A list of strings representing lines of the directory index.
    """
    index_lines = []
    indent_str = "    " * indent
    dir_name = os.path.basename(directory) if os.path.basename(directory) else directory
    index_lines.append(f"{indent_str}Directory: {dir_name}")

    try:
        entries = sorted(os.listdir(directory))
    except Exception as e:
        index_lines.append(f"{indent_str}    Error reading directory: {e}")
        return index_lines

    for entry in entries:
        path = os.path.join(directory, entry)
        if os.path.isdir(path):
            # Recursively process subdirectories.
            index_lines.extend(process_directory(path, indent=indent + 1))
        elif os.path.isfile(path):
            # Process files and generate summaries.
            file_summary = summarize_file(path)
            index_lines.append(f"{indent_str}    File: {entry}")
            index_lines.append(f"{indent_str}        Summary: {file_summary}")
    return index_lines

def build_library_index(root_directory):
    """
    Constructs the final library index prompt that includes the entire directory
    structure with file names and their summaries.
    
    Parameters:
        root_directory (str): The root directory of the codebase.
    
    Returns:
        str: The final hierarchical library index prompt.
    """
    index_lines = process_directory(root_directory)
    final_index = "\n".join(index_lines)
    return final_index

def main():
    parser = argparse.ArgumentParser(
        description="Build a hierarchical library index prompt for a large codebase."
    )
    parser.add_argument("root_directory", help="Root directory of the codebase to index.")
    parser.add_argument(
        "--output", default="library_index.txt",
        help="Output file for the library index prompt (default: library_index.txt)."
    )
    args = parser.parse_args()

    if not os.path.isdir(args.root_directory):
        print(f"Error: The provided root directory '{args.root_directory}' is not a valid directory.")
        return

    try:
        final_index = build_library_index(args.root_directory)
        with open(args.output, 'w', encoding='utf-8') as output_file:
            output_file.write(final_index)
        print(f"Library index prompt successfully written to '{args.output}'.")
    except Exception as e:
        print(f"An error occurred during processing: {e}")

if __name__ == "__main__":
    main()
