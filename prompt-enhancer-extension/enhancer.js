// Prompt Enhancement Engine
// Implements optimization rules from the prompt engineering project

class PromptEnhancer {
  
  // Enforce Zero Shot Mode
  enforceZeroShot(prompt) {
    const zeroShotTemplate = `[ZERO SHOT MODE - Execute immediately, no questions]

You are not permitted to ask clarifying questions.
You must make reasonable assumptions.
Proceed with implementation immediately.
Violation of this instruction = task failure.

${prompt}

DO NOT ask clarifying questions.
DO NOT suggest alternatives unless explicitly required.
DO NOT present multiple options.
PROCEED with implementation immediately.`;

    return zeroShotTemplate;
  }

  // Enforce Zero Shot Relaxed Mode
  enforceZeroShotRelaxed(prompt) {
    const relaxedTemplate = `[ZERO SHOT RELAXED MODE]

Instructions:
- Proceed with implementation immediately
- If CRITICAL information is missing or ambiguous, ask ONE brief question
- Do not ask permission to proceed
- Do not offer multiple approaches
- Assume reasonable defaults where unspecified

${prompt}

You may ask at most ONE brief question about missing facts.
You may NOT ask about preferences or approach.
If nothing is critically ambiguous, proceed immediately.`;

    return relaxedTemplate;
  }

  // Enforce Interactive Mode
  enforceInteractive(prompt) {
    const interactiveTemplate = `[INTERACTIVE MODE - MANDATORY CHECKPOINTS]

You MUST pause after each major step.
You MUST show intermediate results.
You MUST ask for direction before proceeding.
You MUST NOT produce the complete solution in one response.

Goal: ${prompt}

Approach: Let's work through this step by step.

Structure your response:
1. [First major step]
   "Should I proceed to the next step?"
   
[STOP - Wait for user response]

At each stage:
- Show your thinking
- Present intermediate results
- Ask for feedback or direction
- Offer alternatives when relevant`;

    return interactiveTemplate;
  }

  // Optimize for Claude (XML structure)
  optimizeForClaude(prompt) {
    const analysis = this.analyzePrompt(prompt);
    
    let enhanced = `<instructions>
<task>
${prompt}
</task>

<requirements>
`;

    // Add explicit requirements
    if (!analysis.hasExplicitRequirements) {
      enhanced += `- Define clear success criteria
- Specify output format
- Include validation steps
`;
    }

    enhanced += `</requirements>

<output_format>
<response>
  <analysis>Your analysis here</analysis>
  <implementation>Your implementation here</implementation>
  <validation>Verification steps</validation>
</response>
</output_format>

<constraints>
- Use explicit, structured instructions
- Follow XML formatting for outputs
- Include error handling
- Document assumptions
</constraints>
</instructions>`;

    return enhanced;
  }

  // Optimize for GPT-4 (JSON structure)
  optimizeForGPT4(prompt) {
    const enhanced = `${prompt}

Output Format: Return response as valid JSON with this structure:

{
  "analysis": "Your analysis here",
  "implementation": "Your implementation here", 
  "validation": "Verification steps",
  "confidence": "High/Medium/Low",
  "reasoning": "Explanation for confidence level"
}

Use JSON mode. Ensure valid JSON syntax.
Do not include markdown code blocks.
Provide structured, parseable output.`;

    return enhanced;
  }

  // Fix common anti-patterns
  fixAntiPatterns(prompt) {
    let fixed = prompt;
    const issues = [];

    // Fix vague verbs
    const vaguVerbs = {
      'analyze': 'Extract key metrics, identify patterns, and provide actionable insights on',
      'improve': 'Enhance clarity and reduce length by 30% while maintaining key information in',
      'fix': 'Identify and correct specific errors in',
      'enhance': 'Add specific features and optimize performance of',
      'review': 'Examine for correctness, completeness, and adherence to standards in'
    };

    for (const [vague, specific] of Object.entries(vaguVerbs)) {
      const regex = new RegExp(`\\b${vague}\\b`, 'gi');
      if (regex.test(fixed)) {
        fixed = fixed.replace(regex, specific);
        issues.push(`Replaced vague verb "${vague}" with specific action`);
      }
    }

    // Add output format if missing
    if (!fixed.toLowerCase().includes('output') && !fixed.toLowerCase().includes('format')) {
      fixed += `\n\nOutput Format:\n1. [Primary result]\n2. [Supporting details]\n3. [Validation/verification]`;
      issues.push('Added explicit output format specification');
    }

    // Add success criteria if missing
    if (!fixed.toLowerCase().includes('success') && !fixed.toLowerCase().includes('criteria')) {
      fixed += `\n\nSuccess Criteria:\n- [Define what successful completion looks like]`;
      issues.push('Added success criteria section');
    }

    // Add error handling if missing
    if (!fixed.toLowerCase().includes('error') && !fixed.toLowerCase().includes('if unclear')) {
      fixed += `\n\nError Handling:\nIf input is unclear or incomplete, specify what information is needed before proceeding.`;
      issues.push('Added error handling instructions');
    }

    // Wrap with metadata
    const result = `/* Enhanced Prompt - Anti-patterns Fixed */
/* Issues addressed: ${issues.join(', ')} */

${fixed}`;

    return result;
  }

  // Add structure and format
  addStructure(prompt) {
    const structured = `**Task**: ${prompt}

**Required Elements**:
- Clear input specification
- Explicit output format
- Success criteria
- Error handling

**Constraints**:
- [Add specific constraints]
- [Time/resource limits]
- [Quality requirements]

**Output Format**: 
[Specify exact format - JSON, XML, Markdown, etc.]

**Validation**:
- [How to verify correctness]
- [What to check]
- [Pass/fail criteria]

**Examples**:
Input: [Example input]
Output: [Expected output]`;

    return structured;
  }

