from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import os
import json
import re
from werkzeug.utils import secure_filename
import logging
from datetime import datetime
import base64
from cryptography.fernet import Fernet
import hashlib

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ENCRYPTED_FOLDER'] = 'encrypted_files'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SECRET_KEY'] = 'your-secret-key-change-this'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['ENCRYPTED_FOLDER'], exist_ok=True)

# Initialize Elasticsearch (with fallback)
try:
    from elasticsearch import Elasticsearch
    es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])
    ELASTICSEARCH_AVAILABLE = True
    print("✅ Elasticsearch connected successfully")
except Exception as e:
    print(f"⚠️ Elasticsearch not available: {e}")
    es = None
    ELASTICSEARCH_AVAILABLE = False

# Initialize NLP (with fallback)
try:
    import spacy
    nlp = spacy.load('en_core_web_sm')
    SPACY_AVAILABLE = True
    print("✅ spaCy loaded successfully")
except Exception as e:
    print(f"⚠️ spaCy not available: {e}")
    nlp = None
    SPACY_AVAILABLE = False

# Initialize other dependencies (with fallback)
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    print("⚠️ PyPDF2 not available")
    PYPDF2_AVAILABLE = False

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    print("⚠️ python-docx not available")
    DOCX_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    print("⚠️ Tesseract not available")
    TESSERACT_AVAILABLE = False

try:
    import speech_recognition as sr
    from pydub import AudioSegment
    SPEECH_AVAILABLE = True
except ImportError:
    print("⚠️ Speech recognition not available")
    SPEECH_AVAILABLE = False

try:
    import nltk
    from nltk.tokenize import sent_tokenize
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    from collections import Counter
    NLTK_AVAILABLE = True
except ImportError:
    print("⚠️ NLTK not available")
    NLTK_AVAILABLE = False

# Initialize encryption key
try:
    with open('encryption_key.key', 'rb') as key_file:
        encryption_key = key_file.read()
except FileNotFoundError:
    encryption_key = Fernet.generate_key()
    with open('encryption_key.key', 'wb') as key_file:
        key_file.write(encryption_key)

cipher_suite = Fernet(encryption_key)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple file storage for demo (when Elasticsearch is not available)
file_storage = {}

class FileProcessor:
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
        return f"Text extraction not available for {file_path}. Please install required dependencies."
    
    def extract_pdf_text(self, file_path):
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return ""
    
    def extract_docx_text(self, file_path):
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {e}")
            return ""
    
    def extract_txt_text(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error extracting TXT text: {e}")
            return ""
    
    def extract_image_text(self, file_path):
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            logger.error(f"Error extracting image text: {e}")
            return ""
    
    def extract_audio_text(self, file_path):
        try:
            # Convert audio to WAV format for speech recognition
            audio = AudioSegment.from_file(file_path)
            wav_path = file_path.replace(file_path.split('.')[-1], 'wav')
            audio.export(wav_path, format="wav")
            
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)
            
            # Clean up temporary WAV file
            if os.path.exists(wav_path):
                os.remove(wav_path)
            
            return text
        except Exception as e:
            logger.error(f"Error extracting audio text: {e}")
            return ""
    
    def process_file(self, file_path, file_type):
        if file_type in self.supported_formats:
            return self.supported_formats[file_type](file_path)
        return self.fallback_extraction(file_path)

