#!/usr/bin/env python3
"""
Comprehensive test script to process all images in Photos folder
and compare results with actual Bible verses (NIV translation)
"""

import os
import json
import re
from google.cloud import vision
from dotenv import load_dotenv
from verse_detector import BibleVerseDetector
import logging

# Load environment variables
load_dotenv(override=True)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('verse_detection_test.log'),
        logging.StreamHandler()
    ]
)

# Initialize the Vision API client
client = vision.ImageAnnotatorClient()

# Initialize verse detector
detector = BibleVerseDetector()

# Actual Bible verses (NIV translation) for comparison
ACTUAL_VERSES = {
    'proverbs_27': {
        '4': "Anger is cruel and fury overwhelming, but who can stand before jealousy?",
        '5': "Better is open rebuke than hidden love.",
        '6': "Wounds from a friend can be trusted, but an enemy multiplies kisses.",
        '7': "One who is full loathes honey from the comb, but to the hungry even what is bitter tastes sweet.",
        '8': "Like a bird that flees its nest is anyone who flees from home.",
        '9': "Perfume and incense bring joy to the heart, and the pleasantness of a friend springs from their heartfelt advice.",
        '10': "Do not forsake your friend or a friend of your family, and do not go to your relative's house when disaster strikes you— better a neighbor nearby than a relative far away.",
        '11': "Be wise, my son, and bring joy to my heart; then I can answer anyone who treats me with contempt.",
        '12': "The prudent see danger and take refuge, but the simple keep going and pay the penalty.",
        '13': "Take the garment of one who puts up security for a stranger; hold it in pledge if it is done for an outsider.",
        '14': "If anyone loudly blesses their neighbor early in the morning, it will be taken as a curse.",
        '15': "A quarrelsome wife is like the dripping of a leaky roof in a rainstorm;",
        '16': "restraining her is like restraining the wind or grasping oil with the hand.",
        '17': "As iron sharpens iron, so one person sharpens another.",
        '18': "The one who guards a fig tree will eat its fruit, and whoever protects their master will be honored.",
        '19': "As water reflects the face, so one's life reflects the heart.",
        '20': "Death and Destruction are never satisfied, and neither are human eyes.",
        '21': "The crucible for silver and the furnace for gold, but people are tested by their praise.",
        '22': "Though you grind a fool in a mortar, grinding them like grain with a pestle, you will not remove their folly from them.",
        '23': "Be sure you know the condition of your flocks, give careful attention to your herds;",
        '24': "for riches do not endure forever, and a crown is not secure for all generations.",
        '25': "When the hay is removed and new growth appears and the grass from the hills is gathered in,",
        '26': "the lambs will provide you with clothing, and the goats with the price of a field.",
        '27': "You will have plenty of goats' milk to feed your family and to nourish your female servants."
    },
    'proverbs_31': {
        '10': "A wife of noble character who can find? She is worth far more than rubies.",
        '11': "Her husband has full confidence in her and lacks nothing of value.",
        '12': "She brings him good, not harm, all the days of her life.",
        '13': "She selects wool and flax and works with eager hands.",
        '14': "She is like the merchant ships, bringing her food from afar.",
        '15': "She gets up while it is still night; she provides food for her family and portions for her female servants.",
        '16': "She considers a field and buys it; out of her earnings she plants a vineyard.",
        '17': "She sets about her work vigorously; her arms are strong for her tasks.",
        '18': "She sees that her trading is profitable, and her lamp does not go out at night.",
        '19': "In her hand she holds the distaff and grasps the spindle with her fingers.",
        '20': "She opens her arms to the poor and extends her hands to the needy.",
        '21': "When it snows, she has no fear for her household; for all of them are clothed in scarlet.",
        '22': "She makes coverings for her bed; she is clothed in fine linen and purple.",
        '23': "Her husband is respected at the city gate, where he takes his seat among the elders of the land.",
        '24': "She makes linen garments and sells them, and supplies the merchants with sashes.",
        '25': "She is clothed with strength and dignity; she can laugh at the days to come.",
        '26': "She speaks with wisdom, and faithful instruction is on her tongue.",
        '27': "She watches over the affairs of her household and does not eat the bread of idleness.",
        '28': "Her children arise and call her blessed; her husband also, and he praises her:",
        '29': '"Many women do noble things, but you surpass them all."',
        '30': "Charm is deceptive, and beauty is fleeting; but a woman who fears the LORD is to be praised.",
        '31': "Honor her for all that her hands have done, and let her works bring her praise at the city gate."
    },
    'psalm_139': {
        '17': "How precious to me are your thoughts, God! How vast is the sum of them!",
        '18': "Were I to count them, they would outnumber the grains of sand— when I awake, I am still with you.",
        '19': "If only you, God, would slay the wicked! Away from me, you who are bloodthirsty!",
        '20': "They speak of you with evil intent; your adversaries misuse your name.",
        '21': "Do I not hate those who hate you, LORD, and abhor those who are in rebellion against you?",
        '22': "I have nothing but hatred for them; I count them my enemies.",
        '23': "Search me, God, and know my heart; test me and know my anxious thoughts.",
        '24': "See if there is any offensive way in me, and lead me in the way everlasting.",
        # Psalm 140 content (continuing from the same image)
        '140_1': "Rescue me, LORD, from evildoers; protect me from the violent,",
        '140_2': "who devise evil plans in their hearts and stir up war every day.",
        '140_3': "They make their tongues as sharp as a serpent's; the poison of vipers is on their lips.",
        '140_4': "Keep me safe, LORD, from the hands of the wicked; protect me from the violent, who devise ways to trip my feet.",
        '140_5': "The arrogant have hidden a snare for me; they have spread out the cords of their net and have set traps for me along my path.",
        '140_6': "I say to the LORD, 'You are my God.' Hear, LORD, my cry for mercy.",
        '140_7': "Sovereign LORD, my strong deliverer, you shield my head in the day of battle.",
        '140_8': "Do not grant the wicked their desires, LORD; do not let their plans succeed.",
        '140_9': "Those who surround me proudly rear their heads; may the mischief of their lips engulf them.",
        '140_10': "May burning coals fall on them; may they be thrown into the fire, into miry pits, never to rise.",
        '140_11': "May slanderers not be established in the land; may disaster hunt down the violent.",
        '140_12': "I know that the LORD secures justice for the poor and upholds the cause of the needy."
    },
    'proverbs_12': {
        '1': "Whoever loves discipline loves knowledge, but whoever hates correction is stupid.",
        '2': "Good people obtain favor from the LORD, but he condemns those who devise wicked schemes.",
        '3': "No one can be established through wickedness, but the righteous cannot be uprooted.",
        '4': "A wife of noble character is her husband's crown, but a disgraceful wife is like decay in his bones.",
        '5': "The plans of the righteous are just, but the advice of the wicked is deceitful.",
        '6': "The words of the wicked lie in wait for blood, but the speech of the upright rescues them.",
        '7': "The wicked are overthrown and are no more, but the house of the righteous stands firm.",
        '8': "A person is praised according to their prudence, and one with a warped mind is despised.",
        '9': "Better to be a nobody and yet have a servant than pretend to be somebody and have no food.",
        '10': "The righteous care for the needs of their animals, but the kindest acts of the wicked are cruel.",
        '11': "Those who work their land will have abundant food, but those who chase fantasies have no sense.",
        '12': "The wicked desire the stronghold of evildoers, but the root of the righteous endures.",
        '13': "Evildoers are trapped by their sinful talk, and so the innocent escape trouble.",
        '14': "From the fruit of their lips people are filled with good things, and the work of their hands brings them reward.",
        '15': "The way of fools seems right to them, but the wise listen to advice.",
        '16': "Fools show their annoyance at once, but the prudent overlook an insult.",
        '17': "An honest witness tells the truth, but a false witness tells lies.",
        '18': "The words of the reckless pierce like swords, but the tongue of the wise brings healing.",
        '19': "Truthful lips endure forever, but a lying tongue lasts only a moment.",
        '20': "Deceit is in the hearts of those who plot evil, but those who promote peace have joy.",
        '21': "No harm overtakes the righteous, but the wicked have their fill of trouble.",
        '22': "The LORD detests lying lips, but he delights in people who are trustworthy.",
        '23': "The prudent keep their knowledge to themselves, but a fool's heart blurts out folly.",
        '24': "Diligent hands will rule, but laziness ends in forced labor.",
        '25': "Anxiety weighs down the heart, but a kind word cheers it up.",
        '26': "The righteous choose their friends carefully, but the way of the wicked leads them astray.",
        '27': "The lazy do not roast any game, but the diligent feed on the riches of the hunt.",
        '28': "In the way of righteousness there is life; along that path is immortality."
    }
}

