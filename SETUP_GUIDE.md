# Setup Guide

## Quick Start

### 1. Prerequisites
- Python 3.8 or higher
- OpenAI API key
- Internet connection (for initial scraping)

### 2. Installation

```bash
# Clone or navigate to the project directory
cd "AI Champions Project"

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Setup

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
APP_PASSWORD=your-secure-password-here
```

### 4. Build Knowledge Base

**Option A: Scrape from MOM website (Recommended for first time)**
```bash
python knowledge_base/builder.py
```

This will:
- Scrape official MOM website pages
- Process and categorize the content
- Create embeddings
- Store in ChromaDB vector database

**Option B: Use existing processed data**
```bash
python knowledge_base/builder.py --from-file processed_knowledge_base.json
```

**Note**: The scraping process may take 10-30 minutes depending on the number of pages. The scraper includes delays to be respectful to the MOM website.

### 5. Run the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## Troubleshooting

### Issue: "Vector database not found"
**Solution**: Run `python knowledge_base/builder.py` first to build the knowledge base.

### Issue: "OpenAI API key not found"
**Solution**: Make sure your `.env` file exists and contains `OPENAI_API_KEY=your-key-here`

### Issue: Scraping fails or returns no data
**Solution**: 
- Check your internet connection
- Verify MOM website is accessible
- The website structure may have changed - you may need to update the scraper

### Issue: Import errors
**Solution**: 
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.8+)

## File Structure After Setup

After running the builder, you should have:
```
.
├── chroma_db/                    # Vector database (created)
├── mom_data.json                 # Raw scraped data (optional)
├── processed_knowledge_base.json # Processed chunks (optional)
└── ... (other files)
```

## Next Steps

1. Test the chat interface with questions like:
   - "What is an Employment Pass?"
   - "What are the requirements for S Pass?"
   - "How do I apply for a Work Permit?"

2. Try the search functionality with specific queries

3. Explore the visualizations and documentation pages

## Deployment to Streamlit Cloud

For detailed deployment instructions, see **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)**.

Quick steps:
1. Push your code to GitHub
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Connect your repository
4. Set environment variables:
   - `OPENAI_API_KEY`
   - `APP_PASSWORD`
5. Deploy!

**Important**: Make sure to add `chroma_db/` to `.gitignore` if it contains large files. You may need to rebuild the knowledge base on Streamlit Cloud or use a cloud storage solution.


