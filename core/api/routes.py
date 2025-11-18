"""
API Routes - REST and WebSocket endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, Header, Query, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import logging
import uuid
from datetime import datetime
import httpx
import re

logger = logging.getLogger(__name__)

# Request/Response models
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    user_id: int
    email: str
    token: str

class GenerateGameRequest(BaseModel):
    prompt: str
    title: Optional[str] = None
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    project_id: str
    title: str
    description: Optional[str]
    status: str
    web_preview_url: Optional[str]
    builds: Optional[dict]
    created_at: str

# Initialize routers
auth_router = APIRouter()
projects_router = APIRouter()
generation_router = APIRouter()


# Dependency to get components
def get_components():
    from main import components
    return components


# Dependency to get current user
async def get_current_user(
    authorization: Optional[str] = Header(None),
    components = Depends(get_components)
):
    """Extract and verify Supabase JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    auth_manager = components['auth']
    user = auth_manager.get_current_user(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user


# ============= AUTH ROUTES =============

@auth_router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest, components = Depends(get_components)):
    """Register new user"""
    try:
        auth_manager = components['auth']
        result = await auth_manager.register_user(request.email, request.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@auth_router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, components = Depends(get_components)):
    """Login user"""
    try:
        auth_manager = components['auth']
        result = await auth_manager.login_user(request.email, request.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@auth_router.get("/me")
async def get_me(current_user = Depends(get_current_user)):
    """Get current user info"""
    return current_user


# ============= PROJECT ROUTES =============

@projects_router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user = Depends(get_current_user),
    components = Depends(get_components)
):
    """Get project details"""
    db = components['db']
    project = await db.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check ownership
    if project['user_id'] != current_user['user_id']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "project_id": project['id'],
        "title": project['title'],
        "description": project['description'],
        "status": project['status'],
        "web_preview_url": project['web_preview_url'],
        "builds": project['builds'],
        "created_at": project['created_at'].isoformat()
    }


@projects_router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    limit: int = 50,
    offset: int = 0,
    current_user = Depends(get_current_user),
    components = Depends(get_components)
):
    """List user's projects"""
    db = components['db']
    projects = await db.get_user_projects(
        user_id=current_user['user_id'],
        limit=limit,
        offset=offset
    )
    
    return [
        {
            "project_id": p['id'],
            "title": p['title'],
            "description": p['description'],
            "status": p['status'],
            "web_preview_url": p['web_preview_url'],
            "builds": p['builds'],
            "created_at": p['created_at'].isoformat()
        }
        for p in projects
    ]


# ============= GENERATION ROUTES =============