# Load optional NIV translations from JSON (keys should match image_name without extension)
try:
    _json_path = os.path.join(os.path.dirname(__file__), 'niv_translations.json')
    if os.path.exists(_json_path):
        with open(_json_path, 'r') as _f:
            _loaded = json.load(_f)
            if isinstance(_loaded, dict):
                ACTUAL_VERSES.update(_loaded)
except Exception as _e:
    logging.warning(f"Could not load NIV translations JSON: {_e}")

def process_image(image_path):
    """Process a single image and return verse detection results"""
    logging.info(f"Processing image: {image_path}")
    
    try:
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        image = vision.Image(content=content)
        
        # Perform OCR
        response = client.document_text_detection(image=image)
        annotation = response.full_text_annotation
        
        # Get verse statistics with confidence filtering
        stats = detector.get_verse_statistics(annotation.text, confidence_threshold=0.5)
        
        # Get detailed verse blocks for significance scoring
        verse_blocks = detector.detect_verse_blocks(annotation.text)
        verse_details = []
        
        for block in verse_blocks:
            quality_score = detector._calculate_content_quality(block.content)
            verse_details.append({
                'verse_number': block.verse_number,
                'content': block.content,
                'confidence': block.confidence,
                'quality_score': quality_score,
                'is_high_confidence': block.confidence >= 0.5,
                'is_page_boundary': detector._is_page_boundary_fragment(block.content),
                'is_ocr_artifact': detector._is_ocr_artifact(block.content)
            })
        
        return {
            'image_path': image_path,
            'total_lines': stats['total_lines'],
            'verse_blocks': stats['verse_blocks'],
            'high_confidence_blocks': stats['high_confidence_blocks'],
            'low_confidence_blocks': stats['low_confidence_blocks'],
            'valid_verse_blocks': stats['valid_verse_blocks'],
            'invalid_verse_blocks': stats['invalid_verse_blocks'],
            'average_confidence': stats['average_confidence'],
            'average_content_quality': stats['average_content_quality'],
            'high_confidence_verse_numbers': stats['high_confidence_verse_numbers'],
            'filtered_text': stats['filtered_text'],
            'all_text': stats['all_text'],
            'quality_scores': stats['quality_scores'],
            'verse_details': verse_details
        }
        
    except Exception as e:
        logging.error(f"Error processing {image_path}: {str(e)}")
        return None

