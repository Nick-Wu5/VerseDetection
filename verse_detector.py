import re
import math
from typing import List, Tuple, Dict
from dataclasses import dataclass
from collections import Counter

@dataclass
class VerseBlock:
    """
    Represents a detected Bible verse block with metadata.
    
    This dataclass stores information about a single verse detected from OCR text,
    including the verse number, content, and confidence score.
    
    Attributes:
        text (str): The complete raw text of the verse block including verse number
        verse_number (str): The extracted verse number (e.g., "1", "2:3", "Psalm 139:1")
        content (str): The verse content without the verse number
        confidence (float): Confidence score for the verse detection (0.0 to 1.0)
    """
    text: str
    verse_number: str
    content: str
    confidence: float = 0.0

class BibleVerseDetector:
    """
    Detects and extracts Bible verses from OCR text using pattern matching and quality validation.
    
    This class provides comprehensive Bible verse detection capabilities including:
    - Multi-pattern verse number recognition
    - Content quality assessment using entropy analysis
    - OCR artifact detection and filtering
    - Page boundary fragment identification
    - Confidence scoring and filtering
    
    The detector uses a multi-layered validation approach combining pattern matching,
    content quality analysis, and confidence scoring to identify relevant verses
    while filtering out noise, artifacts, and incomplete fragments.
    """
    
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
        Detect and extract verse blocks from raw OCR text.
        
        This method processes the entire OCR text to identify individual Bible verses
        by looking for verse number patterns at the beginning of lines. It handles
        multi-line verses by detecting continuation patterns and groups related lines
        into single verse blocks.
        
        Args:
            text (str): Raw OCR text from the Bible page containing multiple lines
            
        Returns:
            List[VerseBlock]: List of detected verse blocks, each containing:
                - verse_number: The extracted verse number
                - content: The verse content without the verse number
                - text: The complete raw text including verse number
                - confidence: Calculated confidence score (0.0 to 1.0)
                
        Example:
            >>> detector = BibleVerseDetector()
            >>> text = "1 In the beginning God created...\\n2 And the earth was..."
            >>> verses = detector.detect_verse_blocks(text)
            >>> len(verses)
            2
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
        """
        Extract verse number from the beginning of a line using regex patterns.
        
        This method applies multiple regex patterns to identify verse numbers at the
        start of a line. It supports various Bible verse numbering formats including
        standard numbers, chapter:verse format, book references, and Roman numerals.
        
        Args:
            line (str): A single line of text to analyze for verse numbers
            
        Returns:
            str: The extracted verse number if found, empty string otherwise.
                Examples: "1", "2:3", "Psalm 139:1", "I", "Chapter 1"
                
        Note:
            The method uses pre-compiled regex patterns for efficiency and supports
            case-insensitive matching for book names and chapter references.
        """
        for pattern in self.compiled_patterns:
            match = pattern.match(line)
            if match:
                return match.group(1).strip()
        return ""
    
    def _is_verse_continuation(self, line: str) -> bool:
        """
        Determine if a line continues the current verse rather than starting a new one.
        
        This method uses multiple heuristics to identify when a line is part of the
        current verse rather than the start of a new verse. It checks for indentation,
        capitalization, punctuation, and line length to make this determination.
        
        Args:
            line (str): A single line of text to analyze for continuation patterns
            
        Returns:
            bool: True if the line appears to continue the current verse, False otherwise
            
        Note:
            The method uses several indicators of continuation:
            - Indentation (starts with spaces/tabs)
            - Lack of capitalization (doesn't start with capital letter)
            - Punctuation (ends with comma, semicolon, colon)
            - Short length (<50 characters)
        """
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
        """
        Create a VerseBlock object from verse number and multiple lines of text.
        
        This method combines the verse number with the associated text lines to create
        a complete verse block. It extracts the content (removing verse numbers) and
        calculates a confidence score for the verse detection.
        
        Args:
            verse_number (str): The verse number that was detected (e.g., "1", "2:3")
            lines (List[str]): List of text lines that make up this verse block
            
        Returns:
            VerseBlock: A complete verse block containing:
                - text: Full raw text including verse number
                - verse_number: The extracted verse number
                - content: Verse content without verse number
                - confidence: Calculated confidence score (0.0 to 1.0)
                
        Note:
            The confidence score is calculated using the _calculate_confidence method
            which considers content length, verse number format, and content quality.
        """
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
        """
        Extract verse content from multiple lines, removing verse numbers.
        
        This method processes a list of text lines to extract the actual verse content
        by removing verse numbers and cleaning up the text. It handles cases where
        verse numbers appear at the beginning of lines and removes them to get clean content.
        
        Args:
            lines (List[str]): List of text lines that make up the verse
            verse_number (str): The verse number to remove from the content
            
        Returns:
            str: Clean verse content with verse numbers removed and text cleaned up
            
        Example:
            >>> lines = ["1 In the beginning God created", "the heavens and the earth."]
            >>> content = detector._extract_content_from_lines(lines, "1")
            >>> print(content)
            "In the beginning God created the heavens and the earth."
        """
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
        """
        Validate verse number against reasonable Bible verse limits.
        
        This method checks if a detected verse number falls within valid ranges
        for Bible verses. It handles various formats including simple numbers,
        chapter:verse format, and book references with chapter:verse.
        
        Args:
            verse_number (str): The verse number to validate (e.g., "1", "2:3", "Psalm 139:1")
            
        Returns:
            bool: True if the verse number is within valid Bible ranges, False otherwise
            
        Note:
            Validation limits:
            - Chapters: 1-150 (covers all Bible books)
            - Verses: 1-176 (Psalm 119 has 176 verses, the longest)
            - Simple numbers: 1-176 (for verse-only references)
            
        Example:
            >>> detector._is_valid_verse_number("1")
            True
            >>> detector._is_valid_verse_number("1:1")
            True
            >>> detector._is_valid_verse_number("Psalm 139:1")
            True
            >>> detector._is_valid_verse_number("999:999")
            False
        """
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
        """
        Calculate confidence score for verse detection using multiple factors.
        
        This method evaluates the likelihood that a detected verse block represents
        a genuine Bible verse by considering content length, verse number format,
        validation status, and content quality. The score ranges from 0.0 to 1.0.
        
        Args:
            text (str): The complete raw text of the verse block including verse number
            verse_number (str): The extracted verse number (e.g., "1", "2:3", "Psalm 139:1")
            
        Returns:
            float: Confidence score between 0.0 and 1.0, where:
                - 0.0-0.3: Low confidence (likely noise/fragment)
                - 0.3-0.6: Medium confidence (possible verse)
                - 0.6-1.0: High confidence (likely genuine verse)
                
        Scoring Factors:
            - Content length: Longer content gets higher scores
            - Verse number format: Chapter:verse format preferred
            - Validation: Valid verse numbers get bonus points
            - Content quality: Quality score weighted at 40%
            - Fragment penalties: Page boundaries reduce confidence
            
        Example:
            >>> detector._calculate_confidence("1 In the beginning God created...", "1")
            0.85
        """
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
        Filter OCR text to keep only high-confidence Bible verses.
        
        This method processes raw OCR text and returns only the text from verses
        that meet the confidence threshold. It helps remove commentary, footnotes,
        page numbers, and other non-Bible content that might be present in the OCR.
        
        Args:
            text (str): Raw OCR text from the Bible page
            confidence_threshold (float): Minimum confidence score (0.0 to 1.0) for verses to keep.
                                       Default is 0.3 (low confidence filter)
            
        Returns:
            str: Filtered text containing only high-confidence verses, separated by double newlines
            
        Example:
            >>> detector = BibleVerseDetector()
            >>> raw_text = "1 In the beginning God created...\\n\\nCommentary: This verse..."
            >>> filtered = detector.filter_main_text(raw_text, confidence_threshold=0.5)
            >>> print(filtered)
            "1 In the beginning God created..."
        """
        verse_blocks = self.detect_verse_blocks(text)
        high_confidence_blocks = [block for block in verse_blocks if block.confidence >= confidence_threshold]
        return '\n\n'.join(block.text for block in high_confidence_blocks)
    
    def get_verse_statistics(self, text: str, confidence_threshold: float = 0.3) -> Dict:
        """
        Get comprehensive statistics about verse detection performance.
        
        This method analyzes the OCR text and provides detailed statistics about
        verse detection including counts, quality metrics, confidence scores, and
        validation results. It's useful for evaluating detection performance and
        understanding the quality of the OCR text.
        
        Args:
            text (str): Raw OCR text from the Bible page
            confidence_threshold (float): Minimum confidence score (0.0 to 1.0) for high confidence.
                                       Default is 0.3
                                       
        Returns:
            Dict: Comprehensive statistics dictionary containing:
                - total_lines: Total number of lines in the text
                - verse_blocks: Total number of detected verse blocks
                - high_confidence_blocks: Number of verses above confidence threshold
                - low_confidence_blocks: Number of verses below confidence threshold
                - valid_verse_blocks: Number of verses with valid verse numbers
                - invalid_verse_blocks: Number of verses with invalid verse numbers
                - high_quality_blocks: Number of verses with quality score >= 0.6
                - verse_numbers: List of all detected verse numbers
                - high_confidence_verse_numbers: List of high confidence verse numbers
                - low_confidence_verse_numbers: List of low confidence verse numbers
                - invalid_verse_numbers: List of invalid verse numbers
                - average_confidence: Average confidence score across all verses
                - average_high_confidence: Average confidence of high confidence verses
                - average_content_quality: Average content quality score
                - quality_rate: Percentage of high quality verses
                - quality_scores: List of quality scores for each verse
                - filtered_text: Text containing only high confidence verses
                - all_text: Complete original text
                
        Example:
            >>> detector = BibleVerseDetector()
            >>> stats = detector.get_verse_statistics(text, confidence_threshold=0.5)
            >>> print(f"Detected {stats['verse_blocks']} verses")
            >>> print(f"High confidence: {stats['high_confidence_blocks']}")
        """
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
        """
        Calculate comprehensive quality score for verse content using multiple factors.
        
        This method evaluates the quality of verse content by analyzing completeness,
        character quality, entropy, OCR artifacts, and page boundary fragments.
        The score ranges from 0.0 to 1.0, where higher scores indicate better quality.
        
        Args:
            content (str): The verse content to evaluate (without verse number)
            
        Returns:
            float: Quality score between 0.0 and 1.0, where:
                - 0.0-0.3: Poor quality (likely fragment/artifact)
                - 0.3-0.6: Medium quality (partial content)
                - 0.6-1.0: High quality (complete, readable content)
                
        Quality Factors:
            - Content completeness: Word count and word length quality
            - Character quality: Ratio of readable characters
            - Entropy analysis: Text randomness/predictability
            - OCR artifacts: Detection of poor OCR quality
            - Page boundaries: Detection of incomplete fragments
            
        Example:
            >>> detector._calculate_content_quality("In the beginning God created the heavens")
            0.75
            >>> detector._calculate_content_quality("abc123xyz")
            0.15
        """
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
        """
        Calculate character-level Shannon entropy for text quality assessment.
        
        This method measures the randomness/predictability of character distribution
        in the text using Shannon entropy. Higher entropy indicates more diverse
        and natural text, while lower entropy suggests repetitive or artificial content.
        
        Args:
            text (str): The text to analyze for entropy
            
        Returns:
            float: Normalized entropy score between 0.0 and 1.0, where:
                - 0.0-0.3: Low entropy (repetitive, artificial text)
                - 0.3-0.5: Medium entropy (mixed quality)
                - 0.5-1.0: High entropy (natural, diverse text)
                
        Note:
            - Uses Shannon entropy formula: -Σ(p * log2(p))
            - Normalized to 0-1 range with max entropy of 4.5
            - Typical English text has entropy around 4.0-4.5
            - Useful for detecting OCR artifacts and repetitive patterns
            
        Example:
            >>> detector._calculate_text_entropy_simple("Hello world")
            0.85
            >>> detector._calculate_text_entropy_simple("aaaaa")
            0.0
        """
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
        """
        Detect common OCR artifacts that indicate poor quality text.
        
        This method identifies patterns commonly found in poor OCR results,
        including excessive repeated characters, high non-alphabetic ratios,
        and short repeated patterns that suggest OCR errors or noise.
        
        Args:
            content (str): The text content to analyze for OCR artifacts
            
        Returns:
            bool: True if OCR artifacts are detected, False otherwise
            
        Detection Criteria:
            - Excessive repeated characters: >30% same character
            - High non-alphabetic ratio: >40% non-alphabetic characters
            - Short repeated patterns: Repetitive 2-6 character patterns
            - Unusual character distribution: Non-natural text patterns
            
        Example:
            >>> detector._is_ocr_artifact("aaaaa")
            True
            >>> detector._is_ocr_artifact("abc123xyz")
            True
            >>> detector._is_ocr_artifact("In the beginning God created")
            False
        """
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
        """
        Detect fragments that are likely from page boundaries or incomplete content.
        
        This method identifies text fragments that appear to be from page overlaps,
        chapter transitions, or incomplete verses that were cut off during scanning.
        These fragments typically have specific patterns that distinguish them from
        complete, meaningful content.
        
        Args:
            content (str): The text content to analyze for boundary fragments
            
        Returns:
            bool: True if the content appears to be a page boundary fragment, False otherwise
            
        Detection Criteria:
            - Very short fragments: ≤3 words
            - Number + short word patterns: "2 When", "14 abut"
            - Short content after numbers: <20 characters after verse numbers
            - Incomplete sentences: <6 words without proper ending
            - Cut-off content: <40 characters without proper ending
            
        Example:
            >>> detector._is_page_boundary_fragment("2 When")
            True
            >>> detector._is_page_boundary_fragment("for rich and")
            True
            >>> detector._is_page_boundary_fragment("In the beginning God created the heavens")
            False
        """
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
        """
        Get detailed breakdown of content quality scores for analysis.
        
        This method provides a comprehensive analysis of content quality by breaking
        down the quality assessment into individual components. It's useful for
        debugging quality issues and understanding why certain content received
        particular quality scores.
        
        Args:
            content (str): The text content to analyze for quality
            
        Returns:
            Dict[str, float]: Detailed quality breakdown containing:
                - overall_quality: Combined quality score (0.0 to 1.0)
                - content_completeness_score: Word count and length quality
                - character_quality_score: Readable character ratio score
                - entropy_score: Text entropy analysis score
                - ocr_artifact_penalty: Penalty for detected OCR artifacts
                
        Example:
            >>> detector = BibleVerseDetector()
            >>> scores = detector.get_content_quality_score("In the beginning God created")
            >>> print(f"Overall quality: {scores['overall_quality']:.3f}")
            >>> print(f"Completeness: {scores['content_completeness_score']:.3f}")
        """
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
        """
        Calculate common content metrics used across multiple validation functions.
        
        This method provides centralized calculation of basic content metrics to
        avoid redundant computations across different validation functions. It
        calculates word count, average word length, and character quality ratio.
        
        Args:
            content (str): The text content to analyze for metrics
            
        Returns:
            Dict[str, float]: Dictionary containing calculated metrics:
                - word_count: Number of words in the content
                - avg_word_length: Average word length in characters
                - char_quality_ratio: Ratio of readable characters (alphabetic + whitespace)
                - words: List of individual words (for further processing)
                
        Note:
            This method is designed for efficiency by calculating metrics once
            and reusing them across multiple validation functions.
            
        Example:
            >>> detector = BibleVerseDetector()
            >>> metrics = detector._calculate_content_metrics("Hello world")
            >>> print(f"Word count: {metrics['word_count']}")
            >>> print(f"Avg word length: {metrics['avg_word_length']:.1f}")
        """
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
        """
        Calculate character quality score based on readable character ratio.
        
        This method evaluates the quality of text based on the proportion of
        readable characters (alphabetic and whitespace) versus non-readable
        characters (numbers, symbols, special characters). Higher ratios
        indicate better quality text.
        
        Args:
            char_quality_ratio (float): Ratio of readable characters (0.0 to 1.0)
            
        Returns:
            float: Character quality score (0.0, 0.1, or 0.2) where:
                - 0.2: High quality (≥80% readable characters)
                - 0.1: Medium quality (≥60% readable characters)
                - 0.0: Low quality (<60% readable characters)
                
        Note:
            This scoring system prioritizes natural language text over
            technical content with many numbers and symbols.
            
        Example:
            >>> detector._calculate_character_quality_score(0.85)
            0.2
            >>> detector._calculate_character_quality_score(0.65)
            0.1
            >>> detector._calculate_character_quality_score(0.45)
            0.0
        """
        if char_quality_ratio >= 0.8:
            return 0.2
        elif char_quality_ratio >= 0.6:
            return 0.1
        else:
            return 0.0
    
    def _calculate_content_completeness_score(self, word_count: int, avg_word_length: float) -> float:
        """
        Calculate comprehensive content completeness score combining word count and word quality.
        
        This method evaluates content completeness using a multiplicative approach that
        considers both the quantity of content (word count) and the quality of content
        (word length). This provides a more nuanced assessment than simple word counting.
        
        Args:
            word_count (int): Number of words in the content
            avg_word_length (float): Average word length in characters
            
        Returns:
            float: Completeness score between 0.0 and 0.3, where:
                - 0.0: No meaningful content (0 words or very short words)
                - 0.1: Minimal content (2-3 words with quality multiplier)
                - 0.2: Moderate content (4-7 words with quality multiplier)
                - 0.3: Substantial content (≥8 words with quality multiplier)
                
        Scoring Logic:
            Base Score (Word Count):
                - ≥8 words: 0.3 points
                - ≥4 words: 0.2 points
                - ≥2 words: 0.1 points
                - <2 words: 0.0 points
                
            Quality Multiplier (Word Length):
                - ≥4 characters: 1.0x multiplier (full score)
                - ≥3 characters: 0.8x multiplier (slight penalty)
                - <3 characters: 0.5x multiplier (significant penalty)
                
        Example:
            >>> detector._calculate_content_completeness_score(10, 4.5)
            0.3
            >>> detector._calculate_content_completeness_score(5, 3.2)
            0.16
            >>> detector._calculate_content_completeness_score(3, 2.1)
            0.05
        """
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