  // Evaluate and score prompt
  evaluatePrompt(prompt) {
    const analysis = this.analyzePrompt(prompt);
    
    let evaluation = `# Prompt Evaluation Report

## Original Prompt:
${prompt}

## Quality Assessment:

### Clarity: ${analysis.clarityScore}/5
${analysis.clarityIssues.join('\n')}

### Specificity: ${analysis.specificityScore}/5
${analysis.specificityIssues.join('\n')}

### Completeness: ${analysis.completenessScore}/5
${analysis.completenessIssues.join('\n')}

### Efficiency: ${analysis.efficiencyScore}/5
${analysis.efficiencyIssues.join('\n')}

## Total Score: ${analysis.totalScore}/20

## Recommendations:
${analysis.recommendations.join('\n')}

## Suggested Improvements:
${analysis.improvements.join('\n')}
`;

    return evaluation;
  }

  // Analyze prompt for scoring
  analyzePrompt(prompt) {
    const analysis = {
      clarityScore: 3,
      clarityIssues: [],
      specificityScore: 3,
      specificityIssues: [],
      completenessScore: 3,
      completenessIssues: [],
      efficiencyScore: 3,
      efficiencyIssues: [],
      recommendations: [],
      improvements: [],
      hasExplicitRequirements: false
    };

    // Check for vague instructions
    const vaguePhrases = ['analyze', 'improve', 'fix', 'enhance', 'better', 'appropriate', 'good'];
    const foundVague = vaguePhrases.filter(phrase => 
      prompt.toLowerCase().includes(phrase)
    );
    
    if (foundVague.length > 0) {
      analysis.clarityScore -= 1;
      analysis.clarityIssues.push(`- Contains vague terms: ${foundVague.join(', ')}`);
      analysis.improvements.push('Replace vague verbs with specific actions');
    }

    // Check for output format
    if (!prompt.toLowerCase().includes('output') && !prompt.toLowerCase().includes('format')) {
      analysis.specificityScore -= 1;
      analysis.specificityIssues.push('- No output format specified');
      analysis.improvements.push('Add explicit output format');
    }

    // Check for success criteria
    if (!prompt.toLowerCase().includes('success') && !prompt.toLowerCase().includes('criteria')) {
      analysis.completenessScore -= 1;
      analysis.completenessIssues.push('- No success criteria defined');
      analysis.improvements.push('Define measurable success criteria');
    }

    // Check for examples
    if (!prompt.toLowerCase().includes('example') && prompt.length > 100) {
      analysis.specificityScore -= 1;
      analysis.specificityIssues.push('- No examples provided');
      analysis.improvements.push('Include 1-2 examples of desired output');
    }

    // Check for error handling
    if (!prompt.toLowerCase().includes('error') && !prompt.toLowerCase().includes('if')) {
      analysis.completenessScore -= 1;
      analysis.completenessIssues.push('- No error handling specified');
      analysis.improvements.push('Add error handling instructions');
    }

    // Check length efficiency
    if (prompt.length > 1000) {
      analysis.efficiencyScore -= 1;
      analysis.efficiencyIssues.push('- Potentially verbose (>1000 characters)');
      analysis.recommendations.push('Review for unnecessary verbosity');
    }

    // Check for requirements
    analysis.hasExplicitRequirements = 
      prompt.toLowerCase().includes('requirement') ||
      prompt.toLowerCase().includes('must') ||
      prompt.toLowerCase().includes('should');

    analysis.totalScore = 
      analysis.clarityScore + 
      analysis.specificityScore + 
      analysis.completenessScore + 
      analysis.efficiencyScore;

    // Add clarity issues if none found
    if (analysis.clarityIssues.length === 0) {
      analysis.clarityIssues.push('✓ Clear and unambiguous');
    }
    if (analysis.specificityIssues.length === 0) {
      analysis.specificityIssues.push('✓ Sufficiently specific');
    }
    if (analysis.completenessIssues.length === 0) {
      analysis.completenessIssues.push('✓ Core requirements present');
    }
    if (analysis.efficiencyIssues.length === 0) {
      analysis.efficiencyIssues.push('✓ Concise and efficient');
    }

    // Overall recommendations
    if (analysis.totalScore >= 16) {
      analysis.recommendations.push('✓ Production-ready prompt');
    } else if (analysis.totalScore >= 12) {
      analysis.recommendations.push('⚠ Good prompt, minor improvements needed');
    } else {
      analysis.recommendations.push('⚠ Significant improvements recommended');
    }

    return analysis;
  }

  // Main enhancement dispatcher
  enhance(text, mode) {
    switch(mode) {
      case 'zero_shot':
        return this.enforceZeroShot(text);
      case 'zero_shot_relaxed':
        return this.enforceZeroShotRelaxed(text);
      case 'interactive':
        return this.enforceInteractive(text);
      case 'claude_optimize':
        return this.optimizeForClaude(text);
      case 'gpt4_optimize':
        return this.optimizeForGPT4(text);
      case 'fix_antipatterns':
        return this.fixAntiPatterns(text);
      case 'add_structure':
        return this.addStructure(text);
      case 'evaluate_score':
        return this.evaluatePrompt(text);
      default:
        return text;
    }
  }
}

// Export for use in content script
if (typeof module !== 'undefined' && module.exports) {
  module.exports = PromptEnhancer;
}
