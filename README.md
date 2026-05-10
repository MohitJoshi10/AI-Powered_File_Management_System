# SmartFile AI - Intelligent File Management System

SmartFile AI is an intelligent file management system that leverages AI to optimize local file retrieval, organization, and security. By combining NLP (spaCy), search (Elasticsearch), and encryption techniques, it allows users to search files using natural language, automatically categorizes documents, offers voice-command interaction, and ensures data security.

## Features

### 🔍 **AI-Powered Search**
- Natural language search across all file types
- Intelligent keyword and entity extraction
- Fuzzy search capabilities with Elasticsearch
- Search result highlighting and snippets

### 📁 **Multi-Format Support**
- **Text Files**: PDF, DOCX, TXT
- **Images**: JPG, JPEG, PNG (with OCR)
- **Audio**: MP3, WAV, M4A (with speech-to-text)

### 🎯 **Smart Categorization**
- Automatic document categorization using NLP
- Categories: Business, Academic, Legal, Medical, Technical, Financial
- Keyword extraction and tagging

### 🔒 **Security & Encryption**
- End-to-end encryption using Fernet
- Secure file storage and access
- Encryption/decryption on-demand

### 🎤 **Voice Interaction**
- Voice command support for file search
- Speech-to-text integration
- Real-time voice recognition

### 🎨 **Modern UI/UX**
- Responsive web interface
- Animated components and smooth transitions
- Real-time search results
- File preview and management

## Architecture

### Backend
- **Flask**: Web framework and API server
- **Elasticsearch**: Search and indexing engine
- **spaCy**: Natural language processing
- **NLTK**: Text processing and tokenization
- **Cryptography**: File encryption (Fernet)
- **Tesseract**: OCR for images
- **SpeechRecognition**: Voice command processing

### Frontend
- **HTML5/CSS3**: Modern responsive design
- **JavaScript (ES6+)**: Interactive functionality
- **Bootstrap 5**: UI framework
- **Font Awesome**: Icons and visual elements
- **jQuery**: DOM manipulation and AJAX

## Installation

### Prerequisites
- Python 3.8+
- Elasticsearch 8.x
- Tesseract OCR
- FFmpeg (for audio processing)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd SmartFile-AI
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Download spaCy Model
```bash
python -m spacy download en_core_web_sm
```

### 4. Install Elasticsearch
```bash
# For Windows
# Download and install from https://www.elastic.co/downloads/elasticsearch

# For macOS (using Homebrew)
brew tap elastic/tap
brew install elastic/tap/elasticsearch-full

# For Ubuntu/Debian
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.10.0-linux-x86_64.tar.gz
tar -xzf elasticsearch-8.10.0-linux-x86_64.tar.gz
cd elasticsearch-8.10.0/
./bin/elasticsearch
```

### 5. Install Tesseract OCR
```bash
# For Windows
# Download from https://github.com/UB-Mannheim/tesseract/wiki

# For macOS
brew install tesseract

# For Ubuntu/Debian
sudo apt-get install tesseract-ocr
```

### 6. Install FFmpeg
```bash
# For Windows
# Download from https://ffmpeg.org/download.html

# For macOS
brew install ffmpeg

# For Ubuntu/Debian
sudo apt-get install ffmpeg
```

## Usage

### 1. Start Elasticsearch
```bash
# Navigate to Elasticsearch directory
cd elasticsearch-8.10.0/
./bin/elasticsearch
```

### 2. Run the Flask Application
```bash
python app.py
```

### 3. Access the Web Interface
Open your browser and navigate to: `http://localhost:5000`

## API Endpoints

### File Operations
- `POST /api/upload` - Upload and index files
- `POST /api/search` - Search files using natural language
- `POST /api/open_file` - Open a file securely
- `POST /api/encrypt_file` - Encrypt a file

### Voice Commands
- `POST /api/voice_command` - Process voice search commands

### Data & Analytics
- `GET /api/get_stats` - Get file statistics
- `GET /api/get_categories` - Get available categories

## File Processing Pipeline

1. **Upload**: Files are uploaded through the web interface
2. **Text Extraction**: Content is extracted based on file type
   - PDF/DOCX/TXT: Direct text extraction
   - Images: OCR processing with Tesseract
   - Audio: Speech-to-text conversion
3. **NLP Processing**: 
   - Keyword extraction
   - Named entity recognition
   - Document categorization
   - Summary generation
4. **Indexing**: Content is indexed in Elasticsearch
5. **Search**: Natural language queries are processed and matched

## Security Features

### Encryption
- Files are encrypted using Fernet symmetric encryption
- Encryption keys are stored securely
- Encrypted files can be decrypted on-demand

### Path Handling
- Backslash path issues are resolved for Windows compatibility
- Secure file path handling prevents directory traversal

## Configuration

### Environment Variables
```bash
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Elasticsearch Configuration
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200

# File Upload Configuration
MAX_CONTENT_LENGTH=16777216  # 16MB
UPLOAD_FOLDER=uploads
ENCRYPTED_FOLDER=encrypted_files
```

## Troubleshooting

### Common Issues

1. **Elasticsearch Connection Error**
   - Ensure Elasticsearch is running on localhost:9200
   - Check firewall settings

2. **Tesseract OCR Not Found**
   - Install Tesseract OCR and add to PATH
   - Verify installation with `tesseract --version`

3. **Audio Processing Issues**
   - Install FFmpeg for audio format conversion
   - Check audio file formats are supported

4. **SpaCy Model Missing**
   - Run `python -m spacy download en_core_web_sm`
   - Verify model installation

### Debug Mode
Enable debug mode for detailed error logging:
```bash
export FLASK_ENV=development
python app.py
```

## Project Structure
```
SmartFile-AI/
├── app.py                 # Main Flask application
├── requirements.txt        # Python dependencies
├── README.md             # Project documentation
├── encryption_key.key    # Encryption key (auto-generated)
├── templates/
│   └── index.html        # Main web interface
├── static/
│   ├── css/
│   │   └── style.css     # Custom styles
│   ├── js/
│   │   └── app.js        # Frontend JavaScript
│   └── images/           # Static images
├── uploads/              # Temporary file uploads
└── encrypted_files/      # Encrypted file storage
```

## Performance Considerations

### Optimization Tips
1. **Elasticsearch**: Configure appropriate memory settings
2. **File Processing**: Implement batch processing for large files
3. **Caching**: Add Redis for frequently accessed data
4. **Database**: Consider PostgreSQL for metadata storage

### Scalability
- Horizontal scaling with multiple Elasticsearch nodes
- Load balancing for Flask application
- Distributed file storage (S3, etc.)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Team

- **Sujal**: Search bar + Flask API, File indexing with OCR & NLP, Snippet generation
- **Kuldeep**: Keyword/entity extraction & categorization
- **Mohit**: Encryption logic + secure open support
- **Anshul**: Frontend redesign, Voice interaction integration

## Version History

### v1.0.0 (Current)
- ✅ AI-powered search with Elastic
- ✅ Voice command file interaction
- ✅ Auto categorization using NLP
- ✅ Highlighted search snippets and summaries
- ✅ End-to-end encryption support
- ✅ Responsive UI with animated navbar & sections
- ✅ Fully working file open and folder explorer feature

## Support

For support and questions, please open an issue on the GitHub repository or contact the development team.