def compare_with_actual_verses(detected_verses, actual_verses, image_name, all_text):
    """Compare detected verses with actual Bible verses"""
    logging.info(f"Comparing detected verses with actual verses for {image_name}")
    
    comparison_results = {
        'image_name': image_name,
        'detected_verses': detected_verses,
        'actual_verses': list(actual_verses.keys()) if isinstance(actual_verses, dict) else [],
        'matches': [],
        'partial_matches': [],
        'missing_verses': [],
        'extra_verses': [],
        'accuracy_score': 0.0
    }
    
    # Get actual verses for this image
    actual_verses_dict = actual_verses.get(image_name, {})
    
    # Get all verse blocks from the text
    verse_blocks = detector.detect_verse_blocks(all_text)
    
    # Compare each detected verse
    for verse_num in detected_verses:
        if verse_num in actual_verses_dict:
            actual_verse = actual_verses_dict[verse_num]
            
            # Find the detected verse content
            detected_content = ""
            for block in verse_blocks:
                if block.verse_number == verse_num:
                    detected_content = block.content
                    break
            
            # Calculate similarity
            similarity = calculate_similarity(detected_content, actual_verse)
            
            if similarity > 0.8:
                comparison_results['matches'].append({
                    'verse_number': verse_num,
                    'detected': detected_content,
                    'actual': actual_verse,
                    'similarity': similarity
                })
            elif similarity > 0.5:
                comparison_results['partial_matches'].append({
                    'verse_number': verse_num,
                    'detected': detected_content,
                    'actual': actual_verse,
                    'similarity': similarity
                })
            else:
                comparison_results['missing_verses'].append({
                    'verse_number': verse_num,
                    'detected': detected_content,
                    'actual': actual_verse,
                    'similarity': similarity
                })
        else:
            comparison_results['extra_verses'].append(verse_num)
    
    # Calculate accuracy score
    total_actual = len(actual_verses_dict)
    total_detected = len(detected_verses)
    matches = len(comparison_results['matches'])
    
    if total_actual > 0:
        comparison_results['accuracy_score'] = matches / total_actual
    
    return comparison_results

