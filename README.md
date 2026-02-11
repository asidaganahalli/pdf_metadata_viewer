# PDF Metadata Viewer

A user-friendly Streamlit application for extracting, viewing, and editing metadata from PDF documents.

## Features

- 📄 Extract metadata from PDF files
- ✅ Select specific metadata fields to display
- ✏️ Edit metadata fields with guided format hints
- 💾 Download updated PDF with modified metadata
- 🕒 Automatic date formatting with EST timezone conversion
- 🎨 Modern, intuitive UI with custom styling
- 📊 File validation and size limits
- 🔍 Detailed logging for troubleshooting

## Installation

1. Install required dependencies:
```bash
pip install streamlit pikepdf pytz
```

## Usage

Run the application:
```bash
streamlit run pdf_meta.py
```

Then:
1. Upload your PDF file (max 10MB)
2. Select the metadata fields you want to view
3. Click Submit to display the selected metadata
4. (Optional) Select fields to edit and provide new values
5. (Optional) Download the updated PDF with modified metadata

## Supported Metadata Fields

Common PDF metadata fields include:
- `/Title` - Document title
- `/Author` - Document author
- `/Subject` - Document subject
- `/Creator` - Application that created the document
- `/Producer` - PDF producer
- `/CreationDate` - When the document was created
- `/ModDate` - When the document was last modified
- `/Keywords` - Document keywords

## Requirements

- Python 3.7+
- streamlit
- pikepdf
- pytz

## License

MIT License
