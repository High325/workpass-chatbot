"""
Main Streamlit application for Singapore Work Pass Chatbot
"""
import streamlit as st
import os
from pathlib import Path
import sys
from dotenv import load_dotenv
import pandas as pd
from rag_engine import RAGEngine
import config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Singapore Work Pass Assistant",
    page_icon="🇸🇬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
    .source-link {
        color: #1976d2;
        text-decoration: none;
    }
    .source-link:hover {
        text-decoration: underline;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'rag_engine' not in st.session_state:
    st.session_state.rag_engine = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    """Simple password protection"""
    if not st.session_state.authenticated:
        st.title("🔒 Singapore Work Pass Assistant")
        password = st.text_input("Enter password to access the application", type="password")
        
        # Default password - should be changed in production
        correct_password = os.getenv("APP_PASSWORD", "workpass2024")
        
        if st.button("Login"):
            if password == correct_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password. Please try again.")
        return False
    return True

def initialize_rag_engine():
    """Initialize RAG engine if not already initialized"""
    if st.session_state.rag_engine is None:
        try:
            with st.spinner("Loading knowledge base..."):
                st.session_state.rag_engine = RAGEngine()
            return True
        except Exception as e:
            st.error(f"Error initializing RAG engine: {str(e)}")
            st.info("Please ensure you have built the knowledge base by running: `python knowledge_base/builder.py`")
            return False
    return True

def chat_page():
    """Main chat interface page"""
    st.markdown('<h1 class="main-header">🇸🇬 Singapore Work Pass Assistant</h1>', unsafe_allow_html=True)
    st.markdown("### Ask questions about Singapore work passes")
    
    if not initialize_rag_engine():
        return
    
    # User context sidebar
    with st.sidebar:
        st.header("📋 Your Profile (Optional)")
        st.markdown("Provide context to get personalized answers")
        
        nationality = st.selectbox(
            "Nationality",
            ["Select...", "Singaporean", "Malaysian", "Indian", "Chinese", "Filipino", "Indonesian", "Other"]
        )
        
        current_pass = st.selectbox(
            "Current Pass Type (if any)",
            ["None", "Employment Pass", "S Pass", "Work Permit", "Student Pass", "Other"]
        )
        
        salary_range = st.selectbox(
            "Expected Salary Range (SGD)",
            ["Select...", "Below 3,000", "3,000 - 5,000", "5,000 - 10,000", "10,000 - 15,000", "Above 15,000"]
        )
        
        user_context = {}
        if nationality != "Select...":
            user_context["nationality"] = nationality
        if current_pass != "None":
            user_context["current_pass"] = current_pass
        if salary_range != "Select...":
            user_context["salary_range"] = salary_range
    
    # Chat interface
    st.markdown("---")
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message assistant-message"><strong>Assistant:</strong> {message["content"]}</div>', unsafe_allow_html=True)
            
            # Show sources if available
            if "sources" in message and message["sources"]:
                with st.expander("📚 Sources"):
                    for i, source in enumerate(message["sources"][:3], 1):
                        st.markdown(f"{i}. **{source['title']}**")
                        if source['url']:
                            st.markdown(f"   [View source]({source['url']})")
                        if source['pass_type'] != "General":
                            st.caption(f"Pass Type: {source['pass_type']}")
    
    # Chat input
    user_question = st.chat_input("Ask a question about Singapore work passes...")
    
    if user_question:
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": user_question})
        
        # Get response from RAG engine
        with st.spinner("Thinking..."):
            result = st.session_state.rag_engine.query(user_question, user_context)
        
        # Add assistant response to history
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"]
        })
        
        st.rerun()

def search_page():
    """Intelligent search page"""
    st.markdown('<h1 class="main-header">🔍 Intelligent Search</h1>', unsafe_allow_html=True)
    st.markdown("### Search the knowledge base for specific information")
    
    if not initialize_rag_engine():
        return
    
    # Search interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input("Enter your search query", placeholder="e.g., Employment Pass eligibility requirements")
    
    with col2:
        num_results = st.number_input("Results", min_value=5, max_value=20, value=10, step=5)
    
    if st.button("Search", type="primary") or search_query:
        if search_query:
            with st.spinner("Searching knowledge base..."):
                results = st.session_state.rag_engine.search(search_query, top_k=num_results)
            
            if results:
                st.markdown(f"### Found {len(results)} relevant results")
                
                # Display results
                for i, result in enumerate(results, 1):
                    with st.expander(f"Result {i}: {result['title']} (Relevance: {result['relevance_score']:.3f})"):
                        st.markdown(f"**Pass Type:** {result['pass_type']}")
                        st.markdown(f"**Category:** {result['category']}")
                        st.markdown(f"**Source:** [{result['title']}]({result['url']})")
                        st.markdown("---")
                        st.markdown(result['text'])
            else:
                st.info("No results found. Try a different search query.")
        else:
            st.warning("Please enter a search query")


