# Singapore Work Pass Chatbot

An LLM-powered web application that helps citizens understand Singapore work passes by retrieving information from the official Ministry of Manpower (MOM) website.

## Project Structure

```
.
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
├── knowledge_base/           # Knowledge base building scripts
│   ├── scraper.py           # Web scraper for MOM website
│   ├── processor.py         # Data processing and chunking
│   └── builder.py           # Vector database builder
├── app.py                    # Main Streamlit application (to be created)
└── README.md                 # This file

```

## Setup Instructions

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file in the root directory (copy from `.env.example`):
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   APP_PASSWORD=your_app_password_here
   ```

3. **Build the knowledge base:**
   ```bash
   python knowledge_base/builder.py
   ```
   
   This will:
   - Scrape the MOM website for work pass information
   - Process and categorize the data
   - Create embeddings and store in ChromaDB
   
   Or build from existing processed data:
   ```bash
   python knowledge_base/builder.py --from-file processed_knowledge_base.json
   ```

4. **Run the Streamlit application:**
   ```bash
   streamlit run app.py
   ```
   
   The app will be available at `http://localhost:8501`

## Knowledge Base Categories

1. **Professionals & Executives**: EP, PEP, EntrePass
2. **Skilled & Semi-Skilled Workers**: S Pass, Work Permit for Foreign Worker
3. **Domestic & Specific Sectors**: FDW, Performing Artiste, Confinement Nanny
4. **Students, Trainees, Dependants**: Training Employment Pass, Work Holiday Pass, Dependant's Pass, LTVP

## Features

✅ **Chat Interface**: Interactive Q&A powered by RAG  
✅ **Intelligent Search**: Semantic search across knowledge base  
✅ **Visualizations**: Charts and statistics about work passes  
✅ **Personalization**: Context-aware responses based on user profile  
✅ **About Us Page**: Project documentation  
✅ **Methodology Page**: Technical details and flowcharts  
✅ **Password Protection**: Secure access to the application

## Deployment

To deploy on Streamlit Community Cloud:

1. Push your code to a GitHub repository
2. Connect the repository to Streamlit Cloud
3. Set environment variables in Streamlit Cloud settings:
   - `OPENAI_API_KEY`
   - `APP_PASSWORD`
4. Deploy!

## Project Structure

```
.
├── app.py                    # Main Streamlit application
├── rag_engine.py            # RAG engine for Q&A
├── config.py                # Configuration settings
├── knowledge_base/          # Knowledge base building scripts
│   ├── scraper.py          # Web scraper
│   ├── processor.py        # Data processor
│   └── builder.py          # Vector DB builder
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

