import streamlit as st
import json
import sys
import os
import io # Needed for handling file content in memory

# --- Helper function (from original script) ---
def create_notebook_cell(source_lines):
    """Creates a Jupyter notebook code cell JSON structure."""
    processed_source = []
    for line in source_lines:
        processed_source.append(line.rstrip('\n') + '\n')
    if processed_source:
         processed_source[-1] = processed_source[-1].rstrip('\n')

    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": processed_source
    }

# --- Modified Conversion Logic (takes content string, returns notebook string) ---
def convert_py_to_ipynb_content(py_content, original_filename="notebook.py"):
    """
    Converts Python script content (string) to a Jupyter notebook JSON string,
    splitting cells based on '# @title' comments.
    Returns the notebook content as a JSON formatted string.
    """
    try:
        # Use io.StringIO to treat the string content like a file for line reading
        # Or simply split the string into lines
        lines = py_content.splitlines(True) # Keep line endings
    except Exception as e:
        st.error(f"Error processing input content: {e}")
        return None # Indicate failure

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
    for line in lines:
        if line.strip().startswith("# @title"):
            if current_cell_lines:
                notebook["cells"].append(create_notebook_cell(current_cell_lines))
            current_cell_lines = [line]
        else:
            current_cell_lines.append(line)

    if current_cell_lines:
        notebook["cells"].append(create_notebook_cell(current_cell_lines))
    elif not lines:
        st.warning("Input file appears empty. Creating an empty notebook.")

    try:
        # Return the notebook structure as a JSON string
        return json.dumps(notebook, indent=2)
    except Exception as e:
        st.error(f"Error formatting notebook JSON: {e}")
        return None # Indicate failure

# --- Streamlit App UI ---

st.set_page_config(page_title="Python to Notebook Converter", layout="wide")

st.title("🐍 Python Script to Jupyter Notebook Converter 📝")
st.markdown(
    """
    Upload your Python (`.py`) script below. The script will be converted
    into a Jupyter/Colab notebook (`.ipynb`) format.
    Cells in the notebook will be split based on lines starting exactly with `# @title`.
    """
)

uploaded_file = st.file_uploader("Choose a Python file (.py)", type="py")

if uploaded_file is not None:
    # To read file as string:
    try:
        py_content = uploaded_file.read().decode("utf-8")
        st.success(f"Successfully uploaded '{uploaded_file.name}'")

        # Perform the conversion
        st.markdown("---")
        st.subheader("Conversion Result")
        notebook_json_content = convert_py_to_ipynb_content(py_content, uploaded_file.name)

        if notebook_json_content:
            # Prepare download file name
            base_name, _ = os.path.splitext(uploaded_file.name)
            download_filename = f"{base_name}.ipynb"

            st.download_button(
                label="⬇️ Download Notebook (.ipynb)",
                data=notebook_json_content.encode('utf-8'), # Encode string to bytes
                file_name=download_filename,
                mime="application/x-ipynb+json", # Standard MIME type for notebooks
            )

            # Optionally display a preview (might be long)
            with st.expander("Show Generated Notebook JSON (preview)"):
                st.code(notebook_json_content, language='json')

    except UnicodeDecodeError:
        st.error("Error reading file: Could not decode the file using UTF-8. Please ensure the file is UTF-8 encoded.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

else:
    st.info("Please upload a Python file to begin.")

st.markdown("---")
st.markdown("Created with Streamlit")