def parse_image_filename(image_name: str):
    """Parse filenames like 'book_13(19-22)_14(1-5)' into expected chapter/verse ranges.

    Supports numbered books without spaces (e.g., '2samuel') and multi-chapter pages.

    Returns a dict:
      {
        'book': '2samuel',
        'chapters': [
            {'chapter': 19, 'verses': (42, 43)},
            {'chapter': 20, 'verses': (1, 9)}
        ],
        'expected_verses_union': set([...])  # union of all verse numbers across chapters
      }
    """
    # Strip extension if present
    base = image_name
    for ext in ('.jpeg', '.jpg', '.png'):
        if base.lower().endswith(ext):
            base = base[: -len(ext)]
            break

    if '_' not in base:
        return None

    # Split on first underscore: book vs chapter specs
    first_us = base.find('_')
    book = base[:first_us].lower()
    tail = base[first_us + 1:]

    # Find all chapter(range) specs like 13(19-22) or 3(31)
    # Pattern: chapter digits, then '(', then start, optional '-end', then ')'
    pattern = re.compile(r"(\d+)\((\d+)(?:-(\d+))?\)")
    chapters = []
    expected_union = set()

    for match in pattern.finditer(tail):
        chapter_str, start_str, end_str = match.groups()
        chapter = int(chapter_str)
        start = int(start_str)
        end = int(end_str) if end_str else start

        chapters.append({'chapter': chapter, 'verses': (start, end)})
        expected_union.update(range(start, end + 1))

    if not chapters:
        return None

    return {
        'book': book,
        'chapters': chapters,
        'expected_verses_union': expected_union,
    }

def _extract_detected_verse_number(verse_token: str):
    """Map detected verse tokens to an integer verse number if possible.

    Handles formats like '17', '1:3', 'Psalm 139:1'. Returns None if not parseable.
    """
    token = verse_token.strip()
    # Fast path: simple number
    if token.isdigit():
        try:
            return int(token)
        except ValueError:
            return None

    # If contains a colon, attempt to parse the part after the last ':'
    if ':' in token:
        try:
            verse_part = token.split(':')[-1]
            return int(verse_part)
        except ValueError:
            return None

    return None

def compare_with_expected_ranges(detected_verses, expected_spec):
    """Compare detected verse numbers to expected ranges parsed from filename.

    detected_verses: list of strings from detector (e.g., ['17', '18', 'Psalm 140:2'])
    expected_spec: dict from parse_image_filename
    """
    expected_set = set(expected_spec.get('expected_verses_union', set()))

    parsed_detected = []
    for v in detected_verses:
        num = _extract_detected_verse_number(v)
        if num is not None:
            parsed_detected.append(num)

    detected_set = set(parsed_detected)
    matches = sorted(expected_set.intersection(detected_set))
    missing = sorted(expected_set.difference(detected_set))
    extras = sorted(detected_set.difference(expected_set))

    accuracy = (len(matches) / len(expected_set)) if expected_set else 0.0

    return {
        'book': expected_spec['book'],
        'chapters': expected_spec['chapters'],
        'expected_verses': sorted(expected_set),
        'detected_verses_numeric': sorted(detected_set),
        'matches': matches,
        'missing_verses': missing,
        'extra_detected_verses': extras,
        'accuracy_score_numeric': accuracy,
    }

