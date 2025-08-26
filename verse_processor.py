#!/usr/bin/env python3
"""
Verse processing module for verse detection.
Handles verse detection, grouping, and analysis from extracted text.
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class VerseBlock:
    """Represents a detected Bible verse block with metadata."""
    text: str
    verse_number: str
    content: str
    underline_indices: List[int]
    confidence: float = 0.0
    y_position: int = 0

class VerseProcessor:
    """Processes extracted text to identify and group Bible verses."""
    
    def __init__(self):
        # Common verse number patterns
        self.verse_patterns = [
            # Standard verse numbers: 1, 2, 3, etc.
            r'^\s*(\d+)\s+',
            # Chapter:verse format: 1:1, 2:3, etc.
            r'^\s*(\d+:\d+)\s+',
            # Book chapter:verse with optional numeric prefix and multi-word book name
            r'^\s*((?:[1-3]\s*)?[A-Za-z]+(?:\s+[A-Za-z]+)*\s+\d+:\d+)\s+',
            # Roman numerals: I, II, III, etc.
            r'^\s*([IVX]+)\s+',
            # Chapter numbers: Chapter 1, Chapter 2, etc.
            r'^\s*(Chapter\s+\d+)\s+',
        ]
        
        # Compile all patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.verse_patterns]
    
    def detect_verse_blocks(self, text_regions: Dict[int, str], underline_positions: List[Tuple[int, int, int, int]]) -> List[VerseBlock]:
        """
        Detect and extract verse blocks from extracted text regions.
        Groups related underlines into single verse blocks.
        
        Args:
            text_regions: Dictionary mapping underline index to extracted text
            underline_positions: List of underline coordinates [(x1, y1, x2, y2), ...]
            
        Returns:
            List of detected verse blocks
        """
        verse_blocks = []
        
        # First pass: Find all underlines with verse numbers
        verse_starts = {}
        for underline_idx, text in text_regions.items():
            if not text.strip():
                continue
            
            verse_number = self._extract_verse_number(text)
            if verse_number:
                y_pos = underline_positions[underline_idx][1] if underline_idx < len(underline_positions) else 0
                verse_starts[verse_number] = (underline_idx, y_pos, text)
        
        # Second pass: Group underlines by verse number presence
        for verse_number, (start_idx, y_pos, start_text) in verse_starts.items():
            # Find all underlines that are part of this verse (no new verse numbers)
            related_indices = [start_idx]
            
            # Sort all underlines by y-position to process in order
            sorted_indices = sorted([idx for idx in text_regions.keys() if text_regions[idx].strip()])
            
            # Find the position of our verse start in the sorted list
            try:
                start_pos = sorted_indices.index(start_idx)
            except ValueError:
                continue
            
            # Look ahead for underlines that don't have new verse numbers
            for i in range(start_pos + 1, len(sorted_indices)):
                next_idx = sorted_indices[i]
                next_text = text_regions[next_idx]
                
                # Check if this underline has a new verse number
                has_new_verse = self._extract_verse_number(next_text) is not None
                
                if has_new_verse:
                    # Found a new verse number, stop grouping
                    break
                else:
                    # No new verse number, this underline belongs to current verse
                    related_indices.append(next_idx)
            
            # Create verse block with all related underlines
            content = self._extract_verse_content(start_text, verse_number)
            combined_text = ' '.join([text_regions[idx] for idx in related_indices if text_regions[idx].strip()])
            
            verse_block = VerseBlock(
                text=combined_text,
                verse_number=verse_number,
                content=content,
                underline_indices=related_indices,
                confidence=self._calculate_confidence(combined_text),
                y_position=y_pos
            )
            
            verse_blocks.append(verse_block)
            print(f"📖 Detected verse: {verse_number} - '{content[:50]}...' (underlines: {related_indices})")
        
        return verse_blocks
    
    def group_related_verses(self, verse_blocks: List[VerseBlock], max_y_gap: int = 100) -> List[VerseBlock]:
        """
        Group related verses that are close together vertically.
        
        Args:
            verse_blocks: List of detected verse blocks
            max_y_gap: Maximum vertical distance to consider verses related
            
        Returns:
            List of grouped verse blocks
        """
        if not verse_blocks:
            return []
        
        # Sort by y-position
        sorted_verses = sorted(verse_blocks, key=lambda v: v.y_position)
        
        grouped_verses = []
        current_group = [sorted_verses[0]]
        
        for verse in sorted_verses[1:]:
            # Check if this verse is close to the current group
            if abs(verse.y_position - current_group[-1].y_position) <= max_y_gap:
                current_group.append(verse)
            else:
                # Start a new group
                grouped_verses.append(self._merge_verse_group(current_group))
                current_group = [verse]
        
        # Don't forget the last group
        if current_group:
            grouped_verses.append(self._merge_verse_group(current_group))
        
        print(f"🔗 Grouped {len(verse_blocks)} verses into {len(grouped_verses)} groups")
        return grouped_verses
    
    def _extract_verse_number(self, text: str) -> Optional[str]:
        """Extract verse number from text using pattern matching."""
        for pattern in self.compiled_patterns:
            match = pattern.match(text)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_verse_content(self, text: str, verse_number: str) -> str:
        """Extract verse content by removing the verse number."""
        # Remove the verse number from the beginning
        content = text.replace(verse_number, '', 1).strip()
        
        # Clean up any remaining formatting
        content = re.sub(r'^[^\w]*', '', content)  # Remove leading punctuation
        content = re.sub(r'[^\w\s\.,!?;:\'"()-]*$', '', content)  # Remove trailing punctuation
        
        return content
    
    def _calculate_confidence(self, text: str) -> float:
        """Calculate confidence score for text quality."""
        if not text:
            return 0.0
        
        # Simple confidence scoring based on text characteristics
        confidence = 0.5  # Base confidence
        
        # Bonus for reasonable length
        if 10 <= len(text) <= 200:
            confidence += 0.2
        
        # Bonus for containing common words
        common_words = ['the', 'and', 'of', 'to', 'in', 'that', 'is', 'was', 'for', 'with']
        word_count = sum(1 for word in common_words if word.lower() in text.lower())
        confidence += min(0.2, word_count * 0.05)
        
        # Penalty for excessive punctuation or numbers
        punctuation_ratio = sum(1 for c in text if c in '.,!?;:') / len(text)
        if punctuation_ratio > 0.3:
            confidence -= 0.1
        
        return min(1.0, max(0.0, confidence))
    
    def _merge_verse_group(self, verses: List[VerseBlock]) -> VerseBlock:
        """Merge a group of related verses into a single verse block."""
        if len(verses) == 1:
            return verses[0]
        
        # Combine all text
        combined_text = ' '.join(v.text for v in verses)
        
        # Use the first verse number as the main identifier
        main_verse = verses[0]
        
        # Combine underline indices
        all_indices = []
        for verse in verses:
            all_indices.extend(verse.underline_indices)
        
        # Calculate average y-position
        avg_y = sum(v.y_position for v in verses) / len(verses)
        
        return VerseBlock(
            text=combined_text,
            verse_number=main_verse.verse_number,
            content=main_verse.content,
            underline_indices=all_indices,
            confidence=sum(v.confidence for v in verses) / len(verses),
            y_position=int(avg_y)
        )
    
    def analyze_verse_quality(self, verse_blocks: List[VerseBlock]) -> Dict:
        """
        Analyze the quality and completeness of detected verses.
        
        Args:
            verse_blocks: List of detected verse blocks
            
        Returns:
            Dictionary with analysis results
        """
        if not verse_blocks:
            return {
                'total_verses': 0,
                'average_confidence': 0.0,
                'completeness_score': 0.0,
                'quality_issues': []
            }
        
        total_verses = len(verse_blocks)
        average_confidence = sum(v.confidence for v in verse_blocks) / total_verses
        
        # Analyze completeness
        completeness_scores = []
        quality_issues = []
        
        for verse in verse_blocks:
            # Check for common completeness issues
            if len(verse.content) < 10:
                quality_issues.append(f"Verse {verse.verse_number}: Very short content")
                completeness_scores.append(0.3)
            elif verse.content.endswith('-') or verse.content.endswith('...'):
                quality_issues.append(f"Verse {verse.verse_number}: Incomplete ending")
                completeness_scores.append(0.6)
            elif verse.confidence < 0.5:
                quality_issues.append(f"Verse {verse.verse_number}: Low confidence ({verse.confidence:.2f})")
                completeness_scores.append(0.7)
            else:
                completeness_scores.append(1.0)
        
        overall_completeness = sum(completeness_scores) / len(completeness_scores)
        
        return {
            'total_verses': total_verses,
            'average_confidence': average_confidence,
            'completeness_score': overall_completeness,
            'quality_issues': quality_issues
        }
