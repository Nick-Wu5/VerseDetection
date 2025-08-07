import re
from typing import List, Tuple, Dict
from dataclasses import dataclass

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
        
        stats = {
            'total_lines': len(text.split('\n')),
            'verse_blocks': len(verse_blocks),
            'high_confidence_blocks': len(high_confidence_blocks),
            'low_confidence_blocks': len(low_confidence_blocks),
            'valid_verse_blocks': len(valid_verse_blocks),
            'invalid_verse_blocks': len(invalid_verse_blocks),
            'verse_numbers': [block.verse_number for block in verse_blocks],
            'high_confidence_verse_numbers': [block.verse_number for block in high_confidence_blocks],
            'low_confidence_verse_numbers': [block.verse_number for block in low_confidence_blocks],
            'invalid_verse_numbers': [block.verse_number for block in invalid_verse_blocks],
            'average_confidence': sum(block.confidence for block in verse_blocks) / len(verse_blocks) if verse_blocks else 0,
            'average_high_confidence': sum(block.confidence for block in high_confidence_blocks) / len(high_confidence_blocks) if high_confidence_blocks else 0,
            'validation_rate': len(valid_verse_blocks) / len(verse_blocks) if verse_blocks else 0,
            'filtered_text': '\n\n'.join(block.text for block in high_confidence_blocks),
            'all_text': '\n\n'.join(block.text for block in verse_blocks),
            'confidence_threshold': confidence_threshold
        }
        
        return stats