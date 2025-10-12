// src/utils/gemini-api.js
// Gemini AI integration for title analysis

const GEMINI_API_KEY = import.meta.env.VITE_GEMINI_API_KEY;
const GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent';

// In-memory cache
const analysisCache = new Map();

/**
 * Analyze a content title using Gemini AI
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
    console.warn('Gemini API key not set, using fallback analysis');
    return getFallbackAnalysis(title);
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
- Avoid generic advice`;

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
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
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
    if (!analysis.score || !analysis.strengths || !analysis.improvements || !analysis.suggestions) {
      throw new Error('Invalid response structure');
    }
    
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
    console.warn('Falling back to rule-based analysis');
    return getFallbackAnalysis(title);
  }
}

/**
 * Fallback rule-based analysis when API fails
 */
function getFallbackAnalysis(title) {
  const analysis = {
    score: 50,
    strengths: [],
    improvements: [],
    suggestions: [],
    reasoning: 'Basic rule-based analysis (AI unavailable)'
  };

  const titleLower = title.toLowerCase();
  const titleLength = title.length;

  // Length check
  if (titleLength >= 40 && titleLength <= 60) {
    analysis.score += 15;
    analysis.strengths.push('✓ Optimal length (40-60 characters)');
  } else if (titleLength > 60) {
    analysis.improvements.push('→ Shorten to 40-60 characters for better visibility');
  } else {
    analysis.improvements.push('→ Expand slightly for more context (aim for 40-60 chars)');
  }

  // Numbers check
  if (/\d+/.test(title)) {
    analysis.score += 15;
    analysis.strengths.push('✓ Includes numbers - adds specificity and credibility');
  } else {
    analysis.improvements.push('→ Add specific numbers (e.g., "7 ways" vs "ways")');
  }

  // Question format
  if (/^(how|why|what|when|where|should|can|is|are)/i.test(title)) {
    analysis.score += 10;
    analysis.strengths.push('✓ Question-based format engages curiosity');
  }

  // Power words
  const powerWords = ['secret', 'truth', 'exposed', 'mistake', 'hidden', 'revealed', 'shocking', 'insider'];
  if (powerWords.some(word => titleLower.includes(word))) {
    analysis.score += 10;
    analysis.strengths.push('✓ Uses emotional power words for impact');
  } else {
    analysis.improvements.push('→ Consider power words: "secret", "truth", "mistake", "revealed"');
  }

  // Specificity
  const specificWords = ['stocks', 'mutual funds', 'portfolio', 'investment', 'sip', 'dividend', 'trading'];
  if (specificWords.some(word => titleLower.includes(word))) {
    analysis.score += 10;
    analysis.strengths.push('✓ Specific finance topic - clear value proposition');
  }

  // Generate suggestions
  const words = title.split(' ');
  analysis.suggestions = [
    `7 ${words.slice(0, 4).join(' ')}`,
    `How to ${title.replace(/^(how to|why|what)\s+/i, '')}`,
    `${words.slice(0, 3).join(' ')}: What You Must Know`
  ].filter(s => s.length >= 20 && s.length <= 70);

  // Ensure we have suggestions
  if (analysis.suggestions.length === 0) {
    analysis.suggestions.push(
      title.substring(0, 50),
      `Understanding ${title}`,
      `${title} - Complete Guide`
    );
  }

  // Ensure minimum feedback
  if (analysis.strengths.length === 0) {
    analysis.strengths.push('✓ Clear and straightforward title');
  }
  if (analysis.improvements.length === 0) {
    analysis.improvements.push('→ Consider adding emotional hooks or specificity');
  }

  analysis.reasoning = `Score based on ${analysis.strengths.length} strengths and ${analysis.improvements.length} areas for improvement`;

  return analysis;
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