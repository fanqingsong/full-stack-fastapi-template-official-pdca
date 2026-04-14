# Web Automation Testing - User Guide

## Overview

The Web Automation Testing feature allows you to create browser-based tests using natural language descriptions. The system uses Claude CLI's browser automation capabilities to execute tests and provides real-time feedback through WebSocket connections.

## Features

- **Natural Language Testing**: Describe tests in plain English
- **Real-time Logs**: Watch test execution live via WebSocket streaming
- **Screenshot Capture**: Automatic screenshots of important test steps
- **Test Management**: View, retry, and delete tests
- **Concurrent Execution**: Run up to 3 tests simultaneously
- **User Isolation**: Your tests are private and secure

## Creating a Test

1. Navigate to the "Web Tests" section from the sidebar
2. Click the "New Test" button
3. Enter the target URL (e.g., `https://example.com`)
4. Describe what you want to test in natural language
5. Click "Create Test"

## Example Test Descriptions

### Test Login Functionality
```
Test the login functionality:
1. Navigate to the login page
2. Enter username "test@example.com"
3. Enter password "testpass123"
4. Click the login button
5. Verify we are redirected to the dashboard
```

### Test Contact Form
```
Test the contact form:
1. Go to the contact page
2. Fill in all required fields (name, email, message)
3. Submit the form
4. Verify success message appears
```

### Test Navigation
```
Test website navigation:
1. Start at the homepage
2. Click on the "Products" menu
3. Verify products are displayed
4. Click on the first product
5. Verify product details page loads
```

## Viewing Results

Once a test is created:
- Click **"View Details"** to see the test execution
- Watch **real-time logs** in the Execution Log section
- View **screenshots** captured during the test
- Check the **final result** (Pass/Fail)
- Review **execution duration** and error messages

### Execution Logs

The log viewer displays real-time output with color coding:
- 🔵 **Blue**: Actions taken (e.g., clicking, typing)
- 🟠 **Amber**: Observations (e.g., page content, elements found)
- 🟢 **Green**: Successful results
- 🔴 **Red**: Errors and failures

## Test Statuses

| Status | Description |
|--------|-------------|
| **Pending** | Test is queued and waiting to start |
| **Running** | Test is currently executing |
| **Completed** | Test finished successfully |
| **Failed** | Test encountered an error |
| **Cancelled** | Test was cancelled by the user |

## Managing Tests

### View Details
Click the **"View"** button to see:
- Test parameters (URL and description)
- Execution logs
- Screenshots
- Test results

### Retry Test
Click the **"Retry"** button to create a new test with the same parameters. This is useful for:
- Running tests that failed due to temporary issues
- Testing the same scenario again after fixes

### Delete Test
Click the **"Delete"** button to remove a test. Note:
- Only available for **pending** and **failed** tests
- Running tests must be cancelled first
- This action cannot be undone

### Filter Tests
Use the status filter buttons to show:
- **All Tests**: Display all tests regardless of status
- **Pending**: Only show queued tests
- **Running**: Only show active tests
- **Completed**: Only show successful tests
- **Failed**: Only show failed tests

## Tips for Better Tests

### Be Specific
✅ **Good**: "Click the login button, enter username 'user@example.com', password 'pass123', then verify the dashboard appears"
❌ **Poor**: "Test the login"

### Break Down Complex Tests
Instead of one large test, create multiple smaller tests:
- Test 1: Login functionality
- Test 2: Profile update
- Test 3: Logout

### Use Clear Steps
Number your steps and describe actions clearly:
```
1. Navigate to /contact
2. Enter "John Doe" in the name field
3. Enter "john@example.com" in the email field
4. Click the submit button
5. Verify "Thank you" message appears
```

### Include Verification Steps
Always specify what to verify:
- "Verify X appears" rather than just "Check X"
- "Confirm the page title is 'Welcome'"
- "Make sure the error message is displayed"

## Troubleshooting

### Test Stuck in "Pending"
- Check if Claude CLI is installed on the server
- Verify the maximum concurrent tests limit (default: 3)
- Check backend logs for errors

### Test Failed
- Review the execution logs for error messages
- Check screenshots to see what went wrong
- Verify the URL is accessible
- Try re-running the test with a clearer description

### No Screenshots
- Check if MinIO is running and configured
- Verify the screenshots bucket exists
- Check backend logs for upload errors

### WebSocket Connection Issues
- Refresh the page to reconnect
- Check your network connection
- Verify the backend WebSocket endpoint is accessible

## Technical Details

### Execution Flow
1. User creates test with URL and description
2. Backend creates test record (status: pending)
3. Background task starts and invokes Claude CLI
4. WebSocket connection streams real-time logs
5. Executor parses output and extracts structured data
6. Screenshots uploaded to MinIO
7. Results saved to database
8. WebSocket sends completion message

### Claude CLI Integration
The system uses Claude CLI's browser automation to execute tests. The test description is converted into a structured prompt that instructs Claude to:
- Navigate to the specified URL
- Perform the actions described
- Take screenshots of important steps
- Report results with clear markers

### Security
- All endpoints require authentication
- WebSocket connections use token-based authentication
- Users can only access their own tests
- URLs are validated to prevent SSRF attacks
- Private network addresses are blocked

### Configuration
Default settings (can be configured in `.env`):
- **Test Timeout**: 10 minutes
- **Max Concurrent Tests**: 3
- **Screenshots Bucket**: `web-test-screenshots`
- **Claude CLI Path**: `claude`

## Limitations

- Requires Claude CLI to be installed on the server
- Maximum test duration: 10 minutes (configurable)
- Maximum concurrent tests: 3 (configurable)
- Only http:// and https:// URLs are supported
- Private network addresses are blocked

## Future Enhancements

Planned features for future releases:
- Test templates for common scenarios
- Video recording of test execution
- Test scheduling (run tests periodically)
- Test suites (group multiple tests)
- Export results as PDF or JSON
- Analytics and success rate trends
- Email/webhook notifications
