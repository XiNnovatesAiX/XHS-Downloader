#!/usr/bin/env python3
"""
Bulk download script that reads URLs from bulk_urls.txt file
Handles both relative and absolute URLs automatically
"""

import asyncio
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, TaskID
from rich import print as rprint
from source import XHS

console = Console()

def normalize_url(url: str) -> str:
    """Convert relative URLs to absolute URLs"""
    url = url.strip()
    
    # Skip empty lines and comments
    if not url or url.startswith('#'):
        return None
        
    # If it's already absolute, return as-is
    if url.startswith('http'):
        return url
        
    # If it's relative, add the domain
    if url.startswith('/'):
        return f"https://www.xiaohongshu.com{url}"
        
    return url

def load_urls_from_file(file_path: str = "bulk_urls.txt") -> list[str]:
    """Load URLs from a text file, handling both relative and absolute URLs"""
    
    file_obj = Path(file_path)
    if not file_obj.exists():
        rprint(f"[red]❌ File {file_path} not found.[/red]")
        rprint(f"[yellow]💡 Create the file and add URLs (one per line).[/yellow]")
        return []
    
    urls = []
    with open(file_obj, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            normalized_url = normalize_url(line)
            if normalized_url:
                urls.append(normalized_url)
                
    rprint(f"[green]✅ Loaded {len(urls)} URLs from {file_path}[/green]")
    return urls

async def bulk_download_from_file(
    file_path: str = "bulk_urls.txt",
    record_data: bool = True,
    download_record: bool = True,
    author_archive: bool = True,
    folder_mode: bool = True,
    max_concurrent: int = 3
):
    """
    Bulk download posts from URLs in a text file
    
    Args:
        file_path: Path to text file containing URLs
        record_data: Save metadata to database
        download_record: Track downloaded posts to avoid duplicates
        author_archive: Organize by author folders
        folder_mode: Create individual folders for each post
        max_concurrent: Maximum concurrent downloads
    """
    
    # Load URLs from file
    urls = load_urls_from_file(file_path)
    if not urls:
        return []
    
    rprint(f"\n[bold cyan]🚀 Starting bulk download of {len(urls)} posts[/bold cyan]")
    
    # Configure XHS with optimal settings for bulk download
    async with XHS(
        record_data=record_data,
        download_record=download_record,
        author_archive=author_archive,
        folder_mode=folder_mode,
        timeout=15,  # Longer timeout for stability
        max_retry=3,  # More retries for reliability
    ) as xhs:
        
        results = []
        failed_urls = []
        
        # Process with progress bar
        with Progress() as progress:
            task = progress.add_task("Downloading posts...", total=len(urls))
            
            # Semaphore to limit concurrent downloads
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def download_single_url(url: str, index: int) -> dict:
                async with semaphore:
                    try:
                        progress.update(task, description=f"Processing {index+1}/{len(urls)}: {url[:50]}...")
                        
                        result = await xhs.extract(url, download=True)
                        
                        if result and len(result) > 0 and result[0]:
                            post_data = result[0]
                            title = post_data.get('作品标题', 'Unknown title')
                            author = post_data.get('作者昵称', 'Unknown author')
                            
                            rprint(f"[green]✅ {index+1}/{len(urls)}: {title} by {author}[/green]")
                            progress.advance(task)
                            return {"success": True, "data": post_data, "url": url}
                        else:
                            rprint(f"[yellow]⚠️ {index+1}/{len(urls)}: No data returned for {url[:50]}...[/yellow]")
                            progress.advance(task)
                            return {"success": False, "error": "No data", "url": url}
                            
                    except Exception as e:
                        rprint(f"[red]❌ {index+1}/{len(urls)}: Error - {str(e)[:100]}[/red]")
                        progress.advance(task)
                        return {"success": False, "error": str(e), "url": url}
            
            # Process all URLs concurrently (with semaphore limiting)
            tasks = [download_single_url(url, i) for i, url in enumerate(urls)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed = [r for r in results if isinstance(r, dict) and not r.get("success")]
        exceptions = [r for r in results if not isinstance(r, dict)]
        
        # Summary
        rprint(f"\n[bold green]📊 Bulk Download Summary[/bold green]")
        rprint(f"✅ Successful: {len(successful)}")
        rprint(f"❌ Failed: {len(failed) + len(exceptions)}")
        rprint(f"📈 Success rate: {len(successful)/len(urls)*100:.1f}%")
        
        if failed:
            rprint(f"\n[yellow]⚠️ Failed URLs:[/yellow]")
            for fail in failed[:10]:  # Show first 10 failures
                rprint(f"  • {fail['url'][:60]}... - {fail['error']}")
            
            if len(failed) > 10:
                rprint(f"  ... and {len(failed) - 10} more")
        
        # Save failed URLs for retry
        if failed or exceptions:
            failed_file = "failed_urls.txt"
            with open(failed_file, 'w', encoding='utf-8') as f:
                f.write("# Failed URLs - you can retry these\n")
                for fail in failed:
                    f.write(f"{fail['url']}\n")
                for exc in exceptions:
                    if hasattr(exc, 'url'):
                        f.write(f"{exc.url}\n")
            
            rprint(f"[blue]💾 Failed URLs saved to {failed_file} for retry[/blue]")
        
        return successful

async def retry_failed_downloads():
    """Retry downloading from failed_urls.txt"""
    failed_file = "failed_urls.txt"
    if not Path(failed_file).exists():
        rprint(f"[yellow]⚠️ No {failed_file} found. Nothing to retry.[/yellow]")
        return
    
    rprint(f"[blue]🔄 Retrying failed downloads from {failed_file}[/blue]")
    return await bulk_download_from_file(failed_file, max_concurrent=2)

def preview_urls(file_path: str = "bulk_urls.txt", limit: int = 10):
    """Preview URLs that will be processed"""
    urls = load_urls_from_file(file_path)
    
    if not urls:
        return
    
    rprint(f"\n[bold blue]👀 Preview of URLs to download:[/bold blue]")
    for i, url in enumerate(urls[:limit], 1):
        rprint(f"{i:2d}. {url}")
    
    if len(urls) > limit:
        rprint(f"    ... and {len(urls) - limit} more URLs")
    
    rprint(f"\n[bold]Total URLs: {len(urls)}[/bold]")

async def main():
    """Interactive main function"""
    
    while True:
        console.print("\n[bold cyan]📁 XHS Bulk Downloader[/bold cyan]")
        console.print("1. 👀 Preview URLs in bulk_urls.txt")
        console.print("2. 🚀 Start bulk download")
        console.print("3. 🔄 Retry failed downloads")
        console.print("4. ⚙️ Download with custom settings")
        console.print("5. 🚪 Exit")
        
        choice = console.input("\n[bold]Choose an option (1-5): [/bold]")
        
        if choice == "1":
            preview_urls()
            
        elif choice == "2":
            await bulk_download_from_file()
            
        elif choice == "3":
            await retry_failed_downloads()
            
        elif choice == "4":
            # Custom settings
            rprint("[bold]Custom Download Settings:[/bold]")
            record_data = console.input("Save metadata to database? (y/n, default=y): ").lower() != 'n'
            author_archive = console.input("Organize by author folders? (y/n, default=y): ").lower() != 'n'
            folder_mode = console.input("Create individual post folders? (y/n, default=y): ").lower() != 'n'
            
            try:
                max_concurrent = int(console.input("Max concurrent downloads (1-5, default=3): ") or "3")
                max_concurrent = max(1, min(5, max_concurrent))
            except ValueError:
                max_concurrent = 3
            
            await bulk_download_from_file(
                record_data=record_data,
                author_archive=author_archive,
                folder_mode=folder_mode,
                max_concurrent=max_concurrent
            )
            
        elif choice == "5":
            rprint("[green]👋 Goodbye![/green]")
            break
            
        else:
            rprint("[red]❌ Invalid choice. Please select 1-5.[/red]")

if __name__ == "__main__":
    # Quick usage examples:
    
    # Preview URLs
    # preview_urls()
    
    # Simple bulk download
    # asyncio.run(bulk_download_from_file())
    
    # Interactive mode
    asyncio.run(main())