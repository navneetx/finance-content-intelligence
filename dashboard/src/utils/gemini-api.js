// src/utils/gemini-api.js
// Gemini AI integration - NO FALLBACK, AI ONLY

const GEMINI_API_KEY = import.meta.env.VITE_GEMINI_API_KEY;
const GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent';

// In-memory cache
const analysisCache = new Map();

/**
 * Analyze a content title using Gemini AI (NO FALLBACK)
 */
export async function analyzeTitleWithGemini(title, referenceData = []) {
  // Check cache first
  const cacheKey = title.toLowerCase().trim();
  if (analysisCache.has(cacheKey)) {
    console.log('✓ Using cached analysis');
    return analysisCache.get(cacheKey);
  }

  // Check if API key is set
  if (!GEMINI_API_KEY || GEMINI_API_KEY === 'your_gemini_api_key_here') {
    throw new Error('Gemini API key not configured. Please add VITE_GEMINI_API_KEY to environment variables.');
  }

  // Validate title is meaningful (prevent random letter strings)
  const wordCount = title.trim().split(/\s+/).length;
  const hasLetters = /[a-zA-Z]{3,}/.test(title);
  const hasMinLength = title.length >= 5;
  
  if (wordCount < 2) {
    throw new Error('Please enter a title with at least 2 words.');
  }
  
  if (!hasLetters) {
    throw new Error('Title must contain meaningful text (letters/words).');
  }
  
  if (!hasMinLength) {
    throw new Error('Title must be at least 5 characters long.');
  }

  // Get top performing titles for context
  const topTitles = referenceData
    .sort((a, b) => b.views - a.views)
    .slice(0, 10)
    .map(v => `"${v.title}" (${v.views.toLocaleString()} views, ${v.engagement}% engagement)`)
    .join('\n');

  const prompt = `You are an expert YouTube/LinkedIn content strategist analyzing finance content titles.

CONTEXT - Top performing finance titles:
${topTitles || 'No reference data'}

ANALYZE THIS TITLE: "${title}"

Provide analysis in STRICT JSON format (no markdown, no extra text):
{
  "score": <number 0-100>,
  "strengths": [<2-4 specific strengths as strings>],
  "improvements": [<2-4 specific actionable suggestions>],
  "suggestions": [<3 alternative title variations>],
  "reasoning": "<1 sentence explaining the score>"
}

Scoring criteria (total 100):
- Length (40-60 chars ideal): 20 points
- Numbers/specificity: 20 points
- Emotional/power words: 20 points
- Clarity & curiosity gap: 20 points
- Platform optimization: 20 points

Rules:
- Be specific and actionable
- Suggestions should be creative but realistic
- Consider finance audience (investors, beginners)
- Avoid generic advice
- Give honest scores (random letters should score 0-10)`;

  try {
    const response = await fetch(`${GEMINI_API_URL}?key=${GEMINI_API_KEY}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        contents: [{
          parts: [{
            text: prompt
          }]
        }],
        generationConfig: {
          temperature: 0.7,
          topK: 40,
          topP: 0.95,
          maxOutputTokens: 1024,
        }
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error('Gemini API error:', errorData);
      throw new Error(`Gemini API error: ${response.status} - ${errorData.error?.message || 'Unknown error'}`);
    }

    const data = await response.json();
    
    if (!data.candidates || !data.candidates[0]) {
      throw new Error('No response from Gemini API');
    }

    const generatedText = data.candidates[0].content.parts[0].text;
    
    // Extract JSON from response
    let jsonText = generatedText.trim();
    
    // Remove markdown code blocks if present
    if (jsonText.includes('```json')) {
      const match = jsonText.match(/```json\n([\s\S]*?)\n```/);
      if (match) jsonText = match[1];
    } else if (jsonText.includes('```')) {
      const match = jsonText.match(/```\n?([\s\S]*?)\n?```/);
      if (match) jsonText = match[1];
    }
    
    // Extract JSON object
    const jsonMatch = jsonText.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      jsonText = jsonMatch[0];
    }

    const analysis = JSON.parse(jsonText);
    
    // Validate structure
    if (typeof analysis.score !== 'number' || !Array.isArray(analysis.strengths) || 
        !Array.isArray(analysis.improvements) || !Array.isArray(analysis.suggestions)) {
      throw new Error('Invalid response structure from Gemini');
    }

    // Ensure score is between 0-100
    analysis.score = Math.max(0, Math.min(100, analysis.score));
    
    // Cache the result
    analysisCache.set(cacheKey, analysis);
    
    // Clear old cache entries if too many
    if (analysisCache.size > 50) {
      const firstKey = analysisCache.keys().next().value;
      analysisCache.delete(firstKey);
    }

    console.log('✓ Gemini analysis complete');
    return analysis;

  } catch (error) {
    console.error('Gemini API Error:', error);
    throw error; // Re-throw to be handled by calling component
  }
}

/**
 * Clear cache (useful for testing)
 */
export function clearCache() {
  analysisCache.clear();
  console.log('Analysis cache cleared');
}

/**
 * Get cache size
 */
export function getCacheSize() {
  return analysisCache.size;
}