class NLPProcessor:
    def __init__(self):
        self.nlp = nlp
        self.stop_words = set(stopwords.words('english')) if NLTK_AVAILABLE else set()
    
    def extract_keywords(self, text):
        if not SPACY_AVAILABLE or not self.nlp:
            # Simple keyword extraction without spaCy
            words = text.lower().split()
            keywords = [word for word in words if len(word) > 3 and word.isalnum()]
            return list(set(keywords[:20]))
        
        try:
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
            return [kw for kw, freq in keyword_freq.most_common(20)]
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
    
    def extract_entities(self, text):
        if not SPACY_AVAILABLE or not self.nlp:
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
            logger.error(f"Error extracting entities: {e}")
            return {}
    
    def categorize_document(self, text, keywords):
        # Simple categorization based on keywords
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
        if not NLTK_AVAILABLE:
            # Simple summary without NLTK
            sentences = text.split('. ')
            if len(sentences) <= max_sentences:
                return text
            return '. '.join(sentences[:max_sentences])
        
        try:
            sentences = sent_tokenize(text)
            if len(sentences) <= max_sentences:
                return text
            
            # Simple extractive summarization
            sentence_scores = {}
            word_freq = Counter(word.lower() for word in word_tokenize(text) 
                              if word.lower() not in self.stop_words and word.isalnum())
            
            for sentence in sentences:
                words = word_tokenize(sentence.lower())
                score = 0
                for word in words:
                    if word in word_freq:
                        score += word_freq[word]
                sentence_scores[sentence] = score / len(words) if len(words) > 0 else 0
            
            # Get top sentences
            top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:max_sentences]
            summary = ' '.join([sentence for sentence, score in top_sentences])
            
            return summary
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return text[:500] + "..." if len(text) > 500 else text
    
    def generate_snippet(self, text, query, context_length=100):
        query_lower = query.lower()
        text_lower = text.lower()
        
        # Find the first occurrence of the query
        index = text_lower.find(query_lower)
        if index == -1:
            # If exact match not found, try word-based matching
            query_words = query.lower().split()
            for word in query_words:
                index = text_lower.find(word)
                if index != -1:
                    break
        
        if index == -1:
            # Return first part of text if no match found
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

class EncryptionManager:
    def __init__(self):
        self.cipher_suite = cipher_suite
    
    def encrypt_file(self, file_path):
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
            logger.error(f"Error encrypting file: {e}")
            return None
    
    def decrypt_file(self, encrypted_path, output_path):
        try:
            with open(encrypted_path, 'rb') as encrypted_file:
                encrypted_data = encrypted_file.read()
            
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            
            with open(output_path, 'wb') as decrypted_file:
                decrypted_file.write(decrypted_data)
            
            return output_path
        except Exception as e:
            logger.error(f"Error decrypting file: {e}")
            return None

# Initialize processors
file_processor = FileProcessor()
nlp_processor = NLPProcessor()
encryption_manager = EncryptionManager()

def fix_backslashes(path):
    """Fix backslash issues in file paths for JSON/JavaScript compatibility"""
    if not path:
        return path
    return path.replace('\\', '/')

def escape_backslashes(path):
    """Escape backslashes for JSON serialization"""
    if not path:
        return path
    return path.replace('\\', '\\\\')

def create_elasticsearch_index():
    """Create Elasticsearch index if it doesn't exist"""
    if not ELASTICSEARCH_AVAILABLE:
        return False
    
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
    
    try:
        if not es.indices.exists(index="files"):
            es.indices.create(index="files", body=index_mapping)
            logger.info("Created Elasticsearch index 'files'")
        return True
    except Exception as e:
        logger.error(f"Error creating Elasticsearch index: {e}")
        return False

