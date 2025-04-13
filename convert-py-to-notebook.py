import streamlit as st
import json
import sys
import os
import io # Needed for handling file content in memory

# --- Helper function (from original script) ---
def create_notebook_cell(cell_type, source_lines):
    """Creates a Jupyter notebook cell JSON structure."""
    processed_source = []
    for line in source_lines:
        processed_source.append(line.rstrip('\n') + '\n')
    if processed_source:
         processed_source[-1] = processed_source[-1].rstrip('\n')

    cell = {
        "cell_type": cell_type,
        "metadata": {},
        "source": processed_source
    }
    # Execution count and outputs are only for code cells
    if cell_type == "code":
        cell["execution_count"] = None
        cell["outputs"] = []
    return cell

# --- Modified Conversion Logic ---
def convert_py_to_ipynb_content(py_content, delimiter_string):
    """
    Converts Python script content (string) to a Jupyter notebook JSON string,
    splitting cells based on the provided delimiter string.
    Returns a tuple: (notebook_json_string, number_of_cells, delimiter_found_flag)
    or (None, 0, False) on error.
    """
    lines = py_content.splitlines(True) # Keep line endings
    cleaned_delimiter = delimiter_string.strip()

    if not cleaned_delimiter:
        st.error("Delimiter cannot be empty or just whitespace.")
        return None, 0, False # Indicate error

    notebook = {
        "cells": [],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {
                    "name": "ipython",
                    "version": 3
                },
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": sys.version.split()[0]
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }

    current_cell_lines = []
    cell_type = "code" # Default to code
    delimiter_found = False
    processed_first_line = False

    for line in lines:
        # Check if the line *starts* with the delimiter (ignoring leading whitespace on the line)
        if line.strip().startswith(cleaned_delimiter):
            delimiter_found = True
            # If we have accumulated lines for a previous cell, save it
            if current_cell_lines:
                notebook["cells"].append(create_notebook_cell(cell_type, current_cell_lines))
            # Start a new cell, extracting potential cell type hints (optional)
            # Example Hint: '# @title [markdown]' -> cell_type = 'markdown'
            if '[markdown]' in line.lower():
                 cell_type = "markdown"
            else:
                 cell_type = "code" # Default back to code for the new cell
            current_cell_lines = [line] # Start the new cell with the delimiter line itself

            processed_first_line = True # Mark that we've processed at least one line (or delimiter)

        else:
            # Add the line to the current cell
            current_cell_lines.append(line)
            processed_first_line = True # Mark that we've processed at least one line

    # Add the last remaining cell after the loop finishes
    # Only add if there were lines processed OR if it started with a delimiter
    if current_cell_lines or (delimiter_found and not processed_first_line) :
         notebook["cells"].append(create_notebook_cell(cell_type, current_cell_lines))
    elif not lines:
        st.warning("Input file appears empty. Creating an empty notebook.")

    num_cells = len(notebook["cells"])

    # Warn if the delimiter wasn't found but the file wasn't empty
    if not delimiter_found and lines and num_cells <= 1:
        st.warning(f"The delimiter string '{delimiter_string}' was not found in the file. The entire script is placed in a single cell.")
        # Set delimiter_found to True here just to avoid showing the error below,
        # as the warning above is more specific. User might intend a single cell.
        delimiter_found = True # Override for warning logic

    try:
        # Return the notebook structure as a JSON string, cell count, and delimiter status
        return json.dumps(notebook, indent=2), num_cells, delimiter_found
    except Exception as e:
        st.error(f"Error formatting notebook JSON: {e}")
        return None, 0, False # Indicate error

# --- Streamlit App UI ---

st.set_page_config(page_title="Python to Notebook Converter", layout="wide")

st.title("🐍 Python Script to Jupyter Notebook Converter 📝")
st.markdown(
    """
    Upload your Python (`.py`) script and specify the comment string that marks the beginning of a new cell.
    The script will be converted into a Jupyter/Colab notebook (`.ipynb`).
    """
)

# --- User Inputs ---
col1, col2 = st.columns([3, 2])

with col1:
    uploaded_file = st.file_uploader("1. Choose a Python file (.py)", type="py", key="file_uploader")

with col2:
    delimiter = st.text_input(
        "2. Enter Cell Delimiter String",
        value="# @title", # Default value
        key="delimiter_input",
        help="Lines starting with this text (after ignoring leading whitespace) will begin a new notebook cell."
    )

# --- Conversion Logic ---
if uploaded_file is not None and delimiter:
    # Check if delimiter is only whitespace right after input
    if not delimiter.strip():
        st.error("Delimiter cannot be empty or just whitespace. Please enter a valid delimiter string (e.g., '# @title').")
    else:
        # Read file content
        try:
            py_content = uploaded_file.read().decode("utf-8")
            st.success(f"Successfully uploaded and read '{uploaded_file.name}' using UTF-8 encoding.")

            # Perform the conversion
            st.markdown("---")
            st.subheader("Conversion Result")

            notebook_json_content, num_cells, delimiter_found = convert_py_to_ipynb_content(py_content, delimiter)

            if notebook_json_content:
                st.info(f"**Delimiter Used:** `{delimiter}`")
                st.metric(label="Cells Created", value=num_cells)

                # Prepare download file name
                base_name, _ = os.path.splitext(uploaded_file.name)
                download_filename = f"{base_name}.ipynb"

                st.download_button(
                    label="⬇️ Download Notebook (.ipynb)",
                    data=notebook_json_content.encode('utf-8'), # Encode string to bytes
                    file_name=download_filename,
                    mime="application/x-ipynb+json", # Standard MIME type for notebooks
                    key="download_button"
                )

                # Optionally display a preview
                with st.expander("Show Generated Notebook JSON (preview)"):
                    st.code(notebook_json_content, language='json')

            # If conversion function returned None, an error was already shown inside it.

        except UnicodeDecodeError:
            st.error(
                f"Error reading '{uploaded_file.name}': Could not decode the file using UTF-8. "
                "Please ensure the file is saved with UTF-8 encoding, or try converting it before uploading."
            )
        except Exception as e:
            st.error(f"An unexpected error occurred during processing: {e}")
            # Consider adding more detailed logging here if needed for debugging
            # logger.exception("Unexpected error during conversion")

elif uploaded_file is None:
    st.info("Please upload a Python file to begin.")
elif not delimiter: # Only trigger if file is uploaded but delimiter is cleared
     st.warning("Please enter a cell delimiter string.")


st.markdown("---")
st.markdown("Created with Streamlit")