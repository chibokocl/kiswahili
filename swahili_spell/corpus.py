"""
Corpus Builder for Swahili Spell Checker

Handles text extraction from PDFs, text processing, and word frequency analysis.
"""

import json
import re
import os
import time
from collections import Counter
from typing import Dict, List, Tuple, Optional, Union
from pathlib import Path

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


class CorpusBuilder:
    """
    Build and maintain Swahili word frequency datasets from various text sources.
    """
    
    def __init__(self):
        """Initialize the corpus builder."""
        self.text_sources = []
        self.word_frequencies = Counter()
        self.processed_texts = []
        self.stats = {
            'total_words': 0,
            'unique_words': 0,
            'sources': [],
            'top_words': []
        }
    
    def _log(self, message: str) -> None:
        """Print timestamped log message."""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def add_pdf(self, pdf_path: Union[str, Path]) -> bool:
        """
        Add a PDF file to the corpus sources.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            bool: True if successfully added, False otherwise
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            self._log(f"Warning: PDF file not found: {pdf_path}")
            return False
        
        self._log(f"Processing PDF: {pdf_path.name}")
        start_time = time.time()
        
        try:
            text = self._extract_pdf_text(pdf_path)
            if text:
                self.text_sources.append({
                    'type': 'pdf',
                    'path': str(pdf_path),
                    'text': text
                })
                self.stats['sources'].append(pdf_path.name)
                
                elapsed = time.time() - start_time
                self._log(f"✓ PDF processed successfully in {elapsed:.1f}s")
                return True
            else:
                self._log(f"✗ Could not extract text from PDF: {pdf_path}")
                return False
        except Exception as e:
            elapsed = time.time() - start_time
            self._log(f"✗ Error processing PDF {pdf_path} after {elapsed:.1f}s: {e}")
            return False
    
    def add_text_file(self, text_path: Union[str, Path]) -> bool:
        """
        Add a text file to the corpus sources.
        
        Args:
            text_path: Path to the text file
            
        Returns:
            bool: True if successfully added, False otherwise
        """
        text_path = Path(text_path)
        
        if not text_path.exists():
            self._log(f"Warning: Text file not found: {text_path}")
            return False
        
        self._log(f"Processing text file: {text_path.name}")
        start_time = time.time()
        
        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            self.text_sources.append({
                'type': 'text',
                'path': str(text_path),
                'text': text
            })
            self.stats['sources'].append(text_path.name)
            
            elapsed = time.time() - start_time
            self._log(f"✓ Text file processed successfully in {elapsed:.1f}s")
            return True
        except Exception as e:
            elapsed = time.time() - start_time
            self._log(f"✗ Error processing text file {text_path} after {elapsed:.1f}s: {e}")
            return False
    
    def _extract_pdf_text(self, pdf_path: Path) -> Optional[str]:
        """
        Extract text from PDF using available PDF libraries.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            str: Extracted text or None if failed
        """
        # Try pdfplumber first (better for complex layouts)
        if PDFPLUMBER_AVAILABLE:
            try:
                self._log(f"  Using pdfplumber to extract text...")
                with pdfplumber.open(pdf_path) as pdf:
                    text = ""
                    total_pages = len(pdf.pages)
                    self._log(f"  Found {total_pages} pages")
                    
                    for i, page in enumerate(pdf.pages, 1):
                        if i % 10 == 0 or i == total_pages:
                            self._log(f"  Processing page {i}/{total_pages}")
                        
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    
                    return text if text.strip() else None
            except Exception as e:
                self._log(f"  pdfplumber failed: {e}")
        
        # Fallback to PyPDF2
        if PDF_AVAILABLE:
            try:
                self._log(f"  Using PyPDF2 to extract text...")
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    total_pages = len(pdf_reader.pages)
                    self._log(f"  Found {total_pages} pages")
                    
                    for i, page in enumerate(pdf_reader.pages, 1):
                        if i % 10 == 0 or i == total_pages:
                            self._log(f"  Processing page {i}/{total_pages}")
                        
                        text += page.extract_text() + "\n"
                    
                    return text if text.strip() else None
            except Exception as e:
                self._log(f"  PyPDF2 failed: {e}")
        
        self._log("  No PDF libraries available. Install pdfplumber or PyPDF2.")
        return None
    
    def process_texts(self, 
                     remove_punctuation: bool = True,
                     lowercase: bool = True,
                     min_word_length: int = 2,
                     remove_numbers: bool = True) -> None:
        """
        Process all collected texts with specified cleaning options.
        
        Args:
            remove_punctuation: Remove punctuation marks
            lowercase: Convert text to lowercase
            min_word_length: Minimum word length to include
            remove_numbers: Remove words containing numbers
        """
        self._log("Starting text processing...")
        start_time = time.time()
        
        self.processed_texts = []
        total_sources = len(self.text_sources)
        
        for i, source in enumerate(self.text_sources, 1):
            self._log(f"Processing source {i}/{total_sources}: {Path(source['path']).name}")
            source_start = time.time()
            
            text = source['text']
            
            # Apply text cleaning
            if lowercase:
                text = text.lower()
            
            if remove_punctuation:
                # Keep apostrophes for Swahili contractions
                text = re.sub(r'[^\w\s\']', ' ', text)
            
            if remove_numbers:
                text = re.sub(r'\b\w*\d+\w*\b', ' ', text)
            
            # Split into words and filter
            words = re.findall(r'\b\w+\b', text)
            filtered_words = [
                word for word in words 
                if len(word) >= min_word_length
            ]
            
            self.processed_texts.extend(filtered_words)
            
            source_elapsed = time.time() - source_start
            self._log(f"  Processed {len(filtered_words):,} words in {source_elapsed:.1f}s")
        
        # Update word frequencies
        self._log("Building word frequency dictionary...")
        freq_start = time.time()
        self.word_frequencies = Counter(self.processed_texts)
        freq_elapsed = time.time() - freq_start
        
        # Update statistics
        self._update_stats()
        
        total_elapsed = time.time() - start_time
        self._log(f"✓ Text processing completed in {total_elapsed:.1f}s")
        self._log(f"  Frequency counting took {freq_elapsed:.1f}s")
    
    def _update_stats(self) -> None:
        """Update corpus statistics."""
        self.stats['total_words'] = sum(self.word_frequencies.values())
        self.stats['unique_words'] = len(self.word_frequencies)
        self.stats['top_words'] = self.word_frequencies.most_common(20)
    
    def build_corpus(self) -> Dict[str, int]:
        """
        Build the final corpus with word frequencies.
        
        Returns:
            Dict[str, int]: Word frequency dictionary
        """
        if not self.processed_texts:
            self.process_texts()
        
        return dict(self.word_frequencies)
    
    def save_corpus(self, filepath: Union[str, Path]) -> bool:
        """
        Save corpus data to JSON file.
        
        Args:
            filepath: Path to save the corpus
            
        Returns:
            bool: True if successfully saved
        """
        self._log(f"Saving corpus to: {filepath}")
        start_time = time.time()
        
        try:
            corpus_data = self.build_corpus()
            
            # Create directory if it doesn't exist
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(corpus_data, f, ensure_ascii=False, indent=2)
            
            elapsed = time.time() - start_time
            self._log(f"✓ Corpus saved successfully in {elapsed:.1f}s")
            return True
        except Exception as e:
            elapsed = time.time() - start_time
            self._log(f"✗ Error saving corpus after {elapsed:.1f}s: {e}")
            return False
    
    def save_dictionary(self, filepath: Union[str, Path]) -> bool:
        """
        Save just the word list (without frequencies) to a text file.
        
        Args:
            filepath: Path to save the dictionary
            
        Returns:
            bool: True if successfully saved
        """
        self._log(f"Saving dictionary to: {filepath}")
        start_time = time.time()
        
        try:
            words = list(self.word_frequencies.keys())
            
            # Create directory if it doesn't exist
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                for word in sorted(words):
                    f.write(word + '\n')
            
            elapsed = time.time() - start_time
            self._log(f"✓ Dictionary saved successfully in {elapsed:.1f}s")
            return True
        except Exception as e:
            elapsed = time.time() - start_time
            self._log(f"✗ Error saving dictionary after {elapsed:.1f}s: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """
        Get corpus statistics.
        
        Returns:
            Dict: Statistics about the corpus
        """
        if not self.processed_texts:
            self.process_texts()
        
        return self.stats.copy()
    
    def load_corpus(self, filepath: Union[str, Path]) -> bool:
        """
        Load corpus data from JSON file.
        
        Args:
            filepath: Path to the corpus file
            
        Returns:
            bool: True if successfully loaded
        """
        self._log(f"Loading corpus from: {filepath}")
        start_time = time.time()
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                corpus_data = json.load(f)
            
            self.word_frequencies = Counter(corpus_data)
            self._update_stats()
            
            elapsed = time.time() - start_time
            self._log(f"✓ Corpus loaded successfully in {elapsed:.1f}s")
            return True
        except Exception as e:
            elapsed = time.time() - start_time
            self._log(f"✗ Error loading corpus after {elapsed:.1f}s: {e}")
            return False
    
    def clear(self) -> None:
        """Clear all collected data."""
        self.text_sources = []
        self.word_frequencies = Counter()
        self.processed_texts = []
        self.stats = {
            'total_words': 0,
            'unique_words': 0,
            'sources': [],
            'top_words': []
        } 