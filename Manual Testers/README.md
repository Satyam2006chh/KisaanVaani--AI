# Manual Testers

This folder contains scripts for manually verifying the AI's internal tools and backend APIs. These scripts are designed to be run from the project root.

## Usage

Run all tests from the root directory:
```powershell
python "./Manual Testers/test_tools_logic.py"
```

### Scripts

1. **test_tools_logic.py**:
   - Simulates user queries for Weather, Mandi, News, Crop Advice, and Schemes.
   - Shows the Intent detected, the Raw Tool Output, and the Final AI Answer.
   - **Note**: This script uses the API keys defined in `backend/.env`.

2. **debug_mandi.py**:
   - Performs a direct raw API call to the `data.gov.in` Mandi resource.
   - Used for verifying connectivity and checking the latest available records in the government database.

## Security
- These scripts load API keys directly from `backend/.env`.
- **Never** hardcode your API keys inside these files.