def about_page():
    """About Us page"""
    st.markdown('<h1 class="main-header">ℹ️ About Us</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    ## Project Overview
    
    The Singapore Work Pass Assistant is an LLM-powered web application designed to help citizens 
    and foreign workers understand Singapore work passes by providing accurate, up-to-date information 
    from official Ministry of Manpower (MOM) sources.
    
    ## Objectives
    
    1. **Consolidate Information**: Aggregate data from official MOM sources to provide a unified 
       repository of work pass information
    
    2. **Personalize User Experience**: Allow users to provide context (nationality, salary range, etc.) 
       to receive tailored guidance relevant to their specific scenarios
    
    3. **Enhance Understanding**: Generate interactive content, explanations, and responses to 
       follow-up questions to facilitate deeper comprehension
    
    4. **Present Information Effectively**: Present information through various formats including 
       text, tables, visualizations, and interactive forms
    
    ## Data Sources
    
    All information is retrieved from official and publicly accessible sources:
    
    - **Ministry of Manpower Singapore (MOM)**: https://www.mom.gov.sg
    - **MOM Passes and Permits Portal**: https://www.mom.gov.sg/passes-and-permits
    
    The knowledge base is built by scraping and processing official MOM web pages to ensure 
    accuracy and reliability.
    
    ## Features
    
    ### 1. Chat Interface
    - Interactive Q&A powered by RAG (Retrieval-Augmented Generation)
    - Context-aware responses based on user profile
    - Source citations for transparency
    
    ### 2. Intelligent Search
    - Semantic search across the knowledge base
    - Relevance-ranked results
    - Detailed document previews
    
    ### 3. Personalized Guidance
    - User profile collection (nationality, current pass, salary range)
    - Contextualized responses
    - Scenario-specific information
    
    ## Technology Stack
    
    - **Frontend**: Streamlit
    - **LLM**: OpenAI GPT-4o-mini
    - **Vector Database**: ChromaDB
    - **Embeddings**: OpenAI text-embedding-3-small
    - **RAG Framework**: LangChain
    
    ## Work Pass Coverage
    
    The application covers information about:
    
    - Employment Pass (EP)
    - Personalised Employment Pass (PEP)
    - EntrePass
    - S Pass
    - Work Permits (various types)
    - Foreign Domestic Worker (FDW) permits
    - Training Employment Pass
    - Work Holiday Pass
    - Dependant's Pass
    - Long-Term Visit Pass (LTVP)
    - And other related passes and permits
    
    ## Disclaimer
    
    This application provides information based on publicly available MOM sources. For official 
    applications, renewals, or specific queries, users should always refer to the official 
    MOM website or contact MOM directly.
    """)

def methodology_page():
    """Methodology page with flowcharts"""
    st.markdown('<h1 class="main-header">🔬 Methodology</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    ## System Architecture
    
    The application uses a Retrieval-Augmented Generation (RAG) architecture to provide accurate 
    answers about Singapore work passes.
    """)
    
    # Use Case 1: Chat with Information
    st.markdown("### Use Case 1: Chat with Information")
    
    st.markdown("""
    **Process Flow:**
    
    1. User submits a question through the chat interface
    2. Optional user context (nationality, salary, etc.) is collected
    3. Question is enhanced with user context
    4. RAG engine performs semantic search in vector database
    5. Top 5 relevant document chunks are retrieved
    6. Retrieved context is passed to LLM with prompt template
    7. LLM generates answer based on retrieved context
    8. Answer and source citations are returned to user
    9. Conversation history is maintained for context
    """)
    
    # Simple flowchart representation using text
    st.code("""
    ┌─────────────┐
    │ User Query  │
    └──────┬──────┘
           │
           ▼
    ┌─────────────────────┐
    │ Collect User Context│
    │ (Optional)          │
    └──────┬──────────────┘
           │
           ▼
    ┌─────────────────────┐
    │ Enhance Query       │
    │ with Context        │
    └──────┬──────────────┘
           │
           ▼
    ┌─────────────────────┐
    │ Vector DB Search    │
    │ (Semantic Search)   │
    └──────┬──────────────┘
           │
           ▼
    ┌─────────────────────┐
    │ Retrieve Top 5      │
    │ Relevant Chunks      │
    └──────┬──────────────┘
           │
           ▼
    ┌─────────────────────┐
    │ LLM Generation      │
    │ (with Context)      │
    └──────┬──────────────┘
           │
           ▼
    ┌─────────────────────┐
    │ Return Answer +     │
    │ Source Citations    │
    └─────────────────────┘
    """, language="text")
    
    st.markdown("---")
    
    # Use Case 2: Intelligent Search
    st.markdown("### Use Case 2: Intelligent Search")
    
    st.markdown("""
    **Process Flow:**
    
    1. User enters search query
    2. Query is converted to embedding vector
    3. Similarity search performed in vector database
    4. Top K most relevant documents retrieved (default: 10)
    5. Results ranked by relevance score
    6. Documents displayed with metadata (title, URL, pass type, category)
    7. User can expand each result to view full content
    """)
    
    st.code("""
    ┌─────────────┐
    │ Search Query│
    └──────┬──────┘
           │
           ▼
    ┌─────────────────────┐
    │ Convert to          │
    │ Embedding Vector    │
    └──────┬──────────────┘
           │
           ▼
    ┌─────────────────────┐
    │ Similarity Search   │
    │ in Vector DB        │
    └──────┬──────────────┘
           │
           ▼
    ┌─────────────────────┐
    │ Rank by Relevance   │
    │ Score               │
    └──────┬──────────────┘
           │
           ▼
    ┌─────────────────────┐
    │ Return Top K        │
    │ Results with        │
    │ Metadata            │
    └─────────────────────┘
    """, language="text")
    
    st.markdown("---")
    
    # Data Flow
    st.markdown("### Knowledge Base Building Process")
    
    st.markdown("""
    **Data Flow:**
    
    1. **Web Scraping**: Scrape official MOM website pages
    2. **Data Processing**: Clean and structure scraped content
    3. **Categorization**: Automatically categorize by pass type and content type
    4. **Chunking**: Split documents into manageable chunks (1000 chars, 200 overlap)
    5. **Embedding**: Convert chunks to vector embeddings
    6. **Storage**: Store in ChromaDB vector database
    7. **Indexing**: Create searchable index for retrieval
    """)
    
    st.code("""
    ┌─────────────────┐
    │ MOM Website      │
    │ (mom.gov.sg)     │
    └────────┬─────────┘
             │
             ▼
    ┌─────────────────┐
    │ Web Scraper      │
    │ (BeautifulSoup) │
    └────────┬─────────┘
             │
             ▼
    ┌─────────────────┐
    │ Data Processor   │
    │ (Clean & Chunk)  │
    └────────┬─────────┘
             │
             ▼
    ┌─────────────────┐
    │ Embedding       │
    │ (OpenAI API)    │
    └────────┬─────────┘
             │
             ▼
    ┌─────────────────┐
    │ Vector Database │
    │ (ChromaDB)      │
    └─────────────────┘
    """, language="text")
    
    st.markdown("---")
    
    # Implementation Details
    st.markdown("### Implementation Details")
    
    st.markdown("""
    #### Technologies Used
    
    - **LangChain**: RAG framework and chain orchestration
    - **ChromaDB**: Vector database for semantic search
    - **OpenAI Embeddings**: text-embedding-3-small for document embeddings
    - **OpenAI GPT-4o-mini**: LLM for answer generation
    - **Streamlit**: Web application framework
    
    #### Key Parameters
    
    - **Chunk Size**: 1000 characters
    - **Chunk Overlap**: 200 characters
    - **Retrieval Count**: Top 5 chunks per query
    - **Temperature**: 0.3 (for consistent, factual responses)
    
    #### Prompt Engineering
    
    The system uses a custom prompt template that:
    - Instructs the LLM to use only provided context
    - Encourages citing sources
    - Handles cases where information is not available
    - Maintains a helpful, professional tone
    """)

def main():
    """Main application"""
    # Check authentication
    if not check_password():
        return
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["💬 Chat", "🔍 Search", "ℹ️ About Us", "🔬 Methodology"]
    )
    
    # Route to appropriate page
    if page == "💬 Chat":
        chat_page()
    elif page == "🔍 Search":
        search_page()
    elif page == "ℹ️ About Us":
        about_page()
    elif page == "🔬 Methodology":
        methodology_page()

if __name__ == "__main__":
    main()


