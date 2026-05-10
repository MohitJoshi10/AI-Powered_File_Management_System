#!/usr/bin/env python3
"""
SmartFile AI - Final Error-Free Version
Intelligent File Management System with AI-powered search, NLP, and encryption
"""

import os
import sys
import json
import re
import hashlib
import logging
from datetime import datetime
from pathlib import Path

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Flask and web framework
try:
    from flask import Flask, request, jsonify, render_template, send_file
    from flask_cors import CORS
    from werkzeug.utils import secure_filename
    FLASK_AVAILABLE = True
except ImportError as e:
    print(f"❌ Flask not available: {e}")
    FLASK_AVAILABLE = False
    sys.exit(1)

# Core dependencies
try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    print("❌ Cryptography not available")
    CRYPTO_AVAILABLE = False

# Optional dependencies with graceful fallback
ELASTICSEARCH_AVAILABLE = False
SPACY_AVAILABLE = False
PYPDF2_AVAILABLE = False
DOCX_AVAILABLE = False
TESSERACT_AVAILABLE = False
SPEECH_AVAILABLE = False
NLTK_AVAILABLE = False

try:
    from elasticsearch import Elasticsearch
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    print("⚠️ Elasticsearch not available - using local storage")

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    print("⚠️ spaCy not available - using basic text processing")

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    print("⚠️ PyPDF2 not available - PDF processing disabled")

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    print("⚠️ python-docx not available - DOCX processing disabled")

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    print("⚠️ Tesseract not available - OCR disabled")

try:
    import speech_recognition as sr
    from pydub import AudioSegment
    SPEECH_AVAILABLE = True
except ImportError:
    print("⚠️ Speech recognition not available - voice commands disabled")

try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    from collections import Counter
    NLTK_AVAILABLE = True
except ImportError:
    print("⚠️ NLTK not available - using basic text processing")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ENCRYPTED_FOLDER'] = 'encrypted_files'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SECRET_KEY'] = 'smartfile-ai-secret-key-change-in-production'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['ENCRYPTED_FOLDER'], exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smartfile.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize components with error handling
class ComponentManager:
    def __init__(self):
        self.elasticsearch = None
        self.nlp = None
        self.cipher_suite = None
        self.file_storage = {}  # Fallback storage
        self.initialize_components()
    
    def initialize_components(self):
        """Initialize all components with error handling"""
        # Initialize Elasticsearch
        if ELASTICSEARCH_AVAILABLE:
            try:
                self.elasticsearch = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}], 
                                                 timeout=5, max_retries=1, retry_on_timeout=True)
                # Test connection
                if self.elasticsearch.ping():
                    logger.info("✅ Elasticsearch connected successfully")
                    self.create_elasticsearch_index()
                else:
                    logger.warning("⚠️ Elasticsearch connection failed - using local storage")
                    self.elasticsearch = None
            except Exception as e:
                logger.warning(f"⚠️ Elasticsearch initialization failed: {e}")
                self.elasticsearch = None
        else:
            logger.info("📝 Using local file storage")
        
        # Initialize spaCy
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load('en_core_web_sm')
                logger.info("✅ spaCy loaded successfully")
            except OSError:
                try:
                    logger.info("📥 Downloading spaCy model...")
                    os.system("python -m spacy download en_core_web_sm")
                    self.nlp = spacy.load('en_core_web_sm')
                    logger.info("✅ spaCy model downloaded and loaded")
                except Exception as e:
                    logger.warning(f"⚠️ spaCy model download failed: {e}")
                    self.nlp = None
            except Exception as e:
                logger.warning(f"⚠️ spaCy loading failed: {e}")
                self.nlp = None
        
        # Initialize encryption
        if CRYPTO_AVAILABLE:
            try:
                key_file = Path('encryption_key.key')
                if key_file.exists():
                    with open(key_file, 'rb') as f:
                        encryption_key = f.read()
                else:
                    encryption_key = Fernet.generate_key()
                    with open(key_file, 'wb') as f:
                        f.write(encryption_key)
                self.cipher_suite = Fernet(encryption_key)
                logger.info("✅ Encryption initialized successfully")
            except Exception as e:
                logger.error(f"❌ Encryption initialization failed: {e}")
                self.cipher_suite = None
        else:
            logger.error("❌ Cryptography not available - encryption disabled")
    
    def create_elasticsearch_index(self):
        """Create Elasticsearch index with error handling"""
        if not self.elasticsearch:
            return False
        
        try:
            index_mapping = {
                "mappings": {
                    "properties": {
                        "filename": {"type": "text"},
                        "file_path": {"type": "keyword"},
                        "file_type": {"type": "keyword"},
                        "content": {"type": "text"},
                        "keywords": {"type": "keyword"},
                        "entities": {"type": "object"},
                        "category": {"type": "keyword"},
                        "summary": {"type": "text"},
                        "indexed_date": {"type": "date"},
                        "file_size": {"type": "long"},
                        "is_encrypted": {"type": "boolean"}
                    }
                }
            }
            
            if not self.elasticsearch.indices.exists(index="files"):
                self.elasticsearch.indices.create(index="files", body=index_mapping)
                logger.info("✅ Elasticsearch index created")
            return True
        except Exception as e:
            logger.error(f"❌ Elasticsearch index creation failed: {e}")
            return False

