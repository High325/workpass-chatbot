"""
Build and populate the vector database with processed knowledge base
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from knowledge_base.scraper import MOMScraper
from knowledge_base.processor import DataProcessor
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from typing import List, Dict
import config
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeBaseBuilder:
    """Build the knowledge base from MOM website data"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=config.OPENAI_API_KEY
        )
        self.vector_store = None
        
    def build_from_scraping(self, max_pages: int = 50, save_raw: bool = True):
        """Build knowledge base by scraping MOM website"""
        logger.info("Starting knowledge base building process...")
        
        # Step 1: Scrape MOM website
        logger.info("Step 1: Scraping MOM website...")
        scraper = MOMScraper(config.MOM_BASE_URL)
        scraped_data = scraper.scrape_all(max_pages=max_pages)
        
        if save_raw:
            scraper.save_to_json("mom_data.json")
            logger.info("Saved raw scraped data to mom_data.json")
        
        if not scraped_data:
            logger.error("No data scraped. Please check your internet connection and MOM website accessibility.")
            return False
        
        # Step 2: Process scraped data
        logger.info("Step 2: Processing scraped data...")
        processor = DataProcessor(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP
        )
        # Process with flexible categorization (categories parameter is optional)
        processed_chunks = processor.process_scraped_data(
            scraped_data,
            categories=config.WORK_PASS_CATEGORIES  # Optional reference, not enforced
        )
        
        processor.save_processed_data(processed_chunks, "processed_knowledge_base.json")
        logger.info("Saved processed data to processed_knowledge_base.json")
        
        # Step 3: Create vector database
        logger.info("Step 3: Creating vector database...")
        self.create_vector_db(processed_chunks)
        
        logger.info("Knowledge base building completed successfully!")
        return True
    
    def build_from_processed_file(self, filename: str = "processed_knowledge_base.json"):
        """Build knowledge base from existing processed JSON file"""
        logger.info(f"Loading processed data from {filename}...")
        
        processor = DataProcessor()
        processed_chunks = processor.load_from_json(filename)
        
        logger.info("Creating vector database...")
        self.create_vector_db(processed_chunks)
        
        logger.info("Knowledge base building completed successfully!")
        return True
    
    def create_vector_db(self, processed_chunks: List[dict]):
        """Create and populate ChromaDB vector database"""
        import time
        
        # Convert to LangChain Documents and clean metadata
        documents = []
        for chunk in processed_chunks:
            # Clean metadata - convert complex types to strings
            metadata = chunk['metadata'].copy()
            
            # Convert headings list to string if it exists
            if 'headings' in metadata and isinstance(metadata['headings'], list):
                # Convert list of dicts to a readable string
                headings_str = "; ".join([f"{h.get('level', '')}: {h.get('text', '')}" for h in metadata['headings']])
                metadata['headings'] = headings_str
            
            # Filter out any remaining complex metadata types
            cleaned_metadata = {}
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)) or value is None:
                    cleaned_metadata[key] = value
                elif isinstance(value, list):
                    # Convert lists to string
                    cleaned_metadata[key] = json.dumps(value) if value else ""
                elif isinstance(value, dict):
                    # Convert dicts to string
                    cleaned_metadata[key] = json.dumps(value)
                # Skip other complex types
            
            doc = Document(
                page_content=chunk['text'],
                metadata=cleaned_metadata
            )
            documents.append(doc)
        
        # Create vector store with retry logic for rate limits
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Creating vector database (attempt {attempt + 1}/{max_retries})...")
                self.vector_store = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    persist_directory=config.VECTOR_DB_PATH,
                    collection_name=config.COLLECTION_NAME
                )
                break
            except Exception as e:
                if "429" in str(e) or "rate" in str(e).lower() or "quota" in str(e).lower():
                    if attempt < max_retries - 1:
                        logger.warning(f"Rate limit hit. Waiting {retry_delay} seconds before retry...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        raise Exception(f"Failed after {max_retries} attempts due to rate limits. Please check your OpenAI API quota.")
                else:
                    raise
        
        logger.info(f"Created vector database with {len(documents)} documents")
        logger.info(f"Vector DB saved to: {config.VECTOR_DB_PATH}")
    
    def load_vector_db(self):
        """Load existing vector database"""
        if not os.path.exists(config.VECTOR_DB_PATH):
            logger.error(f"Vector database not found at {config.VECTOR_DB_PATH}")
            return None
        
        self.vector_store = Chroma(
            persist_directory=config.VECTOR_DB_PATH,
            embedding_function=self.embeddings,
            collection_name=config.COLLECTION_NAME
        )
        
        logger.info("Vector database loaded successfully")
        return self.vector_store

def main():
    """Main function to build knowledge base"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Build knowledge base for Singapore Work Pass Chatbot')
    parser.add_argument('--from-file', type=str, help='Build from processed JSON file instead of scraping')
    parser.add_argument('--max-pages', type=int, default=50, help='Maximum pages to scrape')
    
    args = parser.parse_args()
    
    builder = KnowledgeBaseBuilder()
    
    if args.from_file:
        success = builder.build_from_processed_file(args.from_file)
    else:
        success = builder.build_from_scraping(max_pages=args.max_pages)
    
    if success:
        logger.info("Knowledge base is ready to use!")
    else:
        logger.error("Failed to build knowledge base")

if __name__ == "__main__":
    main()

