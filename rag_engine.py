"""
RAG (Retrieval-Augmented Generation) engine for the chatbot
"""
import os
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
    
    def __init__(self):
        """Initialize RAG engine with vector store and LLM"""
        try:
            # Initialize embeddings
            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=config.OPENAI_API_KEY
            )
            
            # Load vector database
            if not os.path.exists(config.VECTOR_DB_PATH):
                raise FileNotFoundError(
                    f"Vector database not found at {config.VECTOR_DB_PATH}. "
                    "Please run knowledge_base/builder.py first."
                )
            
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

