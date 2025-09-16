# 🪟 SOC Agent Windows Setup

## Quick Start

### Option 1: Full Stack (Recommended)
```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup-windows-full.ps1
```

### Option 2: Backend Only
```powershell
.\setup-windows.ps1
```

### Option 3: Batch File
```cmd
# Double-click or run from command prompt
setup-windows-full.bat
```

### Option 4: Docker
```powershell
.\setup-windows-full.ps1 -UseDocker
```

## Demo

### Automated Demo
```powershell
# Full stack demo (with frontend)
.\demo-windows-full.ps1

# Backend only demo
.\demo-windows.ps1
```

### Manual Demo
```cmd
# Full stack demo (with frontend)
demo-windows-full.bat

# Backend only demo
demo-windows.bat
```

## URLs

- **Web Interface**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Health Check**: http://localhost:8000/healthz
- **API Docs**: http://localhost:8000/docs
- **MailDev**: http://localhost:1080 (Docker only)

## Troubleshooting

### PowerShell Error
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Port 8000 in Use
```cmd
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Python Not Found
- Download from https://www.python.org/downloads/
- Check "Add Python to PATH" during installation

### Node.js Not Found
- Download from https://nodejs.org/
- Check "Add to PATH" during installation

## Files Created

- `setup-windows-full.ps1` - PowerShell full stack setup script
- `setup-windows.ps1` - PowerShell backend-only setup script
- `setup-windows-full.bat` - Batch file full stack setup script
- `setup-windows.bat` - Batch file backend-only setup script
- `demo-windows-full.ps1` - PowerShell full stack demo script
- `demo-windows.ps1` - PowerShell backend-only demo script
- `demo-windows-full.bat` - Batch file full stack demo script
- `demo-windows.bat` - Batch file backend-only demo script
- `WINDOWS_PRESENTATION_GUIDE.md` - Complete presentation guide

## Support

For detailed instructions, see `WINDOWS_PRESENTATION_GUIDE.md`
