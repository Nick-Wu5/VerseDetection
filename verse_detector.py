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
        Detect verse blocks in the given text.
        
        Args:
            text: Raw OCR text from the Bible page
            
        Returns:
            List of detected verse blocks
        """
        lines = text.split('\n')
        verse_blocks = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line starts with a verse number
            verse_number = self._extract_verse_number(line)
            if verse_number:
                # Extract the content after the verse number
                content = self._extract_content(line, verse_number)
                confidence = self._calculate_confidence(line, verse_number)
                
                verse_block = VerseBlock(
                    text=line,
                    verse_number=verse_number,
                    content=content,
                    confidence=confidence
                )
                verse_blocks.append(verse_block)
        
        return verse_blocks
    
    def _extract_verse_number(self, line: str) -> str:
        """Extract verse number from the beginning of a line"""
        for pattern in self.compiled_patterns:
            match = pattern.match(line)
            if match:
                return match.group(1).strip()
        return ""
    
    def _extract_content(self, line: str, verse_number: str) -> str:
        """Extract the content after the verse number"""
        # Remove the verse number from the beginning
        content = line[len(verse_number):].strip()
        return content
    
    def _calculate_confidence(self, line: str, verse_number: str) -> float:
        """Calculate confidence score for verse detection"""
        confidence = 0.0
        
        # Higher confidence for longer content
        content_length = len(line) - len(verse_number)
        if content_length > 10:
            confidence += 0.3
        
        # Higher confidence for specific patterns
        if ':' in verse_number:  # Chapter:verse format
            confidence += 0.4
        elif verse_number.isdigit():  # Simple verse number
            confidence += 0.3
        elif any(word in verse_number.lower() for word in ['psalm', 'john', 'matthew', 'mark', 'luke']):
            confidence += 0.5  # Book names
            
        # Penalize very short content
        if content_length < 5:
            confidence -= 0.2
            
        return min(confidence, 1.0)
    
    def filter_main_text(self, text: str) -> str:
        """
        Filter text to keep only lines that contain verse numbers.
        This helps remove commentary and other non-Bible text.
        """
        lines = text.split('\n')
        filtered_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line contains a verse number
            if self._extract_verse_number(line):
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def get_verse_statistics(self, text: str) -> Dict:
        """Get statistics about verse detection"""
        verse_blocks = self.detect_verse_blocks(text)
        
        stats = {
            'total_lines': len(text.split('\n')),
            'verse_blocks': len(verse_blocks),
            'verse_numbers': [block.verse_number for block in verse_blocks],
            'average_confidence': sum(block.confidence for block in verse_blocks) / len(verse_blocks) if verse_blocks else 0,
            'filtered_text': self.filter_main_text(text)
        }
        
        return stats

# Example usage and testing
if __name__ == "__main__":
    detector = BibleVerseDetector()
    
    # Test with sample Bible text
    sample_text = """
    1 The Lord is my shepherd, I shall not want.
    2 He makes me lie down in green pastures,
    he leads me beside quiet waters,
    3 he refreshes my soul.
    He guides me along the right paths
    for his name's sake.
    """
    
    print("Testing verse detection:")
    stats = detector.get_verse_statistics(sample_text)
    print(f"Found {stats['verse_blocks']} verse blocks")
    print(f"Verse numbers: {stats['verse_numbers']}")
    print(f"Average confidence: {stats['average_confidence']:.2f}")
    print("\nFiltered text:")
    print(stats['filtered_text']) 