# 🚀 Bulk Download Setup Guide

This guide helps you set up and use the enhanced bulk download functionality.

## ⚡ Quick Start with uv (Recommended)

```bash
# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/XiNnovatesAiX/XHS-Downloader.git
cd XHS-Downloader

# Setup your URLs
cp bulk_urls_template.txt bulk_urls.txt
# Edit bulk_urls.txt - add your XiaoHongShu URLs (one per line)

# Run bulk download (dependencies installed automatically)
uv run bulk_download_from_file.py
```

## 🐍 Alternative: Traditional Python Setup

```bash
# Clone repository
git clone https://github.com/XiNnovatesAiX/XHS-Downloader.git
cd XHS-Downloader

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup your URLs  
cp bulk_urls_template.txt bulk_urls.txt
# Edit bulk_urls.txt with your URLs

# Run bulk download
python bulk_download_from_file.py
```

## 📝 URL Format Support

The bulk downloader supports both relative and absolute URLs:

```
# Relative URLs (domain added automatically):
/user/profile/AUTHOR_ID/POST_ID?xsec_token=TOKEN&xsec_source=pc_user

# Absolute URLs (used as-is):
https://www.xiaohongshu.com/explore/POST_ID?xsec_token=TOKEN&xsec_source=pc_user
```

## 🎯 Features

- ✅ **Smart URL Processing**: Handles both relative and absolute URLs
- ✅ **Progress Tracking**: Real-time progress bar and status updates  
- ✅ **Error Handling**: Failed URLs saved for retry
- ✅ **Concurrent Downloads**: Configurable parallel processing
- ✅ **Privacy Protection**: Personal URLs and content ignored by git

## 🔄 Usage Modes

1. **Interactive Mode**: `uv run bulk_download_from_file.py` → Choose options
2. **Direct Download**: Edit URLs in `bulk_urls.txt` → Run script
3. **Retry Failed**: Automatically handles failed downloads

## ⚙️ Configuration

The script uses optimal defaults but you can customize:
- **Concurrent downloads**: Default 3 (configurable 1-5)
- **File organization**: Author folders + individual post folders  
- **Metadata saving**: SQLite database for post information
- **Error handling**: Automatic retry and failure logging

## 🔧 Troubleshooting

**Issue**: `uv: command not found`
- **Solution**: Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`

**Issue**: Dependencies not found  
- **Solution**: Run `uv sync` or use traditional pip setup

**Issue**: No URLs processed
- **Solution**: Check `bulk_urls.txt` format and remove comment lines

**Issue**: Permission errors
- **Solution**: Ensure write permissions in download directory