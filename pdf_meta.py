import streamlit as st
import pikepdf
import logging
from datetime import datetime
import pytz

# Configure logging
logging.basicConfig(
    filename="pdf_metadata_viewer.log",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Function to parse PDF date format and convert to EST
def parse_pdf_date(date_str):
    try:
        # PDF date format: D:YYYYMMDDHHmmSSOHH'mm'
        date_str = str(date_str).strip()
        if date_str.startswith('D:'):
            date_str = date_str[2:]
        
        # Extract date components
        year = int(date_str[0:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        hour = int(date_str[8:10]) if len(date_str) >= 10 else 0
        minute = int(date_str[10:12]) if len(date_str) >= 12 else 0
        second = int(date_str[12:14]) if len(date_str) >= 14 else 0
        
        # Create datetime object (assume UTC if no timezone info)
        dt = datetime(year, month, day, hour, minute, second)
        dt = pytz.utc.localize(dt)
        
        # Convert to EST
        est = pytz.timezone('US/Eastern')
        dt_est = dt.astimezone(est)
        
        # Format as user-friendly string
        return dt_est.strftime('%B %d, %Y at %I:%M:%S %p %Z')
    except:
        # If parsing fails, return original string
        return str(date_str)

# Function to Extract Metadata
def extract_metadata(pdf_file):
    import io
    try:
        # Reset file pointer and convert to BytesIO for pikepdf
        pdf_file.seek(0)
        pdf_bytes = io.BytesIO(pdf_file.read())
        pdf_bytes.seek(0)
        
        with pikepdf.open(pdf_bytes) as pdf:
            if pdf.is_encrypted:
                logging.warning("Encrypted PDF uploaded.")
                st.error("The uploaded PDF is encrypted and cannot be processed.")
                return None
            
            # Convert pikepdf metadata object to regular Python dict
            metadata_dict = {}
            try:
                docinfo = pdf.docinfo
                # Iterate and convert each key-value pair to regular Python types
                for key in docinfo:
                    try:
                        metadata_dict[str(key)] = str(docinfo[key])
                    except:
                        # Skip any problematic key-value pairs
                        continue
                
                logging.info(f"Metadata successfully extracted: {len(metadata_dict)} fields.")
                return metadata_dict if metadata_dict else {}
            except Exception as meta_error:
                logging.error(f"Error accessing PDF metadata: {meta_error}")
                # Return empty dict instead of None if metadata can't be accessed
                return {}
    except NotImplementedError as nie:
        logging.error(f"NotImplementedError: {nie}")
        st.error("PDF feature not supported or file is invalid.")
        return None
    except Exception as e:
        logging.error(f"Error extracting metadata: {e}")
        st.error("An error occurred while extracting metadata.")
        return None

# Function to update PDF metadata
def update_pdf_metadata(pdf_file, updated_metadata):
    import io
    try:
        # Reset file pointer and convert to BytesIO
        pdf_file.seek(0)
        pdf_bytes = io.BytesIO(pdf_file.read())
        pdf_bytes.seek(0)
        
        # Open PDF and update metadata in docinfo
        pdf = pikepdf.open(pdf_bytes)
        
        # Get all existing metadata to preserve values not being changed
        existing_metadata = {}
        try:
            for key in pdf.docinfo:
                existing_metadata[str(key)] = str(pdf.docinfo[key])
        except:
            pass
        
        # Update docinfo (traditional PDF metadata dictionary)
        for key, value in updated_metadata.items():
            if value:  # Only update if value is not empty
                # Ensure key starts with '/' for PDF dictionary keys
                dict_key = key if key.startswith('/') else f'/{key}'
                # Set the metadata value in docinfo
                pdf.docinfo[dict_key] = value
        
        # If ModDate wasn't explicitly updated, preserve the original or remove it
        # to prevent pikepdf from auto-updating it
        if '/ModDate' not in updated_metadata and 'ModDate' not in updated_metadata:
            if '/ModDate' in existing_metadata and existing_metadata['/ModDate']:
                pdf.docinfo['/ModDate'] = existing_metadata['/ModDate']
        
        # Save to BytesIO without normalizing content to preserve dates
        output_bytes = io.BytesIO()
        pdf.save(output_bytes, normalize_content=False)
        output_bytes.seek(0)
        
        logging.info(f"Metadata updated successfully: {list(updated_metadata.keys())}")
        return output_bytes
    except Exception as e:
        logging.error(f"Error updating PDF metadata: {e}")
        st.error(f"Failed to update metadata: {e}")
        return None

# Function to get format hint for metadata fields
def get_format_hint(key):
    hints = {
        'Title': 'e.g., My Document Title',
        'Author': 'e.g., John Doe',
        'Subject': 'e.g., Document subject or description',
        'Keywords': 'e.g., keyword1, keyword2, keyword3',
        'Creator': 'e.g., Microsoft Word',
        'Producer': 'e.g., Adobe PDF Library',
        'CreationDate': 'e.g., D:20260211120000 (Format: D:YYYYMMDDHHmmSS)',
        'ModDate': 'e.g., D:20260211120000 (Format: D:YYYYMMDDHHmmSS)',
    }
    
    # Check for exact match or partial match
    for hint_key, hint_value in hints.items():
        if hint_key.lower() in key.lower():
            return hint_value
    
    return 'Enter new value for this field'
    
# Streamlit App
# to provide a simple UI with a Title, its description, a side bar with information on how to use with an example. 
def main():
    st.set_page_config(
        page_title="PDF Metadata Viewer",
        page_icon="📄",
        layout="centered",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
        <style>
        .main-header {
            font-size: 3rem;
            font-weight: 700;
            color: #1E88E5;
            text-align: center;
            margin-bottom: 0.5rem;
        }
        .sub-header {
            text-align: center;
            color: #666;
            font-size: 1.1rem;
            margin-bottom: 2rem;
        }
        .stButton>button {
            width: 100%;
            background-color: #1E88E5;
            color: white;
            font-weight: 600;
            border-radius: 10px;
            padding: 0.75rem;
            border: none;
            transition: all 0.3s;
        }
        .stButton>button:hover {
            background-color: #1565C0;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(30, 136, 229, 0.4);
        }
        .metadata-card {
            background-color: #F5F5F5;
            padding: 1rem;
            border-radius: 10px;
            border-left: 4px solid #1E88E5;
            margin: 0.5rem 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Add rerun button to sidebar
    with st.sidebar:
        st.markdown("### 🔄 Controls")
        if st.button("🔄 Rerun (Start Fresh)", use_container_width=True):
            st.session_state.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📖 How to Use")
        st.markdown("""
        <div style='background-color: #E3F2FD; padding: 1rem; border-radius: 10px;'>
        <ol style='margin: 0; padding-left: 1.5rem;'>
            <li>📤 Upload your PDF file</li>
            <li>✅ Select metadata fields</li>
            <li>🚀 Click Submit to view</li>
            <li>✏️ Edit fields (optional)</li>
            <li>💾 Download updated PDF</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("")
        st.markdown("### 💡 Example")
        st.info("Upload `sample.pdf` and select fields like `/Title`, `/Author`, or `/CreationDate` to see metadata.")
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown("""
        This tool extracts and displays embedded metadata from PDF documents, 
        including title, author, creation date, and more. You can also edit 
        metadata fields and download an updated PDF with your changes.
        """)
    
    # Main content
    st.markdown('<h1 class="main-header">📄 PDF Metadata Viewer</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Extract, view, and edit metadata from your PDF documents with ease</p>', unsafe_allow_html=True)
    
    st.markdown("")
    uploaded_file = st.file_uploader(
        "📤 Choose your PDF file",
        type=["pdf"],
        help="Maximum file size: 10MB"
    )
    
    if uploaded_file is not None:
        # Validate file size (max 10MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            st.error("⚠️ File is too large. Please upload a PDF under 10MB.")
            logging.warning("File upload rejected due to size limit.")
            return
        
        # Display file info in columns
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📁 File Name", uploaded_file.name)
        with col2:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            st.metric("📊 File Size", f"{file_size_mb:.2f} MB")
        with col3:
            st.metric("📋 Type", "PDF")
        
        st.markdown("---")
        
        with st.spinner('🔍 Extracting metadata...'):
            metadata = extract_metadata(uploaded_file)
        
        if metadata is not None:
            keys = list(metadata.keys())
            if not keys:
                st.warning("⚠️ No metadata found in this PDF.")
                logging.info("No metadata present in the uploaded PDF.")
                return
            
            st.success(f"✅ Found {len(keys)} metadata fields!")
            
            st.markdown("### 🎯 Select Fields to Display")
            st.markdown("Choose the metadata fields you'd like to view:")
            
            # Organize checkboxes in columns for better layout
            num_cols = 2
            cols = st.columns(num_cols)
            selected_keys = []
            
            for idx, key in enumerate(keys):
                col_idx = idx % num_cols
                with cols[col_idx]:
                    if st.checkbox(f"{key}", key=key):
                        selected_keys.append(key)
            
            st.markdown("")
            if st.button("🚀 Submit", use_container_width=True):
                if selected_keys:
                    st.session_state['displayed_metadata'] = selected_keys
                    st.session_state['all_metadata'] = metadata
                    st.markdown("---")
                    st.markdown("### 📊 Metadata Results")
                    
                    for key in selected_keys:
                        value = metadata.get(key)
                        # Format date fields specially
                        if 'date' in key.lower() or 'Date' in key:
                            value = parse_pdf_date(value)
                        
                        # Display in a styled card
                        st.markdown(f"""
                        <div class='metadata-card'>
                            <strong style='color: #1E88E5;'>{key}</strong><br>
                            <span style='color: #333;'>{value}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    logging.info(f"Displayed metadata fields: {selected_keys}")
                else:
                    st.warning("Please select at least one metadata field.")
                    logging.info("Submit clicked with no fields selected.")
            
            # Edit Metadata Section
            if 'displayed_metadata' in st.session_state and st.session_state['displayed_metadata']:
                st.markdown("---")
                st.markdown("### ✏️ Edit Metadata")
                st.markdown("Select fields to edit and provide new values:")
                
                # Select fields to edit
                st.markdown("#### 📝 Select Fields to Edit")
                displayed_keys = st.session_state['displayed_metadata']
                
                # Organize checkboxes in columns
                num_cols = 2
                cols = st.columns(num_cols)
                fields_to_edit = []
                
                for idx, key in enumerate(displayed_keys):
                    col_idx = idx % num_cols
                    with cols[col_idx]:
                        if st.checkbox(f"Edit {key}", key=f"edit_{key}"):
                            fields_to_edit.append(key)
                
                # Show input fields for selected items
                if fields_to_edit:
                    st.markdown("#### 📥 Enter New Values")
                    updated_values = {}
                    
                    for key in fields_to_edit:
                        current_value = st.session_state['all_metadata'].get(key, '')
                        format_hint = get_format_hint(key)
                        
                        st.markdown(f"**{key}**")
                        st.caption(f"💡 Format: {format_hint}")
                        st.caption(f"Current value: `{current_value}`")
                        
                        new_value = st.text_input(
                            f"New value for {key}",
                            value="",
                            key=f"input_{key}",
                            placeholder=format_hint,
                            label_visibility="collapsed"
                        )
                        
                        if new_value:  # Only add if user entered a value
                            updated_values[key] = new_value
                        
                        st.markdown("")
                    
                    # Save options
                    if updated_values:
                        st.markdown("")
                        st.markdown("#### 💾 Save Options")
                        
                        save_option = st.radio(
                            "Choose how to save:",
                            ["Save as new file", "Overwrite original file"],
                            key="save_option",
                            horizontal=True
                        )
                        
                        if save_option == "Save as new file":
                            default_name = f"updated_{uploaded_file.name}"
                            new_filename = st.text_input(
                                "New filename:",
                                value=default_name,
                                key="new_filename",
                                help="Enter the name for the new PDF file"
                            )
                        else:
                            st.warning("⚠️ This will replace the original file when you download it.")
                            new_filename = uploaded_file.name
                        
                        st.markdown("")
                        
                        # Save button
                        col1, col2 = st.columns([3, 1])
                        with col2:
                            if st.button("💾 Save Changes", use_container_width=True, type="primary"):
                                with st.spinner('💫 Updating metadata...'):
                                    updated_pdf = update_pdf_metadata(uploaded_file, updated_values)
                                    
                                    if updated_pdf:
                                        st.success("✅ Metadata updated successfully!")
                                        
                                        # Provide download button with chosen filename
                                        download_label = "📥 Download Updated PDF" if save_option == "Save as new file" else "📥 Download (Overwrite Original)"
                                        
                                        st.download_button(
                                            label=download_label,
                                            data=updated_pdf,
                                            file_name=new_filename,
                                            mime="application/pdf",
                                            use_container_width=True
                                        )
                                        
                                        save_mode = "new file" if save_option == "Save as new file" else "overwrite"
                                        logging.info(f"PDF metadata updated ({save_mode}): {list(updated_values.keys())}")
                    else:
                        st.info("💡 Enter new values for the selected fields to enable saving.")
                else:
                    st.info("💡 Select fields above to edit their values.")
if __name__ == "__main__":
    main() 