# Initialize Elasticsearch index
if ELASTICSEARCH_AVAILABLE:
    create_elasticsearch_index()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
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
            
            # Store in Elasticsearch or local storage
            doc = {
                'filename': filename,
                'file_path': fix_backslashes(file_path),
                'file_type': file_type,
                'content': content,
                'keywords': keywords,
                'entities': entities,
                'category': category,
                'summary': summary,
                'indexed_date': datetime.now(),
                'file_size': file_size,
                'is_encrypted': False
            }
            
            if ELASTICSEARCH_AVAILABLE:
                es.index(index="files", body=doc)
            else:
                # Store in local storage
                file_id = hashlib.md5(file_path.encode()).hexdigest()
                file_storage[file_id] = doc
            
            return jsonify({
                'message': 'File uploaded and indexed successfully',
                'filename': filename,
                'keywords': keywords[:10],
                'category': category,
                'summary': summary[:200] + '...' if len(summary) > 200 else summary
            })
    
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search_files():
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        results = []
        
        if ELASTICSEARCH_AVAILABLE:
            # Elasticsearch search query
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
            
            response = es.search(index="files", body=search_body)
            hits = response['hits']['hits']
            
            for hit in hits:
                source = hit['_source']
                score = hit['_score']
                highlights = hit.get('highlight', {})
                
                # Generate snippet if no highlights available
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
                    'score': score,
                    'file_size': source['file_size'],
                    'is_encrypted': source['is_encrypted']
                }
                
                results.append(result)
        else:
            # Simple local search
            query_lower = query.lower()
            for file_id, doc in file_storage.items():
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
        
        return jsonify({
            'results': results,
            'total': len(results),
            'query': query
        })
    
    except Exception as e:
        logger.error(f"Error searching files: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice_command', methods=['POST'])
def voice_command():
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
        search_data = {'query': text}
        return search_files()
    
    except Exception as e:
        logger.error(f"Error processing voice command: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/open_file', methods=['POST'])
def open_file():
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
        logger.error(f"Error opening file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/encrypt_file', methods=['POST'])
def encrypt_file_endpoint():
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
            if ELASTICSEARCH_AVAILABLE:
                es.update(
                    index="files",
                    id=hashlib.md5(fixed_path.encode()).hexdigest(),
                    body={"doc": {"is_encrypted": True, "encrypted_path": encrypted_path}}
                )
            else:
                # Update local storage
                for file_id, doc in file_storage.items():
                    if doc['file_path'] == file_path:
                        doc['is_encrypted'] = True
                        doc['encrypted_path'] = encrypted_path
                        break
            
            return jsonify({
                'message': 'File encrypted successfully',
                'encrypted_path': encrypted_path
            })
        else:
            return jsonify({'error': 'Failed to encrypt file'}), 500
    
    except Exception as e:
        logger.error(f"Error encrypting file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_categories', methods=['GET'])
def get_categories():
    try:
        categories = []
        
        if ELASTICSEARCH_AVAILABLE:
            # Get unique categories from Elasticsearch
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
            
            response = es.search(index="files", body=search_body)
            categories = [bucket['key'] for bucket in response['aggregations']['categories']['buckets']]
        else:
            # Get categories from local storage
            categories_set = set()
            for doc in file_storage.values():
                categories_set.add(doc.get('category', 'general'))
            categories = list(categories_set)
        
        return jsonify({'categories': categories})
    
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_stats', methods=['GET'])
def get_stats():
    try:
        stats = {
            'total_files': 0,
            'file_types': {},
            'categories': {}
        }
        
        if ELASTICSEARCH_AVAILABLE:
            # Get statistics from Elasticsearch
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
            
            response = es.search(index="files", body=search_body)
            
            stats = {
                'total_files': response['aggregations']['total_files']['value'],
                'file_types': dict([(bucket['key'], bucket['doc_count']) 
                                   for bucket in response['aggregations']['file_types']['buckets']]),
                'categories': dict([(bucket['key'], bucket['doc_count']) 
                                  for bucket in response['aggregations']['categories']['buckets']])
            }
        else:
            # Get statistics from local storage
            stats['total_files'] = len(file_storage)
            
            file_types = {}
            categories = {}
            for doc in file_storage.values():
                file_type = doc.get('file_type', 'unknown')
                category = doc.get('category', 'general')
                
                file_types[file_type] = file_types.get(file_type, 0) + 1
                categories[category] = categories.get(category, 0) + 1
            
            stats['file_types'] = file_types
            stats['categories'] = categories
        
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status and available features"""
    status = {
        'elasticsearch': ELASTICSEARCH_AVAILABLE,
        'spacy': SPACY_AVAILABLE,
        'pyPDF2': PYPDF2_AVAILABLE,
        'docx': DOCX_AVAILABLE,
        'tesseract': TESSERACT_AVAILABLE,
        'speech': SPEECH_AVAILABLE,
        'nltk': NLTK_AVAILABLE,
        'total_files': len(file_storage) if not ELASTICSEARCH_AVAILABLE else "Elasticsearch"
    }
    return jsonify(status)

if __name__ == '__main__':
    print("🚀 Starting SmartFile AI...")
    print("📊 System Status:")
    print(f"  Elasticsearch: {'✅' if ELASTICSEARCH_AVAILABLE else '❌'}")
    print(f"  spaCy NLP: {'✅' if SPACY_AVAILABLE else '❌'}")
    print(f"  PDF Support: {'✅' if PYPDF2_AVAILABLE else '❌'}")
    print(f"  DOCX Support: {'✅' if DOCX_AVAILABLE else '❌'}")
    print(f"  OCR Support: {'✅' if TESSERACT_AVAILABLE else '❌'}")
    print(f"  Speech Recognition: {'✅' if SPEECH_AVAILABLE else '❌'}")
    print(f"  NLTK Processing: {'✅' if NLTK_AVAILABLE else '❌'}")
    print("\n🌐 Application will be available at: http://localhost:5000")
    print("📝 Note: Some features may be limited due to missing dependencies")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
