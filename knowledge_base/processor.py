"""
Process and structure scraped MOM data into categorized knowledge base
"""
import json
import re
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    """Process scraped data into structured knowledge base chunks"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
    
    def categorize_content(self, content: Dict, categories: Dict = None) -> str:
        """Categorize content based on keywords and URL patterns - flexible categorization"""
        url_lower = content['url'].lower()
        text_lower = content['content'].lower()
        title_lower = content['title'].lower()
        combined_text = f"{url_lower} {text_lower} {title_lower}"
        
        # Extract pass type from content - flexible keyword detection
        pass_type_keywords = {
            "employment_pass": ["employment pass", "ep", "employmentpass"],
            "pep": ["personalised employment pass", "pep", "personalized employment pass"],
            "entrepass": ["entrepass", "entrepreneur pass"],
            "s_pass": ["s pass", "s-pass", "spass"],
            "work_permit": ["work permit", "workpermit"],
            "fdw": ["foreign domestic worker", "fdw", "domestic worker", "domestic helper"],
            "performing_artiste": ["performing artiste", "performing artist"],
            "confinement_nanny": ["confinement nanny", "confinement"],
            "training_pass": ["training employment pass", "training pass"],
            "work_holiday": ["work holiday pass", "work holiday"],
            "dependant": ["dependant", "dependent", "dependant pass"],
            "ltvp": ["ltvp", "long-term visit pass", "long term visit pass"]
        }
        
        # Find the most relevant pass type
        pass_type_scores = {}
        for pass_type, keywords in pass_type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            if score > 0:
                pass_type_scores[pass_type] = score
        
        # Determine category based on pass type or content structure
        if pass_type_scores:
            # Get the pass type with highest score
            detected_pass = max(pass_type_scores, key=pass_type_scores.get)
            
            # Group into broader categories for organization (but keep flexibility)
            if detected_pass in ["employment_pass", "pep", "entrepass"]:
                return "employment_passes"
            elif detected_pass in ["s_pass", "work_permit"]:
                return "work_permits"
            elif detected_pass in ["fdw", "performing_artiste", "confinement_nanny"]:
                return "sector_specific"
            elif detected_pass in ["training_pass", "work_holiday", "dependant", "ltvp"]:
                return "other_passes"
            else:
                return detected_pass
        
        # If no specific pass type detected, categorize by content type
        if "eligibility" in combined_text or "requirements" in combined_text:
            return "eligibility_requirements"
        elif "application" in combined_text or "apply" in combined_text:
            return "application_process"
        elif "renew" in combined_text or "renewal" in combined_text:
            return "renewal"
        elif "fee" in combined_text or "cost" in combined_text or "price" in combined_text:
            return "fees"
        else:
            return "general"
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\:\;\(\)\-\']', ' ', text)
        # Remove multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    
    def process_scraped_data(self, scraped_data: List[Dict], categories: Dict = None) -> List[Dict]:
        """Process scraped data into structured chunks with flexible categorization"""
        processed_chunks = []
        
        for page_data in scraped_data:
            # Clean content
            cleaned_content = self.clean_text(page_data['content'])
            
            # Categorize (flexible - doesn't require predefined categories)
            category = self.categorize_content(page_data, categories)
            
            # Extract pass type from title/URL if available
            pass_type = self._extract_pass_type(page_data)
            
            # Split into chunks
            chunks = self.text_splitter.split_text(cleaned_content)
            
            # Create metadata for each chunk
            for i, chunk in enumerate(chunks):
                chunk_metadata = {
                    'source': page_data['url'],
                    'title': page_data['title'],
                    'category': category,
                    'pass_type': pass_type,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'headings': page_data.get('headings', [])
                }
                
                processed_chunks.append({
                    'text': chunk,
                    'metadata': chunk_metadata
                })
        
        logger.info(f"Processed {len(scraped_data)} pages into {len(processed_chunks)} chunks")
        return processed_chunks
    
    def _extract_pass_type(self, page_data: Dict) -> str:
        """Extract specific pass type from page data"""
        url_lower = page_data['url'].lower()
        title_lower = page_data['title'].lower()
        combined = f"{url_lower} {title_lower}"
        
        # Common pass type patterns
        pass_types = {
            "Employment Pass": ["employment pass", "ep"],
            "Personalised Employment Pass": ["pep", "personalised employment pass"],
            "EntrePass": ["entrepass"],
            "S Pass": ["s pass", "s-pass"],
            "Work Permit": ["work permit"],
            "Foreign Domestic Worker": ["fdw", "foreign domestic worker", "domestic worker"],
            "Performing Artiste": ["performing artiste"],
            "Confinement Nanny": ["confinement nanny"],
            "Training Employment Pass": ["training employment pass"],
            "Work Holiday Pass": ["work holiday pass"],
            "Dependant's Pass": ["dependant", "dependent"],
            "Long-Term Visit Pass": ["ltvp", "long-term visit pass"]
        }
        
        for pass_name, keywords in pass_types.items():
            if any(keyword in combined for keyword in keywords):
                return pass_name
        
        return "General"
    
    def load_from_json(self, filename: str) -> List[Dict]:
        """Load scraped data from JSON file"""
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_processed_data(self, processed_chunks: List[Dict], filename: str = "processed_knowledge_base.json"):
        """Save processed chunks to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(processed_chunks, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(processed_chunks)} processed chunks to {filename}")

