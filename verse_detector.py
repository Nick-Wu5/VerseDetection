import re
import math
from typing import List, Tuple, Dict
from dataclasses import dataclass
from collections import Counter

@dataclass
class VerseBlock:
    """Represents a detected Bible verse block"""
    text: str
    verse_number: str
    content: str
    confidence: float = 0.0

class BibleVerseDetector:
    """Detects and extracts Bible verses using verse numbering patterns"""
    
    def __init__(self):
        # Common verse number patterns
        self.verse_patterns = [
            # Standard verse numbers: 1, 2, 3, etc.
            r'^\s*(\d+)\s+',
            # Chapter:verse format: 1:1, 2:3, etc.
            r'^\s*(\d+:\d+)\s+',
            # Book chapter:verse: Psalm 139:1, John 3:16, etc.
            r'^\s*([A-Za-z]+\s+\d+:\d+)\s+',
            # Roman numerals: I, II, III, etc.
            r'^\s*([IVX]+)\s+',
            # Chapter numbers: Chapter 1, Chapter 2, etc.
            r'^\s*(Chapter\s+\d+)\s+',
        ]
        
        # Compile all patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.verse_patterns]
    
    def detect_verse_blocks(self, text: str) -> List[VerseBlock]:
        """
        Detect verse blocks in the given text, handling multi-line verses.
        
        Args:
            text: Raw OCR text from the Bible page
            
        Returns:
            List of detected verse blocks
        """
        lines = text.split('\n')
        verse_blocks = []
        current_verse = None
        current_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line starts with a verse number
            verse_number = self._extract_verse_number(line)
            
            if verse_number:
                # Save previous verse if exists
                if current_verse:
                    verse_block = self._create_verse_block(current_verse, current_lines)
                    verse_blocks.append(verse_block)
                
                # Start new verse
                current_verse = verse_number
                current_lines = [line]
            elif current_verse and self._is_verse_continuation(line):
                # Continue current verse
                current_lines.append(line)
            else:
                # This might be commentary or other content
                # Save current verse and start fresh
                if current_verse:
                    verse_block = self._create_verse_block(current_verse, current_lines)
                    verse_blocks.append(verse_block)
                current_verse = None
                current_lines = []
        
        # Don't forget the last verse
        if current_verse:
            verse_block = self._create_verse_block(current_verse, current_lines)
            verse_blocks.append(verse_block)
        
        return verse_blocks
    
    def _extract_verse_number(self, line: str) -> str:
        """Extract verse number from the beginning of a line"""
        for pattern in self.compiled_patterns:
            match = pattern.match(line)
            if match:
                return match.group(1).strip()
        return ""
    
    def _is_verse_continuation(self, line: str) -> bool:
        """Determine if a line continues the current verse"""
        line = line.strip()
        
        # Skip empty lines
        if not line:
            return False
        
        # Check for indentation (starts with spaces/tabs)
        if line.startswith((' ', '\t')):
            return True
        
        # Check if line doesn't start with a verse number
        if self._extract_verse_number(line):
            return False
        
        # Check for sentence continuation patterns
        # (doesn't start with capital letter, ends with comma, etc.)
        if not line[0].isupper():
            return True
        
        # Check for punctuation that suggests continuation
        if line.endswith((',', ';', ':')):
            return True
        
        # Check if line is short (likely continuation)
        if len(line) < 50:
            return True
        
        return False
    
    def _create_verse_block(self, verse_number: str, lines: List[str]) -> VerseBlock:
        """Create a VerseBlock from verse number and multiple lines"""
        full_text = '\n'.join(lines)
        content = self._extract_content_from_lines(lines, verse_number)
        confidence = self._calculate_confidence(full_text, verse_number)
        
        return VerseBlock(
            text=full_text,
            verse_number=verse_number,
            content=content,
            confidence=confidence
        )
    
    def _extract_content_from_lines(self, lines: List[str], verse_number: str) -> str:
        """Extract content from multiple lines, removing verse numbers"""
        content_lines = []
        
        for line in lines:
            # Remove verse number from first line only
            if line.strip().startswith(verse_number):
                content = line[len(verse_number):].strip()
            else:
                content = line.strip()
            
            if content:
                content_lines.append(content)
        
        return ' '.join(content_lines)
    
    def _is_valid_verse_number(self, verse_number: str) -> bool:
        """Validate verse number against Bible limits"""
        try:
            # Handle chapter:verse format (e.g., "1:1", "Psalm 139:1")
            if ':' in verse_number:
                parts = verse_number.split(':')
                if len(parts) != 2:
                    return False
                chapter = int(parts[0].split()[-1])  # Handle "Psalm 139:1" -> "139"
                verse = int(parts[1])
                return 1 <= chapter <= 150 and 1 <= verse <= 176
            else:
                # Simple verse number
                num = int(verse_number)
                return 1 <= num <= 176
        except (ValueError, IndexError):
            return False
    
    def _calculate_confidence(self, text: str, verse_number: str) -> float:
        """Calculate confidence score for verse detection"""
        confidence = 0.0
        
        # Calculate total content length (all lines)
        content_length = len(text) - len(verse_number)
        if content_length > 20:
            confidence += 0.3
        elif content_length > 10:
            confidence += 0.2
        
        # Higher confidence for specific patterns
        if ':' in verse_number:  # Chapter:verse format
            confidence += 0.4
        elif verse_number.isdigit():  # Simple verse number
            confidence += 0.3
        elif any(word in verse_number.lower() for word in ['psalm', 'john', 'matthew', 'mark', 'luke']):
            confidence += 0.5  # Book names
            
        # Add validation scoring
        if self._is_valid_verse_number(verse_number):
            confidence += 0.3  # Valid verse number
            # Bonus for common verse numbers (1-50)
            try:
                if ':' in verse_number:
                    verse = int(verse_number.split(':')[1])
                else:
                    verse = int(verse_number)
                if 1 <= verse <= 50:
                    confidence += 0.1  # Common range bonus
            except (ValueError, IndexError):
                pass
        else:
            confidence -= 0.8  # Invalid verse number penalty
            
        # Penalize very short content
        if content_length < 5:
            confidence -= 0.2
        
        # Add content quality scoring using entropy analysis
        # Extract content once and reuse
        content = self._extract_content_from_lines(text.split('\n'), verse_number)
        content_quality = self._calculate_content_quality(content)
        confidence += content_quality * 0.4  # Increased from 0.3 to 0.4 (40% weight)
        
        # Additional penalties for fragments and page boundaries (strengthened)
        if self._is_page_boundary_fragment(content):
            confidence -= 0.5  # Increased from 0.3 to 0.5
        
        return min(confidence, 1.0)
    
    def filter_main_text(self, text: str, confidence_threshold: float = 0.3) -> str:
        """
        Filter text to keep only high-confidence verses, handling multi-line verses.
        This helps remove commentary and other non-Bible text.
        """
        verse_blocks = self.detect_verse_blocks(text)
        high_confidence_blocks = [block for block in verse_blocks if block.confidence >= confidence_threshold]
        return '\n\n'.join(block.text for block in high_confidence_blocks)
    
    def get_verse_statistics(self, text: str, confidence_threshold: float = 0.3) -> Dict:
        """Get statistics about verse detection with confidence-based filtering"""
        verse_blocks = self.detect_verse_blocks(text)
        
        # Filter verses based on confidence threshold
        high_confidence_blocks = [block for block in verse_blocks if block.confidence >= confidence_threshold]
        low_confidence_blocks = [block for block in verse_blocks if block.confidence < confidence_threshold]
        
        # Calculate validation statistics
        valid_verse_blocks = [block for block in verse_blocks if self._is_valid_verse_number(block.verse_number)]
        invalid_verse_blocks = [block for block in verse_blocks if not self._is_valid_verse_number(block.verse_number)]
        
        # Calculate quality statistics (optimized to avoid redundant calculations)
        quality_scores = []
        high_quality_blocks = []
        
        for block in verse_blocks:
            quality_score = self._calculate_content_quality(block.content)
            quality_scores.append(quality_score)
            
            if quality_score >= 0.6:
                high_quality_blocks.append(block)
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        stats = {
            'total_lines': len(text.split('\n')),
            'verse_blocks': len(verse_blocks),
            'high_confidence_blocks': len(high_confidence_blocks),
            'low_confidence_blocks': len(low_confidence_blocks),
            'valid_verse_blocks': len(valid_verse_blocks),
            'invalid_verse_blocks': len(invalid_verse_blocks),
            'high_quality_blocks': len(high_quality_blocks),
            'verse_numbers': [block.verse_number for block in verse_blocks],
            'high_confidence_verse_numbers': [block.verse_number for block in high_confidence_blocks],
            'low_confidence_verse_numbers': [block.verse_number for block in low_confidence_blocks],
            'invalid_verse_numbers': [block.verse_number for block in invalid_verse_blocks],
            'average_confidence': sum(block.confidence for block in verse_blocks) / len(verse_blocks) if verse_blocks else 0,
            'average_high_confidence': sum(block.confidence for block in high_confidence_blocks) / len(high_confidence_blocks) if high_confidence_blocks else 0,
            'average_content_quality': avg_quality,
            'validation_rate': len(valid_verse_blocks) / len(verse_blocks) if verse_blocks else 0,
            'quality_rate': len(high_quality_blocks) / len(verse_blocks) if verse_blocks else 0,
            'filtered_text': '\n\n'.join(block.text for block in high_confidence_blocks),
            'all_text': '\n\n'.join(block.text for block in verse_blocks),
            'confidence_threshold': confidence_threshold,
            'quality_scores': quality_scores
        }
        
        return stats
    
    def _calculate_content_quality(self, content: str) -> float:
        """Calculate quality score for verse content"""
        if not content.strip():
            return 0.0
        
        # Get consolidated metrics
        metrics = self._calculate_content_metrics(content)
        word_count = metrics['word_count']
        avg_word_length = metrics['avg_word_length']
        char_quality_ratio = metrics['char_quality_ratio']
        
        quality_score = 0.0
        
        # Factor 1: Content completeness (combined word count and word quality)
        completeness_score = self._calculate_content_completeness_score(word_count, avg_word_length)
        if completeness_score == 0.0:
            return 0.0  # Early return for very short content
        quality_score += completeness_score
        
        # Factor 2: Character quality validation (using consolidated method)
        quality_score += self._calculate_character_quality_score(char_quality_ratio)
        
        # Factor 3: OCR artifact detection (strengthened penalty)
        if self._is_ocr_artifact(content):
            quality_score -= 0.8  # Increased from -0.5
        
        # Factor 4: Simple entropy analysis
        entropy_quality = self._calculate_text_entropy_simple(content)
        quality_score += entropy_quality * 0.2
        
        # Factor 5: Page boundary detection (strengthened penalty)
        if self._is_page_boundary_fragment(content):
            quality_score -= 0.6  # Increased from -0.3
        
        return max(0.0, min(1.0, quality_score))
    
    def _calculate_text_entropy_simple(self, text: str) -> float:
        """Calculate simple character-level entropy for text quality assessment"""
        if not text.strip():
            return 0.0
        
        # Count character frequencies
        char_counts = Counter(text.lower())
        total_chars = len(text)
        
        if total_chars == 0:
            return 0.0
        
        # Calculate entropy
        entropy = 0.0
        for count in char_counts.values():
            if count > 0:
                probability = count / total_chars
                entropy -= probability * math.log2(probability)
        
        # Normalize entropy (typical English text has entropy ~4.0-4.5)
        # Scale to 0-1 range where 0.3-0.5 is good quality
        normalized_entropy = min(1.0, entropy / 4.5)
        
        return normalized_entropy
    
    def _is_ocr_artifact(self, content: str) -> bool:
        """Detect common OCR artifacts that indicate poor quality"""
        if not content:
            return False
        
        # Check for excessive repeated characters
        for char in content:
            if content.count(char) > len(content) * 0.3:  # More than 30% same character
                return True
        
        # Check for excessive numbers or special characters
        non_alpha_ratio = sum(1 for c in content if not c.isalpha() and not c.isspace()) / len(content)
        if non_alpha_ratio > 0.4:  # More than 40% non-alphabetic
            return True
        
        # Check for very short repeated patterns
        if len(content) >= 6:
            for i in range(2, min(6, len(content) // 2 + 1)):
                pattern = content[:i]
                if content.count(pattern) > len(content) / (i * 2):
                    return True
        
        return False
    
    def _is_page_boundary_fragment(self, content: str) -> bool:
        """Detect fragments that are likely from page boundaries, chapter transitions, or incomplete content"""
        if not content.strip():
            return False
        
        words = content.split()
        
        # Very short fragments (likely page overlap or incomplete)
        if len(words) <= 3:  # Increased from 2
            return True
        
        # Check for chapter transition patterns and page overlap
        # Look for patterns like "2 When", "14 abut", "13 A rule"
        if len(words) >= 2:
            first_word = words[0]
            second_word = words[1] if len(words) > 1 else ""
            
            # Pattern: number + short word (likely chapter transition or page overlap)
            if first_word.isdigit() and len(second_word) <= 4:
                return True
            
            # Pattern: very short content after a number
            if first_word.isdigit() and len(content.strip()) < 20:  # Increased from 15
                return True
        
        # Check for incomplete verses that end abruptly
        if not content.rstrip().endswith(('.', '!', '?', ';', ':')) and len(words) < 6:  # Increased from 5
            return True
        
        # Check for content that looks like it was cut off mid-sentence
        if content.strip() and not content.rstrip().endswith(('.', '!', '?', ';', ':')) and len(content.strip()) < 40:  # Increased from 30
            return True
        
        return False
    
    def get_content_quality_score(self, content: str) -> Dict[str, float]:
        """Get detailed content quality scores for analysis"""
        if not content.strip():
            return {
                'overall_quality': 0.0,
                'content_completeness_score': 0.0,
                'character_quality_score': 0.0,
                'entropy_score': 0.0,
                'ocr_artifact_penalty': 0.0
            }
        
        # Get consolidated metrics
        metrics = self._calculate_content_metrics(content)
        word_count = metrics['word_count']
        avg_word_length = metrics['avg_word_length']
        char_quality_ratio = metrics['char_quality_ratio']
        
        # Calculate individual scores using consolidated methods
        content_completeness_score = self._calculate_content_completeness_score(word_count, avg_word_length)
        character_quality_score = self._calculate_character_quality_score(char_quality_ratio)
        entropy_score = self._calculate_text_entropy_simple(content) * 0.2
        ocr_artifact_penalty = -0.5 if self._is_ocr_artifact(content) else 0.0
        
        overall_quality = max(0.0, min(1.0, 
            content_completeness_score + character_quality_score + 
            entropy_score + ocr_artifact_penalty))
        
        return {
            'overall_quality': overall_quality,
            'content_completeness_score': content_completeness_score,
            'character_quality_score': character_quality_score,
            'entropy_score': entropy_score,
            'ocr_artifact_penalty': ocr_artifact_penalty
        }
    
    def _calculate_content_metrics(self, content: str) -> Dict[str, float]:
        """Calculate common content metrics used across multiple validation functions"""
        if not content.strip():
            return {
                'word_count': 0,
                'avg_word_length': 0.0,
                'char_quality_ratio': 0.0,
                'words': []
            }
        
        words = content.split()
        word_count = len(words)
        
        # Calculate average word length
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0.0
        
        # Calculate character quality ratio
        readable_chars = sum(1 for c in content if c.isalpha() or c.isspace())
        char_quality_ratio = readable_chars / len(content) if content else 0.0
        
        return {
            'word_count': word_count,
            'avg_word_length': avg_word_length,
            'char_quality_ratio': char_quality_ratio,
            'words': words
        }
    
    def _calculate_character_quality_score(self, char_quality_ratio: float) -> float:
        """Calculate character quality score with consistent thresholds"""
        if char_quality_ratio >= 0.8:
            return 0.2
        elif char_quality_ratio >= 0.6:
            return 0.1
        else:
            return 0.0
    
    def _calculate_content_completeness_score(self, word_count: int, avg_word_length: float) -> float:
        """Calculate comprehensive content completeness score combining word count and word quality"""
        if word_count == 0:
            return 0.0
        
        # Base score from word count (completeness)
        if word_count >= 8:
            base_score = 0.3
        elif word_count >= 4:
            base_score = 0.2
        elif word_count >= 2:
            base_score = 0.1
        else:
            return 0.0  # Too short to be meaningful
        
        # Quality multiplier from word length (meaningfulness)
        if avg_word_length >= 4:
            quality_multiplier = 1.0  # Full score
        elif avg_word_length >= 3:
            quality_multiplier = 0.8  # Slight penalty
        else:
            quality_multiplier = 0.5  # Significant penalty for very short words
        
        return base_score * quality_multiplier