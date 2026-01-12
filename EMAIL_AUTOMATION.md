# Automated Email Reports Setup Guide

This guide explains how to configure Oracle to automatically send daily reports to your email **without requiring any passwords or credentials**.

## Why No Credentials?

We use **local sendmail** (pre-installed on most servers) or **file-based delivery** so you don't need:
- ❌ Gmail App Passwords
- ❌ SMTP server credentials  
- ❌ Third-party API keys

## Quick Setup

### 1. Run the Setup Script

```bash
python setup_email_reports.py
```

This creates a `.env` file with automatic email configuration.

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Test Delivery

```bash
python -m backend.cli.main test-email
```

### 4. Start the Scheduler

```bash
python -m backend.cli.main scheduler
```

The scheduler runs in the foreground and automatically:
- **Premarket Report**: 6:30 AM ET
- **Post-market Report**: 4:30 PM ET

## Delivery Methods (No Passwords!)

Choose how you want to receive reports:

### Option 1: Auto (Recommended)
Uses sendmail if available, otherwise saves to file:
```bash
EMAIL_DELIVERY_METHOD=auto
```

### Option 2: Sendmail (Linux Servers)
Uses local sendmail command (most Linux servers have this):
```bash
EMAIL_DELIVERY_METHOD=sendmail
```

### Option 3: File-Based (Simplest)
Saves reports to a directory, no email at all:
```bash
EMAIL_DELIVERY_METHOD=file
EMAIL_OUTPUT_DIR=./email_reports
```

Reports will be saved as: `email_reports/report_20260107_063000.txt`

### Option 4: SMTP (Requires Credentials)
Only use if you need SMTP authentication:
```bash
EMAIL_DELIVERY_METHOD=smtp
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## Manual Configuration

Add these settings to your `.env`:

```bash
# Enable automated reports
ENABLE_EMAIL=true

# Choose delivery method (no credentials for auto, sendmail, or file)
EMAIL_DELIVERY_METHOD=auto

# For file-based delivery
EMAIL_OUTPUT_DIR=./email_reports

# Recipient configuration
EMAIL_TO=your_email@example.com

# Scheduling
SCHEDULER_TIMEZONE=America/New_York
PREMIUM_TIME=06:30  # Premarket
POSTMARKET_TIME=16:30  # 4:30 PM
```

## Command Reference

| Command | Description |
|---------|-------------|
| `oracle test-email` | Test email delivery |
| `oracle scheduler` | Start automated scheduler |
| `oracle scheduler --status` | Check scheduler status |
| `oracle scheduler --stop` | Stop scheduler |
| `oracle daily --show` | Generate and view report |

## Troubleshooting

### Email Not Sent?

1. **Check method**: `EMAIL_DELIVERY_METHOD=auto` (no credentials)
2. **Verify sendmail**: Run `which sendmail` - should show path
3. **Check logs**: Run with `LOG_LEVEL=DEBUG`

### Using File-Based Delivery?

Reports are saved to `./email_reports/` with timestamps:
```
email_reports/
└── report_20260107_063000.txt
```

### Scheduler Issues?

1. Check status: `python -m backend.cli.main scheduler --status`
2. Verify timezone: `SCHEDULER_TIMEZONE=America/New_York`
3. Dependencies: Ensure `apscheduler` is installed

## Testing Without Sending

To test without actually sending:

```bash
# File-based (safest - just saves to disk)
EMAIL_DELIVERY_METHOD=file
EMAIL_OUTPUT_DIR=./test_reports

python -m backend.cli.main test-email
```

## How It Works

```
Scheduler Trigger
        ↓
Generate Report (market data + AI analysis)
        ↓
Delivery Method (auto/sendmail/file)
        ↓
Email Sent OR File Saved
```

No passwords, no OAuth, no external services required!

## Supported Platforms

| Platform | Sendmail Available? | Notes |
|----------|-------------------|-------|
| Linux (Ubuntu/Debian) | ✅ Yes | Pre-installed on most servers |
| Linux (RHEL/CentOS) | ✅ Yes | Pre-installed |
| macOS | ⚠️ Needs setup | Install postfix or use file method |
| Windows | ❌ No | Use file-based delivery |

## Production Deployment

On a Linux server:

```bash
# 1. SSH into server
ssh your-server

# 2. Clone and setup
cd /home/your_user/market-analyst
python setup_email_reports.py

# 3. Install dependencies
pip install -r requirements.txt

# 4. Test
python -m backend.cli.main test-email

# 5. Run in background with systemd
# Create /etc/systemd/system/oracle.service
```

That's it - no email credentials needed!