@generation_router.post("/game")
async def generate_game(
    request: GenerateGameRequest,
    current_user = Depends(get_current_user),
    components = Depends(get_components)
):
    """Start game generation (async)"""
    try:
        # Rate limiting
        rate_limiter = components['rate_limiter']
        allowed, remaining = await rate_limiter.check_rate_limit(
            f"user:{current_user['user_id']}",
            limit=10,  # 10 games per hour
            window=3600
        )
        
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Try again later."
            )
        
        # Create project
        project_id = str(uuid.uuid4())
        db = components['db']
        
        # Supabase uses UUID strings for user_id
        user_id = str(current_user['user_id'])
        
        await db.create_project(
            project_id=project_id,
            user_id=user_id,
            title=request.title or "AI Generated Game",
            description=request.description or "",
            prompt=request.prompt
        )
        
        # Start generation in background (fire and forget)
        import asyncio
        orchestrator = components['orchestrator']
        ws_manager = components['ws_manager']
        
        async def generation_task():
            """Background task for game generation"""
            try:
                # Create progress callback
                async def progress_callback(progress_data):
                    await ws_manager.send_message(project_id, {
                        "type": "progress",
                        "data": progress_data
                    })
                
                # Generate game
                result = await orchestrator.generate_game(
                    project_id=project_id,
                    user_prompt=request.prompt,
                    user_tier="free",  # TODO: Get from user profile
                    db_manager=db
                )
                
                # Update project with results
                if result['success']:
                    # Clean ai_content to remove binary data before saving to database
                    ai_content = result.get('ai_content', {})
                    if isinstance(ai_content, dict):
                        # Remove binary data from assets if present
                        if 'assets' in ai_content and isinstance(ai_content['assets'], list):
                            cleaned_assets = []
                            for asset in ai_content['assets']:
                                if isinstance(asset, dict):
                                    # Keep metadata but remove binary data
                                    cleaned_asset = {k: v for k, v in asset.items() if not isinstance(v, bytes)}
                                    cleaned_assets.append(cleaned_asset)
                                else:
                                    cleaned_assets.append(asset)
                            ai_content['assets'] = cleaned_assets
                    
                    await db.update_project(
                        project_id=project_id,
                        ai_content=ai_content,
                        status='completed',
                        completed_at=datetime.utcnow()
                    )
                    
                    # Save builds
                    builds_dict = result.get('builds', {})
                    for platform, url in builds_dict.items():
                        await db.create_build(
                            project_id=project_id,
                            platform=platform,
                            build_url=url,
                            web_preview_url=result.get('web_preview_url'),
                            status='completed'
                        )
                    
                    # Send completion message
                    await ws_manager.send_message(project_id, {
                        "type": "complete",
                        "data": {
                            "project_id": project_id,
                            "web_preview_url": result.get('web_preview_url'),
                            "builds": builds_dict
                        }
                    })
                else:
                    await db.update_project(
                        project_id=project_id,
                        status='failed'
                    )
                    
                    await ws_manager.send_message(project_id, {
                        "type": "error",
                        "data": {"error": result.get('error')}
                    })
                    
            except Exception as e:
                logger.error(f"Generation task failed: {e}", exc_info=True)
                await db.update_project(project_id=project_id, status='failed')
                await ws_manager.send_message(project_id, {
                    "type": "error",
                    "data": {"error": str(e)}
                })
        
        # Start background task
        asyncio.create_task(generation_task())
        
        return {
            "project_id": project_id,
            "status": "processing",
            "message": "Game generation started. Connect to WebSocket for progress updates.",
            "websocket_url": f"/api/v1/generate/ws/{project_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generation start error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start generation")


