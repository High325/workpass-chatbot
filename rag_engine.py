"""
RAG (Retrieval-Augmented Generation) engine for the chatbot
"""
import os
import sys
from pathlib import Path
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from typing import List, Dict, Tuple
import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGEngine:
    """RAG engine for retrieving and generating responses about Singapore work passes"""
    
    def __init__(self, auto_build: bool = True):
        """
        Initialize RAG engine with vector store and LLM
        
        Args:
            auto_build: If True, automatically build knowledge base if it doesn't exist
        """
        try:
            # Initialize embeddings
            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=config.OPENAI_API_KEY
            )
            
            # Load or build vector database
            if not os.path.exists(config.VECTOR_DB_PATH):
                if auto_build:
                    logger.info("Vector database not found. Attempting to build from processed data...")
                    self._auto_build_knowledge_base()
                else:
                    raise FileNotFoundError(
                        f"Vector database not found at {config.VECTOR_DB_PATH}. "
                        "Please run knowledge_base/builder.py first."
                    )
            
            # Load vector store (either newly created or existing)
            if not hasattr(self, 'vector_store') or self.vector_store is None:
                self.vector_store = Chroma(
                    persist_directory=config.VECTOR_DB_PATH,
                    embedding_function=self.embeddings,
                    collection_name=config.COLLECTION_NAME
                )
            
            # Initialize LLM
            self.llm = ChatOpenAI(
                model_name=config.OPENAI_MODEL,
                temperature=0.3,
                openai_api_key=config.OPENAI_API_KEY
            )
            
            # Create retriever
            self.retriever = self.vector_store.as_retriever(
                search_kwargs={"k": 5}  # Retrieve top 5 relevant chunks
            )
            
            # Create custom prompt template
            self.prompt_template = PromptTemplate(
                input_variables=["context", "question"],
                template="""You are a helpful assistant that provides accurate information about Singapore work passes based on official Ministry of Manpower (MOM) sources.

Use the following context from official MOM sources to answer the question. If the answer is not in the context, say so clearly and suggest the user visit the official MOM website for more information.

Context from MOM sources:
{context}

Question: {question}

Provide a clear, accurate, and helpful answer based on the context above. If relevant, mention the specific pass type(s) and include key details like eligibility requirements, application process, or fees if mentioned in the context.

Answer:"""
            )
            
            # Create RAG chain using LCEL
            def format_docs(docs):
                return "\n\n".join(doc.page_content for doc in docs)
            
            self.qa_chain = (
                {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
                | self.prompt_template
                | self.llm
                | StrOutputParser()
            )
            
            logger.info("RAG engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing RAG engine: {str(e)}")
            raise
    
    def _auto_build_knowledge_base(self):
        """Automatically build knowledge base from processed_knowledge_base.json if available"""
        processed_file = "processed_knowledge_base.json"
        
        if not os.path.exists(processed_file):
            raise FileNotFoundError(
                f"Vector database not found and {processed_file} is also missing. "
                "Please ensure processed_knowledge_base.json exists in the project root, "
                "or run knowledge_base/builder.py to create it."
            )
        
        try:
            # Import builder components
            from knowledge_base.processor import DataProcessor
            import json
            import time
            
            logger.info(f"Loading processed data from {processed_file}...")
            
            # Load processed chunks
            processor = DataProcessor()
            processed_chunks = processor.load_from_json(processed_file)
            
            logger.info(f"Found {len(processed_chunks)} processed chunks. Creating vector database...")
            
            # Convert to LangChain Documents
            documents = []
            for chunk in processed_chunks:
                # Clean metadata - convert complex types to strings
                metadata = chunk['metadata'].copy()
                
                # Convert headings list to string if it exists
                if 'headings' in metadata and isinstance(metadata['headings'], list):
                    headings_str = "; ".join([f"{h.get('level', '')}: {h.get('text', '')}" for h in metadata['headings']])
                    metadata['headings'] = headings_str
                
                # Filter out any remaining complex metadata types
                cleaned_metadata = {}
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)) or value is None:
                        cleaned_metadata[key] = value
                    elif isinstance(value, list):
                        cleaned_metadata[key] = json.dumps(value) if value else ""
                    elif isinstance(value, dict):
                        cleaned_metadata[key] = json.dumps(value)
                
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
                    logger.info(f"Successfully created vector database with {len(documents)} documents")
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
            
        except Exception as e:
            logger.error(f"Error auto-building knowledge base: {str(e)}")
            raise Exception(
                f"Failed to auto-build knowledge base: {str(e)}. "
                "Please run 'python knowledge_base/builder.py --from-file processed_knowledge_base.json' manually."
            )
    
    def query(self, question: str, user_context: Dict = None) -> Dict:
        """
        Query the RAG system with a question
        
        Args:
            question: User's question
            user_context: Optional user context (e.g., nationality, salary, etc.)
        
        Returns:
            Dictionary with answer, sources, and metadata
        """
        try:
            # Enhance question with user context if provided
            enhanced_question = question
            if user_context:
                context_str = ", ".join([f"{k}: {v}" for k, v in user_context.items() if v])
                if context_str:
                    enhanced_question = f"{question} (User context: {context_str})"
            
            # Retrieve relevant documents for source citations
            docs = self.retriever.invoke(enhanced_question)
            
            # Query the chain
            answer = self.qa_chain.invoke(enhanced_question)
            
            # Extract sources from retrieved documents
            sources = []
            for doc in docs:
                source_info = {
                    "title": doc.metadata.get("title", "Unknown"),
                    "url": doc.metadata.get("source", ""),
                    "pass_type": doc.metadata.get("pass_type", "General"),
                    "category": doc.metadata.get("category", "general")
                }
                sources.append(source_info)
            
            return {
                "answer": answer,
                "sources": sources,
                "question": question
            }
            
        except Exception as e:
            logger.error(f"Error querying RAG engine: {str(e)}")
            return {
                "answer": f"I encountered an error: {str(e)}. Please try again.",
                "sources": [],
                "question": question
            }
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Search the knowledge base and return relevant documents
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of relevant documents with metadata
        """
        try:
            # Search vector store
            docs = self.vector_store.similarity_search_with_score(query, k=top_k)
            
            results = []
            for doc, score in docs:
                results.append({
                    "text": doc.page_content,
                    "title": doc.metadata.get("title", "Unknown"),
                    "url": doc.metadata.get("source", ""),
                    "pass_type": doc.metadata.get("pass_type", "General"),
                    "category": doc.metadata.get("category", "general"),
                    "relevance_score": float(score)
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            return []
    
    def get_pass_types(self) -> List[str]:
        """Get list of all unique pass types in the knowledge base"""
        try:
            # Get all documents metadata
            collection = self.vector_store._collection
            all_metadata = collection.get()["metadatas"]
            
            pass_types = set()
            for metadata in all_metadata:
                pass_type = metadata.get("pass_type", "General")
                if pass_type and pass_type != "General":
                    pass_types.add(pass_type)
            
            return sorted(list(pass_types))
            
        except Exception as e:
            logger.error(f"Error getting pass types: {str(e)}")
            return []
    
    def get_categories(self) -> List[str]:
        """Get list of all unique categories in the knowledge base"""
        try:
            collection = self.vector_store._collection
            all_metadata = collection.get()["metadatas"]
            
            categories = set()
            for metadata in all_metadata:
                category = metadata.get("category", "general")
                if category:
                    categories.add(category)
            
            return sorted(list(categories))
            
        except Exception as e:
            logger.error(f"Error getting categories: {str(e)}")
            return []

