# Test workflow for Lucide pipeline improvements
# Tests various intents with Premier League queries on 2026-01-01

$TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiMzJhYTIxMS1jYTU5LTQ3NzgtOWU0Mi1lYTNjNTkzYjFmYjEiLCJleHAiOjE3NjcyODgzNzN9.5RORtcnpO_Jd3HJ815kyedHRN9QpQE5p878-jFXHP4Y"
$BASE_URL = "http://localhost:8001"
$OUTPUT_DIR = "can_analyses"

# Create output directory
New-Item -ItemType Directory -Force -Path $OUTPUT_DIR | Out-Null

# Test cases
$tests = @(
    @{
        Name = "Test01_Standings"
        Question = "Classement de la Premier League"
        Context = "{}"
        ModelType = "fast"
        Intent = "standings"
    },
    @{
        Name = "Test02_TopScorers"
        Question = "Qui sont les meilleurs buteurs de Premier League?"
        Context = "{}"
        ModelType = "fast"
        Intent = "top_scorers"
    },
    @{
        Name = "Test03_LiveMatches"
        Question = "Matchs de Premier League en direct"
        Context = "{}"
        ModelType = "medium"
        Intent = "live_matches"
    },
    @{
        Name = "Test04_MatchAnalysis_Arsenal_ManCity"
        Question = "Analyse du dernier match Arsenal contre Manchester City"
        Context = "{}"
        ModelType = "slow"
        Intent = "match_analysis"
    },
    @{
        Name = "Test05_TeamStats_Liverpool"
        Question = "Statistiques de Liverpool cette saison"
        Context = "{}"
        ModelType = "medium"
        Intent = "team_stats"
    },
    @{
        Name = "Test06_PlayerStats_Haaland"
        Question = "Statistiques de Erling Haaland en Premier League"
        Context = "{}"
        ModelType = "fast"
        Intent = "player_stats"
    },
    @{
        Name = "Test07_H2H_Chelsea_Tottenham"
        Question = "Historique des confrontations entre Chelsea et Tottenham"
        Context = "{}"
        ModelType = "medium"
        Intent = "h2h"
    },
    @{
        Name = "Test08_Prediction_ManUnited_Newcastle"
        Question = "Prediction pour le match Manchester United contre Newcastle"
        Context = "{}"
        ModelType = "slow"
        Intent = "prediction"
    },
    @{
        Name = "Test09_TopAssists"
        Question = "Classement des passeurs decisifs en Premier League"
        Context = "{}"
        ModelType = "fast"
        Intent = "top_assists"
    },
    @{
        Name = "Test10_MatchFixtures_Today"
        Question = "Quels matchs de Premier League sont prevus aujourd'hui 1er janvier 2026?"
        Context = "{}"
        ModelType = "fast"
        Intent = "fixtures"
    }
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Starting Lucide Workflow Tests" -ForegroundColor Cyan
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "Tests: $($tests.Count)" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$results = @()

foreach ($test in $tests) {
    Write-Host "Running $($test.Name)..." -ForegroundColor Yellow

    # Prepare request
    $body = @{
        message = $test.Question
        context = @{}
        model_type = $test.ModelType
    } | ConvertTo-Json

    # Measure latency
    $startTime = Get-Date

    try {
        $response = Invoke-WebRequest -Uri "$BASE_URL/chat" `
            -Method POST `
            -Headers @{
                "Authorization" = "Bearer $TOKEN"
                "Content-Type" = "application/json"
            } `
            -Body $body `
            -UseBasicParsing

        $endTime = Get-Date
        $latency = ($endTime - $startTime).TotalSeconds

        $responseData = $response.Content | ConvertFrom-Json

        # Build markdown content
        $sb = New-Object System.Text.StringBuilder
        [void]$sb.AppendLine("# Test: $($test.Name)")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("**Date**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
        [void]$sb.AppendLine("**Intent attendu**: $($test.Intent)")
        [void]$sb.AppendLine("**Modele utilise**: $($test.ModelType)")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("---")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("## Contexte")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine('```json')
        [void]$sb.AppendLine($test.Context)
        [void]$sb.AppendLine('```')
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("---")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("## Question posee")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("> $($test.Question)")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("---")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("## Performances")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("- **Latence totale**: $([math]::Round($latency, 2))s")
        [void]$sb.AppendLine("- **Intent detecte**: $($responseData.intent)")
        [void]$sb.AppendLine("- **Session ID**: $($responseData.session_id)")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("---")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("## Reponse finale")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine($responseData.response)
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("---")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("**Test complete avec succes**")

        # Save to file
        $fileName = "$OUTPUT_DIR\$($test.Name)_$(Get-Date -Format 'yyyyMMdd_HHmmss').md"
        $sb.ToString() | Out-File -FilePath $fileName -Encoding UTF8

        Write-Host "  Success - Latency: $([math]::Round($latency, 2))s - Intent: $($responseData.intent)" -ForegroundColor Green

        $results += @{
            Test = $test.Name
            Status = "Success"
            Latency = $latency
            Intent = $responseData.intent
            File = $fileName
        }

    } catch {
        $endTime = Get-Date
        $latency = ($endTime - $startTime).TotalSeconds

        Write-Host "  Failed - Error: $($_.Exception.Message)" -ForegroundColor Red

        # Build error markdown
        $sb = New-Object System.Text.StringBuilder
        [void]$sb.AppendLine("# Test: $($test.Name) - ECHEC")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("**Date**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
        [void]$sb.AppendLine("**Intent attendu**: $($test.Intent)")
        [void]$sb.AppendLine("**Modele utilise**: $($test.ModelType)")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("---")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("## Contexte")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine('```json')
        [void]$sb.AppendLine($test.Context)
        [void]$sb.AppendLine('```')
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("---")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("## Question posee")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("> $($test.Question)")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("---")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("## Erreur")
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine('```')
        [void]$sb.AppendLine($_.Exception.Message)
        [void]$sb.AppendLine('```')
        [void]$sb.AppendLine("")
        [void]$sb.AppendLine("**Test echoue**")

        $fileName = "$OUTPUT_DIR\$($test.Name)_$(Get-Date -Format 'yyyyMMdd_HHmmss')_ERROR.md"
        $sb.ToString() | Out-File -FilePath $fileName -Encoding UTF8

        $results += @{
            Test = $test.Name
            Status = "Failed"
            Latency = $latency
            Intent = "N/A"
            Error = $_.Exception.Message
            File = $fileName
        }
    }

    # Pause between tests
    Start-Sleep -Seconds 2
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$successful = ($results | Where-Object { $_.Status -eq "Success" }).Count
$failed = ($results | Where-Object { $_.Status -eq "Failed" }).Count
$avgLatency = ($results | Where-Object { $_.Status -eq "Success" } | Measure-Object -Property Latency -Average).Average

Write-Host "Total tests: $($tests.Count)" -ForegroundColor White
Write-Host "Successful: $successful" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
if ($avgLatency) {
    Write-Host "Average latency: $([math]::Round($avgLatency, 2))s`n" -ForegroundColor Yellow
}

# Display results table
$results | Format-Table Test, Status, @{Label="Latency (s)"; Expression={[math]::Round($_.Latency, 2)}}, Intent -AutoSize

Write-Host "`nAll test reports saved to: $OUTPUT_DIR\" -ForegroundColor Cyan