@generation_router.websocket("/ws/{project_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    project_id: str,
    token: Optional[str] = Query(None),
    components = Depends(get_components)
):
    """WebSocket endpoint for real-time progress updates"""
    # Verify authentication (token from query param)
    if token:
        auth_manager = components['auth']
        user = auth_manager.get_current_user(token)
        if not user:
            await websocket.close(code=1008, reason="Invalid token")
            return
    
    ws_manager = components['ws_manager']
    
    await ws_manager.connect(websocket, project_id)
    
    try:
        # Send initial message
        await websocket.send_json({
            "type": "connected",
            "data": {
                "project_id": project_id,
                "message": "Connected to generation progress stream"
            }
        })
        
        # Keep connection alive
        while True:
            # Wait for messages (if client sends any)
            try:
                data = await websocket.receive_text()
                # Echo back (optional)
                await websocket.send_json({
                    "type": "echo",
                    "data": {"received": data}
                })
            except:
                # Client disconnected or error
                break
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, project_id)
        logger.info(f"WebSocket disconnected: {project_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket, project_id)


@generation_router.get("/preview/{project_id}")
async def proxy_game_preview(
    project_id: str,
    components = Depends(get_components)
):
    """
    Proxy endpoint to serve game preview HTML with proper headers
    This bypasses Supabase Storage's restrictive CSP
    
    The HTML is served from our backend, but assets (.wasm, .pck) are loaded
    from Supabase using relative paths that work because we set the base URL
    """
    try:
        storage_service = components['storage']
        storage_path = f"games/{project_id}/preview/index.html"
        
        logger.info(f"🔍 Attempting to load preview for project: {project_id}")
        logger.info(f"📁 Storage path: {storage_path}")
        
        # Download HTML from Supabase
        try:
            html_content_bytes = await storage_service.download_file(storage_path)
            html_content = html_content_bytes.decode('utf-8')
            logger.info(f"✅ Successfully downloaded HTML ({len(html_content)} bytes)")
        except Exception as download_error:
            logger.error(f"❌ Failed to download HTML: {download_error}")
            # Try to list files in the project directory for debugging
            try:
                # This might not work depending on storage implementation, but worth trying
                logger.error(f"💡 Project directory: games/{project_id}/")
            except:
                pass
            raise HTTPException(
                status_code=404, 
                detail=f"Game preview not found. Make sure the project has been built. Error: {str(download_error)}"
            )
        
        # Get Supabase public URL for assets
        from config.settings import Settings
        settings = Settings()
        supabase_url = settings.supabase_url.rstrip('/')
        bucket = storage_service.bucket
        
        # Calculate the base URL for assets (same directory as index.html)
        asset_base_url = f"{supabase_url}/storage/v1/object/public/{bucket}/games/{project_id}/preview"
        
        # Modify HTML to fix Godot HTML5 export issues
        if '<head>' in html_content:
            # Add base tag so relative paths resolve to Supabase
            base_tag = f'<base href="{asset_base_url}/">'
            html_content = html_content.replace('<head>', f'<head>\n{base_tag}', 1)
        
        # Disable ServiceWorker registration to avoid origin mismatch errors
        # Godot HTML5 exports try to register a service worker, which fails when served from a different origin
        # More aggressive removal - catch all variations
        
        # Remove entire service worker registration blocks
        html_content = re.sub(
            r'navigator\.serviceWorker\.register\([^)]*\)[^;]*;?',
            '// ServiceWorker disabled',
            html_content,
            flags=re.MULTILINE
        )
        
        # Remove service worker checks and registrations in if statements
        html_content = re.sub(
            r'if\s*\([^)]*serviceWorker[^)]*\)\s*\{[^}]*register\([^}]*\}',
            '// ServiceWorker registration disabled',
            html_content,
            flags=re.DOTALL | re.IGNORECASE
        )
        
        # Remove service worker event listeners
        html_content = re.sub(
            r'navigator\.serviceWorker\.(addEventListener|oncontrollerchange|onmessage)[^;]*;?',
            '// ServiceWorker event listener disabled',
            html_content,
            flags=re.IGNORECASE
        )
        
        # Remove service worker script tags entirely
        html_content = re.sub(
            r'<script[^>]*service[_-]?worker[^>]*>.*?</script>',
            '<!-- ServiceWorker script removed -->',
            html_content,
            flags=re.IGNORECASE | re.DOTALL
        )
        
        # Override navigator.serviceWorker entirely - inject at the very beginning
        # This must run before any Godot code tries to register a service worker
        service_worker_override = '''<script>
// Override ServiceWorker to prevent registration errors (injected by proxy)
(function() {
    if (typeof navigator !== 'undefined' && navigator.serviceWorker) {
        const originalRegister = navigator.serviceWorker.register.bind(navigator.serviceWorker);
        navigator.serviceWorker.register = function() {
            console.log('[Proxy] ServiceWorker registration disabled for cross-origin serving');
            return Promise.reject(new DOMException('ServiceWorker registration disabled', 'NotAllowedError'));
        };
        // Also override getRegistration and getRegistrations
        if (navigator.serviceWorker.getRegistration) {
            navigator.serviceWorker.getRegistration = function() {
                return Promise.resolve(null);
            };
        }
        if (navigator.serviceWorker.getRegistrations) {
            navigator.serviceWorker.getRegistrations = function() {
                return Promise.resolve([]);
            };
        }
    }
})();
</script>'''
        
        # Insert at the very beginning of <head> or before first <script>
        if '<head>' in html_content:
            html_content = html_content.replace('<head>', '<head>\n' + service_worker_override, 1)
        elif '<script' in html_content:
            # If no head tag, insert before first script
            html_content = re.sub(
                r'(<script[^>]*>)',
                service_worker_override + r'\n\1',
                html_content,
                count=1
            )
        
        # Fix asset paths in the HTML - ensure .pck and .wasm files use absolute URLs
        # Godot exports reference files like "game.pck" or "game.wasm" - need to make them absolute
        # Also handle data attributes and any other references
        html_content = re.sub(
            r'(src|href|data-[^=]+)=["\']([^"\']+\.(pck|wasm|js))["\']',
            lambda m: f'{m.group(1)}="{asset_base_url}/{m.group(2)}"',
            html_content
        )
        
        # Also fix any JavaScript code that references these files
        # Godot's engine.js might have hardcoded paths
        html_content = re.sub(
            r'["\']([^"\']+\.(pck|wasm))["\']',
            lambda m: f'"{asset_base_url}/{m.group(1)}"',
            html_content
        )
        
        logger.info(f"🔧 Modified HTML: Added base tag, disabled ServiceWorker, fixed asset paths")
        
        # Serve with headers that allow inline styles/scripts and iframe embedding
        # Note: Removed X-Frame-Options to allow cross-origin embedding (frontend on 8080, backend on 8000)
        # Using CSP frame-ancestors instead for better control
        return Response(
            content=html_content.encode('utf-8'),
            media_type="text/html",
            headers={
                "Content-Security-Policy": "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: *; script-src 'self' 'unsafe-inline' 'unsafe-eval' *; style-src 'self' 'unsafe-inline' *; img-src 'self' data: blob: *; font-src 'self' data: *; connect-src 'self' *; worker-src 'self' blob: *; frame-ancestors *;",
                "X-Content-Type-Options": "nosniff",
                "Access-Control-Allow-Origin": "*"  # Allow CORS for asset loading
            }
        )
    except Exception as e:
        logger.error(f"Preview proxy error: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail=f"Game preview not found: {str(e)}")


@generation_router.get("/download/{project_id}")
async def download_game(
    project_id: str,
    request: Request,
    platform: Optional[str] = Query(None, description="Platform: windows, macos, linux, android, ios, web"),
    current_user = Depends(get_current_user),
    components = Depends(get_components)
):
    """
    Download game build for a project.
    Auto-detects best platform based on user's system if not specified.
    """
    try:
        # Auto-detect platform from User-Agent if not specified
        if not platform:
            user_agent = request.headers.get("user-agent", "").lower()
            if "windows" in user_agent:
                platform = "windows"
            elif "mac" in user_agent or "darwin" in user_agent:
                platform = "macos"
            elif "linux" in user_agent or "x11" in user_agent:
                platform = "linux"
            elif "android" in user_agent:
                platform = "android"
            elif "iphone" in user_agent or "ipad" in user_agent or "ios" in user_agent:
                platform = "ios"
            else:
                platform = "web"  # Default to web for unknown platforms
        
        auto_detected = platform is None
        logger.info(f"📥 Download request: project_id={project_id}, platform={platform} (auto-detected: {auto_detected})")
        db = components['database']
        storage_service = components['storage']
        
        # Get builds for this project
        try:
            builds = await db.get_builds(project_id)
            logger.info(f"📦 Found {len(builds)} builds for project {project_id}")
            if builds:
                logger.info(f"📦 Build platforms: {[b.get('platform') for b in builds]}")
        except Exception as e:
            logger.error(f"❌ Failed to get builds from database: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
        if not builds:
            logger.warning(f"⚠️  No builds found for project {project_id}")
            raise HTTPException(status_code=404, detail="No builds found for this project. The game may still be generating.")
        
        # Find the requested platform build, or auto-detect best option
        build_url = None
        filename = None
        selected_platform = None
        
        # Priority order for auto-selection (if requested platform not found)
        # Order: native desktop > mobile > web
        platform_priority = ['windows', 'macos', 'linux', 'android', 'ios', 'web']
        
        if platform and platform.lower() in platform_priority:
            # Look for specific platform
            for build in builds:
                build_platform = build.get('platform', '').lower()
                logger.info(f"🔍 Checking build platform: {build_platform} (requested: {platform.lower()})")
                if build_platform == platform.lower():
                    build_url = build.get('build_url')
                    selected_platform = platform.lower()
                    filename = f"{project_id}_{platform}.{_get_file_extension(platform)}"
                    logger.info(f"✅ Found {platform} build: {build_url}")
                    break
        
        # If not found, try priority order
        if not build_url:
            logger.info("🔍 Platform not found, trying priority order...")
            for p in platform_priority:
                for build in builds:
                    if build.get('platform', '').lower() == p:
                        build_url = build.get('build_url')
                        selected_platform = p
                        filename = f"{project_id}_{p}.{_get_file_extension(p)}"
                        logger.info(f"✅ Found {p} build: {build_url}")
                        break
                if build_url:
                    break
        
        if not build_url:
            logger.error(f"❌ No suitable build found. Available builds: {[(b.get('platform'), b.get('build_url')) for b in builds]}")
            raise HTTPException(status_code=404, detail="No suitable build found for the requested platform")
        
        logger.info(f"📥 Using build URL: {build_url}")
        
        # Extract storage path from Supabase URL
        # URL format: https://{project}.supabase.co/storage/v1/object/public/{bucket}/{path}
        storage_path = _extract_storage_path(build_url)
        
        file_data = None
        
        if storage_path:
            logger.info(f"📁 Storage path extracted: {storage_path}")
            # Try downloading from storage using path
            try:
                file_data = await storage_service.download_file(storage_path)
                logger.info(f"✅ Downloaded build from storage: {storage_path} ({len(file_data)} bytes)")
            except Exception as download_error:
                logger.warning(f"⚠️  Failed to download from storage path: {download_error}")
                # Fall through to try direct URL download
                file_data = None
        
        # Fallback: Try downloading directly from URL if path extraction failed or storage download failed
        if not file_data:
            logger.info(f"🔄 Attempting direct download from URL: {build_url}")
            try:
                import httpx
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.get(build_url)
                    if response.status_code == 200:
                        file_data = response.content
                        logger.info(f"✅ Downloaded build directly from URL ({len(file_data)} bytes)")
                    else:
                        logger.error(f"❌ Direct URL download failed: {response.status_code}")
                        raise HTTPException(
                            status_code=404,
                            detail=f"Build file not accessible. URL returned status {response.status_code}"
                        )
            except httpx.RequestError as e:
                logger.error(f"❌ HTTP request failed: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to download build file: {str(e)}"
                )
            except Exception as e:
                logger.error(f"❌ Direct download failed: {e}", exc_info=True)
                if not storage_path:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid build URL format and direct download failed: {build_url}. Error: {str(e)}"
                    )
                else:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Build file not found. Storage path: {storage_path}, URL: {build_url}. Error: {str(e)}"
                    )
        
        if not file_data or len(file_data) == 0:
            logger.error(f"❌ Downloaded file is empty: {storage_path}")
            raise HTTPException(status_code=404, detail="Build file is empty")
        
        # For web builds, create a ZIP with all files + launcher
        if selected_platform == 'web':
            logger.info("📦 Creating ZIP package for web build with launcher...")
            try:
                import zipfile
                import io
                
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    # Add the HTML file
                    zip_file.writestr('index.html', file_data)
                    
                    # Download and add all associated web files (.wasm, .pck, .js, .png)
                    preview_prefix = f"games/{project_id}/preview/"
                    try:
                        # List all files in preview directory
                        preview_files = await storage_service.list_files(preview_prefix)
                        
                        for file_info in preview_files:
                            if isinstance(file_info, dict):
                                file_name = file_info.get('name', '')
                                if file_name and file_name != 'index.html' and file_name != 'PLAY_GAME.bat':
                                    file_path = f"{preview_prefix}{file_name}"
                                    try:
                                        file_content = await storage_service.download_file(file_path)
                                        zip_file.writestr(file_name, file_content)
                                        logger.info(f"✅ Added to ZIP: {file_name}")
                                    except Exception as e:
                                        logger.warning(f"⚠️  Failed to add {file_name} to ZIP: {e}")
                    except Exception as e:
                        logger.warning(f"⚠️  Could not list preview files: {e}")
                    
                    # Add launcher script
                    launcher_script = '''@echo off
echo ========================================
echo    Gamora AI - Game Launcher
echo ========================================
echo.
echo Starting local server...
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python from https://www.python.org/
    echo Or use one of these alternatives:
    echo   1. Install Python and add it to PATH
    echo   2. Use Node.js: npm install -g http-server, then run: http-server -p 8000
    echo   3. Use VS Code Live Server extension
    echo.
    pause
    exit /b 1
)

REM Start Python HTTP server in background
start /B python -m http.server 8000

REM Wait a moment for server to start
timeout /t 2 /nobreak >nul

REM Open browser
start http://localhost:8000/index.html

echo.
echo Game should open in your browser!
echo.
echo To stop the server, close this window or press Ctrl+C
echo.
pause
'''
                    zip_file.writestr('PLAY_GAME.bat', launcher_script.encode('utf-8'))
                    
                    # Add README
                    readme = f'''# How to Play Your Game

## Quick Start (Windows)
1. Double-click **PLAY_GAME.bat**
2. The game will open in your browser automatically!

## Manual Method
1. Open PowerShell/Command Prompt in this folder
2. Run: `python -m http.server 8000`
3. Open browser: http://localhost:8000

## Requirements
- Python 3.x (for the launcher)
- OR use Node.js: `npm install -g http-server` then `http-server -p 8000`
- OR use VS Code Live Server extension

Enjoy your game!
'''
                    zip_file.writestr('README.txt', readme.encode('utf-8'))
                
                file_data = zip_buffer.getvalue()
                filename = f"{project_id}_web.zip"
                content_type = 'application/zip'
                logger.info(f"✅ Created ZIP package ({len(file_data)} bytes)")
            except Exception as e:
                logger.error(f"❌ Failed to create ZIP: {e}", exc_info=True)
                # Fall back to single HTML file
                content_type = _get_content_type('web')
        else:
            # Determine content type for other platforms
            content_type = _get_content_type(selected_platform or platform or 'windows')
        
        # Return file as download
        logger.info(f"✅ Returning file download: {filename} ({len(file_data)} bytes, type: {content_type})")
        return Response(
            content=file_data,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(file_data)),
                "Access-Control-Allow-Origin": "*"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Download error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


def _get_file_extension(platform: str) -> str:
    """Get file extension for platform"""
    extensions = {
        'windows': 'exe',
        'macos': 'zip',  # macOS .app bundle zipped
        'linux': 'x86_64',  # Linux executable
        'android': 'apk',
        'ios': 'ipa',
        'web': 'zip'  # Web builds are zipped with launcher
    }
    return extensions.get(platform.lower(), 'zip')


def _get_content_type(platform: str) -> str:
    """Get content type for platform"""
    content_types = {
        'windows': 'application/x-msdownload',
        'macos': 'application/zip',
        'linux': 'application/x-executable',
        'android': 'application/vnd.android.package-archive',
        'ios': 'application/octet-stream',
        'web': 'application/zip'
    }
    return content_types.get(platform.lower(), 'application/octet-stream')


def _extract_storage_path(url: str) -> Optional[str]:
    """Extract storage path from Supabase URL (public or signed)"""
    try:
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        
        # Handle public URLs: /storage/v1/object/public/{bucket}/{path}
        if '/storage/v1/object/public/' in parsed.path:
            path_part = parsed.path.split('/storage/v1/object/public/')[1]
            return path_part
        
        # Handle signed URLs: /storage/v1/object/sign/{bucket}/{path}?token=...
        elif '/storage/v1/object/sign/' in parsed.path:
            path_part = parsed.path.split('/storage/v1/object/sign/')[1]
            # Remove any query parameters (token, signature, etc.)
            if '?' in path_part:
                path_part = path_part.split('?')[0]
            return path_part
        
        # If URL is already just a path (bucket/path format), return as-is
        elif not url.startswith('http'):
            return url
        
        return None
    except Exception as e:
        logger.error(f"Failed to extract storage path from URL: {e}")
        return None
