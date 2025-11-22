# Streamlit Cloud Deployment Guide

This guide will walk you through deploying your Singapore Work Pass Assistant to Streamlit Cloud.

## Prerequisites

1. **GitHub Account**: You need a GitHub account
2. **Streamlit Cloud Account**: Sign up at [https://streamlit.io/cloud](https://streamlit.io/cloud)
3. **Git Repository**: Your code should be in a GitHub repository

## Step-by-Step Deployment

### Step 1: Prepare Your Repository

#### 1.1 Ensure `.gitignore` is set up correctly

Your `.gitignore` should already include:
- `.env` (contains sensitive API keys)
- `chroma_db/` (vector database - will be rebuilt on Streamlit Cloud)
- `venv/` (virtual environment)
- `__pycache__/` (Python cache)

#### 1.2 Verify `requirements.txt` is complete

Your `requirements.txt` should include all dependencies. It's already set up correctly.

#### 1.3 Commit and push to GitHub

```bash
# Initialize git if not already done
git init

# Add all files (respecting .gitignore)
git add .

# Commit
git commit -m "Initial commit for Streamlit Cloud deployment"

# Add your GitHub repository as remote (replace with your repo URL)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Important Notes:**
- The `chroma_db/` folder is excluded from git (in `.gitignore`)
- You'll need to rebuild the knowledge base on Streamlit Cloud
- Large data files (`mom_data.json`, `processed_knowledge_base.json`) will be included unless you add them to `.gitignore`

### Step 2: Set Up Streamlit Cloud

#### 2.1 Sign in to Streamlit Cloud

1. Go to [https://streamlit.io/cloud](https://streamlit.io/cloud)
2. Sign in with your GitHub account
3. Authorize Streamlit Cloud to access your repositories

#### 2.2 Deploy Your App

1. Click **"New app"** button
2. Select your repository from the dropdown
3. Select the branch (usually `main` or `master`)
4. Set the **Main file path**: `app.py`
5. Click **"Deploy"**

### Step 3: Configure Environment Variables

After deployment, you need to set up environment variables:

1. Go to your app's settings in Streamlit Cloud
2. Click on **"Secrets"** or **"Advanced settings"**
3. Add the following secrets:

```toml
OPENAI_API_KEY = "sk-your-openai-api-key-here"
APP_PASSWORD = "your-secure-password-here"
```

**Important**: 
- Never commit your `.env` file or API keys to GitHub
- Use Streamlit Cloud's secrets management for sensitive data
- The secrets are automatically loaded as environment variables

### Step 4: Build Knowledge Base on Streamlit Cloud

Since `chroma_db/` is excluded from git, you need to rebuild it on Streamlit Cloud.

#### Option A: Automatic Build on First Run (Recommended)

You can modify your app to automatically build the knowledge base if it doesn't exist. However, this requires:
- The knowledge base builder to run successfully
- Sufficient time/resources on Streamlit Cloud
- Access to the MOM website for scraping

#### Option B: Manual Build via Streamlit Cloud Console

1. Go to your app's settings in Streamlit Cloud
2. Open the **"Console"** tab
3. Run the knowledge base builder:

```bash
python knowledge_base/builder.py --from-file processed_knowledge_base.json
```

**Note**: If you have `processed_knowledge_base.json` in your repo, this will be faster than scraping.

#### Option C: Include Pre-built Database (If Small Enough)

If your `chroma_db/` is small enough (< 100MB), you can:
1. Temporarily remove `chroma_db/` from `.gitignore`
2. Commit and push the database
3. Add it back to `.gitignore` for future updates

**Warning**: This may slow down your git operations if the database is large.

### Step 5: Verify Deployment

1. Visit your app URL (provided by Streamlit Cloud)
2. Test the login with your `APP_PASSWORD`
3. Try asking a question in the chat interface
4. Test the search functionality

## Troubleshooting

### Issue: "Vector database not found"

**Solution**: The knowledge base hasn't been built yet. You need to:
1. Ensure `processed_knowledge_base.json` is in your repository, OR
2. Run the builder on Streamlit Cloud console, OR
3. Include the `chroma_db/` folder in your repository

### Issue: "OpenAI API key not found"

**Solution**: 
1. Check that you've added `OPENAI_API_KEY` in Streamlit Cloud secrets
2. Verify the key is correct (starts with `sk-`)
3. Restart your app after adding secrets

### Issue: App crashes on startup

**Solution**:
1. Check the logs in Streamlit Cloud dashboard
2. Verify all dependencies are in `requirements.txt`
3. Ensure Python version is compatible (Streamlit Cloud uses Python 3.8+)

### Issue: Knowledge base building fails

**Solution**:
1. Use `--from-file` option with `processed_knowledge_base.json` instead of scraping
2. Check that the file exists in your repository
3. Verify the file format is correct

### Issue: Slow performance

**Solution**:
- Streamlit Cloud free tier has resource limits
- Consider upgrading to paid tier for better performance
- Optimize your knowledge base size

## Best Practices

1. **Keep Secrets Secure**: Never commit API keys or passwords
2. **Monitor Usage**: Track your OpenAI API usage to avoid unexpected costs
3. **Update Regularly**: Keep dependencies updated in `requirements.txt`
4. **Test Locally**: Always test changes locally before deploying
5. **Use Processed Data**: Include `processed_knowledge_base.json` for faster builds

## Alternative: Include Knowledge Base in Repository

If you want to include the pre-built knowledge base:

1. **Check size first**:
```bash
du -sh chroma_db/
```

2. **If under 50MB**, you can include it:
   - Remove `chroma_db/` from `.gitignore`
   - Commit and push
   - Your app will work immediately without rebuilding

3. **If over 50MB**, consider:
   - Using Git LFS (Large File Storage)
   - Using cloud storage (S3, Google Cloud Storage)
   - Rebuilding on Streamlit Cloud

## Updating Your App

After making changes:

```bash
git add .
git commit -m "Description of changes"
git push origin main
```

Streamlit Cloud will automatically redeploy your app when you push to the main branch.

## Cost Considerations

- **Streamlit Cloud**: Free tier available, paid tiers for more resources
- **OpenAI API**: Pay-per-use for API calls (GPT-4o-mini is cost-effective)
- **Storage**: Free tier includes limited storage

Monitor your usage in:
- Streamlit Cloud dashboard
- OpenAI usage dashboard

## Support

- Streamlit Cloud Docs: [https://docs.streamlit.io/streamlit-community-cloud](https://docs.streamlit.io/streamlit-community-cloud)
- Streamlit Community: [https://discuss.streamlit.io](https://discuss.streamlit.io)

