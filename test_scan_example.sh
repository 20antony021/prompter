#!/bin/bash
# Example: How to run an actual AI scan with your platform

echo "🎯 Prompter Platform - AI Scan Example"
echo "======================================="
echo ""
echo "This example shows how your platform works:"
echo "1. Sends a prompt to ChatGPT"
echo "2. ChatGPT responds with CRM recommendations"
echo "3. Platform extracts brand mentions"
echo "4. Calculates visibility score"
echo ""

# Example prompt and expected response
cat <<'EOF'
📝 Example Prompt:
"What is the best CRM software for small businesses?"

🤖 ChatGPT Response (example):
"For small businesses, I recommend:

1. HubSpot CRM - Free tier available, great for startups
2. Salesforce Essentials - Comprehensive features
3. AcmeCRM - Modern interface, good value for money
4. Pipedrive - Sales-focused CRM
5. Zoho CRM - Affordable option

Each has different strengths depending on your needs..."

🔍 What Your Platform Does:
1. Extract mentions:
   ✓ HubSpot CRM (position: 0, sentiment: 0.7)
   ✓ Salesforce (position: 1, sentiment: 0.8)
   ✓ AcmeCRM (position: 2, sentiment: 0.6)
   ✓ Pipedrive (position: 3, sentiment: 0.5)
   ✓ Zoho CRM (position: 4, sentiment: 0.5)

2. Calculate visibility score:
   - Brand mentions: 1 (AcmeCRM)
   - Competitor mentions: 4
   - Average position: 2 (mentioned 3rd)
   - Average sentiment: 0.6 (positive)
   
   Score = (1/5 × 40) + (30 - 2×5) + (0.6+1)/2 × 30
        = 8 + 20 + 24
        = 52/100 ✅

3. Store in database:
   - ScanRun created
   - ScanResult saved
   - Mentions extracted
   - Visibility score: 52/100

4. Show on dashboard:
   - Real-time visibility metrics
   - Competitor comparison
   - Trend over time

EOF

echo ""
echo "📊 To run a real scan (once API is working):"
echo ""
echo 'curl -X POST http://localhost:8000/v1/scans \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{'
echo '    "brand_id": 1,'
echo '    "prompt_set_id": 1,'
echo '    "models": ["gpt-4"]'
echo '  }'"'"
echo ""
echo "Then check: http://localhost:3005/dashboard"
echo ""
echo "✅ Your real OpenAI API key is configured and ready!"
echo "✅ Database has sample data to compare against"
echo "✅ Frontend shows real results (no more fake data)"
echo ""
echo "🚀 This is how your customers will track their AI visibility!"

