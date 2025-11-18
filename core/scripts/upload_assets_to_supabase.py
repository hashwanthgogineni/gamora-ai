"""
Upload curated assets to Supabase Storage
Run this script once to migrate all assets from local filesystem to Supabase Storage
"""

import os
import sys
import io
import json
from pathlib import Path
from typing import Dict, List
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

# Asset bucket name (separate from projects)
ASSET_BUCKET = "gamoraai-assets"

async def upload_assets_to_supabase():
    """Upload all curated assets to Supabase Storage"""
    
    # Initialize Supabase client
    supabase_url = os.getenv("VITE_SUPABASE_URL") or os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("VITE_SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
        sys.exit(1)
    
    client = create_client(supabase_url, supabase_key)
    
    # Ensure asset bucket exists
    try:
        buckets = client.storage.list_buckets()
        bucket_names = []
        if buckets:
            if isinstance(buckets, list):
                for b in buckets:
                    if isinstance(b, dict):
                        bucket_names.append(b.get('name', ''))
                    else:
                        bucket_names.append(getattr(b, 'name', getattr(b, 'id', str(b))))
        
        if ASSET_BUCKET not in bucket_names:
            print(f"📦 Creating asset bucket: {ASSET_BUCKET}")
            try:
                client.storage.create_bucket(
                    ASSET_BUCKET,
                    options={"public": True}  # Public bucket for assets
                )
                print(f"✅ Created bucket: {ASSET_BUCKET}")
            except Exception as e:
                print(f"⚠️  Bucket creation error (might already exist): {e}")
        else:
            print(f"✅ Bucket exists: {ASSET_BUCKET}")
    except Exception as e:
        print(f"⚠️  Bucket check failed: {e}")
        print(f"⚠️  Make sure bucket '{ASSET_BUCKET}' exists in Supabase Storage")
    
    # Get assets directory
    assets_dir = Path(__file__).parent.parent / "assets" / "curated"
    index_path = assets_dir / "metadata" / "index.json"
    
    if not index_path.exists():
        print(f"❌ Asset index not found: {index_path}")
        sys.exit(1)
    
    # Load asset index
    with open(index_path, 'r', encoding='utf-8') as f:
        asset_index = json.load(f)
    
    assets = asset_index.get('assets', [])
    print(f"📦 Found {len(assets)} assets to upload")
    
    uploaded = 0
    failed = 0
    
    # Upload each asset
    for asset in assets:
        asset_path = asset.get('path', '')
        if not asset_path:
            continue
        
        full_path = assets_dir / asset_path
        if not full_path.exists():
            print(f"⚠️  Asset file not found: {full_path}")
            failed += 1
            continue
        
        # Upload to Supabase Storage
        storage_path = f"curated/{asset_path.replace('\\', '/')}"
        
        try:
            with open(full_path, 'rb') as f:
                file_data = f.read()
            
            # Upload file
            result = client.storage.from_(ASSET_BUCKET).upload(
                path=storage_path,
                file=file_data,
                file_options={
                    "content-type": "image/png" if asset_path.endswith('.png') else "image/jpeg",
                    "cache-control": "3600"
                }
            )
            
            uploaded += 1
            if uploaded % 100 == 0:
                print(f"✅ Uploaded {uploaded}/{len(assets)} assets...")
        
        except Exception as e:
            print(f"❌ Failed to upload {asset_path}: {e}")
            failed += 1
    
    # Upload index.json to Supabase Storage
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            index_data = f.read()
        
        client.storage.from_(ASSET_BUCKET).upload(
            path="metadata/index.json",
            file=index_data.encode('utf-8'),
            file_options={
                "content-type": "application/json",
                "cache-control": "3600"
            }
        )
        print(f"✅ Uploaded asset index to Supabase")
    except Exception as e:
        print(f"❌ Failed to upload index: {e}")
    
    print(f"\n✅ Upload complete!")
    print(f"   - Uploaded: {uploaded}")
    print(f"   - Failed: {failed}")
    print(f"   - Total: {len(assets)}")
    print(f"\n📦 Assets are now available in Supabase Storage bucket: {ASSET_BUCKET}")

if __name__ == "__main__":
    asyncio.run(upload_assets_to_supabase())

