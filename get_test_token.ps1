# Get or create a test user and obtain JWT token

$BASE_URL = "http://localhost:8001"

# Try to login with existing test user first
$loginBody = @{
    email = "testworkflow@example.com"
    password = "testpass123"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/auth/login" `
        -Method POST `
        -Headers @{"Content-Type" = "application/json"} `
        -Body $loginBody `
        -UseBasicParsing

    $data = $response.Content | ConvertFrom-Json
    Write-Host "Login successful!"
    Write-Host "Token: $($data.access_token)"
    exit 0
} catch {
    Write-Host "Login failed, trying to register..."
}

# Try to register new user
$registerBody = @{
    username = "testworkflow"
    email = "testworkflow@example.com"
    password = "testpass123"
    first_name = "Test"
    last_name = "Workflow"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/auth/register" `
        -Method POST `
        -Headers @{"Content-Type" = "application/json"} `
        -Body $registerBody `
        -UseBasicParsing

    Write-Host "Registration successful! But email needs verification."
    Write-Host "You need to manually verify the email or activate the user in the database."
    exit 1
} catch {
    Write-Host "Registration also failed: $($_.Exception.Message)"
    exit 1
}
