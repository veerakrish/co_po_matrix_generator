import streamlit as st
import pandas as pd
import spacy
import sys
from utils.nlp_processor import extract_cos, process_text
from utils.matrix_generator import generate_matrix
from data.program_outcomes import PROGRAM_OUTCOMES
import io

# Load spaCy model
@st.cache_resource
def load_spacy_model():
    try:
        return spacy.load('en_core_web_sm')
    except OSError:
        st.info("Downloading language model... (this may take a while)")
        spacy.cli.download('en_core_web_sm')
        return spacy.load('en_core_web_sm')

def process_syllabus(content, nlp, threshold):
    """Process a single syllabus and return its analysis results"""
    try:
        cos = extract_cos(content)
        if not cos:
            return None
        
        matrix, debug_info = generate_matrix(cos, PROGRAM_OUTCOMES, nlp, threshold)
        
        # Create matrix dataframe
        matrix_df = pd.DataFrame(
            data=matrix,
            index=pd.Index([f"CO{i+1}" for i in range(len(cos))]),
            columns=pd.Index([f"PO{i+1}" for i in range(len(PROGRAM_OUTCOMES))])
        )
        
        # Calculate averages
        averages = []
        for col in matrix_df.columns:
            col_values = pd.to_numeric(matrix_df[col], errors='coerce')
            avg = col_values.mean()
            averages.append(f"{avg:.2f}" if pd.notnull(avg) else '')
        
        matrix_df.loc['Average'] = averages
        
        # Create CO dataframe
        co_data = {
            'CO': [co[0] for co in cos],
            'Description': [co[1] for co in cos],
            'K-Level': [co[2] for co in cos]
        }
        co_df = pd.DataFrame(co_data)
        
        return {
            'cos': co_df,
            'matrix': matrix_df,
            'debug_info': debug_info,
            'threshold': threshold
        }
    except Exception as e:
        st.error(f"Error processing syllabus: {str(e)}")
        return None

def main():
    st.set_page_config(page_title="CO-PO Mapping Generator", layout="wide")
    
    st.title("CO-PO Mapping Matrix Generator")
    
    # Load custom CSS
    with open("assets/app_style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    # Initialize session states
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = {}
    if 'file_contents' not in st.session_state:
        st.session_state.file_contents = {}
    if 'file_thresholds' not in st.session_state:
        st.session_state.file_thresholds = {}
    if 'matrix_states' not in st.session_state:
        st.session_state.matrix_states = {}
    
    try:
        nlp = load_spacy_model()
        
        # Multiple file upload
        uploaded_files = st.file_uploader(
            "Upload syllabus files (TXT format)", 
            type=["txt"], 
            accept_multiple_files=True
        )
        
        if uploaded_files:
            # Process new files
            for uploaded_file in uploaded_files:
                if uploaded_file.name not in st.session_state.file_contents:
                    content = uploaded_file.getvalue().decode("utf-8")
                    st.session_state.file_contents[uploaded_file.name] = content
                    st.session_state.file_thresholds[uploaded_file.name] = 0.80  # Default threshold
                    results = process_syllabus(content, nlp, 0.80)
                    if results:
                        st.session_state.processed_files[uploaded_file.name] = results
            
            # Display POs (common for all files)
            st.subheader("Program Outcomes")
            po_data = {
                'PO': [po[0] for po in PROGRAM_OUTCOMES],
                'Description': [po[1] for po in PROGRAM_OUTCOMES],
                'K-Level': [po[2] for po in PROGRAM_OUTCOMES]
            }
            po_df = pd.DataFrame(po_data)
            st.dataframe(po_df)
            
            # Create tabs for each processed file
            if st.session_state.processed_files:
                tabs = st.tabs(list(st.session_state.processed_files.keys()))
                
                for tab, filename in zip(tabs, st.session_state.processed_files.keys()):
                    with tab:
                        st.subheader(f"Analysis for {filename}")
                        
                        # Display Course Outcomes
                        st.write("Course Outcomes:")
                        st.dataframe(st.session_state.processed_files[filename]['cos'])
                        
                        # Add threshold slider for each file
                        current_threshold = st.session_state.file_thresholds.get(filename, 0.80)
                        new_threshold = st.slider(
                            "Similarity Threshold",
                            min_value=0.0,
                            max_value=1.0,
                            value=current_threshold,
                            step=0.01,
                            key=f"threshold_{filename}",
                            help="Adjust the similarity threshold for CO-PO mapping"
                        )
                        
                        # Update matrix if threshold changed
                        if new_threshold != current_threshold:
                            st.session_state.file_thresholds[filename] = new_threshold
                            try:
                                new_results = process_syllabus(
                                    st.session_state.file_contents[filename],
                                    nlp,
                                    new_threshold
                                )
                                if new_results:
                                    st.session_state.processed_files[filename] = new_results
                            except Exception as e:
                                st.error(f"Error updating matrix: {str(e)}")
                        
                        # Display Matrix in container
                        matrix_container = st.container()
                        with matrix_container:
                            st.write("CO-PO Mapping Matrix:")
                            st.dataframe(st.session_state.processed_files[filename]['matrix'])
                        
                        # Debug Information
                        with st.expander("Debug Information"):
                            results = st.session_state.processed_files[filename]
                            st.write(f"Similarity Threshold: {results['debug_info']['threshold']}")
                            
                            st.write("Similarity Scores:")
                            similarity_data = []
                            for co_id, po_scores in results['debug_info']['similarity_scores'].items():
                                row = {'CO': co_id}
                                row.update(po_scores)
                                similarity_data.append(row)
                            st.dataframe(pd.DataFrame(similarity_data))
                            
                            st.write("Preprocessed Terms:")
                            for co_id, terms in results['debug_info']['preprocessed_terms'].items():
                                st.write(f"{co_id}: {', '.join(terms)}")
                        
                        # Download button for individual file
                        buffer = io.BytesIO()
                        st.session_state.processed_files[filename]['matrix'].to_csv(buffer, index=True)
                        buffer.seek(0)
                        st.download_button(
                            f"Download Matrix for {filename} as CSV",
                            buffer,
                            f"co_po_matrix_{filename}.csv",
                            "text/csv",
                            key=f'download-csv-{filename}'
                        )
            
            # Add button to clear all processed files
            if st.button("Clear All Files"):
                st.session_state.processed_files = {}
                st.session_state.file_contents = {}
                st.session_state.file_thresholds = {}
                st.session_state.matrix_states = {}
                
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