# Initialize component manager
components = ComponentManager()

class FileProcessor:
    """Robust file processing with fallbacks"""
    
    def __init__(self):
        self.supported_formats = {
            'pdf': self.extract_pdf_text if PYPDF2_AVAILABLE else self.fallback_extraction,
            'docx': self.extract_docx_text if DOCX_AVAILABLE else self.fallback_extraction,
            'txt': self.extract_txt_text,
            'jpg': self.extract_image_text if TESSERACT_AVAILABLE else self.fallback_extraction,
            'jpeg': self.extract_image_text if TESSERACT_AVAILABLE else self.fallback_extraction,
            'png': self.extract_image_text if TESSERACT_AVAILABLE else self.fallback_extraction,
            'mp3': self.extract_audio_text if SPEECH_AVAILABLE else self.fallback_extraction,
            'wav': self.extract_audio_text if SPEECH_AVAILABLE else self.fallback_extraction,
            'm4a': self.extract_audio_text if SPEECH_AVAILABLE else self.fallback_extraction
        }
    
    def fallback_extraction(self, file_path):
        """Fallback when specific extraction is not available"""
        file_type = Path(file_path).suffix.lower()
        return f"Text extraction not available for {file_type} files. Please install required dependencies."
    
    def extract_pdf_text(self, file_path):
        """Extract text from PDF files"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            logger.error(f"❌ PDF extraction failed: {e}")
            return self.fallback_extraction(file_path)
    
    def extract_docx_text(self, file_path):
        """Extract text from DOCX files"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"❌ DOCX extraction failed: {e}")
            return self.fallback_extraction(file_path)
    
    def extract_txt_text(self, file_path):
        """Extract text from TXT files"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()
        except Exception as e:
            logger.error(f"❌ TXT extraction failed: {e}")
            return self.fallback_extraction(file_path)
    
    def extract_image_text(self, file_path):
        """Extract text from images using OCR"""
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            logger.error(f"❌ Image OCR failed: {e}")
            return self.fallback_extraction(file_path)
    
    def extract_audio_text(self, file_path):
        """Extract text from audio files using speech recognition"""
        try:
            # Suppress FFmpeg warnings
            import warnings
            warnings.filterwarnings("ignore", message="Couldn't find ffmpeg")
            
            audio = AudioSegment.from_file(file_path)
            wav_path = file_path.replace(Path(file_path).suffix, '.wav')
            audio.export(wav_path, format="wav", parameters=["-loglevel", "quiet"])
            
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)
            
            # Clean up
            if os.path.exists(wav_path):
                os.remove(wav_path)
            
            return text.strip()
        except Exception as e:
            logger.error(f"❌ Audio extraction failed: {e}")
            return self.fallback_extraction(file_path)
    
    def process_file(self, file_path, file_type):
        """Process file with appropriate extraction method"""
        if file_type in self.supported_formats:
            return self.supported_formats[file_type](file_path)
        return self.fallback_extraction(file_path)

class NLPProcessor:
    """Natural Language Processing with fallbacks"""
    
    def __init__(self):
        self.nlp = components.nlp
        self.stop_words = set()
        if NLTK_AVAILABLE:
            try:
                from nltk.corpus import stopwords
                self.stop_words = set(stopwords.words('english'))
            except:
                pass  # Use empty stop words set
    
    def extract_keywords(self, text, max_keywords=20):
        """Extract keywords from text"""
        if not text:
            return []
        
        try:
            if self.nlp and SPACY_AVAILABLE:
                doc = self.nlp(text)
                keywords = []
                
                # Extract named entities
                for ent in doc.ents:
                    keywords.append(ent.text.lower())
                
                # Extract important nouns and adjectives
                for token in doc:
                    if (token.pos_ in ['NOUN', 'ADJ'] and 
                        not token.is_stop and 
                        not token.is_punct and 
                        len(token.text) > 2):
                        keywords.append(token.lemma_.lower())
                
                # Remove duplicates and return top keywords
                keyword_freq = Counter(keywords)
                return [kw for kw, freq in keyword_freq.most_common(max_keywords)]
            else:
                # Fallback: simple word frequency
                words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
                word_freq = Counter(words)
                return [word for word, freq in word_freq.most_common(max_keywords)]
        except Exception as e:
            logger.error(f"❌ Keyword extraction failed: {e}")
            return []
    
    def extract_entities(self, text):
        """Extract named entities from text"""
        if not text or not self.nlp or not SPACY_AVAILABLE:
            return {}
        
        try:
            doc = self.nlp(text)
            entities = {}
            for ent in doc.ents:
                if ent.label_ not in entities:
                    entities[ent.label_] = []
                entities[ent.label_].append(ent.text)
            return entities
        except Exception as e:
            logger.error(f"❌ Entity extraction failed: {e}")
            return {}
    
    def categorize_document(self, text, keywords):
        """Categorize document based on content"""
        categories = {
            'business': ['business', 'company', 'corporate', 'meeting', 'project', 'report'],
            'academic': ['research', 'study', 'university', 'paper', 'academic', 'education'],
            'legal': ['legal', 'law', 'court', 'contract', 'agreement', 'attorney'],
            'medical': ['medical', 'health', 'patient', 'treatment', 'diagnosis', 'hospital'],
            'technical': ['technical', 'engineering', 'software', 'development', 'code', 'system'],
            'financial': ['financial', 'money', 'budget', 'cost', 'investment', 'revenue']
        }
        
        category_scores = {}
        for category, category_keywords in categories.items():
            score = 0
            for kw in keywords:
                if kw in category_keywords:
                    score += 1
            category_scores[category] = score
        
        # Return category with highest score
        if max(category_scores.values()) > 0:
            return max(category_scores, key=category_scores.get)
        else:
            return 'general'
    
    def generate_summary(self, text, max_sentences=3):
        """Generate text summary"""
        if not text:
            return ""
        
        try:
            if NLTK_AVAILABLE and len(text) > 100:
                sentences = sent_tokenize(text)
                if len(sentences) <= max_sentences:
                    return text
                
                # Simple extractive summarization
                sentence_scores = {}
                words = word_tokenize(text.lower())
                word_freq = Counter(word for word in words if word.isalnum() and word not in self.stop_words)
                
                for sentence in sentences:
                    sentence_words = word_tokenize(sentence.lower())
                    score = sum(word_freq.get(word, 0) for word in sentence_words if word.isalnum())
                    sentence_scores[sentence] = score / len(sentence_words) if len(sentence_words) > 0 else 0
                
                # Get top sentences
                top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:max_sentences]
                summary = ' '.join([sentence for sentence, score in top_sentences])
                return summary
            else:
                # Fallback: return first few sentences
                sentences = text.split('. ')
                if len(sentences) <= max_sentences:
                    return text
                return '. '.join(sentences[:max_sentences]) + '.'
        except Exception as e:
            logger.error(f"❌ Summary generation failed: {e}")
            return text[:300] + "..." if len(text) > 300 else text
    
    def generate_snippet(self, text, query, context_length=150):
        """Generate search snippet with context"""
        if not text or not query:
            return text[:context_length] + "..." if len(text) > context_length else text
        
        try:
            query_lower = query.lower()
            text_lower = text.lower()
            
            # Find the first occurrence of the query
            index = text_lower.find(query_lower)
            if index == -1:
                # Try word-based matching
                query_words = query.lower().split()
                for word in query_words:
                    if len(word) > 2:
                        index = text_lower.find(word)
                        if index != -1:
                            break
            
            if index == -1:
                return text[:context_length] + "..." if len(text) > context_length else text
            
            # Extract context around the match
            start = max(0, index - context_length // 2)
            end = min(len(text), index + len(query) + context_length // 2)
            
            snippet = text[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(text):
                snippet = snippet + "..."
            
            return snippet
        except Exception as e:
            logger.error(f"❌ Snippet generation failed: {e}")
            return text[:context_length] + "..." if len(text) > context_length else text

class EncryptionManager:
    """File encryption and decryption"""
    
    def __init__(self):
        self.cipher_suite = components.cipher_suite
    
    def encrypt_file(self, file_path):
        """Encrypt a file"""
        if not self.cipher_suite:
            return None
        
        try:
            with open(file_path, 'rb') as file:
                file_data = file.read()
            
            encrypted_data = self.cipher_suite.encrypt(file_data)
            
            encrypted_filename = secure_filename(os.path.basename(file_path)) + '.encrypted'
            encrypted_path = os.path.join(app.config['ENCRYPTED_FOLDER'], encrypted_filename)
            
            with open(encrypted_path, 'wb') as encrypted_file:
                encrypted_file.write(encrypted_data)
            
            return encrypted_path
        except Exception as e:
            logger.error(f"❌ File encryption failed: {e}")
            return None
    
    def decrypt_file(self, encrypted_path, output_path):
        """Decrypt a file"""
        if not self.cipher_suite:
            return None
        
        try:
            with open(encrypted_path, 'rb') as encrypted_file:
                encrypted_data = encrypted_file.read()
            
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            
            with open(output_path, 'wb') as decrypted_file:
                decrypted_file.write(decrypted_data)
            
            return output_path
        except Exception as e:
            logger.error(f"❌ File decryption failed: {e}")
            return None

# Initialize processors
file_processor = FileProcessor()
nlp_processor = NLPProcessor()
encryption_manager = EncryptionManager()

# Utility functions
def fix_backslashes(path):
    """Fix backslash issues in file paths"""
    if not path:
        return path
    return path.replace('\\', '/')

def escape_backslashes(path):
    """Escape backslashes for JSON serialization"""
    if not path:
        return path
    return path.replace('\\', '\\\\')

def store_file_document(doc):
    """Store file document in appropriate storage"""
    try:
        if components.elasticsearch:
            # Store in Elasticsearch
            file_id = hashlib.md5(doc['file_path'].encode()).hexdigest()
            components.elasticsearch.index(index="files", id=file_id, body=doc)
        else:
            # Store in local memory
            file_id = hashlib.md5(doc['file_path'].encode()).hexdigest()
            components.file_storage[file_id] = doc
        return True
    except Exception as e:
        logger.error(f"❌ Document storage failed: {e}")
        return False

def search_documents(query):
    """Search documents in appropriate storage"""
    try:
        if components.elasticsearch:
            # Search in Elasticsearch
            search_body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["content^2", "filename", "keywords", "summary"],
                        "fuzziness": "AUTO"
                    }
                },
                "highlight": {
                    "fields": {
                        "content": {},
                        "summary": {}
                    }
                }
            }
            
            response = components.elasticsearch.search(index="files", body=search_body)
            hits = response['hits']['hits']
            
            results = []
            for hit in hits:
                source = hit['_source']
                highlights = hit.get('highlight', {})
                
                snippet = ""
                if 'content' in highlights:
                    snippet = ' '.join(highlights['content'])
                else:
                    snippet = nlp_processor.generate_snippet(source.get('content', ''), query)
                
                result = {
                    'filename': source['filename'],
                    'file_path': source['file_path'],
                    'file_type': source['file_type'],
                    'category': source['category'],
                    'summary': source['summary'],
                    'keywords': source['keywords'][:10],
                    'snippet': snippet,
                    'score': hit['_score'],
                    'file_size': source['file_size'],
                    'is_encrypted': source['is_encrypted']
                }
                results.append(result)
            
            return results
        else:
            # Search in local storage
            results = []
            query_lower = query.lower()
            
            for file_id, doc in components.file_storage.items():
                content = doc.get('content', '').lower()
                filename = doc.get('filename', '').lower()
                keywords = [kw.lower() for kw in doc.get('keywords', [])]
                
                # Simple matching
                if (query_lower in content or 
                    query_lower in filename or 
                    any(query_lower in kw for kw in keywords)):
                    
                    snippet = nlp_processor.generate_snippet(doc.get('content', ''), query)
                    
                    result = {
                        'filename': doc['filename'],
                        'file_path': doc['file_path'],
                        'file_type': doc['file_type'],
                        'category': doc['category'],
                        'summary': doc['summary'],
                        'keywords': doc['keywords'][:10],
                        'snippet': snippet,
                        'score': 1.0,
                        'file_size': doc['file_size'],
                        'is_encrypted': doc['is_encrypted']
                    }
                    results.append(result)
            
            return results
    except Exception as e:
        logger.error(f"❌ Document search failed: {e}")
        return []

# Flask Routes
@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status"""
    status = {
        'elasticsearch': ELASTICSEARCH_AVAILABLE and components.elasticsearch is not None,
        'spacy': SPACY_AVAILABLE and components.nlp is not None,
        'pyPDF2': PYPDF2_AVAILABLE,
        'docx': DOCX_AVAILABLE,
        'tesseract': TESSERACT_AVAILABLE,
        'speech': SPEECH_AVAILABLE,
        'nltk': NLTK_AVAILABLE,
        'cryptography': CRYPTO_AVAILABLE,
        'total_files': len(components.file_storage) if not components.elasticsearch else "Elasticsearch",
        'storage_type': "Elasticsearch" if components.elasticsearch else "Local Storage"
    }
    return jsonify(status)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload and process files"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Extract text content
            file_type = filename.split('.')[-1].lower()
            content = file_processor.process_file(file_path, file_type)
            
            # Process with NLP
            keywords = nlp_processor.extract_keywords(content)
            entities = nlp_processor.extract_entities(content)
            category = nlp_processor.categorize_document(content, keywords)
            summary = nlp_processor.generate_summary(content)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Create document
            doc = {
                'filename': filename,
                'file_path': fix_backslashes(file_path),
                'file_type': file_type,
                'content': content,
                'keywords': keywords,
                'entities': entities,
                'category': category,
                'summary': summary,
                'indexed_date': datetime.now().isoformat(),
                'file_size': file_size,
                'is_encrypted': False
            }
            
            # Store document
            if store_file_document(doc):
                return jsonify({
                    'message': 'File uploaded and indexed successfully',
                    'filename': filename,
                    'keywords': keywords[:10],
                    'category': category,
                    'summary': summary[:200] + '...' if len(summary) > 200 else summary
                })
            else:
                return jsonify({'error': 'Failed to store file document'}), 500
    
    except Exception as e:
        logger.error(f"❌ File upload failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search_files():
    """Search files"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        results = search_documents(query)
        
        return jsonify({
            'results': results,
            'total': len(results),
            'query': query
        })
    
    except Exception as e:
        logger.error(f"❌ File search failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice_command', methods=['POST'])
def voice_command():
    """Process voice commands"""
    try:
        if not SPEECH_AVAILABLE:
            return jsonify({'error': 'Speech recognition not available. Please install SpeechRecognition and pydub.'}), 400
        
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No audio file selected'}), 400
        
        # Save temporary audio file
        temp_audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_voice.wav')
        audio_file.save(temp_audio_path)
        
        # Convert to speech text
        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_audio_path) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data)
            except sr.UnknownValueError:
                return jsonify({'error': 'Could not understand audio'}), 400
            except sr.RequestError as e:
                return jsonify({'error': f'Speech recognition error: {e}'}), 500
        
        # Clean up temporary file
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        
        # Process the voice command as a search query
        results = search_documents(text)
        
        return jsonify({
            'command': text,
            'results': results,
            'total': len(results)
        })
    
    except Exception as e:
        logger.error(f"❌ Voice command failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/open_file', methods=['POST'])
def open_file():
    """Open files securely"""
    try:
        data = request.get_json()
        file_path = data.get('file_path', '')
        
        if not file_path:
            return jsonify({'error': 'No file path provided'}), 400
        
        # Fix backslashes for Windows paths
        fixed_path = file_path.replace('/', '\\')
        
        if not os.path.exists(fixed_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Check if file is encrypted
        if file_path.endswith('.encrypted'):
            # Decrypt file temporarily
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_decrypted')
            decrypted_path = encryption_manager.decrypt_file(file_path, temp_path)
            
            if decrypted_path:
                # Open the decrypted file
                os.startfile(decrypted_path)
                return jsonify({'message': 'Encrypted file opened successfully'})
            else:
                return jsonify({'error': 'Failed to decrypt file'}), 500
        else:
            # Open regular file
            os.startfile(fixed_path)
            return jsonify({'message': 'File opened successfully'})
    
    except Exception as e:
        logger.error(f"❌ File open failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/encrypt_file', methods=['POST'])
def encrypt_file_endpoint():
    """Encrypt files"""
    try:
        data = request.get_json()
        file_path = data.get('file_path', '')
        
        if not file_path:
            return jsonify({'error': 'No file path provided'}), 400
        
        # Fix backslashes for Windows paths
        fixed_path = file_path.replace('/', '\\')
        
        if not os.path.exists(fixed_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Encrypt the file
        encrypted_path = encryption_manager.encrypt_file(fixed_path)
        
        if encrypted_path:
            # Update storage record
            file_id = hashlib.md5(fixed_path.encode()).hexdigest()
            
            if components.elasticsearch:
                try:
                    components.elasticsearch.update(
                        index="files",
                        id=file_id,
                        body={"doc": {"is_encrypted": True, "encrypted_path": encrypted_path}}
                    )
                except:
                    pass  # Fallback to local storage update
            else:
                # Update local storage
                if file_id in components.file_storage:
                    components.file_storage[file_id]['is_encrypted'] = True
                    components.file_storage[file_id]['encrypted_path'] = encrypted_path
            
            return jsonify({
                'message': 'File encrypted successfully',
                'encrypted_path': encrypted_path
            })
        else:
            return jsonify({'error': 'Failed to encrypt file'}), 500
    
    except Exception as e:
        logger.error(f"❌ File encryption failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_categories', methods=['GET'])
def get_categories():
    """Get available categories"""
    try:
        categories = []
        
        if components.elasticsearch:
            # Get categories from Elasticsearch
            try:
                search_body = {
                    "size": 0,
                    "aggs": {
                        "categories": {
                            "terms": {
                                "field": "category"
                            }
                        }
                    }
                }
                
                response = components.elasticsearch.search(index="files", body=search_body)
                categories = [bucket['key'] for bucket in response['aggregations']['categories']['buckets']]
            except:
                pass  # Fallback to local storage
        
        # Fallback to local storage
        if not categories:
            categories_set = set()
            for doc in components.file_storage.values():
                categories_set.add(doc.get('category', 'general'))
            categories = list(categories_set)
        
        return jsonify({'categories': categories})
    
    except Exception as e:
        logger.error(f"❌ Get categories failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_stats', methods=['GET'])
def get_stats():
    """Get file statistics"""
    try:
        stats = {
            'total_files': 0,
            'file_types': {},
            'categories': {}
        }
        
        if components.elasticsearch:
            # Get statistics from Elasticsearch
            try:
                search_body = {
                    "size": 0,
                    "aggs": {
                        "total_files": {
                            "value_count": {
                                "field": "filename"
                            }
                        },
                        "file_types": {
                            "terms": {
                                "field": "file_type"
                            }
                        },
                        "categories": {
                            "terms": {
                                "field": "category"
                            }
                        }
                    }
                }
                
                response = components.elasticsearch.search(index="files", body=search_body)
                
                stats = {
                    'total_files': response['aggregations']['total_files']['value'],
                    'file_types': dict([(bucket['key'], bucket['doc_count']) 
                                       for bucket in response['aggregations']['file_types']['buckets']]),
                    'categories': dict([(bucket['key'], bucket['doc_count']) 
                                      for bucket in response['aggregations']['categories']['buckets']])
                }
            except:
                pass  # Fallback to local storage
        
        # Fallback to local storage
        if stats['total_files'] == 0:
            stats['total_files'] = len(components.file_storage)
            
            file_types = {}
            categories = {}
            for doc in components.file_storage.values():
                file_type = doc.get('file_type', 'unknown')
                category = doc.get('category', 'general')
                
                file_types[file_type] = file_types.get(file_type, 0) + 1
                categories[category] = categories.get(category, 0) + 1
            
            stats['file_types'] = file_types
            stats['categories'] = categories
        
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"❌ Get stats failed: {e}")
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({'error': 'File too large'}), 413

# Main execution
if __name__ == '__main__':
    print("🚀 Starting SmartFile AI - Final Version")
    print("=" * 60)
    print("📊 System Status:")
    print(f"  Elasticsearch: {'✅' if ELASTICSEARCH_AVAILABLE and components.elasticsearch else '❌'}")
    print(f"  spaCy NLP: {'✅' if SPACY_AVAILABLE and components.nlp else '❌'}")
    print(f"  PDF Support: {'✅' if PYPDF2_AVAILABLE else '❌'}")
    print(f"  DOCX Support: {'✅' if DOCX_AVAILABLE else '❌'}")
    print(f"  OCR Support: {'✅' if TESSERACT_AVAILABLE else '❌'}")
    print(f"  Speech Recognition: {'✅' if SPEECH_AVAILABLE else '❌'}")
    print(f"  NLTK Processing: {'✅' if NLTK_AVAILABLE else '❌'}")
    print(f"  Encryption: {'✅' if CRYPTO_AVAILABLE else '❌'}")
    print(f"  Storage: {'Elasticsearch' if components.elasticsearch else 'Local Storage'}")
    print("=" * 60)
    print("🌐 Application will be available at: http://localhost:5000")
    print("📝 Logs are being written to: smartfile.log")
    print("🔧 Use Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n👋 SmartFile AI stopped by user")
    except Exception as e:
        print(f"\n❌ Application failed to start: {e}")
        sys.exit(1)