def calculate_similarity(text1, text2):
    """Calculate similarity between two texts (simple implementation)"""
    if not text1 or not text2:
        return 0.0
    
    # Convert to lowercase and split into words
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0

def main():
    """Main function to process all images in Photos folder"""
    logging.info("Starting comprehensive verse detection test")
    
    photos_dir = "Photos"
    results = {}
    
    # Process each image in the Photos folder
    for filename in os.listdir(photos_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            image_path = os.path.join(photos_dir, filename)
            image_name = filename.replace('.jpeg', '').replace('.jpg', '').replace('.png', '')
            
            logging.info(f"Processing {filename}")
            
            # Process the image
            result = process_image(image_path)
            if result:
                results[image_name] = result
                
                # Compare with actual verses when textual ground truth exists
                if image_name in ACTUAL_VERSES:
                    comparison = compare_with_actual_verses(
                        result['high_confidence_verse_numbers'],
                        ACTUAL_VERSES,
                        image_name,
                        result['all_text'] # Pass all_text to the comparison function
                    )
                    results[image_name]['comparison'] = comparison
                
                # Fallback: use filename to compute expected numeric ranges
                parsed = parse_image_filename(filename)
                if parsed:
                    numeric_comp = compare_with_expected_ranges(
                        result['high_confidence_verse_numbers'],
                        parsed
                    )
                    results[image_name]['expected_from_filename'] = parsed
                    results[image_name]['expected_comparison'] = numeric_comp
                
                # Log detailed results
                logging.info(f"Results for {image_name}:")
                logging.info(f"  - Total verse blocks: {result['verse_blocks']}")
                logging.info(f"  - High confidence blocks: {result['high_confidence_blocks']}")
                logging.info(f"  - Average confidence: {result['average_confidence']:.3f}")
                logging.info(f"  - Average content quality: {result['average_content_quality']:.3f}")
                logging.info(f"  - High confidence verses: {result['high_confidence_verse_numbers']}")
                
                # Log detailed significance scores for each verse
                logging.info(f"  - Detailed verse analysis:")
                for verse_detail in result['verse_details']:
                    status = "✅ HIGH" if verse_detail['is_high_confidence'] else "⚠️  LOW"
                    page_boundary = "🔗 PAGE_BOUNDARY" if verse_detail['is_page_boundary'] else ""
                    ocr_artifact = "🖨️  OCR_ARTIFACT" if verse_detail['is_ocr_artifact'] else ""
                    
                    logging.info(f"    {status} Verse {verse_detail['verse_number']}: "
                               f"confidence={verse_detail['confidence']:.3f}, "
                               f"quality={verse_detail['quality_score']:.3f} "
                               f"{page_boundary} {ocr_artifact}")
                    logging.info(f"      Content: '{verse_detail['content'][:100]}{'...' if len(verse_detail['content']) > 100 else ''}'")
                
                if 'comparison' in results[image_name]:
                    comp = results[image_name]['comparison']
                    logging.info(f"  - Accuracy score: {comp['accuracy_score']:.3f}")
                    logging.info(f"  - Matches: {len(comp['matches'])}")
                    logging.info(f"  - Partial matches: {len(comp['partial_matches'])}")
                    logging.info(f"  - Missing verses: {len(comp['missing_verses'])}")
                    logging.info(f"  - Extra verses: {len(comp['extra_verses'])}")
                    
                    # Log detailed comparison results
                    if comp['matches']:
                        logging.info(f"  - Exact matches:")
                        for match in comp['matches']:
                            logging.info(f"    Verse {match['verse_number']}: similarity={match['similarity']:.3f}")
                    
                    if comp['partial_matches']:
                        logging.info(f"  - Partial matches:")
                        for match in comp['partial_matches']:
                            logging.info(f"    Verse {match['verse_number']}: similarity={match['similarity']:.3f}")
                    
                    if comp['missing_verses']:
                        logging.info(f"  - Missing verses:")
                        for missing in comp['missing_verses']:
                            logging.info(f"    Verse {missing['verse_number']}: similarity={missing['similarity']:.3f}")
                    
                    if comp['extra_verses']:
                        logging.info(f"  - Extra verses: {comp['extra_verses']}")
                
                if 'expected_comparison' in results[image_name]:
                    ncomp = results[image_name]['expected_comparison']
                    ch_list = ", ".join(
                        [f"{c['chapter']}({c['verses'][0]}-{c['verses'][1]})" for c in ncomp['chapters']]
                    )
                    logging.info(f"  - Expected (filename): chapters {ch_list}")
                    logging.info(f"  - Numeric accuracy: {ncomp['accuracy_score_numeric']:.3f}")
                    logging.info(f"  - Numeric matches: {len(ncomp['matches'])}")
                    logging.info(f"  - Numeric missing: {len(ncomp['missing_verses'])}")
                    logging.info(f"  - Numeric extras: {len(ncomp['extra_detected_verses'])}")
    
    # Save results to JSON file
    with open('verse_detection_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Print summary
    print("\n" + "="*60)
    print("COMPREHENSIVE VERSE DETECTION TEST SUMMARY")
    print("="*60)
    
    for image_name, result in results.items():
        print(f"\n📖 {image_name.upper()}")
        print(f"   Total verses detected: {result['verse_blocks']}")
        print(f"   High confidence verses: {result['high_confidence_blocks']}")
        print(f"   Average confidence: {result['average_confidence']:.3f}")
        print(f"   Average content quality: {result['average_content_quality']:.3f}")
        
        if 'comparison' in result:
            comp = result['comparison']
            print(f"   Accuracy vs actual verses: {comp['accuracy_score']:.1%}")
            print(f"   Exact matches: {len(comp['matches'])}")
            print(f"   Partial matches: {len(comp['partial_matches'])}")
            print(f"   Missing verses: {len(comp['missing_verses'])}")
            print(f"   Extra verses: {len(comp['extra_verses'])}")

        if 'expected_comparison' in result:
            ncomp = result['expected_comparison']
            ch_list = ", ".join(
                [f"{c['chapter']}({c['verses'][0]}-{c['verses'][1]})" for c in ncomp['chapters']]
            )
            print(f"   Expected from filename: {result['expected_from_filename']['book']} {ch_list}")
            print(f"   Numeric accuracy (vs. filename ranges): {ncomp['accuracy_score_numeric']:.1%}")
            print(f"   Numeric matches: {len(ncomp['matches'])}")
            print(f"   Numeric missing: {len(ncomp['missing_verses'])}")
            print(f"   Numeric extras: {len(ncomp['extra_detected_verses'])}")
        
        print(f"   High confidence verse numbers: {result['high_confidence_verse_numbers']}")
        
        # Print detailed significance scores for high-confidence verses
        if result['verse_details']:
            print(f"\n   📊 SIGNIFICANCE SCORES (High-Confidence Verses):")
            high_confidence_details = [v for v in result['verse_details'] if v['is_high_confidence']]
            for verse_detail in high_confidence_details:
                status_icons = []
                if verse_detail['is_page_boundary']:
                    status_icons.append("🔗")
                if verse_detail['is_ocr_artifact']:
                    status_icons.append("🖨️")
                
                status_str = " ".join(status_icons) if status_icons else ""
                print(f"     Verse {verse_detail['verse_number']}: "
                      f"confidence={verse_detail['confidence']:.3f}, "
                      f"quality={verse_detail['quality_score']:.3f} {status_str}")
                print(f"       Content: '{verse_detail['content'][:80]}{'...' if len(verse_detail['content']) > 80 else ''}'")
    
    logging.info("Comprehensive test completed. Results saved to verse_detection_results.json")

if __name__ == "__main__":
    main()
